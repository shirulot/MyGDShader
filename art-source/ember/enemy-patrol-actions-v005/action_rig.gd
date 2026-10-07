extends "res://fixed_rig.gd"
## 已通过的母稿与固定区域不变；本批只增加待机和受击关节姿态。
## 这里是人工登记的屏幕空间轻幅动作，不冒称完整三维动力学模拟。
const CLIPS := {
	"idle_down": {"fps":4,"loop":true,"poses":[
		{"shift":[0,0],"angle":0,"claw":0,"phase":"neutral"},
		{"shift":[0,-1],"angle":0,"claw":0,"phase":"breath_rise"},
		{"shift":[0,0],"angle":0,"claw":3,"phase":"coupling_release"},
		{"shift":[0,1],"angle":0,"claw":0,"phase":"breath_settle"}
	]},
	"hit_down": {"fps":12,"loop":false,"poses":[
		{"shift":[0,0],"angle":0,"claw":0,"phase":"neutral"},
		{"shift":[-2,1],"angle":-5,"claw":4,"phase":"impact_recoil"},
		{"shift":[1,0],"angle":3,"claw":-2,"phase":"counter_settle"},
		{"shift":[0,0],"angle":0,"claw":0,"phase":"neutral_recovered"}
	]}
}

func pose_action(action: String,index: int) -> Dictionary:
	bind_pose()
	var definition: Dictionary = CLIPS[action].poses[index]
	var shift := point(definition.shift)
	var waist := Vector2(64,80)
	var body_transform := Transform2D(deg_to_rad(float(definition.angle)),waist+shift)
	for id: String in ["head_chest_pelvis","right_arm_gun","left_arm_claw"]:
		var part: Polygon2D = part_nodes[id]
		var local_pivot := part.position-waist
		part.transform=body_transform*Transform2D(0.0,local_pivot)
		if id=="left_arm_claw": part.rotate(deg_to_rad(float(definition.claw)))
	var record := {"action":action,"frame":index,"phase":definition.phase,"root_px":[64,104],"body_shift":definition.shift,"body_angle_degrees":definition.angle,"pose_space":"authored_screen_joints","legs":{},"part_transforms":{}}
	for side: String in ["right","left"]:
		var sign_x := -1.0 if side=="right" else 1.0
		var hip := body_transform*Vector2(sign_x*6,0)
		var knee := Vector2(64+sign_x*7,90)+Vector2(roundf(shift.x*0.5),roundf(shift.y*0.5))
		var ankle := Vector2(64+sign_x*8,98)
		apply_segment(side+"_thigh",hip,knee)
		apply_segment(side+"_shin",knee,ankle)
		part_nodes[side+"_knee_cap"].position=knee
		part_nodes[side+"_foot"].position=ankle
		record.legs[side]={"hip_px":xy(hip),"knee_px":xy(knee),"ankle_px":xy(ankle),"sole_marker_px":xy(ankle+Vector2(0,6)),"support":true}
	for id: String in part_nodes:
		var part: Polygon2D=part_nodes[id]
		record.part_transforms[id]={"position":xy(part.position),"basis_x":xy(part.transform.x),"basis_y":xy(part.transform.y)}
	return record
