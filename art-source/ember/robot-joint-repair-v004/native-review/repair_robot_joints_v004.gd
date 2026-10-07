extends SceneTree
## 只执行人工逐像素关节补画。原 PNG 永不覆盖，未指定的像素一律保持。
## 接触/连通统计仅诊断；关节自然衔接还必须逐张看图和播放复核。

const PLAN := "art-source/ember/robot-joint-repair-v004/joint_overlay_plan_v004.json"
const OUTPUT := "art-source/ember/robot-joint-repair-v004"
const COLORS := ["101820", "182631", "2b3e4b", "4d6470", "829ba3", "becbc4", "566b78", "ece9d8", "7b4d35", "b77c4b", "e2b77a"]
var workspace := ""
var errors: Array = []
var results: Array = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--workspace="): workspace = arg.trim_prefix("--workspace=")
	if workspace.is_empty():
		push_error("需要 --workspace=<项目绝对路径>")
		quit(1)
		return
	var plan: Dictionary = _json(PLAN)
	var old: Dictionary = _json(plan.source_catalog)
	var lookup := {}
	for record: Dictionary in plan.frames:
		lookup[record.id] = record
	var manifest: Dictionary = old.duplicate(true)
	manifest.status = "PASS"
	manifest.source_catalog = plan.source_catalog
	manifest.source_catalog_sha256 = FileAccess.get_sha256(_abs(plan.source_catalog))
	manifest.joint_overlay_plan = "res://" + PLAN
	manifest.joint_overlay_plan_sha256 = FileAccess.get_sha256(_abs(PLAN))
	manifest.repair_scope = "Only declared native joint pixels; preserved files retain original path and SHA."
	manifest.erase("sheet")
	manifest.erase("source_manifest")
	manifest.erase("source_manifest_sha256")
	# v003 的 legacy 指向更早的 v002 快照；本版活动来源只绑定当前 v003。
	# 不把历史快照字段继承成当前已核验依赖，也不重写旧目录文件。
	manifest.erase("legacy_catalog")
	manifest.erase("legacy_catalog_sha256")
	var changed_count := 0
	for frame: Dictionary in manifest.frames:
		frame.original_file = frame.file
		frame.original_sha256 = FileAccess.get_sha256(_abs(frame.file))
		if frame.original_sha256 != frame.sha256: errors.append("原源 SHA 已漂移: " + str(frame.id))
		frame.changed = lookup.has(frame.id)
		frame.repaired_joints = []
		frame.visible_rgba_changed = 0
		if not frame.changed:
			results.append({"id": frame.id, "changed": false, "original_file": frame.file,
				"file": frame.file, "original_sha256": frame.sha256, "sha256": frame.sha256,
				"visible_rgba_changed": 0, "edited_joints": []})
			continue
		changed_count += 1
		_repair(frame, lookup[frame.id])
	manifest.changed_count = changed_count
	manifest.preserved_count = manifest.frames.size() - changed_count
	if results.size() != manifest.frames.size(): errors.append("部分修复帧未完成，禁止发布不完整报告。")
	if not errors.is_empty(): manifest.status = "FAIL"
	_write(OUTPUT + "/frame_manifest_v004.json", manifest)
	_write(OUTPUT + "/joint_repair_v004.json", {"schema_version": 1, "status": manifest.status,
		"validation_scope": "Exact native overlays, pixel guard rails, source preservation. Separate visual review required.",
		"errors": errors, "changed_count": changed_count, "preserved_count": manifest.preserved_count,
		"plan_sha256": manifest.joint_overlay_plan_sha256, "repair_tool_sha256": FileAccess.get_sha256(_abs("tools/repair_robot_joints_v004.gd")),
		"old_catalog_sha256": manifest.source_catalog_sha256,
		"source_manifest_sha256": FileAccess.get_sha256(_abs(OUTPUT + "/frame_manifest_v004.json")), "frames": results})
	print("NATIVE_JOINT_OVERLAY status=", manifest.status, " changed=", changed_count, " preserved=", manifest.preserved_count)
	for error: String in errors: push_error(error)
	quit(0 if errors.is_empty() else 1)


func _abs(path: String) -> String:
	return workspace.path_join(path.trim_prefix("res://"))


func _json(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(_abs(path)))


func _write(path: String, value: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(_abs(path).get_base_dir())
	var file := FileAccess.open(_abs(path), FileAccess.WRITE)
	file.store_string(JSON.stringify(value, "\t") + "\n")


func _repair(frame: Dictionary, repair: Dictionary) -> void:
	var original := Image.load_from_file(_abs(frame.original_file))
	original.convert(Image.FORMAT_RGBA8)
	var modified: Image = original.duplicate()
	var allowed := {}
	var patches: Array = []
	for issue: Dictionary in repair.issues:
		var roi := Rect2i(int(issue.roi[0]), int(issue.roi[1]), int(issue.roi[2]), int(issue.roi[3]))
		frame.repaired_joints.append(issue.joint)
		for pixel: Dictionary in issue.pixels:
			var point := Vector2i(int(pixel.at[0]), int(pixel.at[1]))
			if not roi.has_point(point): errors.append("补点越过关节 ROI: " + str(frame.id)); continue
			if not COLORS.has(str(pixel.color).trim_prefix("#").to_lower()): errors.append("引入非原调色板色: " + str(frame.id)); continue
			allowed[point] = true
			modified.set_pixelv(point, Color(pixel.color))
		patches.append(issue)
	var changed := 0
	var added := 0
	var opaque := 0
	var changed_pixels: Array = []
	for y in 96:
		for x in 64:
			var point := Vector2i(x, y)
			var before := original.get_pixelv(point)
			var after := modified.get_pixelv(point)
			if after.a > 0: opaque += 1
			if before == after: continue
			changed += 1
			changed_pixels.append([x, y, before.to_html(true), after.to_html(true)])
			if before.a == 0: added += 1
			if not allowed.has(point): errors.append("非指定像素变化: " + str(frame.id))
			if before.a > 0 and after.a == 0: errors.append("禁止删像素: " + str(frame.id))
			if y >= 74: errors.append("脚部像素变化: " + str(frame.id))
	if changed == 0: errors.append("被标为修复但实际像素未变: " + str(frame.id))
	# 原头部源遮罩加整数偏移，保护脸部、头甲和头部比例。
	var pose: Dictionary = {}
	var rig: Dictionary = {}
	if frame.has("pose_file"):
		pose = _json(frame.pose_file)
		rig = _json(pose.parts_file)
	else:
		rig = _json("art-source/ember/robot-repair-v002/annotations/rig_%s_v002.json" % frame.direction)
		pose = _json("art-source/ember/robot-repair-v002/annotations/walk_%s_f%02d.json" % [frame.direction, int(frame.frame_index)])
	for part: Dictionary in rig.parts:
		if part.name != "head": continue
		var offset: Array = pose.get("offsets", {}).get("head", [0, 0])
		for p: Array in part.pixels:
			var point := Vector2i(int(p[0]) + int(offset[0]), int(p[1]) + int(offset[1]))
			if original.get_pixelv(point) != modified.get_pixelv(point): errors.append("头部保护遮罩变化: " + str(frame.id))
	for window: Dictionary in frame.get("runtime_windows", []):
		var r: Array = window.get("safe_active_rect", [])
		if r.size() != 4: continue
		for y in range(int(r[1]), int(r[3])):
			for x in range(int(r[0]), int(r[2])):
				if original.get_pixel(x, y) != modified.get_pixel(x, y): errors.append("状态窗保护区变化: " + str(frame.id))
	var bbox := modified.get_used_rect()
	if bbox.size.x > 40 or bbox.size.y > 64: errors.append("主体尺寸超出原规范: " + str(frame.id))
	if bbox != original.get_used_rect(): errors.append("外轮廓包围盒变化: " + str(frame.id))
	var relative := "assets/ember/characters/robot/repairs_v004/%s_v004.png" % frame.id
	DirAccess.make_dir_recursive_absolute(_abs(relative).get_base_dir())
	if modified.save_png(_abs(relative)) != OK: errors.append("PNG 写入失败: " + relative)
	frame.file = "res://" + relative
	frame.sha256 = FileAccess.get_sha256(_abs(relative))
	frame.visible_rgba_changed = changed
	frame.joint_overlay_plan = "res://" + PLAN
	frame.joint_overlay_issues = patches
	var measurement: Dictionary = frame.measurement.duplicate(true)
	measurement["opaque_pixels"] = opaque
	frame.measurement = measurement
	results.append({"id": frame.id, "changed": true, "original_file": frame.original_file, "file": frame.file,
		"original_sha256": frame.original_sha256, "sha256": frame.sha256,
		"visible_rgba_changed": changed, "added_opaque_pixels": added, "edited_joints": frame.repaired_joints,
		"patches": patches, "changed_pixels": changed_pixels,
		"outside_declared_pixels_unchanged": true, "head_mask_unchanged": true,
		"feet_unchanged": true, "runtime_windows_unchanged": true, "bbox_unchanged": true})
	var folder := _abs(OUTPUT + "/native-review")
	DirAccess.make_dir_recursive_absolute(folder)
	_checker(original, 8).save_png(folder.path_join(str(frame.id) + "_before_8x.png"))
	_checker(modified, 8).save_png(folder.path_join(str(frame.id) + "_after_8x.png"))
	var comparison := Image.create(1024, 768, false, Image.FORMAT_RGBA8)
	comparison.blit_rect(_checker(original, 8), Rect2i(0, 0, 512, 768), Vector2i.ZERO)
	comparison.blit_rect(_checker(modified, 8), Rect2i(0, 0, 512, 768), Vector2i(512, 0))
	comparison.save_png(folder.path_join(str(frame.id) + "_comparison_8x.png"))


func _checker(raw: Image, factor: int) -> Image:
	var preview := Image.create(raw.get_width() * factor, raw.get_height() * factor, false, Image.FORMAT_RGBA8)
	for y in preview.get_height():
		for x in preview.get_width():
			var pixel := raw.get_pixel(x / factor, y / factor)
			var background := Color("3a4850") if ((x / (factor * 2)) + (y / (factor * 2))) % 2 == 0 else Color("29363e")
			preview.set_pixel(x, y, background.blend(pixel))
	return preview
