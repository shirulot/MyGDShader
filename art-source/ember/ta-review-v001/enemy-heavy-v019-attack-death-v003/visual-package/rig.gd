extends Node2D
## 源像素归属只登记一次；履带和下底盘固定，炮塔下沉到下底盘之后，短炮作为独立刚体。
var direction:String
var spec:Dictionary
var config:Dictionary
var tower:Sprite2D
var gun:Sprite2D
var gun_pivot:Vector2
var tower_material:ShaderMaterial
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func polygon(a:Array)->PackedVector2Array:
 var p:=PackedVector2Array()
 for v:Array in a:p.append(point(v))
 return p
func texture_from(path:String)->ImageTexture:
 return ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(path)))
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 config=spec.configs[direction]
 var texture:=texture_from(config.source)
 var masks:Dictionary={}
 for id in ["fixed","tower","gun"]:masks[id]=Image.create(128,128,false,Image.FORMAT_R8)
 var gun_shape:=polygon(config.gun.polygon)
 var receiver_shape:=polygon(config.gun.housing_polygon)
 for y in range(128):
  for x in range(128):
   var p:=Vector2(x+.5,y+.5)
   var track:=false
   for shape:Array in config.track_polygons:
    if Geometry2D.is_point_in_polygon(p,polygon(shape)):track=true
   var id:="fixed"
   if not track and y<int(config.tower_bottom):id="tower"
   if not receiver_shape.is_empty() and Geometry2D.is_point_in_polygon(p,receiver_shape):id="fixed"
   # 这两点属于固定炮盾边缘；随炮塔下沉会在 SW 死亡末段留下细悬挂边条。
   for fixed_pixel:Array in config.gun.get("fixed_receiver_pixels",[]):
    if x==int(fixed_pixel[0]) and y==int(fixed_pixel[1]):id="fixed"
   if not gun_shape.is_empty() and Geometry2D.is_point_in_polygon(p,gun_shape):id="gun"
   masks[id].set_pixel(x,y,Color.WHITE)
 var hidden:=Polygon2D.new()
 var registration:Dictionary=config.hidden
 var box:Array=registration.source_rect
 var size:=Vector2(box[2],box[3])*float(registration.scale)
 var top_left:=point(registration.target_bottom)-Vector2(size.x/2,size.y)
 hidden.polygon=PackedVector2Array([top_left,top_left+Vector2(size.x,0),top_left+size,top_left+Vector2(0,size.y)])
 hidden.uv=PackedVector2Array([Vector2(box[0],box[1]),Vector2(box[0]+box[2],box[1]),Vector2(box[0]+box[2],box[1]+box[3]),Vector2(box[0],box[1]+box[3])])
 hidden.texture=texture_from("res://source/hidden_chassis_eight_views_v001.png")
 var hidden_material:=ShaderMaterial.new()
 hidden_material.shader=load("res://hidden_chassis.gdshader")
 hidden_material.set_shader_parameter("canonical_mask",texture)
 hidden_material.set_shader_parameter("y_min",float(registration.canonical_y_min))
 hidden.material=hidden_material
 hidden.z_index=-1
 add_child(hidden)
 if not gun_shape.is_empty():
  var bounds:=Rect2(gun_shape[0],Vector2.ZERO)
  for p:Vector2 in gun_shape:bounds=bounds.expand(p)
  var socket:=Sprite2D.new()
  socket.centered=false
  socket.texture=texture
  var socket_material:=ShaderMaterial.new()
  socket_material.shader=load("res://socket.gdshader")
  socket_material.set_shader_parameter("ownership",ImageTexture.create_from_image(masks.gun))
  socket_material.set_shader_parameter("socket_source",hidden.texture)
  socket_material.set_shader_parameter("source_rect",Vector4(box[0]+box[2]*.4,box[1]+box[3]*.55,box[2]*.2,box[3]*.15))
  socket_material.set_shader_parameter("target_rect",Vector4(bounds.position.x,bounds.position.y,bounds.size.x,bounds.size.y))
  var socket_clip:Array=config.gun.get("socket_clip_rect",[0,0,128,128])
  socket_material.set_shader_parameter("clip_rect",Vector4(socket_clip[0],socket_clip[1],socket_clip[2],socket_clip[3]))
  socket.material=socket_material
  add_child(socket)
 for id in ["fixed","tower","gun"]:
  var node:=Sprite2D.new()
  node.centered=false
  node.texture=texture
  var material:=ShaderMaterial.new()
  material.shader=load("res://part.gdshader")
  material.set_shader_parameter("ownership",ImageTexture.create_from_image(masks[id]))
  var r:Array=config.sensor_rect
  material.set_shader_parameter("sensor_rect",Vector4(r[0],r[1],r[2],r[3]))
  node.material=material
  node.z_index=2 if id=="fixed" else (1 if id=="tower" else 3)
  add_child(node)
  if id=="tower":tower=node;tower_material=material
  if id=="gun":gun=node
 gun_pivot=point(config.gun.pivot)
func pose_action(action:String,index:int)->Dictionary:
 var state:Dictionary=spec.actions[action]
 tower.position=Vector2(0,state.body_y[index])
 tower_material.set_shader_parameter("sensor_power",float(state.power[index]))
 var delta:Vector2=point(config.gun.recoil)*float(state.recoil[index])+Vector2(0,state.gun_y[index])
 var angle:float=float(state.gun_roll[index])*float(config.gun.droop_sign)
 gun.transform=Transform2D(deg_to_rad(angle),gun_pivot+delta)*Transform2D(0,-gun_pivot)
 return {"action":action,"direction":direction,"frame":index,"body_translation":[0,state.body_y[index]],"gun_translation":[delta.x,delta.y],"gun_roll":angle,"gun_pivot":config.gun.pivot,"sensor_power":state.power[index],"supports":config.supports,"root":[64,104],"gun_basis_x":[gun.transform.x.x,gun.transform.x.y],"gun_basis_y":[gun.transform.y.x,gun.transform.y.y]}
