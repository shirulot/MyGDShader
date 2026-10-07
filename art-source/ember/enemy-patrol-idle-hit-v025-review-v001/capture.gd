extends SceneTree
const Preview=preload("res://preview.gd")
func _initialize()->void:call_deferred("run")
func run()->void:
 var preview:=Preview.new()
 root.add_child(preview)
 await process_frame
 var switches:Array=[]
 for action_index in range(2):
  preview.select_action(action_index)
  preview.playing=false
  preview.approved.pause()
  preview.target.pause()
  for direction_index in range(8):
   preview.approved.set_frame_and_progress(2,0.375)
   preview.select_direction(direction_index)
   var okay:bool=preview.target.frame==2 and absf(preview.target.frame_progress-0.375)<0.0001
   assert(okay,"Direction phase reset")
   switches.append({"action":preview.action,"direction":Preview.DIRS[direction_index],"frame":preview.target.frame,"progress":preview.target.frame_progress,"passed":okay})
 await process_frame
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("res://qa/preview.png")
 var frames:=preview.frames
 preview.queue_free()
 await process_frame
 var actors:Array[AnimatedSprite2D]=[]
 var seen:Dictionary={}
 var loops:Dictionary={}
 var finishes:Dictionary={}
 for index in range(32):
  var row:int=index/8
  var direction:String=Preview.DIRS[index%8]
  var action:="idle" if row<2 else "hit"
  var slow:bool=row%2==1
  var position:=Vector2(8+(index%8)*156,12+row*212)
  var backdrop:=ColorRect.new()
  backdrop.position=position
  backdrop.size=Vector2(152,206)
  backdrop.color=Color("d2d6dc") if not slow else Color("0d141b")
  root.add_child(backdrop)
  var label:=Label.new()
  label.position=position+Vector2(2,0)
  label.text=direction+"\n"+action+(" 1FPS" if slow else " NORMAL")
  label.add_theme_font_size_override("font_size",13)
  label.add_theme_color_override("font_color",Color.WHITE if slow else Color.BLACK)
  root.add_child(label)
  var actor:=AnimatedSprite2D.new()
  actor.sprite_frames=frames
  actor.centered=false
  actor.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
  actor.position=position+Vector2(12,46)
  actor.speed_scale=1.0/frames.get_animation_speed(action+"_"+direction) if slow else 1.0
  var key:=action+"_"+direction+("/slow" if slow else "/normal")
  actor.set_meta("key",key)
  seen[key]=[]
  loops[key]=0
  finishes[key]=0
  actor.animation_looped.connect(func():loops[key]+=1)
  actor.animation_finished.connect(func():finishes[key]+=1)
  root.add_child(actor)
  actor.play(action+"_"+direction)
  actors.append(actor)
 var start:=Time.get_ticks_msec()
 while Time.get_ticks_msec()-start<5200:
  await process_frame
  for actor in actors:
   var key:String=actor.get_meta("key")
   if not seen[key].has(actor.frame):seen[key].append(actor.frame)
 var passed:=true
 var end_states:Array=[]
 for actor in actors:
  var key:String=actor.get_meta("key")
  seen[key].sort()
  var one_shot:bool=key.begins_with("hit_")
  var okay:bool=seen[key].size()==4
  okay=okay and (finishes[key]==1 and loops[key]==0 and actor.frame==3 and not actor.is_playing() if one_shot else loops[key]>=1 and finishes[key]==0)
  passed=passed and okay
  end_states.append({"key":key,"seen_frames":seen[key],"loops":loops[key],"finishes":finishes[key],"last_frame":actor.frame,"playing":actor.is_playing(),"passed":okay})
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("res://qa/runtime_grid.png")
 var report:Dictionary={"status":"PASS" if passed else "FAIL","catalog_sha256":FileAccess.get_sha256("res://output/catalog.json"),"switches":switches,"players":end_states,"renderer":RenderingServer.get_video_adapter_name(),"elapsed_ms":Time.get_ticks_msec()-start}
 FileAccess.open("res://qa/runtime.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 print("PATROL_IDLE_HIT_RUNTIME_",report.status," | players=32 | switches=16")
 quit(0 if passed else 1)
