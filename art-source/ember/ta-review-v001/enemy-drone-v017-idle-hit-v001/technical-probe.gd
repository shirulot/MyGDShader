extends SceneTree
## 最小独立冷资源、图集关联、场景定点；不捕获GPU、不重跑自然循环。
var records:Array=[]
func check(label:String,passed:bool)->void:records.append({"check":label,"pass":passed})
func _initialize()->void:call_deferred("run")
func run()->void:
 var sf=load("res://output/enemy_scout_drone_idle_hit_v017.tres") as SpriteFrames
 var cat:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog.json"))
 check("SpriteFrames loads",sf!=null)
 if sf!=null:
  check("16 idle/hit clips",sf.get_animation_names().size()==16)
  check("TRES embedded external dependencies empty",ResourceLoader.get_dependencies("res://output/enemy_scout_drone_idle_hit_v017.tres").is_empty())
  for clip:Dictionary in cat.clips:
   var action:String=clip.action
   var okay:=sf.has_animation(action) and sf.get_frame_count(action)==4 and sf.get_animation_speed(action)==float(clip.fps) and sf.get_animation_loop(action)==bool(clip.loop)
   var native:=Image.load_from_file(ProjectSettings.globalize_path(clip.atlas))
   for i in range(4):
    var tex=sf.get_frame_texture(action,i) as AtlasTexture
    okay=okay and tex!=null and tex.region==Rect2(i*128,0,128,128) and sf.get_frame_duration(action,i)==1.0
    if tex!=null:okay=okay and tex.atlas.get_image().get_data()==native.get_data()
   check(action+" actual metadata/four regions/embedded atlas RGBA",okay)
 var packed=load("res://preview.tscn") as PackedScene
 check("preview scene loads",packed!=null)
 if packed!=null:
  var preview=packed.instantiate()
  root.add_child(preview)
  await process_frame
  await process_frame
  check("preview16 clips and Nearest",preview.frames.get_animation_names().size()==16 and preview.target.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST)
  for action_index in range(2):
   preview.select_action(action_index)
   preview.playing=false
   preview.target.pause()
   preview.approved.pause()
   preview.approved.set_frame_and_progress(2,.375)
   preview.select_direction(5)
   check(preview.action+" NE phase2/.375 pause",preview.target.frame==2 and is_equal_approx(preview.target.frame_progress,.375) and not preview.target.is_playing())
  preview.queue_free()
 var fixed=load("res://rig.gd").new()
 fixed.direction="up"
 root.add_child(fixed)
 await process_frame
 var state:Dictionary=fixed.pose_action("hit",1)
 check("rig source/fan dependencies instantiate",fixed.body!=null and fixed.rotors.size()==2)
 check("runtime rig hit -6deg around (64,67)",is_equal_approx(fixed.body.rotation_degrees,-6.0) and fixed.body.transform*Vector2(64,67)==Vector2(64,67) and state.body_roll_degrees==-6.0)
 fixed.queue_free()
 var failed=records.filter(func(r):return not r["pass"])
 var report={"status":"PASS" if failed.is_empty() else "FAIL","engine":Engine.get_version_info()["string"],"display_server":DisplayServer.get_name(),"scope":"TA headless cold resources:16clips/64 embedded regions, scene, two pause phase switches, fixed rig dependency and pivot; no GPU/natural playback suite", "checks":records,"passed":records.size()-failed.size(),"total":records.size(),"failed":failed}
 FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 print("TA_DRONE_D17_COLD ",report.status," ",report.passed,"/",report.total)
 quit(0 if failed.is_empty() else 1)
