extends "res://fixed_rig.gd"
## 同源部件制作攻击和侧倒；右上臂与前臂枪只增加一次固定UV分区。
## 部件姿态均登记，不按每帧包围盒对齐。
const CLIPS := {
	"idle_down":{"fps":4,"loop":true,"poses":[
		{"shift":[0,0],"angle":0,"claw":0,"phase":"neutral"},
		{"shift":[0,-1],"angle":0,"claw":0,"phase":"breath_rise"},
		{"shift":[0,0],"angle":0,"claw":3,"phase":"coupling_release"},
		{"shift":[0,1],"angle":0,"claw":0,"phase":"breath_settle"}
	]},
	"move_down":{"fps":8,"loop":true,"poses":[{},{},{},{},{},{},{},{}]},
	"hit_down":{"fps":12,"loop":false,"poses":[
		{"shift":[0,0],"angle":0,"claw":0,"phase":"neutral"},
		{"shift":[-2,1],"angle":-5,"claw":4,"phase":"impact_recoil"},
		{"shift":[1,0],"angle":3,"claw":-2,"phase":"counter_settle"},
		{"shift":[0,0],"angle":0,"claw":0,"phase":"neutral_recovered"}
	]},
	"attack_down":{"fps":10,"loop":false,"poses":[
		{"body_y":0,"elbow":[0,0],"claw":0,"phase":"neutral"},
		{"body_y":0,"elbow":[-1,-1],"claw":-3,"phase":"raise_projector"},
		{"body_y":1,"elbow":[-1,-3],"claw":-5,"phase":"brace_windup"},
		{"body_y":0,"elbow":[-1,-4],"claw":-5,"phase":"release_recoil"},
		{"body_y":1,"elbow":[-1,-2],"claw":-3,"phase":"recover"},
		{"body_y":0,"elbow":[0,0],"claw":0,"phase":"neutral_recovered"}
	]},
	"death_down":{"fps":10,"loop":false,"poses":[
		{"body_y":0,"fold":0,"roll":0,"origin":[64,80],"phase":"neutral","support":true},
		{"body_y":2,"fold":5,"roll":0,"origin":[64,82],"phase":"power_loss","support":true},
		{"body_y":5,"fold":12,"roll":0,"origin":[64,85],"phase":"knees_buckle","support":true},
		{"body_y":8,"fold":22,"roll":22,"origin":[66,86],"phase":"lose_balance","support":false},
		{"body_y":8,"fold":30,"roll":50,"origin":[68,85],"phase":"side_fall","support":false},
		{"body_y":8,"fold":35,"roll":78,"origin":[70,89],"phase":"approach_ground","support":false},
		{"body_y":8,"fold":35,"roll":88,"origin":[70,90],"phase":"shoulder_contact_settle","support":false},
		{"body_y":8,"fold":35,"roll":88,"origin":[70,90],"phase":"wreck_hold","support":false}
	]}
}

func pose_action(action:String,index:int)->Dictionary:
	part_nodes.head_chest_pelvis.material.set_shader_parameter("sensor_power",1.0)
	if action in ["idle_down","hit_down"]: return pose_idle_hit(action,index)
	if action=="move_down":
		var move_record:=pose(index)
		var bob:=Vector2(0,float(spec.phases[index].body_y))
		part_nodes.right_upper_arm.position+=bob
		move_record.action=action
		move_record.arms={"right":{"shoulder_px":xy(Vector2(51,69)+bob),"elbow_px":xy(Vector2(48,77)+bob)}}
		for id:String in part_nodes:
			var part:Polygon2D=part_nodes[id]
			move_record.part_transforms[id]={"position":xy(part.position),"basis_x":xy(part.transform.x),"basis_y":xy(part.transform.y)}
		return move_record
	return pose_combat(action,index)

func pose_idle_hit(action:String,index:int)->Dictionary:
	bind_pose()
	var definition:Dictionary=CLIPS[action].poses[index]
	var shift:=point(definition.shift)
	var waist:=Vector2(64,80)
	var body_transform:=Transform2D(deg_to_rad(float(definition.angle)),waist+shift)
	# 新拆出的上臂/前臂共同接受旧整臂的同一刚性变换，旧三动作不改姿态。
	for id:String in ["head_chest_pelvis","right_arm_gun","left_arm_claw","right_upper_arm"]:
		var part:Polygon2D=part_nodes[id]
		part.transform=body_transform*Transform2D(0.0,part.position-waist)
		if id=="left_arm_claw": part.rotate(deg_to_rad(float(definition.claw)))
	var record:Dictionary={"action":action,"frame":index,"phase":definition.phase,"root_px":[64,104],"body_shift":definition.shift,"body_angle_degrees":definition.angle,"legs":{},"arms":{"right":{"shoulder_px":xy(body_transform*Vector2(-13,-11)),"elbow_px":xy(body_transform*Vector2(-16,-3))}},"part_transforms":{}}
	for side:String in ["right","left"]:
		var sign_x:float=-1.0 if side=="right" else 1.0
		var hip:=body_transform*Vector2(sign_x*6,0)
		var knee:=Vector2(64+sign_x*7,90)+Vector2(roundf(shift.x*0.5),roundf(shift.y*0.5))
		var ankle:=Vector2(64+sign_x*8,98)
		apply_segment(side+"_thigh",hip,knee)
		apply_segment(side+"_shin",knee,ankle)
		part_nodes[side+"_knee_cap"].position=knee
		part_nodes[side+"_foot"].position=ankle
		record.legs[side]={"hip_px":xy(hip),"knee_px":xy(knee),"ankle_px":xy(ankle),"sole_marker_px":xy(ankle+Vector2(0,6)),"support":true}
	for id:String in part_nodes:
		var part:Polygon2D=part_nodes[id]
		record.part_transforms[id]={"position":xy(part.position),"basis_x":xy(part.transform.x),"basis_y":xy(part.transform.y)}
	return record

func pose_combat(action:String,index:int)->Dictionary:
	bind_pose()
	var definition:Dictionary=CLIPS[action].poses[index]
	var body_y:=float(definition.body_y)
	var sensor_power:=maxf(0.0,1.0-float(index)*0.4) if action=="death_down" else 1.0
	part_nodes.head_chest_pelvis.material.set_shader_parameter("sensor_power",sensor_power)
	for id:String in ["head_chest_pelvis","left_arm_claw","right_arm_gun","right_upper_arm"]:
		part_nodes[id].position+=Vector2(0,body_y)
	var joints:Dictionary={}
	for side:String in ["right","left"]:
		var sign_x:float=-1.0 if side=="right" else 1.0
		var hip:=Vector2(64+sign_x*6,80+body_y)
		var knee:=Vector2(64+sign_x*7,90+roundf(body_y*0.6))
		var ankle:=Vector2(64+sign_x*8,98)
		apply_segment(side+"_thigh",hip,knee)
		apply_segment(side+"_shin",knee,ankle)
		part_nodes[side+"_knee_cap"].position=knee
		part_nodes[side+"_foot"].position=ankle
		joints[side]={"hip":hip,"knee":knee,"ankle":ankle}
	var shoulder:=Vector2(51,69+body_y)
	var elbow:=Vector2(48,77+body_y)
	var fall:=Transform2D.IDENTITY
	if action=="attack_down":
		elbow+=point(definition.elbow)
		apply_segment("right_upper_arm",shoulder,elbow)
		part_nodes.right_arm_gun.position=elbow
		part_nodes.left_arm_claw.rotation=deg_to_rad(float(definition.claw))
	else:
		# 两臂沿原肩安装点向身侧折回，再随躯干侧倒，不能复制地面残骸。
		var arm_turn:=Transform2D(deg_to_rad(-float(definition.fold)),shoulder)
		elbow=arm_turn*Vector2(-3,8)
		apply_segment("right_upper_arm",shoulder,elbow)
		part_nodes.right_arm_gun.transform=Transform2D(arm_turn.get_rotation(),elbow)
		part_nodes.left_arm_claw.rotation=deg_to_rad(float(definition.fold))
		fall=Transform2D(deg_to_rad(float(definition.roll)),point(definition.origin))*Transform2D(0,Vector2(-64,-80-body_y))
		for id:String in part_nodes: part_nodes[id].transform=fall*part_nodes[id].transform
	var record:Dictionary={"action":action,"frame":index,"phase":definition.phase,"root_px":[64,104],"pose_definition":definition,"legs":{},"arms":{"right":{"shoulder_px":xy(fall*shoulder),"elbow_px":xy(fall*elbow)}},"part_transforms":{}}
	record.sensor_power=sensor_power
	record.events=[]
	if action=="attack_down" and index==3:
		record.events.append({"name":"attack_release_visual","source_muzzle_px":[47,89],"muzzle_px":xy(part_nodes.right_arm_gun.transform*Vector2(-1,12))})
	if action=="death_down" and index==7: record.events.append({"name":"corpse_hold_visual"})
	for side:String in joints:
		var leg:Dictionary=joints[side]
		record.legs[side]={"hip_px":xy(fall*leg.hip),"knee_px":xy(fall*leg.knee),"ankle_px":xy(fall*leg.ankle),"sole_marker_px":xy(fall*(leg.ankle+Vector2(0,6))),"support":true if action=="attack_down" else definition.support}
	if action=="death_down":
		# 固定源肩缘采样点用于观察接触，不用bbox重新定位整帧。
		var claw:Polygon2D=part_nodes.left_arm_claw
		record.shoulder_contact_landmark_px=xy(claw.transform*Vector2(0,-2))
		record.ground_y=104
	for id:String in part_nodes:
		var part:Polygon2D=part_nodes[id]
		record.part_transforms[id]={"position":xy(part.position),"basis_x":xy(part.transform.x),"basis_y":xy(part.transform.y)}
	return record
