extends Node2D
## 母稿 PNG 不变；区域和关节来源全部在 rig.json，供编辑与审查。
## 腿的二维缩短来自同一组三维矢状面关节投影，而非每帧独立拟合 bbox。
var spec: Dictionary
var part_nodes: Dictionary = {}
var pose_record: Dictionary = {}

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spec = JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
	var texture := load(str(spec.source)) as Texture2D
	var entity_material := ShaderMaterial.new()
	entity_material.shader = load("res://entity_cutout.gdshader")
	for part: Dictionary in spec.parts:
		var node := Polygon2D.new()
		node.name = str(part.id)
		var pivot := point(part.pivot)
		var vertices := PackedVector2Array()
		var uv := PackedVector2Array()
		for vertex: Array in part.polygon:
			vertices.append(point(vertex) - pivot)
			uv.append(point(vertex))
		node.polygon = vertices
		node.uv = uv
		node.texture = texture
		node.material = entity_material
		node.position = pivot
		node.z_index = int(part.z)
		add_child(node)
		part_nodes[str(part.id)] = node

func point(values: Array) -> Vector2:
	return Vector2(float(values[0]), float(values[1]))

func bind_pose() -> void:
	for part: Dictionary in spec.parts:
		var node: Polygon2D = part_nodes[str(part.id)]
		node.transform = Transform2D(0.0,point(part.pivot))

func pose(index: int) -> Dictionary:
	bind_pose()
	var phase: Dictionary = spec.phases[posmod(index, 8)]
	var bob := Vector2(0, float(phase.body_y))
	for id: String in ["head_chest_pelvis", "right_arm_gun", "left_arm_claw"]:
		part_nodes[id].position += bob
	pose_record = {"frame":index,"phase":phase.phase,"root_px":[64,104],"body_translation_px":[0,phase.body_y],"legs":{},"part_transforms":{}}
	for side: String in ["right", "left"]:
		var foot: Dictionary = phase[side]
		var joints := solve_leg(side, foot, float(phase.body_y))
		apply_segment(side + "_thigh", joints.hip, joints.knee)
		apply_segment(side + "_shin", joints.knee, joints.ankle)
		# 膝甲是关节硬壳罩，保持原生体积；只让后方暗色胫轴表现投影缩短。
		# 它独立遮挡胫轴与靴口，避免把整块膝甲沿胫骨压成扁带。
		part_nodes[side + "_knee_cap"].position = joints.knee
		part_nodes[side + "_foot"].position = joints.ankle
		pose_record.legs[side] = {"hip_px":xy(joints.hip),"knee_px":xy(joints.knee),"ankle_px":xy(joints.ankle),"sole_marker_px":xy(joints.ankle + Vector2(0,6)),"projected_ground_px":xy(joints.ground),"lift_world":foot.lift,"depth_world":foot.depth,"support":foot.support,"world_joints":joints.world_joints}
	for id: String in part_nodes:
		var part: Polygon2D = part_nodes[id]
		pose_record.part_transforms[id] = {"position":xy(part.position),"rotation_radians":part.rotation,"scale":xy(part.scale),"basis_x":xy(part.transform.x),"basis_y":xy(part.transform.y)}
	return pose_record

func xy(value: Vector2) -> Array:
	return [value.x,value.y]

func solve_leg(side: String, foot: Dictionary, bob: float) -> Dictionary:
	var projection: Dictionary = spec.projection
	var hip_h := float(projection.hip_height) - bob / 0.75
	var ankle_h := float(projection.ankle_height) + float(foot.lift)
	var hip_world := Vector2(hip_h,0)
	var ankle_world := Vector2(ankle_h,float(foot.depth))
	var direction := ankle_world - hip_world
	var distance := direction.length()
	var thigh := float(projection.thigh_length)
	var shin := float(projection.shin_length)
	var along := (thigh * thigh - shin * shin + distance * distance) / (2.0 * distance)
	var outward := sqrt(maxf(0.0, thigh * thigh - along * along))
	var unit := direction / distance
	# 膝始终向角色前方弯曲，禁止相邻帧切换 IK 分支。
	var knee_world := hip_world + unit * along + Vector2(unit.y,-unit.x) * outward
	var hip_x := 58.0 if side == "right" else 70.0
	var knee_x := 57.0 if side == "right" else 71.0
	var ankle_x := 56.0 if side == "right" else 72.0
	return {"hip":project(hip_world,hip_x),"knee":project(knee_world,knee_x),"ankle":project(ankle_world,ankle_x),"ground":project(Vector2(0,float(foot.depth)),ankle_x),"world_joints":[xy(hip_world),xy(knee_world),xy(ankle_world)]}

func project(world: Vector2, x: float) -> Vector2:
	return Vector2(x,roundf(104.0 - 0.75 * world.x + 0.35 * world.y))

func apply_segment(id: String, start: Vector2, end: Vector2) -> void:
	for part: Dictionary in spec.parts:
		if str(part.id) != id:
			continue
		var rest := point(part.end) - point(part.pivot)
		var current := end - start
		var node: Polygon2D = part_nodes[id]
		# 在原骨段自身坐标系缩短，再投影到当前骨段；避免直接缩local Y
		# 在原骨段倾斜时引入约半像素端点偏移。该矩阵把真实末端精确映射到end。
		var rest_axis := rest.normalized()
		var rest_normal := Vector2(-rest_axis.y,rest_axis.x)
		var target_axis := current / rest.length()
		var target_normal := Vector2(-current.y,current.x).normalized()
		node.transform = Transform2D(target_axis*rest_axis.x+target_normal*rest_normal.x,target_axis*rest_axis.y+target_normal*rest_normal.y,start)
		assert((node.transform*rest).distance_to(end)<0.0001,"Registered bone endpoint mismatch")
		return
