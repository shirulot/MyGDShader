extends Node2D
## 八向资源的真实播放入口：切换方向保留帧与帧内相位，单次动作自然停留。
const UNITS=["enemy_patrol","enemy_tracked_heavy","enemy_cutter","enemy_scout_drone"]
const NAMES=["巡逻兵","履带重装机","切割者","悬浮侦察机"]
const DIRS=["down","down_left","left","up_left","up","up_right","right","down_right"]
const LABELS=["↓ 正下","↙ 左下","← 正左","↖ 左上","↑ 正上","↗ 右上","→ 正右","↘ 右下"]
const ACTIONS=["idle","move","attack","hit","death"]
var resources:Dictionary={}
var unit_index:=0
var action_index:=0
var direction_index:=0
var target:=AnimatedSprite2D.new()
var original:=AnimatedSprite2D.new()
var info:=Label.new()
var playing:=true
var slow:=false
func button(text:String,at:Vector2,callback:Callable)->void:
 var b:=Button.new();b.text=text;b.position=at;b.pressed.connect(callback);add_child(b)
func _ready()->void:
 for unit:String in UNITS:resources[unit]=load("res://output/"+unit+".tres")
 var bg:=ColorRect.new();bg.color=Color("151b22");bg.size=Vector2(1280,900);add_child(bg)
 for i in range(4):button(NAMES[i],Vector2(24+i*160,22),func():select_unit(i))
 for i in range(5):button(ACTIONS[i],Vector2(24+i*120,68),func():select_action(i))
 for i in range(8):button(LABELS[i],Vector2(24+i*150,740),func():select_direction(i))
 button("播放 / 暂停",Vector2(670,22),toggle)
 button("从头播放",Vector2(820,22),replay)
 button("正常 / 1 FPS",Vector2(960,22),toggle_speed)
 button("前一帧",Vector2(670,68),func():step(-1))
 button("后一帧",Vector2(820,68),func():step(1))
 for i in range(2):
  var stage:=ColorRect.new();stage.position=Vector2(24+i*620,145);stage.size=Vector2(596,560);stage.color=Color("d2d6dc") if i==0 else Color("0b1017");add_child(stage)
 for actor:AnimatedSprite2D in [target,original]:
  actor.centered=false;actor.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;actor.scale=Vector2(4,4);add_child(actor)
 target.position=Vector2(64,165);original.position=Vector2(684,165)
 info.position=Vector2(24,805);add_child(info)
 select_unit(0)
func select_unit(index:int)->void:
 unit_index=index;target.sprite_frames=resources[UNITS[index]];original.sprite_frames=target.sprite_frames;replay()
func select_action(index:int)->void:action_index=index;replay()
func select_direction(index:int)->void:
 var frame:=target.frame;var progress:=target.frame_progress;var was_playing:=target.is_playing()
 direction_index=index
 target.play(ACTIONS[action_index]+"_"+DIRS[index])
 target.set_frame_and_progress(frame,progress)
 if not was_playing:target.pause()
func replay()->void:
 playing=true;target.play(ACTIONS[action_index]+"_"+DIRS[direction_index]);target.set_frame_and_progress(0,0)
 original.play(ACTIONS[action_index]+"_down");original.set_frame_and_progress(0,0);apply_speed()
func apply_speed()->void:
 var factor:=1.0/target.sprite_frames.get_animation_speed(target.animation) if slow else 1.0
 target.speed_scale=factor;original.speed_scale=factor
func toggle_speed()->void:slow=not slow;apply_speed()
func toggle()->void:
 playing=not target.is_playing()
 if playing:
  if target.frame==target.sprite_frames.get_frame_count(target.animation)-1 and not target.sprite_frames.get_animation_loop(target.animation):replay()
  else:target.play();original.play()
 else:target.pause();original.pause()
func step(delta:int)->void:
 target.pause();original.pause();playing=false
 var frame:=posmod(target.frame+delta,target.sprite_frames.get_frame_count(target.animation))
 target.set_frame_and_progress(frame,0);original.set_frame_and_progress(frame,0)
func _process(_delta:float)->void:
 if target.sprite_frames==null:return
 info.text="%s | %s_%s | frame %d/%d | %s\n左：选定方向 4×　右：原通过正向，同相位 4×。单次动作停留在末帧。"%[NAMES[unit_index],ACTIONS[action_index],DIRS[direction_index],target.frame+1,target.sprite_frames.get_frame_count(target.animation),"1 FPS" if slow else "正常速度"]
