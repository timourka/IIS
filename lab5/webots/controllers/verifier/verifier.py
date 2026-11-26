"""Read-only ground truth checker; controller never receives true object pose."""
import json
import math
import os
from pathlib import Path
from controller import Supervisor

robot = Supervisor()
dt = int(robot.getBasicTimeStep())
cube = robot.getFromDef('CUBE')
goal = robot.getFromDef('GOAL')
initial = cube.getPosition()
target = goal.getPosition()
folder = os.getenv('PICKER_RUN_DIR')
if folder:
    path = Path(folder)/'picker.json'
    first = True
    while robot.step(dt) != -1:
        if first:
            robot.exportImage(str(Path(folder)/'start.png'),95)
            first = False
        if path.is_file() or robot.getTime() >= 30:
            break
    picker = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {'status':'timeout'}
    for _ in range(24):
        if robot.step(dt)==-1: raise SystemExit(2)
    final = cube.getPosition()
    error = math.dist(final[:2],target[:2])
    passed = picker['status']=='released' and error<0.02 and abs(final[2]-0.025)<0.005 and math.dist(initial[:2],final[:2])>0.25
    report=dict(passed=passed,initial_m=initial,target_m=target,final_m=final,xy_error_mm=1000*error,picker=picker)
    (Path(folder)/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    robot.exportImage(str(Path(folder)/'final.png'),95)
    robot.simulationQuit(0 if passed else 2)
while robot.step(dt)!=-1: pass
