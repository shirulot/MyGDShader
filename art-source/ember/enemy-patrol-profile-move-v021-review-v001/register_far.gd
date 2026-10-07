extends SceneTree
## 新隐藏腿只做一次等比注册；之后动作共享这些固定原生像素。
func _initialize()->void:call_deferred("run")
func run()->void:
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(128,128)
 viewport.transparent_bg=true
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 var texture:=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://source/far_legs_v002.png")))
 var configurations:={"left":{"rect":Rect2(180,240,450,670),"anchor":Vector2(455,896),"target":Vector2(66,101)},"right":{"rect":Rect2(920,240,430,670),"anchor":Vector2(1080,895),"target":Vector2(61,101)}}
 configurations["near_left"]={"rect":Rect2(180,240,450,670),"anchor":Vector2(455,896),"target":Vector2(66,104)}
 configurations["near_right"]={"rect":Rect2(920,240,430,670),"anchor":Vector2(1080,895),"target":Vector2(59,104)}
 var report:Dictionary={"common_scale":23.0/641.0,"generation_exec":"47d5045e-52e1-4cdf-b4ee-dcab347aad38","source_sha256":FileAccess.get_sha256("res://source/far_legs_v002.png"),"directions":{}}
 for direction:String in configurations:
  var cfg:Dictionary=configurations[direction]
  var rect:Rect2=cfg.rect
  var uv:=PackedVector2Array([rect.position,rect.position+Vector2(rect.size.x,0),rect.end,rect.position+Vector2(0,rect.size.y)])
  var points:=PackedVector2Array()
  for p:Vector2 in uv:points.append((p-cfg.anchor)*float(report.common_scale)+cfg.target)
  var part:=Polygon2D.new()
  part.texture=texture;part.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
  part.polygon=points;part.uv=uv
  var material:=ShaderMaterial.new()
  material.shader=load("res://binary_alpha.gdshader")
  part.material=material
  viewport.add_child(part)
  await process_frame
  await RenderingServer.frame_post_draw
  var frame:=viewport.get_texture().get_image()
  frame.convert(Image.FORMAT_RGBA8)
  for y in range(128):
   for x in range(128):
    if frame.get_pixel(x,y).a8==0:frame.set_pixel(x,y,Color.TRANSPARENT)
  var path:="res://source/far_registered_"+direction+".png"
  frame.save_png(path)
  report.directions[direction]={"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"source_anchor":[cfg.anchor.x,cfg.anchor.y],"target_anchor":[cfg.target.x,cfg.target.y],"sha256":FileAccess.get_sha256(path)}
  part.queue_free()
  await process_frame
 FileAccess.open("res://source/far_registration.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 quit()
