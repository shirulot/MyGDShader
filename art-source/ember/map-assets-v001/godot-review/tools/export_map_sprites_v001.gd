extends SceneTree
## 将真实生图注册成统一像素画布；不抠图、不改色、不重绘。
## 使用：Godot --headless --path 项目 --script res://tools/export_map_sprites_v001.gd
## 可选：-- --ids=harbor_office,cargo_crate；只处理列出的 ID。

const SPECS_PATH := "res://art-source/ember/map-assets-v001/source_specs_v001.json"
const SOURCE_DIR := "res://art-source/ember/map-assets-v001/masters/"
const OUTPUT_DIR := "res://assets/ember/map_assets_v001/"
const REPORT_PATH := OUTPUT_DIR + "sprite_registration_v001.json"
const ALPHA_THRESHOLD := 0.01
var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	if not FileAccess.file_exists(SPECS_PATH):
		push_error("Missing sprite specification: " + SPECS_PATH)
		quit(1)
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(SPECS_PATH))
	var specs: Array = []
	if parsed is Array:
		specs = parsed
	elif parsed is Dictionary:
		specs = parsed.get("sprites", [])
	else:
		push_error("Sprite specification must be an array or an object with sprites array.")
		quit(1)
		return
	var requested: PackedStringArray = []
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--ids="):
			requested = argument.trim_prefix("--ids=").split(",", false)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	# 分批生成时合并已经成功注册的记录，避免后续批次覆盖先前的目录。
	var entries_by_id: Dictionary = {}
	if FileAccess.file_exists(REPORT_PATH):
		var previous: Variant = JSON.parse_string(FileAccess.get_file_as_string(REPORT_PATH))
		if previous is Dictionary:
			for entry: Dictionary in previous.get("sprites", []):
				entries_by_id[String(entry.get("id", ""))] = entry
	var processed: Array[String] = []
	for spec_variant: Variant in specs:
		if not spec_variant is Dictionary:
			failures.append("Invalid non-object sprite specification.")
			continue
		var spec: Dictionary = spec_variant
		var id := String(spec.get("id", ""))
		if not requested.is_empty() and not id in requested:
			continue
		var entry := _register(spec)
		entries_by_id[id] = entry
		processed.append(id)
		print("MAP_SPRITE_REGISTERED: " + id + " " + String(entry.get("status", "FAIL")))
	var entries: Array = []
	var ids: Array = entries_by_id.keys()
	ids.sort()
	for id: String in ids:
		entries.append(entries_by_id[id])
	if processed.is_empty(): failures.append("No requested sprites were processed.")
	for entry: Dictionary in entries:
		if entry.get("status") != "PASS" and not String(entry.get("id", "")) in processed:
			failures.append("Previously registered sprite still requires attention: " + String(entry.get("id", "")))
	var report := {
		"revision": "map_assets_v001", "status": "PASS" if failures.is_empty() else "FAIL",
		"engine": Engine.get_version_info().string,
		"tool_sha256": FileAccess.get_sha256("res://tools/export_map_sprites_v001.gd"),
		"source_specs": SPECS_PATH, "source_specs_sha256": FileAccess.get_sha256(SPECS_PATH),
		"alpha_threshold": ALPHA_THRESHOLD, "processing": "alpha crop, aspect-preserving nearest resize, transparent canvas registration only",
		"collision_animation_gameplay": "NOT_INCLUDED", "processed_ids": processed,
		"sprites": entries, "failures": failures
	}
	_write_json(REPORT_PATH, report)
	print("MAP_SPRITE_EXPORT_" + report.status + ": " + str(processed.size()) + " sprites")
	for failure: String in failures:
		printerr(failure)
	quit(0 if failures.is_empty() else 1)


func _register(spec: Dictionary) -> Dictionary:
	var id := String(spec.get("id", ""))
	var category := String(spec.get("category", "props"))
	if category == "building": category = "buildings"
	if category == "prop" or category == "decoration": category = "props"
	var source_path := String(spec.get("source_path", SOURCE_DIR + id + ".png"))
	if not source_path.begins_with("res://") and not source_path.is_absolute_path():
		source_path = "res://" + source_path
	var result := {"id": id, "category": category, "source_path": source_path, "status": "FAIL"}
	if id.is_empty() or not id.is_valid_identifier() or id.to_lower() != id:
		return _reject(result, "Invalid stable asset ID: " + id)
	if not category in ["buildings", "props"]:
		return _reject(result, "Unknown sprite category for " + id + ": " + category)
	if not FileAccess.file_exists(source_path):
		return _reject(result, "Missing original imagegen PNG: " + source_path)
	var image := Image.new()
	if image.load_png_from_buffer(FileAccess.get_file_as_bytes(source_path)) != OK:
		return _reject(result, "Cannot read original PNG: " + source_path)
	image.convert(Image.FORMAT_RGBA8)
	result["source_sha256"] = FileAccess.get_sha256(source_path)
	result["source_size_px"] = [image.get_width(), image.get_height()]
	result["references"] = spec.get("references", spec.get("reference", []))
	result["name"] = spec.get("name", id)
	result["maps"] = spec.get("maps", [])
	result["asset_stage"] = "REGISTERED_CANDIDATE"
	result["user_accepted"] = false
	var anchor_mode := String(spec.get("anchor_mode", "bottom_center"))
	if anchor_mode == "centre": anchor_mode = "center"
	if not anchor_mode in ["bottom_center", "center"]:
		return _reject(result, "Unknown anchor_mode; use bottom_center or center: " + id)
	result["anchor_mode"] = anchor_mode
	# sheet 只有在美术提供明确 region 时才裁切，禁止按网格猜位置。
	var source_region := Rect2i(Vector2i.ZERO, image.get_size())
	if spec.has("region_px"):
		var values: Array = spec.region_px
		if values.size() != 4:
			return _reject(result, "region_px must contain x,y,w,h: " + id)
		source_region = Rect2i(int(values[0]), int(values[1]), int(values[2]), int(values[3]))
		if not Rect2i(Vector2i.ZERO, image.get_size()).encloses(source_region) or not source_region.has_area():
			return _reject(result, "Explicit source region is out of bounds: " + id)
		image = image.get_region(source_region)
	result["source_region_px"] = _rect_values(source_region)
	var alpha := _alpha_information(image)
	result["source_alpha"] = alpha
	if int(alpha.visible_pixels) == 0 or int(alpha.fully_transparent_pixels) == 0:
		result["status"] = "NEEDS_IMAGEGEN_REGENERATION"
		return _reject(result, "Original sprite must contain visible content and true transparent pixels: " + id, false)
	var canvas := _vector(spec.get("canvas_px", []))
	var body_max := _vector(spec.get("body_max_px", []))
	var pivot := _vector(spec.get("pivot_px", []))
	if canvas.x <= 2 or canvas.y <= 2 or body_max.x <= 0 or body_max.y <= 0:
		return _reject(result, "Invalid canvas_px/body_max_px: " + id)
	if pivot.x <= 0 or pivot.x >= canvas.x or pivot.y <= 0 or pivot.y >= canvas.y:
		return _reject(result, "pivot_px must lie inside the transparent canvas: " + id)
	var used_values: Array = alpha.visible_rect_px
	var used := Rect2i(int(used_values[0]), int(used_values[1]), int(used_values[2]), int(used_values[3]))
	var cropped := image.get_region(used)
	var fit_ratio := minf(float(body_max.x) / used.size.x, float(body_max.y) / used.size.y)
	var body_size := Vector2i(maxi(1, roundi(used.size.x * fit_ratio)), maxi(1, roundi(used.size.y * fit_ratio)))
	# 保留主体长宽比。Nearest 只复制来源像素，不加滤波、不重采样颜色。
	cropped.resize(body_size.x, body_size.y, Image.INTERPOLATE_NEAREST)
	# 立起的建筑与道具按接地底座注册；水面覆盖和管段按平面中心注册。
	# 两种模式的 pivot 都由规范提供，不能根据透明画布底边猜测锚点。
	var anchor_y := body_size.y if anchor_mode == "bottom_center" else floori(body_size.y / 2.0)
	var offset := Vector2i(pivot.x - floori(body_size.x / 2.0), pivot.y - anchor_y)
	var body_rect := Rect2i(offset, body_size)
	var inner_canvas := Rect2i(1, 1, canvas.x - 2, canvas.y - 2)
	if not inner_canvas.encloses(body_rect):
		return _reject(result, "Body exceeds canvas transparent border; adjust specified canvas/body/pivot: " + id)
	var exported := Image.create(canvas.x, canvas.y, false, Image.FORMAT_RGBA8)
	exported.fill(Color(0, 0, 0, 0))
	exported.blit_rect(cropped, Rect2i(Vector2i.ZERO, cropped.get_size()), offset)
	var folder := OUTPUT_DIR + category + "/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
	var output_path := folder + id + ".png"
	if exported.save_png(output_path) != OK:
		return _reject(result, "Could not save registered PNG: " + output_path)
	var scene_path := OUTPUT_DIR + "scene_library/" + id + ".tscn"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR + "scene_library/"))
	# 外部 PNG 引用让后续可在 Godot 中编辑 Sprite；导入后可直接作为 PackedScene 使用。
	var scene_text := "[gd_scene load_steps=2 format=3]\n\n[ext_resource type=\"Texture2D\" path=\"" + output_path + "\" id=\"1_sprite\"]\n\n[node name=\"" + id + "\" type=\"Sprite2D\"]\ntexture_filter = 1\ntexture = ExtResource(\"1_sprite\")\ncentered = false\noffset = Vector2(" + str(-pivot.x) + ", " + str(-pivot.y) + ")\n"
	var scene_file := FileAccess.open(scene_path, FileAccess.WRITE)
	if scene_file == null:
		return _reject(result, "Could not save reusable Sprite scene: " + scene_path)
	scene_file.store_string(scene_text)
	scene_file.close()
	result.merge({"status": "PASS", "texture": output_path, "texture_sha256": FileAccess.get_sha256(output_path),
		"scene": scene_path, "scene_sha256": FileAccess.get_sha256(scene_path),
		"canvas_px": [canvas.x, canvas.y], "body_max_px": [body_max.x, body_max.y],
		"pivot_px": [pivot.x, pivot.y], "source_crop_px": _rect_values(used),
		"registered_body_px": _rect_values(body_rect), "nearest_fit_ratio": fit_ratio,
		"output_alpha": _alpha_information(exported), "transparent_border_px": 1,
		"color_editing": "NONE", "background_removal": "NONE"}, true)
	# 接口坐标只接受美术明确标注，绝不扫描纹理猜管道端口。
	# ports_px 是规范给定的正式画布坐标；source_ports_px 是母稿全图坐标。
	if spec.has("ports_px"):
		if not spec.ports_px is Dictionary:
			return _reject(result, "ports_px must map explicit port names to canvas coordinates: " + id)
		result["ports_px"] = spec.ports_px
	if spec.has("source_ports_px"):
		if not spec.source_ports_px is Dictionary:
			return _reject(result, "source_ports_px must map explicit port names to master coordinates: " + id)
		result["source_ports_px"] = spec.source_ports_px
		var registered_ports: Dictionary = {}
		for port_name: String in spec.source_ports_px:
			if not spec.source_ports_px[port_name] is Array or spec.source_ports_px[port_name].size() != 2:
				return _reject(result, "Explicit source port must contain x,y: " + id + "/" + port_name)
			var point := _vector(spec.source_ports_px[port_name])
			var local_point := point - source_region.position - used.position
			var destination := Vector2i(
				offset.x + roundi(float(local_point.x) * body_size.x / used.size.x),
				offset.y + roundi(float(local_point.y) * body_size.y / used.size.y))
			registered_ports[port_name] = [destination.x, destination.y]
		result["registered_source_ports_px"] = registered_ports
	return result


func _alpha_information(image: Image) -> Dictionary:
	var min_x := image.get_width()
	var min_y := image.get_height()
	var max_x := -1
	var max_y := -1
	var visible := 0
	var transparent := 0
	var partial := 0
	var border_visible := 0
	# 像素遍历用于注册证据，只读取 alpha，不擦除 RGB 或任何背景。
	for y in range(image.get_height()):
		for x in range(image.get_width()):
			var alpha := image.get_pixel(x, y).a
			if alpha == 0.0: transparent += 1
			elif alpha < 1.0: partial += 1
			if alpha < ALPHA_THRESHOLD: continue
			visible += 1
			min_x = mini(min_x, x)
			min_y = mini(min_y, y)
			max_x = maxi(max_x, x)
			max_y = maxi(max_y, y)
			if x == 0 or y == 0 or x == image.get_width() - 1 or y == image.get_height() - 1:
				border_visible += 1
	var used := Rect2i(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1) if visible > 0 else Rect2i()
	return {"visible_pixels": visible, "fully_transparent_pixels": transparent, "partial_alpha_pixels": partial,
		"visible_rect_px": _rect_values(used), "edge_visible_pixels": border_visible,
		"visible_fraction": float(visible) / float(image.get_width() * image.get_height())}


func _vector(values: Variant) -> Vector2i:
	if values is Array and values.size() == 2:
		return Vector2i(int(values[0]), int(values[1]))
	return Vector2i.ZERO


func _rect_values(rect: Rect2i) -> Array:
	return [rect.position.x, rect.position.y, rect.size.x, rect.size.y]


func _reject(result: Dictionary, message: String, set_status := true) -> Dictionary:
	if set_status: result["status"] = "FAIL"
	result["reason"] = message
	failures.append(message)
	return result


func _write_json(path: String, data: Dictionary) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(data, "\t") + "\n")
	file.close()
