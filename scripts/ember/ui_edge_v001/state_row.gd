extends Control
## 一行只展示一个状态；激活/停用由外部真实状态统一决定。

const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
@export var row_state: int = STATE.StationState.SAFE
var active: bool = false
var _backplate: Panel
var _tick: TextureRect
var _icon: TextureRect
var _label: Label

func _ready() -> void:
	STYLE.prepare(self)
	custom_minimum_size = Vector2(120, 40)
	_backplate = STYLE.panel(self, "selection_row_96")
	_tick = STYLE.texture(self, "selection_tick_4x32")
	_icon = STYLE.texture(self, "status_safe_32")
	_label = STYLE.label(self, "", 22)
	resized.connect(_layout)
	set_data(row_state, active)

func set_data(state_value: int, is_active: bool) -> void:
	row_state = STATE.normalize(state_value)
	active = is_active
	if _label == null:
		return
	var definition := STATE.definition(row_state)
	_icon.texture = STYLE.skin(str(definition["icon"]))
	_icon.modulate = Color.WHITE if active else Color(0.48, 0.48, 0.48, 1.0)
	_tick.modulate = definition["color"]
	_tick.visible = active
	_backplate.visible = active
	_label.text = str(definition["label"])
	_label.add_theme_color_override("font_color", definition["color"] if active else STATE.DIM_COLOR)
	_layout()
	queue_redraw()

func _layout() -> void:
	if _label == null:
		return
	_backplate.size = size
	_tick.position = Vector2(0, roundf((size.y - 32) / 2))
	_tick.size = Vector2(4, 32)
	_icon.position = Vector2(20, roundf((size.y - 32) / 2))
	_icon.size = Vector2(32, 32)
	_label.position = Vector2(72, 0)
	_label.size = Vector2(maxf(0, size.x - 80), size.y)
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER

func _draw() -> void:
	if not active:
		draw_line(Vector2(8, roundf(size.y) - 1), Vector2(roundf(size.x) - 8, roundf(size.y) - 1), STATE.STRUCTURE_COLOR, 1, false)
