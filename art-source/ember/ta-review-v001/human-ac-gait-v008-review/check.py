"""独立核对v008导出、静态部件保持及量化后的重心表现；只读作者目录。"""
from pathlib import Path
from PIL import Image
import hashlib, json, math, shutil

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent.parent/'human-ac-gait-v008'
OLD=SOURCE.parent/'human-ac-rig-pilot-v006'
entries=[]
for path in sorted(SOURCE.rglob('*')):
    if not path.is_file(): continue
    rel=path.relative_to(SOURCE); data=path.read_bytes(); target=HERE/'submitted'/rel
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists(): assert target.read_bytes()==data
    else: shutil.copyfile(path,target)
    entries.append({'path':rel.as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
manifest=(json.dumps(entries,ensure_ascii=False,indent=2)+'\n').encode()
(HERE/'source-manifest.json').write_bytes(manifest)
snap=HERE/'submitted'
atlas=Image.open(snap/'final/A-walk-down_right-gait-v008.png').convert('RGBA')
assert atlas.size==(512,96)
assert set(atlas.getchannel('A').getdata())=={0,255}
frames=[atlas.crop((i*64,0,(i+1)*64,96)) for i in range(8)]
assert len({im.tobytes() for im in frames})==8
assert Image.open(snap/'qa/contact.png').convert('RGBA').tobytes()==atlas.resize((2048,384),Image.Resampling.NEAREST).tobytes()
parts=list((snap/'parts').glob('*.png'))
assert len(parts)==12
assert all(p.read_bytes()==(OLD/'parts'/p.name).read_bytes() for p in parts)
poses=json.loads((snap/'qa/poses.json').read_text(encoding='utf-8'))
rounding={key:[list(map(lambda x:math.floor(x+.5),p[key])) for p in poses] for key in ['head','torso']}
errors=[]; contacts={}
for side in ['near','far']:
    points=[]
    for i,p in enumerate(poses):
        q=p[side]; s=q['spatial']
        errors.extend([abs(math.dist(s['hip'],s['knee'])-12),abs(math.dist(s['knee'],s['ankle'])-11)])
        if q['support']: points.append([q['ankle'][0]+i/8*13,q['ankle'][1]+i/8*4.6])
    contacts[side]={'positions':points,'error':max(math.dist(points[0],v) for v in points)}
result={'files':len(entries),'manifest_sha256':hashlib.sha256(manifest).hexdigest(),'parts_unchanged_vs_v006':12,
        'frames':8,'colors':len({x[:3] for x in atlas.getdata() if x[3]}),'rounded_positions':rounding,
        'head_region_unique_rgba':len({im.crop((18,0,45,29)).tobytes() for im in frames}),
        'spatial_bone_error':max(errors),'support_samples':contacts,
        'far_forearm_in_front':[p['far']['armForward']>0 for p in poses],
        'continuous_visual_or_godot_pass':False,'scope':'export_and_recorded_pose_checks'}
(HERE/'technical.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
