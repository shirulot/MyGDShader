extends Node2D
## 每一块零件只分配一次源纹理，动作仅改变刚性位姿；两侧履带始终落地。
const CLIPS:Dictionary={
 "attack_down":{"fps":10,"loop":false,"poses":[
  {"body_y":0,"gun_y":0,"gun_angle":0,"power":1,"phase":"neutral"},
  {"body_y":0,"gun_y":-1,"gun_angle":0,"power":1,"phase":"chamber_charge"},
  {"body_y":0,"gun_y":0,"gun_angle":0,"power":1,"phase":"ready"},
  {"body_y":1,"gun_y":-2,"gun_angle":0,"power":1,"phase":"release_recoil"},
  {"body_y":1,"gun_y":-1,"gun_angle":0,"power":1,"phase":"damped_recovery"},
  {"body_y":0,"gun_y":0,"gun_angle":0,"power":1,"phase":"neutral_recovered"}
 ]},
 "death_down":{"fps":10,"loop":false,"poses":[
  {"body_y":0,"gun_y":0,"gun_angle":0,"power":1,"phase":"neutral"},
  {"body_y":2,"gun_y":0,"gun_angle":0,"power":0.7,"phase":"power_loss"},
  {"body_y":5,"gun_y":0,"gun_angle":3,"power":0.3,"phase":"tower_drops"},
  {"body_y":9,"gun_y":0,"gun_angle":7,"power":0,"phase":"chassis_collapse"},
  {"body_y":13,"gun_y":1,"gun_angle":12,"power":0,"phase":"lower_stop"},
  {"body_y":12,"gun_y":1,"gun_angle":12,"power":0,"phase":"damped_settle"},
  {"body_y":13,"gun_y":1,"gun_angle":12,"power":0,"phase":"grounded_wreck"},
  {"body_y":13,"gun_y":1,"gun_angle":12,"power":0,"phase":"wreck_hold"}
 ]}
}
var spec:Dictionary
var part_nodes:Dictionary={}
var entity_material:ShaderMaterial
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func xy(p:Vector2)->Array:return [p.x,p.y]
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 var texture:=load(str(spec.source)) as Texture2D
 entity_material=ShaderMaterial.new()
 entity_material.shader=load("res://entity_cutout.gdshader")
 # 一次校准的隐藏安装座；中性帧完全被原稿覆盖，不能改变中性RGB。
 var hidden:=Polygon2D.new()
 hidden.polygon=PackedVector2Array([Vector2(48,78),Vector2(80,78),Vector2(80,98),Vector2(48,98)])
 hidden.uv=PackedVector2Array([Vector2(253,238),Vector2(1283,238),Vector2(1283,790),Vector2(253,790)])
 hidden.texture=load("res://source/hidden_chassis_master.png")
 var hidden_material:=ShaderMaterial.new()
 hidden_material.shader=load("res://hidden_chassis.gdshader")
 hidden_material.set_shader_parameter("canonical_mask",texture)
 hidden.material=hidden_material
 hidden.z_index=0
 add_child(hidden)
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
  node.texture=texture
  node.material=entity_material
  node.position=pivot
  node.z_index=part.z
  add_child(node)
  part_nodes[part.id]=node
func pose_action(action:String,index:int)->Dictionary:
 var pose:Dictionary=CLIPS[action].poses[index]
 for part:Dictionary in spec.parts:part_nodes[part.id].transform=Transform2D(0,point(part.pivot))
 part_nodes.tower_shell.position.y+=pose.body_y
 part_nodes.projector.position.y+=pose.gun_y
 part_nodes.projector.rotation=deg_to_rad(pose.gun_angle)
 entity_material.set_shader_parameter("sensor_power",float(pose.power))
 var record:Dictionary={"action":action,"frame":index,"phase":pose.phase,"root_px":[64,104],"body_translation_px":[0,pose.body_y],"gun_translation_px":[0,pose.gun_y],"gun_angle_deg":pose.gun_angle,"supports":[[36,104],[92,104]],"part_transforms":{}}
 for id:String in part_nodes:
  var node:Polygon2D=part_nodes[id]
  record.part_transforms[id]={"position":xy(node.position),"basis_x":xy(node.transform.x),"basis_y":xy(node.transform.y)}
 return record
