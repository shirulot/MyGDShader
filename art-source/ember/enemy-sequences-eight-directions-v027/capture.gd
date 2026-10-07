extends SceneTree
## 真实320个播放器覆盖全部160动作的正常/1 FPS时序，并验证160次保相位切换。
const Preview=preload("res://preview.gd")
func _initialize()->void:call_deferred("run")
func run()->void:
 var preview:=Preview.new();root.add_child(preview);await process_frame
 var switches:Array=[]
 for u in range(4):
  preview.select_unit(u)
  for a in range(5):
   preview.select_action(a);preview.target.pause();preview.original.pause()
   for d in range(8):
    preview.target.set_frame_and_progress(2,.375);preview.select_direction(d)
    var okay:bool=preview.target.frame==2 and absf(preview.target.frame_progress-.375)<.0001
    assert(okay)
    switches.append({"unit":Preview.UNITS[u],"action":Preview.ACTIONS[a],"direction":Preview.DIRS[d],"passed":okay})
 preview.select_unit(0);preview.select_action(1);preview.select_direction(7)
 await process_frame;await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("res://qa/preview.png")
 var resources:Dictionary=preview.resources
 preview.queue_free();await process_frame
 var actors:Array[AnimatedSprite2D]=[];var states:Dictionary={}
 for unit:String in Preview.UNITS:
  var frames:SpriteFrames=resources[unit]
  for name:StringName in frames.get_animation_names():
   for slow:bool in [false,true]:
    var actor:=AnimatedSprite2D.new();actor.sprite_frames=frames
    actor.position=Vector2(-256,-256)
    actor.speed_scale=1.0/frames.get_animation_speed(name) if slow else 1.0
    var key:=unit+"/"+str(name)+("/slow" if slow else "/normal")
    var state:Dictionary={"key":key,"seen":[0],"loops":0,"finishes":0,"count":frames.get_frame_count(name),"loop":frames.get_animation_loop(name)}
    states[key]=state;actor.set_meta("key",key)
    actor.animation_looped.connect(func():state.loops+=1)
    actor.animation_finished.connect(func():state.finishes+=1)
    root.add_child(actor);actor.play(name);actors.append(actor)
 var start:=Time.get_ticks_msec()
 while Time.get_ticks_msec()-start<9300:
  await process_frame
  for actor:AnimatedSprite2D in actors:
   var state:Dictionary=states[actor.get_meta("key")]
   if not state.seen.has(actor.frame):state.seen.append(actor.frame)
 var passed:=true
 for actor:AnimatedSprite2D in actors:
  var state:Dictionary=states[actor.get_meta("key")];state.seen.sort()
  state.last_frame=actor.frame;state.playing=actor.is_playing()
  state.passed=state.seen.size()==state.count and (state.loops>=1 and state.finishes==0 if state.loop else state.finishes==1 and state.loops==0 and actor.frame==state.count-1 and not actor.is_playing())
  passed=passed and state.passed
 var report:Dictionary={"status":"PASS" if passed else "FAIL","catalog_sha256":FileAccess.get_sha256("res://output/catalog.json"),"switches":switches,"players":states.values(),"renderer":RenderingServer.get_video_adapter_name(),"elapsed_ms":Time.get_ticks_msec()-start}
 FileAccess.open("res://qa/runtime.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("ASSEMBLY_RUNTIME_",report.status," | players=320 | switches=160")
 quit(0 if passed else 1)
