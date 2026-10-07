extends Button
## 按钮文字、hover/pressed底层、focus透明角层互相独立，能单独替换。

const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
var _corners: Array[TextureRect] = []
var _focus_layer: Panel

func _enter_tree() -> void:
	# 重挂后外层按钮尺寸可能已变，焦点角层也须按新尺寸重排。
	if _focus_layer != null:
		_layout.call_deferred()
		_sync_focus.call_deferred()

func _ready() -> void:
	STYLE.prepare(self, true)
	focus_mode = Control.FOCUS_ALL
	custom_minimum_size = Vector2(160, 52)
	if text.is_empty():
		text = "返回"
	add_theme_font_override("font", STYLE.font())
	add_theme_font_size_override("font_size", 22)
	add_theme_color_override("font_color", STATE.TEXT_COLOR)
	add_theme_color_override("font_hover_color", STATE.TEXT_COLOR)
	add_theme_color_override("font_pressed_color", STATE.BRASS_COLOR)
	add_theme_color_override("font_disabled_color", STATE.DIM_COLOR)
	var idle := StyleBoxFlat.new()
	idle.bg_color = Color(0, 0, 0, 0)
	add_theme_stylebox_override("normal", idle)
	add_theme_stylebox_override("disabled", idle)
	add_theme_stylebox_override("hover", STYLE.box("selection_row_96", Color("182631")))
	var pressed_box := StyleBoxFlat.new()
	pressed_box.bg_color = Color("101820")
	pressed_box.border_color = STATE.BRASS_COLOR
	pressed_box.set_border_width_all(1)
	add_theme_stylebox_override("pressed", pressed_box)
	add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	_corners = STYLE.corners(self)
	_focus_layer = STYLE.panel(self, "button_focus_96")
	_focus_layer.name = "FocusOverlay"
	focus_entered.connect(_sync_focus)
	focus_exited.connect(_sync_focus)
	resized.connect(_layout)
	_layout()
	_sync_focus()

func _process(_delta: float) -> void:
	# Godot 4.7 的 disabled=true 不自动释放焦点，也不会触发 focus_exited。
	# 原生属性没有变化信号；下一帧清理焦点/角层，避免禁用按钮仍像可操作。
	if disabled:
		if has_focus():
			release_focus()
		if _focus_layer != null and _focus_layer.visible:
			_sync_focus()

func _layout() -> void:
	STYLE.layout_corners(_corners, size)
	if _focus_layer != null:
		_focus_layer.size = size

func _sync_focus() -> void:
	if _focus_layer != null:
		_focus_layer.visible = has_focus() and not disabled
