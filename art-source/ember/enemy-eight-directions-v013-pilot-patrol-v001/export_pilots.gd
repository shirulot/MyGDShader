extends SceneTree
const Rig=preload("res://pilot_rig.gd")
const UNITS=["enemy_patrol","enemy_tracked_heavy","enemy_cutter","enemy_scout_drone"]
func _initialize()->void:call_deferred("run")
func run()->void:
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(128,128)
 viewport.transparent_bg=true
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 var catalog:Dictionary={"version":"v013-first-gate","status":"CANDIDATE_NOT_TA_APPROVED","scope":"four down_right movement pilots, 32 new frames","rig_spec_sha256":FileAccess.get_sha256("res://pilot_rigs.json"),"rig_script_sha256":FileAccess.get_sha256("res://pilot_rig.gd"),"root":[64,104],"canvas":[128,128],"clips":[]}
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://pilot_rigs.json"))
 for unit:String in spec.enabled_pilot_units:
  if not OS.get_cmdline_user_args().is_empty() and not unit in OS.get_cmdline_user_args():continue
  var rig:=Rig.new()
  rig.unit_id=unit
  viewport.add_child(rig)
  await process_frame
  rig.reset_bind()
  await process_frame
  await RenderingServer.frame_post_draw
  var bind:=read_viewport_frame(viewport)
  bind.save_png("res://output/"+unit+"/rig_neutral_down_right.png")
  var directory:="res://output/"+unit+"/move_down_right"
  DirAccess.make_dir_recursive_absolute(directory)
  var atlas:=Image.create(1024,128,false,Image.FORMAT_RGBA8)
  atlas.fill(Color.TRANSPARENT)
  var records:Array=[]
  var frame_hashes:Array=[]
  var pixel_reports:Array=[]
  for index in range(8):
   records.append(rig.pose(index))
   await process_frame
   await RenderingServer.frame_post_draw
   var frame:=read_viewport_frame(viewport)
   assert(frame.get_used_rect().has_area(),"Empty pilot frame: source or shader did not load")
   var path:="%s/f%02d.png"%[directory,index]
   frame.save_png(path)
   frame_hashes.append(FileAccess.get_sha256(path))
   pixel_reports.append(pixels(frame))
   atlas.blit_rect(frame,Rect2i(0,0,128,128),Vector2i(index*128,0))
  var atlas_path:="res://output/"+unit+"/move_down_right.png"
  atlas.save_png(atlas_path)
  var frames:=SpriteFrames.new()
  frames.remove_animation("default")
  frames.add_animation("move_down_right")
  frames.set_animation_speed("move_down_right",8)
  frames.set_animation_loop("move_down_right",true)
  var texture:=ImageTexture.create_from_image(atlas)
  for index in range(8):
   var sub:=AtlasTexture.new()
   sub.atlas=texture
   sub.region=Rect2(index*128,0,128,128)
   frames.add_frame("move_down_right",sub)
  var tres_path:="res://output/"+unit+"_pilot_v013.tres"
  ResourceSaver.save(frames,tres_path)
  for background:String in ["white","black"]:
   var contact:=Image.create(1024,128,false,Image.FORMAT_RGBA8)
   contact.fill(Color.WHITE if background=="white" else Color.BLACK)
   contact.blend_rect(atlas,Rect2i(0,0,1024,128),Vector2i.ZERO)
   contact.save_png("res://qa/"+unit+"_move_"+background+"_1x.png")
   contact.resize(4096,512,Image.INTERPOLATE_NEAREST)
   contact.save_png("res://qa/"+unit+"_move_"+background+"_4x.png")
   var detail:=Image.create(128,128,false,Image.FORMAT_RGBA8)
   detail.fill(Color.WHITE if background=="white" else Color.BLACK)
   detail.blend_rect(bind,Rect2i(0,0,128,128),Vector2i.ZERO)
   detail.resize(1024,1024,Image.INTERPOLATE_NEAREST)
   detail.save_png("res://qa/"+unit+"_rig_bind_"+background+"_8x.png")
  catalog.clips.append({"unit":unit,"action":"move_down_right","fps":8,"loop":true,"frame_count":8,"atlas":atlas_path,"atlas_sha256":FileAccess.get_sha256(atlas_path),"tres":tres_path,"tres_sha256":FileAccess.get_sha256(tres_path),"bind_sha256":FileAccess.get_sha256("res://output/"+unit+"/rig_neutral_down_right.png"),"frame_hashes":frame_hashes,"poses":records,"pixel_reports":pixel_reports})
  rig.queue_free()
  await process_frame
 catalog.scope="%d down_right movement prototypes, %d new unapproved frames"%[catalog.clips.size(),catalog.clips.size()*8]
 FileAccess.open("res://output/pilot_catalog_v013.json",FileAccess.WRITE).store_string(JSON.stringify(catalog,"\t"))
 print("EXPORTED_PILOT_CLIPS_",catalog.clips.size())
 quit()

func read_viewport_frame(viewport:SubViewport)->Image:
 var frame:=viewport.get_texture().get_image()
 frame.convert(Image.FORMAT_RGBA8)
 for y in range(128):
  for x in range(128):
   if frame.get_pixel(x,y).a8==0:frame.set_pixel(x,y,Color.TRANSPARENT)
 return frame

func pixels(frame:Image)->Dictionary:
 var partial:=0
 var edge:=0
 var visible:=0
 for y in range(128):
  for x in range(128):
   var a:=frame.get_pixel(x,y).a8
   if a>0:
    visible+=1
    if x==0 or x==127 or y==0 or y==127:edge+=1
   if a>0 and a<255:partial+=1
 return {"visible":visible,"partial_alpha":partial,"edge_pixels":edge,"bounds":str(frame.get_used_rect())}
