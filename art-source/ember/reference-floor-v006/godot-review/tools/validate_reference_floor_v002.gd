extends SceneTree
## 独立验收 v002 艺术瓦片包。只读取生产 atlas / TileSet，不替生产器重建资源。
## 逻辑格 32 world，源纹理格 128，TileMapLayer 必须缩放 0.25。
## 本脚本的 PASS 仅代表结构与拼接验证，不代表用户接受了美术风格。
## godot --headless --path <isolated-project> --script res://tools/validate_reference_floor_v002.gd

const OUTPUT := "res://assets/ember/environment/reference_floor_v002/"
const DIRECTIONS := [Vector2i.UP, Vector2i(1,-1), Vector2i.RIGHT, Vector2i(1,1), Vector2i.DOWN, Vector2i(-1,1), Vector2i.LEFT, Vector2i(-1,-1)]
const PEERING := [TileSet.CELL_NEIGHBOR_TOP_SIDE, TileSet.CELL_NEIGHBOR_TOP_RIGHT_CORNER, TileSet.CELL_NEIGHBOR_RIGHT_SIDE, TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER, TileSet.CELL_NEIGHBOR_BOTTOM_SIDE, TileSet.CELL_NEIGHBOR_BOTTOM_LEFT_CORNER, TileSet.CELL_NEIGHBOR_LEFT_SIDE, TileSet.CELL_NEIGHBOR_TOP_LEFT_CORNER]
const TEXTURE_TILE := 128
const WORLD_TILE := 32
const LAYER_SCALE := 0.25

var failures: Array[String] = []
var checked_cells := 0
var atlases: Dictionary = {}
var sets: Dictionary = {}
var report: Dictionary = {
	"scope": "Independent structural verification. User visual acceptance is not inferred.",
	"engine": "", "normalized_masks": 0, "native_families": {},
	"checked_cells": 0, "native_erase": false,
	"runtime_checks": {}, "scene_resource_roundtrip": false,
	"editor_gui_undo_redo": "NOT_TESTED", "failures": []
}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	report.engine = Engine.get_version_info().string
	_test_normalization()
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(OUTPUT + "catalog.json"))
	if not parsed is Dictionary:
		_fail("Production catalog.json is missing or invalid; an image sample is not a brushable TileSet.")
		_finish()
		return
	for entry: Dictionary in parsed.get("atlases", []):
		atlases[str(entry.id)] = entry
	for id in ["floor", "bridge"]:
		if not atlases.has(id):
			_fail("Missing native Terrain family: " + id)
			continue
		_test_catalog(id)
		var path: String = OUTPUT + str(id) + "_terrain_v002.tres"
		var loaded := ResourceLoader.load(path, "TileSet", ResourceLoader.CACHE_MODE_IGNORE)
		if not loaded is TileSet:
			_fail("TileSet cannot reload from disk: " + path)
			continue
		sets[id] = loaded
		_test_tileset(id)
		_test_native_family(id)
	await _test_runtime()
	_finish()


func _normalized(mask: int) -> int:
	# 对角关系只能在相邻的两个正交格均有占用时成立。
	for diagonal in [1, 3, 5, 7]:
		if not (mask & (1 << ((diagonal + 7) % 8))) or not (mask & (1 << ((diagonal + 1) % 8))):
			mask &= ~(1 << diagonal)
	return mask


func _mask(cell: Vector2i, occupied: Dictionary) -> int:
	var raw := 0
	for bit in range(8):
		if occupied.has(cell + DIRECTIONS[bit]): raw |= 1 << bit
	return _normalized(raw)


func _test_normalization() -> void:
	var masks := {}
	for raw in range(256):
		var normalized := _normalized(raw)
		masks[normalized] = true
		if _normalized(normalized) != normalized: _fail("Non-idempotent normalization: " + str(raw))
	report.normalized_masks = masks.size()
	if masks.size() != 47: _fail("Eight-neighbor normalization must produce exactly 47 masks.")
	# 与项目规范只核对拓扑约定。旧规范的32px尺寸不冒充v002的128px实际纹理。
	var spec_path := "res://docs/shader-learning/autotile-neighborhoods-v002.json"
	if FileAccess.file_exists(spec_path):
		var specification = JSON.parse_string(FileAccess.get_file_as_string(spec_path))
		if specification is Dictionary:
			var specification_masks := {}
			for tile: Dictionary in specification.area.tiles:
				specification_masks[int(tile.mask)] = true
			if specification_masks.size() != 47: _fail("Project neighborhood specification does not contain 47 masks.")
			for mask_value: int in masks:
				if not specification_masks.has(mask_value): _fail("Production topology differs from project specification: " + str(mask_value))
			report.specification_mask_crosscheck = true


func _test_catalog(id: String) -> void:
	var atlas: Dictionary = atlases[id]
	if str(atlas.get("mode", "")) != "blob": _fail(id + " is required to be an area47 blob family.")
	var texture_path := str(atlas.get("texture", ""))
	var pixels := Image.load_from_file(ProjectSettings.globalize_path(texture_path))
	if pixels == null or pixels.is_empty():
		_fail(id + " production atlas PNG cannot load: " + texture_path)
		return
	var masks := {}
	var coordinates := {}
	for entry: Dictionary in atlas.get("tiles", []):
		var mask_value := int(entry.mask)
		var coord := Vector2i(int(entry.coord[0]), int(entry.coord[1]))
		if mask_value != _normalized(mask_value): _fail(id + " includes unnormalized mask " + str(mask_value))
		if masks.has(mask_value): _fail(id + " duplicate normalized mask " + str(mask_value))
		if coordinates.has(coord): _fail(id + " duplicate atlas coordinate " + str(coord))
		masks[mask_value] = true
		coordinates[coord] = true
		var region := Rect2i(coord * TEXTURE_TILE, Vector2i(TEXTURE_TILE, TEXTURE_TILE))
		if not Rect2i(Vector2i.ZERO, pixels.get_size()).encloses(region):
			_fail(id + " catalog coordinate outside PNG: " + str(coord))
			continue
		# 每种地形必须真正存在可见顶面，避免透明tile只有Terrain元数据。
		if pixels.get_pixelv(region.position + Vector2i(TEXTURE_TILE / 2, TEXTURE_TILE / 2)).a < 0.9:
			_fail(id + " opaque deck center missing for mask " + str(mask_value))
	if masks.size() != 47: _fail(id + " must cover all 47 normalized masks; got " + str(masks.size()))
	report.native_families[id] = {"catalog_masks": masks.size(), "png_size": [pixels.get_width(), pixels.get_height()], "resource_reload": false}


func _test_tileset(id: String) -> void:
	var tile_set: TileSet = sets[id]
	if tile_set.tile_size != Vector2i(TEXTURE_TILE, TEXTURE_TILE):
		_fail(id + " TileSet.tile_size must be128; scale0.25 gives32world.")
	if tile_set.get_terrain_sets_count() < 1 or tile_set.get_terrains_count(0) < 1:
		_fail(id + " lacks terrain set0 / terrain0.")
		return
	if tile_set.get_terrain_set_mode(0) != TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES:
		_fail(id + " Terrain is not Match Corners and Sides.")
	if not tile_set.has_source(0):
		_fail(id + " lacks native source0.")
		return
	var source := tile_set.get_source(0) as TileSetAtlasSource
	if source == null:
		_fail(id + " source0 is not an atlas source.")
		return
	if source.texture_region_size != Vector2i(TEXTURE_TILE, TEXTURE_TILE):
		_fail(id + " source texture_region_size differs from128.")
	for entry: Dictionary in atlases[id].tiles:
		var coord := Vector2i(int(entry.coord[0]), int(entry.coord[1]))
		if not source.has_tile(coord):
			_fail(id + " catalog tile absent from resource: " + str(coord))
			continue
		var data := source.get_tile_data(coord, 0)
		if data.terrain_set != 0 or data.terrain != 0: _fail(id + " tile missing center Terrain identity.")
		for bit in range(8):
			var expected := 0 if int(entry.mask) & (1 << bit) else -1
			if data.get_terrain_peering_bit(PEERING[bit]) != expected:
				_fail(id + " wrong catalog peering bit " + str(bit) + " at " + str(coord))
	if report.native_families.has(id): report.native_families[id].resource_reload = true


func _test_native_family(id: String) -> void:
	var layer := TileMapLayer.new()
	layer.name = id
	layer.tile_set = sets[id]
	layer.scale = Vector2(LAYER_SCALE, LAYER_SCALE)
	root.add_child(layer)
	var world_delta := (layer.map_to_local(Vector2i.RIGHT) - layer.map_to_local(Vector2i.ZERO)) * layer.scale
	if world_delta != Vector2(WORLD_TILE, 0): _fail(id + " map_to_local world spacing differs from32.")
	for raw in range(256):
		layer.clear()
		var cells: Array[Vector2i] = [Vector2i.ZERO]
		for bit in range(8):
			if raw & (1 << bit): cells.append(DIRECTIONS[bit])
		layer.set_cells_terrain_connect(cells, 0, 0, false)
		_check_native(layer, cells, "exhaustive " + str(raw))
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026100602
	for trial in range(12):
		var cells: Array[Vector2i] = []
		for y in range(12):
			for x in range(14):
				if rng.randf() < 0.6: cells.append(Vector2i(x, y))
		layer.clear()
		layer.set_cells_terrain_connect(cells, 0, 0, false)
		_check_native(layer, cells, "random " + str(trial))
		var keep_count := int(cells.size() / 2)
		var removed: Array[Vector2i] = []
		for index in range(keep_count, cells.size()):
			removed.append(cells[index])
			layer.erase_cell(cells[index])
		# erase_cell 本身不重新求Terrain。明确把被擦格约束成 empty，再更新存活格。
		layer.set_cells_terrain_connect(removed, 0, -1, false)
		cells.resize(keep_count)
		layer.set_cells_terrain_connect(cells, 0, 0, false)
		_check_native(layer, cells, "erase " + str(trial))
	var shape: Array[Vector2i] = []
	for y in range(8):
		for x in range(10):
			if not Rect2i(3, 2, 3, 3).has_point(Vector2i(x,y)): shape.append(Vector2i(x,y))
	# 两个仅对角接触的单格保持四向分离，兼顾孤岛与凸角。
	shape.append(Vector2i(12,2))
	shape.append(Vector2i(13,3))
	for order in range(3):
		var sequence := shape.duplicate()
		if order == 1: sequence.reverse()
		if order == 2:
			for index in range(sequence.size()):
				var other := rng.randi_range(index, sequence.size() - 1)
				var temporary: Vector2i = sequence[index]
				sequence[index] = sequence[other]
				sequence[other] = temporary
		layer.clear()
		var built: Array[Vector2i] = []
		for cell: Vector2i in sequence:
			built.append(cell)
			layer.set_cells_terrain_connect([cell], 0, 0, false)
			_check_native(layer, built, "incremental " + str(order))
	if report.native_families.has(id):
		report.native_families[id].exhaustive_raw_neighborhoods = 256
		report.native_families[id].random_paint_erase_trials = 12
		report.native_families[id].incremental_orders = 3
	report.native_erase = true
	layer.free()


func _check_native(layer: TileMapLayer, cells: Array[Vector2i], context: String) -> void:
	var occupied := {}
	for cell: Vector2i in cells: occupied[cell] = true
	if layer.get_used_cells().size() != cells.size(): _fail(str(layer.name) + " " + context + " occupancy count mismatch.")
	for cell: Vector2i in cells:
		var data := layer.get_cell_tile_data(cell)
		if data == null:
			_fail(str(layer.name) + " " + context + " missing tile " + str(cell))
			continue
		checked_cells += 1
		var expected_mask := _mask(cell, occupied)
		if data.terrain != 0 or data.terrain_set != 0: _fail(str(layer.name) + " " + context + " center Terrain mismatch.")
		for bit in range(8):
			if data.get_terrain_peering_bit(PEERING[bit]) != (0 if expected_mask & (1 << bit) else -1):
				_fail(str(layer.name) + " " + context + " wrong bit " + str(bit) + " at " + str(cell))


func _test_runtime() -> void:
	var compiler_path := "res://scripts/ember/reference_floor_compiler_v002.gd"
	if not FileAccess.file_exists(compiler_path):
		report.runtime_checks.status = "PENDING_PRODUCTION_INTERFACE"
		await process_frame
		return
	var compiler_script = load(compiler_path)
	if compiler_script == null:
		_fail("Artist coverage compiler cannot load.")
		return
	var compiler = compiler_script.new()
	compiler.load_materials()
	for material_id in ["floor_albedo_period", "water_artist_period", "north_cap_source", "south_cap_source", "east_cap_source", "south_face_source", "east_face_source", "bridge_horizontal_artist", "bridge_vertical_artist"]:
		if not compiler.materials.has(material_id):
			_fail("Compiler production module is missing: " + material_id)
	if not failures.is_empty(): return
	_test_four_landings(compiler)
	_test_bridge_shapes(compiler)
	report.runtime_checks.compiler_footprints = true
	# painter磁盘接口独立验收，不能由compiler的PASS代替真实编辑入口。
	var painter_path := "res://scripts/ember/reference_floor_painter_v002.gd"
	if not FileAccess.file_exists(painter_path):
		report.runtime_checks.status = "PENDING_PAINTER_INTERFACE"
		await process_frame
		return
	if sets.size() != 2:
		_fail("Runtime verification requires both saved native TileSets.")
		return
	await _test_painter(painter_path)
	await _test_production_cache()
	report.runtime_checks.status = "PASS" if failures.is_empty() else "FAIL"


func _test_production_cache() -> void:
	# 初始production scene读取外部PNG缓存，与空fixture首建是两条独立路径。
	var scene_path := "res://scenes/ember/reference_floor_sandbox_v002.tscn"
	var packed := ResourceLoader.load(scene_path,"PackedScene",ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	if packed == null:
		_fail("Saved production sandbox cannot load for warm-cache verification.")
		return
	var painter := packed.instantiate() as Node2D
	var started := Time.get_ticks_msec()
	root.add_child(painter)
	var warm_ready: bool = painter.last_build.has("coverage") and painter.last_build.has("heads")
	report.runtime_checks.production_warm_cache_loaded = warm_ready
	report.runtime_checks.production_warm_cache_load_ms = Time.get_ticks_msec()-started
	if not warm_ready:
		_fail("Production initial layout cannot immediately restore its matching raw-PNG cache.")
		await process_frame
		await process_frame
	var previous := {}
	for id in ["water", "facade", "floor", "rim", "bridge", "heads"]:
		previous[id] = painter.last_build[id].duplicate()
	if not painter.floor_cells.has(Vector2i(12,3)):
		_fail("Production warm-cache edit fixture does not target an actual floor cell.")
	else:
		painter.erase_cell(Vector2i(12,3))
		painter.synchronize()
		_validate_painter(painter,"production warm-cache first dirty erase")
		var dirty: Rect2i = painter.last_dirty_bounds
		var excluded := Rect2i((dirty.position-painter.bounds_cells.position)*TEXTURE_TILE,dirty.size*TEXTURE_TILE)
		var outside_unchanged := _outside_hash(previous,excluded) == _outside_hash(painter.last_build,excluded)
		if not outside_unchanged: _fail("Production warm-cache dirty edit changes pixels outside its declared region.")
		var compiler_script = load("res://scripts/ember/reference_floor_compiler_v002.gd")
		var compiler = compiler_script.new()
		var full_started := Time.get_ticks_msec()
		var full_images: Dictionary = compiler.build_visual_layers(painter.floor_cells,painter.bridge_cells,painter.bounds_cells)
		var full_ms := Time.get_ticks_msec()-full_started
		var matches := _visual_hash(full_images) == _visual_hash(painter.last_build)
		if not matches: _fail("Production warm-cache first dirty edit differs from fresh full-domain RGBA compilation.")
		report.runtime_checks.production_warm_first_dirty_vs_full_rgba = matches
		report.runtime_checks.production_warm_dirty_outside_unchanged = outside_unchanged
		report.runtime_checks.production_warm_dirty_rebuild_ms = painter.last_rebuild_ms
		report.runtime_checks.production_full_fresh_rebuild_ms = full_ms
	painter.free()
	await process_frame


func _test_painter(painter_path: String) -> void:
	var painter := Node2D.new()
	painter.name = "IndependentReferenceFloorPainter"
	painter.set_script(load(painter_path))
	painter.bounds_cells = Rect2i(0,0,6,6)
	for id in ["floor", "bridge"]:
		var layer := TileMapLayer.new()
		layer.name = str(id).capitalize()
		layer.tile_set = sets[id]
		layer.scale = Vector2(LAYER_SCALE,LAYER_SCALE)
		painter.add_child(layer)
		layer.owner = painter
	# 与用户重新打开仅保存输入的场景一致：context由synchronize创建。
	# _ready排队的重建在下方首次同步后会命中无修改路径，不重复编译。
	root.add_child(painter)
	# 等_ready的延后编译完成再模拟用户输入，避免测试在首帧前抢写原生层。
	await process_frame
	await process_frame
	var before: Dictionary = painter.snapshot()
	for cell in [Vector2i(2,0),Vector2i(3,0),Vector2i(2,1),Vector2i(3,1)]: painter.paint_floor(cell)
	painter.paint_bridge(Vector2i(2,2))
	if painter.bridge_cells.size() != 4: _fail("Default bridge brush does not create a2x2 stamp.")
	painter.synchronize()
	painter.commit_edit(before)
	_validate_painter(painter,"default2x2 brush")
	var painted: String = JSON.stringify(painter.snapshot())
	var visual_hash := _visual_hash(painter.last_build)
	report.runtime_checks.measured_rebuild_ms = [painter.last_rebuild_ms]
	if not painter.undo_edit(): _fail("Runtime undo did not apply.")
	_validate_painter(painter,"undo")
	if JSON.stringify(painter.snapshot()) != JSON.stringify(before): _fail("Runtime undo changed the initial semantic layout.")
	if not painter.redo_edit(): _fail("Runtime redo did not apply.")
	_validate_painter(painter,"redo")
	if JSON.stringify(painter.snapshot()) != painted or _visual_hash(painter.last_build) != visual_hash:
		_fail("Runtime redo does not restore both semantic layout and artist pixels.")
	report.runtime_checks.undo_redo = true
	var layout_path := OUTPUT + "independent_layout_roundtrip_v002.json"
	if not painter.save_layout(layout_path): _fail("Runtime layout save failed.")
	for y in range(2):
		for x in range(2): painter.erase_cell(Vector2i(2+x,2+y))
	painter.synchronize()
	_validate_painter(painter,"erase2x2 bridge")
	if not painter.bridge_cells.is_empty(): _fail("Erasing a2x2 bridge leaves stale semantic cells.")
	var rim: Image = painter.last_build.rim
	var facade: Image = painter.last_build.facade
	if rim.get_pixel(3*TEXTURE_TILE,2*TEXTURE_TILE-1).a < 0.9: _fail("Coping does not close after bridge erase.")
	if facade.get_pixel(3*TEXTURE_TILE,2*TEXTURE_TILE+16).a < 0.9: _fail("South retaining face does not close after bridge erase.")
	if not painter.load_layout(layout_path): _fail("Runtime layout reload failed.")
	_validate_painter(painter,"layout reload")
	if JSON.stringify(painter.snapshot()) != painted or _visual_hash(painter.last_build) != visual_hash:
		_fail("Layout reload changed semantic data or artist pixels.")
	report.runtime_checks.layout_roundtrip = true
	# 真正修改原生输入层，让changed debounce自动采纳；不手动代替其同步入口。
	var floor_layer := painter.get_node("Floor") as TileMapLayer
	var native_started := Time.get_ticks_msec()
	floor_layer.set_cells_terrain_connect([Vector2i(2,2)],0,0,false)
	print("Native immediate state: ", {"processing":painter.is_processing(),"pending":painter._pending,"writing":painter._writing,"refresh":painter.refresh_in_editor,"signal_connected":floor_layer.changed.is_connected(Callable(painter,"_input_changed")),"native_floor_cells":floor_layer.get_used_cells().size(),"semantic_floor_cells":painter.floor_cells.size()})
	for attempt in range(30):
		await create_timer(0.05).timeout
		await process_frame
		# 轮询先采纳占用、debounce后再编图；必须等渲染指纹也追上新语义。
		if painter.floor_cells.has(Vector2i(2,2)) and not painter.bridge_cells.has(Vector2i(2,2)) and not painter._pending and painter._fingerprint == JSON.stringify(painter.snapshot()): break
	print("Native settled state: ", {"processing":painter.is_processing(),"pending":painter._pending,"changed_age_ms":Time.get_ticks_msec()-painter._changed_at,"elapsed_ms":Time.get_ticks_msec()-native_started,"native_floor_cells":floor_layer.get_used_cells().size(),"semantic_floor_cells":painter.floor_cells.size()})
	var native_adopted: bool = painter.floor_cells.has(Vector2i(2,2)) and not painter.bridge_cells.has(Vector2i(2,2))
	if not native_adopted:
		_fail("Native Terrain changed signal does not adopt floor priority over bridge.")
	_validate_painter(painter,"native changed signal adoption")
	report.runtime_checks.native_input_adoption = native_adopted
	report.runtime_checks.native_input_adoption_ms = Time.get_ticks_msec()-native_started
	# 派生ImageTexture不保存为场景拥有节点；重新打开必须从输入恢复同样画面。
	var state_before_reload: String = JSON.stringify(painter.snapshot())
	var hash_before_reload := _visual_hash(painter.last_build)
	var packed := PackedScene.new()
	if packed.pack(painter) != OK:
		_fail("Runtime scene pack failed.")
	else:
		var scene_path := OUTPUT + "independent_scene_roundtrip_v002.tscn"
		if ResourceSaver.save(packed,scene_path) != OK:
			_fail("Runtime scene disk save failed.")
		else:
			var saved := ResourceLoader.load(scene_path,"PackedScene",ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
			if saved == null:
				_fail("Saved scene cannot reload from disk.")
			else:
				var restored := saved.instantiate() as Node2D
				root.add_child(restored)
				await process_frame
				if JSON.stringify(restored.snapshot()) != state_before_reload or _visual_hash(restored.last_build) != hash_before_reload:
					_fail("Saved scene reopened with a different semantic layout or artist image.")
				_validate_painter(restored,"saved scene resource reload")
				report.scene_resource_roundtrip = true
				report.runtime_checks.measured_rebuild_ms.append(restored.last_rebuild_ms)
				restored.free()
	_test_incremental_pixels(painter)
	painter.free()


func _validate_painter(painter: Node2D, context: String) -> void:
	for id in ["floor", "bridge"]:
		var layer := painter.get_node(str(id).capitalize()) as TileMapLayer
		var semantic: Dictionary = painter.floor_cells if id == "floor" else painter.bridge_cells
		var cells: Array[Vector2i] = []
		for cell: Vector2i in semantic: cells.append(cell)
		_check_native(layer,cells,context)
		if layer.scale != Vector2(LAYER_SCALE,LAYER_SCALE): _fail(context + " native layer scale differs from0.25.")
	for id in ["water", "facade", "floor", "rim", "bridge", "heads"]:
		var layer := painter.get_node(str(id).capitalize()+"Context") as TileMapLayer
		if layer == null or layer.tile_set == null:
			_fail(context + " missing artist context layer: " + str(id))
			continue
		if layer.scale != Vector2(LAYER_SCALE,LAYER_SCALE) or layer.tile_set.tile_size != Vector2i(TEXTURE_TILE,TEXTURE_TILE):
			_fail(context + " artist context layer has incorrect world scale: " + str(id))
		var source := layer.tile_set.get_source(0) as TileSetAtlasSource
		if source == null or source.texture_region_size != Vector2i(TEXTURE_TILE,TEXTURE_TILE):
			_fail(context + " artist context atlas region differs from128: " + str(id))
			continue
		if layer.get_used_cells().size() != painter.bounds_cells.size.x*painter.bounds_cells.size.y:
			_fail(context + " artist context does not map the complete compiled bounds.")
		for cell: Vector2i in layer.get_used_cells():
			var coord: Vector2i = cell-painter.bounds_cells.position
			if layer.get_cell_atlas_coords(cell) != coord or not source.has_tile(coord):
				_fail(context + " artist context cell is not the saved RGBA slice: " + str(cell))
			checked_cells += 1


func _visual_hash(images: Dictionary) -> String:
	if images.is_empty(): return "NO_COMPILED_IMAGES"
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	for id in ["water", "facade", "floor", "rim", "bridge", "heads"]:
		if not images.has(id): return "MISSING_LAYER"
		var pixels: Image = images[id]
		hash.update(pixels.get_data())
	return hash.finish().hex_encode()


func _test_incremental_pixels(painter: Node2D) -> void:
	var initial := {"version":2,"bounds":[0,0,12,10],"floor":[],"bridge":[]}
	for y in range(2,6):
		for x in range(1,5): initial.floor.append([x,y])
	for y in range(3,5):
		for x in range(5,8): initial.bridge.append([x,y])
	painter.restore_snapshot(initial)
	var retained_images := {}
	for id in ["water", "facade", "floor", "rim", "bridge", "heads"]:
		retained_images[id] = painter.last_build[id].duplicate()
	painter.paint_bridge(Vector2i(8,3))
	painter.synchronize()
	_validate_painter(painter,"incremental bridge extension")
	var dirty: Rect2i = painter.last_dirty_bounds
	if dirty.size.x * dirty.size.y >= painter.bounds_cells.size.x * painter.bounds_cells.size.y:
		_fail("Incremental verification did not exercise an actual smaller dirty region.")
	var dirty_pixels := Rect2i((dirty.position - painter.bounds_cells.position) * TEXTURE_TILE, dirty.size * TEXTURE_TILE)
	var outside_unchanged := _outside_hash(retained_images,dirty_pixels) == _outside_hash(painter.last_build,dirty_pixels)
	if not outside_unchanged:
		_fail("Incremental patch changes artist pixels outside its declared dirty region.")
	var compiler_script = load("res://scripts/ember/reference_floor_compiler_v002.gd")
	var full_compiler = compiler_script.new()
	var full_images: Dictionary = full_compiler.build_visual_layers(painter.floor_cells,painter.bridge_cells,painter.bounds_cells)
	var incremental_matches := _visual_hash(full_images) == _visual_hash(painter.last_build)
	if not incremental_matches:
		_fail("Incremental bridge extension differs from a fresh full-domain artist compilation.")
	report.runtime_checks.incremental_vs_full_rgba = incremental_matches
	report.runtime_checks.incremental_outside_unchanged = outside_unchanged
	report.runtime_checks.incremental_fixture_bounds = [12,10]
	report.runtime_checks.incremental_compiled_bounds = [dirty.position.x,dirty.position.y,dirty.size.x,dirty.size.y]
	report.runtime_checks.incremental_measured_rebuild_ms = painter.last_rebuild_ms
	# 再擦桥头，验证立面和压顶恢复也与全域重算相同。
	for y in range(2):
		for x in range(2): painter.erase_cell(Vector2i(8+x,3+y))
	painter.synchronize()
	_validate_painter(painter,"incremental bridge erase")
	full_images = full_compiler.build_visual_layers(painter.floor_cells,painter.bridge_cells,painter.bounds_cells)
	var erase_matches := _visual_hash(full_images) == _visual_hash(painter.last_build)
	if not erase_matches:
		_fail("Incremental bridge erase differs from a fresh full-domain artist compilation.")
	report.runtime_checks.incremental_erase_vs_full_rgba = erase_matches


func _outside_hash(images: Dictionary,excluded: Rect2i) -> String:
	var first: Image = images.floor
	var size := first.get_size()
	var regions := [
		Rect2i(0,0,size.x,excluded.position.y),
		Rect2i(0,excluded.end.y,size.x,size.y-excluded.end.y),
		Rect2i(0,excluded.position.y,excluded.position.x,excluded.size.y),
		Rect2i(excluded.end.x,excluded.position.y,size.x-excluded.end.x,excluded.size.y)
	]
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	for id in ["water", "facade", "floor", "rim", "bridge", "heads"]:
		var pixels: Image = images[id]
		for region: Rect2i in regions:
			if region.size.x > 0 and region.size.y > 0: hash.update(pixels.get_region(region).get_data())
	return hash.finish().hex_encode()


func _test_four_landings(compiler) -> void:
	var origin := Vector2i(4,4)
	var area := Rect2i(0,0,9,9)
	var checked_pixels := 0
	for direction_index in range(4):
		var direction: Vector2i = DIRECTIONS[direction_index * 2]
		var tangent := Vector2i(-direction.y, direction.x)
		var floor_input := {}
		var bridge_input := {}
		# 地板口宽4格；居中的两格桥意味着两边各仍有12world肩口。
		for depth in range(3):
			for width_index in range(-1,3):
				floor_input[origin - direction * depth + tangent * width_index] = true
		for length_index in range(1,4):
			for width_index in range(2):
				bridge_input[origin + direction * length_index + tangent * width_index] = true
		var images: Dictionary = compiler.build_visual_layers(floor_input, bridge_input, area)
		if not images.has("coverage"):
			_fail("Compiler does not expose the exact footprint used to derive rims and facades.")
			return
		var footprint: Image = images.coverage
		var facade: Image = images.facade
		var bridge_image: Image = images.bridge
		var rim: Image = images.rim
		# 每个桥端第一排：在两格总宽256native的横截面中，实际通道仅[48,208)。
		for across in range(256):
			var width_index := int(across / TEXTURE_TILE)
			var cell := origin + direction + tangent * width_index
			var offset := across % TEXTURE_TILE
			var local_point := Vector2i(64,64) - direction * 63 + tangent * (offset - 64)
			# 反向切线的127-offset保持离散像素范围[0,127]，避免一像素偏移。
			if tangent.x < 0: local_point.x -= 1
			if tangent.y < 0: local_point.y -= 1
			var bridge_point := cell * TEXTURE_TILE + local_point
			var expected_open := across >= 48 and across < 208
			var actual_open := footprint.get_pixelv(bridge_point).g > 0.9
			if actual_open != expected_open:
				_fail("Landing " + str(direction_index) + " bridge must keep12world shoulders; wrong cross-section pixel " + str(across))
			if (bridge_image.get_pixelv(bridge_point).a > 0.9) != expected_open:
				_fail("Landing " + str(direction_index) + " rendered bridge alpha differs from the40world footprint.")
			var floor_point := bridge_point - direction * 2
			if footprint.get_pixelv(floor_point).r < 0.9:
				_fail("Landing " + str(direction_index) + " adjacent floor footprint is missing.")
			if facade.get_pixelv(bridge_point).a > 0.1 and expected_open:
				_fail("Landing " + str(direction_index) + " facade is drawn over the bridge opening.")
			# 保留下来的地板肩仍有外露压顶；桥口内部不能留下封路岸线。
			if not expected_open and rim.get_pixelv(floor_point).a < 0.9:
				_fail("Landing " + str(direction_index) + "12world shoulder lost its coping at across=" + str(across))
			checked_pixels += 1
		# 南向外露面向下投影；桥口中间无立面，肩口下方仍有32world厚立面。
		if direction == Vector2i.DOWN:
			var bridge_start := (origin + direction) * TEXTURE_TILE + Vector2i(64,64)
			var channel_point := bridge_start + tangent * 64 - direction * 48
			var shoulder_point := bridge_start - tangent * 44 - direction * 48
			if facade.get_pixelv(channel_point).a > 0.1: _fail("South landing face closes the central bridge channel.")
			if facade.get_pixelv(shoulder_point).a < 0.9: _fail("South landing shoulder face is absent.")
		print("Landing direction checked: ", direction_index)
	report.runtime_checks.landing_directions = 4
	report.runtime_checks.landing_cross_section_pixels = checked_pixels
	report.runtime_checks.bridge_visible_width_world = 40
	report.runtime_checks.bridge_shoulders_world = 12


func _test_bridge_shapes(compiler) -> void:
	# alpha脚印之外，还导出真实RGBA交点图供独立视觉审阅。
	# 颜色差分只能发现候选断缝，不能把格栅梁纹的美术连接误称为自动证明。
	var floor_input := {}
	var bridge_input := {}
	for point in [Vector2i(1,1), Vector2i(2,2)]: floor_input[point] = true
	# 两格宽L形，再加支路构成T和十字；中段挖2x2洞形成桥环。
	for y in range(3,5):
		for x in range(2,10): bridge_input[Vector2i(x,y)] = true
	for y in range(1,9):
		for x in range(5,7): bridge_input[Vector2i(x,y)] = true
	for y in range(7,9):
		for x in range(2,6): bridge_input[Vector2i(x,y)] = true
	for y in range(4,8):
		for x in range(2,4): bridge_input[Vector2i(x,y)] = true
	var images: Dictionary = compiler.build_visual_layers(floor_input, bridge_input, Rect2i(0,0,12,10))
	# 整个双格交叉中心必须贯通，不因四个单格端帽堵住。
	for point in [Vector2i(5,3), Vector2i(6,3), Vector2i(5,4), Vector2i(6,4)]:
		if compiler.footprint_at(point * TEXTURE_TILE + Vector2i(64,64)) != 2: _fail("Two-cell bridge junction is not open.")
	# 环内2x2空洞不得被面积补全填成桥；孤岛只对角接触时不能误连。
	if compiler.footprint_at(Vector2i(4,6) * TEXTURE_TILE + Vector2i(64,64)) != 0: _fail("Bridge ring hole was incorrectly filled.")
	if compiler.footprint_at(Vector2i(2,1) * TEXTURE_TILE + Vector2i(64,64)) != 0: _fail("Diagonal floor islands incorrectly connected.")
	report.runtime_checks.bridge_junction_shapes = ["L", "T", "cross", "ring_hole", "diagonal_islands"]
	var preview: Image = compiler.flatten_layers(images)
	preview.resize(preview.get_width() / 2, preview.get_height() / 2, Image.INTERPOLATE_NEAREST)
	var preview_path := OUTPUT + "independent_bridge_junctions_v002.png"
	if preview.save_png(preview_path) != OK: _fail("ActualRGBA bridge junction preview cannot save.")
	report.runtime_checks.bridge_junction_actual_rgba_preview = preview_path
	report.runtime_checks.bridge_rgba_interfaces = _bridge_interface_metrics(images.bridge, images.coverage, bridge_input)


func _bridge_interface_metrics(pixels: Image, footprint: Image, bridge_input: Dictionary) -> Dictionary:
	var samples := 0
	var total_delta := 0.0
	var largest_delta := 0.0
	var internal_total := 0.0
	var discontinuous_alpha := 0
	for cell: Vector2i in bridge_input:
		for direction in [Vector2i.RIGHT, Vector2i.DOWN]:
			if not bridge_input.has(cell + direction): continue
			for across in range(TEXTURE_TILE):
				var a := cell * TEXTURE_TILE + (Vector2i(TEXTURE_TILE - 1, across) if direction == Vector2i.RIGHT else Vector2i(across, TEXTURE_TILE - 1))
				var b: Vector2i = a + direction
				if footprint.get_pixelv(a).g < 0.9 or footprint.get_pixelv(b).g < 0.9: continue
				var color_a := pixels.get_pixelv(a)
				var color_b := pixels.get_pixelv(b)
				if color_a.a < 0.9 or color_b.a < 0.9: discontinuous_alpha += 1
				var delta := _rgb_delta(color_a, color_b)
				total_delta += delta
				largest_delta = maxf(largest_delta, delta)
				internal_total += (_rgb_delta(pixels.get_pixelv(a - direction), color_a) + _rgb_delta(color_b, pixels.get_pixelv(b + direction))) * 0.5
				samples += 1
	if discontinuous_alpha != 0: _fail("ActualRGBA bridge interfaces contain alpha gaps inside open footprints.")
	return {
		"status": "RGBA_MEASURED; ART_INTERFACE_REQUIRES_VISUAL_REVIEW",
		"open_interface_samples": samples, "alpha_gaps": discontinuous_alpha,
		"mean_border_rgb_delta": total_delta / maxf(samples, 1),
		"mean_adjacent_internal_rgb_delta": internal_total / maxf(samples, 1),
		"maximum_border_rgb_delta": largest_delta,
		"border_to_internal_ratio": total_delta / maxf(internal_total, 0.000001)
	}


func _rgb_delta(a: Color, b: Color) -> float:
	return (absf(a.r - b.r) + absf(a.g - b.g) + absf(a.b - b.b)) / 3.0


func _finish() -> void:
	report.checked_cells = checked_cells
	report.failures = failures
	report.status = "PASS" if failures.is_empty() and report.runtime_checks.get("status", "") == "PASS" else ("PENDING" if failures.is_empty() else "FAIL")
	var file := FileAccess.open(OUTPUT + "independent_validation_v002.json", FileAccess.WRITE)
	if file != null: file.store_string(JSON.stringify(report, "\t") + "\n")
	print(JSON.stringify(report))
	quit(0 if report.status == "PASS" else 1)


func _fail(message: String) -> void:
	if failures.size() < 100: failures.append(message)
