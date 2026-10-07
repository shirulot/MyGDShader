extends SceneTree
## 原生部件动画：复用经过审阅的 idle 像素与修复后 rig，每个部件仅作整数位移。
## 空画布按明确层次合成，不擦除源点、不膨胀 Alpha、不自动填缝、不缩放或镜像。
## 姿态文件可以逐部件审阅和修改；任何断开/越界/脚底变化都会阻止生产验收。

const SIZE := Vector2i(64, 96)
const ANCHOR := Vector2i(32, 80)
const DIRECTIONS := ["down", "left", "right", "up"]
const PART_NAMES := ["head", "torso", "right_arm", "left_arm", "right_leg", "left_leg"]
const SOURCE_DIR := "art-source/ember/robot-actions-v003"
const OUTPUT_DIR := "assets/ember/characters/robot/actions_v003"
var workspace := ""
var errors: Array[String] = []
var frames: Array[Dictionary] = []
var dependency_hashes: Dictionary = {}
var rendered: Array[Image] = []
var pose_names: Array[String] = []
var refresh_authored_poses := false

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--workspace="):
			workspace = argument.trim_prefix("--workspace=").replace("\\", "/")
		elif argument == "--refresh-authored-poses":
			# 仅显式调用时更新本工具的新姿态；通常重跑保留人工编辑的 pose JSON。
			refresh_authored_poses = true
	if workspace.is_empty():
		workspace = ProjectSettings.globalize_path("res://").trim_suffix("/")
	DirAccess.make_dir_recursive_absolute(_path(SOURCE_DIR + "/poses"))
	DirAccess.make_dir_recursive_absolute(_path(SOURCE_DIR + "/source-rigs"))
	DirAccess.make_dir_recursive_absolute(_path(OUTPUT_DIR))
	var old_catalog: Variant = JSON.parse_string(FileAccess.get_file_as_string(_path("assets/ember/characters/robot/robot_frames_catalog_v002.json")))
	if not old_catalog is Dictionary:
		push_error("缺少已审阅角色目录。")
		quit(1)
		return
	for direction: String in DIRECTIONS:
		_build_direction(direction, old_catalog)
	for path: String in dependency_hashes:
		if FileAccess.get_sha256(_path(path)) != dependency_hashes[path]:
			errors.append("源资源 SHA 在合成期间发生变化：" + path)
	var manifest := {"schema_version": 1, "status": "PASS" if errors.is_empty() and frames.size() == 24 else "FAIL",
		"date": "2026-10-06", "engine": Engine.get_version_info(), "canvas": [64, 96], "anchor": [32, 80],
		"subject_limit": [40, 64], "directions": DIRECTIONS, "new_png_count": rendered.size(), "frame_count": frames.size(),
		"construction": "AUTHORED_INTEGER_COMPONENT_POSES_FROM_ACCEPTED_NATIVE_IDLE_AND_REPAIRED_V002_RIG",
		"whole_image_transform": "NONE", "alpha_repair_or_dilation": "NONE", "dependency_sha256": dependency_hashes,
		"frames": frames, "errors": errors, "builder_sha256": FileAccess.get_sha256(_path("tools/build_robot_actions_v003.gd"))}
	_write_json(SOURCE_DIR + "/frame_manifest_v003.json", manifest)
	if DisplayServer.get_name() != "headless" and rendered.size() == 20:
		await _capture_contact_sheet()
	print("ROBOT_ACTIONS ", manifest["status"], " new_png=", rendered.size(), " frames=", frames.size(), " errors=", errors.size())
	for message in errors:
		push_error(message)
	quit(0 if manifest["status"] == "PASS" else 1)

func _path(path: String) -> String:
	return workspace.path_join(path.trim_prefix("res://"))

func _source_image(path: String) -> Image:
	dependency_hashes[path] = FileAccess.get_sha256(_path(path))
	var image := Image.load_from_file(_path(path))
	if image != null:
		image.convert(Image.FORMAT_RGBA8)
	return image

func _build_direction(direction: String, old_catalog: Dictionary) -> void:
	var idle_path := "assets/ember/characters/robot/robot_idle_%s_v001.png" % direction
	var image := _source_image(idle_path)
	if image == null or image.get_size() != SIZE:
		errors.append("idle 原图缺失或尺寸不符：" + direction)
		return
	var rig_original := "art-source/ember/robot-repair-v002/annotations/rig_%s_v002.json" % direction
	var rig_copy := SOURCE_DIR + "/source-rigs/rig_%s_v002.json" % direction
	dependency_hashes[rig_original] = FileAccess.get_sha256(_path(rig_original))
	if not FileAccess.file_exists(_path(rig_copy)):
		DirAccess.copy_absolute(_path(rig_original), _path(rig_copy))
	if FileAccess.get_sha256(_path(rig_copy)) != dependency_hashes[rig_original]:
		errors.append("复制的 rig 与已审阅 v002 来源不符：" + direction)
		return
	var value: Variant = JSON.parse_string(FileAccess.get_file_as_string(_path(rig_copy)))
	if not value is Dictionary:
		errors.append("rig 文件不是 JSON 对象：" + direction)
		return
	var rig: Dictionary = value
	if str(rig["idle_sha256"]) != dependency_hashes[idle_path]:
		errors.append("rig 的 idle SHA 不符：" + direction)
		return
	var parts := _validate_parts(image, rig)
	if parts.size() != 6:
		return
	parts = _split_left_arm(parts, direction)
	var action_rig_file := SOURCE_DIR + "/source-rigs/rig_%s_actions_v003.json" % direction
	var action_rig_parts := []
	for name: String in parts:
		action_rig_parts.append({"name": name, "pixels": parts[name]})
	_write_json(action_rig_file, {"schema_version": 1, "idle_source": "res://" + idle_path,
		"idle_sha256": dependency_hashes[idle_path], "source_rig": "res://" + rig_copy,
		"source_rig_sha256": FileAccess.get_sha256(_path(rig_copy)), "parts": action_rig_parts,
		"tool_arm_split": {"upper_inclusive_last_y": _arm_cut_y(direction),
			"reason": "肩甲与上臂保持躯干落点；前臂及原左腕工具整体进行采集伸展。原实体像素只重新归属，不改变 RGBA。"}})
	var idle_window: Array = []
	for old_frame: Dictionary in old_catalog["frames"]:
		if str(old_frame["id"]) == "robot_idle_" + direction:
			idle_window = old_frame.get("runtime_windows", []).duplicate(true)
	var original := _record_frame(image, image, idle_path, direction, "idle", 0, {}, idle_window)
	original["reused_original"] = true
	original["source_idle"] = "res://" + idle_path
	original["source_idle_sha256"] = dependency_hashes[idle_path]
	frames.append(original)
	for state: String in ["idle", "collect"]:
		var indices := [1] if state == "idle" else [0, 1, 2, 3]
		for index: int in indices:
			var pose_file := SOURCE_DIR + "/poses/robot_%s_%s_f%02d_v003.json" % [state, direction, index]
			if refresh_authored_poses or not FileAccess.file_exists(_path(pose_file)):
				_write_json(pose_file, _default_pose(direction, state, index, idle_path, action_rig_file))
			var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(_path(pose_file)))
			if not parsed is Dictionary:
				errors.append("姿态文件不是 JSON 对象：" + pose_file)
				continue
			var pose: Dictionary = parsed
			var output := _render_pose(image, parts, pose)
			if output == null:
				continue
			var output_path := OUTPUT_DIR + "/robot_%s_%s_f%02d_v003.png" % [state, direction, index]
			var windows := _translate_windows(idle_window, pose, output, image)
			var record := _record_frame(output, image, output_path, direction, state, index, pose, windows)
			record["pose_file"] = "res://" + pose_file
			record["pose_sha256"] = FileAccess.get_sha256(_path(pose_file))
			record["source_idle"] = "res://" + idle_path
			record["source_idle_sha256"] = dependency_hashes[idle_path]
			record["source_rig"] = "res://" + action_rig_file
			record["source_rig_sha256"] = FileAccess.get_sha256(_path(action_rig_file))
			record["reused_original"] = false
			record["head_exact_translated_rgba"] = _part_matches(output, image, parts["head"], pose["offsets"]["head"])
			record["support_feet_rows_74_79_unchanged"] = _region_matches(output, image, Rect2i(0, 74, 64, 6))
			record["shoulder_offset_matches_torso"] = pose["offsets"]["left_upper_arm"] == pose["offsets"]["torso"]
			record["tool_integrity"] = _tool_measurement(output, image, parts, pose)
			var measurement: Dictionary = record["measurement"]
			if measurement["components_8"] != 1 or not measurement["binary_alpha"] or not measurement["subject_size_pass"] or not measurement["transparent_border"] or not record["head_exact_translated_rgba"] or not record["support_feet_rows_74_79_unchanged"] or not record["shoulder_offset_matches_torso"] or not record["tool_integrity"]["all_source_bronze_pixels_owned_by_forearm_tool"]:
				errors.append("姿态验收失败，保留诊断源，禁止自动擦点或填缝：" + pose_file)
			if output.save_png(_path(output_path)) != OK:
				errors.append("无法保存新版本 PNG：" + output_path)
			record["sha256"] = FileAccess.get_sha256(_path(output_path))
			frames.append(record)
			rendered.append(output)
			pose_names.append("%s %s f%02d" % [direction, state, index])

func _validate_parts(image: Image, rig: Dictionary) -> Dictionary:
	var parts := {}
	var covered := {}
	for part: Dictionary in rig["parts"]:
		var pixels: Array = part["pixels"]
		var name := str(part["name"])
		if not name in PART_NAMES or pixels.is_empty():
			errors.append("rig 部件缺失或未知：" + name)
			return {}
		parts[name] = pixels
		for pixel: Array in pixels:
			var point := Vector2i(int(pixel[0]), int(pixel[1]))
			if covered.has(point) or image.get_pixelv(point).a != 1.0:
				errors.append("rig 部件重叠或包含透明源点：" + name)
				return {}
			covered[point] = name
	for y in SIZE.y:
		for x in SIZE.x:
			if image.get_pixel(x, y).a > 0.0 and not covered.has(Vector2i(x, y)):
				errors.append("rig 未覆盖原图实体点。")
				return {}
	return parts

func _arm_cut_y(direction: String) -> int:
	return {"down": 48, "left": 50, "right": 47, "up": 50}[direction]

func _split_left_arm(parts: Dictionary, direction: String) -> Dictionary:
	## 明确逐点子部件归属：不再把肩甲随整个工具臂大幅搬过胸口。
	var result := parts.duplicate(true)
	var upper := []
	var forearm := []
	var boundary := _arm_cut_y(direction)
	for pixel: Array in parts["left_arm"]:
		if int(pixel[1]) <= boundary:
			upper.append(pixel)
		else:
			forearm.append(pixel)
	result.erase("left_arm")
	result["left_upper_arm"] = upper
	result["left_forearm_tool"] = forearm
	return result

func _default_pose(direction: String, state: String, index: int, idle_file: String, rig_file: String) -> Dictionary:
	var offsets := {"head": [0, 0], "torso": [0, 0], "right_arm": [0, 0], "left_upper_arm": [0, 0], "left_forearm_tool": [0, 0], "right_leg": [0, 0], "left_leg": [0, 0]}
	var order := ["right_leg", "left_leg", "torso", "right_arm", "left_upper_arm", "left_forearm_tool", "head"]
	if direction == "left":
		order = ["right_leg", "right_arm", "torso", "left_leg", "left_upper_arm", "left_forearm_tool", "head"]
	elif direction == "right":
		order = ["left_leg", "left_upper_arm", "left_forearm_tool", "torso", "right_leg", "right_arm", "head"]
	elif direction == "up":
		order = ["left_leg", "right_leg", "torso", "left_forearm_tool", "left_upper_arm", "right_arm", "head"]
	var joint_pixels := []
	var phase := "呼吸微动：上身下降 1 像素，双脚原位支撑。"
	if state == "idle":
		for name: String in ["head", "torso", "right_arm", "left_upper_arm", "left_forearm_tool"]:
			offsets[name] = [0, 1]
	else:
		phase = ["准备：微俯身并抬出原左腕采集工具。", "下探：头盔和胸甲整体俯低，左腕伸向采集方向。", "保持：维持支撑与工具指向，继续 1 像素下探。", "收回：左腕与上身朝原站姿返回。"][index]
		var lean: int = [1, 3, 4, 2][index]
		var side := -1 if direction == "left" else 1 if direction == "right" else 0
		var shift: int = [0, 2, 2, 1][index] * side
		for name: String in ["head", "torso", "right_arm"]:
			offsets[name] = [shift, lean]
		offsets["left_upper_arm"] = [shift, lean]
		if direction == "down":
			var forearm_down: int = [2, 6, 7, 3][index]
			offsets["left_forearm_tool"] = [0, forearm_down]
			# 原肘部的深色套杆显式延伸：逐点标注，不根据输出 Alpha 自动填洞。
			for y in range(49 + lean, 49 + forearm_down):
				for x in range(43, 48):
					joint_pixels.append({"at": [x, y], "source_rgba_at": [x, 50],
						"anatomical_reason": "Anchored upper-arm cuff to reaching forearm elbow sleeve; original dark joint outline and steel colors."})
		elif direction == "left":
			offsets["left_forearm_tool"] = [[-1, -7, -7, -3][index], lean]
		elif direction == "right":
			offsets["left_forearm_tool"] = [[1, 4, 4, 2][index], lean]
		elif direction == "up":
			offsets["left_forearm_tool"] = [0, [-1, -4, -5, -2][index]]
	return {"schema_version": 2, "direction": direction, "state": state, "frame_index": index,
		"idle_source": "res://" + idle_file, "parts_file": "res://" + rig_file,
		"foot_anchor": [32, 80], "offsets": offsets, "draw_order": order, "joint_pixels": joint_pixels,
		"pose_description": phase, "tool_hand": "anatomical_left_arm_from_v002_rig; no mirror and no hand swap",
		"joint_policy": "Explicit overlap and draw order. Empty joint_pixels means no new pixel paint.",
		"source_art_policy": "Original component RGBA only; integer translation, no whole sprite transform or alpha repair."}

func _render_pose(image: Image, parts: Dictionary, pose: Dictionary) -> Image:
	var output := Image.create(SIZE.x, SIZE.y, false, Image.FORMAT_RGBA8)
	output.fill(Color(0, 0, 0, 0))
	var order: Array = pose["draw_order"]
	var offsets: Dictionary = pose["offsets"]
	if order.size() != 7 or offsets.size() != 7:
		errors.append("每个姿态必须明确包含七部件（工具臂分上臂及前臂）。")
		return null
	var seen := {}
	for name: String in order:
		if seen.has(name) or not parts.has(name) or not offsets.has(name):
			errors.append("绘制顺序重复或部件缺失。")
			return null
		seen[name] = true
		var offset: Array = offsets[name]
		if offset.size() != 2 or float(offset[0]) != int(offset[0]) or float(offset[1]) != int(offset[1]):
			errors.append("部件位移必须是原生整数像素。")
			return null
		var movement := Vector2i(int(offset[0]), int(offset[1]))
		for pixel: Array in parts[name]:
			var source := Vector2i(int(pixel[0]), int(pixel[1]))
			var target := source + movement
			if target.x < 0 or target.y < 0 or target.x >= SIZE.x or target.y >= SIZE.y:
				errors.append("部件越出固定画布：" + name)
				return null
			output.set_pixelv(target, image.get_pixelv(source))
	## 仅允许明确人工标注的实体关节像素；绝不自动依据 Alpha 填缝。
	for patch: Dictionary in pose.get("joint_pixels", []):
		var point := Vector2i(int(patch["at"][0]), int(patch["at"][1]))
		var sample := Vector2i(int(patch["source_rgba_at"][0]), int(patch["source_rgba_at"][1]))
		if str(patch.get("anatomical_reason", "")).is_empty() or image.get_pixelv(sample).a != 1.0:
			errors.append("关节标注必须解释解剖连接并采样原实体 RGBA。")
			return null
		output.set_pixelv(point, image.get_pixelv(sample))
	return output

func _translate_windows(windows: Array, pose: Dictionary, actual: Image, source: Image) -> Array:
	var output := windows.duplicate(true)
	var offset: Array = pose["offsets"]["torso"]
	for window: Dictionary in output:
		var rect: Array = window["safe_active_rect"]
		var original_rect := rect.duplicate()
		window["safe_active_rect"] = [int(rect[0]) + int(offset[0]), int(rect[1]) + int(offset[1]), int(rect[2]) + int(offset[0]), int(rect[3]) + int(offset[1])]
		var center: Array = window["center"]
		window["center"] = [float(center[0]) + int(offset[0]), float(center[1]) + int(offset[1])]
		window["normalized_uv"] = [float(window["center"][0]) / SIZE.x, float(window["center"][1]) / SIZE.y]
		var matches := true
		for y in range(int(original_rect[1]), int(original_rect[3])):
			for x in range(int(original_rect[0]), int(original_rect[2])):
				matches = matches and source.get_pixel(x, y) == actual.get_pixel(x + int(offset[0]), y + int(offset[1]))
		window["actual_rgba_matches_source"] = matches
		window["runtime_paint_allowed"] = matches
		if not matches:
			window["visibility"] = "OCCLUDED_BY_AUTHORED_ACTION_COMPONENT"
	return output

func _record_frame(image: Image, idle: Image, file: String, direction: String, state: String, index: int, pose: Dictionary, windows: Array) -> Dictionary:
	var bbox := image.get_used_rect()
	var binary := true
	var changes := 0
	var colors := {}
	var opaque := 0
	for y in SIZE.y:
		for x in SIZE.x:
			var color := image.get_pixel(x, y)
			binary = binary and (color.a == 0.0 or color.a == 1.0)
			if color != idle.get_pixel(x, y):
				changes += 1
			if color.a > 0.0:
				opaque += 1
				colors[color.to_html(false)] = true
	var count := _component_count(image)
	return {"id": "robot_%s_%s_f%02d" % [state, direction, index], "direction": direction, "state": state,
		"frame_index": index, "file": "res://" + file, "sha256": FileAccess.get_sha256(_path(file)),
		"anchor": [32, 80], "offsets": pose.get("offsets", {}), "draw_order": pose.get("draw_order", []),
		"pose_description": pose.get("pose_description", "Original idle reused unchanged."),
		"changed_rgba_pixels_vs_idle": changes, "runtime_windows": windows,
		"measurement": {"canvas": [64, 96], "bbox": [bbox.position.x, bbox.position.y, bbox.end.x, bbox.end.y],
			"bbox_xywh": [bbox.position.x, bbox.position.y, bbox.size.x, bbox.size.y], "binary_alpha": binary,
			"components_8": count, "visible_bottom_boundary": bbox.end.y, "opaque_pixels": opaque, "rgb_count": colors.size(),
			"subject_size_pass": bbox.size.x <= 40 and bbox.size.y <= 64,
			"transparent_border": bbox.position.x > 0 and bbox.position.y > 0 and bbox.end.x < SIZE.x and bbox.end.y < SIZE.y}}

func _component_count(image: Image) -> int:
	var seen := PackedByteArray()
	seen.resize(SIZE.x * SIZE.y)
	var count := 0
	for y in SIZE.y:
		for x in SIZE.x:
			if seen[y * SIZE.x + x] != 0 or image.get_pixel(x, y).a == 0.0:
				continue
			count += 1
			var queue: Array[Vector2i] = [Vector2i(x, y)]
			seen[y * SIZE.x + x] = 1
			var cursor := 0
			while cursor < queue.size():
				var point := queue[cursor]
				cursor += 1
				for dy in range(-1, 2):
					for dx in range(-1, 2):
						var neighbor := point + Vector2i(dx, dy)
						if neighbor.x < 0 or neighbor.y < 0 or neighbor.x >= SIZE.x or neighbor.y >= SIZE.y:
							continue
						var key := neighbor.y * SIZE.x + neighbor.x
						if seen[key] == 0 and image.get_pixelv(neighbor).a > 0.0:
							seen[key] = 1
							queue.append(neighbor)
	return count

func _part_matches(actual: Image, source: Image, pixels: Array, offset: Array) -> bool:
	for pixel: Array in pixels:
		var point := Vector2i(int(pixel[0]), int(pixel[1]))
		var target := point + Vector2i(int(offset[0]), int(offset[1]))
		if actual.get_pixelv(target) != source.get_pixelv(point):
			return false
	return true

func _region_matches(first: Image, second: Image, region: Rect2i) -> bool:
	return first.get_region(region).get_data() == second.get_region(region).get_data()

func _tool_measurement(actual: Image, source: Image, parts: Dictionary, pose: Dictionary) -> Dictionary:
	## 黄铜工具原色点只能属于解剖左腕的前臂子部件，避免任何换手或镜像。
	var bronze := ["7b4d35", "b77c4b", "e2b77a"]
	var source_points := []
	var owned := {}
	for point: Array in parts["left_forearm_tool"]:
		owned[Vector2i(int(point[0]), int(point[1]))] = true
	var all_owned := true
	var visible_exact := 0
	var offset: Array = pose["offsets"]["left_forearm_tool"]
	for y in SIZE.y:
		for x in SIZE.x:
			var color := source.get_pixel(x, y)
			if color.a == 0.0 or not color.to_html(false).to_lower() in bronze:
				continue
			var point := Vector2i(x, y)
			all_owned = all_owned and owned.has(point)
			source_points.append([x, y])
			var target := point + Vector2i(int(offset[0]), int(offset[1]))
			if actual.get_pixelv(target) == color:
				visible_exact += 1
	return {"anatomical_hand": "left", "source_bronze_pixel_count": source_points.size(),
		"all_source_bronze_pixels_owned_by_forearm_tool": all_owned, "translated_visible_exact_bronze_pixels": visible_exact,
		"forearm_tool_offset": offset, "source_bronze_points": source_points,
		"note": "Only source component placement and authored overlap; no copied tool on the right arm."}

func _write_json(path: String, value: Dictionary) -> void:
	var file := FileAccess.open(_path(path), FileAccess.WRITE)
	if file == null:
		errors.append("无法写入新版本源记录：" + path)
		return
	file.store_string(JSON.stringify(value, "\t") + "\n")

func _capture_contact_sheet() -> void:
	## 只做真实 GPU 预览，整数 4× 采样不修改新角色 PNG。
	var viewport := SubViewport.new()
	viewport.size = Vector2i(5 * 256, 4 * 416)
	viewport.transparent_bg = false
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	var background := ColorRect.new()
	background.size = Vector2(viewport.size)
	background.color = Color("34454e")
	viewport.add_child(background)
	for index in rendered.size():
		var sprite := Sprite2D.new()
		sprite.texture = ImageTexture.create_from_image(rendered[index])
		sprite.centered = false
		sprite.scale = Vector2(4, 4)
		sprite.position = Vector2(index % 5 * 256, index / 5 * 416)
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		viewport.add_child(sprite)
		var label := Label.new()
		label.text = pose_names[index]
		label.position = sprite.position + Vector2(8, 386)
		label.add_theme_font_size_override("font_size", 18)
		viewport.add_child(label)
	root.add_child(viewport)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	image.save_png(_path(SOURCE_DIR + "/new_actions_contact_4x_v003.png"))
	root.remove_child(viewport)
	viewport.free()
