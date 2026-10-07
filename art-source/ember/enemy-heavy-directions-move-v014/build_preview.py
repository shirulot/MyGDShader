"""Reuse the reviewed preview controls; bind all eight movement actions explicitly."""
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'enemy-eight-directions-v013'
gd=(PREVIOUS/'preview.gd').read_text(encoding='utf-8')
gd=gd.replace('const UNITS=["enemy_patrol","enemy_tracked_heavy","enemy_cutter","enemy_scout_drone"]','const UNITS=["enemy_tracked_heavy"]')
gd=gd.replace('var unit_index:=1','var unit_index:=0').replace('var direction_index:=7','var direction_index:=1')
gd=gd.replace('_pilot_v013.tres','_move_v014.tres')
gd=gd.replace('EMBER / EIGHT DIRECTIONS / FIRST GATE CANDIDATE','EMBER / HEAVY / EIGHT-DIRECTION MOVEMENT')
gd=gd.replace('This new movement pilot is pending TA. Static direction approval is recorded separately.','Six new directions pending TA; approved down and down_right preserved.')
start=gd.index(' frames.add_animation("move_down")')
end=gd.index(' cache[unit]=frames',start)
gd=gd[:start]+''' var saved:=load("res://output/"+unit+"_move_v014.tres") as SpriteFrames
 for direction:String in DIRS:
  var action:="move_"+direction
  frames.add_animation(action)
  frames.set_animation_speed(action,8)
  frames.set_animation_loop(action,true)
  for index in range(8):frames.add_frame(action,saved.get_frame_texture(action,index))
'''+gd[end:]
(ROOT/'preview.gd').write_text(gd,encoding='utf-8')
shutil.copy2(PREVIOUS/'preview.tscn',ROOT/'preview.tscn')
html=(PREVIOUS/'previews/index.html').read_text(encoding='utf-8')
html=html.replace('八向首批候选 v013','重装机八向移动 v014')
html=html.replace('新增方向正在审查，尚未通过。已通过的正向版本保留。','新增六向移动待审；已通过的正下、右下移动原文件保留。')
html=html.replace('没有制作的方向只显示中性造型。','八个方向均可播放移动。')
html=html.replace("direction='down_right'","direction='down_left'")
html=html.replace("direction==='down'?'原正向已通过':'新增候选未通过'","['down','down_right'].includes(direction)?'原动作已通过':'新增候选未通过'")
html=html.replace("fetch('pilot_catalog_v013.json')","fetch('catalog.json')")
html=html.replace('本页有 ${c.clips.length} 条移动小样，以已通过的正向移动供对照；未包含的方向或动作不计为完成。','本页包含八向移动共64帧，其中6条/48帧待审、2条/16帧保留既有通过版本。其它四类动作不计入本批。')
(ROOT/'previews/index.html').write_text(html,encoding='utf-8')
