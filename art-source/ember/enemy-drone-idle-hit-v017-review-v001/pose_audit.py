"""Read-only rigid transform, fixed fan-axis spacing, and exact hit recovery checks."""
from pathlib import Path
import hashlib,json,math
from PIL import Image
ROOT=Path(__file__).resolve().parent
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
records=[];recovery=[]
for clip in catalog['clips']:
    for pose in clip['poses']:
        x,y=pose['body_basis_x'],pose['body_basis_y']
        error=max(abs(math.hypot(*x)-1),abs(math.hypot(*y)-1),abs(x[0]*y[0]+x[1]*y[1]),abs(x[0]*y[1]-x[1]*y[0]-1))
        first,second=pose['fans']
        rest=math.dist(first['center'],second['center'])
        current=math.dist(pose['axis_world'][first['id']],pose['axis_world'][second['id']])
        passed=error<1e-5 and abs(rest-current)<1e-4
        records.append(dict(action=clip['action'],frame=pose['frame'],rigid_error=error,
                            source_axis_distance=rest,posed_axis_distance=current,passed=passed))
    if clip['action'].startswith('hit_'):
        folder=ROOT/'output/enemy_scout_drone'/clip['action']
        first=Image.open(folder/'f00.png').convert('RGBA')
        last=Image.open(folder/'f03.png').convert('RGBA')
        passed=first.tobytes()==last.tobytes()
        recovery.append(dict(action=clip['action'],first_last_rgba_identical=passed))
passed=all(x['passed'] for x in records) and all(x['first_last_rgba_identical'] for x in recovery)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=hashlib.sha256((ROOT/'output/catalog.json').read_bytes()).hexdigest(),
            scope='Rigid metadata and exact rendered hit recovery; visual behavior requires TA review',poses=records,hit_recovery=recovery)
(ROOT/'qa/pose_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],new_pose_checks=len(records),hit_recovery_checks=len(recovery))))
raise SystemExit(0 if passed else 1)
