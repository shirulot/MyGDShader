extends Control
## 层级关键：轨道、FillClip、端帽是兄弟节点；裁切只影响 FillClip 的子节点。
## 填充宽度 round 到整数像素；零目标不会除零，也不会出现满条假象。

const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
@export var show_labels: bool = true:
	set(value):
		show_labels = value
		# 属性可在入树前或运行中切换；最小高度与真实标签布局一起同步。
		custom_minimum_size = Vector2(96, 64 if show_labels else 24)
		_layout()
@export var show_clamps: bool = true:
	set(value):
		show_clamps = value
		# _layout 内有构建检查，未入树时安全；已构建后不依赖 resize 才更新。
		_layout()
var current: float = 145.0
var maximum: float = 380.0
var ratio: float = 0.0
var fill_pixels: int = 0
var _value: Label
var _percent: Label
var _value_plate: Panel
var _track: Panel
var _fill_clip: Control
var _fill: TextureRect
var _left_clamp: TextureRect
var _right_clamp: TextureRect

func _enter_tree() -> void:
	# 重挂时父HUD可能已更新尺寸；重排真实轨道和FillClip，不能只看外层矩形。
	if _track != null:
		_layout.call_deferred()

func _ready() -> void:
	STYLE.prepare(self)
	custom_minimum_size = Vector2(96, 64 if show_labels else 24)
	_value_plate = STYLE.panel(self, "text_backplate_96")
	_value = STYLE.label(self, "", 26)
	_value.clip_text = true
	_value.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_percent = STYLE.label(self, "", 20)
	_percent.clip_text = true
	STYLE.add_world_text_outline(_value)
	STYLE.add_world_text_outline(_percent)
	_track = STYLE.panel(self, "energy_track_32x16")
	_fill_clip = Control.new()
	_fill_clip.name = "FillClip"
	_fill_clip.clip_contents = true
	STYLE.prepare(_fill_clip)
	add_child(_fill_clip)
	_fill = STYLE.texture(_fill_clip, "energy_fill_8x8")
	_fill.name = "FillTexture"
	_fill.stretch_mode = TextureRect.STRETCH_TILE
	_left_clamp = STYLE.texture(self, "copper_clamp_12x24")
	_right_clamp = STYLE.texture(self, "copper_clamp_12x24")
	_right_clamp.flip_h = true
	resized.connect(_layout)
	set_data(current, maximum)

func set_data(value: float, goal: float) -> void:
	maximum = STATE.safe_value(goal)
	current = clampf(STATE.safe_value(value), 0.0, maximum)
	ratio = STATE.safe_ratio(current, maximum)
	if _value != null:
		_value.text = "%s / %s" % [STATE.format_quantity(current), STATE.format_quantity(maximum)]
		_percent.text = "%d%%" % int(floorf(ratio * 100.0))
		_layout()

func get_fill_pixels() -> int:
	return fill_pixels

func get_fill_clip() -> Control:
	return _fill_clip

func _layout() -> void:
	if _track == null:
		return
	var track_y := 42.0 if show_labels else 4.0
	var width := maxi(0, int(roundf(size.x)) - 16)
	_value.visible = show_labels
	_percent.visible = show_labels
	_value_plate.visible = show_labels
	_value_plate.position = Vector2(6, 0)
	_value_plate.size = Vector2(minf(maxf(0, size.x - 74), 180), 34)
	_value.position = Vector2(14, 0)
	# 数字与右侧百分比各有独立宽度；预留8px给字形/描边，长数值走现有省略号。
	_value.size = Vector2(maxf(0, size.x - 86), 36)
	_percent.position = Vector2(maxf(0, size.x - 64), 4)
	_percent.size = Vector2(56, 30)
	_percent.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_track.position = Vector2(8, track_y)
	_track.size = Vector2(width, 16)
	# 合同内区从轨道(2,4)开始；铜夹始终在该裁切节点外。
	var interior_width := maxi(0, width - 4)
	fill_pixels = int(roundf(interior_width * ratio))
	_fill_clip.position = Vector2(10, track_y + 4)
	_fill_clip.size = Vector2(fill_pixels, 8)
	_fill_clip.visible = fill_pixels > 0
	_fill.size = Vector2(interior_width, 8)
	_left_clamp.visible = show_clamps
	_right_clamp.visible = show_clamps
	_left_clamp.position = Vector2(2, track_y - 4)
	_right_clamp.position = Vector2(maxf(2, size.x - 14), track_y - 4)
	_left_clamp.size = Vector2(12, 24)
	_right_clamp.size = Vector2(12, 24)
