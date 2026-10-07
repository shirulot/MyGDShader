extends SceneTree
## 只读机器人复查：加载原始 PNG，报告连通域、边界、哈希与图集一致性。
## 本脚本不修补、不擦除 Alpha、不回写角色资源；预览由真实 Godot 绘制。

const FRAME_SIZE := Vector2i(64, 96)
const PIVOT := Vector2i(32, 80)
var workspace := ""
var output_dir := ""
var errors: Array[String] = []
var current_frames: Array[Dictionary] = []
var current_images: Array[Image] = []
var report: Dictionary = {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--workspace="):
			workspace = argument.trim_prefix("--workspace=").replace("\\", "/")
		elif argument.begins_with("--output="):
			output_dir = argument.trim_prefix("--output=").replace("\\", "/")
	if workspace.is_empty() or output_dir.is_empty():
		push_error("需要 --workspace 与 --output 绝对路径。")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_dir)
	report = {"schema_version": 1, "timestamp_utc": Time.get_datetime_string_from_system(true),
		"engine": Engine.get_version_info(), "scope": "read_only_raw_png_alpha_and_gpu_audit",
		"canvas": [64, 96], "foot_pivot": [32, 80], "versions": {}, "source_hashes_before": {}}
	for version in ["v001", "v002"]:
		_audit_catalog(version)
	_audit_map_references()
	if DisplayServer.get_name() != "headless" and current_images.size() == 20:
		await _capture_sheet(false)
		await _capture_sheet(true)
		await _capture_map_scale()
	report["source_hashes_preserved"] = true
	for path: String in report["source_hashes_before"]:
		if FileAccess.get_sha256(path) != report["source_hashes_before"][path]:
			errors.append("只读审查过程中源文件发生变化：" + path)
			report["source_hashes_preserved"] = false
	report["technical_status"] = "PASS" if errors.is_empty() else "FAIL"
	report["errors"] = errors
	var file := FileAccess.open(output_dir.path_join("alpha_audit_v003.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	print("ROBOT_AUDIT ", report["technical_status"], " current=", current_images.size(), " errors=", errors.size())
	quit(0 if errors.is_empty() else 1)

func _absolute(path: String) -> String:
	return workspace.path_join(path.trim_prefix("res://"))

func _read_image(path: String) -> Image:
	var image := Image.load_from_file(path)
	if image == null:
		errors.append("无法读原始 PNG：" + path)
		return null
	image.convert(Image.FORMAT_RGBA8)
	report["source_hashes_before"][path] = FileAccess.get_sha256(path)
	return image

func _audit_catalog(version: String) -> void:
	var catalog_path := _absolute("res://assets/ember/characters/robot/robot_frames_catalog_%s.json" % version)
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(catalog_path))
	if not parsed is Dictionary:
		errors.append("角色目录不是 JSON object：" + catalog_path)
		return
	var catalog: Dictionary = parsed
	report["source_hashes_before"][catalog_path] = FileAccess.get_sha256(catalog_path)
	var atlas_path := _absolute("res://assets/ember/characters/robot/robot_animations_%s.png" % version)
	var atlas := _read_image(atlas_path)
	var records: Array[Dictionary] = []
	var transitions: Array[Dictionary] = []
	var loaded: Dictionary = {}
	for frame: Dictionary in catalog["frames"]:
		var path := _absolute(str(frame["file"]))
		var image := _read_image(path)
		if image == null:
			continue
		var record := _measure(image)
		record["id"] = str(frame["id"])
		record["file"] = str(frame["file"])
		record["sha256"] = FileAccess.get_sha256(path)
		record["catalog_sha_matches"] = record["sha256"] == str(frame["sha256"])
		var coord: Array = frame["coord"]
		var atlas_region := Rect2i(Vector2i(int(coord[0]), int(coord[1])) * FRAME_SIZE, FRAME_SIZE)
		record["atlas_region_rgba_matches"] = atlas != null and atlas.get_region(atlas_region).get_data() == image.get_data()
		if not record["catalog_sha_matches"] or not record["atlas_region_rgba_matches"]:
			errors.append("目录哈希或图集区域不一致：" + path)
		if image.get_size() != FRAME_SIZE or not record["binary_alpha"] or record["edge_occupied"]:
			errors.append("画布、二值 Alpha 或边界留白异常：" + path)
		if version == "v002" and record["components_8"].size() != 1:
			errors.append("当前帧存在游离主体：" + path)
		records.append(record)
		loaded[str(frame["id"])] = image
		if version == "v002":
			current_frames.append(frame)
			current_images.append(image)
	for direction: String in ["down", "left", "right", "up"]:
		for index in range(4):
			var from_id := "robot_walk_%s_f%02d" % [direction, index]
			var to_id := "robot_walk_%s_f%02d" % [direction, (index + 1) % 4]
			if loaded.has(from_id) and loaded.has(to_id):
				var changes := _changed_pixels(loaded[from_id], loaded[to_id])
				transitions.append({"from": from_id, "to": to_id, "rgba_changed_pixels": changes})
	report["versions"][version] = {"catalog": catalog_path, "catalog_sha256": FileAccess.get_sha256(catalog_path),
		"frames": records, "walk_transitions": transitions, "frame_count": records.size()}

func _measure(image: Image) -> Dictionary:
	var opaque := 0
	var binary := true
	var edge := false
	var minimum := image.get_size()
	var maximum := Vector2i(-1, -1)
	var colors := {}
	for y in image.get_height():
		for x in image.get_width():
			var color := image.get_pixel(x, y)
			if color.a > 0.0 and color.a < 1.0:
				binary = false
			if color.a == 0.0:
				continue
			opaque += 1
			colors[color.to_html(false)] = true
			minimum.x = mini(minimum.x, x)
			minimum.y = mini(minimum.y, y)
			maximum.x = maxi(maximum.x, x)
			maximum.y = maxi(maximum.y, y)
			edge = edge or x == 0 or y == 0 or x == image.get_width() - 1 or y == image.get_height() - 1
	return {"size": [image.get_width(), image.get_height()], "bbox_xywh": [minimum.x, minimum.y,
		maximum.x - minimum.x + 1, maximum.y - minimum.y + 1], "visible_bottom_boundary": maximum.y + 1,
		"opaque_pixels": opaque, "binary_alpha": binary, "edge_occupied": edge,
		"rgb_count": colors.size(), "components_8": _components(image, true), "components_4": _components(image, false)}

func _components(image: Image, diagonal: bool) -> Array[Dictionary]:
	## 8 连通允许像素对角相连，避免把合法像素轮廓误判成断裂。
	var width := image.get_width()
	var height := image.get_height()
	var seen := PackedByteArray()
	seen.resize(width * height)
	var components: Array[Dictionary] = []
	for y in height:
		for x in width:
			var start := y * width + x
			if seen[start] != 0 or image.get_pixel(x, y).a == 0.0:
				continue
			var pending: Array[Vector2i] = [Vector2i(x, y)]
			seen[start] = 1
			var cursor := 0
			var minimum := Vector2i(x, y)
			var maximum := minimum
			while cursor < pending.size():
				var point := pending[cursor]
				cursor += 1
				minimum.x = mini(minimum.x, point.x)
				minimum.y = mini(minimum.y, point.y)
				maximum.x = maxi(maximum.x, point.x)
				maximum.y = maxi(maximum.y, point.y)
				for dy in range(-1, 2):
					for dx in range(-1, 2):
						if (dx == 0 and dy == 0) or (not diagonal and dx != 0 and dy != 0):
							continue
						var next := point + Vector2i(dx, dy)
						if next.x < 0 or next.x >= width or next.y < 0 or next.y >= height:
							continue
						var next_index := next.y * width + next.x
						if seen[next_index] == 0 and image.get_pixelv(next).a > 0.0:
							seen[next_index] = 1
							pending.append(next)
			var record := {"area": pending.size(), "bbox_xywh": [minimum.x, minimum.y, maximum.x - minimum.x + 1, maximum.y - minimum.y + 1]}
			if pending.size() <= 32:
				var pixels := []
				for point in pending:
					pixels.append([point.x, point.y])
				record["exact_pixels"] = pixels
			components.append(record)
	components.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["area"]) > int(b["area"]))
	return components

func _changed_pixels(first: Image, second: Image) -> int:
	var count := 0
	for y in first.get_height():
		for x in first.get_width():
			if first.get_pixel(x, y) != second.get_pixel(x, y):
				count += 1
	return count

func _audit_map_references() -> void:
	var maps := []
	for key: String in ["tidal_port", "dry_mine", "overgrown_lab"]:
		var path := _absolute("res://scenes/ember/map_assets_%s_v001.tscn" % key)
		var text := FileAccess.get_file_as_string(path)
		report["source_hashes_before"][path] = FileAccess.get_sha256(path)
		var block_start := text.find("[node name=\"ExistingRobot\"")
		var block_end := text.find("\n[node ", block_start + 1) if block_start >= 0 else -1
		var robot_block := text.substr(block_start, block_end - block_start if block_end >= 0 else -1) if block_start >= 0 else ""
		var scale_pattern := RegEx.new()
		scale_pattern.compile("scale = Vector2\\(([^,]+), ([^)]+)\\)")
		var offset_pattern := RegEx.new()
		offset_pattern.compile("offset = Vector2\\(([^,]+), ([^)]+)\\)")
		var scale_match := scale_pattern.search(robot_block)
		var offset_match := offset_pattern.search(robot_block)
		var scale := Vector2.ONE
		var offset := Vector2.ZERO
		if scale_match != null:
			scale = Vector2(scale_match.get_string(1).to_float(), scale_match.get_string(2).to_float())
		if offset_match != null:
			offset = Vector2(offset_match.get_string(1).to_float(), offset_match.get_string(2).to_float())
		var centered := not robot_block.contains("centered = false")
		var local_top_left := -Vector2(FRAME_SIZE) / 2.0 if centered else Vector2.ZERO
		var actual_foot_from_node := (local_top_left + offset + Vector2(PIVOT)) * scale
		maps.append({"scene": path, "sha256": FileAccess.get_sha256(path),
			"uses_idle_down_v001": text.contains("robot_idle_down_v001.png"), "uses_walk_v001": text.contains("robot_walk_") and text.contains("_v001.png"),
			"uses_animation_atlas_v001": text.contains("robot_animations_v001.png"),
			"robot_centered": centered, "robot_scale": [scale.x, scale.y], "robot_offset": [offset.x, offset.y],
			"actual_foot_offset_from_node_world": [actual_foot_from_node.x, actual_foot_from_node.y],
			"foot_pivot_registration_matches": actual_foot_from_node.is_zero_approx(),
			"integration_finding": "FOOT_NODE_REGISTRATION_MISMATCH" if not actual_foot_from_node.is_zero_approx() else "NONE"})
	report["current_map_references"] = maps

func _capture_sheet(checker: bool) -> void:
	var factor := 4
	var viewport := SubViewport.new()
	viewport.size = FRAME_SIZE * Vector2i(5, 4) * factor
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	if checker:
		for y in range(0, viewport.size.y, 32):
			for x in range(0, viewport.size.x, 32):
				var tile := ColorRect.new()
				tile.position = Vector2(x, y)
				tile.size = Vector2(32, 32)
				tile.color = Color("26343b") if (x / 32 + y / 32) % 2 == 0 else Color("34454e")
				viewport.add_child(tile)
	for index in current_images.size():
		var sprite := Sprite2D.new()
		sprite.texture = ImageTexture.create_from_image(current_images[index])
		sprite.centered = false
		sprite.scale = Vector2(factor, factor)
		sprite.position = Vector2(index % 5 * FRAME_SIZE.x, index / 5 * FRAME_SIZE.y) * factor
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		viewport.add_child(sprite)
	root.add_child(viewport)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var captured := viewport.get_texture().get_image()
	captured.convert(Image.FORMAT_RGBA8)
	var filename := "current_v002_gpu_checker_4x.png" if checker else "current_v002_gpu_transparent_4x.png"
	var path := output_dir.path_join(filename)
	captured.save_png(path)
	if not checker:
		var alpha_changes := 0
		var visible_rgb_changes := 0
		for index in current_images.size():
			var image := current_images[index]
			var origin := Vector2i(index % 5 * FRAME_SIZE.x, index / 5 * FRAME_SIZE.y) * factor
			for y in image.get_height():
				for x in image.get_width():
					var expected := image.get_pixel(x, y)
					for dy in factor:
						for dx in factor:
							var actual := captured.get_pixelv(origin + Vector2i(x, y) * factor + Vector2i(dx, dy))
							if actual.a != expected.a:
								alpha_changes += 1
							if expected.a > 0.0 and (actual.r8 != expected.r8 or actual.g8 != expected.g8 or actual.b8 != expected.b8):
								visible_rgb_changes += 1
		report["gpu_transparent_rgba"] = {"alpha_changed_pixels": alpha_changes, "visible_rgb_changed_pixels": visible_rgb_changes,
			"source_frames": 20, "factor": 4, "dimensions": [captured.get_width(), captured.get_height()], "file": path,
			"sha256": FileAccess.get_sha256(path)}
		if alpha_changes != 0 or visible_rgb_changes != 0:
			errors.append("GPU 4× 读回出现 Alpha 或可见 RGB 差异。")
	root.remove_child(viewport)
	viewport.free()

func _capture_map_scale() -> void:
	## 现有地图角色 scale=0.65，Camera2D.zoom=2，最终等效 1.3×。
	var viewport := SubViewport.new()
	viewport.size = Vector2i(832, 160)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	for index in range(5):
		var sprite := Sprite2D.new()
		sprite.texture = ImageTexture.create_from_image(current_images[index])
		sprite.centered = false
		sprite.offset = -Vector2(PIVOT)
		sprite.scale = Vector2(1.3, 1.3)
		sprite.position = Vector2(80 + index * 160, 140)
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		viewport.add_child(sprite)
	root.add_child(viewport)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	var path := output_dir.path_join("down_equivalent_map_scale_1p3x.png")
	image.save_png(path)
	report["map_scale_diagnostic"] = {"equivalent_scale": 1.3, "file": path,
		"purpose": "sampling appearance only; fractional nearest produces alternating pixel widths but no source edits"}
	root.remove_child(viewport)
	viewport.free()
