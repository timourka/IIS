import argparse
import json
import os
import subprocess
from pathlib import Path


root=Path(__file__).resolve().parent
home=Path(os.environ.get('WEBOTS_HOME',r'C:\Program Files\Webots'))
webots=home/'msys64/mingw64/bin/webots.exe'
if not webots.is_file(): raise SystemExit(f'Webots not found: {webots}; set WEBOTS_HOME')
world=root/'webots/worlds/pick_place.wbt'
parser=argparse.ArgumentParser(description='Run the Webots lab scene.')
parser.add_argument('--gui',action='store_true')
parser.add_argument('--shifted',action='store_true',help='Run an alternate start position without changing the picker.')
args=parser.parse_args()
if args.gui and args.shifted:
    parser.error('--shifted is for automated verification')
if args.gui:
    subprocess.Popen([str(webots),str(world)])
    raise SystemExit(0)
run=root/'results'/('shifted' if args.shifted else 'baseline')
run.mkdir(exist_ok=True,parents=True)
for name in ('result.json','picker.json','final.png','start.png','view_1.png','view_2.png','placed_rgb.png'):
    (run/name).unlink(missing_ok=True)
env=dict(os.environ,PICKER_RUN_DIR=str(run))
alternate=None
try:
    if args.shifted:
        text=world.read_text(encoding='utf-8')
        before='translation 0.39 0.19 0.0255'
        assert text.count(before)==1
        alternate=world.with_name('pick_place_verify_shifted.wbt')
        with alternate.open('x',encoding='utf-8') as f:
            f.write(text.replace(before,'translation 0.35 0.23 0.0255'))
        world=alternate
    with (run/'webots.log').open('wb') as log:
        done=subprocess.run([str(webots),'--batch','--mode=fast','--stdout','--stderr',str(world)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90)
finally:
    if alternate is not None and world==alternate:
        alternate.unlink()
file=run/'result.json'
if not file.is_file():
    print(f'No verification result. See {run / "webots.log"}.')
    raise SystemExit(done.returncode or 3)
result=json.loads(file.read_text(encoding='utf-8'))
print(f'{run.name}: passed={result["passed"]}; XY error={result["xy_error_mm"]:.2f} mm; {file}')
raise SystemExit(done.returncode or (0 if result['passed'] else 2))
