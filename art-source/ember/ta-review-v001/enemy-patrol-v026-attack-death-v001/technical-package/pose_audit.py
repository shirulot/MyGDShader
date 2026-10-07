"""Read-only checks of combat endpoints, fixed armor and registered floor contacts."""
from pathlib import Path
from PIL import Image
import hashlib,json,math
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
catalog=json.loads((ROOT/'output/catalog.json').read_text(encoding='utf-8'))
directions=json.loads((ROOT/'directions_rig.json').read_text(encoding='utf-8'))
pilot=json.loads((ROOT/'pilot_rigs.json').read_text(encoding='utf-8'))['units'][0]
profile=json.loads((ROOT/'profile_rig.json').read_text(encoding='utf-8')) if (ROOT/'profile_rig.json').exists() else {}
records=[]
def basis(t,v):return [t['basis_x'][j]*v[0]+t['basis_y'][j]*v[1] for j in (0,1)]
for clip in catalog['clips']:
    kind=clip['action'].split('_')[0];d=clip['direction']
    frames=[Image.open(ROOT/'output/enemy_patrol'/clip['action']/f'f{i:02}.png').convert('RGBA') for i in range(clip['frame_count'])]
    if d=='down':
        records.append(dict(action=clip['action'],passed=True,preserved_down=True));continue
    cfg=pilot if d=='down_right' else (profile['configs'][d] if spec['configs'][d]['base']=='profile' else directions['configs'][d])
    neutral=Image.open(ROOT/spec['configs'][d]['source'].removeprefix('res://')).convert('RGBA')
    bind=frames[0].tobytes()==neutral.tobytes()
    endpoint=frames[0].tobytes()==frames[-1].tobytes() if kind=='attack' else frames[-2].tobytes()==frames[-1].tobytes()
    bounds=[im.getchannel('A').getbbox() for im in frames]
    floor=all(b[3]<=104 for b in bounds)
    corpse_ground=kind!='death' or bounds[-1][3]==104
    rigid=True;errors=[];source_exact=sha(ROOT/spec['configs'][d]['source'].removeprefix('res://'))==spec['configs'][d]['source_sha256']
    fixed_supports=True;foot_records=[]
    for i,pose in enumerate(clip['poses']):
        for name,t in pose['part_transforms'].items():
            if name.endswith(('_thigh','_shin')):continue
            x,y=t['basis_x'],t['basis_y']
            rigid &= abs(math.hypot(*x)-1)<1e-5 and abs(math.hypot(*y)-1)<1e-5 and abs(x[0]*y[0]+x[1]*y[1])<1e-5
        for side,leg in cfg['legs'].items():
            actual=pose['supports'][side]
            t=pose['part_transforms'][side+'_foot']
            if actual['support']:
                fixed_supports &= math.dist(actual['ankle'],leg['ankle'])<1e-5
                fixed_supports &= abs(t['basis_x'][0]-1)<1e-5 and abs(t['basis_y'][1]-1)<1e-5
            for p in cfg['parts']:
                if p['id'] not in (side+'_thigh',side+'_shin'):continue
                anchor='knee' if p['id'].endswith('_thigh') else 'ankle'
                offset=basis(t,[p['end'][j]-leg[anchor][j] for j in (0,1)])
                expected=[actual[anchor][j]+offset[j] for j in (0,1)]
                segment=pose['part_transforms'][p['id']]
                mapped=basis(segment,[p['end'][j]-p['pivot'][j] for j in (0,1)])
                mapped=[mapped[j]+segment['position'][j] for j in (0,1)]
                errors.append(math.dist(expected,mapped))
    sensor=kind!='death' or all(p['sensor_power']==0 for p in clip['poses'][3:])
    release=kind!='attack' or clip['poses'][3].get('event')=='attack_release_visual'
    fallen=kind!='death' or (clip['poses'][-1]['roll_degrees']==88 and bounds[-1][2]-bounds[-1][0]>bounds[-1][3]-bounds[-1][1])
    checks=[bind,endpoint,floor,corpse_ground,rigid,source_exact,fixed_supports,sensor,release,fallen,max(errors)<1e-4]
    records.append(dict(action=clip['action'],neutral_exact=bind,endpoints_equal=endpoint,opaque_bounds=bounds,final_contact_on_ground=corpse_ground,rigid_armor=rigid,source_exact=source_exact,supported_ankles_fixed=fixed_supports,connector_max_error=max(errors),sensor_off_after_f2=sensor,attack_release=release,corpse_reads_side_fall=fallen,passed=all(checks)))
passed=all(r['passed'] for r in records)
report=dict(status='PASS' if passed else 'FAIL',catalog_sha256=sha(ROOT/'output/catalog.json'),records=records,limits='After the first three death frames the character tips and the feet leave their original contacts. The fall trajectory uses fixed registered key values; no per-frame bounding-box recentering. RGB is unchanged except the registered red sensor losing power. Source UV joint instances can expose extra pixels. Author checks do not constitute TA approval.')
(ROOT/'qa/pose_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(status=report['status'],actions=len(records),failures=[r for r in records if not r['passed']])))
raise SystemExit(not passed)
