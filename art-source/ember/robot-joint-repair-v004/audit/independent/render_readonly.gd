extends SceneTree
## 只读审阅工具：把现有 PNG 放在棋盘格上做 nearest 放大，不修改任何源资产。
const OUT := "res://art-source/ember/robot-joint-repair-v004/audit/independent/"
func _initialize() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ember/characters/robot/robot_frames_catalog_v003.json"))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var metrics := []
	for frame: Dictionary in catalog["frames"]:
		var source := Image.load_from_file(ProjectSettings.globalize_path(frame["file"]))
		source.convert(Image.FORMAT_RGBA8)
		var canvas := Image.create(64, 96, false, Image.FORMAT_RGBA8)
		for y in 96:
			for x in 64:
				canvas.set_pixel(x, y, Color("#a9aab4") if (floori(float(x) / 4.0) + floori(float(y) / 4.0)) % 2 == 0 else Color("#d4d5de"))
		canvas.blend_rect(source, Rect2i(0, 0, 64, 96), Vector2i.ZERO)
		canvas.resize(512, 768, Image.INTERPOLATE_NEAREST)
		canvas.save_png(ProjectSettings.globalize_path(OUT + frame["id"] + ".png"))
		var rows := []
		for y in 96:
			var line := ""
			for x in 64:
				var color := source.get_pixel(x, y)
				line += "." if color.a == 0 else "#" if color.r < 0.25 else "m" if color.r < 0.6 else "W"
			rows.append(line)
		metrics.append({"id": frame["id"], "file": frame["file"], "sha256": FileAccess.get_sha256(ProjectSettings.globalize_path(frame["file"])), "components_4": components(source, false), "components_8": components(source, true), "ascii_alpha_dark_mid_light": rows, "authored_parts_contact": part_contacts(frame)})
	var file := FileAccess.open(OUT + "literal_alpha_components.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(metrics, "\t"))
	print("Created 40 readonly checkerboard 8x previews")
	quit()

func part_contacts(frame: Dictionary) -> Dictionary:
	var direction: String = frame["direction"]
	var pose: Dictionary = {}
	var rig_file: String
	if frame.has("pose_file"):
		pose = JSON.parse_string(FileAccess.get_file_as_string(frame["pose_file"]))
		rig_file = pose["parts_file"]
	elif frame["state"] == "walk":
		pose = JSON.parse_string(FileAccess.get_file_as_string("res://art-source/ember/robot-repair-v002/annotations/walk_%s_f%02d.json" % [direction, frame["frame_index"]]))
		rig_file = "res://art-source/ember/robot-repair-v002/annotations/rig_%s_v002.json" % direction
	else:
		rig_file = "res://art-source/ember/robot-repair-v002/annotations/rig_%s_v002.json" % direction
	var rig: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(rig_file))
	var sets := {}
	for part: Dictionary in rig["parts"]:
		var name: String = part["name"]
		var offset: Array = pose.get("offsets", {}).get(name, [0, 0])
		var points := {}
		for point: Array in part["pixels"]:
			points[Vector2i(int(point[0] + offset[0]), int(point[1] + offset[1]))] = true
		sets[name] = points
	var result := {}
	for pair in [["torso", "right_arm"], ["torso", "left_arm"], ["torso", "left_upper_arm"], ["left_upper_arm", "left_forearm_tool"], ["torso", "right_leg"], ["torso", "left_leg"]]:
		if not sets.has(pair[0]) or not sets.has(pair[1]):
			continue
		var cardinal := []
		var diagonal := []
		var overlap := []
		for point: Vector2i in sets[pair[0]]:
			if sets[pair[1]].has(point):
				overlap.append([point.x, point.y])
			for delta in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				if sets[pair[1]].has(point + delta):
					cardinal.append([point.x, point.y, point.x + delta.x, point.y + delta.y])
			for delta in [Vector2i(1, 1), Vector2i(-1, 1), Vector2i(1, -1), Vector2i(-1, -1)]:
				if sets[pair[1]].has(point + delta):
					diagonal.append([point.x, point.y, point.x + delta.x, point.y + delta.y])
		result["%s__%s" % pair] = {"cardinal_count": cardinal.size(), "diagonal_count": diagonal.size(), "overlap_count": overlap.size(), "cardinal_points": cardinal, "overlap_points": overlap, "note": "Source coordinate evidence, before occlusion and joint-pixel patches. Does not certify natural joint connection."}
	return result

func components(source: Image, diagonal: bool) -> Array:
	var seen := {}
	var result := []
	var deltas := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]
	if diagonal:
		deltas.append_array([Vector2i(1, 1), Vector2i(-1, 1), Vector2i(1, -1), Vector2i(-1, -1)])
	for y in 96:
		for x in 64:
			var start := Vector2i(x, y)
			if seen.has(start) or source.get_pixelv(start).a == 0:
				continue
			var queue := [start]
			seen[start] = true
			var index := 0
			var bounds := Rect2i(start, Vector2i.ONE)
			while index < queue.size():
				var point: Vector2i = queue[index]
				index += 1
				bounds = bounds.expand(point)
				for delta: Vector2i in deltas:
					var other := point + delta
					if not Rect2i(0, 0, 64, 96).has_point(other) or seen.has(other) or source.get_pixelv(other).a == 0:
						continue
					seen[other] = true
					queue.append(other)
			result.append({"size": queue.size(), "bbox": [bounds.position.x, bounds.position.y, bounds.size.x, bounds.size.y], "points": queue.map(func(point): return [point.x, point.y]) if queue.size() < 400 else []})
	return result
