extends Node2D
## 同相位双栏审阅：idle正常循环；hit播放一次后停在恢复帧。
const DIRS=["down","down_left","left","up_left","up","up_right","right","down_right"]
const ACTIONS=["idle","hit"]
var direction_index:=1
var action:="idle"
var playing:=true
var slow:=false
var zoom:=4
var target:=AnimatedSprite2D.new()
var approved:=AnimatedSprite2D.new()
var info:=Label.new()
var stages:Array[ColorRect]=[]
var frames:SpriteFrames

func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 frames=load("res://output/enemy_scout_drone_idle_hit_v017.tres") as SpriteFrames
 add_label("EMBER / DRONE / IDLE + HIT / v017",Vector2(24,16),23)
 add_label("14 new clips pending TA; original down unchanged. Hit is one-shot.",Vector2(24,50),16)
 var picker:=OptionButton.new()
 picker.position=Vector2(24,82)
 picker.size=Vector2(156,36)
 picker.add_item("IDLE / 4 FPS")
 picker.add_item("HIT / 12 FPS")
 picker.item_selected.connect(func(index:int):select_action(index))
 add_child(picker)
 add_button("Play / Pause",Vector2(194,82),toggle_play)
 add_button("Replay",Vector2(354,82),replay)
 add_button("Next frame",Vector2(514,82),step_frame)
 add_button("Normal / 1 FPS",Vector2(674,82),func():slow=not slow;apply_display())
 add_button("4x / 1x",Vector2(834,82),func():zoom=1 if zoom==4 else 4;apply_display())
 add_button("Light / Dark",Vector2(994,82),toggle_background)
 for origin:Vector2 in [Vector2(24,158),Vector2(568,158)]:
  var stage:=ColorRect.new()
  stage.position=origin
  stage.size=Vector2(512,512)
  stage.color=Color("d2d6dc")
  stages.append(stage)
  add_child(stage)
 add_label("SELECTED DIRECTION / CANDIDATE",Vector2(24,132),16)
 add_label("APPROVED DOWN / SAME PHASE",Vector2(568,132),16)
 for actor in [target,approved]:
  actor.centered=false
  actor.sprite_frames=frames
  actor.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
  add_child(actor)
 target.animation_finished.connect(func():playing=false)
 info.position=Vector2(24,684)
 info.add_theme_font_size_override("font_size",17)
 add_child(info)
 for index in range(8):add_button(DIRS[index],Vector2(24+(index%4)*266,728+(index/4)*44),func():select_direction(index),252)
 replay()
 apply_display()

func add_label(text:String,where:Vector2,size:int)->void:
 var label:=Label.new()
 label.text=text
 label.position=where
 label.add_theme_font_size_override("font_size",size)
 add_child(label)
func add_button(text:String,where:Vector2,callback:Callable,width:float=148)->void:
 var button:=Button.new()
 button.text=text
 button.position=where
 button.size=Vector2(width,36)
 button.pressed.connect(callback)
 add_child(button)
func select_action(index:int)->void:
 action=ACTIONS[index]
 replay()
 apply_display()
func select_direction(index:int)->void:
 direction_index=index
 var frame:=approved.frame
 var progress:=approved.frame_progress
 target.play(action+"_"+DIRS[index])
 target.set_frame_and_progress(frame,progress)
 if not playing:target.pause()
func replay()->void:
 playing=true
 target.stop()
 approved.stop()
 approved.play(action+"_down")
 target.play(action+"_"+DIRS[direction_index])
func toggle_play()->void:
 if playing:
  playing=false
  target.pause()
  approved.pause()
 elif action=="hit" and target.frame==3:replay()
 else:
  playing=true
  target.play()
  approved.play()
func step_frame()->void:
 playing=false
 target.pause()
 approved.pause()
 var frame:=posmod(approved.frame+1,4)
 for actor in [target,approved]:actor.set_frame_and_progress(frame,0)
func toggle_background()->void:
 for stage in stages:stage.color=Color("080b10") if stage.color.r>0.2 else Color("d2d6dc")
func apply_display()->void:
 for index in range(2):
  var actor:AnimatedSprite2D=target if index==0 else approved
  actor.speed_scale=1.0/frames.get_animation_speed(action+"_down") if slow else 1.0
  actor.scale=Vector2.ONE*zoom
  actor.position=stages[index].position+Vector2.ONE*(512-128*zoom)*0.5
func _process(_delta:float)->void:
 info.text="%s | %s | frame %d / 4 | %s | %s"%[action,DIRS[direction_index],target.frame+1,"LOOP" if action=="idle" else "ONE SHOT","APPROVED DOWN" if direction_index==0 else "PENDING TA"]
