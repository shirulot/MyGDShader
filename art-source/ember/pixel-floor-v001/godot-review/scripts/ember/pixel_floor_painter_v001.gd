@tool
extends Node2D
## 原生 32 px 地板素材试铺：占用数据决定结构，图块坐标只是渲染结果。
## 编辑器中 Floor / Bridge 的 Terrain 修改也会同步所有跨层落桥开口。
## 不依赖主游戏的 Game autoload；此场景可以复制进空项目独立使用。

const ASSET_DIR := "res://assets/ember/environment/pixel_floor_v001/"
const SAVE_PATH := "user://pixel_floor_layout_v001.json"
const BRUSHES := ["floor", "grate", "seam", "bridge", "details"]
const LABELS := {"floor": "地板＋自动收边", "grate": "格栅覆盖", "seam": "板缝路径", "bridge": "栈桥＋自动落桥", "details": "独立装饰"}
const DETAIL_LABELS := ["小油渍", "长油渍", "小掉漆", "长掉漆", "锈斑", "细裂", "检修盖闭", "检修盖开"]
const DIRECTIONS := [Vector2i.UP, Vector2i(1,-1), Vector2i.RIGHT, Vector2i(1,1), Vector2i.DOWN, Vector2i(-1,1), Vector2i.LEFT, Vector2i(-1,-1)]
const BOARD := Rect2i(0, 0, 22, 16)

var occupied: Dictionary = {"floor": {}, "grate": {}, "seam": {}, "bridge": {}, "details": {}}
## seam 的每条边显式登记，邻近的两笔不会因为相邻就自动串线。
var seam_edges: Dictionary = {}
var atlas_lookup: Dictionary = {}
var brush := "floor"
var undo_stack: Array[Dictionary] = []
var redo_stack: Array[Dictionary] = []
var _stroke_start: Dictionary = {}
var _previous_cell := Vector2i(9999, 9999)
var _erasing := false
var _drawing := false
var _synchronizing := false
var _editor_sync_pending := false
var _editor_occupancy_fingerprint := ""
var _camera: Camera2D
var _status: Label
var _brush_select: OptionButton
var _zoom := 1
var _detail_index := 0

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_load_catalog()
	if Engine.is_editor_hint():
		for id in BRUSHES:
			var layer := _layer(id)
			if layer != null and not layer.changed.is_connected(_on_editor_layer_changed):
				layer.changed.connect(_on_editor_layer_changed)
		_on_editor_layer_changed()
		return
	_create_interface()
	if _layer("floor").get_used_cells().is_empty():
		seed_demo()
	else:
		_adopt_layer_occupancy()
		_rebuild_all()
	set_process_unhandled_input(true)
	queue_redraw()

func _load_catalog() -> void:
	if not FileAccess.file_exists(ASSET_DIR + "catalog.json"):
		return
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ASSET_DIR + "catalog.json"))
	for atlas: Dictionary in catalog.atlases:
		atlas_lookup[atlas.id] = {}
		for tile: Dictionary in atlas.tiles:
			var key = "%d:%d" % [int(tile.floor_mask), int(tile.bridge_ports)] if atlas.mode == "context" else int(tile.mask)
			atlas_lookup[atlas.id][key] = Vector2i(int(tile.coord[0]), int(tile.coord[1]))

func _layer(id: String) -> TileMapLayer:
	return get_node_or_null(NodePath(id.to_pascal_case())) as TileMapLayer

func _on_editor_layer_changed() -> void:
	# Changed 可以在同一帧触发多次。延后一帧汇总，避免信号递归与重做顺序。
	if _synchronizing or _editor_sync_pending:
		return
	_editor_sync_pending = true
	call_deferred("_synchronize_editor_layers")

func _synchronize_editor_layers() -> void:
	_editor_sync_pending = false
	if not Engine.is_editor_hint() or atlas_lookup.is_empty():
		return
	var fingerprint := _fingerprint_layers()
	if fingerprint.is_empty(): return
	# 自身重选只改图块；记录稳定的最终渲染指纹，避免 changed 信号无限循环。
	if fingerprint == _editor_occupancy_fingerprint:
		return
	_adopt_layer_occupancy()
	_rebuild_all()
	_editor_occupancy_fingerprint = _fingerprint_layers()

func _fingerprint_layers() -> String:
	var fingerprint := ""
	for id in BRUSHES:
		var layer := _layer(id)
		if layer == null or layer.tile_set == null:
			return ""
		var cells := layer.get_used_cells()
		cells.sort_custom(func(a: Vector2i, b: Vector2i) -> bool: return a.y < b.y or (a.y == b.y and a.x < b.x))
		fingerprint += id + str(cells)
		# native Terrain 在相同占用上重刷仍可能替换落桥 source1，必须捕获坐标变化。
		for cell in cells: fingerprint += str(layer.get_cell_source_id(cell)) + ":" + str(layer.get_cell_atlas_coords(cell))
	return fingerprint

func _adopt_layer_occupancy() -> void:
	for id in BRUSHES:
		occupied[id] = {}
		for cell in _layer(id).get_used_cells():
			occupied[id][cell] = _layer(id).get_cell_atlas_coords(cell).x if id == "details" else true
	# 读取实际 peering bits，保留编辑器 Terrain Path 的相邻但不连接语义。
	seam_edges.clear()
	var seam_layer := _layer("seam")
	var side_bits := [TileSet.CELL_NEIGHBOR_TOP_SIDE, TileSet.CELL_NEIGHBOR_RIGHT_SIDE, TileSet.CELL_NEIGHBOR_BOTTOM_SIDE, TileSet.CELL_NEIGHBOR_LEFT_SIDE]
	for cell: Vector2i in occupied.seam:
		var data := seam_layer.get_cell_tile_data(cell)
		for bit in [1,2]:
			var neighbor: Vector2i = cell + DIRECTIONS[bit * 2]
			if not occupied.seam.has(neighbor): continue
			var neighbor_data := seam_layer.get_cell_tile_data(neighbor)
			if data != null and neighbor_data != null and data.get_terrain_peering_bit(side_bits[bit]) == 0 and neighbor_data.get_terrain_peering_bit(side_bits[(bit+2)%4]) == 0:
				_link_seam(cell, neighbor)

func seed_demo() -> void:
	occupied = {"floor": {}, "grate": {}, "seam": {}, "bridge": {}, "details": {}}
	seam_edges.clear()
	# 主平台有凹洞、切角、窄路与孤岛，直接展示 47 型区域能力。
	for y in range(1, 13):
		for x in range(1, 16):
			if (x < 3 and y < 3) or (x >= 12 and y >= 10):
				continue
			if Rect2i(8, 5, 3, 3).has_point(Vector2i(x, y)):
				continue
			occupied.floor[Vector2i(x, y)] = true
	for x in range(1, 7): occupied.floor[Vector2i(x, 14)] = true
	for y in range(12, 15): occupied.floor[Vector2i(3, y)] = true
	for cell in [Vector2i(8, 14), Vector2i(9, 15), Vector2i(11, 14)]: occupied.floor[cell] = true
	# 功能格栅占用自己的区域，下面仍是同一整片地板。
	for y in range(3, 6):
		for x in range(3, 6): occupied.grate[Vector2i(x, y)] = true
	for cell in [Vector2i(4, 6), Vector2i(5, 6), Vector2i(5, 7), Vector2i(6, 7)]: occupied.grate[cell] = true
	var seam_path: Array[Vector2i] = []
	for x in range(2, 15): seam_path.append(Vector2i(x, 9))
	for y in range(3, 10): seam_path.append(Vector2i(14, y))
	for cell in seam_path: occupied.seam[cell] = true
	for i in range(1, seam_path.size()):
		if seam_path[i - 1].distance_to(seam_path[i]) == 1.0: _link_seam(seam_path[i - 1], seam_path[i])
	# 东向落桥与 T / L / 十字；桥与地板之间自动打开放口。
	for x in range(16, 21): occupied.bridge[Vector2i(x, 4)] = true
	for y in range(2, 11): occupied.bridge[Vector2i(18, y)] = true
	for x in range(18, 21): occupied.bridge[Vector2i(x, 10)] = true
	for entry in [[6,3,0],[12,6,2],[12,8,6],[3,10,4],[7,11,5],[5,10,1]]:
		occupied.details[Vector2i(entry[0],entry[1])] = entry[2]
	_rebuild_all()
	_update_status("演示布局已生成")

func _normalized_blob_mask(cell: Vector2i, region: Dictionary) -> int:
	var mask := 0
	for bit in range(8):
		if region.has(cell + DIRECTIONS[bit]): mask |= 1 << bit
	for diagonal in [1, 3, 5, 7]:
		if (mask & (1 << ((diagonal + 7) % 8))) == 0 or (mask & (1 << ((diagonal + 1) % 8))) == 0:
			mask &= ~(1 << diagonal)
	return mask

func _sides_mask(cell: Vector2i, region: Dictionary) -> int:
	var mask := 0
	for bit in range(4):
		if region.has(cell + DIRECTIONS[bit * 2]): mask |= 1 << bit
	return mask

func _rebuild_all() -> void:
	if atlas_lookup.is_empty(): return
	_synchronizing = true
	# 先归一所有语义占用，再计算任何邻接，避免删除的晚遍历邻格残留端帽。
	# 同格冲突统一 floor 优先：运行时、编辑器采纳、布局重载都使用此规则。
	for cell in occupied.bridge.keys():
		if occupied.floor.has(cell): occupied.bridge.erase(cell)
	for cell in occupied.grate.keys():
		if not occupied.floor.has(cell): occupied.grate.erase(cell)
	for cell in occupied.seam.keys():
		if not occupied.floor.has(cell): _remove_seam(cell)
	for cell in occupied.details.keys():
		if not occupied.floor.has(cell): occupied.details.erase(cell)
	# 24px 桥不能假装成 32px 地板邻格：两侧各 4px 肩口仍要收边。
	# 地板先按自身 47 型 mask，落桥格再用独立上下文图块打开中央 24px。
	var walkable: Dictionary = occupied.floor.duplicate()
	for cell in occupied.bridge: walkable[cell] = true
	for id in ["floor_facade", "floor", "floor_landing", "rim", "grate", "seam", "bridge", "details"]:
		if _layer(id) != null: _layer(id).clear()
	for cell: Vector2i in occupied.floor:
		var mask := _normalized_blob_mask(cell, occupied.floor)
		var bridge_ports := _sides_mask(cell, occupied.bridge)
		_put_floor_context("floor", cell, mask, bridge_ports)
		# 立面按同一 floor mask 派生。其节点整体下移16px，投影落到所属格南侧。
		# 仅显示南侧外露面；有南向桥端时，context图块让中央24px通道贯通。
		_put_floor_context("facade",cell,mask,bridge_ports)
		# Rim 使用完全相同的地板格及 mask；255 全透明块也必须放入层。
		_put_floor_context("rim", cell, mask, bridge_ports)
	for cell: Vector2i in occupied.grate:
		_put("grate", cell, _normalized_blob_mask(cell, occupied.grate))
	for cell: Vector2i in occupied.seam:
		var mask := 0
		for bit in range(4):
			if seam_edges.has(_edge_key(cell, cell + DIRECTIONS[bit * 2])): mask |= 1 << bit
		_put("seam", cell, mask)
	for cell: Vector2i in occupied.bridge:
		_put("bridge", cell, _sides_mask(cell, walkable))
	if _layer("details") != null:
		for cell: Vector2i in occupied.details:
			_layer("details").set_cell(cell,0,Vector2i(int(occupied.details[cell]),0))
	_synchronizing = false
	queue_redraw()

func _put(id: String, cell: Vector2i, mask: int) -> void:
	_layer(id).set_cell(cell, 0, atlas_lookup[id][mask], 0)

func _put_floor_context(id: String, cell: Vector2i, floor_mask: int, bridge_ports: int) -> void:
	# Floor 永远保留 source0 的原生 Terrain 身份；落桥实心图覆盖在派生层。
	# native Terrain 不会把普通 source1 当 empty，也不会误选上下文桥口。
	if id == "floor": _put("floor",cell,floor_mask)
	var target_id := "floor_landing" if id == "floor" else ("floor_facade" if id == "facade" else id)
	if bridge_ports == 0:
		if id != "floor": _layer(target_id).set_cell(cell,0,atlas_lookup[id][floor_mask],0)
		return
	# source 1 是普通 atlas source，无 Terrain 候选身份，避免编辑器随机选到桥口。
	var key := "%d:%d" % [floor_mask, bridge_ports]
	if atlas_lookup.has(id + "_landing") and atlas_lookup[id + "_landing"].has(key):
		_layer(target_id).set_cell(cell,1,atlas_lookup[id + "_landing"][key],0)
	else:
		push_error("Missing landing context %s %s" % [id, key])
		if id != "floor": _layer(target_id).set_cell(cell,0,atlas_lookup[id][floor_mask],0)

func _edge_key(a: Vector2i, b: Vector2i) -> String:
	if a.y > b.y or (a.y == b.y and a.x > b.x):
		var temp := a; a = b; b = temp
	return "%d,%d:%d,%d" % [a.x, a.y, b.x, b.y]

func _link_seam(a: Vector2i, b: Vector2i) -> void:
	if a.distance_to(b) == 1.0 and occupied.seam.has(a) and occupied.seam.has(b):
		seam_edges[_edge_key(a, b)] = true

func _remove_seam(cell: Vector2i) -> void:
	occupied.seam.erase(cell)
	for direction in [Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT]:
		seam_edges.erase(_edge_key(cell, cell + direction))

func paint_cell(cell: Vector2i, erase := false, previous := Vector2i(9999,9999)) -> void:
	## 工具与验证脚本共用的语义编辑入口；每次修改后重算所有关联层。
	if not BOARD.has_point(cell): return
	if erase:
		if brush == "seam": _remove_seam(cell)
		else: occupied[brush].erase(cell)
	else:
		if brush in ["grate", "seam", "details"] and not occupied.floor.has(cell): return
		if brush == "bridge" and occupied.floor.has(cell): return
		occupied[brush][cell] = _detail_index if brush == "details" else true
		if brush == "floor": occupied.bridge.erase(cell)
		if brush == "seam": _link_seam(previous, cell)
	_rebuild_all()

func snapshot() -> Dictionary:
	var edges := seam_edges.keys()
	edges.sort()
	var state := {"version":1,"tile_size":32,"occupied":{},"seam_edges":edges}
	for id in BRUSHES:
		state.occupied[id] = []
		# TileMapLayer.get_used_cells() 的遍历顺序不是布局语义，保存时固定排序。
		var cells: Array = occupied[id].keys()
		cells.sort_custom(func(a: Vector2i,b: Vector2i) -> bool: return a.y < b.y or (a.y == b.y and a.x < b.x))
		for cell: Vector2i in cells:
			state.occupied[id].append([cell.x,cell.y,int(occupied[id][cell])] if id == "details" else [cell.x,cell.y])
	return state

func restore_snapshot(state: Dictionary) -> void:
	for id in BRUSHES:
		occupied[id] = {}
		for point in state.occupied.get(id, []):
			occupied[id][Vector2i(int(point[0]), int(point[1]))] = int(point[2]) if id == "details" else true
	seam_edges.clear()
	for key in state.get("seam_edges", []): seam_edges[str(key)] = true
	_rebuild_all()

func commit_edit(before: Dictionary) -> void:
	if JSON.stringify(before) != JSON.stringify(snapshot()):
		undo_stack.append(before)
		redo_stack.clear()
	_update_status()

func undo_edit() -> void:
	if undo_stack.is_empty(): return
	redo_stack.append(snapshot())
	restore_snapshot(undo_stack.pop_back())
	_update_status("已撤销")

func redo_edit() -> void:
	if redo_stack.is_empty(): return
	undo_stack.append(snapshot())
	restore_snapshot(redo_stack.pop_back())
	_update_status("已重做")

func save_layout(path := SAVE_PATH) -> Error:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null: return FileAccess.get_open_error()
	file.store_string(JSON.stringify(snapshot(), "\t") + "\n")
	_update_status("布局已保存：" + path)
	return OK

func load_layout(path := SAVE_PATH) -> Error:
	if not FileAccess.file_exists(path):
		_update_status("尚无保存布局")
		return ERR_FILE_NOT_FOUND
	var state = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not state is Dictionary or not state.has("occupied"): return ERR_PARSE_ERROR
	var before := snapshot()
	restore_snapshot(state)
	commit_edit(before)
	_update_status("已重载语义布局并重新补全")
	return OK

func set_zoom(value: int) -> void:
	_zoom = value
	if _camera != null: _camera.zoom = Vector2.ONE * value
	_update_status()

func _unhandled_input(event: InputEvent) -> void:
	if Engine.is_editor_hint(): return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.ctrl_pressed and event.keycode == KEY_Z:
			if event.shift_pressed: redo_edit()
			else: undo_edit()
		elif event.ctrl_pressed and event.keycode == KEY_Y: redo_edit()
		elif event.ctrl_pressed and event.keycode == KEY_S: save_layout()
		elif event.ctrl_pressed and event.keycode == KEY_L: load_layout()
		elif event.keycode in [KEY_1, KEY_2, KEY_3, KEY_4, KEY_5]:
			brush = BRUSHES[int(event.keycode - KEY_1)]
			_brush_select.select(BRUSHES.find(brush))
			_update_status()
		return
	if event is InputEventMouseButton:
		if event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN] and event.pressed:
			var levels := [1,2,4]
			var next := clampi(levels.find(_zoom) + (1 if event.button_index == MOUSE_BUTTON_WHEEL_UP else -1), 0, 2)
			set_zoom(levels[next])
			return
		if event.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
			if event.pressed:
				_stroke_start = snapshot()
				_drawing = true
				_erasing = event.button_index == MOUSE_BUTTON_RIGHT
				_previous_cell = Vector2i(9999,9999)
				_paint_to_mouse()
			elif _drawing:
				_drawing = false
				commit_edit(_stroke_start)
	if event is InputEventMouseMotion:
		if Input.is_mouse_button_pressed(MOUSE_BUTTON_MIDDLE):
			_camera.position -= event.relative / _camera.zoom
		elif _drawing: _paint_to_mouse()

func _input(event: InputEvent) -> void:
	# 释放时即使鼠标落到 HUD 上，也结束这一笔，避免 UI 吞掉释放事件。
	if not Engine.is_editor_hint() and _drawing and event is InputEventMouseButton and not event.pressed and event.button_index in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_RIGHT]:
		_drawing = false
		commit_edit(_stroke_start)

func _paint_to_mouse() -> void:
	var cell := _layer("floor").local_to_map(_layer("floor").get_local_mouse_position())
	if cell == _previous_cell: return
	# 快速拖动会跳格：按正交步进插值，不漏中间格、不画出对角伪连接。
	var cursor := _previous_cell
	if not BOARD.has_point(cursor): cursor = cell
	while cursor != cell:
		var next := cursor
		if next.x != cell.x: next.x += 1 if cell.x > next.x else -1
		else: next.y += 1 if cell.y > next.y else -1
		paint_cell(next, _erasing, cursor)
		cursor = next
	paint_cell(cell, _erasing, _previous_cell)
	_previous_cell = cell

func _create_interface() -> void:
	_camera = Camera2D.new()
	_camera.name = "PreviewCamera"
	_camera.position = Vector2(352,196)
	add_child(_camera)
	var hud := CanvasLayer.new()
	add_child(hud)
	var panel := PanelContainer.new()
	panel.position = Vector2(10,10)
	panel.size = Vector2(680,142)
	hud.add_child(panel)
	var column := VBoxContainer.new()
	panel.add_child(column)
	var title := Label.new()
	title.text = "PIXEL FLOOR v001  ·  原生 32px / 32世界单位"
	column.add_child(title)
	var row := HBoxContainer.new()
	column.add_child(row)
	_brush_select = OptionButton.new()
	for id in BRUSHES: _brush_select.add_item(LABELS[id])
	_brush_select.item_selected.connect(func(index: int) -> void: brush = BRUSHES[index]; _update_status())
	row.add_child(_brush_select)
	var detail_select := OptionButton.new()
	for label in DETAIL_LABELS: detail_select.add_item(label)
	detail_select.item_selected.connect(func(index: int) -> void: _detail_index = index; brush = "details"; _brush_select.select(4); _update_status())
	row.add_child(detail_select)
	for level in [1, 2, 4]:
		_add_button(row, str(level) + "x", func() -> void: set_zoom(level))
	var actions := HBoxContainer.new()
	column.add_child(actions)
	_add_button(actions, "撤销", undo_edit)
	_add_button(actions, "重做", redo_edit)
	_add_button(actions, "保存", func() -> void: save_layout())
	_add_button(actions, "重载", func() -> void: load_layout())
	var hint := Label.new()
	hint.text = "左键连续铺刷 · 右键擦除 · 中键拖动 · 1～5选笔刷 · Ctrl+Z/Y撤销重做"
	column.add_child(hint)
	_status = Label.new()
	column.add_child(_status)

func _add_button(row: HBoxContainer, text: String, action: Callable) -> void:
	var button := Button.new()
	button.text = text
	button.pressed.connect(action)
	row.add_child(button)

func _update_status(message := "") -> void:
	if _status != null:
		_status.text = "%s · %dx · floor %d / grate %d / seam %d / bridge %d  %s" % [LABELS[brush], _zoom, occupied.floor.size(), occupied.grate.size(), occupied.seam.size(), occupied.bridge.size(), message]

func _draw() -> void:
	if Engine.is_editor_hint(): return
	# 冷色中性底模拟空地 / 深水，不把动态水纹烘焙进地板资源。
	draw_rect(Rect2(Vector2.ZERO, Vector2(704,512)), Color("14272c"))
	for x in range(23): draw_line(Vector2(x*32,0), Vector2(x*32,512), Color(0.15,0.24,0.27,0.25), 1.0)
	for y in range(17): draw_line(Vector2(0,y*32), Vector2(704,y*32), Color(0.15,0.24,0.27,0.25), 1.0)
