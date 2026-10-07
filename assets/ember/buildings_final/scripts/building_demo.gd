extends Node2D
## 独立审阅场景：已有连续地板 + 三栋正式注册建筑 + 原机器人。
## 不改变主工程输入或课程 Autoload，所有快捷键仅属于这个示例。

const FLOOR_TEXTURE := "res://assets/ember/map_assets_v001/floors/floor_steel_period_v001.png"
const SAVE_PATH := "user://building_assets_demo_v004r1.json"
const BUILDING_IDS := ["control_tower", "repair_workshop", "logistics_warehouse"]

var buildings: Array[Node2D] = []
var actor: CharacterBody2D
var world: Node2D
var title_label: Label
var status_label: Label
var help_label: Label
var toast_label: Label
var capture_mode := false
var _toast_until := 0.0



# 正式组件与演员无旧版本脚本依赖。
const PRODUCTION_BUILDING := preload("res://assets/ember/buildings_final/scripts/building_asset.gd")
const INTACT_ACTOR := preload("res://assets/ember/buildings_final/scripts/building_demo_actor.gd")
const PLACEMENTS := [Vector2(160, 590), Vector2(514, 590), Vector2(1030, 590)]
var building_labels: Array[Label] = []

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	world = Node2D.new()
	world.name = "World"
	world.y_sort_enabled = true
	add_child(world)
	_build_existing_floor()
	for index: int in BUILDING_IDS.size():
		var building = PRODUCTION_BUILDING.new()
		building.building_id = BUILDING_IDS[index]
		building.position = PLACEMENTS[index]
		world.add_child(building)
		buildings.append(building)
		building.operation_denied.connect(_show_toast)
	actor = INTACT_ACTOR.new()
	actor.name = "Player"
	actor.position = Vector2(160, 650)
	world.add_child(actor)
	_build_ui()


func _process(_delta: float) -> void:
	if actor == null: return
	var actor_rects: Array[Rect2] = [actor.ground_rect()]
	for building in buildings: building.set_actor_rects(actor_rects)
	if capture_mode: return
	var building = nearest_building()
	if building == null: return
	var door_words := ""
	for id: String in building.doors:
		var door: Dictionary = building.doors[id]
		var state := "开启" if door.progress >= 0.999 else ("关闭" if door.progress <= 0.001 else "升降中")
		door_words += ("人门" if id == "personnel" else "货门") + ":" + state + ("/锁定 " if door.locked else " ")
	status_label.text = String(building.definition.get("name", building.building_id)) + "  " + door_words + ("供电" if building.powered else "断电") + (" / 故障" if building.faulted else "") + (" / 室内" if building.interior_visible else "")
	toast_label.visible = Time.get_ticks_msec() * 0.001 < _toast_until


func _unhandled_key_input(event: InputEvent) -> void:
	if capture_mode or not event is InputEventKey or not event.pressed or event.echo: return
	var building = nearest_building()
	if building == null: return
	if not building.initialized:
		_show_toast("建筑资源仍在注册，稍后重新打开示例")
		return
	match event.physical_keycode:
		KEY_E: building.toggle_door("personnel", actor.global_position)
		KEY_G: building.toggle_door("cargo", actor.global_position)
		KEY_C: building.toggle_maintenance(actor.global_position)
		KEY_F: building.toggle_device(actor.global_position)
		KEY_R: building.repair_device(actor.global_position)
		KEY_H: building.set_inspection_mode(not building.inspection_mode)
		KEY_J: building.set_roof_hatch_inspection(not building.roof_hatch_open)
		KEY_I: building.set_glass_lit(not building.glass_lit)
		KEY_P:
			if _near_panel(building): building.set_power(not building.powered)
		KEY_X:
			if _near_panel(building): building.set_fault(not building.faulted)
		KEY_L:
			if _near_panel(building): building.set_locked("personnel", not building.doors.personnel.locked)
		KEY_F5: save_state()
		KEY_F9: load_state()
	get_viewport().set_input_as_handled()


func nearest_building() -> Node2D:
	var nearest: Node2D
	var distance := INF
	for building: Node2D in buildings:
		var rect: Rect2 = building.footprint_rect()
		var local := building.to_local(actor.global_position)
		var clamped := local.clamp(rect.position, rect.end)
		var next_distance := local.distance_to(clamped)
		if next_distance < distance:
			distance = next_distance
			nearest = building
	return nearest


func save_state(path: String = SAVE_PATH) -> void:
	var states: Array[Dictionary] = []
	for building in buildings: states.append(building.snapshot())
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		_show_toast("保存失败")
		return
	file.store_string(JSON.stringify({"buildings": states, "player": [actor.position.x, actor.position.y]}, "\t"))
	_show_toast("已保存建筑状态")


func load_state(path: String = SAVE_PATH) -> void:
	if not FileAccess.file_exists(path):
		_show_toast("还没有保存记录")
		return
	var state: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not state is Dictionary: return
	var point: Array = state.get("player", [112, 446])
	# 先恢复玩家，再向所有建筑提交同一保存时刻的真实接触盒。
	# restore()内部会做零时长安全检查，不能沿用读档前玩家所在的位置。
	actor.position = Vector2(float(point[0]), float(point[1]))
	var actor_rects: Array[Rect2] = [actor.ground_rect()]
	for building in buildings: building.set_actor_rects(actor_rects)
	for saved: Dictionary in state.get("buildings", []):
		for building in buildings:
			if building.building_id == saved.get("building_id", ""): building.restore(saved)
	_show_toast("已恢复建筑状态")


func _near_panel(building: Node2D) -> bool:
	if building.to_local(actor.global_position).distance_to(building._service_ground_mount()) <= building.interaction_distance:
		return true
	_show_toast("请靠近地面面板操作")
	return false


func _build_existing_floor() -> void:
	# 从现有1024周期读取8×8原生128图块；TileMapLayer.scale=0.25保持旧地板标准。
	# 本示例展示连续地面，不生成建筑Terrain，也不宣称新增47型建筑笔刷。
	var layer := TileMapLayer.new()
	layer.name = "ExistingContinuousFloor"
	layer.scale = Vector2(0.25, 0.25)
	layer.z_index = -10
	layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var set := TileSet.new()
	set.tile_size = Vector2i(128, 128)
	var source := TileSetAtlasSource.new()
	source.texture = load(FLOOR_TEXTURE) as Texture2D
	source.texture_region_size = Vector2i(128, 128)
	for y: int in 8:
		for x: int in 8: source.create_tile(Vector2i(x, y))
	set.add_source(source, 0)
	layer.tile_set = set
	for y: int in 25:
		for x: int in 44: layer.set_cell(Vector2i(x, y), 0, Vector2i(x % 8, y % 8))
	world.add_child(layer)


func _build_ui() -> void:
	var canvas := CanvasLayer.new()
	canvas.name = "ReviewInterface"
	add_child(canvas)
	title_label = _label(canvas, Vector2(28, 18), 24, "EMBER v004r1 / INTACT BUILDINGS")
	status_label = _label(canvas, Vector2(28, 58), 18, "")
	help_label = _label(canvas, Vector2.ZERO, 18, "WASD/方向键 移动 | E 人门 | G 卷帘 | C 检修盖 | F 设备启停 | R 维修\nP 供电 | L 门锁 | X 故障 | I 窗玻璃亮暗 | H 遮挡检视 | J 塔顶盖检视 | F5/F9 保存/恢复")
	help_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	toast_label = _label(canvas, Vector2.ZERO, 19, "")
	toast_label.modulate = Color(0.83, 0.68, 0.43)
	for index: int in buildings.size():
		var label := _label(canvas, Vector2.ZERO, 18, String(buildings[index].definition.name))
		label.size = Vector2(190, 28)
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		building_labels.append(label)
	get_viewport().size_changed.connect(_layout_review_ui)
	_layout_review_ui()


func _label(parent: Node, point: Vector2, font_size: int, content: String) -> Label:
	var label := Label.new()
	label.position = point
	label.text = content
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", Color(0.78, 0.84, 0.82))
	parent.add_child(label)
	return label


func _show_toast(message: String) -> void:
	if toast_label == null: return
	toast_label.text = message
	_toast_until = Time.get_ticks_msec() * 0.001 + 2.4


func _layout_review_ui() -> void:
	# 使用实际逻辑视口，避免再次继承旧1024高界面的y946/y896常量。
	var view := get_viewport_rect().size
	help_label.position = Vector2(28, view.y - 78)
	help_label.size = Vector2(maxf(200, view.x - 56), 58)
	toast_label.position = Vector2(28, view.y - 120)
	toast_label.size.x = maxf(200, view.x - 56)
	for index: int in building_labels.size():
		building_labels[index].position = Vector2(PLACEMENTS[index].x - 95, 100)
