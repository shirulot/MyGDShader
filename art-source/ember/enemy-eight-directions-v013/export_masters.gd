extends SceneTree
## 一次方向母版注册：每单位共同缩放，每方向固定偏移。down直接复制批准帧。
func _initialize()->void:call_deferred("run")
func run()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://registration.json"))
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
 var units:Array=[]
 for unit:Dictionary in spec.units:
  units.append(unit.unit)
  var source:=load(str(unit.source)) as Texture2D
  var directory:="res://output/"+str(unit.unit)
  DirAccess.make_dir_recursive_absolute(directory)
  for view:Dictionary in unit.views:
   var texture:=AtlasTexture.new()
   texture.atlas=source
   var r:Array=view.source_rect
   # 部分原画跨越网格：只裁源归属，不重新居中或缩放角色。
   var owned:Array=view.get("owned_rect",[0,0,r[2],r[3]])
   texture.region=Rect2(r[0]+owned[0],r[1]+owned[1],owned[2],owned[3])
   sprite.texture=texture
   sprite.position=Vector2(view.offset[0],view.offset[1])+Vector2(owned[0],owned[1])*float(unit.common_scale)
   sprite.scale=Vector2.ONE*float(unit.common_scale)
   await process_frame
   await RenderingServer.frame_post_draw
   var image:=viewport.get_texture().get_image()
   image.convert(Image.FORMAT_RGBA8)
   for y in range(128):
    for x in range(128):
     if image.get_pixel(x,y).a8==0:image.set_pixel(x,y,Color.TRANSPARENT)
   var path:=directory+"/neutral_"+str(view.direction)+".png"
   if view.direction=="down":
    image.save_png("res://qa/"+str(unit.unit)+"_generated_front.png")
    DirAccess.copy_absolute(ProjectSettings.globalize_path(unit.approved_down),ProjectSettings.globalize_path(path))
    image=Image.load_from_file(ProjectSettings.globalize_path(path))
   else:image.save_png(path)
   if view.direction=="down_right":
    var detail:=Image.create(128,128,false,Image.FORMAT_RGBA8)
    detail.fill(Color("d2d6dc"))
    detail.blend_rect(image,Rect2i(0,0,128,128),Vector2i.ZERO)
    detail.resize(1024,1024,Image.INTERPOLATE_NEAREST)
    detail.save_png("res://qa/"+str(unit.unit)+"_down_right_8x.png")
   rows.append({"unit":unit.unit,"direction":view.direction,"path":path,"sha256":FileAccess.get_sha256(path),"bounds":str(image.get_used_rect()),"scale":unit.common_scale,"offset":view.offset,"status":"PRESERVED_APPROVED_DOWN" if view.direction=="down" else "DIRECTION_MASTER_PENDING_TA"})
 for background:String in ["white","black"]:
  var contact:=Image.create(8*128,4*128,false,Image.FORMAT_RGBA8)
  contact.fill(Color.WHITE if background=="white" else Color.BLACK)
  for index in range(rows.size()):
   var image:=Image.load_from_file(ProjectSettings.globalize_path(rows[index].path))
   contact.blend_rect(image,Rect2i(0,0,128,128),Vector2i((index%8)*128,(index/8)*128))
  contact.save_png("res://qa/eight_direction_masters_"+background+"_1x.png")
  contact.resize(4096,2048,Image.INTERPOLATE_NEAREST)
  contact.save_png("res://qa/eight_direction_masters_"+background+"_4x.png")
 FileAccess.open("res://output/master_catalog_v013.json",FileAccess.WRITE).store_string(JSON.stringify({"status":"FIRST_GATE_CANDIDATE","directions":["down","down_left","left","up_left","up","up_right","right","down_right"],"units":units,"registration_sha256":FileAccess.get_sha256("res://registration.json"),"masters":rows},"\t"))
 print("EXPORTED_32_DIRECTION_MASTERS_DOWN_PRESERVED")
 quit()
