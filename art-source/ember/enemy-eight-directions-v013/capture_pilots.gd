extends SceneTree
const Preview=preload("res://preview.gd")
func _initialize()->void:call_deferred("run")
func xy(p:Vector2)->Array:return [p.x,p.y]
func run()->void:
 var preview:=Preview.new()
 root.add_child(preview)
 await process_frame
 var checks:Array=[]
 var frames_by_unit:Dictionary={}
 var catalog:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/pilot_catalog_v013.json"))
 for clip:Dictionary in catalog.clips:
  var index:int=Preview.UNITS.find(clip.unit)
  preview.select_unit(index)
  preview.playing=false
  preview.approved.pause()
  preview.target.pause()
  frames_by_unit[clip.unit]=preview.frames_for(clip.unit)
  for direction_index in range(8):
   # 相位保持依赖真实 AnimatedSprite2D API，避免用重新 play 后的首帧假装切换。
   preview.approved.set_frame_and_progress(3,0.375)
   preview.select_direction(direction_index)
   var made:bool=preview.target.animation.begins_with("move_")
   var passed:bool=(preview.target.frame==3 and absf(preview.target.frame_progress-0.375)<0.0001) if made else preview.target.frame==0
   assert(passed,"Direction switch reset an existing movement phase")
   checks.append({"unit":clip.unit,"direction":Preview.DIRS[direction_index],"made":made,"target_animation":preview.target.animation,"frame":preview.target.frame,"progress":preview.target.frame_progress,"pass":passed})
  await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_png("res://qa/picker_"+str(clip.unit)+".png")
 preview.queue_free()
 await process_frame
 var grid:=Node2D.new()
 root.add_child(grid)
 var actors:Array[AnimatedSprite2D]=[]
 var seen:Dictionary={}
 var loops:Dictionary={}
 var row:=0
 for unit:String in frames_by_unit:
  for column in range(4):
   var old:bool=column>=2
   var slow:bool=column%2==1
   var backdrop:=ColorRect.new()
   backdrop.position=Vector2(20+column*300,30+row*340)
   backdrop.size=Vector2(280,300)
   backdrop.color=Color("111822") if old else Color("d2d6dc")
   grid.add_child(backdrop)
   var label:=Label.new()
   label.position=backdrop.position+Vector2(8,8)
   label.text="%s\n%s / %s"%[unit.trim_prefix("enemy_"),"DOWN" if old else "SE PILOT","1 FPS" if slow else "8 FPS"]
   label.add_theme_color_override("font_color",Color.WHITE if old else Color("1b2632"))
   grid.add_child(label)
   var sprite:=AnimatedSprite2D.new()
   sprite.sprite_frames=frames_by_unit[unit]
   sprite.centered=false
   sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
   sprite.position=backdrop.position+Vector2(12,40)
   sprite.scale=Vector2(2,2)
   sprite.speed_scale=0.125 if slow else 1.0
   var action:="move_down" if old else "move_down_right"
   var key:="%s/%s/%s"%[unit,action,"slow" if slow else "normal"]
   sprite.set_meta("key",key)
   seen[key]=[]
   loops[key]=0
   sprite.animation_looped.connect(func():loops[key]+=1)
   grid.add_child(sprite)
   sprite.play(action)
   actors.append(sprite)
  row+=1
 var started:=Time.get_ticks_msec()
 while Time.get_ticks_msec()-started<9300:
  await process_frame
  for actor:AnimatedSprite2D in actors:
   var key:String=actor.get_meta("key")
   if not seen[key].has(actor.frame):seen[key].append(actor.frame)
 var passed:=true
 for key:String in seen:
  seen[key].sort()
  passed=passed and seen[key].size()==8 and loops[key]>=1
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("res://qa/pilot_runtime.png")
 var report:Dictionary={"status":"PASS" if passed else "FAIL","scope":"author Godot runtime, not TA approval","catalog_sha256":FileAccess.get_sha256("res://output/pilot_catalog_v013.json"),"direction_switches":checks,"seen_frames":seen,"completed_loops":loops,"elapsed_ms":Time.get_ticks_msec()-started,"renderer":RenderingServer.get_video_adapter_name()}
 FileAccess.open("res://qa/pilot_runtime.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 print("PILOT_RUNTIME_",report.status," | players=",actors.size()," | switches=",checks.size())
 quit(0 if passed else 1)
