extends Node2D
## 用真实TileMapLayer显示候选，并检查导入；本工程不代表完整Terrain47验收。

var samples: TileSet
var manifest: Dictionary
var indices: Dictionary = {}
var failures: Array[String] = []


func _ready() -> void:
	manifest = JSON.parse_string(FileAccess.get_file_as_string("res://inputs/catalog.json")) as Dictionary
	var source := TileSetAtlasSource.new()
	source.texture = load("res://inputs/pilot_samples.png") as Texture2D
	source.texture_region_size = Vector2i(128, 128)
	source.use_texture_padding = true
	samples = TileSet.new()
	samples.tile_size = Vector2i(128, 128)
	samples.add_source(source, 0)
	for entry: Dictionary in manifest.entries:
		var index: int = int(entry.atlas_coord[0])
		source.create_tile(Vector2i(index, 0))
		indices[entry.id] = index
	# 保存手工诊断笔刷，包含标记为拒收的对照块，禁止作为正式整套发布。
	assert(ResourceSaver.save(samples, "res://pilot_diagnostic_tileset.tres") == OK)
	if "--capture" in OS.get_cmdline_user_args():
		call_deferred("_capture")
	else:
		_build_cases(self, 4.0)


func _label(parent: Node, caption: String, position: Vector2, font_size: int = 17) -> void:
	var label := Label.new()
	label.text = caption
	label.position = position
	label.add_theme_font_size_override("font_size", font_size)
	parent.add_child(label)


func _layer(parent: Node) -> TileMapLayer:
	var layer := TileMapLayer.new()
	layer.tile_set = samples
	# 所有层始终保持128纹理/32世界格；父节点倍率仅用于观察。
	layer.scale = Vector2.ONE * 0.25
	layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	parent.add_child(layer)
	return layer


func _case(parent: Node, position: Vector2, zoom: float, cells: Array, water: bool = false) -> void:
	var group := Node2D.new()
	group.position = position
	group.scale = Vector2.ONE * zoom
	parent.add_child(group)
	if water:
		var background := _layer(group)
		for cell: Array in cells:
			background.set_cell(Vector2i(int(cell[0]), int(cell[1])), 0, Vector2i(int(indices.water_reference), 0))
	var foreground := _layer(group)
	for cell: Array in cells:
		foreground.set_cell(Vector2i(int(cell[0]), int(cell[1])), 0, Vector2i(int(indices[cell[2]]), 0))


func _area(width: int, height: int, north: bool = false) -> Array:
	var result: Array = []
	for y in range(height):
		for x in range(width):
			result.append([x, y, "floor_edge_N" if north and y == 0 else "floor_center"])
	return result


func _passage(corrected: bool) -> Array:
	var result: Array = [[0, 0, "old_floor_cap_N"]]
	for y in range(1, 4):
		result.append([0, y, "floor_narrow_NS" if corrected else "old_floor_narrow_NS"])
	result.append([0, 4, "old_floor_cap_S"])
	return result


func _bank_repeat(count: int) -> Array:
	var result: Array = []
	for x in range(count):
		result.append([x, 0, "bank_straight_N"])
		result.append([x, 1, "water_reference"])
	return result


func _build_cases(parent: Node, zoom: float) -> void:
	if zoom == 4.0:
		_label(parent, "Pixel correction pilot | texture128 / world32 | ART NOT PASSED | manual TileMapLayer", Vector2(24, 14), 21)
		_label(parent, "Center 3x3 repeat", Vector2(32, 50))
		_case(parent, Vector2(32, 80), zoom, _area(3, 3))
		_label(parent, "North edge + center (joint phase pending)", Vector2(452, 50))
		_case(parent, Vector2(452, 80), zoom, _area(3, 3, true))
		_label(parent, "Old ends + old thin46", Vector2(900, 50))
		_label(parent, "Old ends + new126", Vector2(1120, 50))
		_case(parent, Vector2(900, 80), zoom, _passage(false))
		_case(parent, Vector2(1120, 80), zoom, _passage(true))
		_label(parent, "NW outer -> north | joint rows73 vs66, alpha shape rejected", Vector2(32, 492))
		_case(parent, Vector2(32, 530), zoom, [[0, 0, "floor_outer_NW"], [1, 0, "floor_edge_N"], [2, 0, "floor_edge_N"]])
		_label(parent, "Registered north bank repeat | ports33 (target32 +/-1) | water separate", Vector2(32, 716))
		_case(parent, Vector2(32, 752), zoom, _bank_repeat(6), true)
		_label(parent, "Inner bank: REJECTED", Vector2(860, 750))
		_case(parent, Vector2(860, 786), zoom, [[0, 0, "bank_inner_NW"]], true)
		_label(parent, "Actual world32 view", Vector2(1040, 924))
		_case(parent, Vector2(1040, 960), 1.0, _area(3, 3))
		_case(parent, Vector2(1160, 960), 1.0, _area(3, 3, true))
		_case(parent, Vector2(1296, 916), 1.0, _passage(true))
		_label(parent, "Old caps are geometry references only. Missing directions / ends / corners are NOT a complete tileset.", Vector2(24, 1066), 16)
	else:
		_label(parent, "Actual world32 | pixel candidates | not a complete tileset", Vector2(20, 14), 20)
		_label(parent, "Center 6x6", Vector2(20, 54))
		_case(parent, Vector2(20, 84), 1.0, _area(6, 6))
		_label(parent, "North long8 + center", Vector2(252, 54))
		_case(parent, Vector2(252, 84), 1.0, _area(8, 4, true))
		_label(parent, "Old / new passage", Vector2(556, 54))
		_case(parent, Vector2(556, 84), 1.0, _passage(false))
		_case(parent, Vector2(624, 84), 1.0, _passage(true))
		_label(parent, "Corner -> edge (rejected)", Vector2(252, 240))
		_case(parent, Vector2(252, 274), 1.0, [[0, 0, "floor_outer_NW"], [1, 0, "floor_edge_N"], [2, 0, "floor_edge_N"]])
		_label(parent, "North bank repeat8 (registered diagnostic)", Vector2(20, 326))
		_case(parent, Vector2(20, 362), 1.0, _bank_repeat(8), true)
		_label(parent, "Inner bank rejected", Vector2(420, 326))
		_case(parent, Vector2(420, 362), 1.0, [[0, 0, "bank_inner_NW"]], true)
		_label(parent, "Import/GPU capture does not certify artwork compatibility.", Vector2(20, 466))


func _import_check() -> Dictionary:
	var path := "res://inputs/pilot_samples.png"
	var source := Image.new()
	assert(source.load_png_from_buffer(FileAccess.get_file_as_bytes(path)) == OK)
	var imported := (load(path) as Texture2D).get_image()
	if imported.is_compressed():
		assert(imported.decompress() == OK)
	source.convert(Image.FORMAT_RGBA8)
	imported.convert(Image.FORMAT_RGBA8)
	var alpha_diff := 0
	var visible_rgb_diff := 0
	for y in range(source.get_height()):
		for x in range(source.get_width()):
			var a := source.get_pixel(x, y)
			var b := imported.get_pixel(x, y)
			if a.a != b.a:
				alpha_diff += 1
			if a.a > 0.0 and (a.r != b.r or a.g != b.g or a.b != b.b):
				visible_rgb_diff += 1
	if alpha_diff != 0 or visible_rgb_diff != 0:
		failures.append("Import changed Alpha or visible RGB.")
	return {"compared_pixels": source.get_width() * source.get_height(), "alpha_differences": alpha_diff, "visible_rgb_differences": visible_rgb_diff}


func _save_view(size: Vector2i, zoom: float, output: String) -> void:
	var viewport := SubViewport.new()
	viewport.size = size
	viewport.disable_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)
	var background := ColorRect.new()
	background.size = Vector2(size)
	background.color = Color("182631")
	viewport.add_child(background)
	_build_cases(viewport, zoom)
	await get_tree().process_frame
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	assert(DisplayServer.get_name() != "headless", "Actual GPU required for this capture.")
	assert(viewport.get_texture().get_image().save_png(output) == OK)
	viewport.queue_free()
	await get_tree().process_frame


func _capture() -> void:
	var import_result := _import_check()
	await _save_view(Vector2i(1600, 1100), 4.0, "res://pixel_pilot_native_gpu.png")
	await _save_view(Vector2i(800, 500), 1.0, "res://pixel_pilot_world32_gpu.png")
	var report := {"status": "TECHNICAL_IMPORT_GPU_CAPTURED_ART_NOT_PASSED", "engine": Engine.get_version_info(),
		"source_atlas_sha256": manifest.atlas_sha256, "import": import_result,
		"texture_tile_size": 128, "world_cell_size": 32, "layer_scale": 0.25, "padding": true,
		"gpu_captures": ["pixel_pilot_native_gpu.png", "pixel_pilot_world32_gpu.png"],
		"complete_47": false, "terrain_selection_tested_in_this_pilot": false,
		"visual_approval": false, "production_ready": false, "failures": failures}
	FileAccess.open("res://validation.json", FileAccess.WRITE).store_string(JSON.stringify(report, "\t"))
	print("PIXEL_PILOT_GPU_CAPTURED alpha_diff=", import_result.alpha_differences, " visible_rgb_diff=", import_result.visible_rgb_differences)
	get_tree().quit(0 if failures.is_empty() else 1)
