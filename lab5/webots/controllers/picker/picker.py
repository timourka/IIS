"""Minimal RGB pick-and-place prototype for the accompanying Webots world."""
import json
import os
from pathlib import Path
from typing import Any
from controller import Robot
from vision import detect, project, fuse

robot = Robot()
dt = int(robot.getBasicTimeStep())
camera = robot.getDevice('rgb')
cup = robot.getDevice('cup')
motors = [robot.getDevice(a) for a in 'xyz']
sensors = [robot.getDevice('s'+a) for a in 'xyz']
for device in (camera, *sensors):
    device.enable(dt)
cup.enablePresence(dt)
trace = []
run_dir = os.getenv('PICKER_RUN_DIR')
for motor in motors:
    motor.setVelocity(0.36)

def step():
    if robot.step(dt) == -1:
        raise SystemExit(0)
    present = bool(cup.getPresence())
    if not trace or present != trace[-1][2]:
        trace.append((robot.getTime(), position(), present))

def position():
    return tuple(s.getValue() for s in sensors)

def move(x,y,z):
    goals = (x,y,z)
    for motor, pos in zip(motors, goals):
        motor.setPosition(pos)
    for _ in range(350):
        step()
        if max(abs(a-b) for a,b in zip(position(), goals)) < 0.0008:
            for _ in range(5): step()
            return
    raise RuntimeError(f'Motion timeout: {goals}, measured {position()}')

def observe(color, z):
    w, h = camera.getWidth(), camera.getHeight()
    p = detect(camera.getImage(), w, h, color)
    if p is None: raise RuntimeError(f'No {color} region in RGB frame')
    x,y,sz = position()
    return project(p,w,h,camera.getFov(),(x+0.09,y,sz+0.12),z)

def execute():
    samples = []
    for x,y in ((0.30,0.055),(0.34,-0.045)):
        move(x,y,0.42)
        if run_dir:
            camera.saveImage(str(Path(run_dir)/f'view_{len(samples)+1}.png'), 95)
        samples.append((observe('red',0.05), observe('green',0.001)))
    source, target = (fuse(points) for points in zip(*samples))
    sx, sy = source
    tx, ty = target
    print('RGB source, goal:',source,target,flush=True)
    move(sx,sy,0.17)
    cup.turnOn()
    move(sx,sy,0.049)
    if not cup.getPresence(): raise RuntimeError('Vacuum contact not confirmed')
    move(sx,sy,0.19)
    move(tx,ty,0.19)
    if not cup.getPresence(): raise RuntimeError('Cube lost in transit')
    move(tx,ty,0.052)
    cup.turnOff()
    for _ in range(12): step()
    if cup.getPresence(): raise RuntimeError('Cube not released')
    move(tx,ty,0.17)
    move(0.28,0,0.42)
    if run_dir:
        camera.saveImage(str(Path(run_dir)/'placed_rgb.png'), 95)
    return dict(status='released',source=source,target=target,observations=samples,sim_time_s=robot.getTime())

try:
    result: dict[str, Any] = execute()
except (RuntimeError,ValueError) as exc:
    result=dict(status='failed',reason=str(exc),sim_time_s=robot.getTime())
result['grip_trace']=trace
print(json.dumps(result),flush=True)
if run_dir:
    path=Path(run_dir)/'picker.json'
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(result,indent=2),encoding='utf-8')
    temporary.replace(path)
while True: step()
