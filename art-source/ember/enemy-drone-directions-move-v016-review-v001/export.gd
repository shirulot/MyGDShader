extends SceneTree
## 只渲染六个新方向。两个已通过动作从磁盘原样读入，不重新导出。
const Rig=preload("res://rig.gd")
const UNIT="enemy_scout_drone"
func _initialize()->void:call_deferred("run")

func read_viewport_frame(viewport:SubViewport)->Image:
 var image:=viewport.get_texture().get_image()
 image.convert(Image.FORMAT_RGBA8)
 for y in range(128):
  for x in range(128):
   if image.get_pixel(x,y).a8==0:image.set_pixel(x,y,Color.TRANSPARENT)
 return image

func run()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(128,128)
 viewport.transparent_bg=true
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 var saved:=SpriteFrames.new()
 saved.remove_animation("default")
 var catalog:Dictionary={"version":"v016-drone-move","scope":"6 new moves / 48 new frames; down and down_right preserved","status":"PENDING_TA_REVIEW","rig_sha256":FileAccess.get_sha256("res://rig.json"),"root":[64,104],"canvas":[128,128],"clips":[]}
 var requested:=OS.get_cmdline_user_args()
 var previous:Dictionary={}
 if not requested.is_empty():previous=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog.json"))
 for direction:String in spec.directions:
  var action:="move_"+direction
  var directory:="res://output/"+UNIT+"/"+action
  var path:=directory+".png"
  var poses:Array=[]
  var fresh:bool=spec.configs.has(direction)
  var regenerate:bool=fresh and (requested.is_empty() or direction in requested)
  if fresh and not regenerate:
   for old:Dictionary in previous.clips:
    if old.direction==direction:poses=old.poses
  if regenerate:
   DirAccess.make_dir_recursive_absolute(directory)
   var rig:=Rig.new()
   rig.direction=direction
   viewport.add_child(rig)
   await process_frame
   var atlas:=Image.create(1024,128,false,Image.FORMAT_RGBA8)
   atlas.fill(Color.TRANSPARENT)
   for index in range(8):
    poses.append(rig.pose(index))
    await process_frame
    await RenderingServer.frame_post_draw
    var frame:=read_viewport_frame(viewport)
    assert(frame.get_used_rect().has_area(),"Empty export: "+action)
    frame.save_png("%s/f%02d.png"%[directory,index])
    if index==0:frame.save_png("res://qa/bind_"+direction+".png")
    atlas.blit_rect(frame,Rect2i(0,0,128,128),Vector2i(index*128,0))
   atlas.save_png(path)
   rig.queue_free()
   await process_frame
  var atlas:=Image.load_from_file(ProjectSettings.globalize_path(path))
  saved.add_animation(action)
  saved.set_animation_speed(action,8)
  saved.set_animation_loop(action,true)
  var texture:=ImageTexture.create_from_image(atlas)
  var hashes:Array=[]
  for index in range(8):
   hashes.append(FileAccess.get_sha256("%s/f%02d.png"%[directory,index]))
   var region:=AtlasTexture.new()
   region.atlas=texture
   region.region=Rect2(index*128,0,128,128)
   saved.add_frame(action,region)
  for background:String in ["white","black"]:
   var contact:=Image.create(512,256,false,Image.FORMAT_RGBA8)
   contact.fill(Color.WHITE if background=="white" else Color.BLACK)
   for index in range(8):contact.blend_rect(atlas,Rect2i(index*128,0,128,128),Vector2i(index%4*128,index/4*128))
   contact.save_png("res://qa/"+action+"_"+background+"_1x.png")
   contact.resize(2048,1024,Image.INTERPOLATE_NEAREST)
   contact.save_png("res://qa/"+action+"_"+background+"_4x.png")
  catalog.clips.append({"unit":UNIT,"action":action,"direction":direction,"status":"PENDING_TA_REVIEW" if fresh else "PRESERVED_TA_APPROVED","frame_count":8,"fps":8,"loop":true,"atlas":path,"atlas_sha256":FileAccess.get_sha256(path),"frame_hashes":hashes,"poses":poses})
 var tres:="res://output/"+UNIT+"_move_v016.tres"
 ResourceSaver.save(saved,tres)
 catalog.tres=tres
 catalog.tres_sha256=FileAccess.get_sha256(tres)
 FileAccess.open("res://output/catalog.json",FileAccess.WRITE).store_string(JSON.stringify(catalog,"\t"))
 print("DRONE_MOVE_EXPORTED: six new clips; two preserved; eight animations in SpriteFrames")
 quit()
