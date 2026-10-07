"""Register four unobstructed new walking views; profile legs are a separate batch."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
UNIT='enemy_patrol'
BASE=ROOT.parent/'enemy-heavy-directions-move-v014'
PILOT=ROOT.parent/'enemy-eight-directions-v013-pilot-patrol-v001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rect(x,y,w,h):return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
def part(name,poly,pivot,end=None,exclude=None,z=0):return dict(id=name,polygon=poly,pivot=pivot,end=end,exclude=exclude or [],z=z)
def leg(side,hip,knee,ankle,cap,thigh,shin,foot,z,sole=7):
    # 连杆按实际可见接缝注册端点，刚性护膝/靴子不参与伸缩。
    thigh_end=[knee[0],cap[1]]
    shin_start=[knee[0],shin[1]]
    shin_end=[ankle[0],foot[1]]
    cap=rect(*cap)
    return [part(side+'_thigh',rect(*thigh),hip,thigh_end,[cap],z),part(side+'_shin',rect(*shin),shin_start,shin_end,z=z),part(side+'_cap',cap,knee,z=z+2),part(side+'_foot',rect(*foot),ankle,z=z+1)],dict(hip=hip,knee=knee,ankle=ankle,sole_offset=[0,sole])
definitions={
 'down_left':{
  'right':([58,82],[58,89],[58,97],[54,85,11,7],[54,82,10,10],[54,92,11,2],[52,94,12,34],0,7),
  'left':([69,82],[69,89],[70,97],[65,85,10,7],[65,82,10,10],[65,92,10,2],[64,94,14,34],1,7)},
 'up_left':{
  'left':([58,81],[58,88],[58,97],[54,84,10,8],[54,81,10,11],[54,92,10,2],[51,94,15,34],1,7),
  'right':([71,81],[71,88],[71,96],[66,84,10,8],[66,81,10,11],[66,92,10,1],[66,93,13,35],0,6)},
 'up':{
  'left':([58,82],[58,89],[58,97],[53,85,10,7],[54,82,9,10],[54,92,9,2],[52,94,12,34],1,7),
  'right':([70,82],[70,89],[70,97],[65,85,11,7],[65,82,11,10],[65,92,11,2],[64,94,13,34],0,7)},
 'up_right':{
  'left':([57,80],[57,88],[56,96],[54,85,10,7],[57,80,2,5],[54,92,10,1],[49,93,15,35],0,4),
  'right':([67,82],[67,89],[67,97],[64,85,8,7],[64,82,8,10],[64,92,8,2],[63,94,13,34],1,7)}
}
heading={'down_left':[-.7071,.7071],'up_left':[-.7071,-.7071],'up':[0,-1],'up_right':[.7071,-.7071]}
tools={'down_left':[[43,76,11,12],[75,82,8,12]],'up_left':[[43,78,13,16],[75,78,7,13]],
       'up':[[43,78,10,14],[76,78,7,14]],'up_right':[[46,75,10,9],[74,78,10,15]]}
configs={}
for direction,data in definitions.items():
    parts=[];legs={}
    for side,values in data.items():
        p,l=leg(side,*values);parts+=p;legs[side]=l
    if direction=='up_right':
        # 东北向远靴的边界在 y96 收入一列；这一列在上方属于远靴，在下方属于近靴。
        far_boot=[[49,93],[64,93],[64,96],[63,96],[63,99],[62,99],[62,128],[49,128]]
        for p in parts:
            if p['id']=='left_foot':p['polygon']=far_boot
            elif p['id']=='right_foot':p['exclude'].append(far_boot)
    configs[direction]=dict(source=f'res://source/{direction}.png',source_sha256=sha(ROOT/'source'/f'{direction}.png'),parts=parts,legs=legs,heading=heading[direction],protected_body_polygons=[rect(*r) for r in tools[direction]])
for folder in ['output/'+UNIT,'reference/'+UNIT]:(ROOT/folder).mkdir(parents=True,exist_ok=True)
for d in ['down','down_left','left','up_left','up','up_right','right','down_right']:
    shutil.copy2(ROOT/'source'/f'{d}.png',ROOT/'output'/UNIT/f'neutral_{d}.png')
preserved=[]
for direction,package in [('down',ROOT.parent/'enemy-sequences-v012'),('down_right',PILOT)]:
    action='move_'+direction
    src=package/'output'/UNIT/action;dst=ROOT/'output'/UNIT/action
    shutil.copytree(src,dst,dirs_exist_ok=True);shutil.copy2(src.with_suffix('.png'),dst.with_suffix('.png'))
    preserved.append(dict(action=action,atlas_sha256=sha(dst.with_suffix('.png')),frame_hashes=[sha(dst/f'f{i:02}.png') for i in range(8)]))
shutil.copy2(ROOT/'output'/UNIT/'move_down.png',ROOT/'reference'/UNIT/'move_down.png')
shutil.copy2(ROOT/'source/down.png',ROOT/'reference'/UNIT/'neutral_down.png')
spec=dict(version='v020-patrol-four-new-moves',unit=UNIT,canvas=[128,128],root=[64,104],directions=['down','down_left','up_left','up','up_right','down_right'],not_made=['left','right'],configs=configs,preserved=preserved,phases=json.loads((ROOT.parent/'enemy-patrol-actions-v008/rig.json').read_text(encoding='utf-8'))['phases'])
(ROOT/'rig.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
for name in ['export.gd','verify.gd','preview.gd','capture.gd','preview.tscn','previews/index.html','pixel_audit.py','masked_part.gdshader']:
    text=(BASE/name).read_text(encoding='utf-8').replace('enemy_tracked_heavy',UNIT).replace('v014','v020').replace('HEAVY','PATROL').replace('重装机','巡逻兵')
    text=text.replace('6 new moves / 48 new frames','4 new moves / 32 new frames').replace('Six new directions pending TA','Four new directions pending TA; W/E not made')
    text=text.replace('六个新方向','四个新方向').replace('六个方向','四个方向').replace('six new clips','four new clips')
    text=text.replace('v020-heavy-move','v020-patrol-move').replace('eight animations in SpriteFrames','six animations in SpriteFrames')
    if name=='previews/index.html':
        text=text.replace('v020 · v002','v020 · v001').replace('新增六向移动待审','新增四向移动待审').replace('八个方向均可播放移动。','本包六向可播放移动；正左、正右尚未制作，显示静态母稿。')
        text=text.replace("const units=[['enemy_patrol','巡逻兵'],['enemy_patrol','巡逻兵'],['enemy_cutter','切割工蜂'],['enemy_scout_drone','侦察机']];","const units=[['enemy_patrol','巡逻兵']];")
        text=text.replace('本页包含八向移动共64帧，其中6条/48帧待审、2条/16帧保留既有通过版本。','本页包含六向移动共48帧，其中4条/32帧待审、2条/16帧保留既有通过版本。W/E尚未制作。')
    if name=='export.gd':
        text=text.replace('var atlas:=Image.create(1024','rig.reset_bind()\n   await process_frame\n   await RenderingServer.frame_post_draw\n   read_viewport_frame(viewport).save_png("res://qa/bind_"+direction+".png")\n   var atlas:=Image.create(1024')
        text=text.replace('    if index==0:frame.save_png("res://qa/bind_"+direction+".png")\n','')
    if name=='preview.gd':
        text=text.replace('var action:="move_"+direction\n  frames.add_animation(action)','var action:="move_"+direction\n  if not saved.has_animation(action):continue\n  frames.add_animation(action)')
    if name=='capture.gd':
        text=text.replace('var passed:bool=preview.target.frame==3 and absf(preview.target.frame_progress-0.375)<0.0001','var made:bool=not Preview.DIRS[index] in ["left","right"]\n  var passed:bool=(preview.target.frame==3 and absf(preview.target.frame_progress-0.375)<0.0001) if made else (preview.target.animation=="neutral_"+Preview.DIRS[index] and preview.target.frame==0)')
        text=text.replace('for index in range(16):','var made_dirs:Array=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json")).directions\n for index in range(made_dirs.size()*2):').replace('Preview.DIRS[index%8]','made_dirs[index%made_dirs.size()]').replace('index>=8','index>=made_dirs.size()').replace('players=16','players=12')
        text=text.replace('(index%8)*156','(index%6)*206').replace('(index/8)*400','(index/6)*400')
    (ROOT/name).write_text(text,encoding='utf-8')
print('PATROL_FOUR_DIRECTION_RIG_REGISTERED')
