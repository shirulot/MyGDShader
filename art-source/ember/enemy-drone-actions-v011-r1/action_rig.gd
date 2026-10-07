extends Node2D
## 叶片来自唯一四叶源图：先绕电机轴旋转，再做固定俯视投影；不逐帧生成。
const CLIPS:Dictionary={
 "idle_down":{"fps":4,"loop":true,"poses":[0,1,2,3]},
 "move_down":{"fps":8,"loop":true,"poses":[0,1,2,3,4,5,6,7]},
 "attack_down":{"fps":10,"loop":false,"poses":[0,1,2,3,4,5]},
 "hit_down":{"fps":12,"loop":false,"poses":[0,1,2,3]},
 "death_down":{"fps":10,"loop":false,"poses":[0,1,2,3,4,5,6,7]}
}
var spec:Dictionary
var part_nodes:Dictionary={}
var fans:Dictionary={}
var rotors:Dictionary={}
var entity_material:ShaderMaterial
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func xy(p:Vector2)->Array:return [p.x,p.y]
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 entity_material=ShaderMaterial.new()
 entity_material.shader=load("res://entity_cutout.gdshader")
 for part:Dictionary in spec.parts:
  var node:=Polygon2D.new()
  var pivot:=point(part.pivot)
  var vertices:=PackedVector2Array()
  var uv:=PackedVector2Array()
  for vertex:Array in part.polygon:
   vertices.append(point(vertex)-pivot)
   uv.append(point(vertex))
  node.polygon=vertices
  node.uv=uv
  node.texture=load(str(spec.source))
  node.material=entity_material
  node.position=pivot
  node.z_index=part.z
  add_child(node)
  part_nodes[part.id]=node
 var fan_material:=ShaderMaterial.new()
 fan_material.shader=load("res://fan_cutout.gdshader")
 for side:String in ["left","right"]:
  var plane:=Node2D.new()
  plane.z_index=2
  add_child(plane)
  fans[side]=plane
  for layer:String in ["well","rotor"]:
   var node:=Polygon2D.new()
   var source:Array=spec[layer+"_source_rect"]
   node.polygon=PackedVector2Array([Vector2(-6.5,-6.5),Vector2(6.5,-6.5),Vector2(6.5,6.5),Vector2(-6.5,6.5)])
   node.uv=PackedVector2Array([Vector2(source[0],source[1]),Vector2(source[0]+source[2],source[1]),Vector2(source[0]+source[2],source[1]+source[3]),Vector2(source[0],source[1]+source[3])])
   node.texture=load(str(spec.fan_source))
   node.material=fan_material
   plane.add_child(node)
   if layer=="rotor":rotors[side]=node
func pose_action(action:String,index:int)->Dictionary:
 for part:Dictionary in spec.parts:part_nodes[part.id].transform=Transform2D(0,point(part.pivot))
 var body_y:=0.0
 var pod_y:=0.0
 var rotor_angle:=0.0
 var roll:=0.0
 var probe_y:=0.0
 var power:=1.0
 var phase:="hover"
 if action=="idle_down":
  body_y=[0,-1,0,1][index]
  rotor_angle=index*22.5
 elif action=="move_down":
  body_y=[0,-1,-1,0,1,1,0,0][index]
  rotor_angle=index*11.25
  phase="hover_cruise"
 elif action=="attack_down":
  body_y=[0,0,1,2,1,0][index]
  probe_y=[0,0,1,2,1,0][index]
  rotor_angle=[0,22.5,45,67.5,22.5,0][index]
  phase=["neutral","target_lock","probe_ready","short_forward_dip","recover","neutral_recovered"][index]
 elif action=="hit_down":
  roll=[0,-6,3,0][index]
  rotor_angle=[0,15,8,0][index]
  phase="impact_roll_recover"
 else:
  body_y=[0,3,8,14,20,24,24,24][index]
  pod_y=[0,0,0,1,2,3,3,3][index]
  rotor_angle=[0,25,42,52,58,60,60,60][index]
  power=[1,0.6,0.2,0,0,0,0,0][index]
  phase=["hover","power_loss","drop","drop_fold_struts","approach_ground","contact","grounded_wreck","wreck_hold"][index]
 var whole:=Transform2D(deg_to_rad(roll),Vector2(64,67+body_y))*Transform2D(0,Vector2(-64,-67))
 for id:String in ["body","probe"]:part_nodes[id].transform=whole*part_nodes[id].transform
 part_nodes.probe.position+=whole.y*probe_y
 # 保留安装口原有蓝灰源带作为伸缩颈，而非把整个探头拉出后留下透空。
 part_nodes.probe_rail.scale.y=1.0+probe_y
 part_nodes.probe_rail.transform=whole*part_nodes.probe_rail.transform
 for side:String in ["left","right"]:
  var id:=side+"_pod"
  part_nodes[id].position.y+=pod_y
  part_nodes[id].transform=whole*part_nodes[id].transform
  var plane:Node2D=fans[side]
  plane.transform=part_nodes[id].transform*Transform2D(0,Vector2(1.0,9.0/13.0),0,Vector2.ZERO)
  rotors[side].rotation=deg_to_rad(rotor_angle*(1.0 if side=="left" else -1.0))
  # 连接杆按固定两端映射，只有细连接杆长度变化；风扇壳和机身保持刚性。
  var source_start:=Vector2(54,67) if side=="left" else Vector2(74,67)
  var source_end:=Vector2(51,67) if side=="left" else Vector2(77,67)
  var target_start:=whole*source_start
  var target_end:=whole*(source_end+Vector2(0,pod_y))
  var rest_axis:Vector2=(source_end-source_start).normalized()
  var current_axis:Vector2=(target_end-target_start)/(source_end-source_start).length()
  var normal_axis:Vector2=Vector2(-current_axis.y,current_axis.x).normalized()
  var rest_normal:=Vector2(-rest_axis.y,rest_axis.x)
  var basis:=Transform2D(current_axis*rest_axis.x+normal_axis*rest_normal.x,current_axis*rest_axis.y+normal_axis*rest_normal.y,target_start)
  part_nodes[side+"_strut"].transform=basis
 entity_material.set_shader_parameter("sensor_power",power)
 var record:Dictionary={"action":action,"frame":index,"phase":phase,"root_px":[64,104],"body_y":body_y,"pod_local_y":pod_y,"rotor_angle_deg":rotor_angle,"rotor_count":2,"blades_per_rotor":4,"part_transforms":{},"feet":{},"contacts":{},"strut_endpoints":{}}
 for id:String in part_nodes:
  var node:Polygon2D=part_nodes[id]
  record.part_transforms[id]={"position":xy(node.position),"basis_x":xy(node.transform.x),"basis_y":xy(node.transform.y)}
 record.contacts.body_probe_bottom=xy(whole*Vector2(64,80)+whole.y*probe_y)
 record.contacts.left_pod_bottom=xy(whole*Vector2(42,77+pod_y))
 record.contacts.right_pod_bottom=xy(whole*Vector2(86,77+pod_y))
 record["probe_rail_endpoints"]={"start":xy(whole*Vector2(64,76)),"end":xy(whole*Vector2(64,77+probe_y))}
 for side:String in ["left","right"]:
  var start:=Vector2(54,67) if side=="left" else Vector2(74,67)
  var end:=Vector2(51,67) if side=="left" else Vector2(77,67)
  record.strut_endpoints[side]={"start":xy(whole*start),"end":xy(whole*(end+Vector2(0,pod_y))),"rest_local_end":xy(end-start)}
 return record
