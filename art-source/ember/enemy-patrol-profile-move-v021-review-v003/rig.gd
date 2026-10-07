extends Node2D
## 解剖左右和已过正向保持同一脚步相位。仅短深色连杆使用端点映射；护膝与靴子保持刚性。
var direction:String
var spec:Dictionary
var config:Dictionary
var parts:Dictionary={}
var body:Node2D
var texture:Texture2D
var far_texture:Texture2D
var near_texture:Texture2D
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func xy(v:Vector2)->Array:return [v.x,v.y]
func polygon(a:Array)->PackedVector2Array:
 var points:=PackedVector2Array()
 for v:Array in a:points.append(point(v))
 return points
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 config=spec.configs[direction]
 texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(config.get("body_source",config.source))))
 far_texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(config.far_source)))
 near_texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(config.near_source)))
 var excluded:Array=[]
 for part:Dictionary in config.parts:
  if part.source_kind=="canonical":excluded.append(part.polygon)
 excluded.append_array(config.occluded_original_polygons)
 body=make_part("body",Vector2.ZERO,[],excluded,10)
 for part:Dictionary in config.parts:make_part(part.id,point(part.pivot),[part.polygon],part.exclude,part.z,part.source_kind)
func make_part(id:String,pivot:Vector2,includes:Array,excludes:Array,z:int,source_kind:String="canonical")->Node2D:
 var mask:=Image.create(128,128,false,Image.FORMAT_R8)
 for y in range(128):
  for x in range(128):
   var p:=Vector2(x+.5,y+.5)
   var owned:bool=includes.is_empty()
   for shape:Array in includes:
    if Geometry2D.is_point_in_polygon(p,polygon(shape)):owned=true
   for shape:Array in excludes:
    if Geometry2D.is_point_in_polygon(p,polygon(shape)):owned=false
   # 手持工具和夹爪与身体保持刚性，不能被邻近大腿的矩形范围捎带移动。
   for shape:Array in config.get("protected_body_polygons",[]):
    if source_kind=="canonical" and Geometry2D.is_point_in_polygon(p,polygon(shape)):owned=id=="body"
   mask.set_pixel(x,y,Color.WHITE if owned else Color.BLACK)
 var node:=Node2D.new()
 node.position=pivot
 node.z_index=z
 var sprite:=Sprite2D.new()
 sprite.centered=false
 sprite.texture=far_texture if source_kind=="far" else (near_texture if source_kind=="near" else texture)
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
 for part:Dictionary in config.parts:parts[part.id].transform=Transform2D(0,point(part.pivot))
func world_knee(bob:float,depth:float,lift:float)->Vector2:
 var hip:=Vector2(32-bob/.75,0)
 var ankle:=Vector2(8+lift,depth)
 var axis:=ankle-hip
 var length:=axis.length()
 var unit:=axis/length
 return hip+unit*length/2+Vector2(unit.y,-unit.x)*sqrt(maxf(0,169-length*length/4))
func project_delta(v:Vector2)->Vector2:
 return Vector2(roundf(v.y*float(config.heading[0])*.7),roundf(-v.x*.75+v.y*.35*float(config.heading[1])))
func pose(index:int)->Dictionary:
 reset_bind()
 var phase:Dictionary=spec.phases[index]
 body.position.y=phase.body_y
 var rest_knee:=world_knee(0,0,0)
 var record:Dictionary={"unit":"enemy_patrol","action":"move_"+direction,"frame":index,"root":[64,104],"supports":{},"part_transforms":{}}
 for side:String in ["right","left"]:
  var leg:Dictionary=config.legs[side]
  var foot:Dictionary=phase[side]
  var hip:=point(leg.hip)+body.position
  var knee:=point(leg.knee)+project_delta(world_knee(phase.body_y,foot.depth,foot.lift)-rest_knee)
  var ankle:=point(leg.ankle)+project_delta(Vector2(foot.lift,foot.depth))
  for part:Dictionary in config.parts:
   if part.id==side+"_thigh":
    apply_segment(part.id,hip,knee+point(part.end)-point(leg.knee))
   elif part.id==side+"_shin":
    apply_segment(part.id,knee+point(part.pivot)-point(leg.knee),ankle+point(part.end)-point(leg.ankle))
  parts[side+"_cap"].position=knee
  parts[side+"_foot"].position=ankle
  record.supports[side]={"hip":xy(hip),"knee":xy(knee),"ankle":xy(ankle),"sole":xy(ankle+point(leg.sole_offset)),"ground":xy(point(leg.ankle)+point(leg.sole_offset)+project_delta(Vector2(0,foot.depth))),"support":foot.support,"depth":foot.depth,"lift":foot.lift}
 for part:String in parts:
  var transform:Transform2D=parts[part].transform
  record.part_transforms[part]={"position":xy(transform.origin),"basis_x":xy(transform.x),"basis_y":xy(transform.y)}
 return record
func apply_segment(id:String,start:Vector2,end:Vector2)->void:
 for part:Dictionary in config.parts:
  if part.id!=id:continue
  var rest:=point(part.end)-point(part.pivot)
  var current:=end-start
  var rest_axis:=rest.normalized()
  var rest_normal:=Vector2(-rest_axis.y,rest_axis.x)
  var target_axis:=current/rest.length()
  var target_normal:=Vector2(-current.y,current.x).normalized()
  parts[id].transform=Transform2D(target_axis*rest_axis.x+target_normal*rest_normal.x,target_axis*rest_axis.y+target_normal*rest_normal.y,start)
  assert((parts[id].transform*rest).distance_to(end)<.0001)
