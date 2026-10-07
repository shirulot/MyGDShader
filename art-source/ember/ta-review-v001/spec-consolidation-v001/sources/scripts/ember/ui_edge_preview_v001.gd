extends Node2D
## 实际 Godot 组件拼装预览：背景是现有 TileMap 场景实例，不是生图截图。
## 这里只注入演示数据。数字键/空格等仅控制此预览，不修改项目输入表或 M0。
const HUD_SCENE := "res://scenes/ember/ui_edge_v001/components/edge_hud.tscn"
const MAP_SCENE := "res://scenes/ember/map_assets_tidal_port_v001.tscn"
const STATE := preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")

var hud: Control
var world: Node2D
var selected_station: Node2D
var current_state: int = 0
var current_life: int = 2
var current_energy: float = 145.0
var current_seconds: float = 78.0
var collecting_enabled: bool = true


func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	world = (load(MAP_SCENE) as PackedScene).instantiate()
	# 当前地图包含已通过生产验证的外部 TileMap 缓存；演示实例不需要编辑刷器脚本。
	world.set_script(null)
	world.name = "World"
	add_child(world)
	var camera := world.get_node("Camera2D") as Camera2D
	camera.position = Vector2(600, 236)
	camera.zoom = Vector2(2, 2)
	var robot := world.get_node("Props/ExistingRobot") as Sprite2D
	robot.position = Vector2(659, 290)
	selected_station = world.get_node("Props/EnergyStation0") as Node2D
	var layer := CanvasLayer.new()
	layer.name = "UILayer"
	layer.layer = 20
	add_child(layer)
	hud = (load(HUD_SCENE) as PackedScene).instantiate()
	layer.add_child(hud)
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	apply_example(0, false, 2, 145, 78, true)


func apply_example(state: int, drawer_open: bool, life: int = 2, energy: float = 145.0,
		seconds: float = 78.0, collecting: bool = true) -> void:
	current_state = STATE.normalize(state)
	current_life = life
	current_energy = energy
	current_seconds = seconds
	collecting_enabled = collecting
	_refresh_data()
	hud.call("set_drawer_open", drawer_open)


func _refresh_data() -> void:
	if not is_instance_valid(hud):
		return
	hud.call("set_game_state", {
		"life": current_life, "max_life": 3, "energy": current_energy, "energy_goal": 380.0,
		"seconds": current_seconds, "station_state": current_state,
		"collecting": collecting_enabled and STATE.can_collect(current_state),
		"station_name": "采能站 01"
	})


func _process(_delta: float) -> void:
	if is_instance_valid(hud) and is_instance_valid(selected_station):
		var point: Vector2 = selected_station.get_global_transform_with_canvas().origin
		point += Vector2(34, -98)
		hud.call("set_marker_screen_position", point.round(), collecting_enabled)


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	var key := event as InputEventKey
	match key.keycode:
		KEY_TAB:
			hud.call("set_drawer_open", not bool(hud.call("is_drawer_open")))
		KEY_ESCAPE:
			hud.call("close_drawer")
		KEY_1, KEY_2, KEY_3, KEY_4:
			current_state = int(key.keycode - KEY_1)
			_refresh_data()
		KEY_H:
			current_life = (current_life + 1) % 4
			_refresh_data()
		KEY_G:
			current_energy = fmod(current_energy + 95, 475)
			_refresh_data()
		KEY_T:
			current_seconds = 0 if current_seconds > 0 else 78
			_refresh_data()
		KEY_SPACE:
			collecting_enabled = not collecting_enabled
			_refresh_data()
		_:
			return
	get_viewport().set_input_as_handled()
