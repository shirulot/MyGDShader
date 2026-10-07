extends Node2D
## 仅验证本轮新像素构件；用真实TileMapLayer呈现重复接头，记录导入一致性。

var samples: TileSet
var manifest: Dictionary
var cases: Dictionary
var indices: Dictionary = {}
var failures: Array[String] = []


func _ready() -> void:
	manifest = JSON.parse_string(FileAccess.get_file_as_string("res://inputs/catalog.json")) as Dictionary
	cases = JSON.parse_string(FileAccess.get_file_as_string("res://inputs/cases.json")) as Dictionary
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
	# 该笔刷包含尚未通过结构审查的候选；文件名保留diagnostic，避免当正式套装发布。
	assert(ResourceSaver.save(samples, "res://connected_diagnostic_tileset.tres") == OK)
	if "--capture" in OS.get_cmdline_user_args():
		call_deferred("_capture")
	else:
		_build_cases(self, 4.0)


func _label(parent: Node, caption: String, position: Vector2, size: int = 17) -> void:
	var label := Label.new()
	label.text = caption
	label.position = position
	label.add_theme_font_size_override("font_size", size)
	parent.add_child(label)


func _case(parent: Node, position: Vector2, zoom: float, cells: Array) -> void:
	var group := Node2D.new()
	group.position = position
	group.scale = Vector2.ONE * zoom
	parent.add_child(group)
	var layer := TileMapLayer.new()
	layer.tile_set = samples
	# 128纹理对应32世界格；父级仅改变观察倍率。Nearest防止插值糊边。
	layer.scale = Vector2.ONE * 0.25
	layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	group.add_child(layer)
	for cell: Array in cells:
		layer.set_cell(Vector2i(int(cell[0]), int(cell[1])), 0, Vector2i(int(indices[cell[2]]), 0))


func _build_cases(parent: Node, zoom: float) -> void:
	if zoom == 4.0:
		_label(parent, "Connected pixel mothers | all NEW assets | manual TileMapLayer | texture128 / world32", Vector2(24, 14), 21)
		_label(parent, "Floor: original 2x2 cells", Vector2(24, 56))
		_case(parent, Vector2(24, 88), zoom, cases.floor_2x2)
		_label(parent, "Floor: 4x4 repeat (north/west rims)", Vector2(320, 56))
		_case(parent, Vector2(320, 88), zoom, cases.floor_4x4)
		_label(parent, "New caps + middle", Vector2(880, 56))
		_case(parent, Vector2(880, 88), zoom, cases.corridor_original_three)
		_label(parent, "Middle repeated x3", Vector2(1064, 56))
		_case(parent, Vector2(1064, 88), zoom, cases.corridor_repeated_five)
		_label(parent, "Actual world32 below", Vector2(24, 396))
		_case(parent, Vector2(24, 428), 1.0, cases.floor_8x5)
		_case(parent, Vector2(296, 428), 1.0, cases.corridor_repeated_five)
		_label(parent, "Color/style are closer. Panel phase and rim width still require correction; not a complete 47 set.", Vector2(24, 758), 18)
	else:
		_label(parent, "Actual world32 | all NEW pixel samples | manual TileMapLayer", Vector2(24, 16), 21)
		_label(parent, "Floor 8x5 repeat", Vector2(24, 60))
		_case(parent, Vector2(24, 96), zoom, cases.floor_8x5)
		_label(parent, "Original / repeated corridor", Vector2(328, 60))
		_case(parent, Vector2(328, 96), zoom, cases.corridor_original_three)
		_case(parent, Vector2(408, 96), zoom, cases.corridor_repeated_five)
		_label(parent, "Only N/W rims and NW outer corner. E/S closures and inner corners are missing.", Vector2(24, 294))
		_label(parent, "Import / GPU rendering pass is separate from material and structure approval.", Vector2(24, 328))


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
	if output.ends_with("registration_compare_gpu.png"):
		_label(viewport, "Whole square crop comparison | same mother / palette | not a production pass", Vector2(24, 14), 20)
		_label(viewport, "627px squares (baseline)", Vector2(24, 56))
		_case(viewport, Vector2(24, 88), 4.0, cases.floor_repeat_627)
		_label(viewport, "617px squares (preserves more leading bevel)", Vector2(456, 56))
		_case(viewport, Vector2(456, 88), 4.0, cases.floor_repeat_617)
		_label(viewport, "Both retain nonuniform plate pitch. Compare complete borders and repeated interior seams.", Vector2(24, 510), 17)
	else:
		_build_cases(viewport, zoom)
	await get_tree().process_frame
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	assert(DisplayServer.get_name() != "headless", "Actual GPU is required for captures.")
	assert(viewport.get_texture().get_image().save_png(output) == OK)
	viewport.queue_free()
	await get_tree().process_frame


func _capture() -> void:
	var import_result := _import_check()
	await _save_view(Vector2i(1344, 804), 4.0, "res://connected_native_gpu.png")
	await _save_view(Vector2i(960, 380), 1.0, "res://connected_world32_gpu.png")
	await _save_view(Vector2i(960, 550), 4.0, "res://registration_compare_gpu.png")
	var report := {"status": "TECHNICAL_IMPORT_GPU_CAPTURED_VISUAL_REVIEW_SEPARATE", "engine": Engine.get_version_info(),
		"display_server": DisplayServer.get_name(), "rendering_driver": RenderingServer.get_current_rendering_driver_name(),
		"source_atlas_sha256": manifest.atlas_sha256, "import": import_result,
		"texture_tile_size": 128, "world_cell_size": 32, "layer_scale": 0.25, "padding": true,
		"gpu_captures": ["connected_native_gpu.png", "connected_world32_gpu.png", "registration_compare_gpu.png"],
		"old_assets_in_corrected_layout": 0, "complete_47": false, "terrain_selection_tested": false,
		"visual_approval": false, "production_ready": false, "failures": failures}
	FileAccess.open("res://validation.json", FileAccess.WRITE).store_string(JSON.stringify(report, "\t"))
	print("CONNECTED_GPU_CAPTURED alpha_diff=", import_result.alpha_differences, " visible_rgb_diff=", import_result.visible_rgb_differences)
	get_tree().quit(0 if failures.is_empty() else 1)
