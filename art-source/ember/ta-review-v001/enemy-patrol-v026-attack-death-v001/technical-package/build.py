"""Copy approved rig parts; register combat joints once, never draw animation pixels."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'enemy-patrol-idle-hit-v025'
TEMPLATE=ROOT.parent/'enemy-heavy-attack-death-v019'
OLD=ROOT.parent/'enemy-sequences-v012/output/enemy_patrol'
UNIT='enemy_patrol'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rect=lambda x,y,w,h:[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
for f in ['output/'+UNIT,'reference/'+UNIT,'qa','source','previews']:(ROOT/f).mkdir(parents=True,exist_ok=True)
shutil.copytree(BASE/'source',ROOT/'source',dirs_exist_ok=True)
for name in ['directions_rig.gd','directions_rig.json','pilot_rig.gd','pilot_rigs.json','profile_rig.gd','profile_rig.json','masked_part.gdshader','entity_cutout.gdshader']:
 if (BASE/name).exists():shutil.copy2(BASE/name,ROOT/name)
shutil.copy2(BASE/'rig.gd',ROOT/'setup_rig.gd')
spec=json.loads((BASE/'rig.json').read_text(encoding='utf-8'))
spec['version']='v026-patrol-attack-death'
spec['actions']={
 'attack':dict(frame_count=6,fps=10,loop=False,body_y=[0,0,1,0,1,0],raise_arm=[0,1,3,4,2,0],fold=[0,3,5,5,3,0],roll=[0]*6,power=[1]*6),
 'death':dict(frame_count=8,fps=10,loop=False,body_y=[0,2,4,6,7,7,7,7],raise_arm=[0]*8,fold=[0,5,12,22,30,35,35,35],roll=[0,0,0,22,50,78,88,88],power=[1,.6,.2,0,0,0,0,0])}
arms={
 'down_left':[(rect(39,76,15,14),[50,76],[50,74],[-.25,-1]),(rect(75,76,11,18),[78,78],[78,76],[0,0])],
 'up_left':[(rect(75,77,11,13),[79,78],[78,76],[-.25,-1]),(rect(42,78,13,17),[52,80],[54,77],[0,0])],
 'up':[([[75,77],[86,77],[86,92],[76,92],[76,84],[75,84]],[79,79],[78,76],[0,-1]),(rect(41,77,13,15),[49,79],[50,76],[0,0])],
 'up_right':[(rect(73,79,16,15),[77,81],[75,78],[.25,-1]),(rect(46,75,11,10),[52,77],[52,74],[0,0])],
 'down_right':[(rect(44,75,12,18),[51,77],[51,74],[.25,-1]),(rect(75,76,11,18),[79,78],[78,75],[0,0])],
 'left':[([[48,76],[60,76],[60,84],[57,84],[57,90],[48,90]],[55,81],[55,78],[-.25,-1]),(rect(57,84,8,11),[60,85],[61,82],[0,0])],
 'right':[(rect(62,82,13,13),[67,83],[65,80],[.25,-1]),(rect(52,77,11,7),[57,79],[58,77],[0,0])]}
spec['combat']={}
# 一次登记的接触轨迹：起初由外侧靴沿承重，末段由折叠前臂接触地面。
# 这些是动画键值，不在播放/导出时按包围盒逐帧重对齐。
ground_keys={
 'down_left':[80,82,84,84,87,86,86,86],
 'up_left':[80,82,84,85,85,88,89,89],
 'up':[80,82,84,84,86,86,86,86],
 'up_right':[80,82,84,84,86,88,89,89],
 'down_right':[80,82,84,83,85,87,87,87],
 'left':[80,82,84,86,87,91,93,93],
 'right':[80,82,84,86,91,94,94,94]}
contact_pixels={'down_left':[80,76],'up_left':[49,79],'up':[46,78],'up_right':[49,75],'down_right':[80,76],'left':[74,71],'right':[73,81]}
for d in spec['configs']:
 definitions=[]
 for i,(poly,pivot,shoulder,raise_vector) in enumerate(arms[d]):
  # 侧面隐藏轴在中性时起终点重合；仅前臂发生位移时露出连接，不扩宽原轮廓。
  socket_start=pivot if (d=='left' and i==0) or (d=='right' and i==1) else shoulder
  definitions.append(dict(id='gun' if i==0 else 'claw',polygon=poly,pivot=pivot,shoulder=shoulder,socket_start=socket_start,raise_vector=raise_vector,fold_sign=-1 if pivot[0]<64 else 1,socket_uv=[shoulder[0]-1,shoulder[1],2,2],socket_width=3))
 spec['combat'][d]=dict(arms=definitions,ownership_transfers=[[75,82]] if d=='up' else [],fall_sign=-1 if d in ['up_left','up','up_right'] else 1,fall_origin_y=ground_keys[d][-1],fall_origin_y_keys=ground_keys[d],final_contact_source=dict(part='body' if d in ['left','right'] else 'claw',source_pixel=contact_pixels.get(d),floor_y=104),sensor_rect={'down_left':[56,59,15,6],'down_right':[59,59,15,6],'left':[50,59,9,7],'right':[62,59,12,7]}.get(d,[0,0,0,0]))
spec['preserved']=[]
for d in ['down','down_left','left','up_left','up','up_right','right','down_right']:shutil.copy2(BASE/'output'/UNIT/f'neutral_{d}.png',ROOT/'output'/UNIT/f'neutral_{d}.png')
for kind in spec['actions']:
 action=kind+'_down';dst=ROOT/'output'/UNIT/action
 shutil.copytree(OLD/action,dst,dirs_exist_ok=True);shutil.copy2(OLD/(action+'.png'),dst.with_suffix('.png'));shutil.copy2(dst.with_suffix('.png'),ROOT/'reference'/UNIT/(action+'.png'))
 spec['preserved'].append(dict(action=action,atlas_sha256=sha(dst.with_suffix('.png')),frame_hashes=[sha(dst/f'f{i:02}.png') for i in range(spec['actions'][kind]['frame_count'])]))
(ROOT/'rig.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
for name in ['export.gd','verify.gd','capture.gd','preview.gd','preview.tscn','previews/index.html']:
 t=(TEMPLATE/name).read_text(encoding='utf-8').replace('v019','v026').replace('enemy_tracked_heavy',UNIT).replace('heavy','patrol').replace('HEAVY','PATROL').replace('重装机','巡逻兵')
 t=t.replace('攻击炮口回坐；死亡炮塔下沉、炮管垂落，履带接地不移动。后方炮口保持遮挡；各方向使用固定零件。','攻击抬起前臂投射器后复位；死亡屈膝、侧倒并落地停留。各方向使用固定零件。')
 (ROOT/name).write_text(t,encoding='utf-8')
shutil.copy2(BASE/'project.godot',ROOT/'project.godot')
p=ROOT/'project.godot';p.write_text(p.read_text(encoding='utf-8').replace('idle and hit v025','attack and death v026'),encoding='utf-8')
t=(BASE/'pixel_audit.py').read_text(encoding='utf-8');(ROOT/'pixel_audit.py').write_text(t,encoding='utf-8')
t=(ROOT.parent/'enemy-cutter-attack-death-v024/inspect_actions.gd').read_text(encoding='utf-8').replace('enemy_cutter',UNIT).replace('16,48,96,64','8,40,112,80').replace('96*','112*').replace('64*','80*').replace(' )*96',' )*112').replace(' )*64',' )*80')
(ROOT/'inspect_actions.gd').write_text(t,encoding='utf-8')
print('P26_COMBAT_PREPARED',len(spec['configs']),'new directions')

# 真实计数按本次已登记方向推导。

p=ROOT/'export.gd'
t=p.read_text(encoding='utf-8')
t=t.replace('14 new clips / 98 new frames; two down actions preserved',f'{len(spec["configs"])*2} new clips / {len(spec["configs"])*14} new frames; two down actions preserved')
t=t.replace('fourteen new clips; two preserved; sixteen animations',f'{len(spec["configs"])*2} new clips; two preserved; {len(spec["configs"])*2+2} animations')
p.write_text(t,encoding='utf-8')
