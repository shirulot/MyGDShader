extends SceneTree
## A「边缘标记」的原生 UI 皮肤导出器。
## 只构建独立静态构件：数字、正文、进度、显隐及状态判定由 Control 组件负责。
## 运行：Godot --headless --path . --script res://tools/build_ui_edge_skin_v001.gd
## 首次输出后再次运行需显式 --rebuild，避免意外覆盖已经审阅的资源。

const OUTPUT := "res://assets/ember/ui_final/skins"
const INK := Color("101820")
const PANEL := Color("182631")
const STEEL := Color("4d6470")
const STEEL_LIGHT := Color("829ba3")
const ARMOR := Color("becbc4")
const IVORY := Color("ece9d8")
const COPPER_DARK := Color("7b4d35")
const COPPER := Color("b77c4b")
const COPPER_LIGHT := Color("e2b77a")
const CYAN := Color("51c5c2")
const WARN := Color("e5a44b")
const BURST := Color("e65b4a")
const COOL := Color("566b78")
const TRANSPARENT := Color(0, 0, 0, 0)

var _entries: Array[Dictionary] = []
var _errors: PackedStringArray = []

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var absolute_output := ProjectSettings.globalize_path(OUTPUT)
	if DirAccess.dir_exists_absolute(absolute_output) and not "--rebuild" in OS.get_cmdline_user_args():
		push_error("输出目录已存在。确认需要重建后使用 --rebuild；默认保留已有资产。")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(absolute_output)
	_emit("panel_backplate_96.png", _panel(), [8, 8, 8, 8], "opaque_backplate", "弹窗自身负责遮盖场景；本层保持不透明，不能靠大图裁切遮挡。")
	_emit("text_backplate_96.png", _text_panel(), [8, 8, 8, 8], "opaque_readout_backplate", "数字与标签为独立 Label；此层仅提供安静且不透明的读数底板。")
	_emit("bracket_corner_16.png", _bracket(), [0, 0, 0, 0], "bracket_overlay", "左上 L；程序水平/垂直翻转生成另外三角，角件不能整体拉伸。")
	_emit("life_outline_24x32.png", _life_outline(), [0, 0, 0, 0], "life_outline", "每格常驻底框，24×32 画布与 fill 完全对齐；失去生命只隐藏 fill。")
	_emit("life_fill_24x32.png", _life_fill(), [0, 0, 0, 0], "life_active_fill", "生命值决定每格显隐；与 outline 同位置，不裁切或重排画布。")
	_emit("energy_track_32x16.png", _energy_track(), [8, 4, 8, 4], "energy_track", "左右边固定 8px、上下边固定 4px；推荐宽度可伸展且高度维持 16px。")
	_emit("energy_fill_8x8.png", _energy_fill(), [0, 0, 0, 0], "energy_dynamic_fill", "只重复或伸展此层。由独立 ClipContents 容器按 clamp(value/max,0,1) 裁切宽度。")
	_emit("energy_mask_8x8.png", _energy_mask(), [1, 1, 1, 1], "optional_alpha_mask", "白色 alpha 技术 Mask，四个外角透明。若使用 shader，应取 alpha；不得把此图当可见层。")
	_emit("copper_clamp_12x24.png", _clamp(), [0, 0, 0, 0], "energy_cap_overlay", "固定端帽/夹件置于填充裁切节点之外。空值、满值均保持可见。")
	_emit("drawer_handle_10x32.png", _drawer_handle(), [0, 0, 0, 0], "drawer_handle_overlay", "独立铜拉手，可固定在抽屉边界；面板开合由容器位移控制。")
	_emit("selection_row_96.png", _selection_row(), [8, 8, 8, 8], "selection_row_backplate", "只提供选中行底板；正文、图标、选中竖条独立，显隐由单一状态数据控制。")
	_emit("selection_tick_4x32.png", _selection_tick(), [1, 2, 1, 2], "state_color_overlay", "纯白颜色载体，程序 modulate 为状态颜色；可纵向九宫伸展，保留上下 2px。")
	_emit("status_safe_32.png", _safe_icon(), [0, 0, 0, 0], "state_icon", "安全菱形；选中与禁用效果由同源状态逻辑切换，图标不包含标签。")
	_emit("status_warning_32.png", _warning_icon(), [0, 0, 0, 0], "state_icon", "预警三角与镂空感叹号；形状和颜色共同传达状态。")
	_emit("status_burst_32.png", _burst_icon(), [0, 0, 0, 0], "state_icon", "爆发星形；没有烘焙外部火焰或场景危险边界。")
	_emit("status_cooldown_32.png", _cooldown_icon(), [0, 0, 0, 0], "state_icon", "冷却时钟；倒计时是独立 Label，由程序更新。")
	_emit("button_focus_96.png", _button_focus(), [8, 8, 8, 8], "button_focus_overlay", "纯角括号焦点层，中心透明，无文字；normal/hover/pressed 的底层由组件处理。")
	_emit("portrait_frame_96.png", _portrait_frame(), [8, 8, 8, 8], "portrait_border_overlay", "细蓝灰边框且中心透明。设备真实纹理是独立 TextureRect，可由单独容器裁剪。")
	_write_inventory()
	for message in _errors:
		push_error(message)
	print(JSON.stringify({"status": "PASS" if _errors.is_empty() else "FAIL", "png_count": _entries.size(), "output": OUTPUT, "errors": Array(_errors)}))
	quit(0 if _errors.is_empty() else 1)

## 所有静态艺术图严格使用二值 Alpha 与整数坐标；透明区域的 RGB 保持零。
func _canvas(width: int, height: int) -> Image:
	var image := Image.create(width, height, false, Image.FORMAT_RGBA8)
	image.fill(TRANSPARENT)
	return image

func _rect(image: Image, area: Rect2i, color: Color) -> void:
	var bounds := area.intersection(Rect2i(Vector2i.ZERO, image.get_size()))
	for y in range(bounds.position.y, bounds.end.y):
		for x in range(bounds.position.x, bounds.end.x):
			image.set_pixel(x, y, color)

func _line(image: Image, a: Vector2i, b: Vector2i, color: Color) -> void:
	# Bresenham 的全部运算保持整数，因此斜线没有抗锯齿灰边。
	var x := a.x
	var y := a.y
	var dx := absi(b.x - x)
	var dy := -absi(b.y - y)
	var sx := 1 if x < b.x else -1
	var sy := 1 if y < b.y else -1
	var error := dx + dy
	while true:
		if x >= 0 and x < image.get_width() and y >= 0 and y < image.get_height():
			image.set_pixel(x, y, color)
		if x == b.x and y == b.y:
			break
		var double_error := 2 * error
		if double_error >= dy:
			error += dy
			x += sx
		if double_error <= dx:
			error += dx
			y += sy

func _chamfer_rect(image: Image, area: Rect2i, corner: int, color: Color) -> void:
	for y in range(area.position.y, area.end.y):
		for x in range(area.position.x, area.end.x):
			var from_left := x - area.position.x
			var from_right := area.end.x - 1 - x
			var from_top := y - area.position.y
			var from_bottom := area.end.y - 1 - y
			if mini(from_left, from_right) + mini(from_top, from_bottom) >= corner:
				image.set_pixel(x, y, color)

func _panel() -> Image:
	var image := _canvas(96, 96)
	image.fill(INK)
	# 只有一像素线，没有厚框或密集铆钉；九宫中心为安静的整片色。
	_rect(image, Rect2i(0, 0, 96, 1), STEEL)
	_rect(image, Rect2i(0, 0, 1, 96), STEEL)
	_rect(image, Rect2i(95, 0, 1, 96), PANEL)
	_rect(image, Rect2i(0, 95, 96, 1), PANEL)
	return image

func _text_panel() -> Image:
	var image := _canvas(96, 96)
	image.fill(INK)
	_rect(image, Rect2i(0, 0, 96, 1), PANEL)
	_rect(image, Rect2i(0, 95, 96, 1), PANEL)
	return image

func _bracket() -> Image:
	var image := _canvas(16, 16)
	_rect(image, Rect2i(2, 2, 12, 2), IVORY)
	_rect(image, Rect2i(2, 2, 2, 12), IVORY)
	return image

func _life_outline() -> Image:
	var image := _canvas(24, 32)
	_chamfer_rect(image, Rect2i(4, 2, 16, 28), 3, STEEL)
	_chamfer_rect(image, Rect2i(4, 2, 15, 27), 3, IVORY)
	_chamfer_rect(image, Rect2i(6, 4, 11, 23), 1, TRANSPARENT)
	return image

func _life_fill() -> Image:
	var image := _canvas(24, 32)
	_chamfer_rect(image, Rect2i(7, 5, 10, 22), 1, CYAN)
	_rect(image, Rect2i(8, 5, 8, 1), ARMOR)
	_rect(image, Rect2i(7, 6, 1, 19), ARMOR)
	return image

func _energy_track() -> Image:
	var image := _canvas(32, 16)
	_chamfer_rect(image, Rect2i(0, 1, 32, 14), 1, INK)
	_rect(image, Rect2i(1, 2, 30, 1), STEEL_LIGHT)
	_rect(image, Rect2i(1, 13, 30, 1), STEEL)
	_rect(image, Rect2i(0, 3, 1, 10), STEEL)
	_rect(image, Rect2i(31, 3, 1, 10), STEEL)
	_rect(image, Rect2i(2, 4, 28, 8), PANEL)
	return image

func _energy_fill() -> Image:
	var image := _canvas(8, 8)
	image.fill(CYAN)
	_rect(image, Rect2i(0, 0, 8, 1), ARMOR)
	return image

func _energy_mask() -> Image:
	var image := _canvas(8, 8)
	_chamfer_rect(image, Rect2i(0, 0, 8, 8), 1, Color.WHITE)
	return image

func _clamp() -> Image:
	var image := _canvas(12, 24)
	_chamfer_rect(image, Rect2i(1, 1, 10, 22), 1, INK)
	_rect(image, Rect2i(3, 2, 6, 20), COPPER_DARK)
	_rect(image, Rect2i(3, 3, 4, 18), COPPER)
	_rect(image, Rect2i(3, 3, 1, 18), COPPER_LIGHT)
	_rect(image, Rect2i(7, 5, 2, 14), PANEL)
	_rect(image, Rect2i(3, 7, 4, 1), COPPER_DARK)
	_rect(image, Rect2i(3, 16, 4, 1), COPPER_DARK)
	return image

func _drawer_handle() -> Image:
	var image := _canvas(10, 32)
	_chamfer_rect(image, Rect2i(0, 0, 10, 32), 1, INK)
	_rect(image, Rect2i(1, 1, 8, 30), STEEL)
	_rect(image, Rect2i(2, 2, 6, 28), COPPER_DARK)
	_rect(image, Rect2i(2, 2, 5, 28), COPPER)
	_rect(image, Rect2i(2, 2, 1, 28), COPPER_LIGHT)
	_rect(image, Rect2i(4, 7, 2, 18), COPPER_DARK)
	_rect(image, Rect2i(4, 5, 2, 1), COPPER_LIGHT)
	_rect(image, Rect2i(4, 27, 2, 1), PANEL)
	return image

func _selection_row() -> Image:
	var image := _canvas(96, 96)
	image.fill(PANEL)
	_rect(image, Rect2i(0, 0, 96, 1), STEEL)
	_rect(image, Rect2i(0, 95, 96, 1), INK)
	return image

func _selection_tick() -> Image:
	var image := _canvas(4, 32)
	# 纯白使 modulate 的目标 RGB 不被烘焙色再次相乘。
	_chamfer_rect(image, Rect2i(0, 0, 4, 32), 1, Color.WHITE)
	return image

func _safe_icon() -> Image:
	var image := _canvas(32, 32)
	for y in range(32):
		for x in range(32):
			var distance := absi(2 * x - 31) + absi(2 * y - 31)
			if distance <= 26:
				image.set_pixel(x, y, INK if distance >= 23 else CYAN)
	return image

func _warning_icon() -> Image:
	var image := _canvas(32, 32)
	for y in range(3, 28):
		var half_width := (y - 3) / 2
		for x in range(16 - half_width, 16 + half_width + 1):
			image.set_pixel(x, y, WARN)
	_rect(image, Rect2i(15, 12, 3, 8), INK)
	_rect(image, Rect2i(15, 23, 3, 2), INK)
	return image

func _burst_icon() -> Image:
	var image := _canvas(32, 32)
	# 八个清楚的整数射线和中心块；小尺寸下仍区别于安全菱形。
	for y in range(4, 28):
		for x in range(4, 28):
			var dx := absi(x - 16)
			var dy := absi(y - 16)
			var core := dx + dy <= 9
			var axial_ray := (dx <= 2 and dy <= 13) or (dy <= 2 and dx <= 13)
			var diagonal_ray := absi(dx - dy) <= 1 and dx <= 10 and dy <= 10
			if core or axial_ray or diagonal_ray:
				image.set_pixel(x, y, BURST)
	return image

func _cooldown_icon() -> Image:
	var image := _canvas(32, 32)
	for y in range(32):
		for x in range(32):
			var dx := 2 * x - 31
			var dy := 2 * y - 31
			var radius_squared := dx * dx + dy * dy
			if radius_squared <= 625 and radius_squared >= 400:
				image.set_pixel(x, y, COOL)
	_rect(image, Rect2i(15, 8, 2, 9), COOL)
	_line(image, Vector2i(16, 16), Vector2i(22, 21), COOL)
	_line(image, Vector2i(15, 16), Vector2i(21, 21), COOL)
	return image

func _button_focus() -> Image:
	var image := _canvas(96, 96)
	for position: Vector2i in [Vector2i(0, 0), Vector2i(88, 0), Vector2i(0, 88), Vector2i(88, 88)]:
		var right := position.x > 0
		var bottom := position.y > 0
		_rect(image, Rect2i(position.x, position.y + (6 if bottom else 0), 8, 2), IVORY)
		_rect(image, Rect2i(position.x + (6 if right else 0), position.y, 2, 8), IVORY)
	return image

func _portrait_frame() -> Image:
	var image := _canvas(96, 96)
	_rect(image, Rect2i(1, 0, 94, 1), STEEL)
	_rect(image, Rect2i(1, 95, 94, 1), STEEL)
	_rect(image, Rect2i(0, 1, 1, 94), STEEL)
	_rect(image, Rect2i(95, 1, 1, 94), STEEL)
	return image

func _emit(filename: String, image: Image, margins: Array, layer: String, dynamic: String) -> void:
	var path := OUTPUT.path_join(filename)
	var save_result := image.save_png(ProjectSettings.globalize_path(path))
	if save_result != OK:
		_errors.append("PNG 保存失败：%s (%s)" % [path, save_result])
		return
	var alpha_opaque := 0
	var alpha_transparent := 0
	var alpha_other := 0
	for y in range(image.get_height()):
		for x in range(image.get_width()):
			var alpha := image.get_pixel(x, y).a8
			if alpha == 255:
				alpha_opaque += 1
			elif alpha == 0:
				alpha_transparent += 1
			else:
				alpha_other += 1
	if alpha_other > 0:
		_errors.append("静态 PNG 含非二值 Alpha：" + filename)
	_write_import(path)
	_entries.append({"id": filename.get_basename(), "file": path, "canvas": [image.get_width(), image.get_height()],
		"format": "RGBA8", "native_scale": 1, "nine_slice_margin_ltrb": margins,
		"layer": layer, "dynamic_responsibility": dynamic, "contains_text": false,
		"alpha": {"opaque_pixels": alpha_opaque, "transparent_pixels": alpha_transparent, "partial_pixels": alpha_other},
		"sha256": FileAccess.get_sha256(path)})

func _write_import(path: String) -> void:
	# Godot 4 的 nearest 由 CanvasItem.texture_filter 决定，不是旧版 importer 的 filter 开关。
	# 写明 lossless / no mipmaps / no alpha-border 补色，正式组件也必须显式使用 NEAREST。
	var imported_path := "res://.godot/imported/%s-%s.ctex" % [path.get_file(), path.md5_text()]
	# 重建时保留 UID，保证引用与导入配置也稳定，不只保证 PNG 字节稳定。
	var old_config := ConfigFile.new()
	var texture_uid := ""
	if old_config.load(path + ".import") == OK:
		texture_uid = str(old_config.get_value("remap", "uid", ""))
	if texture_uid.is_empty():
		texture_uid = ResourceUID.id_to_text(ResourceUID.create_id())
	var config := ConfigFile.new()
	config.set_value("remap", "importer", "texture")
	config.set_value("remap", "type", "CompressedTexture2D")
	config.set_value("remap", "uid", texture_uid)
	config.set_value("remap", "path", imported_path)
	config.set_value("remap", "metadata", {"vram_texture": false})
	config.set_value("deps", "source_file", path)
	config.set_value("deps", "dest_files", PackedStringArray([imported_path]))
	config.set_value("params", "compress/mode", 0)
	config.set_value("params", "compress/high_quality", false)
	config.set_value("params", "compress/lossy_quality", 0.7)
	config.set_value("params", "compress/hdr_compression", 1)
	config.set_value("params", "compress/normal_map", 0)
	config.set_value("params", "mipmaps/generate", false)
	config.set_value("params", "mipmaps/limit", -1)
	config.set_value("params", "process/fix_alpha_border", false)
	config.set_value("params", "process/premult_alpha", false)
	config.set_value("params", "process/size_limit", 0)
	config.set_value("params", "detect_3d/compress_to", 1)
	var import_error := config.save(path + ".import")
	if import_error != OK:
		_errors.append("导入配置保存失败：" + path)

func _write_inventory() -> void:
	var inventory := {"schema_version": 1, "collection": "ember_ui_edge_v001", "skin_direction": "A 边缘标记",
		"generator": "res://tools/build_ui_edge_skin_v001.gd", "production": "native Godot Image integer geometry; no screenshot edits",
		"palette": {"ink": "#101820", "panel": "#182631", "steel": "#4D6470", "steel_light": "#829BA3", "armor": "#BECBC4", "ivory": "#ECE9D8", "copper_dark": "#7B4D35", "copper": "#B77C4B", "copper_light": "#E2B77A", "cyan": "#51C5C2", "warning": "#E5A44B", "burst": "#E65B4A", "cooldown": "#566B78"},
		"technical_white": "#FFFFFF only for alpha mask and programmable state tint carrier",
		"import": {"compress_mode": "lossless", "mipmaps_generate": false, "fix_alpha_border": false,
			"nearest": "CanvasItem.TEXTURE_FILTER_NEAREST required by consuming Control nodes; no Godot 4 importer filter flag"},
		"coordinate_space": "screen pixels; do not apply world TileMapLayer scale 0.25",
		"nine_slice_order": "left, top, right, bottom",
		"layer_rules": ["文字/数字不进 PNG", "动态能量只裁填充层", "铜夹和框架在裁切层之外", "portrait 设备纹理不烘焙进框", "状态判定来自一个数据源", "opaque backplates 覆盖背景，透明 overlay 不承担遮挡"],
		"assets": _entries, "errors": Array(_errors)}
	var inventory_file := FileAccess.open(OUTPUT.path_join("inventory.json"), FileAccess.WRITE)
	if inventory_file == null:
		_errors.append("inventory.json 保存失败")
	else:
		inventory_file.store_string(JSON.stringify(inventory, "\t") + "\n")
