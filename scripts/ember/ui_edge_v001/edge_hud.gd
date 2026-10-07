extends Control
## 数据驱动 HUD：调用方传入真实玩法数据，本节点不读取/改写 Game。
## 建议作为 CanvasLayer 子节点实例化；屏幕尺度与世界瓦片缩放无关。

signal drawer_closed

const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
const LIFE = preload("res://scripts/ember/ui_edge_v001/life_indicator.gd")
const TIMER = preload("res://scripts/ember/ui_edge_v001/timer_badge.gd")
const PROGRESS = preload("res://scripts/ember/ui_edge_v001/energy_progress.gd")
const MARKER = preload("res://scripts/ember/ui_edge_v001/station_marker.gd")
const DRAWER = preload("res://scripts/ember/ui_edge_v001/station_drawer.gd")

@export_range(16, 80, 1) var safe_margin: int = 36:
	set(value):
		safe_margin = clampi(value, 16, 80)
		_layout()
@export_range(224, 320, 1) var drawer_width: int = 248:
	set(value):
		drawer_width = clampi(value, 224, 320)
		_layout()
var _data: Dictionary = {
	"life": 2, "max_life": 3, "energy": 145.0, "energy_goal": 380.0,
	"seconds": 78.0, "station_state": STATE.StationState.SAFE,
	"collecting": true, "station_name": "采能站 01",
}
var _life
var _timer
var _energy
var _marker
var _drawer
var _built: bool = false
var _drawer_open: bool = false
var _marker_requested: bool = false
var _marker_source_position: Vector2 = Vector2.ZERO
var _world_rect := Rect2()
var _portrait_was_supplied: bool = false
var _station_portrait: Texture2D

func _enter_tree() -> void:
	# 缓存HUD重新挂接时不会再次_ready。待子节点入树、锚点更新后恢复布局，
	# 不重建组件；执行时读取最新状态，避免离树期间的关闭被旧回调覆盖。
	if _built:
		_restore_after_reentry.call_deferred()

func _restore_after_reentry() -> void:
	if is_inside_tree() and _built:
		set_drawer_open(_drawer_open)

func _ready() -> void:
	STYLE.prepare(self)
	_life = LIFE.new()
	_life.name = "LifeIndicator"
	add_child(_life)
	_timer = TIMER.new()
	_timer.name = "TimerBadge"
	add_child(_timer)
	_energy = PROGRESS.new()
	_energy.name = "EnergyProgress"
	add_child(_energy)
	_marker = MARKER.new()
	_marker.name = "StationMarker"
	add_child(_marker)
	_drawer = DRAWER.new()
	_drawer.name = "StationDrawer"
	add_child(_drawer)
	if _portrait_was_supplied:
		_drawer.set_station_portrait(_station_portrait)
	_drawer.closed.connect(_on_drawer_closed)
	_built = true
	resized.connect(_layout)
	_apply_data()
	set_drawer_open(_drawer_open)

func set_game_state(data: Dictionary) -> void:
	# 支持部分更新；未知键忽略，避免演示数据无意污染组件契约。
	for key in _data.keys():
		if data.has(key):
			_data[key] = data[key]
	_data["max_life"] = maxi(0, int(_data["max_life"]))
	_data["life"] = clampi(int(_data["life"]), 0, int(_data["max_life"]))
	_data["energy_goal"] = STATE.safe_value(float(_data["energy_goal"]))
	_data["energy"] = clampf(STATE.safe_value(float(_data["energy"])), 0.0, float(_data["energy_goal"]))
	_data["seconds"] = STATE.safe_value(float(_data["seconds"]))
	_data["station_state"] = STATE.normalize(int(_data["station_state"]))
	_data["collecting"] = bool(_data["collecting"]) and STATE.can_collect(int(_data["station_state"]))
	if _built:
		_apply_data()

func set_data(data: Dictionary) -> void:
	set_game_state(data)

func get_game_state() -> Dictionary:
	return _data.duplicate(true)

func set_station_state(state_value: int, is_collecting: bool = false) -> void:
	set_game_state({"station_state": state_value, "collecting": is_collecting})

func set_marker_screen_position(screen_position: Vector2, should_show: bool = true) -> void:
	# 保留未裁切的源坐标：关闭抽屉或 resize 后才能正确恢复标记。
	var valid_position := is_finite(screen_position.x) and is_finite(screen_position.y)
	_marker_source_position = screen_position.round() if valid_position else Vector2.ZERO
	_marker_requested = should_show and valid_position
	if _built:
		_update_marker_visibility()

func open_drawer() -> void:
	set_drawer_open(true)

func close_drawer() -> void:
	if _built:
		_drawer.close()
	else:
		_drawer_open = false

func set_drawer_open(should_open: bool) -> void:
	_drawer_open = should_open
	if not _built:
		return
	if should_open:
		_drawer.open()
	else:
		# 初次闭合无需发出 closed 信号；只负责层和交互设置。
		# 已构建HUD也可能被remove_child暂存：离树没有viewport，但仍须隐藏抽屉。
		if is_inside_tree():
			var focused := get_viewport().gui_get_focus_owner()
			if focused != null and _drawer.is_ancestor_of(focused):
				focused.release_focus()
		_drawer.hide()
		_drawer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layout()

func is_drawer_open() -> bool:
	return _drawer_open

func get_available_world_rect() -> Rect2:
	return _world_rect

func get_energy_progress() -> Control:
	return _energy

func get_drawer() -> Control:
	return _drawer

func get_marker() -> Control:
	return _marker

func set_station_portrait(portrait: Texture2D) -> void:
	_portrait_was_supplied = true
	_station_portrait = portrait
	if _built:
		_drawer.set_station_portrait(portrait)

func _apply_data() -> void:
	_life.set_data(int(_data["life"]), int(_data["max_life"]))
	_timer.set_data(float(_data["seconds"]))
	_energy.set_data(float(_data["energy"]), float(_data["energy_goal"]))
	_marker.set_data(int(_data["station_state"]), bool(_data["collecting"]))
	_drawer.set_data(_data)
	_layout()

func _layout() -> void:
	if not _built:
		return
	var view_size := size.round()
	# 窄视口也必须为抽屉保留实际224px最小宽，不能按136px排位却画224px。
	# 世界不足224px时暂藏现场HUD，优先完整显示终端；正常720布局保持原样。
	var drawer_limit := minf(view_size.x, maxf(224, view_size.x - 224))
	var used_drawer_width := minf(float(drawer_width), drawer_limit) if _drawer_open else 0.0
	var world_width := maxf(0, view_size.x - used_drawer_width)
	_world_rect = Rect2(Vector2.ZERO, Vector2(world_width, view_size.y))
	var margin := minf(float(safe_margin), minf(world_width, view_size.y) * 0.1)
	margin = floorf(margin)
	_life.position = Vector2(margin, margin)
	_timer.size = Vector2(124, 78)
	_timer.position = Vector2(maxf(margin, world_width - margin - 124), margin)
	var stacked_header := world_width < 300
	if stacked_header:
		_timer.position.y += 110
	_energy.position = Vector2(margin, maxf(margin, view_size.y - margin - 64))
	_energy.size = Vector2(maxf(96, world_width - margin * 2), 64)
	# 横向生命条与右侧时钟分栏；空间不足折叠格数，数字仍准确。
	var life_width_budget: float = world_width - margin * 2 if stacked_header else _timer.position.x - 16 - margin
	var slot_budget := clampi(int(floorf((life_width_budget + 8) / 32)), 0, 6)
	_life.set_slot_budget(slot_budget)
	_life.size = _life.custom_minimum_size
	var show_world_hud := world_width >= 224
	_life.visible = show_world_hud
	_timer.visible = show_world_hud
	_energy.visible = show_world_hud
	_drawer.position = Vector2(view_size.x - used_drawer_width, 0)
	_drawer.size = Vector2(float(drawer_width) if not _drawer_open else used_drawer_width, view_size.y)
	_marker.size = Vector2(136, 40)
	_update_marker_visibility()

func _update_marker_visibility() -> void:
	if not _built:
		return
	_marker.position = _marker_source_position
	var marker_bounds := Rect2(_marker_source_position, _marker.size)
	# 整个标记须留在可见世界区域，避免只露半行字或遮在抽屉下。
	_marker.visible = _marker_requested and int(_data["station_state"]) != STATE.UNKNOWN_STATE and _world_rect.encloses(marker_bounds)

func _on_drawer_closed() -> void:
	_drawer_open = false
	_layout()
	drawer_closed.emit()
