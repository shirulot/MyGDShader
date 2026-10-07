extends SceneTree
## 保留原近腿可见甲片和靴，远腿使用同朝向的同设计零件实例。
## 这是固定源纹理的骨架装配，没有重绘 RGB；所有差异交给造型闸门单独审。
func _initialize()->void:call_deferred("run")
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func poly(a:Array)->PackedVector2Array:
 var result:=PackedVector2Array()
 for p:Array in a:result.append(point(p))
 return result
func read_frame(v:SubViewport)->Image:
 var frame:=v.get_texture().get_image()
 frame.convert(Image.FORMAT_RGBA8)
 for y in range(128):
  for x in range(128):
   if frame.get_pixel(x,y).a8==0:frame.set_pixel(x,y,Color.TRANSPARENT)
 return frame
func run()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://calibration.json"))
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(128,128)
 viewport.transparent_bg=true
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 for direction:String in spec.configs:
  var cfg:Dictionary=spec.configs[direction]
  var original:=Image.load_from_file(ProjectSettings.globalize_path("res://source/"+direction+".png"))
  var texture:=ImageTexture.create_from_image(original)
  var actor:=Node2D.new()
  viewport.add_child(actor)
  var groups:Dictionary={}
  for group:String in ["far","near","body"]:
   var container:=Node2D.new()
   container.position=point(cfg.offset) if group=="far" else Vector2.ZERO
   container.z_index=-1 if group=="far" else (2 if group=="body" else 1)
   actor.add_child(container)
   groups[group]=container
   var mask:=Image.create(128,128,false,Image.FORMAT_R8)
   for y in range(128):
    for x in range(128):
     var p:=Vector2(x+.5,y+.5)
     var protected:=false
     for shape:Array in cfg.protected:
      if Geometry2D.is_point_in_polygon(p,poly(shape)):protected=true
     var owned:bool=not Rect2(50,84,27,44).has_point(p) or protected if group=="body" else (Geometry2D.is_point_in_polygon(p,poly(cfg.cap)) or Geometry2D.is_point_in_polygon(p,poly(cfg.shin)) or Geometry2D.is_point_in_polygon(p,poly(cfg.foot))) and not protected
     mask.set_pixel(x,y,Color.WHITE if owned else Color.BLACK)
   var sprite:=Sprite2D.new()
   sprite.centered=false
   sprite.texture=texture
   sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
   var material:=ShaderMaterial.new()
   material.shader=load("res://masked_part.gdshader")
   material.set_shader_parameter("ownership",ImageTexture.create_from_image(mask))
   sprite.material=material
   container.add_child(sprite)
   if group!="body":
    var bridge:=Polygon2D.new()
    bridge.z_index=-1
    bridge.texture=texture
    bridge.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
    var a:=point(cfg.socket_start)
    var b:=point(cfg.socket_end)
    var n:=Vector2(-(b-a).y,(b-a).x).normalized()*2
    bridge.polygon=PackedVector2Array([a-n,a+n,b+n,b-n])
    var uv:Array=cfg.socket_uv
    var lo:=Vector2(uv[0]+.001,uv[1]+.001)
    var hi:=Vector2(uv[0]+uv[2]-.001,uv[1]+uv[3]-.001)
    bridge.uv=PackedVector2Array([lo,Vector2(hi.x,lo.y),hi,Vector2(lo.x,hi.y)])
    container.add_child(bridge)
  await process_frame
  await RenderingServer.frame_post_draw
  read_frame(viewport).save_png("res://output/neutral_"+direction+".png")
  for name:String in groups:
   for key:String in groups:groups[key].visible=key==name
   await process_frame
   await RenderingServer.frame_post_draw
   read_frame(viewport).save_png("res://output/"+direction+"_"+name+".png")
  actor.queue_free()
  await process_frame
 var contact:=Image.create(1024,512,false,Image.FORMAT_RGBA8)
 contact.fill(Color("dddddd"))
 for row in range(2):
  var d:String=["left","right"][row]
  for col in range(4):
   var image:=Image.load_from_file(ProjectSettings.globalize_path(("res://source/"+d+".png") if col%2==0 else ("res://output/neutral_"+d+".png")))
   var panel:=Image.create(128,128,false,Image.FORMAT_RGBA8)
   panel.fill(Color("dddddd") if col<2 else Color("080b10"))
   panel.blend_rect(image,Rect2i(0,0,128,128),Vector2i.ZERO)
   panel.resize(256,256,Image.INTERPOLATE_NEAREST)
   contact.blit_rect(panel,Rect2i(0,0,256,256),Vector2i(col*256,row*256))
 contact.save_png("res://qa/original_candidate_2x.png")
 quit()
