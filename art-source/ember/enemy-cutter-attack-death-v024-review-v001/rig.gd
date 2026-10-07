extends Node2D
## 固定像素零件绑定：工具和腿壳不缩放，脚掌固定；短连接带只采样原有蓝灰关节。
var direction:String
var spec:Dictionary
var config:Dictionary
var texture:Texture2D
var parts:Dictionary={}
var pivots:Dictionary={}
var links:Dictionary={}
var materials:Array[ShaderMaterial]=[]
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func xy(v:Vector2)->Array:return [v.x,v.y]
func polygon(a:Array)->PackedVector2Array:
 var result:=PackedVector2Array()
 for v:Array in a:result.append(point(v))
 return result
func inside(p:Vector2,a:Array)->bool:return not a.is_empty() and Geometry2D.is_point_in_polygon(p,polygon(a))
func owner(p:Vector2)->String:
 # 同一母版像素只归一个可见部件；工具优先于其后的支撑腿。
 for item:Dictionary in config.ownership_overrides:
  if inside(p,item.polygon):return item.owner
 for t:Dictionary in config.tools:
  var selected:=inside(p,t.polygon)
  for shape:Array in t.extra_polygons:
   if inside(p,shape):selected=true
  if selected:return t.id+"_blade" if inside(p,t.blade_polygon) else t.id
 var protected:=false
 for shape:Array in config.protected_body_polygons:
  if inside(p,shape):protected=true
 if not protected:
  for leg:Dictionary in config.parts:
   if inside(p,leg.polygon):return leg.id+"_foot" if p.y>=float(leg.foot_cut_y) else leg.id
 return "body"
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 config=spec.configs[direction]
 texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(config.source)))
 pivots.body=Vector2.ZERO
 var definitions:Array=config.parts.duplicate()
 for t:Dictionary in config.tools:
  if t.has("socket"):definitions.append(t)
  if t.has("spindle"):definitions.append({"id":t.id+"_spindle","socket":t.spindle})
 for leg:Dictionary in config.parts:
  pivots[leg.id]=point(leg.pivot)
  pivots[leg.id+"_foot"]=Vector2.ZERO
 for t:Dictionary in config.tools:
  pivots[t.id]=point(t.pivot)
  if not t.blade_polygon.is_empty():pivots[t.id+"_blade"]=point(t.hub)
 var masks:Dictionary={}
 for id:String in pivots:masks[id]=Image.create(128,128,false,Image.FORMAT_R8)
 for y in range(128):
  for x in range(128):masks[owner(Vector2(x+.5,y+.5))].set_pixel(x,y,Color.WHITE)
 for id:String in pivots:
  var node:=Node2D.new()
  node.position=pivots[id]
  node.z_index=5 if id=="body" else (6 if id in ["saw","saw_blade","claw"] else 0)
  var sprite:=Sprite2D.new()
  sprite.texture=texture
  sprite.centered=false
  sprite.position=-pivots[id]
  var mat:=ShaderMaterial.new()
  mat.shader=load("res://part.gdshader")
  mat.set_shader_parameter("ownership",ImageTexture.create_from_image(masks[id]))
  mat.set_shader_parameter("sensor_rect",Vector4(config.sensor_rect[0],config.sensor_rect[1],config.sensor_rect[2],config.sensor_rect[3]))
  sprite.material=mat
  materials.append(mat)
  node.add_child(sprite)
  add_child(node)
  parts[id]=node
 for leg:Dictionary in definitions:
  var node:=Polygon2D.new()
  node.texture=texture
  node.z_index=-10
  var r:Array=leg.socket.source_rect
  var lo:=Vector2(r[0]+.001,r[1]+.001)
  var hi:=Vector2(r[0]+r[2]-.001,r[1]+r[3]-.001)
  node.uv=PackedVector2Array([lo,Vector2(hi.x,lo.y),hi,Vector2(lo.x,hi.y)])
  add_child(node)
  links[leg.id]=node
 pose_action("attack",0)
func pose_action(action:String,index:int)->Dictionary:
 var values:Dictionary=spec.actions[action]
 var delta:=Vector2(0,values.body_y[index])
 for id:String in parts:parts[id].transform=Transform2D(0,pivots[id])
 parts.body.position=delta
 for mat:ShaderMaterial in materials:mat.set_shader_parameter("sensor_power",float(values.power[index]))
 var record:Dictionary={"action":action,"direction":direction,"frame":index,"root":[64,104],"body_translation":xy(delta),"supports":{},"part_transforms":{},"socket_polygons":{},"sensor_power":values.power[index]}
 for leg:Dictionary in config.parts:
  var node:Node2D=parts[leg.id]
  var angle:=deg_to_rad(float(values.fold[index])*float(leg.fold_sign)*float(leg.fold_multiplier))
  # 靠脚掌的轴承为折叠中心。被遮住而没有脚掌的远腿随机身收纳。
  if leg.sole!=null:
   var ankle:=point(leg.ankle)
   node.transform=Transform2D(angle,ankle+(point(leg.pivot)-ankle).rotated(angle))
  else:node.position+=delta
  var a:=point(leg.socket.start)+delta
  var b:Vector2=node.transform*(point(leg.socket.end)-point(leg.pivot))
  var normal:=Vector2(-(b-a).y,(b-a).x).normalized()*float(leg.socket.width)*.5
  links[leg.id].polygon=PackedVector2Array([a-normal,a+normal,b+normal,b-normal])
  record.socket_polygons[leg.id]=[]
  for v:Vector2 in links[leg.id].polygon:record.socket_polygons[leg.id].append(xy(v))
  record.supports[leg.id]={"sole":leg.sole,"ground":leg.sole,"support":leg.sole!=null,"foot_cut_y":leg.foot_cut_y}
 for t:Dictionary in config.tools:
  var angle:=deg_to_rad(float(t.attack_angle if action=="attack" else t.death_angle)*float(values.swing[index]))
  var pivot:=point(t.pivot)
  parts[t.id].transform=Transform2D(angle,pivot+delta)
  if not t.blade_polygon.is_empty():
   var hub:Vector2=pivot+delta+(point(t.hub)-pivot).rotated(angle)
   # 锯片在已投影的椭圆平面内转动，平面宽高比固定。
   var spin:=deg_to_rad(float(values.blade[index]))
   var radius:=point(t.radius)
   var basis_x:=Vector2(cos(spin),sin(spin)*radius.y/radius.x).rotated(angle)
   var basis_y:=Vector2(-sin(spin)*radius.x/radius.y,cos(spin)).rotated(angle)
   parts[t.id+"_blade"].transform=Transform2D(basis_x,basis_y,hub)
  if t.has("socket"):
   var a:=point(t.socket.start)+delta
   var b:Vector2=parts[t.id].transform*(point(t.socket.end)-pivot)
   var normal:=Vector2(-(b-a).y,(b-a).x).normalized()*float(t.socket.width)*.5
   links[t.id].polygon=PackedVector2Array([a-normal,a+normal,b+normal,b-normal])
   record.socket_polygons[t.id]=[]
   for v:Vector2 in links[t.id].polygon:record.socket_polygons[t.id].append(xy(v))
  if t.has("spindle"):
   var a:Vector2=parts[t.id].transform*(point(t.spindle.start)-pivot)
   var b:Vector2=parts[t.id].transform*(point(t.spindle.end)-pivot)
   var normal:=Vector2(-(b-a).y,(b-a).x).normalized()*float(t.spindle.width)*.5
   var key:String=t.id+"_spindle"
   links[key].polygon=PackedVector2Array([a-normal,a+normal,b+normal,b-normal])
   record.socket_polygons[key]=[]
   for v:Vector2 in links[key].polygon:record.socket_polygons[key].append(xy(v))
 for id:String in parts:
  var t:Transform2D=parts[id].transform
  record.part_transforms[id]={"position":xy(t.origin),"basis_x":xy(t.x),"basis_y":xy(t.y)}
 return record
