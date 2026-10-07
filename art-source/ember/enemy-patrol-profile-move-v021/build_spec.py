"""Register two profile walks with fixed replacement lower-leg parts for TA review."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
UNIT='enemy_patrol'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rect(x,y,w,h):return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
def part(name,poly,pivot,end=None,exclude=None,z=0,source='canonical'):
    return dict(id=name,polygon=poly,pivot=pivot,end=end,exclude=exclude or [],z=z,source_kind=source)
def leg(side,hip,knee,ankle,cap,thigh,shin,foot,z,sole=7,source='canonical'):
    cap_shape=rect(*cap)
    parts=[part(side+'_thigh',rect(*thigh),hip,[knee[0],cap[1]],[cap_shape],z,source),part(side+'_shin',rect(*shin),[knee[0],shin[1]],[ankle[0],foot[1]],z=z,source=source),part(side+'_cap',cap_shape,knee,z=z+2,source=source),part(side+'_foot',rect(*foot),ankle,z=z+1,source=source)]
    return parts,dict(hip=hip,knee=knee,ankle=ankle,sole_offset=[0,sole])
definitions={
 'left':{
  'left':([66,81],[68,90],[68,99],[61,88,11,6],[61,81,11,7],[61,94,11,2],[55,96,18,32],4,5,'near'),
  'right':([66,78],[68,87],[68,96],[61,85,11,6],[61,78,11,7],[61,91,11,2],[55,93,18,35],-4,5,'far')},
 'right':{
  'right':([59,81],[58,90],[57,99],[54,88,11,6],[54,81,11,7],[54,94,11,2],[53,96,17,32],4,5,'near'),
  'left':([61,78],[60,87],[59,96],[56,85,11,6],[56,78,11,7],[56,91,11,2],[55,93,17,35],-4,5,'far')}
}
configs={}
for direction,defs in definitions.items():
    parts=[];legs={}
    for side,args in defs.items():
        p,l=leg(side,*args);parts+=p;legs[side]=l
    # 侧向旧图两靴遮挡粘连，无法可靠拆出闭合轮廓。两腿均使用固定零件母稿，
    # 头身手臂保持原像素；腿部变化单独做绑定差异与中性对照并送总监复审。
    protected=[rect(49,76,11,13),rect(58,77,14,7),rect(57,84,8,11)] if direction=='left' else [rect(62,74,12,9),rect(62,82,13,11),rect(52,77,11,7)]
    configs[direction]=dict(source=f'res://source/{direction}.png',source_sha256=sha(ROOT/'source'/f'{direction}.png'),far_source=f'res://source/far_registered_{direction}.png',far_sha256=sha(ROOT/'source'/f'far_registered_{direction}.png'),near_source=f'res://source/far_registered_near_{direction}.png',near_sha256=sha(ROOT/'source'/f'far_registered_near_{direction}.png'),parts=parts,legs=legs,heading=[-1,0] if direction=='left' else [1,0],protected_body_polygons=protected,occluded_original_polygons=[rect(50,84,27,44)])
preserved=[]
for direction,folder in [('down','enemy-sequences-v012'),('down_right','enemy-eight-directions-v013-pilot-patrol-v001')]:
    name='move_'+direction;src=ROOT.parent/folder/'output'/UNIT/name;dst=ROOT/'output'/UNIT/name
    shutil.copytree(src,dst,dirs_exist_ok=True);shutil.copy2(src.with_suffix('.png'),dst.with_suffix('.png'))
    preserved.append(dict(action=name,atlas_sha256=sha(dst.with_suffix('.png')),frame_hashes=[sha(dst/f'f{i:02}.png') for i in range(8)]))
for direction in ['down','down_left','left','up_left','up','up_right','right','down_right']:shutil.copy2(ROOT/'source'/f'{direction}.png',ROOT/'output'/UNIT/f'neutral_{direction}.png')
for name in ['move_down.png','neutral_down.png']:shutil.copy2(ROOT/'output'/UNIT/name,ROOT/'reference'/UNIT/name)
for direction in ['down','down_left','left','up_left','up','up_right','right','down_right']:
    shutil.copy2(ROOT/'source'/f'{direction}.png',ROOT/'reference'/UNIT/f'neutral_{direction}.png')
spec=dict(version='v021-patrol-two-profile-moves',unit=UNIT,canvas=[128,128],root=[64,104],directions=['down','left','right','down_right'],outside_batch=['down_left','up_left','up','up_right'],configs=configs,preserved=preserved,phases=json.loads((ROOT.parent/'enemy-patrol-actions-v008/rig.json').read_text(encoding='utf-8'))['phases'])
(ROOT/'rig.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('PATROL_PROFILE_RIG_REGISTERED')
