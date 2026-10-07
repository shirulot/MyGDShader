"""Use the exact C002 v003 approved visible body and leg instances for both walks."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parent
CAL=ROOT.parent/'enemy-patrol-profile-calibration-v021-c002-review-v003'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rect=lambda x,y,w,h:[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
data=json.loads((CAL/'calibration.json').read_text(encoding='utf-8'))
spec=json.loads((ROOT/'rig.json').read_text(encoding='utf-8'))
spec['version']='v021-patrol-two-profile-moves-v003-c002-boot-ownership'
spec['calibration_zip_sha256']='87d0ecf437c93451eddcdad59387f6f03191efcdfdfa1cb197b6e41e819f4ab2'
for direction,c in data['configs'].items():
 cfg=spec['configs'][direction]
 cfg['parts']=[];cfg['legs']={};cfg['occluded_original_polygons']=[]
 for kind in ['body','near','far']:
  dst=ROOT/'source'/f'c002_{direction}_{kind}.png'
  shutil.copy2(CAL/'output'/f'{direction}_{kind}.png',dst)
  cfg[kind+'_source']='res://source/'+dst.name
  cfg[kind+'_sha256']=sha(dst)
 shutil.copy2(CAL/'output'/f'neutral_{direction}.png',ROOT/'source'/f'c002_neutral_{direction}.png')
 cfg['approved_bind_source']=f'res://source/c002_neutral_{direction}.png'
 near_side='left' if direction=='left' else 'right'
 for side in ['left','right']:
  kind='near' if side==near_side else 'far'
  offset=[0,0] if kind=='near' else c['offset']
  shift=lambda p:[p[0]+offset[0],p[1]+offset[1]]
  shape=lambda a:[shift(p) for p in a]
  cap=shape(c['cap']);foot=shape(c['foot'])
  if direction=='right':
   # (61,94)/(61,95)是浅色靴口硬边，必须与靴刚性平移，不能归入仿射胫连接。
   foot=shape([[57,94],[62,94],[62,96],[65,96],[65,99],[67,99],[67,104],[53,104],[53,95],[57,95]])
  cap_top=min(p[1] for p in cap);cap_bottom=max(p[1] for p in cap)
  hip=shift(c['socket_start'])
  knee=shift([68,89] if direction=='left' else [58,88])
  ankle=shift([67,94] if direction=='left' else [58,94])
  z=4 if kind=='near' else -4
  defs=[
   dict(id=side+'_thigh',polygon=rect(0,0,128,cap_bottom),pivot=hip,end=[knee[0],cap_top],exclude=[cap,foot],z=z,source_kind=kind),
   dict(id=side+'_shin',polygon=rect(0,cap_bottom,128,128-cap_bottom),pivot=[knee[0],cap_bottom],end=ankle,exclude=[foot],z=z,source_kind=kind),
   dict(id=side+'_cap',polygon=cap,pivot=knee,end=None,exclude=[],z=z+2,source_kind=kind),
   dict(id=side+'_foot',polygon=foot,pivot=ankle,end=None,exclude=[cap],z=z+1,source_kind=kind)]
  cfg['parts'].extend(defs)
  # sole_offset保留原步态登记；可见足底另登记真实不透明源像素中心，避免用透明斜底点作证据。
  probe=shift([64.5,103.5] if direction=='left' else [63.5,103.5])
  cfg['legs'][side]=dict(hip=hip,knee=knee,ankle=ankle,sole_offset=[0,10],
                       nominal_sole_note='Kinematic registration at bottom edge; not necessarily an opaque source pixel.',
                       visible_sole_source_pixel_center=probe)
 cfg['source_note']='Body/near/far are byte-exact C002 v003 approved GPU exports; near/far reuse the same original same-direction visible leg with explicit integer depth offset. No rejected v001 generated boot is used.'
(ROOT/'rig.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('P21_C002_V003_FIXED_PARTS_REGISTERED')
