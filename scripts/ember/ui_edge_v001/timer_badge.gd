extends Control
## 时间正文由 Label 负责；四角是独立透明角件，禁止将时间烘焙入底图。

const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
# 保留有限浮点秒数；巨大输入不能未经范围判断直接转int64。
var seconds: float = 78.0
var _title: Label
var _value: Label
var _backplate: Panel
var _corners: Array[TextureRect] = []

func _ready() -> void:
	STYLE.prepare(self)
	custom_minimum_size = Vector2(124, 78)
	_backplate = STYLE.panel(self, "text_backplate_96")
	_title = STYLE.label(self, "时间", 18)
	_value = STYLE.label(self, "", 28)
	_value.clip_text = true
	_value.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_corners = STYLE.corners(self)
	resized.connect(_layout)
	_layout()
	set_data(seconds)

func set_data(remaining_seconds: float) -> void:
	seconds = ceilf(STATE.safe_value(remaining_seconds))
	if _value != null:
		_value.text = _format_time(seconds)
		_layout()

func _format_time(value: float) -> String:
	# 原稿的正常游戏倒计时保持MM:SS；只有已知小范围才转整数。
	if value < 6000.0:
		var small_seconds := int(value)
		return "%02d:%02d" % [small_seconds / 60, small_seconds % 60]
	if value < 360000.0:
		var small_seconds := int(value)
		return "%02dh%02d" % [small_seconds / 3600, (small_seconds / 60) % 60]
	# 长时间改为天数，巨大有限数使用短科学记数，避免正文撑破角框。
	var days := value / 86400.0
	return (str(int(days)) if days < 10000.0 else STATE.format_scientific(days, 1)) + "d"

func _layout() -> void:
	if _value == null:
		return
	_backplate.position = Vector2(6, 24)
	_backplate.size = Vector2(maxf(0, size.x - 12), maxf(0, size.y - 24))
	_title.position = Vector2(24, 0)
	_value.position = Vector2(16, 28)
	var available_width := maxf(0, size.x - 32)
	# 按实际字体测量，短MM:SS继续用28px；长格式最低缩到16px后由裁切兜底。
	var font_size := 28
	var value_font := _value.get_theme_font("font")
	while font_size > 16 and value_font.get_string_size(_value.text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x > available_width:
		font_size -= 1
	_value.add_theme_font_size_override("font_size", font_size)
	_value.size = Vector2(available_width, 42)
	_value.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	STYLE.layout_corners(_corners, size)
