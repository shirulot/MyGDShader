extends RefCounted
## A「边缘标记」的共享工厂。静态皮肤与动态文本/布局分开。
## 皮肤缺失时保留简单后备绘制，便于独立审阅脚本和后续替换素材。

const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
const ASSET_ROOT := "res://assets/ember/ui_final/skins/"
static var _font: SystemFont

static func font() -> Font:
	if _font == null:
		_font = SystemFont.new()
		_font.font_names = PackedStringArray(["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"])
		_font.font_weight = 700
		_font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	return _font

static func skin(identifier: String) -> Texture2D:
	var path := ASSET_ROOT + identifier + ".png"
	return load(path) as Texture2D if ResourceLoader.exists(path) else null

static func prepare(control: Control, interactive: bool = false) -> void:
	control.mouse_filter = Control.MOUSE_FILTER_STOP if interactive else Control.MOUSE_FILTER_IGNORE
	control.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

static func label(parent: Control, text: String, font_size: int = 20, color: Color = STATE.TEXT_COLOR) -> Label:
	var node := Label.new()
	node.text = text
	node.add_theme_font_override("font", font())
	node.add_theme_font_size_override("font_size", font_size)
	node.add_theme_color_override("font_color", color)
	prepare(node)
	parent.add_child(node)
	return node

static func add_world_text_outline(node: Label) -> void:
	# HUD裸露文字覆盖地图时，描边保持高频水纹和地板上的可读性。
	# 面板正文不套描边，避免所有文字都显得过重。
	node.add_theme_constant_override("outline_size", 2)
	node.add_theme_color_override("font_outline_color", Color("101820"))

static func texture(parent: Control, identifier: String) -> TextureRect:
	var node := TextureRect.new()
	node.texture = skin(identifier)
	node.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	node.stretch_mode = TextureRect.STRETCH_SCALE
	prepare(node)
	parent.add_child(node)
	return node

static func box(identifier: String, fallback_color: Color = Color("101820"), margin: int = 8) -> StyleBox:
	var image := skin(identifier)
	if image != null:
		var textured := StyleBoxTexture.new()
		textured.texture = image
		for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
			textured.set_texture_margin(side, margin)
		if identifier == "energy_track_32x16":
			# 轨道高度仅16px；上下8px会吃光中心，按资产合同保留4px。
			textured.set_texture_margin(SIDE_TOP, 4)
			textured.set_texture_margin(SIDE_BOTTOM, 4)
		elif identifier == "selection_tick_4x32":
			textured.set_texture_margin(SIDE_LEFT, 1)
			textured.set_texture_margin(SIDE_RIGHT, 1)
			textured.set_texture_margin(SIDE_TOP, 2)
			textured.set_texture_margin(SIDE_BOTTOM, 2)
		return textured
	var plain := StyleBoxFlat.new()
	plain.bg_color = fallback_color
	plain.border_color = STATE.STRUCTURE_COLOR
	plain.set_border_width_all(1)
	return plain

static func panel(parent: Control, identifier: String = "panel_backplate_96") -> Panel:
	var node := Panel.new()
	node.add_theme_stylebox_override("panel", box(identifier))
	prepare(node)
	parent.add_child(node)
	return node

static func corners(parent: Control) -> Array[TextureRect]:
	var result: Array[TextureRect] = []
	for index in range(4):
		var corner := texture(parent, "bracket_corner_16")
		corner.size = Vector2(16, 16)
		corner.flip_h = index == 1 or index == 3
		corner.flip_v = index >= 2
		result.append(corner)
	return result

static func layout_corners(corners_list: Array[TextureRect], area: Vector2) -> void:
	if corners_list.size() != 4:
		return
	corners_list[0].position = Vector2.ZERO
	corners_list[1].position = Vector2(roundf(area.x) - 16, 0)
	corners_list[2].position = Vector2(0, roundf(area.y) - 16)
	corners_list[3].position = Vector2(roundf(area.x) - 16, roundf(area.y) - 16)
