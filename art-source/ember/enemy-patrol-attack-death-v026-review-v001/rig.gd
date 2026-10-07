extends Node2D
## 前臂固定源区从原身体遮罩分出；腿部沿用过审绑定，整体侧倒使用固定落地轨迹。
const Setup=preload("res://setup_rig.gd")
var direction:String
var spec:Dictionary
var config:Dictionary
var raw:Node2D
var whole:=Node2D.new()
var arms:Dictionary={}
var links:Dictionary={}
var body_material:ShaderMaterial
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func xy(v:Vector2)->Array:return [v.x,v.y]
func polygon(a:Array)->PackedVector2Array:
 var result:=PackedVector2Array()
 for p:Array in a:result.append(point(p))
 return result
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 config=spec.combat[direction]
 add_child(whole)
 var setup:=Setup.new()
 setup.direction=direction
 whole.add_child(setup)
 raw=setup.base
 var sprite:Sprite2D=raw.body.get_child(0)
 var original:Image=sprite.material.get_shader_parameter("ownership").get_image()
 var remaining:=original.duplicate()
 # N 的投射器内缘(75,82)在旧轻动作中被腿遮罩占用；大幅抬臂前一次性归还前臂。
 # 只更正源像素归属，不擦除或重画任何RGB。
 for pixel:Array in config.ownership_transfers:
  remaining.set_pixel(pixel[0],pixel[1],Color.WHITE)
  for id:String in raw.parts:
   if id=="body":continue
   var item:Sprite2D=raw.parts[id].get_child(0)
   var mask:Image=item.material.get_shader_parameter("ownership").get_image()
   mask.set_pixel(pixel[0],pixel[1],Color.BLACK)
   item.material.set_shader_parameter("ownership",ImageTexture.create_from_image(mask))
 for arm:Dictionary in config.arms:
  var mask:=Image.create(128,128,false,Image.FORMAT_R8)
  for y in range(128):
   for x in range(128):
    if remaining.get_pixel(x,y).r>.5 and Geometry2D.is_point_in_polygon(Vector2(x+.5,y+.5),polygon(arm.polygon)):
     mask.set_pixel(x,y,Color.WHITE);remaining.set_pixel(x,y,Color.BLACK)
  var node:=Node2D.new()
  node.position=point(arm.pivot)
  node.z_index=12
  var part:=Sprite2D.new()
  part.centered=false
  part.position=-point(arm.pivot)
  part.texture=raw.texture
  var material:=ShaderMaterial.new()
  material.shader=load("res://masked_part.gdshader")
  material.set_shader_parameter("ownership",ImageTexture.create_from_image(mask))
  part.material=material
  node.add_child(part)
  whole.add_child(node)
  arms[arm.id]=node
  var link:=Polygon2D.new()
  link.texture=raw.texture
  link.z_index=-10
  var r:Array=arm.socket_uv
  var lo:=Vector2(r[0]+.001,r[1]+.001)
  var hi:=Vector2(r[0]+r[2]-.001,r[1]+r[3]-.001)
  link.uv=PackedVector2Array([lo,Vector2(hi.x,lo.y),hi,Vector2(lo.x,hi.y)])
  whole.add_child(link)
  links[arm.id]=link
 body_material=ShaderMaterial.new()
 body_material.shader=load("res://combat_body.gdshader")
 body_material.set_shader_parameter("ownership",ImageTexture.create_from_image(remaining))
 var r:Array=config.sensor_rect
 body_material.set_shader_parameter("sensor_rect",Vector4(r[0],r[1],r[2],r[3]))
 sprite.material=body_material
 pose_action("attack",0)
func pose_action(action:String,index:int)->Dictionary:
 raw.reset_bind()
 whole.transform=Transform2D.IDENTITY
 var values:Dictionary=spec.actions[action]
 var body_y:float=values.body_y[index]
 var delta:=Vector2(0,body_y)
 raw.body.position=delta
 body_material.set_shader_parameter("sensor_power",float(values.power[index]))
 var cfg:Dictionary=raw.spec if direction=="down_right" else raw.config
 var knee_delta:=Vector2(0,roundf(body_y*.6))
 for side:String in ["right","left"]:
  for p:Dictionary in cfg.parts:
   if p.id==side+"_thigh":raw.apply_segment(p.id,point(p.pivot)+delta,point(p.end)+knee_delta)
   elif p.id==side+"_shin":raw.apply_segment(p.id,point(p.pivot)+knee_delta,point(p.end))
   elif p.id==side+"_cap":raw.parts[p.id].position+=knee_delta
 var local_links:Dictionary={}
 for arm:Dictionary in config.arms:
  var pivot:=point(arm.pivot)
  var travel:=point(arm.raise_vector)*float(values.raise_arm[index]) if arm.id=="gun" else Vector2.ZERO
  travel=Vector2(roundf(travel.x),roundf(travel.y))
  var angle:=0.0
  if action=="death" or arm.id=="claw":angle=deg_to_rad(float(values.fold[index])*float(arm.fold_sign))
  arms[arm.id].transform=Transform2D(angle,pivot+delta+travel)
  var a:=point(arm.socket_start)+delta
  var b:Vector2=arms[arm.id].transform*Vector2.ZERO
  var normal:=Vector2(-(b-a).y,(b-a).x).normalized()*float(arm.socket_width)*.5
  links[arm.id].polygon=PackedVector2Array([a-normal,a+normal,b+normal,b-normal])
 if action=="death":
  var sign_x:float=config.fall_sign
  var origin:=Vector2(64+[0,0,0,2,4,6,6,6][index]*sign_x,config.fall_origin_y_keys[index])
  whole.transform=Transform2D(deg_to_rad(float(values.roll[index])*sign_x),origin)*Transform2D(0,Vector2(-64,-80-body_y))
 var record:Dictionary={"action":action,"direction":direction,"frame":index,"root":[64,104],"body_translation":xy(delta),"part_transforms":{},"supports":{},"socket_polygons":{},"sensor_power":values.power[index],"roll_degrees":values.roll[index],"support_phase":action=="attack" or index<3}
 for side:String in ["right","left"]:
  var leg:Dictionary=cfg.legs[side]
  record.supports[side]={"hip":xy(whole.transform*(point(leg.hip)+delta)),"knee":xy(whole.transform*(point(leg.knee)+knee_delta)),"ankle":xy(whole.transform*point(leg.ankle)),"sole":xy(whole.transform*(point(leg.ankle)+point(leg.sole_offset))),"support":action=="attack" or index<3}
 for id:String in raw.parts:
  var t:Transform2D=whole.transform*raw.parts[id].transform
  record.part_transforms[id]={"position":xy(t.origin),"basis_x":xy(t.x),"basis_y":xy(t.y)}
 for id:String in arms:
  var t:Transform2D=whole.transform*arms[id].transform
  record.part_transforms[id]={"position":xy(t.origin),"basis_x":xy(t.x),"basis_y":xy(t.y)}
  record.socket_polygons[id]=[]
  for vertex:Vector2 in links[id].polygon:record.socket_polygons[id].append(xy(whole.transform*vertex))
 if action=="attack" and index==3:record.event="attack_release_visual"
 if action=="death" and index==7:record.event="corpse_hold_visual"
 return record
