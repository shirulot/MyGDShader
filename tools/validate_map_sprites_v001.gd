extends SceneTree
## 独立读取生产 PNG 与场景校验注册证据；只读美术，不重绘或修补像素。
## 须先导入项目，让 scene_library 中的外部 PNG 引用可加载。

const OUTPUT_DIR := "res://assets/ember/map_assets_v001/"
const REGISTRATION := OUTPUT_DIR + "sprite_registration_v001.json"
const ALPHA_THRESHOLD := 0.01
var failures: Array[String] = []
var checked: Array = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--audit-sheet="):
			_audit_sheet_alpha(argument.trim_prefix("--audit-sheet="))
			return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(REGISTRATION))
	if not parsed is Dictionary:
		push_error("Missing sprite registration report: " + REGISTRATION)
		quit(1)
		return
	var registration: Dictionary = parsed
	for entry: Dictionary in registration.get("sprites", []):
		_check(entry)
	if checked.is_empty(): failures.append("No registered sprites to verify.")
	var report := {"revision": "map_assets_v001", "status": "PASS" if failures.is_empty() else "FAIL",
		"engine": Engine.get_version_info().string, "registration_sha256": FileAccess.get_sha256(REGISTRATION),
		"validator_sha256": FileAccess.get_sha256("res://tools/validate_map_sprites_v001.gd"),
		"sprites_checked": checked.size(), "checks": checked, "failures": failures,
		"scope": "PNG transparency, dimensions, source/output hashes, nearest provenance, pivot and reusable Sprite2D scenes",
		"visual_style_acceptance": "REQUIRES_USER_REVIEW", "collision_animation_gameplay": "NOT_INCLUDED"}
	var file := FileAccess.open(OUTPUT_DIR + "sprite_validation_v001.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	file.close()
	print("MAP_SPRITE_VALIDATION_" + report.status + ": " + str(checked.size()) + " sprites")
	for failure: String in failures: printerr(failure)
	quit(0 if failures.is_empty() else 1)


func _check(entry: Dictionary) -> void:
	var id := String(entry.get("id", ""))
	var before := failures.size()
	if entry.get("status") != "PASS":
		failures.append(id + ": registration is not PASS.")
		checked.append({"id": id, "status": "FAIL"})
		return
	var texture_path := String(entry.get("texture", ""))
	var source_path := String(entry.get("source_path", ""))
	var scene_path := String(entry.get("scene", ""))
	for path: String in [texture_path, source_path, scene_path]:
		if not FileAccess.file_exists(path): failures.append(id + ": missing file " + path)
	if failures.size() > before:
		checked.append({"id": id, "status": "FAIL"})
		return
	if FileAccess.get_sha256(texture_path) != entry.get("texture_sha256"):
		failures.append(id + ": output PNG differs from recorded bytes.")
	if FileAccess.get_sha256(source_path) != entry.get("source_sha256"):
		failures.append(id + ": source PNG differs from recorded bytes.")
	if FileAccess.get_sha256(scene_path) != entry.get("scene_sha256"):
		failures.append(id + ": PackedScene text differs from recorded bytes.")
	var image := Image.new()
	if image.load_png_from_buffer(FileAccess.get_file_as_bytes(texture_path)) != OK:
		failures.append(id + ": cannot read registered PNG.")
		checked.append({"id": id, "status": "FAIL"})
		return
	image.convert(Image.FORMAT_RGBA8)
	var canvas := _vector(entry.get("canvas_px", []))
	var pivot := _vector(entry.get("pivot_px", []))
	var body_max := _vector(entry.get("body_max_px", []))
	var rect_values: Array = entry.get("registered_body_px", [0, 0, 0, 0])
	var body_rect := Rect2i(int(rect_values[0]), int(rect_values[1]), int(rect_values[2]), int(rect_values[3]))
	var anchor_mode := String(entry.get("anchor_mode", "bottom_center"))
	var expected_anchor_y := body_rect.size.y if anchor_mode == "bottom_center" else floori(body_rect.size.y / 2.0)
	if image.get_size() != canvas: failures.append(id + ": wrong formal canvas size.")
	if body_rect.size.x > body_max.x or body_rect.size.y > body_max.y:
		failures.append(id + ": body exceeds specified display size.")
	if not anchor_mode in ["bottom_center", "center"]:
		failures.append(id + ": unknown registration anchor mode.")
	if body_rect.position.y + expected_anchor_y != pivot.y or body_rect.position.x != pivot.x - floori(body_rect.size.x / 2.0):
		failures.append(id + ": specified pivot registration differs.")
	if not Rect2i(1, 1, canvas.x - 2, canvas.y - 2).encloses(body_rect):
		failures.append(id + ": registered rectangle reaches transparent canvas border.")
	var visible := 0
	var partial := 0
	var transparent := 0
	var edge_visible := 0
	var outside_visible := 0
	for y in range(image.get_height()):
		for x in range(image.get_width()):
			var alpha := image.get_pixel(x, y).a
			if alpha == 0.0: transparent += 1
			elif alpha < 1.0: partial += 1
			if alpha < ALPHA_THRESHOLD: continue
			visible += 1
			if not body_rect.has_point(Vector2i(x, y)): outside_visible += 1
			if x == 0 or y == 0 or x == image.get_width() - 1 or y == image.get_height() - 1:
				edge_visible += 1
	if visible == 0 or transparent == 0: failures.append(id + ": empty content or no true transparency.")
	if edge_visible > 0 or outside_visible > 0: failures.append(id + ": visible pixels exceed registered canvas/body.")
	if entry.get("color_editing") != "NONE" or entry.get("background_removal") != "NONE":
		failures.append(id + ": unsupported modification policy.")
	# 从母稿重新执行注册，只比较生产 bytes；有效保证裁切与 nearest 没有偷偷重绘。
	_verify_nearest_pixels(entry, image)
	_verify_ports(entry, canvas)
	var packed := load(scene_path) as PackedScene
	if packed == null:
		failures.append(id + ": reusable scene cannot load after import.")
	else:
		var sprite := packed.instantiate() as Sprite2D
		if sprite == null:
			failures.append(id + ": scene root is not Sprite2D.")
		else:
			if sprite.centered or sprite.offset != -Vector2(pivot) or sprite.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST:
				failures.append(id + ": scene pivot or nearest texture filter differs.")
			if sprite.texture == null or sprite.texture.get_size() != Vector2(canvas):
				failures.append(id + ": scene texture is missing or sized incorrectly.")
			if sprite.get_child_count() != 0:
				failures.append(id + ": unexpected scene child nodes.")
			sprite.free()
	checked.append({"id": id, "status": "PASS" if failures.size() == before else "FAIL",
		"canvas_px": [canvas.x, canvas.y], "pivot_px": [pivot.x, pivot.y], "anchor_mode": anchor_mode,
		"visible_pixels": visible, "partial_alpha_pixels": partial, "transparent_pixels": transparent,
		"edge_visible_pixels": edge_visible, "outside_registered_body_pixels": outside_visible,
		"visible_fraction": float(visible) / float(canvas.x * canvas.y),
		"nearest_source_rgba_match": failures.size() == before})


func _verify_nearest_pixels(entry: Dictionary, formal: Image) -> void:
	var source := Image.new()
	if source.load_png_from_buffer(FileAccess.get_file_as_bytes(String(entry.source_path))) != OK:
		failures.append(String(entry.id) + ": source cannot be decoded for nearest proof.")
		return
	source.convert(Image.FORMAT_RGBA8)
	var region_values: Array = entry.source_region_px
	var region := Rect2i(int(region_values[0]), int(region_values[1]), int(region_values[2]), int(region_values[3]))
	source = source.get_region(region)
	var crop_values: Array = entry.source_crop_px
	var crop := Rect2i(int(crop_values[0]), int(crop_values[1]), int(crop_values[2]), int(crop_values[3]))
	source = source.get_region(crop)
	var body_values: Array = entry.registered_body_px
	var body := Rect2i(int(body_values[0]), int(body_values[1]), int(body_values[2]), int(body_values[3]))
	source.resize(body.size.x, body.size.y, Image.INTERPOLATE_NEAREST)
	var expected := Image.create(formal.get_width(), formal.get_height(), false, Image.FORMAT_RGBA8)
	expected.fill(Color(0, 0, 0, 0))
	expected.blit_rect(source, Rect2i(Vector2i.ZERO, source.get_size()), body.position)
	if expected.get_data() != formal.get_data():
		failures.append(String(entry.id) + ": formal RGBA is not the recorded nearest crop registration.")


func _verify_ports(entry: Dictionary, canvas: Vector2i) -> void:
	# 只校验明确标注坐标与转换记录，不把坐标校验等同于管道视觉接缝验收。
	for key: String in ["ports_px", "registered_source_ports_px"]:
		if not entry.has(key): continue
		var ports: Variant = entry[key]
		if not ports is Dictionary:
			failures.append(String(entry.id) + ": invalid explicit port dictionary.")
			continue
		for name: String in ports:
			var point: Variant = ports[name]
			if not point is Array or point.size() != 2:
				failures.append(String(entry.id) + ": invalid port x,y array: " + name)
				continue
			if int(point[0]) < 0 or int(point[1]) < 0 or int(point[0]) > canvas.x or int(point[1]) > canvas.y:
				failures.append(String(entry.id) + ": marked port exceeds canvas: " + name)
	if not entry.has("source_ports_px"): return
	var region: Array = entry.source_region_px
	var crop: Array = entry.source_crop_px
	var body: Array = entry.registered_body_px
	for name: String in entry.source_ports_px:
		var source_point := _vector(entry.source_ports_px[name])
		var local_point := source_point - Vector2i(int(region[0]) + int(crop[0]), int(region[1]) + int(crop[1]))
		var expected := Vector2i(int(body[0]) + roundi(float(local_point.x) * int(body[2]) / int(crop[2])),
			int(body[1]) + roundi(float(local_point.y) * int(body[3]) / int(crop[3])))
		if entry.get("registered_source_ports_px", {}).get(name) != [expected.x, expected.y]:
			failures.append(String(entry.id) + ": explicit source port transform differs: " + name)


func _vector(values: Variant) -> Vector2i:
	if values is Array and values.size() == 2: return Vector2i(int(values[0]), int(values[1]))
	return Vector2i.ZERO


func _audit_sheet_alpha(path: String) -> void:
	## 此入口只测明确 4×2 sheet 的 alpha，不导出、不擦雾、不裁成可用素材。
	## 外侧 32/64px 条带与四角 64px 方区分别测量，避免把主体亮色误称背景。
	var image := Image.new()
	if image.load_png_from_buffer(FileAccess.get_file_as_bytes(path)) != OK:
		push_error("Cannot read alpha-audit source: " + path)
		quit(1)
		return
	image.convert(Image.FORMAT_RGBA8)
	if image.get_size() != Vector2i(1536, 1024):
		push_error("Alpha audit expects explicitly approved 1536x1024 4x2 sheet.")
		quit(1)
		return
	var cells: Array = []
	for row in range(2):
		for column in range(4):
			var rect := Rect2i(column * 384, row * 512, 384, 512)
			cells.append({"cell": [column, row], "region_px": [rect.position.x, rect.position.y, rect.size.x, rect.size.y],
				"outer_32px": _alpha_zone(image, rect, 32, false),
				"outer_64px": _alpha_zone(image, rect, 64, false),
				"corner_squares_64px": _alpha_zone(image, rect, 64, true),
				"outside_opaque_bbox_plus_8px": _alpha_outside_core(image, rect)})
	var report := {"status": "READ_ONLY_MEASURED", "source": path,
		"source_sha256": FileAccess.get_sha256(path), "source_size_px": [1536, 1024],
		"explicit_grid": [4, 2], "cells": cells, "pixel_edits": "NONE",
		"note": "Statistics describe alpha only; root visually decides whether haze is unwanted."}
	var output := OUTPUT_DIR + "pipe_sheet_alpha_audit_v001.json"
	var file := FileAccess.open(output, FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	file.close()
	print("MAP_PIPE_ALPHA_AUDIT: " + JSON.stringify(cells))
	quit(0)


func _alpha_zone(image: Image, rect: Rect2i, band: int, corners_only: bool) -> Dictionary:
	var count := 0
	var total := 0.0
	var nonzero := 0
	var visible := 0
	var maximum := 0.0
	for y in range(rect.size.y):
		for x in range(rect.size.x):
			var edge_x := x < band or x >= rect.size.x - band
			var edge_y := y < band or y >= rect.size.y - band
			if not (edge_x and edge_y if corners_only else edge_x or edge_y): continue
			var alpha := image.get_pixel(rect.position.x + x, rect.position.y + y).a
			count += 1
			total += alpha
			maximum = maxf(maximum, alpha)
			if alpha > 0.0: nonzero += 1
			if alpha >= ALPHA_THRESHOLD: visible += 1
	return {"sample_pixels": count, "mean_alpha": total / count, "max_alpha": maximum,
		"nonzero_alpha_pixels": nonzero, "nonzero_alpha_fraction": float(nonzero) / count,
		"alpha_at_least_0_01_pixels": visible, "alpha_at_least_0_01_fraction": float(visible) / count}


func _alpha_outside_core(image: Image, rect: Rect2i) -> Dictionary:
	# 只读测量：近不透明主体的包围盒再向外留8px，用于判断远离主体的雾光。
	# 此盒仅为测量区域，不能用于自动裁掉背景或代替人工美术ROI。
	var min_x := rect.size.x
	var min_y := rect.size.y
	var max_x := -1
	var max_y := -1
	for y in range(rect.size.y):
		for x in range(rect.size.x):
			if image.get_pixel(rect.position.x + x, rect.position.y + y).a < 0.95: continue
			min_x = mini(min_x, x)
			min_y = mini(min_y, y)
			max_x = maxi(max_x, x)
			max_y = maxi(max_y, y)
	if max_x < 0: return {"status": "NO_OPAQUE_CORE"}
	var opaque := Rect2i(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
	var exclusion := opaque.grow(8)
	var count := 0
	var total := 0.0
	var nonzero := 0
	var visible := 0
	var maximum := 0.0
	for y in range(rect.size.y):
		for x in range(rect.size.x):
			if exclusion.has_point(Vector2i(x, y)): continue
			var alpha := image.get_pixel(rect.position.x + x, rect.position.y + y).a
			count += 1
			total += alpha
			maximum = maxf(maximum, alpha)
			if alpha > 0.0: nonzero += 1
			if alpha >= ALPHA_THRESHOLD: visible += 1
	return {"opaque_alpha_threshold": 0.95, "opaque_bbox_px": [opaque.position.x, opaque.position.y, opaque.size.x, opaque.size.y],
		"excluded_padding_px": 8, "sample_pixels": count, "mean_alpha": total / count, "max_alpha": maximum,
		"nonzero_alpha_fraction": float(nonzero) / count, "alpha_at_least_0_01_fraction": float(visible) / count}
