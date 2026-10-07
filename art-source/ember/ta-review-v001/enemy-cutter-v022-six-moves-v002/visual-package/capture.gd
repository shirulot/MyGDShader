extends SceneTree
const Preview=preload("res://preview.gd")
func _initialize()->void:call_deferred("run")
func run()->void:
 var preview:=Preview.new()
 root.add_child(preview)
 await process_frame
 preview.playing=false
 preview.approved.pause()
 preview.target.pause()
 var switches:Array=[]
 for index in range(8):
  preview.approved.set_frame_and_progress(3,0.375)
  preview.select_direction(index)
  var made:bool=preview.target.sprite_frames.has_animation("move_"+Preview.DIRS[index])
  var passed:bool=(preview.target.frame==3 and absf(preview.target.frame_progress-0.375)<0.0001) if made else (preview.target.animation=="neutral_"+Preview.DIRS[index] and preview.target.frame==0)
  assert(passed,"Direction phase reset")
  switches.append({"direction":Preview.DIRS[index],"frame":preview.target.frame,"progress":preview.target.frame_progress,"passed":passed})
 await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("res://qa/preview.png")
 var frames:=preview.target.sprite_frames
 preview.queue_free()
 await process_frame
 var actors:Array[AnimatedSprite2D]=[]
 var seen:Dictionary={}
 var loops:Dictionary={}
 var made_dirs:Array=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json")).directions
 for index in range(made_dirs.size()*2):
  var direction:String=made_dirs[index%made_dirs.size()]
  var slow:bool=index>=made_dirs.size()
  var position:=Vector2(8+(index%8)*156,30+(index/8)*400)
  var backdrop:=ColorRect.new()
  backdrop.position=position
  backdrop.size=Vector2(152,370)
  backdrop.color=Color("d2d6dc") if not slow else Color("0d141b")
  root.add_child(backdrop)
  var label:=Label.new()
  label.position=position+Vector2(2,0)
  label.text=direction+"\n"+("1 FPS" if slow else "8 FPS")
  label.add_theme_font_size_override("font_size",14)
  label.add_theme_color_override("font_color",Color.WHITE if slow else Color.BLACK)
  root.add_child(label)
  var actor:=AnimatedSprite2D.new()
  actor.sprite_frames=frames
  actor.centered=false
  actor.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
  actor.position=position+Vector2(12,60)
  actor.speed_scale=0.125 if slow else 1.0
  var key:=direction+("/slow" if slow else "/normal")
  actor.set_meta("key",key)
  seen[key]=[]
  loops[key]=0
  actor.animation_looped.connect(func():loops[key]+=1)
  root.add_child(actor)
  actor.play("move_"+direction)
  actors.append(actor)
 var start:=Time.get_ticks_msec()
 while Time.get_ticks_msec()-start<9300:
  await process_frame
  for actor in actors:
   var key:String=actor.get_meta("key")
   if not seen[key].has(actor.frame):seen[key].append(actor.frame)
 var passed:=true
 for key:String in seen:
  seen[key].sort()
  passed=passed and seen[key].size()==8 and loops[key]>=1
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("res://qa/runtime_grid.png")
 var report:Dictionary={"status":"PASS" if passed else "FAIL","catalog_sha256":FileAccess.get_sha256("res://output/catalog.json"),"switches":switches,"seen_frames":seen,"loops":loops,"renderer":RenderingServer.get_video_adapter_name(),"elapsed_ms":Time.get_ticks_msec()-start}
 FileAccess.open("res://qa/runtime.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 print("CUTTER_RUNTIME_",report.status," | players=16 | switches=8")
 quit(0 if passed else 1)
