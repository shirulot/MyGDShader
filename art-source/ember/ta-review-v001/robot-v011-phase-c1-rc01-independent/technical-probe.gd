extends SceneTree
## 独立冷资源 + C1唯一必要行为：collect恰一次结束并经原演示回idle0。
var records:Array=[]
var finish_count:=0
var finish_state:Dictionary={}
func check(label:String,passed:bool)->void:records.append({"check":label,"pass":passed})
func _initialize()->void:call_deferred("run")
func run()->void:
 var sf=load("res://robot_action_pilot_v011.tres") as SpriteFrames
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://action-pilot-metadata.json"))
 check("SpriteFrames loads",sf!=null)
 if sf!=null:
  check("four clips idle/collect/walk/pose",sf.get_animation_names().size()==4)
  var dependencies_ok:=true
  for dep:String in ResourceLoader.get_dependencies("res://robot_action_pilot_v011.tres"):
   dependencies_ok=dependencies_ok and FileAccess.file_exists(dep.get_slice("::",dep.get_slice_count("::")-1))
  check("atlas external dependency resolves inside cold project",dependencies_ok)
  for clip:Dictionary in spec.clips:
   var name:String=clip.name
   check(name+" fps/loop/count",sf.has_animation(name) and sf.get_frame_count(name)==clip.frames.size() and sf.get_animation_speed(name)==float(clip.fps) and sf.get_animation_loop(name)==bool(clip.loop))
   for f:Dictionary in clip.frames:
    var texture=sf.get_frame_texture(name,int(f.frame)) as AtlasTexture
    var region:=Rect2(float(f.region[0]),float(f.region[1]),float(f.region[2]),float(f.region[3]))
    var native:=Image.load_from_file(ProjectSettings.globalize_path("res://../"+String(f.file)))
    var okay:bool=texture!=null and texture.region==region and sf.get_frame_duration(name,int(f.frame))==1.0
    if okay:okay=texture.atlas.get_image().get_region(Rect2i(region)).get_data()==native.get_data()
    check(name+" f%d atlas import RGBA"%int(f.frame),okay)
 var scene=load("res://preview_action_pilot.tscn") as PackedScene
 check("preview scene loads",scene!=null)
 if scene!=null:
  var preview=scene.instantiate()
  root.add_child(preview)
  await process_frame
  await process_frame
  check("fixed root/Nearest",not preview.robot.centered and preview.robot.offset==Vector2(-32,-80) and preview.robot.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST)
  var seen:Array=[0]
  preview.robot.animation_finished.connect(func():
   finish_count+=1
   finish_state={"animation":preview.robot.animation,"frame":preview.robot.frame,"native_animation":preview.native.animation,"native_frame":preview.native.frame}
   preview.robot.pause()
   preview.native.pause()
  )
  preview._play("collect_down_left")
  var start:=Time.get_ticks_msec()
  while finish_count==0 and Time.get_ticks_msec()-start<1800:
   await process_frame
   if preview.robot.animation=="collect_down_left" and not seen.has(preview.robot.frame):seen.append(preview.robot.frame)
  await process_frame
  seen.sort()
  check("actual collect observes0/1/2/3 and one finish",seen==[0,1,2,3] and finish_count==1)
  check("original finish handler returns both sprites idle0",finish_state.get("animation")=="idle_down_left" and finish_state.get("frame")==0 and finish_state.get("native_animation")=="idle_down_left" and finish_state.get("native_frame")==0)
  var frames=preview.robot.sprite_frames
  check("collect last and idle0 actual imported RGBA same",(frames.get_frame_texture("collect_down_left",3) as AtlasTexture).get_image().get_data()==(frames.get_frame_texture("idle_down_left",0) as AtlasTexture).get_image().get_data())
  finish_state["seen_collect_frames"]=seen
  finish_state["elapsed_ms"]=Time.get_ticks_msec()-start
  preview.queue_free()
 var failed=records.filter(func(r):return not r["pass"])
 var report={"status":"PASS" if failed.is_empty() else "FAIL","scope":"Independent headless cold four resources/15regions and actual C1 collect single-finish->idle0 only; no GPU or author natural two-loop matrix", "engine":Engine.get_version_info()["string"],"display_server":DisplayServer.get_name(),"checks":records,"passed":records.size()-failed.size(),"total":records.size(),"finish_count":finish_count,"finish_state":finish_state,"failed":failed}
 FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 print("TA_C1_COLD ",report.status," ",report.passed,"/",report.total)
 quit(0 if failed.is_empty() else 1)
