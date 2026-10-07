extends SceneTree
## 只渲染七个新方向的待机和受击；两条已过正向动作原样读入。
const Rig=preload("res://rig.gd")
const UNIT="enemy_patrol"
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
 var catalog:Dictionary={"version":"v025-patrol-idle-hit","scope":"14 new clips / 56 new frames; two down actions preserved","status":"PENDING_TA_REVIEW","rig_sha256":FileAccess.get_sha256("res://rig.json"),"root":[64,104],"canvas":[128,128],"clips":[]}
 for kind:String in spec.actions:
  for direction:String in spec.directions:
   var action:=kind+"_"+direction
   var directory:="res://output/"+UNIT+"/"+action
   var path:=directory+".png"
   var poses:Array=[]
   var fresh:bool=spec.configs.has(direction)
   if fresh:
    DirAccess.make_dir_recursive_absolute(directory)
    var rig:=Rig.new()
    rig.direction=direction
    viewport.add_child(rig)
    await process_frame
    var atlas:=Image.create(512,128,false,Image.FORMAT_RGBA8)
    atlas.fill(Color.TRANSPARENT)
    for index in range(4):
     poses.append(rig.pose_action(kind,index))
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
   saved.set_animation_speed(action,spec.actions[kind].fps)
   saved.set_animation_loop(action,spec.actions[kind].loop)
   var texture:=ImageTexture.create_from_image(atlas)
   var hashes:Array=[]
   for index in range(4):
    hashes.append(FileAccess.get_sha256("%s/f%02d.png"%[directory,index]))
    var region:=AtlasTexture.new()
    region.atlas=texture
    region.region=Rect2(index*128,0,128,128)
    saved.add_frame(action,region)
   for background:String in ["white","black"]:
    var contact:=Image.create(512,128,false,Image.FORMAT_RGBA8)
    contact.fill(Color.WHITE if background=="white" else Color.BLACK)
    for index in range(4):contact.blend_rect(atlas,Rect2i(index*128,0,128,128),Vector2i(index%4*128,index/4*128))
    contact.save_png("res://qa/"+action+"_"+background+"_1x.png")
    contact.resize(2048,512,Image.INTERPOLATE_NEAREST)
    contact.save_png("res://qa/"+action+"_"+background+"_4x.png")
   catalog.clips.append({"unit":UNIT,"action":action,"direction":direction,"status":"PENDING_TA_REVIEW" if fresh else "PRESERVED_TA_APPROVED","frame_count":4,"fps":spec.actions[kind].fps,"loop":spec.actions[kind].loop,"atlas":path,"atlas_sha256":FileAccess.get_sha256(path),"frame_hashes":hashes,"poses":poses})
 var tres:="res://output/"+UNIT+"_idle_hit_v025.tres"
 ResourceSaver.save(saved,tres)
 catalog.tres=tres
 catalog.tres_sha256=FileAccess.get_sha256(tres)
 FileAccess.open("res://output/catalog.json",FileAccess.WRITE).store_string(JSON.stringify(catalog,"\t"))
 print("PATROL_IDLE_HIT_EXPORTED: 14 new clips; two preserved; 16 animations")
 quit()
