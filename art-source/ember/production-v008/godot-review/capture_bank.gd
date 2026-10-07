extends SceneTree
## 检查三个真实岸稿的独立导入、分层水底及GPU铺刷；不声明完整岸线47型。

var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func _make_tileset(path: String, count: int) -> TileSet:
	var result := TileSet.new()
	result.tile_size = Vector2i(128, 128)
	var source := TileSetAtlasSource.new()
	source.texture = load(path) as Texture2D
	source.texture_region_size = Vector2i(128, 128)
	source.use_texture_padding = true
	result.add_source(source, 0)
	for i in range(count):
		source.create_tile(Vector2i(i, 0))
	return result

func _label(parent: Node, caption: String, position: Vector2) -> void:
	var label := Label.new()
	label.text = caption
	label.position = position
	label.add_theme_font_size_override("font_size", 18)
	parent.add_child(label)

func _layer(parent: Node, tileset: TileSet) -> TileMapLayer:
	var layer := TileMapLayer.new()
	layer.tile_set = tileset
	# 纹理128、世界格32；父节点缩放只是检视倍率，源图和逻辑尺寸不变。
	layer.scale = Vector2.ONE * 0.25
	layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	parent.add_child(layer)
	return layer

func _run() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1024, 768)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var background := ColorRect.new()
	background.size = Vector2(1024, 768)
	background.color = Color("182631")
	viewport.add_child(background)
	_label(viewport, "Bank samples | texture128 / world32 | N/W inner ports32px | interfaces pending", Vector2(20, 14))
	var bank_path := "res://inputs/bank_samples_diagnostic.png"
	var bank := _make_tileset(bank_path, 3)
	var water := _make_tileset("res://inputs/water_v007_diagnostic.png", 1)
	var source := bank.get_source(0) as TileSetAtlasSource
	var raw := Image.new()
	assert(raw.load_png_from_buffer(FileAccess.get_file_as_bytes(bank_path)) == OK)
	var imported := source.texture.get_image()
	if imported.is_compressed():
		assert(imported.decompress() == OK)
	imported.convert(Image.FORMAT_RGBA8)
	raw.convert(Image.FORMAT_RGBA8)
	var alpha_differences := 0
	var rgb_differences := 0
	for y in range(raw.get_height()):
		for x in range(raw.get_width()):
			var a := raw.get_pixel(x, y)
			var b := imported.get_pixel(x, y)
			if a.a != b.a:
				alpha_differences += 1
			if a.a > 0.0 and (a.r != b.r or a.g != b.g or a.b != b.b):
				rgb_differences += 1
	if alpha_differences != 0 or rgb_differences != 0:
		failures.append("Import changed source Alpha or visible RGB.")
	for i in range(3):
		var sample := Node2D.new()
		sample.position = Vector2(40+i*320, 86)
		sample.scale = Vector2.ONE * 8
		viewport.add_child(sample)
		var water_layer := _layer(sample, water)
		water_layer.set_cell(Vector2i.ZERO, 0, Vector2i.ZERO)
		var bank_layer := _layer(sample, bank)
		bank_layer.set_cell(Vector2i.ZERO, 0, Vector2i(i, 0))
		_label(viewport, ["N straight | width30", "NW outer | width31/32", "NW inner v003 | curved, ports32"][i], Vector2(40+i*320, 362))
	_label(viewport, "Partial N join: outer + five straight cells; other directions are not provided.", Vector2(40, 410))
	var join := Node2D.new()
	join.position = Vector2(40, 460)
	join.scale = Vector2.ONE * 4
	viewport.add_child(join)
	var water_layer := _layer(join, water)
	var bank_layer := _layer(join, bank)
	for x in range(6):
		for y in range(2):
			water_layer.set_cell(Vector2i(x, y), 0, Vector2i.ZERO)
		bank_layer.set_cell(Vector2i(x, 0), 0, Vector2i(1 if x == 0 else 0, 0))
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	assert(DisplayServer.get_name() != "headless", "Capture requires actual GPU.")
	var image := viewport.get_texture().get_image()
	assert(image.save_png("res://bank_samples_gpu.png") == OK)
	var report := {"status": "GPU_CAPTURED_ART_REVIEW_PENDING", "engine": Engine.get_version_info(),
		"compared_import_pixels": 384*128, "alpha_differences": alpha_differences,
		"visible_rgb_differences": rgb_differences, "padding": true, "layer_scale": 0.25,
		"texture_tile_size": 128, "world_cell_size": 32, "gpu_image": "bank_samples_gpu.png",
		"image_size": image.get_size(), "complete_bank_47": false, "visual_approval": false,
		"failures": failures}
	var file := FileAccess.open("res://bank-validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	print("BANK_GPU_CAPTURED alpha_diff=", alpha_differences, " rgb_diff=", rgb_differences)
	quit(0 if failures.is_empty() else 1)
