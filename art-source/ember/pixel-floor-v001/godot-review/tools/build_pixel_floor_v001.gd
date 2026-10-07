extends SceneTree
## 新地板包的真实引擎构建与验收。可在原工程或无 autoload 的隔离副本运行。
## godot --headless --path . --script res://tools/build_pixel_floor_v001.gd
## GPU 截图：去掉 --headless，并在末尾加 -- --capture。

const OUTPUT := "res://assets/ember/environment/pixel_floor_v001/"
const SCENE_PATH := "res://scenes/ember/pixel_floor_sandbox_v001.tscn"
const PAINTER_PATH := "res://scripts/ember/pixel_floor_painter_v001.gd"
const DIRECTIONS := [Vector2i.UP, Vector2i(1,-1), Vector2i.RIGHT, Vector2i(1,1), Vector2i.DOWN, Vector2i(-1,1), Vector2i.LEFT, Vector2i(-1,-1)]
const PEERING := [TileSet.CELL_NEIGHBOR_TOP_SIDE, TileSet.CELL_NEIGHBOR_TOP_RIGHT_CORNER, TileSet.CELL_NEIGHBOR_RIGHT_SIDE, TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER, TileSet.CELL_NEIGHBOR_BOTTOM_SIDE, TileSet.CELL_NEIGHBOR_BOTTOM_LEFT_CORNER, TileSet.CELL_NEIGHBOR_LEFT_SIDE, TileSet.CELL_NEIGHBOR_TOP_LEFT_CORNER]
var failures: Array[String] = []
var checked_cells := 0
var report := {"engine": "", "patterns": {}, "context_patterns": {}, "exhaustive_cases": {}, "random_trials_per_family": 24, "incremental_orders_per_family": 3, "checked_cells": 0, "landing_cases": 0, "edit_actions": 0, "save_reload": false, "undo_redo": false, "seam_parallel_paths": false, "gpu_captures": [], "failures": []}
var atlases: Dictionary = {}
var sets: Dictionary = {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	report.engine = Engine.get_version_info().string
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(OUTPUT + "catalog.json"))
	if not parsed is Dictionary:
		push_error("catalog.json 尚未生产或格式错误")
		quit(2)
		return
	var catalog: Dictionary = parsed
	report.material_revision = catalog.get("material_revision","unrecorded")
	for atlas: Dictionary in catalog.atlases: atlases[atlas.id] = atlas
	for id in ["floor", "rim", "grate", "seam", "bridge", "facade", "floor_landing", "rim_landing", "facade_landing"]:
		if not atlases.has(id):
			push_error("缺少完整可铺刷 catalog 家族：" + id)
			quit(2)
			return
	for id: String in ["floor", "rim", "grate", "seam", "bridge", "facade"]:
		var tile_set := _make_tileset(atlases[id])
		if atlases.has(id + "_landing"):
			_add_context_source(tile_set, atlases[id + "_landing"])
		var path := OUTPUT + id + "_terrain_v001.tres"
		assert(ResourceSaver.save(tile_set, path) == OK)
		# 验收磁盘资源，避免内存正确而交付文件漏 source / terrain 的情况。
		sets[id] = ResourceLoader.load(path, "TileSet", ResourceLoader.CACHE_MODE_IGNORE)
		report.patterns[id] = atlases[id].tiles.size()
		# 立面只承诺派生同步，不冒充新增原生铺刷家族的穷举验收。
		if id != "facade": _test_native_family(id)
	var demo := _create_painter()
	demo.seed_demo()
	_test_painter(demo)
	# 初始布局保存为实际 TileMapLayer 数据，编辑器打开也能直接看到试铺。
	demo.seed_demo()
	var packed := PackedScene.new()
	assert(packed.pack(demo) == OK)
	assert(ResourceSaver.save(packed, SCENE_PATH) == OK)
	var reloaded_packed := ResourceLoader.load(SCENE_PATH,"PackedScene",ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	var reloaded_scene := reloaded_packed.instantiate() as Node2D
	root.add_child(reloaded_scene)
	_validate_painter(reloaded_scene,"saved scene resource reload")
	if JSON.stringify(reloaded_scene.snapshot()) != JSON.stringify(demo.snapshot()): _fail("Saved .tscn changed semantic layout")
	else: report.scene_resource_roundtrip = true
	reloaded_scene.free()
	if "--capture" in OS.get_cmdline_user_args():
		await _capture_demo(demo)
	report.checked_cells = checked_cells
	report.failures = failures
	report.status = "PASS" if failures.is_empty() else "FAIL"
	report.editor_sync = "@tool + editable layers changed signals + deferred stable fingerprint; Floor remains native source0, FloorLanding/Rim use ordinary context source1"
	var output := FileAccess.open(OUTPUT + "engine_validation.json", FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "\t") + "\n")
	print(JSON.stringify(report))
	demo.free()
	quit(0 if failures.is_empty() else 1)

func _make_tileset(atlas: Dictionary) -> TileSet:
	var tile_set := TileSet.new()
	tile_set.tile_size = Vector2i(32,32)
	tile_set.add_terrain_set()
	tile_set.set_terrain_set_mode(0, TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES if atlas.mode == "blob" else TileSet.TERRAIN_MODE_MATCH_SIDES)
	tile_set.add_terrain(0)
	tile_set.set_terrain_name(0,0,str(atlas.id).capitalize())
	tile_set.set_terrain_color(0,0,Color("63a39d"))
	var source := TileSetAtlasSource.new()
	# 直接读 RGBA PNG，打包为无损 ImageTexture，使 fresh 工程无需旧 .import。
	var pixels := _read_png(atlas.texture)
	assert(pixels != null and not pixels.is_empty())
	source.texture = ImageTexture.create_from_image(pixels)
	source.texture_region_size = Vector2i(32,32)
	source.use_texture_padding = true
	tile_set.add_source(source,0)
	for entry: Dictionary in atlas.tiles:
		var coord := Vector2i(int(entry.coord[0]), int(entry.coord[1]))
		source.create_tile(coord)
		var data := source.get_tile_data(coord,0)
		data.terrain_set = 0
		data.terrain = 0
		var step := 1 if atlas.mode == "blob" else 2
		for bit in range(0,8,step):
			data.set_terrain_peering_bit(PEERING[bit],0 if int(entry.mask) & (1 << (bit / step)) else -1)
	return tile_set

func _add_context_source(tile_set: TileSet, atlas: Dictionary) -> void:
	var source := TileSetAtlasSource.new()
	source.texture = ImageTexture.create_from_image(_read_png(atlas.texture))
	source.texture_region_size = Vector2i(32,32)
	source.use_texture_padding = true
	tile_set.add_source(source,1)
	for entry: Dictionary in atlas.tiles:
		source.create_tile(Vector2i(int(entry.coord[0]), int(entry.coord[1])))
		# 不赋 Terrain：这些图块由跨层 helper 根据 floor_mask + bridge_ports 选用。
	report.context_patterns[atlas.id] = atlas.tiles.size()

func _read_png(path: String) -> Image:
	# 构建时读 PNG 字节；资源内嵌像素，成品导出不依赖未导入的原始 Image 文件。
	var pixels := Image.new()
	assert(pixels.load_png_from_buffer(FileAccess.get_file_as_bytes(path)) == OK)
	return pixels

func _test_native_family(id: String) -> void:
	var atlas: Dictionary = atlases[id]
	var layer := TileMapLayer.new()
	layer.name = id
	layer.tile_set = sets[id]
	root.add_child(layer)
	var total := 256 if atlas.mode == "blob" else 16
	var step := 1 if atlas.mode == "blob" else 2
	for mask in range(total):
		layer.clear()
		var region: Array[Vector2i] = [Vector2i.ZERO]
		for bit in range(0,8,step):
			if mask & (1 << (bit / step)): region.append(DIRECTIONS[bit])
		layer.set_cells_terrain_connect(region,0,0,false)
		_check_native(layer, region, atlas.mode, "exhaustive " + str(mask))
	report.exhaustive_cases[id] = total
	var rng := RandomNumberGenerator.new()
	rng.seed = 20261006
	for trial in range(24):
		var region: Array[Vector2i] = []
		for y in range(12):
			for x in range(14):
				if rng.randf() < 0.58: region.append(Vector2i(x,y))
		layer.clear()
		layer.set_cells_terrain_connect(region,0,0,false)
		_check_native(layer,region,atlas.mode,"random " + str(trial))
		# 保留原层，实际 erase_cell 后重选存活邻格，检查动态擦除收口。
		var retained_count := region.size() / 2
		var removed: Array[Vector2i] = []
		for i in range(retained_count, region.size()):
			removed.append(region[i])
			layer.erase_cell(region[i])
		# erase_cell 只删除图块，不表达“这些端口改为 empty”的 Terrain 约束。
		# 显式重铺 empty terrain -1，使周围旧连接一并更新。
		layer.set_cells_terrain_connect(removed,0,-1,false)
		region.resize(retained_count)
		layer.set_cells_terrain_connect(region,0,0,false)
		_check_native(layer,region,atlas.mode,"erase " + str(trial))
	report.native_erase_contract = "erase_cell + set_cells_terrain_connect(removed,0,-1,false) + survivor reconnect; erase_cell alone does not rederive peering bits"
	var shape: Array[Vector2i] = []
	for y in range(6):
		for x in range(9):
			if not Rect2i(3,2,2,2).has_point(Vector2i(x,y)): shape.append(Vector2i(x,y))
	for order in range(3):
		var sequence := shape.duplicate()
		if order == 1: sequence.reverse()
		if order == 2:
			for i in range(sequence.size()):
				var j := rng.randi_range(i, sequence.size()-1)
				var temp: Vector2i = sequence[i]; sequence[i] = sequence[j]; sequence[j] = temp
		layer.clear()
		var built: Array[Vector2i] = []
		for cell: Vector2i in sequence:
			built.append(cell)
			layer.set_cells_terrain_connect([cell],0,0,false)
			_check_native(layer,built,atlas.mode,"incremental " + str(order))
	layer.free()

func _check_native(layer: TileMapLayer, cells: Array[Vector2i], mode: String, context: String) -> void:
	var occupied := {}
	for cell in cells: occupied[cell] = true
	if layer.get_used_cells().size() != cells.size(): _fail(str(layer.name) + " " + context + ": count mismatch")
	for cell in cells:
		var data := layer.get_cell_tile_data(cell)
		if data == null:
			_fail(str(layer.name) + " " + context + ": missing " + str(cell))
			continue
		checked_cells += 1
		for bit in range(0,8,1 if mode == "blob" else 2):
			var connects := occupied.has(cell + DIRECTIONS[bit])
			if bit % 2 == 1:
				connects = connects and occupied.has(cell + DIRECTIONS[(bit+7)%8]) and occupied.has(cell+DIRECTIONS[(bit+1)%8])
			if data.get_terrain_peering_bit(PEERING[bit]) != (0 if connects else -1):
				_fail(str(layer.name) + " " + context + ": wrong bit " + str(bit) + " at " + str(cell))

func _create_painter() -> Node2D:
	var scene := Node2D.new()
	scene.name = "PixelFloorSandboxV001"
	scene.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	scene.set_script(load(PAINTER_PATH))
	for id in ["floor_facade", "floor", "bridge", "floor_landing", "grate", "seam", "rim"]:
		var layer := TileMapLayer.new()
		layer.name = id.to_pascal_case()
		var family: String = "floor" if id == "floor_landing" else ("facade" if id == "floor_facade" else id)
		layer.tile_set = sets[family]
		if id == "floor_facade": layer.position = Vector2(0,16)
		scene.add_child(layer)
		layer.owner = scene
	if FileAccess.file_exists(OUTPUT + "details_tileset_v001.tres"):
		var details := TileMapLayer.new()
		details.name = "Details"
		details.tile_set = load(OUTPUT + "details_tileset_v001.tres")
		scene.add_child(details)
		details.owner = scene
	root.add_child(scene)
	return scene

func _test_painter(painter: Node2D) -> void:
	_validate_painter(painter, "initial demo")
	var rng := RandomNumberGenerator.new()
	rng.seed = 386271
	for action in range(128):
		painter.brush = painter.BRUSHES[action % painter.BRUSHES.size()]
		painter._detail_index = action % 8
		var before: Dictionary = painter.snapshot()
		painter.paint_cell(Vector2i(rng.randi_range(0,21),rng.randi_range(0,15)), action % 3 == 0)
		painter.commit_edit(before)
		_validate_painter(painter, "edit " + str(action))
		report.edit_actions += 1
	var after_edit: String = JSON.stringify(painter.snapshot())
	painter.undo_edit()
	_validate_painter(painter, "undo")
	painter.redo_edit()
	_validate_painter(painter, "redo")
	if JSON.stringify(painter.snapshot()) != after_edit: _fail("Undo/redo changed semantic layout")
	else: report.undo_redo = true
	var save_path := OUTPUT + "validation_layout_v001.json"
	if painter.save_layout(save_path) != OK: _fail("Layout save failed")
	painter.seed_demo()
	if painter.load_layout(save_path) != OK: _fail("Layout reload failed")
	_validate_painter(painter, "save reload")
	if JSON.stringify(painter.snapshot()) != after_edit: _fail("Save/reload changed semantic layout")
	else: report.save_reload = true
	_test_landing_contexts(painter)
	_test_parallel_seams(painter)
	_test_overlay_pruning(painter)
	_test_layer_adoption(painter)
	_test_details(painter)

func _validate_painter(painter: Node2D, context: String) -> void:
	var state: Dictionary = painter.occupied
	var walkable: Dictionary = state.floor.duplicate()
	for cell in state.bridge: walkable[cell] = true
	for id in ["floor", "rim"]:
		var layer: TileMapLayer = painter._layer(id)
		if layer.get_used_cells().size() != state.floor.size(): _fail(context + " " + id + ": stale occupied cells")
		for cell: Vector2i in state.floor:
			var floor_mask: int = painter._normalized_blob_mask(cell,state.floor)
			var ports: int = painter._sides_mask(cell,state.bridge)
			var source_id := 1 if ports and id == "rim" else 0
			var expected: Vector2i = painter.atlas_lookup[id + "_landing"]["%d:%d" % [floor_mask,ports]] if ports and id == "rim" else painter.atlas_lookup[id][floor_mask]
			if layer.get_cell_source_id(cell) != source_id or layer.get_cell_atlas_coords(cell) != expected:
				_fail(context + " " + id + ": wrong landing mask at " + str(cell))
			checked_cells += 1
	for id in ["grate", "seam", "bridge"]:
		# 下列是独立功能层；FloorLanding 则只在真实桥口存在。
		var layer: TileMapLayer = painter._layer(id)
		if layer.get_used_cells().size() != state[id].size(): _fail(context + " " + id + ": stale occupied cells")
		for cell: Vector2i in state[id]:
			var mask := 0
			if id == "grate": mask = painter._normalized_blob_mask(cell,state.grate)
			elif id == "bridge": mask = painter._sides_mask(cell,walkable)
			else:
				for bit in range(4):
					if painter.seam_edges.has(painter._edge_key(cell,cell+DIRECTIONS[bit*2])): mask |= 1 << bit
			if layer.get_cell_atlas_coords(cell) != painter.atlas_lookup[id][mask]: _fail(context + " " + id + ": wrong selected mask")
			if id in ["grate", "seam"] and not state.floor.has(cell): _fail(context + ": overlay outside floor")
			checked_cells += 1
	var details_layer: TileMapLayer = painter._layer("details")
	var landing_layer: TileMapLayer = painter._layer("floor_landing")
	var facade_layer: TileMapLayer = painter._layer("floor_facade")
	if facade_layer.position != Vector2(0,16): _fail(context + ": facade projection offset differs from 16px")
	if facade_layer.get_index() > painter._layer("floor").get_index() or facade_layer.get_index() > painter._layer("bridge").get_index(): _fail(context + ": facade is drawn over the floor/bridge")
	if facade_layer.get_used_cells().size() != state.floor.size(): _fail(context + ": stale FloorFacade occupied cells")
	for cell: Vector2i in state.floor:
		var ports: int = painter._sides_mask(cell,state.bridge)
		var floor_mask: int = painter._normalized_blob_mask(cell,state.floor)
		var expected: Vector2i = painter.atlas_lookup.facade_landing["%d:%d" % [floor_mask,ports]] if ports else painter.atlas_lookup.facade[floor_mask]
		if facade_layer.get_cell_source_id(cell) != (1 if ports else 0) or facade_layer.get_cell_atlas_coords(cell) != expected: _fail(context + ": wrong FloorFacade mask/context")
		checked_cells += 1
	report.facade_derived_sync = "PASS; floor masks, bridge ports, floor erase, bridge erase, undo/redo, save/reload and scene roundtrip; not an independently painted Terrain family"
	var landing_cells := 0
	for cell: Vector2i in state.floor:
		var ports: int = painter._sides_mask(cell,state.bridge)
		if ports == 0:
			if landing_layer.get_cell_source_id(cell) != -1: _fail(context + ": stale FloorLanding context")
			continue
		landing_cells += 1
		var floor_mask: int = painter._normalized_blob_mask(cell,state.floor)
		var expected: Vector2i = painter.atlas_lookup.floor_landing["%d:%d" % [floor_mask,ports]]
		if landing_layer.get_cell_source_id(cell) != 1 or landing_layer.get_cell_atlas_coords(cell) != expected: _fail(context + ": wrong FloorLanding context")
		checked_cells += 1
	if landing_layer.get_used_cells().size() != landing_cells: _fail(context + ": FloorLanding occupancy mismatch")
	if details_layer.get_used_cells().size() != state.details.size(): _fail(context + ": stale decoration cells")
	for cell: Vector2i in state.details:
		if not state.floor.has(cell): _fail(context + ": decoration outside floor")
		if details_layer.get_cell_atlas_coords(cell) != Vector2i(int(state.details[cell]),0): _fail(context + ": wrong decoration slot")
		checked_cells += 1

func _empty_state() -> Dictionary:
	return {"version":1,"tile_size":32,"occupied":{"floor":[],"grate":[],"seam":[],"bridge":[]},"seam_edges":[]}

func _test_landing_contexts(painter: Node2D) -> void:
	if not atlases.has("floor_landing"):
		_fail("Landing catalog missing")
		return
	var center := Vector2i(7,7)
	for entry: Dictionary in atlases.floor_landing.tiles:
		var state := _empty_state()
		state.occupied.floor.append([center.x,center.y])
		for bit in range(8):
			if int(entry.floor_mask) & (1 << bit):
				var cell: Vector2i = center + DIRECTIONS[bit]
				state.occupied.floor.append([cell.x,cell.y])
		for bit in range(4):
			if int(entry.bridge_ports) & (1 << bit):
				var cell: Vector2i = center + DIRECTIONS[bit*2]
				state.occupied.bridge.append([cell.x,cell.y])
		painter.restore_snapshot(state)
		_validate_painter(painter,"landing context " + str(entry.floor_mask) + ":" + str(entry.bridge_ports))
		report.landing_cases += 1
		# 擦除全部桥，原来 source 1 的落桥格必须自动复原 source 0 闭边。
		painter.brush = "bridge"
		for point in state.occupied.bridge: painter.paint_cell(Vector2i(int(point[0]),int(point[1])),true)
		_validate_painter(painter,"landing erase")
		if painter._layer("floor_landing").get_cell_source_id(center) != -1 or painter._layer("rim").get_cell_source_id(center) != 0: _fail("Landing closure not restored after erase")

func _test_parallel_seams(painter: Node2D) -> void:
	var state := _empty_state()
	for y in range(4,8):
		for x in range(4,10): state.occupied.floor.append([x,y])
	painter.restore_snapshot(state)
	painter.brush = "seam"
	for y in [5,6]:
		var previous := Vector2i(9999,9999)
		for x in range(5,9):
			var cell := Vector2i(x,y)
			painter.paint_cell(cell,false,previous)
			previous = cell
	_validate_painter(painter,"parallel seam paths")
	for x in range(5,9):
		if painter.seam_edges.has(painter._edge_key(Vector2i(x,5),Vector2i(x,6))): _fail("Adjacent seam strokes unexpectedly connected")
	var before: Dictionary = painter.snapshot()
	painter._adopt_layer_occupancy()
	painter._rebuild_all()
	if JSON.stringify(painter.snapshot()) != JSON.stringify(before): _fail("Layer adoption changed explicit parallel seam paths")
	report.seam_parallel_paths = true

func _test_overlay_pruning(painter: Node2D) -> void:
	for reverse_order in [false,true]:
		var state := _empty_state()
		state.occupied.floor = [[7,7],[8,7]]
		state.occupied.grate = [[8,7],[7,7]] if reverse_order else [[7,7],[8,7]]
		state.occupied.seam = [[8,7],[7,7]] if reverse_order else [[7,7],[8,7]]
		state.seam_edges = ["7,7:8,7"]
		painter.restore_snapshot(state)
		painter.brush = "floor"
		painter.paint_cell(Vector2i(8,7),true)
		_validate_painter(painter,"overlay floor clipping")
		if painter._layer("grate").get_cell_atlas_coords(Vector2i(7,7)) != painter.atlas_lookup.grate[0]: _fail("Grate retained stale edge after floor erase")
		if painter._layer("seam").get_cell_atlas_coords(Vector2i(7,7)) != painter.atlas_lookup.seam[0]: _fail("Seam retained stale edge after floor erase")
	report.overlay_pruning = "PASS; both insertion orders"

func _test_layer_adoption(painter: Node2D) -> void:
	var state := _empty_state()
	state.occupied.floor = [[7,7],[7,8]]
	state.occupied.bridge = [[8,7],[9,7]]
	painter.restore_snapshot(state)
	# 只刷派生 source1 落桥格旁的一个新地板格，不显式把落桥地板加入输入。
	# Floor 的 source0 身份使 native API 不会把 FloorLanding 的普通图块当 empty。
	var floor_layer: TileMapLayer = painter._layer("floor")
	floor_layer.set_cells_terrain_connect([Vector2i(6,7)],0,0,false)
	var neighbor_paint_kept_landing := floor_layer.get_cell_source_id(Vector2i(7,7)) >= 0
	painter._adopt_layer_occupancy()
	painter._rebuild_all()
	if not painter.occupied.floor.has(Vector2i(7,7)): _fail("Native neighboring floor paint removed landing occupancy")
	_validate_painter(painter,"native single neighbor paint")
	floor_layer.erase_cell(Vector2i(6,7))
	var survivors := floor_layer.get_used_cells()
	floor_layer.set_cells_terrain_connect(survivors,0,0,false)
	var neighbor_erase_kept_landing := floor_layer.get_cell_source_id(Vector2i(7,7)) >= 0
	painter._adopt_layer_occupancy()
	painter._rebuild_all()
	if not painter.occupied.floor.has(Vector2i(7,7)): _fail("Native neighboring floor erase removed landing occupancy")
	_validate_painter(painter,"native neighbor erase and survivor reconnect")
	report.native_landing_neighbor_edit = {"paint_kept_floor":neighbor_paint_kept_landing,"erase_kept_floor":neighbor_erase_kept_landing}
	painter.restore_snapshot(state)
	# 模拟编辑器重刷：Floor仍是source0，派生落桥source1由同一占用自动保留。
	floor_layer.set_cells_terrain_connect([Vector2i(7,7),Vector2i(7,8)],0,0,false)
	painter._adopt_layer_occupancy()
	painter._rebuild_all()
	_validate_painter(painter,"native repaint followed by helper adoption")
	if floor_layer.get_cell_source_id(Vector2i(7,7)) != 0 or painter._layer("floor_landing").get_cell_source_id(Vector2i(7,7)) != 1: _fail("Landing lost after native Terrain repaint")
	# 编辑器 / 外部 JSON 的同格重叠也归一为 floor 优先。
	painter._layer("bridge").set_cell(Vector2i(7,7),0,painter.atlas_lookup.bridge[0])
	painter._adopt_layer_occupancy()
	painter._rebuild_all()
	_validate_painter(painter,"editor overlap adoption")
	if painter.occupied.bridge.has(Vector2i(7,7)): _fail("Editor adoption retained floor/bridge overlap")
	state.occupied.bridge = [[7,7],[8,7]]
	painter.restore_snapshot(state)
	_validate_painter(painter,"overlapping layout reload")
	if painter.occupied.bridge.has(Vector2i(7,7)): _fail("Layout reload retained floor/bridge overlap")
	painter.brush = "floor"
	painter.paint_cell(Vector2i(8,7))
	_validate_painter(painter,"floor overwrites bridge")
	report.layer_sync_simulation = "PASS; native repaint, layer adoption, overlap reload, floor overwrite; actual editor UI UndoRedo not exercised"

func _test_details(painter: Node2D) -> void:
	var state := _empty_state()
	for y in range(3,7):
		for x in range(3,9): state.occupied.floor.append([x,y])
	painter.restore_snapshot(state)
	var before: Dictionary = painter.snapshot()
	painter.brush = "details"
	for index in range(8):
		painter._detail_index = index
		painter.paint_cell(Vector2i(4+index%4,4+index/4))
	painter.commit_edit(before)
	_validate_painter(painter,"all 8 decoration slots")
	var saved: String = JSON.stringify(painter.snapshot())
	painter.undo_edit()
	if not painter.occupied.details.is_empty(): _fail("Decoration undo retained cells")
	painter.redo_edit()
	if JSON.stringify(painter.snapshot()) != saved: _fail("Decoration redo lost slots")
	var path := "user://pixel_floor_details_validation_v001.json"
	if painter.save_layout(path) != OK: _fail("Decoration save failed")
	painter.restore_snapshot(state)
	if painter.load_layout(path) != OK or JSON.stringify(painter.snapshot()) != saved: _fail("Decoration reload lost slots")
	painter.brush = "floor"
	painter.paint_cell(Vector2i(4,4),true)
	_validate_painter(painter,"decoration floor clipping")
	if painter.occupied.details.has(Vector2i(4,4)): _fail("Decoration survived erase of supporting floor")
	report.details_slots = 8
	report.details_edits = "PASS; paint, undo, redo, save, reload, supporting floor erase"

func _capture_demo(painter: Node2D) -> void:
	# 含 HUD 的真实 GPU 画面；CPU atlas 拼图不冒充引擎采样验收。
	root.size = Vector2i(1152,880)
	root.content_scale_size = Vector2i(1152,880)
	for level in [1,2,4]:
		painter.set_zoom(level)
		if level > 1: painter._camera.position = Vector2(14*32,6*32)
		await process_frame
		await RenderingServer.frame_post_draw
		var relative := "gpu_sandbox_%dx_v001.png" % level
		var pixels := root.get_texture().get_image()
		if pixels == null or pixels.is_empty():
			_fail("GPU viewport readback empty")
			continue
		if pixels.save_png(OUTPUT + relative) != OK: _fail("GPU capture save failed")
		report.gpu_captures.append({"path":relative,"zoom":level,"size":[pixels.get_width(),pixels.get_height()],"renderer":RenderingServer.get_current_rendering_method()})
	# 单独验证 4 朝向的 24px 桥口和两侧 4px 肩口，含最易漏掉的边梁交点。
	var state := _empty_state()
	var centers := [Vector2i(5,4),Vector2i(15,4),Vector2i(5,12),Vector2i(15,12)]
	for direction_index in range(4):
		var center: Vector2i = centers[direction_index]
		var direction: Vector2i = DIRECTIONS[direction_index*2]
		var tangent := Vector2i(-direction.y,direction.x)
		for depth in range(3):
			for width in range(-2,3):
				var cell := center - direction*depth + tangent*width
				state.occupied.floor.append([cell.x,cell.y])
		for distance in range(1,4):
			var cell := center + direction*distance
			state.occupied.bridge.append([cell.x,cell.y])
	painter.restore_snapshot(state)
	_validate_painter(painter,"GPU four direction landing layout")
	painter.set_zoom(1)
	painter._camera.position = Vector2(352,196)
	painter._update_status("北／东／南／西落桥：中央24px开放＋4px肩口")
	await process_frame
	await RenderingServer.frame_post_draw
	var landing_path := "gpu_landing_four_directions_v001.png"
	root.get_texture().get_image().save_png(OUTPUT + landing_path)
	report.gpu_captures.append({"path":landing_path,"zoom":1,"renderer":RenderingServer.get_current_rendering_method()})
	for direction_index in range(4):
		painter.set_zoom(4)
		painter._camera.position = Vector2(centers[direction_index] * 32 + Vector2i(16,16))
		await process_frame
		await RenderingServer.frame_post_draw
		var relative := "gpu_landing_%s_4x_v001.png" % ["north","east","south","west"][direction_index]
		root.get_texture().get_image().save_png(OUTPUT + relative)
		report.gpu_captures.append({"path":relative,"zoom":4,"renderer":RenderingServer.get_current_rendering_method()})

func _fail(message: String) -> void:
	if failures.size() < 80: failures.append(message)
