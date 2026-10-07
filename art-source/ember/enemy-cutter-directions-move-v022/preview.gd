extends Node2D
## 审阅器：方向切换保留动画相位；未制作方向明确显示静态候选。
const UNITS=["enemy_cutter"]
const DIRS=["down","down_left","left","up_left","up","up_right","right","down_right"]
var unit_index:=0
var direction_index:=1
var moving:=true
var playing:=true
var slow:=false
var zoom:=4
var target:=AnimatedSprite2D.new()
var approved:=AnimatedSprite2D.new()
var info:=Label.new()
var stages:Array[ColorRect]=[]
var cache:Dictionary={}
var unit_picker:OptionButton

func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 add_label("EMBER / CUTTER / EIGHT-DIRECTION MOVEMENT",Vector2(24,14),22)
 add_label("Six new directions pending TA; approved down and down_right preserved.",Vector2(24,48),16)
 var select:=OptionButton.new()
 unit_picker=select
 select.position=Vector2(24,78)
 select.size=Vector2(220,36)
 for index in range(UNITS.size()):
  var unit:String=UNITS[index]
  if FileAccess.file_exists("res://output/"+unit+"_move_v022.tres"):select.add_item(unit.trim_prefix("enemy_"),index)
 select.selected=0
 select.item_selected.connect(func(item:int):select_unit(select.get_item_id(item)))
 add_child(select)
 add_button("Play / Pause",Vector2(260,78),toggle_play)
 add_button("Next frame",Vector2(420,78),step_frame)
 add_button("8 FPS / 1 FPS",Vector2(580,78),toggle_speed)
 add_button("4x / 1x",Vector2(740,78),toggle_zoom)
 add_button("Light / Dark",Vector2(900,78),toggle_background)
 for origin:Vector2 in [Vector2(24,160),Vector2(568,160)]:
  var stage:=ColorRect.new()
  stage.position=origin
  stage.size=Vector2(512,512)
  stage.color=Color("d2d6dc")
  stages.append(stage)
  add_child(stage)
 add_label("SELECTED DIRECTION",Vector2(24,130),17)
 add_label("APPROVED DOWN / SAME PHASE",Vector2(568,130),17)
 for actor:AnimatedSprite2D in [target,approved]:
  actor.centered=false
  actor.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
  add_child(actor)
 info.position=Vector2(24,686)
 info.add_theme_font_size_override("font_size",17)
 add_child(info)
 for index in range(8):
  add_button(DIRS[index],Vector2(24+(index%4)*266,730+(index/4)*44),func():select_direction(index),252)
 add_button("Move / Neutral",Vector2(24,826),func():moving=not moving;select_direction(direction_index))
 select_unit(select.get_item_id(0))

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

func image_texture(path:String)->ImageTexture:
 return ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(path)))

func frames_for(unit:String)->SpriteFrames:
 if cache.has(unit):return cache[unit]
 var frames:=SpriteFrames.new()
 frames.remove_animation("default")
 for direction:String in DIRS:
  var name:="neutral_"+direction
  frames.add_animation(name)
  frames.set_animation_loop(name,false)
  frames.add_frame(name,image_texture("res://output/"+unit+"/neutral_"+direction+".png"))
 var saved:=load("res://output/"+unit+"_move_v022.tres") as SpriteFrames
 for direction:String in DIRS:
  var action:="move_"+direction
  if not saved.has_animation(action):continue
  frames.add_animation(action)
  frames.set_animation_speed(action,8)
  frames.set_animation_loop(action,true)
  for index in range(8):frames.add_frame(action,saved.get_frame_texture(action,index))
 cache[unit]=frames
 return frames

func select_unit(index:int)->void:
 var frame:=approved.frame
 var progress:=approved.frame_progress
 unit_index=index
 for item in range(unit_picker.item_count):
  if unit_picker.get_item_id(item)==index:unit_picker.selected=item
 var frames:=frames_for(UNITS[index])
 target.sprite_frames=frames
 approved.sprite_frames=frames
 approved.play("move_down" if moving else "neutral_down")
 if moving:approved.set_frame_and_progress(frame%8,progress)
 select_direction(direction_index)
 apply_display()

func select_direction(index:int)->void:
 direction_index=index
 var frame:=approved.frame
 var progress:=approved.frame_progress
 var action:="move_"+str(DIRS[index]) if moving else "neutral_"+str(DIRS[index])
 if moving and not target.sprite_frames.has_animation(action):action="neutral_"+str(DIRS[index])
 target.play(action)
 if action.begins_with("move_"):target.set_frame_and_progress(frame%8,progress)
 if moving:
  approved.play("move_down")
  approved.set_frame_and_progress(frame%8,progress)
 else:approved.play("neutral_down")
 if not playing:target.pause();approved.pause()

func toggle_play()->void:
 playing=not playing
 for actor:AnimatedSprite2D in [target,approved]:
  if playing:actor.play()
  else:actor.pause()

func step_frame()->void:
 playing=false
 approved.pause()
 target.pause()
 var frame:=posmod(approved.frame+1,8)
 if moving:approved.set_frame_and_progress(frame,0)
 if target.animation.begins_with("move_"):target.set_frame_and_progress(frame,0)

func toggle_speed()->void:
 slow=not slow
 apply_display()
func toggle_zoom()->void:
 zoom=1 if zoom==4 else 4
 apply_display()
func toggle_background()->void:
 for stage:ColorRect in stages:stage.color=Color("080b10") if stage.color.r>0.2 else Color("d2d6dc")
func apply_display()->void:
 for index in range(2):
  var actor:AnimatedSprite2D=target if index==0 else approved
  actor.speed_scale=0.125 if slow else 1.0
  actor.scale=Vector2.ONE*zoom
  actor.position=stages[index].position+Vector2.ONE*(512-128*zoom)*0.5

func _process(_delta:float)->void:
 info.text="%s | %s | phase %d / 8 | %s"%[UNITS[unit_index],DIRS[direction_index],approved.frame+1,"OUTSIDE BATCH" if moving and target.animation.begins_with("neutral_") else "CANDIDATE"]
