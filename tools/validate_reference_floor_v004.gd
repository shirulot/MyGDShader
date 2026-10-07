extends SceneTree
## v004 多材质独立验收：读取真实生产 PNG，不生成或替换任何美术。
## 已交付 v002/v003 的报告、资产和完整 Terrain suite 保持冻结。
## 本轮只检查新材料与已有铺刷结构的集成；技术 PASS 不表示用户接受风格。

const OUTPUT := "res://assets/ember/environment/reference_floor_v004/"
const BASE := "res://assets/ember/environment/reference_floor_v002/"
const OLD_MATERIALS := "res://assets/ember/environment/reference_floor_v003/catalog.json"
const COMPILER_PATH := "res://scripts/ember/reference_floor_compiler_v002.gd"
const PAINTER_PATH := "res://scripts/ember/reference_floor_painter_v004.gd"
const TILE := 128
const AREA := Rect2i(0,0,7,6)
const MATERIAL_IDS := [0,1,2,3,4,5,6]
const NEW_IDS := [4,5,6]
const NEW_KEYS := ["concrete","teal","ceramic"]
const LAYERS := ["water","facade","floor","rim","bridge","heads"]
const FIXED_LAYERS := ["water","facade","rim","bridge","heads","coverage"]

var palette: Dictionary = {}
var catalog: Dictionary = {}
var failures: Array[String] = []
var baked_states: Dictionary = {}
var report: Dictionary = {
	"scope":"v004 material extension only; frozen v002/v003 files remain unchanged.",
	"engine":"", "fixture_bounds":[0,0,7,6], "material_ids":[],
	"pair_cases":0, "checked_material_pixels":0, "runtime":{}, "failures":[],
	"default_v002_full_rebuild":"PREVIOUSLY_VERIFIED_IN_V003_NOT_REPEATED",
	"editor_gui_undo_redo":"NOT_TESTED", "changed_source_cache_fallback":"NOT_TESTED"
}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	report.engine=Engine.get_version_info().string
	report.painter_sha256=FileAccess.get_sha256(PAINTER_PATH)
	report.compiler_sha256=FileAccess.get_sha256(COMPILER_PATH)
	if not _load_palette():
		_finish()
		return
	_test_baked_scene_metadata()
	_test_solo_cached_samples()
	var compiler=_new_compiler()
	var fixture:=_fixture()
	var baseline: Dictionary=compiler.build_visual_layers(fixture.floor,fixture.bridge,AREA,{})
	# 同一占用只保留一份 steel 基线；30 case 不重复编译参考图。
	_test_pair_boundaries(compiler,fixture,baseline)
	_test_mixed_preview(compiler,fixture,baseline)
	baseline.clear()
	_test_new_material_landings(compiler)
	await _test_painter()
	_finish()


func _raw_png(path: String) -> Image:
	var image:=Image.new()
	if image.load_png_from_buffer(FileAccess.get_file_as_bytes(path))!=OK:
		_fail("Cannot read production PNG: "+path)
		return image
	# 避免 importer 的 fix_alpha_border 改写透明 RGB，验收原生产字节。
	image.convert(Image.FORMAT_RGBA8)
	return image


func _load_palette() -> bool:
	var parsed=JSON.parse_string(FileAccess.get_file_as_string(OUTPUT+"catalog.json"))
	if not parsed is Dictionary:
		_fail("Production v004 catalog is missing or invalid.")
		return false
	catalog=parsed
	var hashes: Dictionary={}
	for entry: Dictionary in catalog.get("materials",[]):
		var id:=int(entry.get("id",-1))
		if id not in MATERIAL_IDS or palette.has(id):
			_fail("Expected unique production material id0..6: "+str(id))
			continue
		var path:=str(entry.get("texture",""))
		var image:=_raw_png(path)
		if image.is_empty(): continue
		if image.get_width()<TILE or image.get_height()<TILE:
			_fail("Material period cannot supply a native128 tile: "+path)
		# 已交付旧 RGBA 原样保留；本轮三个新增实心 albedo 必须没有透明缺口。
		if id in NEW_IDS and image.detect_alpha()!=Image.ALPHA_NONE:
			_fail("New solid albedo contains transparency: "+path)
		var expected_sha:=str(entry.get("sha256",""))
		if not expected_sha.is_empty() and FileAccess.get_sha256(path)!=expected_sha:
			_fail("Material PNG does not match its declared source SHA: "+path)
		var digest:=_image_hash(image)
		if hashes.has(digest): _fail("Two declared materials have identical RGBA: "+str(id))
		hashes[digest]=id
		palette[id]=image
	for id: int in MATERIAL_IDS:
		if not palette.has(id): _fail("Missing material period id"+str(id))
	# 有旧 catalog 时再只读核对四个旧材料，避免新增包悄悄替换已认可的素材。
	if FileAccess.file_exists(OLD_MATERIALS):
		var old_catalog=JSON.parse_string(FileAccess.get_file_as_string(OLD_MATERIALS))
		if old_catalog is Dictionary:
			var compared:=0
			for entry: Dictionary in old_catalog.get("materials",[]):
				var id:=int(entry.get("id",-1))
				if id>=0 and id<=3 and palette.has(id):
					var old_image:=_raw_png(str(entry.texture))
					if _image_hash(old_image)!=_image_hash(palette[id]): _fail("v004 changes delivered material id"+str(id))
					compared+=1
			report.frozen_v003_material_rgba_compared=compared
	else:
		report.frozen_v003_material_rgba_compared="OLD_CATALOG_UNAVAILABLE"
	report.material_ids=palette.keys()
	return palette.size()==MATERIAL_IDS.size() and failures.is_empty()


func _new_compiler():
	var script=load(COMPILER_PATH)
	var compiler=script.new()
	compiler.load_materials()
	for id: int in palette: compiler.floor_material_periods[id]=palette[id]
	return compiler


func _fixture() -> Dictionary:
	var floor_input: Dictionary={}
	var bridge_input: Dictionary={}
	for y in range(1,5):
		for x in range(1,5):
			if Vector2i(x,y)!=Vector2i(2,3): floor_input[Vector2i(x,y)]=true
	for y in range(2,4):
		for x in range(5,7): bridge_input[Vector2i(x,y)]=true
	return {"floor":floor_input,"bridge":bridge_input}


func _test_pair_boundaries(compiler,fixture: Dictionary,baseline: Dictionary) -> void:
	var initial_failures:=failures.size()
	var baseline_hashes:=_fixed_hashes(baseline)
	var tested_pairs: Array=[]
	# 新3×旧4，加新3之间的3对，共15对；每对横纵交界都保留洞和双格桥。
	for first: int in MATERIAL_IDS:
		for second in range(first+1,MATERIAL_IDS.size()):
			if first<4 and second<4: continue
			tested_pairs.append([first,second])
			for orientation in range(2):
				var mapping: Dictionary={}
				for cell: Vector2i in fixture.floor:
					var id: int=first if (cell.x<3 if orientation==0 else cell.y<3) else second
					if id!=0: mapping[cell]=id
				var images: Dictionary=compiler.build_visual_layers(fixture.floor,fixture.bridge,AREA,mapping)
				var context:="pair%d-%d orientation%d"%[first,second,orientation]
				_check_fixed_hashes(baseline_hashes,images,context)
				_check_albedo_samples(images,fixture.floor,mapping,AREA)
				# 这里两侧都是连续 floor，材质分界不能产生额外压顶/立面。
				var seam:=Vector2i(3*TILE-1,2*TILE+64) if orientation==0 else Vector2i(3*TILE+64,3*TILE-1)
				if images.rim.get_pixelv(seam).a>0.01 or images.facade.get_pixelv(seam).a>0.01:
					_fail("Material boundary adds an internal curb/facade: "+context)
				report.pair_cases+=1
	if tested_pairs.size()!=15 or int(report.pair_cases)!=30: _fail("New-material pair suite did not cover15 pairs/30 orientations.")
	report.material_pairs=tested_pairs
	report.material_boundary_coverage_unchanged=failures.size()==initial_failures
	print("New material boundaries checked: ",report.pair_cases)


func _fixed_hashes(images: Dictionary) -> Dictionary:
	var result: Dictionary={}
	for id in FIXED_LAYERS: result[id]=_image_hash(images[id])
	return result


func _check_fixed_hashes(before: Dictionary,after: Dictionary,context: String) -> void:
	for id in FIXED_LAYERS:
		if before[id]!=_image_hash(after[id]): _fail(context+" changes fixed structural/decorative layer "+str(id))


func _check_albedo_samples(images: Dictionary,floor_input: Dictionary,mapping: Dictionary,area: Rect2i) -> void:
	var offsets: Array=[Vector2i.ZERO,Vector2i(32,32),Vector2i(64,64),Vector2i(96,96),Vector2i(127,127)]
	for cell: Vector2i in floor_input:
		var id:=int(mapping.get(cell,0))
		var source: Image=palette[id]
		for offset: Vector2i in offsets:
			var world:=cell*TILE+offset
			var at:=world-area.position*TILE
			var expected:=Color(0,0,0,0)
			if images.coverage.get_pixelv(at).r>0.9:
				expected=source.get_pixel(posmod(world.x,source.get_width()),posmod(world.y,source.get_height()))
			if images.floor.get_pixelv(at)!=expected: _fail("Floor samples wrong material/world phase id%d at%s"%[id,str(world)])
			report.checked_material_pixels+=1


func _test_mixed_preview(compiler,fixture: Dictionary,baseline: Dictionary) -> void:
	var mapping: Dictionary={}
	for cell: Vector2i in fixture.floor:
		var id:=posmod(cell.x+2*cell.y,7)
		if id!=0: mapping[cell]=id
	var images: Dictionary=compiler.build_visual_layers(fixture.floor,fixture.bridge,AREA,mapping)
	_check_fixed_hashes(_fixed_hashes(baseline),images,"seven-material checker/T/X junctions")
	_check_albedo_samples(images,fixture.floor,mapping,AREA)
	var preview: Image=compiler.flatten_layers(images)
	preview.resize(preview.get_width()/2,preview.get_height()/2,Image.INTERPOLATE_NEAREST)
	var path:=OUTPUT+"independent_mixed_materials_v004.png"
	if preview.save_png(path)!=OK: _fail("Mixed-material diagnostic PNG cannot save.")
	report.mixed_preview=path
	report.mixed_preview_visual_acceptance="REQUIRES_VISUAL_REVIEW"


func _test_new_material_landings(compiler) -> void:
	var floor_input: Dictionary={}
	var bridge_input: Dictionary={}
	# 7×6 内同时放四个2格桥口，每个新材料都独立运行四方向验收。
	for y in range(2,4):
		for x in range(2,5): floor_input[Vector2i(x,y)]=true
	for rectangle in [Rect2i(2,0,2,2),Rect2i(5,2,2,2),Rect2i(2,4,2,2),Rect2i(0,2,2,2)]:
		for y in range(rectangle.position.y,rectangle.end.y):
			for x in range(rectangle.position.x,rectangle.end.x): bridge_input[Vector2i(x,y)]=true
	var steel: Dictionary=compiler.build_visual_layers(floor_input,bridge_input,AREA,{})
	var fixed:=_fixed_hashes(steel)
	steel.clear()
	var origins: Array=[Vector2i(2,2),Vector2i(4,2),Vector2i(3,3),Vector2i(2,3)]
	var directions: Array=[Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]
	var checked:=0
	for id: int in NEW_IDS:
		var mapping: Dictionary={}
		for cell: Vector2i in floor_input: mapping[cell]=id
		var images: Dictionary=compiler.build_visual_layers(floor_input,bridge_input,AREA,mapping)
		_check_fixed_hashes(fixed,images,"material%d four-direction landings"%id)
		_check_albedo_samples(images,floor_input,mapping,AREA)
		for index in range(4):
			var direction: Vector2i=directions[index]
			var tangent:=Vector2i(-direction.y,direction.x)
			for across in range(256):
				var cell: Vector2i=origins[index]+direction+tangent*int(across/TILE)
				var local:=Vector2i(64,64)-direction*63+tangent*(across%TILE-64)
				if tangent.x<0: local.x-=1
				if tangent.y<0: local.y-=1
				var at:=cell*TILE+local
				if (images.coverage.get_pixelv(at).g>0.9)!=(across>=48 and across<208):
					_fail("Material%d direction%d changes40world bridge/12world shoulders."%[id,index])
				checked+=1
	report.material_landing_ids=NEW_IDS
	report.material_landing_cases=12
	report.material_landing_cross_section_pixels=checked


func _test_baked_scene_metadata() -> void:
	var keys: Array=["mixed"]+NEW_KEYS
	for key: String in keys:
		var suffix:="" if key=="mixed" else "_"+key
		var path:="res://scenes/ember/reference_floor"+suffix+"_sandbox_v004.tscn"
		var packed:=ResourceLoader.load(path,"PackedScene",ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
		if packed==null:
			_fail("Production baked scene is unavailable: "+path)
			continue
		# 只读 native 层，不能启动场景 runtime 并用重编译掩盖错误缓存。
		var scene:=packed.instantiate() as Node2D
		if str(scene.baked_layout_id)!=key: _fail("Baked scene selects the wrong layout id: "+path)
		var floor_layer:=scene.get_node_or_null("Floor") as TileMapLayer
		var bridge_layer:=scene.get_node_or_null("Bridge") as TileMapLayer
		var material_layer:=scene.get_node_or_null("FloorMaterials") as TileMapLayer
		if floor_layer==null or bridge_layer==null or material_layer==null:
			_fail("Baked scene is missing persistent native inputs: "+path)
			scene.free()
			continue
		var area: Rect2i=scene.bounds_cells
		var state: Dictionary={"version":3,"bounds":[area.position.x,area.position.y,area.size.x,area.size.y],"floor":[],"bridge":[],"materials":[]}
		for cell: Vector2i in _sorted_cells(floor_layer.get_used_cells()): state.floor.append([cell.x,cell.y])
		for cell: Vector2i in _sorted_cells(bridge_layer.get_used_cells()): state.bridge.append([cell.x,cell.y])
		for cell: Vector2i in _sorted_cells(material_layer.get_used_cells()):
			var coord:=material_layer.get_cell_atlas_coords(cell)
			if coord.x<=0 or not palette.has(coord.x) or coord.y!=0 or material_layer.get_cell_source_id(cell)!=0:
				_fail("Baked scene has an invalid/default material index: "+path)
			state.materials.append([cell.x,cell.y,coord.x])
		var layouts: Dictionary=catalog.get("layout_cache",{})
		if not layouts.has(key) or str(layouts[key].get("signature",""))!=JSON.stringify(state).sha256_text():
			_fail("Baked layout signature does not match its native input: "+key)
		if key!="mixed":
			var selected: int=NEW_IDS[NEW_KEYS.find(key)]
			if state.materials.size()!=state.floor.size(): _fail("Solo scene has unlabeled steel floor: "+key)
			for entry: Array in state.materials:
				if int(entry[2])!=selected: _fail("Solo scene uses the wrong new material: "+key)
		baked_states[key]=state
		scene.free()
	report.baked_scene_ids_checked=baked_states.keys()


func _test_solo_cached_samples() -> void:
	var coverage:=_raw_png(OUTPUT+"union_coverage_v004.png")
	if coverage.is_empty(): return
	var origins: Array=[Vector2i(0,0),Vector2i(1,4),Vector2i(4,5),Vector2i(5,5),Vector2i(8,5),Vector2i(12,10),Vector2i(13,10),Vector2i(22,14),Vector2i(7,10),Vector2i(23,15)]
	var offsets: Array=[Vector2i.ZERO,Vector2i.ONE,Vector2i(31,0),Vector2i(32,32),Vector2i(64,64),Vector2i(96,96),Vector2i(127,127),Vector2i(0,127),Vector2i(127,0)]
	var checked:=0
	var categories: Dictionary={"floor":0,"bridge":0,"outside":0}
	for index in range(3):
		var key: String=NEW_KEYS[index]
		if not baked_states.has(key): continue
		var state: Dictionary=baked_states[key]
		var values: Array=state.bounds
		var area:=Rect2i(int(values[0]),int(values[1]),int(values[2]),int(values[3]))
		var pixels:=_raw_png(OUTPUT+key+"_floor_context_atlas_v004.png")
		if pixels.is_empty(): continue
		if pixels.get_size()!=coverage.get_size() or pixels.get_size()!=area.size*TILE:
			_fail("Solo floor cache dimensions do not match the baked coverage: "+key)
			continue
		var period: Image=palette[NEW_IDS[index]]
		for local_cell: Vector2i in origins:
			var cell:=local_cell+area.position
			if not area.has_point(cell): continue
			for offset: Vector2i in offsets:
				var at:=local_cell*TILE+offset
				var world:=cell*TILE+offset
				var footprint:=coverage.get_pixelv(at)
				var expected:=Color(0,0,0,0)
				if footprint.r>0.9:
					expected=period.get_pixel(posmod(world.x,period.get_width()),posmod(world.y,period.get_height()))
					categories.floor+=1
				elif footprint.g>0.9: categories.bridge+=1
				else: categories.outside+=1
				if pixels.get_pixelv(at)!=expected: _fail("Solo "+key+" cached RGBA/world phase differs at"+str(at))
				checked+=1
	report.solo_floor_cached_sample_pixels=checked
	report.solo_cached_sample_categories=categories
	if checked==0 or int(categories.floor)==0 or int(categories.outside)==0:
		_fail("Solo floor samples do not cover floor pixels and transparent exterior.")


func _sorted_cells(cells: Array) -> Array:
	var result:=cells.duplicate()
	result.sort_custom(func(a: Vector2i,b: Vector2i) -> bool: return a.y<b.y if a.y!=b.y else a.x<b.x)
	return result


func _create_painter() -> Node2D:
	var painter:=Node2D.new()
	painter.name="IndependentMaterialPainterV004"
	painter.set_script(load(PAINTER_PATH))
	painter.bounds_cells=AREA
	# FloorMaterials由生产 painter 补建，以验收其实际七格索引、owner和存储行为。
	for id in ["floor","bridge"]:
		var layer:=TileMapLayer.new()
		layer.name=str(id).capitalize()
		layer.tile_set=ResourceLoader.load(BASE+str(id)+"_terrain_v002.tres","TileSet",ResourceLoader.CACHE_MODE_IGNORE)
		layer.scale=Vector2(0.25,0.25)
		painter.add_child(layer)
		layer.owner=painter
	root.add_child(painter)
	return painter


func _state() -> Dictionary:
	var state: Dictionary={"version":3,"bounds":[0,0,7,6],"floor":[],"bridge":[],"materials":[[2,2,1],[3,2,2],[4,2,6],[4,4,3]]}
	var fixture:=_fixture()
	for cell: Vector2i in _sorted_cells(fixture.floor.keys()): state.floor.append([cell.x,cell.y])
	for cell: Vector2i in _sorted_cells(fixture.bridge.keys()): state.bridge.append([cell.x,cell.y])
	return state


func _test_painter() -> void:
	if not FileAccess.file_exists(PAINTER_PATH):
		_fail("v004 painter has not been produced.")
		return
	var painter:=_create_painter()
	await process_frame
	await process_frame
	painter.restore_snapshot(_state())
	_validate_material_input(painter,"initial")
	var original_topology:=_topology(painter)
	var fixed:=_fixed_hashes(painter.last_build)
	var cases: Array=[Vector2i(3,4),Vector2i(1,1),Vector2i(3,3),Vector2i(4,2)]
	var ids: Array=[4,5,6,0]
	var before_states: Array=[]
	var before_hashes: Array=[]
	var after_states: Array=[]
	var after_hashes: Array=[]
	var measured: Array=[]
	for index in range(cases.size()):
		var before_state: Dictionary=painter.snapshot()
		before_states.append(before_state)
		before_hashes.append(_visual_hash(painter.last_build))
		var before:=_clone_images(painter.last_build)
		painter.paint_material(cases[index],ids[index])
		painter.synchronize()
		painter.commit_edit(before_state)
		if _topology(painter)!=original_topology: _fail("Material-only paint changes floor/bridge occupancy.")
		if painter.last_dirty_bounds.size==Vector2i.ZERO: _fail("Material-only edit produced no dirty region.")
		_check_fixed_hashes(fixed,painter.last_build,"material-only id"+str(ids[index]))
		_compare_full(painter,"material edit"+str(ids[index]))
		_compare_outside(before,painter,"material edit"+str(ids[index]))
		_validate_material_input(painter,"material edit"+str(ids[index]))
		if int(painter.floor_materials.get(cases[index],0))!=ids[index]: _fail("Material brush rejects new/default id"+str(ids[index]))
		measured.append(painter.last_rebuild_ms)
		after_states.append(painter.snapshot())
		after_hashes.append(_visual_hash(painter.last_build))
	report.runtime.material_only_edit_ids=ids
	report.runtime.material_only_rebuild_ms=measured
	# 四个材质事务均走真实撤销栈，再按顺序全部重做；比较先前已验收的完整RGBA。
	for index in range(cases.size()-1,-1,-1):
		if not painter.undo_edit() or JSON.stringify(painter.snapshot())!=JSON.stringify(before_states[index]) or _visual_hash(painter.last_build)!=before_hashes[index]:
			_fail("Undo loses mapping or artist RGBA for id"+str(ids[index]))
	for index in range(cases.size()):
		if not painter.redo_edit() or JSON.stringify(painter.snapshot())!=JSON.stringify(after_states[index]) or _visual_hash(painter.last_build)!=after_hashes[index]:
			_fail("Redo loses mapping or artist RGBA for id"+str(ids[index]))
	report.runtime.material_undo_cases=4
	report.runtime.material_redo_cases=4
	var edited: String=JSON.stringify(painter.snapshot())
	var edited_hash:=_visual_hash(painter.last_build)
	var save_path:=OUTPUT+"independent_layout_roundtrip_v004.json"
	if not painter.save_layout(save_path): _fail("Material layout save failed.")
	painter.erase_cell(Vector2i(3,3))
	painter.synchronize()
	if painter.floor_materials.has(Vector2i(3,3)): _fail("Floor erase leaves an orphan material id6.")
	_compare_full(painter,"erase material floor")
	if not painter.load_layout(save_path) or JSON.stringify(painter.snapshot())!=edited or _visual_hash(painter.last_build)!=edited_hash:
		_fail("JSON reload loses new material ids or artist RGBA.")
	report.runtime.material_json_roundtrip=true
	painter.floor_materials[Vector2i(6,5)]=4
	painter.synchronize()
	if painter.floor_materials.has(Vector2i(6,5)): _fail("Synchronize retains an orphan material entry.")
	_validate_material_input(painter,"orphan pruning")
	report.runtime.orphan_material_pruned=true
	var input:=painter.get_node_or_null("FloorMaterials") as TileMapLayer
	if input==null:
		_fail("Painter did not create the FloorMaterials input layer.")
	else:
		# 不调用内部adopt方法。只编辑原生普通TileMapLayer，等待实际自动补全结果。
		input.set_cell(Vector2i(2,2),0,Vector2i(6,0))
		var started:=Time.get_ticks_msec()
		var adopted: bool=await _wait_for_material(painter,Vector2i(2,2),6)
		report.runtime.native_material_adoption_ms=Time.get_ticks_msec()-started
		if not adopted: _fail("Native material id6 is not adopted/rendered automatically.")
		_compare_full(painter,"native material input id6")
		report.runtime.native_material_adoption=adopted
		input.set_cell(Vector2i(2,2),0,Vector2i(0,0))
		var reset: bool=await _wait_for_material(painter,Vector2i(2,2),0)
		if not reset or painter.floor_materials.has(Vector2i(2,2)) or input.get_cell_source_id(Vector2i(2,2))!=-1:
			_fail("Native steel index0 is not normalized to an absent material entry.")
		_compare_full(painter,"native material input steel reset")
		report.runtime.native_default_index_normalized=reset
	await _test_scene_roundtrip(painter)
	_test_shifted_bounds(painter)
	_test_v003_file_compatibility(painter)
	# 带新材质的floor笔刷仍须移除同格bridge，id0必须清除之前的非零材料。
	painter.paint_floor(Vector2i(5,2),6)
	painter.synchronize()
	if not painter.floor_cells.has(Vector2i(5,2)) or painter.bridge_cells.has(Vector2i(5,2)) or int(painter.floor_materials.get(Vector2i(5,2),0))!=6:
		_fail("New-material floor brush violates chosen material or floor priority.")
	_compare_full(painter,"new material floor brush")
	painter.paint_floor(Vector2i(5,2),0)
	painter.synchronize()
	if painter.floor_materials.has(Vector2i(5,2)): _fail("Steel floor repaint stores a default material entry.")
	_compare_full(painter,"default steel floor repaint")
	report.runtime.material_floor_brush_and_default_reset=true
	painter.free()


func _wait_for_material(painter: Node2D,cell: Vector2i,id: int) -> bool:
	# 逐帧等待生产poll/debounce；计时截止避免静默挂起，也不把后续full比较算进监听延迟。
	var deadline:=Time.get_ticks_msec()+8000
	while Time.get_ticks_msec()<deadline:
		await process_frame
		if int(painter.floor_materials.get(cell,0))==id and _material_cell_matches(painter,cell,id): return true
	return false


func _material_cell_matches(painter: Node2D,cell: Vector2i,id: int) -> bool:
	if painter.last_build.is_empty() or not painter.last_build.has("coverage"): return false
	var source: Image=palette[id]
	var origin: Vector2i=(cell-painter.bounds_cells.position)*TILE
	for y in range(TILE):
		for x in range(TILE):
			var at:=origin+Vector2i(x,y)
			var world:=cell*TILE+Vector2i(x,y)
			var expected:=Color(0,0,0,0)
			if painter.last_build.coverage.get_pixelv(at).r>0.9:
				expected=source.get_pixel(posmod(world.x,source.get_width()),posmod(world.y,source.get_height()))
			if painter.last_build.floor.get_pixelv(at)!=expected: return false
	return true


func _test_v003_file_compatibility(painter: Node2D) -> void:
	var state:=_state()
	state.materials=[[2,2,1],[3,2,2],[4,4,3]]
	var path:=OUTPUT+"independent_legacy_v003_into_v004.json"
	var file:=FileAccess.open(path,FileAccess.WRITE)
	if file==null:
		_fail("Cannot write the legacy v003 file fixture.")
		return
	file.store_string(JSON.stringify(state,"\t")+"\n")
	file.close()
	if not painter.load_layout(path) or JSON.stringify(painter.snapshot())!=JSON.stringify(state):
		_fail("v004 cannot load an unchanged version3 file with old material ids0..3.")
	_validate_material_input(painter,"legacy v003 file")
	_compare_full(painter,"legacy v003 materials")
	report.runtime.legacy_v003_material_ids_preserved=true


func _test_shifted_bounds(painter: Node2D) -> void:
	# 图片尺寸相同不能说明缓存可用：世界原点变化还会改变纹理相位和所有格子的显示位置。
	# 此时已经有真实 ImageTexture 缓存，平移整个多材质布局才能覆盖原先的update快路。
	var initial_failures:=failures.size()
	var original: Dictionary=painter.snapshot()
	var shifted: Dictionary=original.duplicate(true)
	var delta:=Vector2i(-3,-2)
	shifted.bounds[0]=int(shifted.bounds[0])+delta.x
	shifted.bounds[1]=int(shifted.bounds[1])+delta.y
	for key in ["floor","bridge","materials"]:
		for entry: Array in shifted[key]:
			entry[0]=int(entry[0])+delta.x
			entry[1]=int(entry[1])+delta.y
	painter.restore_snapshot(shifted)
	if painter.bounds_cells.size!=AREA.size or painter.bounds_cells.position!=delta:
		_fail("Translated fixture does not preserve7x6 dimensions and its negative origin.")
	if not painter.last_build.has("pixel_origin") or painter.last_build.pixel_origin!=painter.bounds_cells.position*TILE:
		_fail("Same-size origin move retains the previous cached pixel_origin.")
	if painter.last_dirty_bounds!=painter.bounds_cells:
		_fail("Same-size origin move must rebuild the full new bounds.")
	if JSON.stringify(painter.snapshot())!=JSON.stringify(shifted):
		_fail("Origin move loses translated floor, bridge, or material input.")
	_validate_material_input(painter,"negative origin")
	_compare_full(painter,"same-size negative origin/world phase")
	_check_albedo_samples(painter.last_build,painter.floor_cells,painter.floor_materials,painter.bounds_cells)
	_check_context_positions(painter,"negative origin")
	# 再回到原点，确认第二次相同大小的ImageTexture不会留在刚才的负坐标。
	painter.restore_snapshot(original)
	if painter.last_build.pixel_origin!=painter.bounds_cells.position*TILE or painter.last_dirty_bounds!=painter.bounds_cells:
		_fail("Returning same-size bounds to the original origin reuses a stale cache.")
	_compare_full(painter,"restored original origin/world phase")
	_check_context_positions(painter,"restored original origin")
	report.runtime.same_size_bounds_shift_origin=[delta.x,delta.y]
	report.runtime.same_size_bounds_shift_and_restore=failures.size()==initial_failures


func _check_context_positions(painter: Node2D,context: String) -> void:
	var checked:=0
	for id: String in LAYERS:
		var layer:=painter.get_node_or_null(id.capitalize()+"Context") as TileMapLayer
		if layer==null or layer.tile_set==null:
			_fail(context+" lacks the visual layer "+id)
			continue
		if layer.get_used_rect()!=painter.bounds_cells:
			_fail(context+" leaves visual TileMap cells at the previous bounds: "+id)
		var inverse:=layer.get_transform().affine_inverse()
		var wrong_mapping:=false
		for y in range(painter.bounds_cells.size.y):
			for x in range(painter.bounds_cells.size.x):
				var atlas:=Vector2i(x,y)
				var world_cell: Vector2i=painter.bounds_cells.position+atlas
				var expected:=(Vector2(world_cell)+Vector2(0.5,0.5))*32.0
				# 验证真实TileMap变换后的世界位置，不能仅用CPU图像正确来证明显示正确。
				var drawn_cell:=layer.local_to_map(inverse*expected)
				var drawn_position:=layer.get_transform()*layer.map_to_local(drawn_cell)
				if layer.get_cell_source_id(drawn_cell)!=0 or layer.get_cell_atlas_coords(drawn_cell)!=atlas or not drawn_position.is_equal_approx(expected):
					wrong_mapping=true
				checked+=1
		if wrong_mapping: _fail(context+" displays atlas cells at stale world positions: "+id)
	report.runtime.context_tile_origin_mappings_checked=int(report.runtime.get("context_tile_origin_mappings_checked",0))+checked


func _validate_material_input(painter: Node2D,context: String) -> void:
	var layer:=painter.get_node_or_null("FloorMaterials") as TileMapLayer
	if layer==null or layer.tile_set==null:
		_fail(context+" lacks a usable FloorMaterials input layer.")
		return
	if layer.owner!=painter: _fail(context+" FloorMaterials is not owned and cannot persist.")
	if layer.scale!=Vector2(0.25,0.25) or layer.tile_set.tile_size!=Vector2i(TILE,TILE):
		_fail(context+" material indexing violates128native/32world scale.")
	if layer.tile_set.get_terrain_sets_count()!=0: _fail("Material input must remain ordinary tiles, without Terrain randomness.")
	var source:=layer.tile_set.get_source(0) as TileSetAtlasSource if layer.tile_set.has_source(0) else null
	if source==null or source.texture_region_size!=Vector2i(TILE,TILE):
		_fail(context+" lacks the native128 material source0.")
	else:
		for id: int in MATERIAL_IDS:
			if not source.has_tile(Vector2i(id,0)): _fail(context+" material TileSet cannot paint id"+str(id))
	if layer.get_used_cells().size()!=painter.floor_materials.size(): _fail(context+" material map differs from input occupancy.")
	for cell: Vector2i in painter.floor_materials:
		var id:=int(painter.floor_materials[cell])
		if id==0 or not palette.has(id) or not painter.floor_cells.has(cell): _fail(context+" stores invalid/default/orphan material.")
		if layer.get_cell_source_id(cell)!=0 or layer.get_cell_atlas_coords(cell)!=Vector2i(id,0):
			_fail(context+" ordinary material source/coordinate differs from its id.")
	var state: Dictionary=painter.snapshot()
	if int(state.get("version",0))!=3 or not state.has("materials"): _fail("Snapshot must retain version3 and explicit material triples.")
	var last:=Vector2i(-2147483647,-2147483647)
	for entry: Array in state.get("materials",[]):
		var cell:=Vector2i(int(entry[0]),int(entry[1]))
		if cell.y<last.y or (cell.y==last.y and cell.x<last.x): _fail("Saved materials are not in stable coordinate order.")
		last=cell


func _compare_full(painter: Node2D,context: String) -> void:
	var compiler=_new_compiler()
	var expected: Dictionary=compiler.build_visual_layers(painter.floor_cells,painter.bridge_cells,painter.bounds_cells,painter.floor_materials)
	if _visual_hash(expected)!=_visual_hash(painter.last_build): _fail(context+" incremental RGBA differs from fresh full-domain compilation.")
	report.runtime.full_rgba_comparisons=int(report.runtime.get("full_rgba_comparisons",0))+1


func _compare_outside(before: Dictionary,painter: Node2D,context: String) -> void:
	var dirty: Rect2i=painter.last_dirty_bounds
	var excluded:=Rect2i((dirty.position-painter.bounds_cells.position)*TILE,dirty.size*TILE)
	if _outside_hash(before,excluded)!=_outside_hash(painter.last_build,excluded): _fail(context+" changes pixels outside its declared dirty region.")


func _test_scene_roundtrip(painter: Node2D) -> void:
	var state: String=JSON.stringify(painter.snapshot())
	var image_hash:=_visual_hash(painter.last_build)
	var packed:=PackedScene.new()
	var path:=OUTPUT+"independent_scene_roundtrip_v004.tscn"
	if packed.pack(painter)!=OK or ResourceSaver.save(packed,path)!=OK:
		_fail("Material scene cannot save to disk.")
		return
	var reloaded:=ResourceLoader.load(path,"PackedScene",ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	if reloaded==null:
		_fail("Saved material scene cannot reload.")
		return
	var restored:=reloaded.instantiate() as Node2D
	root.add_child(restored)
	await process_frame
	await process_frame
	if JSON.stringify(restored.snapshot())!=state or _visual_hash(restored.last_build)!=image_hash:
		_fail("Scene reload loses new material ids or changes artist RGBA.")
	_validate_material_input(restored,"saved scene reload")
	report.runtime.material_scene_roundtrip=true
	restored.free()


func _topology(painter: Node2D) -> String:
	var state: Dictionary=painter.snapshot()
	return JSON.stringify({"floor":state.floor,"bridge":state.bridge,"bounds":state.bounds})


func _clone_images(images: Dictionary) -> Dictionary:
	var result: Dictionary={}
	for id in LAYERS+["coverage"]: result[id]=images[id].duplicate()
	return result


func _image_hash(image: Image) -> String:
	var hashing:=HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256)
	hashing.update(image.get_data())
	return hashing.finish().hex_encode()


func _visual_hash(images: Dictionary) -> String:
	if images.is_empty(): return "MISSING_COMPILED_IMAGES"
	var hashing:=HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256)
	for id in LAYERS+["coverage"]:
		if not images.has(id): return "MISSING_LAYER"
		hashing.update(images[id].get_data())
	return hashing.finish().hex_encode()


func _outside_hash(images: Dictionary,excluded: Rect2i) -> String:
	var floor_image: Image=images.floor
	var size:=floor_image.get_size()
	var regions: Array=[Rect2i(0,0,size.x,excluded.position.y),Rect2i(0,excluded.end.y,size.x,size.y-excluded.end.y),Rect2i(0,excluded.position.y,excluded.position.x,excluded.size.y),Rect2i(excluded.end.x,excluded.position.y,size.x-excluded.end.x,excluded.size.y)]
	var hashing:=HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256)
	for id in LAYERS+["coverage"]:
		var image: Image=images[id]
		for region: Rect2i in regions:
			if region.size.x>0 and region.size.y>0: hashing.update(image.get_region(region).get_data())
	return hashing.finish().hex_encode()


func _finish() -> void:
	report.failures=failures
	report.status="PASS" if failures.is_empty() else "FAIL"
	var file:=FileAccess.open(OUTPUT+"independent_validation_v004.json",FileAccess.WRITE)
	if file!=null: file.store_string(JSON.stringify(report,"\t")+"\n")
	print(JSON.stringify(report))
	quit(0 if failures.is_empty() else 1)


func _fail(message: String) -> void:
	if failures.size()<100: failures.append(message)
