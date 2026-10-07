@tool
extends Node2D
## 最终建筑运行组件：解析 v004r1 登记，保持完整母图与既有交互。
## 已合并历史继承链；原始实现可从冻结 v004r1 包追溯。

signal state_changed(building_id: String)
signal operation_denied(reason: String)

@export_enum("control_tower", "repair_workshop", "logistics_warehouse") var building_id := "control_tower"
@export_file("*.json") var catalog_path := "res://assets/ember/buildings_final/textures/catalog_v004r1.json"
@export var motion_seconds := 0.8
@export var interaction_distance := 64.0

const WALL_THICKNESS := 8.0
const CLEAR_COLLISION_PROGRESS := 0.9999

var definition: Dictionary = {}
var doors: Dictionary = {}
var powered := true
var faulted := false
var device_enabled := true
var maintenance_open := false
var roof_hatch_open := false
var glass_lit := false
var inspection_mode := false
var interior_visible := false
var initialized := false
var load_errors: Array[String] = []

var _rotors: Array[Sprite2D] = []
var _actor_rects: Array[Rect2] = []
var _blink_time := 0.0



const INTACT_SHADER := preload("res://assets/ember/buildings_final/shaders/building_intact.gdshader")
var intact_sprite: Sprite2D
var intact_material: ShaderMaterial
var native_scale := 1.0
var source_pivot := Vector2.ZERO

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_rebuild()


func _process(delta: float) -> void:
	# 编辑器只展示注册部件，避免编辑场景时自动开门或转动设备。
	if Engine.is_editor_hint(): return
	advance_state(delta)


func advance_state(delta: float) -> void:
	## 此方法同时供真实帧循环与验收调用，不为测试维护第二套状态机。
	if not initialized: return
	_blink_time += delta
	for id: String in doors:
		var door: Dictionary = doors[id]
		if door.target < door.progress and _aperture_occupied(door):
			# 门口有人时立刻反向；开始关闭前也使用同一感应区。
			door.target = 1.0
			door.obstructed = true
		if powered and not faulted:
			door.progress = move_toward(float(door.progress), float(door.target), delta / maxf(motion_seconds, 0.01))
		_apply_door_visual(door)
		# 只有净口完全打开才释放门碰撞；部分升起不能误判为通行。
		var collision: CollisionShape2D = door.collision
		collision.set_deferred("disabled", float(door.progress) >= CLEAR_COLLISION_PROGRESS)
	for rotor: Sprite2D in _rotors:
		if powered and not faulted and device_enabled:
			rotor.rotation += delta * 4.0
	_update_status_lenses()


func footprint_rect() -> Rect2:
	var footprint := _vec(definition.get("footprint_px", [0, 0]))
	return Rect2(Vector2(-footprint.x * 0.5, -footprint.y), footprint)


func set_actor_rects(world_rects: Array) -> void:
	## 只把地面接触包围盒送入建筑，机器人64×96绘图画布不是碰撞尺寸。
	_actor_rects.clear()
	var is_inside := false
	for world_rect: Rect2 in world_rects:
		var local_rect := Rect2(to_local(world_rect.position), world_rect.size / global_scale)
		_actor_rects.append(local_rect)
		if footprint_rect().has_point(local_rect.get_center()): is_inside = true
	set_interior_visible(is_inside)


func set_interior_visible(value: bool) -> void:
	interior_visible = value
	_apply_occlusion()


func set_inspection_mode(value: bool) -> void:
	inspection_mode = value
	_apply_occlusion()
	state_changed.emit(building_id)


func request_door(id: String, open: bool, actor_world: Vector2 = Vector2.INF, inspection := false) -> bool:
	if not doors.has(id): return _deny("找不到门")
	var door: Dictionary = doors[id]
	if not inspection and not _near_mount(actor_world, Vector2(float(door.center_x), 0.0)):
		return _deny("请走到门前再操作")
	if not powered: return _deny("建筑断电，门板停止")
	if faulted: return _deny("设备故障，请打开地面检修盖维修")
	if open and door.locked: return _deny("门已锁定")
	if not open and _aperture_occupied(door):
		door.target = 1.0
		door.obstructed = true
		state_changed.emit(building_id)
		return _deny("入口被占用，自动重开")
	door.target = 1.0 if open else 0.0
	door.obstructed = false
	state_changed.emit(building_id)
	return true


func toggle_door(id: String, actor_world: Vector2 = Vector2.INF, inspection := false) -> bool:
	if not doors.has(id): return false
	return request_door(id, float(doors[id].target) < 0.5, actor_world, inspection)


func set_locked(id: String, value: bool) -> void:
	if not doors.has(id): return
	doors[id].locked = value
	_update_status_lenses()
	state_changed.emit(building_id)


func set_power(value: bool) -> void:
	powered = value
	_apply_glass_state()
	_update_status_lenses()
	state_changed.emit(building_id)


func set_fault(value: bool) -> void:
	faulted = value
	_update_status_lenses()
	state_changed.emit(building_id)


func toggle_maintenance(actor_world: Vector2 = Vector2.INF, inspection := false) -> bool:
	if not definition.has("service_rect"): return _deny("该建筑未登记地面检修盖")
	if not inspection and not _near_mount(actor_world, _service_ground_mount()): return _deny("请靠近检修盖")
	maintenance_open = not maintenance_open
	_apply_covers()
	state_changed.emit(building_id)
	return true


func repair_device(actor_world: Vector2 = Vector2.INF, inspection := false) -> bool:
	if not inspection and not _near_mount(actor_world, _service_ground_mount()): return _deny("请靠近地面控制面板")
	if definition.has("service_rect") and not maintenance_open: return _deny("先打开检修盖")
	set_fault(false)
	return true


func toggle_device(actor_world: Vector2 = Vector2.INF, inspection := false) -> bool:
	if not inspection and not _near_mount(actor_world, _service_ground_mount()):
		return _deny("请走到地面设备控制面板")
	if not powered or faulted: return _deny("设备断电或故障，不能启动")
	device_enabled = not device_enabled
	_update_status_lenses()
	state_changed.emit(building_id)
	return true


func set_roof_hatch_inspection(value: bool) -> void:
	# 原图有舱盖的控制塔提供检视开合。此接口不声明角色能攀爬屋顶。
	roof_hatch_open = value and definition.has("hatch_rect")
	if intact_material != null: intact_material.set_shader_parameter("hatch_open", roof_hatch_open)
	state_changed.emit(building_id)


func set_glass_lit(value: bool) -> void:
	glass_lit = value
	_apply_glass_state()
	state_changed.emit(building_id)


func _apply_glass_state() -> void:
	if intact_material != null: intact_material.set_shader_parameter("glass_lit", glass_lit)


func snapshot() -> Dictionary:
	var door_states: Dictionary = {}
	for id: String in doors:
		var door: Dictionary = doors[id]
		door_states[id] = {"progress": door.progress, "target": door.target, "locked": door.locked}
	return {"revision": "building_assets_v004r1", "building_id": building_id,
		"powered": powered, "faulted": faulted, "device_enabled": device_enabled,
		"maintenance_open": maintenance_open, "roof_hatch_open": roof_hatch_open,
		"glass_lit": glass_lit, "doors": door_states}


func restore(state: Dictionary) -> bool:
	if state.get("building_id", "") != building_id: return false
	powered = bool(state.get("powered", true))
	faulted = bool(state.get("faulted", false))
	device_enabled = bool(state.get("device_enabled", true))
	maintenance_open = bool(state.get("maintenance_open", false))
	roof_hatch_open = bool(state.get("roof_hatch_open", false))
	glass_lit = bool(state.get("glass_lit", false))
	var saved_doors: Dictionary = state.get("doors", {})
	for id: String in doors:
		if not saved_doors.has(id): continue
		doors[id].progress = clampf(float(saved_doors[id].get("progress", 0.0)), 0.0, 1.0)
		doors[id].target = 1.0 if float(saved_doors[id].get("target", 0.0)) >= 0.5 else 0.0
		doors[id].locked = bool(saved_doors[id].get("locked", false))
	_apply_covers()
	set_roof_hatch_inspection(roof_hatch_open)
	set_glass_lit(glass_lit)
	advance_state(0.0)
	return true


func _rebuild() -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(catalog_path))
	if not data is Dictionary:
		load_errors.append("完整母图登记无法读取")
		return
	for item: Dictionary in data.get("buildings", []):
		if item.id == building_id: definition = item
	if definition.is_empty():
		load_errors.append("未登记完整建筑：" + building_id)
		return
	native_scale = float(definition.uniform_scale)
	source_pivot = _vec(definition.source_pivot_px)
	intact_sprite = Sprite2D.new()
	intact_sprite.name = "IntactArchitecture"
	intact_sprite.texture = load(definition.complete_texture)
	intact_sprite.centered = false
	intact_sprite.offset = -source_pivot
	intact_sprite.scale = Vector2.ONE * native_scale
	intact_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	intact_material = ShaderMaterial.new()
	intact_material.shader = INTACT_SHADER
	intact_sprite.material = intact_material
	add_child(intact_sprite)
	for spec: Dictionary in definition.doors: _register_source_door(spec)
	_set_source_rect("service_rect", definition.get("service_rect", [0, 0, 0, 0]))
	_set_source_rect("hatch_rect", definition.get("hatch_rect", [0, 0, 0, 0]))
	_set_rect_array("lens_rects", "lens_count", definition.get("lens_rects", []))
	_set_rect_array("glass_rects", "glass_count", definition.get("glass_rects", []))
	_build_wall_collisions(_vec(definition.footprint_px))
	initialized = true
	advance_state(0.0)
	_apply_occlusion()


func _build_wall_collisions(footprint: Vector2) -> void:
	var left := -footprint.x * 0.5
	var right := footprint.x * 0.5
	_static_box("NorthWall", Rect2(left, -footprint.y, footprint.x, WALL_THICKNESS))
	_static_box("WestWall", Rect2(left, -footprint.y, WALL_THICKNESS, footprint.y))
	_static_box("EastWall", Rect2(right - WALL_THICKNESS, -footprint.y, WALL_THICKNESS, footprint.y))
	var slots: Array[Vector2] = []
	for id: String in doors:
		var door: Dictionary = doors[id]
		slots.append(Vector2(float(door.center_x) - door.clear_px.x * 0.5, float(door.center_x) + door.clear_px.x * 0.5))
	slots.sort_custom(func(a: Vector2, b: Vector2) -> bool: return a.x < b.x)
	var cursor := left
	for slot: Vector2 in slots:
		if slot.x > cursor: _static_box("SouthWall" + str(cursor), Rect2(cursor, -4.0, slot.x - cursor, WALL_THICKNESS))
		cursor = slot.y
	if cursor < right: _static_box("SouthWallEnd", Rect2(cursor, -4.0, right - cursor, WALL_THICKNESS))


func _static_box(node_name: String, rect: Rect2) -> CollisionShape2D:
	var body := StaticBody2D.new()
	body.name = node_name
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	var shape := CollisionShape2D.new()
	var rectangle := RectangleShape2D.new()
	rectangle.size = rect.size
	shape.shape = rectangle
	shape.position = rect.get_center()
	body.add_child(shape)
	return shape


func _apply_door_visual(door: Dictionary) -> void:
	intact_material.set_shader_parameter(String(door.id) + "_progress", float(door.progress))


func _aperture_occupied(door: Dictionary) -> bool:
	for actor: Rect2 in _actor_rects:
		if actor.intersects(door.safety_rect): return true
	return false


func _apply_covers() -> void:
	if intact_material != null: intact_material.set_shader_parameter("service_open", maintenance_open)


func _apply_occlusion() -> void:
	# 进入建筑后整壳统一淡出；无需沿外檐或圆角人为切出第二圈边缘。
	if intact_sprite != null: intact_sprite.modulate.a = 0.14 if interior_visible or inspection_mode else 1.0


func _update_status_lenses() -> void:
	if intact_material == null: return
	var is_moving := false
	for id: String in doors:
		if not is_equal_approx(float(doors[id].target), float(doors[id].progress)): is_moving = true
	intact_material.set_shader_parameter("powered", powered)
	intact_material.set_shader_parameter("faulted", faulted)
	intact_material.set_shader_parameter("locked", bool(doors.get("personnel", {}).get("locked", false)))
	intact_material.set_shader_parameter("moving", is_moving && powered && not faulted)
	intact_material.set_shader_parameter("device_enabled", device_enabled)
	intact_material.set_shader_parameter("state_clock", _blink_time)


func _near_mount(actor_world: Vector2, local_mount: Vector2) -> bool:
	return actor_world.is_finite() and to_local(actor_world).distance_to(local_mount) <= interaction_distance


func _service_ground_mount() -> Vector2:
	return Vector2(float(definition.get("service_mount_x", 0.0)), 0.0)


func _deny(reason: String) -> bool:
	operation_denied.emit(reason)
	return false


func _vec(array: Array) -> Vector2:
	return Vector2(float(array[0]), float(array[1]))


func _rect(array: Array) -> Rect2:
	return Rect2(float(array[0]), float(array[1]), float(array[2]), float(array[3]))


func _register_source_door(spec: Dictionary) -> void:
	var id := String(spec.id)
	var source := _rect(spec.source_rect_px)
	var clear := source.size * native_scale
	var center_x := (source.get_center().x - source_pivot.x) * native_scale
	var draw_top_left := (source.position - source_pivot) * native_scale
	var collision := _static_box("Door_" + id, Rect2(center_x - clear.x * 0.5, -4.0, clear.x, 8.0))
	doors[id] = {"id": id, "center_x": center_x, "clear_px": clear, "source_rect": source,
		"opening_rect": Rect2(draw_top_left, clear),
		"safety_rect": Rect2(center_x - clear.x * 0.5, -12.0, clear.x, 24.0),
		"progress": 0.0, "target": 0.0, "locked": false, "obstructed": false,
		"collision": collision}
	_set_source_rect(id + "_rect", spec.source_rect_px)
	if id == "personnel": intact_material.set_shader_parameter("personnel_chamfer", float(spec.get("chamfer_px", 0)))


func _set_source_rect(parameter: String, values: Array) -> void:
	intact_material.set_shader_parameter(parameter, Vector4(values[0], values[1], values[2], values[3]))


func _set_rect_array(parameter: String, count_name: String, values: Array) -> void:
	var rectangles := PackedVector4Array()
	for i: int in 6:
		var r: Array = values[i] if i < values.size() else [0, 0, 0, 0]
		rectangles.append(Vector4(r[0], r[1], r[2], r[3]))
	intact_material.set_shader_parameter(parameter, rectangles)
	intact_material.set_shader_parameter(count_name, values.size())
