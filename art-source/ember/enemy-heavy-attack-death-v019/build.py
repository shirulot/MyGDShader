"""Fixed ownership and pose registration for the heavy robot; no raster painting."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'enemy-heavy-idle-hit-v015'
TEMPLATE=ROOT.parent/'enemy-drone-attack-death-v018'
OLD=ROOT.parent/'enemy-sequences-v012/output/enemy_tracked_heavy'
UNIT='enemy_tracked_heavy'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=json.loads((BASE/'rig.json').read_text(encoding='utf-8'))
for key in ['frame_count','fps','loop','body_y']:spec.pop(key,None)
spec['version']='v019-heavy-attack-death'
spec['method']='Fixed tower, lower chassis, tracks and cannon; hidden mount source registered once per direction; no frame regeneration or image mirroring.'
spec['actions']={
 'attack':dict(frame_count=6,fps=10,loop=False,body_y=[0,0,0,1,1,0],recoil=[0,1,0,2,1,0],gun_roll=[0]*6,gun_y=[0]*6,power=[1]*6),
 'death':dict(frame_count=8,fps=10,loop=False,body_y=[0,2,5,9,13,12,13,13],recoil=[0]*8,gun_roll=[0,0,3,7,12,12,12,12],gun_y=[0,0,0,0,1,1,1,1],power=[1,.7,.3,0,0,0,0,0])}
west=[[34,67],[38,67],[38,71],[36,75],[35,80],[35,88],[32,92],[30,90],[30,84],[24,84],[24,74],[29,74],[30,71]]
gun={
 'down_left':dict(polygon=[[50,69],[58,69],[60,73],[60,87],[57,92],[52,91],[47,84],[47,77]],pivot=[56,72],recoil=[1,-1],droop_sign=-1),
 'down_right':dict(polygon=[[67,69],[74,69],[77,73],[80,80],[79,84],[75,87],[74,92],[69,93],[65,89],[65,79]],pivot=[69,71],recoil=[-1,-1],droop_sign=1),
 'left':dict(polygon=west,pivot=[37,73],recoil=[1,0],droop_sign=-1),
 'right':dict(polygon=[[123-x,y] for x,y in west],pivot=[86,73],recoil=[-1,0],droop_sign=1)}
hidden=json.loads((ROOT/'source/hidden_registration.json').read_text(encoding='utf-8'))
for direction,c in spec['configs'].items():
 c['tower_bottom']={'down_left':78,'down_right':78,'up_left':78,'up_right':78,'up':83,'left':79,'right':79}[direction]
 c['gun']=gun.get(direction,dict(polygon=[],pivot=[64,72],recoil=[0,0],droop_sign=0))
 c['gun']['housing_polygon']=c['gun']['polygon']
 # The cream receiver plate stays on the chassis. Only the short blue-gray barrel recoils/droops.
 barrel={
  'left':([[23,73],[31,73],[31,87],[23,87]],[30,80]),
  'right':([[92,73],[100,73],[100,87],[92,87]],[93,80]),
  'down_left':([[51,76],[55,76],[58,79],[58,84],[55,87],[51,87],[48,84],[48,79]],[55,77]),
  'down_right':([[71,76],[75,77],[78,80],[78,84],[75,87],[71,85],[68,81],[68,78]],[70,77])}
 if direction in barrel:c['gun']['polygon'],c['gun']['pivot']=barrel[direction]
 c['gun']['fixed_receiver_pixels']=[[46,76],[46,77]] if direction=='down_left' else []
 # E 的固定内壁只属于枪根；炮口后坐腾出的最外端应让出轮廓。
 c['gun']['socket_clip_rect']=[92,73,3,14] if direction=='right' else [0,0,128,128]
 c['sensor_rect']={'down_left':[51,62,9,3],'down_right':[66,62,10,3],'left':[38,63,3,3],'right':[84,63,3,3]}.get(direction,[0,0,0,0])
 i=spec['directions'].index(direction)
 c['hidden']=dict(source_rect=hidden['regions'][i],scale=hidden['common_scale'],target_bottom=[64,98],canonical_y_min=72)
spec['preserved']=[]
for folder in ['output/'+UNIT,'reference/'+UNIT,'qa','previews']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
for direction in spec['directions']:
 shutil.copy2(ROOT/'source'/f'{direction}.png',ROOT/'output'/UNIT/f'neutral_{direction}.png')
for kind in spec['actions']:
 action=kind+'_down';dst=ROOT/'output'/UNIT/action
 shutil.copytree(OLD/action,dst,dirs_exist_ok=True)
 shutil.copy2(OLD/(action+'.png'),dst.with_suffix('.png'))
 shutil.copy2(dst.with_suffix('.png'),ROOT/'reference'/UNIT/(action+'.png'))
 spec['preserved'].append(dict(action=action,atlas_sha256=sha(dst.with_suffix('.png')),frame_hashes=[sha(dst/f'f{i:02}.png') for i in range(spec['actions'][kind]['frame_count'])]))
(ROOT/'rig.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
for name in ['export.gd','verify.gd','capture.gd','preview.gd','preview.tscn','previews/index.html']:
 text=(TEMPLATE/name).read_text(encoding='utf-8').replace('v018','v019').replace('enemy_scout_drone',UNIT).replace('DRONE','HEAVY').replace('侦察机','重装机')
 text=text.replace('攻击短促下探后复位；死亡断电、转子减速、整机刚性坠落并停在地面。隐藏的探头保留遮挡；无逐帧生图。','攻击炮口回坐；死亡炮塔下沉、炮管垂落，履带接地不移动。后方炮口保持遮挡；各方向使用固定零件。')
 text=text.replace('v019-drone-attack-death','v019-heavy-attack-death').replace('idle正常循环；hit播放一次后停在恢复帧。','attack和death均播放一次后停在末帧。').replace('HEAVY_IDLE_HIT_EXPORTED','HEAVY_ATTACK_DEATH_EXPORTED')
 (ROOT/name).write_text(text,encoding='utf-8')
shutil.copy2(BASE/'pixel_audit.py',ROOT/'pixel_audit.py')
shutil.copy2(BASE/'masked_part.gdshader',ROOT/'masked_part.gdshader')
print('HEAVY_V019_PREPARED')
