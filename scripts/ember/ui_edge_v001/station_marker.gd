extends Control
## 世界标记只接收屏幕坐标；转换/遮挡由 HUD 或调用方承担，不侵入站点玩法。

const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
var station_state: int = STATE.StationState.SAFE
var collecting: bool = true
var _plate: Panel
var _icon: TextureRect
var _label: Label

func _ready() -> void:
	STYLE.prepare(self)
	custom_minimum_size = Vector2(136, 40)
	_plate = STYLE.panel(self, "text_backplate_96")
	_icon = STYLE.texture(self, "status_safe_32")
	_label = STYLE.label(self, "", 20)
	resized.connect(_layout)
	set_data(station_state, collecting)

func set_data(state_value: int, is_collecting: bool) -> void:
	station_state = STATE.normalize(state_value)
	collecting = is_collecting and STATE.can_collect(station_state)
	if _label == null:
		return
	var definition := STATE.definition(station_state)
	_icon.texture = STYLE.skin(str(definition["icon"]))
	_label.text = "采集中" if collecting else ("可采集" if station_state == STATE.StationState.SAFE else str(definition["marker"]))
	_label.add_theme_color_override("font_color", definition["color"])
	_layout()

func _layout() -> void:
	if _label == null:
		return
	_plate.size = size
	_icon.position = Vector2(4, 4)
	_icon.size = Vector2(32, 32)
	_label.position = Vector2(42, 0)
	_label.size = Vector2(maxf(0, size.x - 48), size.y)
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
