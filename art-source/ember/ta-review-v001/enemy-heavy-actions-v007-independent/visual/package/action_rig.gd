extends Node2D
## 固定的双履带外形/支撑不变；履带相位只改变内部原纹理采样。
const CLIPS:Dictionary={
	"idle_down":{"fps":4,"loop":true,"poses":[
		{"body":[0,0],"tread":0,"phase":"neutral"},
		{"body":[0,-1],"tread":0,"phase":"suspension_rise"},
		{"body":[0,0],"tread":0,"phase":"neutral_return"},
		{"body":[0,1],"tread":0,"phase":"suspension_settle"}
	]},
	"move_down":{"fps":8,"loop":true,"poses":[
		{"body":[0,0],"tread":0,"phase":"tread_00"},
		{"body":[0,0],"tread":2,"phase":"tread_02"},
		{"body":[0,1],"tread":4,"phase":"tread_04_settle"},
		{"body":[0,0],"tread":6,"phase":"tread_06"},
		{"body":[0,0],"tread":8,"phase":"tread_08"},
		{"body":[0,0],"tread":10,"phase":"tread_10"},
		{"body":[0,1],"tread":12,"phase":"tread_12_settle"},
		{"body":[0,0],"tread":14,"phase":"tread_14"}
	]},
	"hit_down":{"fps":12,"loop":false,"poses":[
		{"body":[0,0],"tread":0,"phase":"neutral"},
		{"body":[-2,1],"tread":0,"phase":"mass_recoil"},
		{"body":[1,0],"tread":0,"phase":"counter_settle"},
		{"body":[0,0],"tread":0,"phase":"neutral_recovered"}
	]}
}
var spec:Dictionary
var part_nodes:Dictionary={}
var entity_material:ShaderMaterial
func _ready()->void:
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
	var texture:=load(str(spec.source)) as Texture2D
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
		node.texture=texture
		node.material=entity_material
		node.position=pivot
		node.z_index=part.z
		add_child(node)
		part_nodes[part.id]=node
func point(values:Array)->Vector2: return Vector2(values[0],values[1])
func xy(value:Vector2)->Array: return [value.x,value.y]
func pose_action(action:String,index:int)->Dictionary:
	var pose:Dictionary=CLIPS[action].poses[index]
	for part:Dictionary in spec.parts: part_nodes[part.id].transform=Transform2D(0,point(part.pivot))
	part_nodes.tower_projector.position+=point(pose.body)
	entity_material.set_shader_parameter("tread_phase_px",float(pose.tread))
	var record:Dictionary={"action":action,"frame":index,"phase":pose.phase,"root_px":[64,104],"body_translation_px":pose.body,"tread_phase_px":pose.tread,"supports":[[36,104],[92,104]],"part_transforms":{}}
	for id:String in part_nodes:
		var node:Polygon2D=part_nodes[id]
		record.part_transforms[id]={"position":xy(node.position),"basis_x":xy(node.transform.x),"basis_y":xy(node.transform.y)}
	return record
