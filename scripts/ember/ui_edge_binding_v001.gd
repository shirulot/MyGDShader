extends Node
## A 稿 UI 的可选只读适配器。添加到自己的游戏场景后显式 bind_sources 即可。
## 组件不负责递减倒计时，也不改变站点、玩家输入、胜利阈值或暂停状态。
## 所有场景/数据源都显式传入，避免依赖当前工程尚不存在的选站系统。

@export var energy_goal: float = 380.0
@export_range(0, 9999, 1) var max_life: int = 3
@export var station_title: String = "采能站 01"
@export var marker_offset := Vector2(30, -52)
@export var station_portrait: Texture2D = preload("res://assets/ember/map_assets_v001/buildings/energy_station.png"):
	set(value):
		station_portrait = value
		_portrait_bound = false

var _hud: Control
var _game_source: Node
var _station_source: Node
var _last_snapshot: Dictionary = {}
var _portrait_bound: bool = false


func bind_sources(hud: Control, game_source: Node, station_source: Node = null) -> void:
	_hud = hud
	_game_source = game_source
	_station_source = station_source
	_portrait_bound = false
	_last_snapshot.clear()
	refresh()


func select_station(station_source: Node, title: String = "采能站 01", portrait: Texture2D = null) -> void:
	_station_source = station_source
	station_title = title
	station_portrait = portrait if portrait != null else preload("res://assets/ember/map_assets_v001/buildings/energy_station.png")
	_portrait_bound = false
	_last_snapshot.clear()
	refresh()


func _process(_delta: float) -> void:
	refresh()


## 与 energy_station.gd 的实际采能条件一致，预警阶段仍然允许采集。
## 不单独使用 isGetPoint 缓存：游戏结束时缓存可能保留上一帧的 true。
static func should_show_collecting(active: bool, in_energy_area: bool, still: bool, state: int) -> bool:
	return active and in_energy_area and still and state in [0, 1]


func refresh() -> void:
	if not is_instance_valid(_hud):
		return
	if not is_instance_valid(_game_source):
		_hud.call("set_station_portrait", null)
		_portrait_bound = false
		_hud.call("set_station_state", -1, false)
		_hud.call("set_marker_screen_position", Vector2.ZERO, false)
		_hud.call("close_drawer")
		return
	var active: bool = bool(_read(_game_source, "isGameStarting", false))
	var has_station: bool = is_instance_valid(_station_source)
	if has_station and not _portrait_bound:
		_hud.call("set_station_portrait", station_portrait)
		_portrait_bound = true
	var state: int = int(_read(_station_source, "enrgyState", -1)) if has_station else -1
	var player_value: Variant = _read(_station_source, "player", null) if has_station else null
	# 已释放的 Object 不能再强制转换；站点离开/销毁的同帧也安全隐藏标记。
	var player: CharacterBody2D = (player_value as CharacterBody2D) if is_instance_valid(player_value) else null
	var in_range: bool = is_instance_valid(player)
	var still: bool = player.velocity.is_zero_approx() if in_range else false
	var collecting: bool = should_show_collecting(active, in_range, still, state)
	var snapshot: Dictionary = {
		"life": int(_read(_game_source, "lifePoint", 0)), "max_life": maxi(0, max_life),
		"energy": float(_read(_game_source, "energyPoint", 0.0)),
		"energy_goal": energy_goal, "seconds": float(_read(_game_source, "countdown", 0)),
		"station_state": state, "collecting": collecting,
		"station_name": station_title if has_station else "未连接设备"
	}
	if snapshot != _last_snapshot:
		_hud.call("set_game_state", snapshot)
		_last_snapshot = snapshot
	if not has_station:
		_hud.call("set_station_portrait", null)
		_portrait_bound = false
		_hud.call("close_drawer")
		_hud.call("set_marker_screen_position", Vector2.ZERO, false)
		return
	# get_global_transform_with_canvas 包含 Camera2D 的平移/缩放；转回 HUD 本地空间。
	# marker 是屏幕 UI，不能再沿用世界地板 0.25 的缩放。
	if _station_source is Node2D and _station_source.is_inside_tree() and _hud.is_inside_tree() and _station_source.get_viewport() == _hud.get_viewport():
		var screen_position: Vector2 = (_station_source as Node2D).get_global_transform_with_canvas().origin
		var hud_position: Vector2 = _hud.get_global_transform_with_canvas().affine_inverse() * screen_position
		_hud.call("set_marker_screen_position", (hud_position + marker_offset).round(), collecting)
	else:
		# 普通Node、暂时离树或不同Viewport均不能直接投影；不能留下旧屏幕标记。
		_hud.call("set_marker_screen_position", Vector2.ZERO, false)


func _read(source: Object, property_name: String, fallback: Variant) -> Variant:
	if not is_instance_valid(source):
		return fallback
	for property_info: Dictionary in source.get_property_list():
		if String(property_info.name) == property_name:
			return source.get(property_name)
	return fallback
