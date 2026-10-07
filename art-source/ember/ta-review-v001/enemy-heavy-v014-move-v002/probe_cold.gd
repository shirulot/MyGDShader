extends SceneTree
## v002定点冷资源复核。继承v001未变管线，不跑GPU/自然循环/全交互。
const DIRS=["down","down_left","left","up_left","up","up_right","right","down_right"]
var records:Array=[]
func check(label:String,passed:bool)->void:records.append({"check":label,"pass":passed})
func _initialize()->void:call_deferred("run")
func run()->void:
 var sf=load("res://output/enemy_tracked_heavy_move_v014.tres") as SpriteFrames
 check("SpriteFrames loads",sf!=null)
 if sf!=null:
  check("eight animations retained",sf.get_animation_names().size()==8)
  check("embedded resource has no external dependencies",ResourceLoader.get_dependencies("res://output/enemy_tracked_heavy_move_v014.tres").is_empty())
  for direction:String in DIRS:
   var action:="move_"+direction
   var first=sf.get_frame_texture(action,0) as AtlasTexture
   var expected:=Image.load_from_file(ProjectSettings.globalize_path("res://output/enemy_tracked_heavy/"+action+".png"))
   var actual:Image=first.atlas.get_image() if first!=null else null
   check(direction+" actual atlas association/metadata",first!=null and actual!=null and actual.get_data()==expected.get_data() and sf.get_frame_count(action)==8 and sf.get_animation_speed(action)==8.0 and sf.get_animation_loop(action))
  for i in range(8):
   var texture=sf.get_frame_texture("move_up",i) as AtlasTexture
   check("N frame%d region/duration"%i,texture!=null and texture.region==Rect2(i*128,0,128,128) and texture.atlas.get_width()==1024 and texture.atlas.get_height()==128 and sf.get_frame_duration("move_up",i)==1.0)
 var scene=load("res://preview.tscn") as PackedScene
 check("preview scene loads",scene!=null)
 if scene!=null:
  var preview=scene.instantiate()
  root.add_child(preview)
  await process_frame
  await process_frame
  check("preview16 animations retained",preview.target.sprite_frames.get_animation_names().size()==16)
  check("preview Nearest",preview.target.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST)
  preview.playing=false
  preview.target.pause()
  preview.approved.pause()
  preview.approved.set_frame_and_progress(3,.375)
  preview.select_direction(4)
  check("N switch phase retained",preview.target.animation=="move_up" and preview.target.frame==3 and is_equal_approx(preview.target.frame_progress,.375))
  preview.select_direction(0)
  check("down reference switch phase retained",preview.target.animation=="move_down" and preview.target.frame==3 and is_equal_approx(preview.target.frame_progress,.375))
  preview.queue_free()
 var failed=records.filter(func(r):return not r["pass"])
 var report={"status":"PASS" if failed.is_empty() else "FAIL","scope":"TA independent headless cold N resource/embedded associations/scene phase properties only; no GPU framebuffer or natural-loop/full interactive suite", "engine":Engine.get_version_info()["string"],"display_server":DisplayServer.get_name(),"checks":records,"passed":records.size()-failed.size(),"total":records.size(),"failed":failed}
 FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 print("TA_HEAVY_INCREMENTAL_COLD ",report.status," ",report.passed,"/",report.total)
 quit(0 if failed.is_empty() else 1)
