extends SceneTree
## 静态方案的体量比较：保留母稿 RGBA，只做透明边裁切与最近邻缩放。
## 小图仅用于观察造型在目标体量下的可读性，不代表已经完成原生像素修整。

var source_dir: String
var font: SystemFont


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	source_dir = ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	var specs: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(source_dir + "/source_specs_v001.json"))
	var records: Array = []
	var images: Array[Image] = []
	for spec: Dictionary in specs.examples:
		var raw := Image.load_from_file(spec.output_path)
		assert(raw != null and not raw.is_empty(), "Missing master: " + str(spec.id))
		raw.convert(Image.FORMAT_RGBA8)
		# 母稿透明留白中可能有极浅 alpha；仅按可见主体确定裁切范围。
		# 裁切范围内部仍完整保留原 RGBA，不根据 RGB 抠背景，也不擦除边缘。
		var used: Rect2i = _visible_rect(raw)
		assert(used.has_area() and used.size != raw.get_size(), "Expected an isolated transparent unit")
		assert(raw.get_pixel(0, 0).a == 0.0 and raw.get_pixel(raw.get_width() - 1, raw.get_height() - 1).a == 0.0)
		var maximum := Vector2i(int(spec.body_max_px[0]), int(spec.body_max_px[1]))
		var ratio: float = minf(float(maximum.x) / used.size.x, float(maximum.y) / used.size.y)
		var body_size := Vector2i(maxi(1, roundi(used.size.x * ratio)), maxi(1, roundi(used.size.y * ratio)))
		var body: Image = raw.get_region(used)
		body.resize(body_size.x, body_size.y, Image.INTERPOLATE_NEAREST)
		var canvas := Vector2i(int(spec.canvas_px[0]), int(spec.canvas_px[1]))
		var pivot := Vector2i(int(spec.pivot_px[0]), int(spec.pivot_px[1]))
		var destination := Vector2i((canvas.x - body_size.x) / 2, pivot.y - body_size.y)
		var small := Image.create(canvas.x, canvas.y, false, Image.FORMAT_RGBA8)
		small.fill(Color.TRANSPARENT)
		small.blit_rect(body, Rect2i(Vector2i.ZERO, body_size), destination)
		var output := source_dir + "/" + str(spec.id) + "_scale_example_v001.png"
		assert(small.save_png(output) == OK)
		images.append(small)
		records.append({"id": spec.id, "name": spec.name, "source": spec.output_path,
			"source_size_px": [raw.get_width(), raw.get_height()],
			"source_visible_rect_px": [used.position.x, used.position.y, used.size.x, used.size.y],
			"body_size_px": [body_size.x, body_size.y], "preview": output,
			"source_sha256": FileAccess.get_sha256(spec.output_path),
			"alpha_preserved_inside_crop": true, "crop_alpha_threshold": 0.1,
			"interpolation": "nearest", "colour_editing": "none"})
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1920, 768)
	viewport.transparent_bg = false
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	root.add_child(viewport)
	var backdrop := ColorRect.new()
	backdrop.size = Vector2(1920, 768)
	backdrop.color = Color("17232a")
	viewport.add_child(backdrop)
	font = SystemFont.new()
	font.font_names = PackedStringArray(["Microsoft YaHei", "Segoe UI"])
	_label(viewport, "EMBER  /  敌人单位示例 001", Vector2(64, 40), Vector2(1600, 60), 36, Color("e1dfcd"))
	_label(viewport, "统一体量比较 · 最近邻 4 倍显示 · 静态造型参考", Vector2(64, 112), Vector2(1600, 50), 22, Color("98aaa9"))
	var hero := Image.load_from_file(str(specs.examples[0].references[0]))
	_add_unit(viewport, hero, Vector2(192, 520), Vector2(32, 80))
	_label(viewport, "现有机器人", Vector2(32, 208), Vector2(320, 46), 28, Color("b9cbbf"), true)
	_label(viewport, "比例基准", Vector2(32, 612), Vector2(320, 40), 22, Color("98aaa9"), true)
	for index in range(images.size()):
		var spec: Dictionary = specs.examples[index]
		var center_x: float = 576.0 + index * 384.0
		var anchor := Vector2(center_x, 520)
		# 悬浮机留出悬空距离；机身像素比例仍与其他单位相同。
		if str(spec.id) == "enemy_scout_drone":
			anchor.y -= 96
		_add_unit(viewport, images[index], anchor, Vector2(spec.pivot_px[0], spec.pivot_px[1]))
		_label(viewport, "%02d  %s" % [index + 1, str(spec.name)], Vector2(center_x - 176, 208), Vector2(352, 46), 26, Color("e1dfcd"), true)
		_label(viewport, str(spec.role), Vector2(center_x - 176, 612), Vector2(352, 40), 22, Color("98aaa9"), true)
	_label(viewport, "四款沿用浅装甲 / 蓝灰结构 / 黄铜接头，通过轮廓与工具区分职能。", Vector2(64, 702), Vector2(1792, 42), 22, Color("b0bbb4"))
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var board_path := source_dir + "/enemy_examples_comparison_v001.png"
	assert(viewport.get_texture().get_image().save_png(board_path) == OK)
	var report := FileAccess.open(source_dir + "/preview_report_v001.json", FileAccess.WRITE)
	report.store_string(JSON.stringify({"status": "VISUAL_EXAMPLES_READY", "scope": "Static design and size study, not production-native sprites or implemented enemies", "engine": Engine.get_version_info().string, "board": board_path, "board_scale": 4, "examples": records}, "\t"))
	report.close()
	print("ENEMY_EXAMPLES_READY ", board_path)
	quit(0)


func _add_unit(viewport: SubViewport, image: Image, anchor: Vector2, pivot: Vector2) -> void:
	var sprite := Sprite2D.new()
	sprite.texture = ImageTexture.create_from_image(image)
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.centered = false
	sprite.offset = -pivot
	sprite.scale = Vector2(4, 4)
	sprite.position = anchor
	viewport.add_child(sprite)


func _visible_rect(image: Image) -> Rect2i:
	var minimum := image.get_size()
	var maximum := Vector2i(-1, -1)
	for y in range(image.get_height()):
		for x in range(image.get_width()):
			if image.get_pixel(x, y).a < 0.1:
				continue
			minimum.x = mini(minimum.x, x)
			minimum.y = mini(minimum.y, y)
			maximum.x = maxi(maximum.x, x)
			maximum.y = maxi(maximum.y, y)
	return Rect2i(minimum, maximum - minimum + Vector2i.ONE)


func _label(parent: Node, text: String, position: Vector2, size: Vector2, pixels: int, colour: Color, centered := false) -> void:
	var label := Label.new()
	label.text = text
	label.position = position
	label.size = size
	label.add_theme_font_override("font", font)
	label.add_theme_font_size_override("font_size", pixels)
	label.add_theme_color_override("font_color", colour)
	if centered:
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	parent.add_child(label)
