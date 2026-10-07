extends Control
## 抽屉是独立的世界遮盖面板；只有抽屉及按钮拦截指针，关闭时 hidden 并释放焦点。
## 本组件展示全局采集目标，不虚构站点储量，也不绑定 Game 单例。

signal closed

const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
const PROGRESS = preload("res://scripts/ember/ui_edge_v001/energy_progress.gd")
const ROW = preload("res://scripts/ember/ui_edge_v001/state_row.gd")
const BUTTON = preload("res://scripts/ember/ui_edge_v001/bracket_button.gd")
const PORTRAIT_PATH := "res://assets/ember/map_assets_v001/buildings/energy_station.png"

var station_name: String = "采能站 01"
var station_state: int = STATE.StationState.SAFE
var collecting: bool = true
var current: float = 145.0
var maximum: float = 380.0
var _content_clip: Control
var _plate: Panel
var _handle: TextureRect
var _title: Label
var _portrait: TextureRect
var _portrait_frame: Panel
var _goal_label: Label
var _goal_value: Label
var _progress
var _rows: Array = []
var _hint: Label
var _back: Button
var _header_corners: Array[TextureRect] = []
var _portrait_was_supplied: bool = false
var _station_portrait: Texture2D

func _enter_tree() -> void:
	# 跨视口挂接可能先改size再让本节点入树；同尺寸不会再次发resized。
	# 构建过的抽屉须在重入后重排内部节点，避免返回按钮留在旧画布底部。
	if _back != null:
		_layout.call_deferred()

func _ready() -> void:
	# 保留入树前close设置的交互状态，隐藏抽屉不能被_ready改回STOP。
	STYLE.prepare(self, visible)
	custom_minimum_size = Vector2(224, 480)
	# 只裁内容层：铜拉手仍挂在抽屉本体上，能露出抽屉左边。
	_content_clip = Control.new()
	_content_clip.name = "ContentClip"
	_content_clip.clip_contents = true
	STYLE.prepare(_content_clip)
	add_child(_content_clip)
	_plate = STYLE.panel(_content_clip, "panel_backplate_96")
	_handle = STYLE.texture(self, "drawer_handle_10x32")
	_title = STYLE.label(_content_clip, station_name, 24)
	_title.clip_text = true
	_title.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_header_corners = STYLE.corners(_content_clip)
	_portrait = STYLE.texture(_content_clip, "")
	if not _portrait_was_supplied:
		_station_portrait = load(PORTRAIT_PATH) as Texture2D
	_portrait.texture = _station_portrait
	_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_portrait_frame = STYLE.panel(_content_clip, "portrait_frame_96")
	_goal_label = STYLE.label(_content_clip, "采集目标", 16, STATE.MUTED_COLOR)
	_goal_value = STYLE.label(_content_clip, "", 26)
	_goal_value.clip_text = true
	_goal_value.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_progress = PROGRESS.new()
	_progress.show_labels = false
	_progress.show_clamps = false
	_content_clip.add_child(_progress)
	for state_value in range(4):
		var row := ROW.new()
		row.row_state = state_value
		_content_clip.add_child(row)
		_rows.append(row)
	_hint = STYLE.label(_content_clip, "", 20)
	_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_back = BUTTON.new()
	_back.text = "返回"
	_content_clip.add_child(_back)
	_back.pressed.connect(close)
	resized.connect(_layout)
	set_data({})

func set_data(data: Dictionary) -> void:
	station_name = str(data.get("station_name", station_name))
	station_state = STATE.normalize(int(data.get("station_state", station_state)))
	collecting = bool(data.get("collecting", collecting)) and STATE.can_collect(station_state)
	maximum = STATE.safe_value(float(data.get("energy_goal", maximum)))
	current = clampf(STATE.safe_value(float(data.get("energy", current))), 0, maximum)
	if _title == null:
		return
	_title.text = station_name
	_goal_value.text = "%s / %s" % [STATE.format_quantity(current), STATE.format_quantity(maximum)]
	_progress.set_data(current, maximum)
	for index in range(_rows.size()):
		_rows[index].set_data(index, index == station_state)
	if collecting:
		_hint.text = "停下采集 ·\n移动中断"
	elif STATE.can_collect(station_state):
		_hint.text = "站入采集区 ·\n停下开始采集"
	elif station_state == STATE.StationState.BURST:
		_hint.text = "危险爆发 ·\n离开危险区域"
	elif station_state == STATE.StationState.COOLDOWN:
		_hint.text = "设备冷却中 ·\n等待状态恢复"
	else:
		_hint.text = "未知状态 ·\n等待设备数据"
	_layout()

func open(grab_button_focus: bool = true) -> void:
	show()
	mouse_filter = Control.MOUSE_FILTER_STOP
	# 已构建抽屉也允许离树期间open；焦点留到真正入树后由HUD恢复。
	if _back != null and _back.is_inside_tree() and _back.is_visible_in_tree() and not _back.disabled and grab_button_focus:
		_back.grab_focus()

func close() -> void:
	# 已关闭是无操作；真实可见->隐藏才通知调用方，避免每帧重复 close 发信号。
	var was_visible := visible
	# 未入树/已移出树时没有 viewport；仍允许调用方提前设置关闭状态。
	# 入树后的关闭必须释放内部焦点，否则隐藏按钮仍可能收到确认键。
	if is_inside_tree():
		var focused := get_viewport().gui_get_focus_owner()
		if focused != null and (focused == self or is_ancestor_of(focused)):
			focused.release_focus()
	hide()
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if was_visible:
		closed.emit()

func get_back_button() -> Button:
	return _back

func set_station_portrait(portrait: Texture2D) -> void:
	# null 表示明确清空。切换到没有新肖像的站点时，不能残留上一台设备。
	_portrait_was_supplied = true
	_station_portrait = portrait
	if _portrait != null:
		_portrait.texture = portrait

func _layout() -> void:
	if _back == null:
		return
	_content_clip.size = size
	_plate.size = size
	_handle.position = Vector2(-10, roundf(size.y * 0.44))
	_handle.size = Vector2(10, 32)
	_title.position = Vector2(20, 18)
	_title.size = Vector2(size.x - 40, 40)
	var header_area := Vector2(size.x - 24, 48)
	STYLE.layout_corners(_header_corners, header_area)
	for corner in _header_corners:
		corner.position += Vector2(12, 12)
	var compact := size.y < 700
	var very_short := size.y < 540
	# 先为提示的真实两行高度、按钮、8px间隔和12px底边预留空间。
	# 不能仅靠clip隐藏溢出：540px高时肖像48px，返回按钮仍完整可见。
	var hint_font_size := 18 if very_short else 20
	_hint.add_theme_font_size_override("font_size", hint_font_size)
	var hint_height := 56.0 if very_short else 64.0
	var hint_gap := 8.0 if very_short else 12.0
	var value_offset := 80.0 if very_short else 88.0
	var row_height := 40.0 if compact else 48.0
	var button_y := maxf(0, size.y - 12 - 52)
	var portrait_budget := button_y - 8 - hint_height - hint_gap - (value_offset + 96 + row_height * 4)
	var portrait_height := clampf(floorf(portrait_budget), 0, 174)
	_portrait.position = Vector2(36, 78)
	_portrait.size = Vector2(size.x - 72, portrait_height)
	_portrait.visible = portrait_height >= 24
	_portrait_frame.position = Vector2(26, 74)
	_portrait_frame.size = Vector2(size.x - 52, portrait_height + 8)
	_portrait_frame.visible = portrait_height >= 24
	var value_y := value_offset + portrait_height
	_goal_label.position = Vector2(24, value_y)
	_goal_label.size = Vector2(size.x - 48, 24)
	_goal_value.position = Vector2(24, value_y + 22)
	_goal_value.size = Vector2(size.x - 48, 36)
	_progress.position = Vector2(20, value_y + 60)
	_progress.size = Vector2(size.x - 40, 24)
	var row_y := value_y + 96
	for index in range(_rows.size()):
		_rows[index].position = Vector2(20, row_y + index * row_height)
		_rows[index].size = Vector2(size.x - 40, row_height)
	_hint.position = Vector2(28, row_y + row_height * 4 + hint_gap)
	_hint.size = Vector2(size.x - 56, hint_height)
	_back.position = Vector2(28, button_y)
	_back.size = Vector2(size.x - 56, 52)
