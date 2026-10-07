"""Prepare idle/hit from approved move rigs, keeping profile expansion behind its TA gate."""
from pathlib import Path
import argparse,hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
TEMPLATE=ROOT.parent/'enemy-cutter-idle-hit-v023'
MOVE=ROOT.parent/'enemy-patrol-directions-move-v020-review-v002'
PILOT=ROOT.parent/'enemy-eight-directions-v013-pilot-patrol-v001'
PROFILE=ROOT.parent/'enemy-patrol-profile-move-v021-review-v003'
OLD=ROOT.parent/'enemy-sequences-v012/output/enemy_patrol'
UNIT='enemy_patrol'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
args=argparse.ArgumentParser();args.add_argument('--include-profiles',action='store_true');opt=args.parse_args()
for f in ['output/'+UNIT,'reference/'+UNIT,'qa','source','source/registered','previews']:(ROOT/f).mkdir(parents=True,exist_ok=True)
directions=['down','down_left','left','up_left','up','up_right','right','down_right']
base=json.loads((MOVE/'rig.json').read_text(encoding='utf-8'))
(ROOT/'directions_rig.json').write_text(json.dumps(base,indent=2),encoding='utf-8')
(ROOT/'directions_rig.gd').write_text((MOVE/'rig.gd').read_text(encoding='utf-8').replace('res://rig.json','res://directions_rig.json'),encoding='utf-8')
pilot=json.loads((PILOT/'pilot_rigs.json').read_text(encoding='utf-8'));pilot['units']=[u for u in pilot['units'] if u['unit']==UNIT]
(ROOT/'pilot_rigs.json').write_text(json.dumps(pilot,indent=2),encoding='utf-8')
shutil.copy2(TEMPLATE/'pilot_rig.gd',ROOT/'pilot_rig.gd')
p=pilot['units'][0]['source'].removeprefix('res://');shutil.copy2(PILOT/p,ROOT/p)
configs={d:dict(source=f'res://source/{d}.png',base='direction') for d in base['configs']}
configs['down_right']=dict(source='res://source/down_right.png',base='pilot')
for d in directions:
 src=MOVE/'source'/f'{d}.png'
 if d=='down_right':src=PILOT/'output'/UNIT/'rig_neutral_down_right.png'
 shutil.copy2(src,ROOT/'source'/f'{d}.png');shutil.copy2(src,ROOT/'output'/UNIT/f'neutral_{d}.png')
if opt.include_profiles:
 ledger=json.loads((ROOT.parent/'enemy-eight-directions-v013/animation_review_ledger.json').read_text(encoding='utf-8'))
 gate=next((b for b in ledger['batches'] if b['folder']==PROFILE.name),None)
 assert gate and gate['status']=='TA_APPROVED','Profile move approval is required before expanding profile actions'
 # Caller only enables this after explicit TA approval of the exact frozen profile package.
 pr=json.loads((PROFILE/'rig.json').read_text(encoding='utf-8'))
 (ROOT/'profile_rig.json').write_text(json.dumps(pr,indent=2),encoding='utf-8')
 (ROOT/'profile_rig.gd').write_text((PROFILE/'rig.gd').read_text(encoding='utf-8').replace('res://rig.json','res://profile_rig.json'),encoding='utf-8')
 for d in ['left','right']:
  configs[d]=dict(source=f'res://source/{d}.png',base='profile')
  for kind in ['body','near','far']:shutil.copy2(PROFILE/'source'/f'c002_{d}_{kind}.png',ROOT/'source'/f'c002_{d}_{kind}.png')
  shutil.copy2(PROFILE/'source'/f'c002_neutral_{d}.png',ROOT/'source'/f'c002_neutral_{d}.png')
  shutil.copy2(PROFILE/'output'/UNIT/f'neutral_{d}.png',ROOT/'source'/f'{d}.png')
  shutil.copy2(ROOT/'source'/f'{d}.png',ROOT/'output'/UNIT/f'neutral_{d}.png')
spec=dict(version='v025-patrol-idle-hit',unit=UNIT,canvas=[128,128],root=[64,104],directions=[d for d in directions if d=='down' or d in configs],configs=configs,preserved=[],actions={
 'idle':dict(fps=4,loop=True,body=[[0,0],[0,-1],[0,0],[0,1]]),
 'hit':dict(fps=12,loop=False,body=[[0,0],[-1,1],[1,0],[0,0]])})
for kind in spec['actions']:
 action=kind+'_down';dst=ROOT/'output'/UNIT/action
 shutil.copytree(OLD/action,dst,dirs_exist_ok=True);shutil.copy2(OLD/(action+'.png'),dst.with_suffix('.png'))
 shutil.copy2(dst.with_suffix('.png'),ROOT/'reference'/UNIT/(action+'.png'))
 spec['preserved'].append(dict(action=action,atlas_sha256=sha(dst.with_suffix('.png')),frame_hashes=[sha(dst/f'f{i:02}.png') for i in range(4)]))
for d,c in configs.items():c['source_sha256']=sha(ROOT/'source'/f'{d}.png')
(ROOT/'rig.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
for name in ['export.gd','verify.gd','capture.gd','preview.gd','preview.tscn','project.godot','masked_part.gdshader','entity_cutout.gdshader','pixel_audit.py','build_web.py']:
 t=(TEMPLATE/name).read_text(encoding='utf-8').replace('v023','v025').replace('enemy_cutter',UNIT).replace('cutter','patrol').replace('CUTTER','PATROL').replace('切割机','巡逻兵').replace('四足保持支撑','双足保持支撑')
 (ROOT/name).write_text(t,encoding='utf-8')
t=(ROOT.parent/'enemy-patrol-profile-move-v021/inspect_actions.gd').read_text(encoding='utf-8').replace('range(8)','range(int(clip.frame_count))')
(ROOT/'inspect_actions.gd').write_text(t,encoding='utf-8')
print('P25_PREPARED',len(configs),'new directions; profiles included:',opt.include_profiles)

# 真实计数按本次已登记方向推导。

p=ROOT/'export.gd'
t=p.read_text(encoding='utf-8')
t=t.replace('14 new clips / 56 new frames; two down actions preserved',f'{len(spec["configs"])*2} new clips / {len(spec["configs"])*8} new frames; two down actions preserved')
t=t.replace('fourteen new clips; two preserved; sixteen animations',f'{len(spec["configs"])*2} new clips; two preserved; {len(spec["configs"])*2+2} animations')
p.write_text(t,encoding='utf-8')
