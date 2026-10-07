extends Node2D
## 四足对角相位。原生腿壳保持刚体，隐藏安装座只允许短行程。
var direction:String
var spec:Dictionary
var config:Dictionary
var parts:Dictionary={}
var body:Node2D
var texture:Texture2D
var sockets:Dictionary={}
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func xy(v:Vector2)->Array:return [v.x,v.y]
func polygon(a:Array)->PackedVector2Array:
 var result:=PackedVector2Array()
 for v:Array in a:result.append(point(v))
 return result
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 config=spec.configs[direction]
 texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(config.source)))
 var excluded:Array=[]
 for p:Dictionary in config.parts:excluded.append(p.polygon)
 body=make_part("body",Vector2.ZERO,[],excluded,5)
 for p:Dictionary in config.parts:make_part(p.id,point(p.pivot),[p.polygon]+p.overlap_polygons,[],p.z)
 for p:Dictionary in config.parts:
  var link:=Polygon2D.new()
  link.texture=texture
  link.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
  link.z_index=-10
  var r:Array=p.socket.source_rect
  # Nearest 的端点也留在注册矩形内部，避免边界精度误采相邻黄铜像素。
  var lo:=Vector2(r[0]+.001,r[1]+.001)
  var hi:=Vector2(r[0]+r[2]-.001,r[1]+r[3]-.001)
  link.uv=PackedVector2Array([lo,Vector2(hi.x,lo.y),hi,Vector2(lo.x,hi.y)])
  add_child(link)
  sockets[p.id]=link
  update_socket(p,Vector2.ZERO)
func update_socket(p:Dictionary,travel:Vector2)->void:
 var a:=point(p.socket.start)+body.position
 var b:=point(p.socket.end)+travel
 var n:=Vector2(-(b-a).y,(b-a).x).normalized()*float(p.socket.width)*.5
 sockets[p.id].polygon=PackedVector2Array([a-n,a+n,b+n,b-n])
func make_part(id:String,pivot:Vector2,includes:Array,excludes:Array,z:int)->Node2D:
 var mask:=Image.create(128,128,false,Image.FORMAT_R8)
 for y in range(128):
  for x in range(128):
   var sample:=Vector2(x+.5,y+.5)
   var owned:bool=includes.is_empty()
   for shape:Array in includes:
    if Geometry2D.is_point_in_polygon(sample,polygon(shape)):owned=true
   for shape:Array in excludes:
    if Geometry2D.is_point_in_polygon(sample,polygon(shape)):owned=false
   for shape:Array in config.protected_body_polygons:
    if Geometry2D.is_point_in_polygon(sample,polygon(shape)):owned=id=="body"
   mask.set_pixel(x,y,Color.WHITE if owned else Color.BLACK)
 var node:=Node2D.new()
 node.position=pivot
 node.z_index=z
 var sprite:=Sprite2D.new()
 sprite.centered=false
 sprite.texture=texture
 sprite.position=-pivot
 var material:=ShaderMaterial.new()
 material.shader=load("res://masked_part.gdshader")
 material.set_shader_parameter("ownership",ImageTexture.create_from_image(mask))
 sprite.material=material
 node.add_child(sprite)
 add_child(node)
 parts[id]=node
 return node
func reset_bind()->void:
 body.position=Vector2.ZERO
 for p:Dictionary in config.parts:parts[p.id].transform=Transform2D(0,point(p.pivot))
 for p:Dictionary in config.parts:update_socket(p,Vector2.ZERO)
func pose(index:int)->Dictionary:
 reset_bind()
 body.position.y=spec.body_y[index]
 var record:Dictionary={"unit":"enemy_cutter","action":"move_"+direction,"frame":index,"root":[64,104],"supports":{},"part_transforms":{},"body_translation":xy(body.position),"hidden_legs":config.hidden_legs,"socket_polygons":{}}
 for p:Dictionary in config.parts:
  var phase:=posmod(index+int(p.phase_offset),8)
  var depth:float=spec.depth[phase]
  var lift:float=spec.lift[phase]
  var travel:=Vector2(roundf(depth*.7*float(config.heading[0])),roundf(depth*.35*float(config.heading[1])-lift))
  parts[p.id].position+=travel
  update_socket(p,travel)
  record.socket_polygons[p.id]=[]
  for vertex:Vector2 in sockets[p.id].polygon:record.socket_polygons[p.id].append(xy(vertex))
  var sole:Variant=null
  var ground:Variant=null
  if p.sole!=null:
   sole=xy(point(p.sole)+travel)
   ground=xy(point(p.sole)+Vector2(roundf(depth*.7*float(config.heading[0])),roundf(depth*.35*float(config.heading[1]))))
  record.supports[p.id]={"sole":sole,"ground":ground,"support":lift==0,"depth":depth,"lift":lift,"hidden_mount_travel":xy(travel),"phase":phase}
 for id:String in parts:
  var t:Transform2D=parts[id].transform
  record.part_transforms[id]={"position":xy(t.origin),"basis_x":xy(t.x),"basis_y":xy(t.y)}
 return record
