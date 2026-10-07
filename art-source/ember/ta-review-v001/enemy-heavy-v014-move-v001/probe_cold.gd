extends SceneTree
## TA 独立 headless 冷包探针。无 framebuffer、无自然循环或作者全套交互。
const DIRS=["down","down_left","left","up_left","up","up_right","right","down_right"]
var records:Array=[]
func check(label:String,passed:bool,detail:Variant=null)->void:
 records.append({"check":label,"pass":passed,"detail":detail})
func _initialize()->void:call_deferred("run")
func run()->void:
 var report_path:String=OS.get_cmdline_user_args()[0]
 var sf=load("res://output/enemy_tracked_heavy_move_v014.tres") as SpriteFrames
 check("SpriteFrames loads",sf!=null)
 if sf!=null:
  check("only 8 declared moves",sf.get_animation_names().size()==8)
  check("embedded resource external dependencies empty",ResourceLoader.get_dependencies("res://output/enemy_tracked_heavy_move_v014.tres").is_empty())
  for direction:String in DIRS:
   var action:="move_"+direction
   check(action+" properties",sf.has_animation(action) and sf.get_frame_count(action)==8 and sf.get_animation_speed(action)==8.0 and sf.get_animation_loop(action))
   var first=sf.get_frame_texture(action,0) as AtlasTexture
   var expected:=Image.load_from_file(ProjectSettings.globalize_path("res://output/enemy_tracked_heavy/"+action+".png"))
   var actual:Image=first.atlas.get_image() if first!=null else null
   check(action+" actual embedded atlas RGBA",actual!=null and actual.get_data()==expected.get_data())
   for i in range(8):
    var texture=sf.get_frame_texture(action,i) as AtlasTexture
    check("%s frame%d region/duration"%[action,i],texture!=null and texture.region==Rect2(i*128,0,128,128) and texture.atlas.get_width()==1024 and texture.atlas.get_height()==128 and sf.get_frame_duration(action,i)==1.0)
 var packed=load("res://preview.tscn") as PackedScene
 check("preview loads",packed!=null)
 if packed!=null:
  var preview=packed.instantiate()
  root.add_child(preview)
  await process_frame
  await process_frame
  check("preview only heavy",preview.unit_picker.item_count==1 and preview.unit_index==0)
  check("preview16 animations",preview.target.sprite_frames.get_animation_names().size()==16)
  check("preview Nearest",preview.target.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST)
  preview.playing=false
  preview.approved.pause()
  preview.target.pause()
  preview.approved.set_frame_and_progress(3,.375)
  preview.select_direction(7)
  check("SE switch preserves phase",preview.target.animation=="move_down_right" and preview.target.frame==3 and is_equal_approx(preview.target.frame_progress,.375))
  preview.select_direction(5)
  check("NE switch preserves phase",preview.target.animation=="move_up_right" and preview.target.frame==3 and is_equal_approx(preview.target.frame_progress,.375))
  preview.queue_free()
 # 最小定点补充：确认26个理想CPU边界差的实际Godot多边形归属，不运行rig捕获。
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 var mask_records:Array=[]
 for direction:String in spec.configs:
  var image:=Image.create(128,128,false,Image.FORMAT_R8)
  image.fill(Color.BLACK)
  var owned:=0
  for y in range(128):
   for x in range(128):
    var hit:=false
    for poly:Array in spec.configs[direction].track_polygons:
     var points:=PackedVector2Array()
     for q:Array in poly:points.append(Vector2(q[0],q[1]))
     if Geometry2D.is_point_in_polygon(Vector2(x+.5,y+.5),points):hit=true
    if hit:image.set_pixel(x,y,Color.WHITE);owned+=1
  var file:=report_path.get_base_dir()+"/godot_ownership_"+direction+".png"
  check(direction+" ownership mask saved",image.save_png(file)==OK)
  mask_records.append({"direction":direction,"owned_pixels":owned,"file":file})
 var failed=records.filter(func(r):return not r["pass"])
 var report={"status":"PASS" if failed.is_empty() else "FAIL","scope":"TA independent cold resource/scene/point-property and CPU Geometry2D only; no GPU framebuffer or natural loop", "engine":Engine.get_version_info()["string"],"display_server":DisplayServer.get_name(),"checks":records,"passed":records.size()-failed.size(),"total":records.size(),"failed":failed,"godot_geometry_masks":mask_records}
 FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 print("TA_HEAVY_COLD ",report.status," ",report.passed,"/",report.total)
 quit(0 if failed.is_empty() else 1)
