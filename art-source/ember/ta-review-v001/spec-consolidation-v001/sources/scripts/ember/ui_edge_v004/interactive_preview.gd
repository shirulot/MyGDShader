extends "res://scripts/ember/ui_edge_preview_v001.gd"
## UI专项可交互场景，复用真实地图与旧预览数据源。未替换M0教学主场景。
## 宿主明确执行窗口暂停契约：详情/菜单/结果打开时，演示计时与采集停止。
const FLOW = preload("res://scenes/ember/ui_edge_v004/interaction_ui.tscn")
@export var use_saved_preferences := true
var ui: Control
var live_simulation := false

func _ready() -> void:
	super._ready()
	# 在同一CanvasLayer内替换独立HUD为包含HUD和窗口的完整入口。
	hud.free()
	ui = FLOW.instantiate()
	if not use_saved_preferences:
		ui.settings_path = ""
	get_node("UILayer").add_child(ui)
	hud = ui.hud
	ui.restart_requested.connect(reset_session)
	ui.session_requested.connect(reset_session)
	ui.title_requested.connect(func(): live_simulation = false)
	ui.hud.drawer_closed.connect(ui._layout)
	_refresh_data()

func _refresh_data() -> void:
	if not is_instance_valid(ui):
		super._refresh_data()
		return
	ui.set_game_state({"life":current_life,"max_life":3,"energy":current_energy,
		"energy_goal":380.0,"seconds":current_seconds,"station_state":current_state,
		"collecting":collecting_enabled and STATE.can_collect(current_state),"station_name":"采能站 01"})

func _process(delta: float) -> void:
	if not is_instance_valid(ui):
		return
	advance_simulation(delta)
	var camera := world.get_node("Camera2D") as Camera2D
	camera.position = Vector2(686 if hud.is_drawer_open() else 600, 236)
	super._process(delta)
	var point: Vector2 = selected_station.get_global_transform_with_canvas().origin
	ui.set_station_screen_rect(Rect2(point + Vector2(-66, -218), Vector2(124, 44)))
	if not bool(ui.preferences.show_markers):
		hud.set_marker_screen_position(Vector2.ZERO, false)

func advance_simulation(delta: float) -> void:
	if not live_simulation or ui.is_blocking():
		return
	current_seconds = maxf(0, current_seconds - delta)
	if collecting_enabled and STATE.can_collect(current_state):
		current_energy = minf(380, current_energy + delta * 3)
	_refresh_data()
	_check_result()

func reset_session() -> void:
	hud.set_drawer_open(false)
	current_life = 3
	current_energy = 0
	current_seconds = 180
	current_state = 0
	collecting_enabled = true
	live_simulation = true
	_refresh_data()

func _check_result() -> void:
	if current_energy >= 380:
		live_simulation = false
		ui.show_result(true)
	elif current_life <= 0 or current_seconds <= 0:
		live_simulation = false
		ui.show_result(false)

func _unhandled_key_input(event: InputEvent) -> void:
	if not is_instance_valid(ui) or ui.is_blocking():
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_TAB:
			ui.open_details()
			get_viewport().set_input_as_handled()
			return
		# Esc由窗口路由处理；旧预览的Esc只有关闭抽屉，不能吞掉菜单入口。
		if event.keycode == KEY_ESCAPE:
			return
		super._unhandled_key_input(event)
		_check_result()
