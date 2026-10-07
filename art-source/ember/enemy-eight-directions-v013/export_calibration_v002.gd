extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://calibration_registration_v002.json"))
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(128,128)
 viewport.transparent_bg=true
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 var sprite:=Sprite2D.new()
 sprite.centered=false
 sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 var material:=ShaderMaterial.new()
 material.shader=load("res://entity_cutout.gdshader")
 sprite.material=material
 viewport.add_child(sprite)
 var rows:Array=[]
 for unit:Dictionary in data.units:
  var directory:="res://calibration_check_v002/"+str(unit.unit)
  DirAccess.make_dir_recursive_absolute(directory)
  DirAccess.copy_absolute(ProjectSettings.globalize_path("res://source/approved_down/"+str(unit.unit)+".png"),ProjectSettings.globalize_path(directory+"/approved_down.png"))
  rows.append({"unit":unit.unit,"view":"approved_down","path":directory+"/approved_down.png","sha256":FileAccess.get_sha256(directory+"/approved_down.png")})
  for view:Dictionary in unit.views:
   var atlas:=AtlasTexture.new()
   atlas.atlas=load(str(unit.source))
   var r:Array=view.source_rect
   atlas.region=Rect2(r[0],r[1],r[2],r[3])
   sprite.texture=atlas
   sprite.scale=Vector2.ONE*float(unit.common_scale)
   sprite.position=Vector2(64,float(unit.target_anchor_y))-Vector2(view.source_anchor[0],view.source_anchor[1])*float(unit.common_scale)
   await process_frame
   await RenderingServer.frame_post_draw
   var frame:=viewport.get_texture().get_image()
   frame.convert(Image.FORMAT_RGBA8)
   for y in range(128):
    for x in range(128):
     if frame.get_pixel(x,y).a8==0:frame.set_pixel(x,y,Color.TRANSPARENT)
   var path:=directory+"/"+str(view.direction)+".png"
   frame.save_png(path)
   rows.append({"unit":unit.unit,"view":view.direction,"path":path,"sha256":FileAccess.get_sha256(path),"bounds":str(frame.get_used_rect()),"registration":view})
 for background:String in ["white","black"]:
  var contact:=Image.create(512,256,false,Image.FORMAT_RGBA8)
  contact.fill(Color.WHITE if background=="white" else Color.BLACK)
  for index in range(rows.size()):
   var frame:=Image.load_from_file(ProjectSettings.globalize_path(rows[index].path))
   contact.blend_rect(frame,Rect2i(0,0,128,128),Vector2i((index%4)*128,(index/4)*128))
  contact.save_png("res://calibration_check_v002/comparison_"+background+"_1x.png")
  contact.resize(2048,1024,Image.INTERPOLATE_NEAREST)
  contact.save_png("res://calibration_check_v002/comparison_"+background+"_4x.png")
 FileAccess.open("res://calibration_check_v002/catalog.json",FileAccess.WRITE).store_string(JSON.stringify({"scope":"two units, generated front plus SW/SE only; not seven-direction resubmission","status":"PENDING_CALIBRATION_REVIEW","registration_sha256":FileAccess.get_sha256("res://calibration_registration_v002.json"),"columns":["approved_down","generated_front","down_left","down_right"],"rows":rows},"\t"))
 print("EXPORTED_CALIBRATION_CHECK_V002")
 quit()
