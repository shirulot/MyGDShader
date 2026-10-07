extends Node2D
## 四条行走腿独立于两条工具臂；固定源部分的尺寸和UV均不随帧变化。
const CLIPS:Dictionary={
 "idle_down":{"fps":4,"loop":true,"poses":[0,1,2,3]},
 "move_down":{"fps":8,"loop":true,"poses":[0,1,2,3,4,5,6,7]},
 "attack_down":{"fps":10,"loop":false,"poses":[0,1,2,3,4,5]},
 "hit_down":{"fps":12,"loop":false,"poses":[0,1,2,3]},
 "death_down":{"fps":10,"loop":false,"poses":[0,1,2,3,4,5,6,7]}
}
var spec:Dictionary
var part_nodes:Dictionary={}
var entity_material:ShaderMaterial
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func xy(p:Vector2)->Array:return [p.x,p.y]
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 entity_material=ShaderMaterial.new()
 entity_material.shader=load("res://entity_cutout.gdshader")
 var leg_material:=entity_material.duplicate() as ShaderMaterial
 leg_material.set_shader_parameter("canonical_source",false)
 for part:Dictionary in spec.parts:
  var node:=Polygon2D.new()
  var pivot:=point(part.pivot)
  var vertices:=PackedVector2Array()
  var uv:=PackedVector2Array()
  if part.has("source_rect"):
   var s:Array=part.source_rect
   var d:Array=part.destination_rect
   for corner:Vector2 in [Vector2(0,0),Vector2(1,0),Vector2(1,1),Vector2(0,1)]:
    vertices.append(Vector2(d[0],d[1])+corner*Vector2(d[2],d[3])-pivot)
    uv.append(Vector2(s[0],s[1])+corner*Vector2(s[2],s[3]))
  else:
   for vertex:Array in part.polygon:
    vertices.append(point(vertex)-pivot)
    uv.append(point(vertex))
  node.polygon=vertices
  node.uv=uv
  node.texture=load(str(part.get("source",spec.source)))
  node.material=leg_material if part.has("source_rect") else entity_material
  node.position=pivot
  node.z_index=part.z
  add_child(node)
  part_nodes[part.id]=node
func pose_action(action:String,index:int)->Dictionary:
 for part:Dictionary in spec.parts:part_nodes[part.id].transform=Transform2D(0,point(part.pivot))
 var body_delta:=Vector2.ZERO
 var body_angle:=0.0
 var saw_angle:=0.0
 var claw_angle:=0.0
 var blade_angle:=0.0
 var leg_fold:=0.0
 var power:=1.0
 var phase:="neutral"
 var stance:Array=["rear_left","rear_right","front_left","front_right"]
 if action=="idle_down":
  body_delta.y=[0,-1,0,1][index]
  phase="quiet_actuator_idle"
 elif action=="move_down":
  var sweep:Array=[2,1,0,-1,-2,-1,0,1]
  var a:float=sweep[index]
  var b:float=sweep[(index+4)%8]
  part_nodes.rear_left.position.y+=a
  part_nodes.front_right.position.y+=a
  part_nodes.front_right_foot.position.y+=a
  part_nodes.rear_right.position.y+=b
  part_nodes.front_left.position.y+=b
  part_nodes.front_left_foot.position.y+=b
  body_delta.y=[0,0,-1,0,0,0,-1,0][index]
  stance=["rear_left","front_right"] if index<4 else ["rear_right","front_left"]
  phase="diagonal_pair_A" if index<4 else "diagonal_pair_B"
 elif action=="attack_down":
  saw_angle=[0,12,22,-18,-8,0][index]
  claw_angle=[0,-3,-6,3,1,0][index]
  blade_angle=[0,15,30,45,15,0][index]
  body_delta.y=[0,-1,-1,1,1,0][index]
  phase=["neutral","saw_windup","ready","short_cut_release","recovery","neutral_recovered"][index]
 elif action=="hit_down":
  body_delta=[Vector2.ZERO,Vector2(0,-1),Vector2(0,1),Vector2.ZERO][index]
  saw_angle=[0,8,-4,0][index]
  claw_angle=[0,-8,4,0][index]
  phase="impact_then_recover"
 else:
  body_delta.y=[0,1,3,5,7,8,8,8][index]
  leg_fold=[0,3,7,12,18,22,22,22][index]
  saw_angle=leg_fold*2.0
  claw_angle=-leg_fold*2.0
  power=[1,0.6,0.2,0,0,0,0,0][index]
  phase=["neutral","power_loss","legs_fold","body_drops","lower_stop","settle","wreck","wreck_hold"][index]
  # 前后腿向机身收拢；每腿仍是一份固定装甲/脚，不复制第二份残骸。
  part_nodes.rear_left.rotation=deg_to_rad(leg_fold)
  part_nodes.rear_right.rotation=deg_to_rad(-leg_fold)
  part_nodes.rear_left.position.y+=body_delta.y
  part_nodes.rear_right.position.y+=body_delta.y
  for side:String in ["left","right"]:
   var ankle:=Vector2(49,96) if side=="left" else Vector2(79,96)
   var angle:=deg_to_rad(leg_fold*1.5*(1.0 if side=="left" else -1.0))
   var id:="front_"+side
   part_nodes[id].transform=Transform2D(0,ankle)*Transform2D(angle,Vector2.ZERO)*Transform2D(0,-ankle)*part_nodes[id].transform
 var torso_transform:=Transform2D(deg_to_rad(body_angle),Vector2(64,85)+body_delta)
 var body_origin:=Vector2(64,85)
 for id:String in ["body","saw_arm","saw_blade","claw_arm"]:
  var original:Transform2D=part_nodes[id].transform
  var transform:=torso_transform*Transform2D(0,-body_origin)*original
  part_nodes[id].transform=transform
 # 工具绕肩转，圆锯再绕自己的轮毂转；支撑腿不继承工具动作。
 var shoulder:Vector2=part_nodes.saw_arm.position
 var saw_rotation:=Transform2D(deg_to_rad(saw_angle),Vector2.ZERO)
 for id:String in ["saw_arm","saw_blade"]:
  var old:Transform2D=part_nodes[id].transform
  part_nodes[id].transform=Transform2D(0,shoulder)*saw_rotation*Transform2D(0,-shoulder)*old
 part_nodes.saw_blade.rotation+=deg_to_rad(blade_angle)
 part_nodes.claw_arm.rotation+=deg_to_rad(claw_angle)
 entity_material.set_shader_parameter("sensor_power",power)
 var record:Dictionary={"action":action,"frame":index,"phase":phase,"root_px":[64,104],"stance":stance,"leg_count":4,"tool_count":2,"body_delta":xy(body_delta),"part_transforms":{},"feet":{}}
 for id:String in part_nodes:
  var node:Polygon2D=part_nodes[id]
  record.part_transforms[id]={"position":xy(node.position),"basis_x":xy(node.transform.x),"basis_y":xy(node.transform.y)}
 for id:String in spec.supports:
  var node_id:=id+"_foot" if id.begins_with("front_") else id
  var part_pivot:Vector2=Vector2.ZERO
  for part:Dictionary in spec.parts:
   if part.id==node_id:part_pivot=point(part.pivot)
  record.feet[id]=xy(part_nodes[node_id].transform*(point(spec.supports[id])-part_pivot))
 return record
