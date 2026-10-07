"""Prepare fixed-source attack/death rigs; copies files and writes metadata only."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'enemy-drone-idle-hit-v017'
OLD=ROOT.parent/'enemy-sequences-v012'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for folder in ['source','output/enemy_scout_drone','reference/enemy_scout_drone','qa','previews']:
    (ROOT/folder).mkdir(parents=True,exist_ok=True)
for path in (BASE/'source').glob('*.png'):
    shutil.copy2(path,ROOT/'source'/path.name)
spec=json.loads((BASE/'rig.json').read_text(encoding='utf-8'))
spec['version']='v018-drone-attack-death'
spec['actions']={
    'attack':dict(frame_count=6,fps=10,loop=False,body_y=[0,0,1,2,1,0],probe_y=[0,0,1,2,1,0],rotor_angles=[0,22.5,45,67.5,22.5,0],power=[1]*6),
    'death':dict(frame_count=8,fps=10,loop=False,drop_fraction=[0,0.125,1/3,7/12,5/6,1,1,1],probe_y=[0]*8,rotor_angles=[0,25,42,52,58,60,60,60],power=[1,.6,.2,0,0,0,0,0])}
spec['preserved']=[]
for action in spec['actions']:
    old=OLD/'output/enemy_scout_drone'/f'{action}_down'
    dest=ROOT/'output/enemy_scout_drone'/f'{action}_down'
    shutil.copytree(old,dest,dirs_exist_ok=True)
    shutil.copy2(old.with_suffix('.png'),dest.with_suffix('.png'))
    shutil.copy2(old.with_suffix('.png'),ROOT/'reference/enemy_scout_drone'/f'{action}_down.png')
    spec['preserved'].append(dict(action=action+'_down',atlas_sha256=sha(dest.with_suffix('.png')),frame_hashes=[sha(dest/f'f{i:02}.png') for i in range(spec['actions'][action]['frame_count'])]))
for direction,config in spec['configs'].items():
    # All body/pod geometry remains rigid. The falling assembly lands with its
    # lowest opaque edge at the same ground plane, without per-frame resizing.
    box=Image.open(ROOT/'source'/f'{direction}.png').getchannel('A').getbbox()
    config['ground_edge_y']=box[3]
    config['fall_distance']=104-box[3]
    config['probe_rect']={'down_left':[55,75,6,5],'down_right':[67,75,6,5]}.get(direction,[0,0,0,0])
    config['sensor_rect']={'down_left':[57,67,2,2],'down_right':[69,67,2,2],'right':[73,67,1,2]}.get(direction,[0,0,0,0])
    config['probe_visibility']='exposed_fixed_tip_over_fixed_sleeve' if config['probe_rect'][2] else 'occluded_by_casing_or_near_pod'
spec['death_motion']='Rigid power-loss landing. No hidden pod geometry is fabricated: shell, pods and struts retain approved static geometry; rotor braking and ground contact carry the death action.'
(ROOT/'rig.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
for direction in spec['directions']:
    shutil.copy2(ROOT/'source'/f'{direction}.png',ROOT/'output/enemy_scout_drone'/f'neutral_{direction}.png')
for name in ['project.godot','preview.tscn','pilot_fan.gdshader','pixel_audit.py','verify.gd']:
    text=(BASE/name).read_text(encoding='utf-8').replace('v017','v018').replace('idle_hit','attack_death').replace('idle-hit','attack-death')
    (ROOT/name).write_text(text,encoding='utf-8')
text=(BASE/'export.gd').read_text(encoding='utf-8')
text=text.replace('v017','v018').replace('idle_hit','attack_death').replace('idle-hit','attack-death')
text=text.replace('56 new frames','98 new frames').replace('待机和受击','攻击和死亡')
text=text.replace('var action:=kind+"_"+direction','var count:int=spec.actions[kind].frame_count\n   var action:=kind+"_"+direction')
text=text.replace('Image.create(512,128','Image.create(count*128,128').replace('range(4)','range(count)')
text=text.replace('Vector2i(index%4*128,index/4*128)','Vector2i(index*128,0)').replace('contact.resize(2048,512','contact.resize(count*512,512').replace('"frame_count":4','"frame_count":count')
(ROOT/'export.gd').write_text(text,encoding='utf-8')
text=(BASE/'preview.gd').read_text(encoding='utf-8')
text=text.replace('v017','v018').replace('idle_hit','attack_death').replace('IDLE + HIT','ATTACK + DEATH')
text=text.replace('"idle"','"attack"').replace('"hit"','"death"').replace('IDLE / 4 FPS','ATTACK / 10 FPS').replace('HIT / 12 FPS','DEATH / 10 FPS')
text=text.replace('Hit is one-shot.','Both actions are one-shot.').replace('action=="death" and target.frame==3','target.frame==frames.get_frame_count(action+"_down")-1')
text=text.replace('posmod(approved.frame+1,4)','posmod(approved.frame+1,frames.get_frame_count(action+"_down"))')
text=text.replace('frame %d / 4','frame %d / %d').replace('target.frame+1,"LOOP" if action=="attack" else "ONE SHOT"','target.frame+1,frames.get_frame_count(action+"_down"),"ONE SHOT"')
(ROOT/'preview.gd').write_text(text,encoding='utf-8')
text=(BASE/'capture.gd').read_text(encoding='utf-8')
text=text.replace('"idle"','"attack"').replace('"hit"','"death"').replace('<5200','<9300')
text=text.replace('var one_shot:bool=key.begins_with("hit_")','var count:int=frames.get_frame_count(actor.animation)')
text=text.replace('seen[key].size()==4','seen[key].size()==count').replace('actor.frame==3','actor.frame==count-1')
text=text.replace(' if one_shot else loops[key]>=1 and finishes[key]==0','')
text=text.replace('DRONE_IDLE_HIT_RUNTIME','DRONE_ATTACK_DEATH_RUNTIME')
(ROOT/'capture.gd').write_text(text,encoding='utf-8')
text=(BASE/'previews/index.html').read_text(encoding='utf-8')
text=text.replace('v017','v018').replace('待机与受击','攻击与死亡').replace('待机循环播放，受击播放一次后停在恢复帧。','攻击与死亡均播放一次后停在末帧。')
text=text.replace('value="idle">待机 · 4 FPS','value="attack">攻击 · 10 FPS').replace('value="hit">受击 · 12 FPS','value="death">死亡 · 10 FPS')
text=text.replace("kind='idle'","kind='attack'").replace("kind==='idle'?'待机':'受击'","kind==='attack'?'攻击':'死亡'").replace("kind==='idle'?'循环':'单次播放'","'单次播放'")
text=text.replace('/ 4 帧','/ ${clip().frame_count} 帧').replace('(frame+delta+4)%4','(frame+delta+clip().frame_count)%clip().frame_count')
text=text.replace("kind==='hit'&&frame===3","frame===clip().frame_count-1").replace('frame===3&&!clip().loop','frame===clip().frame_count-1&&!clip().loop').replace('(frame+1)%4','(frame+1)%clip().frame_count')
text=text.replace('从头播放受击','从头播放当前动作').replace('16 条动作共64帧：14条/56帧新增候选，2条/8帧原通过正向。','16 条动作共112帧：14条/98帧新增候选，2条/14帧原通过正向。')
text=text.replace('机壳和风筒整体刚性倾转，风口内叶片独立旋转，无逐帧生图。','攻击短促下探后复位；死亡断电、转子减速、整机刚性坠落并停在地面。隐藏的探头保留遮挡；无逐帧生图。')
(ROOT/'previews/index.html').write_text(text,encoding='utf-8')
print('DRONE_V018_FIXED_SOURCES_READY')
