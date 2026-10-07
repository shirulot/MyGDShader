extends SceneTree
## 逐关节只读复查。全身连通不代表每条肢体都连在正确关节上。
## 本工具只输出放大审查图、部件邻接测量与源 SHA；不修补原 PNG。

var workspace := ""
var output := ""
var records: Array = []
var palette := {"head": Color("c6a66c"), "torso": Color("698fb6"),
	"right_arm": Color("cf7395"), "left_arm": Color("89b862"),
	"left_upper_arm": Color("89b862"), "left_forearm_tool": Color("dcb06e"),
	"right_leg": Color("8b81be"), "left_leg": Color("55aaac"), "joint": Color("e0e2ca")}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--workspace="): workspace = arg.trim_prefix("--workspace=")
		elif arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	if workspace.is_empty() or output.is_empty():
		push_error("需要 --workspace 和 --output")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output)
	var catalog: Dictionary = _json("assets/ember/characters/robot/robot_frames_catalog_v003.json")
	for entry: Dictionary in catalog.frames:
		_audit(entry)
	var file := FileAccess.open(output.path_join("joint_contacts_v004.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"scope": "Readonly diagnostic; direct component contacts are evidence, not final art acceptance",
		"frames": records, "catalog_sha256": FileAccess.get_sha256(_abs("assets/ember/characters/robot/robot_frames_catalog_v003.json"))}, "\t") + "\n")
	print("JOINT_DIAGNOSTICS frames=", records.size())
	quit()


func _abs(path: String) -> String:
	return workspace.path_join(path.trim_prefix("res://"))


func _json(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(_abs(path)))


func _audit(entry: Dictionary) -> void:
	var raw := Image.load_from_file(_abs(entry.file))
	raw.convert(Image.FORMAT_RGBA8)
	var pose: Dictionary = {}
	var rig: Dictionary = {}
	if entry.has("pose_file"):
		pose = _json(entry.pose_file)
		rig = _json(pose.parts_file)
	else:
		var rig_path := "art-source/ember/robot-repair-v002/annotations/rig_%s_v002.json" % entry.direction
		rig = _json(rig_path)
		if entry.state == "walk":
			pose = _json("art-source/ember/robot-repair-v002/annotations/walk_%s_f%02d.json" % [entry.direction, int(entry.frame_index)])
	var parts: Dictionary = {}
	for part: Dictionary in rig.parts:
		var points := {}
		var offset: Array = pose.get("offsets", {}).get(part.name, [0, 0])
		for p: Array in part.pixels:
			points[Vector2i(int(p[0]) + int(offset[0]), int(p[1]) + int(offset[1]))] = true
		parts[part.name] = points
	var elbow_joint := {}
	for patch: Dictionary in pose.get("joint_pixels", []):
		elbow_joint[Vector2i(int(patch.at[0]), int(patch.at[1]))] = true
	var arm_top: String = "left_upper_arm" if parts.has("left_upper_arm") else "left_arm"
	var pairs := [["left_shoulder", "torso", arm_top], ["right_shoulder", "torso", "right_arm"],
		["left_hip", "torso", "left_leg"], ["right_hip", "torso", "right_leg"]]
	if parts.has("left_forearm_tool"):
		pairs.append(["left_elbow", "left_upper_arm", "left_forearm_tool"])
	var contacts := {}
	for pair: Array in pairs:
		contacts[pair[0]] = _contacts(parts[pair[1]], parts[pair[2]])
	if not elbow_joint.is_empty():
		var upper: Dictionary = parts["left_upper_arm"].duplicate()
		upper.merge(elbow_joint)
		contacts["left_elbow_with_authored_sleeve"] = _contacts(upper, parts["left_forearm_tool"])
	var record := {"id": entry.id, "file": entry.file, "sha256": FileAccess.get_sha256(_abs(entry.file)),
		"joint_contacts": contacts, "opaque_bbox": [raw.get_used_rect().position.x, raw.get_used_rect().position.y,
			raw.get_used_rect().size.x, raw.get_used_rect().size.y]}
	var parts_image := Image.create(64, 96, false, Image.FORMAT_RGBA8)
	parts_image.fill(Color(0, 0, 0, 0))
	var order: Array = pose.get("draw_order", [])
	if order.is_empty():
		for part: Dictionary in rig.parts: order.append(part.name)
	for name: String in order:
		for point: Vector2i in parts[name]:
			if point.x >= 0 and point.y >= 0 and point.x < 64 and point.y < 96:
				parts_image.set_pixelv(point, palette[name])
	for point: Vector2i in elbow_joint:
		parts_image.set_pixelv(point, palette.joint)
	var enlarged := _checker(raw, 12)
	enlarged.save_png(output.path_join(entry.id + "_actual_12x.png"))
	_checker(parts_image, 12).save_png(output.path_join(entry.id + "_parts_12x.png"))
	# 两条关节区域并排：肩肘和髋膝。原坐标仍可从裁片还原。
	var shoulder := _checker(raw.get_region(Rect2i(10, 38, 44, 28)), 16)
	var hips := _checker(raw.get_region(Rect2i(16, 56, 34, 24)), 16)
	var joint_view := Image.create(1248, 448, false, Image.FORMAT_RGBA8)
	joint_view.fill(Color("34434a"))
	joint_view.blit_rect(shoulder, Rect2i(Vector2i.ZERO, shoulder.get_size()), Vector2i.ZERO)
	joint_view.blit_rect(hips, Rect2i(Vector2i.ZERO, hips.get_size()), Vector2i(704, 0))
	joint_view.save_png(output.path_join(entry.id + "_joints_16x.png"))
	records.append(record)


func _contacts(a: Dictionary, b: Dictionary) -> Dictionary:
	var count_4 := 0
	var count_8 := 0
	var overlaps := 0
	var minimum := 999
	var nearest: Array = []
	for p: Vector2i in a:
		if b.has(p): overlaps += 1
		for q: Vector2i in b:
			var dx := absi(p.x - q.x)
			var dy := absi(p.y - q.y)
			var distance := maxi(dx, dy)
			if distance < minimum:
				minimum = distance
				nearest = [[p.x, p.y], [q.x, q.y]]
			if dx + dy == 1: count_4 += 1
			if distance == 1: count_8 += 1
	return {"overlap_pixels": overlaps, "contact_pairs_4": count_4, "contact_pairs_8": count_8,
		"minimum_chebyshev_distance": minimum, "nearest_pair": nearest}


func _checker(raw: Image, factor: int) -> Image:
	var preview := Image.create(raw.get_width() * factor, raw.get_height() * factor, false, Image.FORMAT_RGBA8)
	for y in preview.get_height():
		for x in preview.get_width():
			var pixel := raw.get_pixel(x / factor, y / factor)
			var background := Color("3a4850") if ((x / (factor * 2)) + (y / (factor * 2))) % 2 == 0 else Color("29363e")
			preview.set_pixel(x, y, background.blend(pixel))
	return preview
