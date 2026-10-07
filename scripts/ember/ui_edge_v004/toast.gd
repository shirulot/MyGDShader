extends Control
## 非阻断提示：不会抢焦点、不截获鼠标，重复消息刷新显示时长。
const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
var _plate: Panel
var _label: Label
var _remaining := 0.0

func _ready() -> void:
	STYLE.prepare(self)
	_plate = STYLE.panel(self)
	_label = STYLE.label(self, "", 18)
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	resized.connect(_layout)
	hide()

func notify(message: String, duration: float = 3.0) -> void:
	_label.text = message
	_remaining = maxf(0.1, duration)
	show()
	_layout()

func _process(delta: float) -> void:
	if not visible:
		return
	_remaining -= delta
	if _remaining <= 0:
		hide()

func _layout() -> void:
	if _plate == null:
		return
	_plate.size = size
	_label.position = Vector2(16, 12)
	_label.size = size - Vector2(32, 24)
