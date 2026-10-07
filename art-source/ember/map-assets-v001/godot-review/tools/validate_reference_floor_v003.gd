extends SceneTree
## v003 多材质独立验收。只读取生产PNG，不生产或替换美术资源。
## 旧v002的完整Terrain验收已冻结；本轮只检查材质扩展引入的新行为。
## 结构PASS不代表用户接受素材风格，混铺诊断PNG须独立视觉审阅。

const OUTPUT := "res://assets/ember/environment/reference_floor_v003/"
const BASE := "res://assets/ember/environment/reference_floor_v002/"
const COMPILER_PATH := "res://scripts/ember/reference_floor_compiler_v002.gd"
const PAINTER_PATH := "res://scripts/ember/reference_floor_painter_v003.gd"
const TILE := 128
const LAYERS := ["water","facade","floor","rim","bridge","heads"]
const FIXED_LAYERS := ["water","facade","rim","bridge","heads","coverage"]

var palette: Dictionary = {}
var failures: Array[String] = []
var report: Dictionary = {
	"scope":"v003 material extension only; v002 structural report remains unchanged.",
	"engine":"", "material_ids":[], "pair_cases":0, "checked_material_pixels":0,
	"runtime":{}, "editor_gui_undo_redo":"NOT_TESTED", "failures":[]
}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	report.engine=Engine.get_version_info().string
	if not _load_palette():
		_finish()
		return
	var compiler=_new_compiler()
	var default_images:=_test_default_v002_output()
	if not default_images.is_empty(): _test_solo_cached_samples(default_images)
	default_images.clear()
	_test_pair_boundaries(compiler)
	_test_mixed_preview(compiler)
	_test_four_material_landings(compiler)
	await _test_painter()
	_finish()


func _raw_png(path: String) -> Image:
	var image:=Image.new()
	if image.load_png_from_buffer(FileAccess.get_file_as_bytes(path))!=OK:
		_fail("Cannot read production PNG: "+path)
		return image
	image.convert(Image.FORMAT_RGBA8)
	return image


func _test_default_v002_output() -> Dictionary:
	# 直接从已交付v002场景的native输入读占用，不启动其@tool/runtime逻辑。
	var packed:=ResourceLoader.load("res://scenes/ember/reference_floor_sandbox_v002.tscn","PackedScene",ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	if packed==null:
		_fail("Frozen v002 production scene is unavailable for default API regression.")
		return {}
	var scene:=packed.instantiate() as Node2D
	var floor_input: Dictionary={}
	var bridge_input: Dictionary={}
	for cell: Vector2i in scene.get_node("Floor").get_used_cells(): floor_input[cell]=true
	for cell: Vector2i in scene.get_node("Bridge").get_used_cells(): bridge_input[cell]=true
	var area: Rect2i=scene.bounds_cells
	scene.free()
	var compiler=_new_compiler()
	var started:=Time.get_ticks_msec()
	# 特意省略第4个material参数，验证旧API的默认结果，而非手动传空表替它证明。
	var images: Dictionary=compiler.build_visual_layers(floor_input,bridge_input,area)
	report.default_v002_full_compile_ms=Time.get_ticks_msec()-started
	var all_equal:=true
	for id in LAYERS:
		var delivered:=_raw_png(BASE+str(id)+"_context_atlas_v002.png")
		if _image_hash(delivered)!=_image_hash(images[id]):
			all_equal=false
			_fail("Optional material API changes frozen v002 default layer "+str(id))
	report.default_v002_six_context_rgba_identical=all_equal
	report.default_v002_bounds=[area.position.x,area.position.y,area.size.x,area.size.y]
	print("Frozen v002 default output checked.")
	return images


func _test_solo_cached_samples(default_images: Dictionary) -> void:
	var coverage: Image=default_images.coverage
	var origins: Array=[Vector2i(0,0),Vector2i(1,4),Vector2i(4,5),Vector2i(5,5),Vector2i(8,5),Vector2i(12,10),Vector2i(13,10),Vector2i(22,14),Vector2i(7,10),Vector2i(23,15)]
	var offsets: Array=[Vector2i(0,0),Vector2i(1,1),Vector2i(31,0),Vector2i(32,32),Vector2i(64,64),Vector2i(96,96),Vector2i(127,127),Vector2i(0,127),Vector2i(127,0)]
	var names: Array=["steel","control","service","rust"]
	var checked:=0
	for id in range(1,4):
		var pixels:=_raw_png(OUTPUT+str(names[id])+"_floor_context_atlas_v003.png")
		var period: Image=palette[id]
		for cell: Vector2i in origins:
			for offset: Vector2i in offsets:
				var at:=cell*TILE+offset
				var expected:=Color(0,0,0,0)
				if coverage.get_pixelv(at).r>0.9:
					expected=period.get_pixel(posmod(at.x,period.get_width()),posmod(at.y,period.get_height()))
				if pixels.get_pixelv(at)!=expected: _fail("Solo material%d cachedRGBA differs at%s"%[id,str(at)])
				checked+=1
	report.solo_floor_cached_sample_pixels=checked
	print("Three solo floor caches sampled: ",checked)


func _load_palette() -> bool:
	var parsed=JSON.parse_string(FileAccess.get_file_as_string(OUTPUT+"catalog.json"))
	if not parsed is Dictionary:
		_fail("Production v003 catalog is missing or invalid.")
		return false
	var pixel_hashes: Dictionary={}
	for entry: Dictionary in parsed.get("materials",[]):
		var id:=int(entry.id)
		if id<0 or id>3 or palette.has(id):
			_fail("Material id must be unique in0..3: "+str(id))
			continue
		var path:=str(entry.texture)
		var image:=Image.new()
		if image.load_png_from_buffer(FileAccess.get_file_as_bytes(path))!=OK:
			_fail("Material source PNG cannot load: "+path)
			continue
		image.convert(Image.FORMAT_RGBA8)
		# id0保留已交付原始RGBA。新增材质必须是实心albedo，不补验证或改写旧艺术。
		if id!=0 and image.detect_alpha()!=Image.ALPHA_NONE: _fail("New solid floor albedo contains transparency: "+path)
		var digest:=_image_hash(image)
		if pixel_hashes.has(digest): _fail("Two declared materials have identical RGBA pixels: "+str(id))
		pixel_hashes[digest]=id
		palette[id]=image
	for id in range(4):
		if not palette.has(id): _fail("Missing material period id"+str(id))
	report.material_ids=palette.keys()
	return palette.size()==4 and failures.is_empty()


func _new_compiler():
	var script=load(COMPILER_PATH)
	var compiler=script.new()
	compiler.load_materials()
	for id: int in palette: compiler.floor_material_periods[id]=palette[id]
	return compiler


func _fixture(area:=Rect2i(0,0,8,7)) -> Dictionary:
	var floor_input: Dictionary={}
	var bridge_input: Dictionary={}
	for y in range(1,6):
		for x in range(1,5):
			if Vector2i(x,y)!=Vector2i(2,3): floor_input[Vector2i(x,y)]=true
	for y in range(2,4):
		for x in range(5,7): bridge_input[Vector2i(x,y)]=true
	return {"floor":floor_input,"bridge":bridge_input,"area":area}


func _test_pair_boundaries(compiler) -> void:
	var fixture:=_fixture()
	var baseline: Dictionary=compiler.build_visual_layers(fixture.floor,fixture.bridge,fixture.area,{})
	# 4种材质共6对，每对水平/垂直交界各一次。占用始终是一片floor。
	for first in range(4):
		for second in range(first+1,4):
			for orientation in range(2):
				var mapping: Dictionary={}
				for cell: Vector2i in fixture.floor:
					var id: int=first if (cell.x<3 if orientation==0 else cell.y<3) else second
					if id!=0: mapping[cell]=id
				var images: Dictionary=compiler.build_visual_layers(fixture.floor,fixture.bridge,fixture.area,mapping)
				_check_fixed_layers(baseline,images,"pair%d-%d orientation%d"%[first,second,orientation])
				_check_albedo_samples(images,fixture.floor,mapping,fixture.area)
				# 选远离外围和洞沿的内部交界点，不能因换材质额外生成压顶或立面。
				var seam:=Vector2i(3*TILE-1,2*TILE+64) if orientation==0 else Vector2i(3*TILE+64,3*TILE-1)
				if images.rim.get_pixelv(seam).a>0.01 or images.facade.get_pixelv(seam).a>0.01:
					_fail("Material boundary adds an internal curb/facade: "+str(first)+"/"+str(second))
				report.pair_cases+=1
	report.material_boundary_coverage_unchanged=true


func _check_fixed_layers(before: Dictionary,after: Dictionary,context: String) -> void:
	for id in FIXED_LAYERS:
		if _image_hash(before[id])!=_image_hash(after[id]): _fail(context+" changes topology/decorative layer "+str(id))


func _check_albedo_samples(images: Dictionary,floor_input: Dictionary,mapping: Dictionary,area: Rect2i) -> void:
	for cell: Vector2i in floor_input:
		var id:=int(mapping.get(cell,0))
		var source: Image=palette[id]
		var world:=cell*TILE+Vector2i(64,64)
		var expected:=source.get_pixel(posmod(world.x,source.get_width()),posmod(world.y,source.get_height()))
		var actual: Color=images.floor.get_pixelv(world-area.position*TILE)
		if actual!=expected: _fail("Floor did not sample material id%d at%s"%[id,str(cell)])
		report.checked_material_pixels+=1


func _test_mixed_preview(compiler) -> void:
	var fixture:=_fixture()
	var materials: Dictionary={}
	for cell: Vector2i in fixture.floor:
		var id:=posmod(cell.x+cell.y,4)
		if id!=0: materials[cell]=id
	var mixed: Dictionary=compiler.build_visual_layers(fixture.floor,fixture.bridge,fixture.area,materials)
	var steel: Dictionary=compiler.build_visual_layers(fixture.floor,fixture.bridge,fixture.area,{})
	_check_fixed_layers(steel,mixed,"checker/T/X mixed materials")
	_check_albedo_samples(mixed,fixture.floor,materials,fixture.area)
	var preview: Image=compiler.flatten_layers(mixed)
	preview.resize(preview.get_width()/2,preview.get_height()/2,Image.INTERPOLATE_NEAREST)
	var path:=OUTPUT+"independent_mixed_materials_v003.png"
	if preview.save_png(path)!=OK: _fail("Mixed-material diagnostic PNG cannot save.")
	report.mixed_preview=path
	report.mixed_preview_visual_acceptance="REQUIRES_VISUAL_REVIEW"
	# 桥口虽然贴两种不同材质，仍是256native总宽中[48,208)贯通。
	var footprint: Image=mixed.coverage
	for across in range(256):
		var at:=Vector2i(5*TILE+1,2*TILE+across)
		var expected:=across>=48 and across<208
		if (footprint.get_pixelv(at).g>0.9)!=expected: _fail("Mixed materials changed40world bridge opening or12world shoulders.")
	report.bridge_cross_section_pixels=256


func _test_four_material_landings(compiler) -> void:
	var floor_input: Dictionary={}
	var bridge_input: Dictionary={}
	var mapping: Dictionary={}
	for y in range(2,5):
		for x in range(2,5):
			var cell:=Vector2i(x,y)
			floor_input[cell]=true
			var id:=posmod(x+y,4)
			if id!=0: mapping[cell]=id
	for rectangle in [Rect2i(2,0,2,2),Rect2i(5,2,2,2),Rect2i(2,5,2,2),Rect2i(0,2,2,2)]:
		for y in range(rectangle.position.y,rectangle.end.y):
			for x in range(rectangle.position.x,rectangle.end.x): bridge_input[Vector2i(x,y)]=true
	var area:=Rect2i(0,0,8,7)
	var steel: Dictionary=compiler.build_visual_layers(floor_input,bridge_input,area,{})
	var colored: Dictionary=compiler.build_visual_layers(floor_input,bridge_input,area,mapping)
	_check_fixed_layers(steel,colored,"four-direction mixed material landings")
	var origins: Array=[Vector2i(2,2),Vector2i(4,2),Vector2i(3,4),Vector2i(2,3)]
	var directions: Array=[Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]
	for index in range(4):
		var direction: Vector2i=directions[index]
		var tangent:=Vector2i(-direction.y,direction.x)
		for across in range(256):
			var cell: Vector2i=origins[index]+direction+tangent*int(across/TILE)
			var local:=Vector2i(64,64)-direction*63+tangent*(across%TILE-64)
			if tangent.x<0: local.x-=1
			if tangent.y<0: local.y-=1
			var at:=cell*TILE+local
			if (colored.coverage.get_pixelv(at).g>0.9)!=(across>=48 and across<208):
				_fail("Material landing direction%d changed40world bridge width."%index)
	report.material_landing_directions=4
	report.material_landing_cross_section_pixels=1024


func _create_painter() -> Node2D:
	var painter:=Node2D.new()
	painter.name="IndependentMaterialPainterV003"
	painter.set_script(load(PAINTER_PATH))
	painter.bounds_cells=Rect2i(0,0,10,8)
	# FloorMaterials由production painter自动补建，验证其真实owner与保存行为。
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
	var state: Dictionary={"version":3,"bounds":[0,0,10,8],"floor":[],"bridge":[],"materials":[[2,2,1],[4,2,2],[5,4,3]]}
	for y in range(1,6):
		for x in range(1,7):
			if Vector2i(x,y)!=Vector2i(3,3): state.floor.append([x,y])
	for y in range(2,4):
		for x in range(7,9): state.bridge.append([x,y])
	return state


func _test_painter() -> void:
	if not FileAccess.file_exists(PAINTER_PATH):
		_fail("v003 painter has not been produced.")
		return
	var painter:=_create_painter()
	await process_frame
	await process_frame
	painter.restore_snapshot(_state())
	_validate_material_input(painter,"initial")
	var original_topology:=_topology(painter)
	var unchanged:=_clone_images(painter.last_build)
	var cases: Array=[Vector2i(4,4),Vector2i(1,1),Vector2i(3,2),Vector2i(6,2)]
	var ids: Array=[1,2,3,1]
	var measured: Array=[]
	var before_last: Dictionary={}
	var before_last_hash:=""
	for index in range(cases.size()):
		before_last=painter.snapshot()
		before_last_hash=_visual_hash(painter.last_build)
		var before:=_clone_images(painter.last_build)
		painter.paint_material(cases[index],ids[index])
		painter.synchronize()
		painter.commit_edit(before_last)
		if _topology(painter)!=original_topology: _fail("Painting material changes floor/bridge occupancy.")
		if painter.last_dirty_bounds.size==Vector2i.ZERO: _fail("Material-only edit produced no dirty region.")
		_check_fixed_layers(unchanged,painter.last_build,"material-only edit")
		_compare_full(painter,"material edit"+str(index))
		_compare_outside(before,painter,"material edit"+str(index))
		_validate_material_input(painter,"material edit"+str(index))
		measured.append(painter.last_rebuild_ms)
	report.runtime.material_only_edit_cases=cases.size()
	report.runtime.material_only_rebuild_ms=measured
	var edited: String=JSON.stringify(painter.snapshot())
	var edited_hash:=_visual_hash(painter.last_build)
	if not painter.undo_edit() or JSON.stringify(painter.snapshot())!=JSON.stringify(before_last) or _visual_hash(painter.last_build)!=before_last_hash:
		_fail("Material undo does not restore both material mapping and artist RGBA.")
	if not painter.redo_edit() or JSON.stringify(painter.snapshot())!=edited or _visual_hash(painter.last_build)!=edited_hash:
		_fail("Material redo does not restore both material mapping and artist RGBA.")
	report.runtime.material_undo_redo=true
	var save_path:=OUTPUT+"independent_layout_roundtrip_v003.json"
	if not painter.save_layout(save_path): _fail("Material layout save failed.")
	painter.erase_cell(Vector2i(6,2))
	painter.synchronize()
	if painter.floor_materials.has(Vector2i(6,2)): _fail("Floor erase leaves an orphaned material id.")
	_compare_full(painter,"erase material floor")
	if not painter.load_layout(save_path) or JSON.stringify(painter.snapshot())!=edited or _visual_hash(painter.last_build)!=edited_hash:
		_fail("JSON reload does not restore material ids and artist pixels.")
	report.runtime.material_json_roundtrip=true
	painter.floor_materials[Vector2i(9,7)]=3
	painter.synchronize()
	if painter.floor_materials.has(Vector2i(9,7)): _fail("Synchronization does not prune orphaned material entries.")
	_validate_material_input(painter,"orphan pruning")
	report.runtime.orphan_material_pruned=true
	# 真正编辑普通材料层，验证无changed的set_cell也由生产poll采纳。
	var material_layer:=painter.get_node_or_null("FloorMaterials") as TileMapLayer
	if material_layer==null:
		_fail("Painter did not create FloorMaterials input layer.")
	else:
		material_layer.set_cell(Vector2i(2,2),0,Vector2i(3,0))
		var started:=Time.get_ticks_msec()
		for attempt in range(60):
			await create_timer(0.05).timeout
			await process_frame
			if int(painter.floor_materials.get(Vector2i(2,2),0))==3 and not painter._pending and painter._fingerprint==JSON.stringify(painter.snapshot()): break
		if int(painter.floor_materials.get(Vector2i(2,2),0))!=3: _fail("Native FloorMaterials set_cell is not adopted automatically.")
		_compare_full(painter,"native material input adoption")
		report.runtime.native_material_adoption_ms=Time.get_ticks_msec()-started
		report.runtime.native_material_adoption=int(painter.floor_materials.get(Vector2i(2,2),0))==3
	await _test_scene_roundtrip(painter)
	# 旧version2文件没有material字段，必须得到原steel默认，不继承先前材质。
	var legacy:=_state()
	legacy.version=2
	legacy.erase("materials")
	painter.restore_snapshot(legacy)
	if not painter.floor_materials.is_empty(): _fail("Legacy v002 layout did not reset materials to default steel.")
	_compare_full(painter,"legacy v002 default steel")
	report.runtime.legacy_v002_default_steel=true
	# 带材质floor笔刷仍保留floor优先规则，并且id0确实清除旧材料索引。
	painter.paint_floor(Vector2i(7,2),2)
	painter.synchronize()
	if not painter.floor_cells.has(Vector2i(7,2)) or painter.bridge_cells.has(Vector2i(7,2)) or int(painter.floor_materials.get(Vector2i(7,2),0))!=2:
		_fail("paint_floor(cell,material) does not preserve floor priority or chosen material.")
	_compare_full(painter,"new material floor brush")
	painter.paint_floor(Vector2i(7,2),0)
	painter.synchronize()
	if painter.floor_materials.has(Vector2i(7,2)): _fail("Steel id0 leaves a stored nondefault material entry.")
	_compare_full(painter,"default steel repaint")
	report.runtime.material_floor_brush_and_default_reset=true
	painter.free()


func _validate_material_input(painter: Node2D,context: String) -> void:
	var layer:=painter.get_node_or_null("FloorMaterials") as TileMapLayer
	if layer==null or layer.tile_set==null:
		_fail(context+" lacks a usable FloorMaterials input layer.")
		return
	if layer.owner!=painter: _fail(context+" FloorMaterials is not owned by the scene and cannot persist.")
	if layer.tile_set.get_terrain_sets_count()!=0: _fail("Material input must not be a competing native Terrain family.")
	if layer.get_used_cells().size()!=painter.floor_materials.size(): _fail(context+" material map differs from input-layer occupancy.")
	for cell: Vector2i in painter.floor_materials:
		var id:=int(painter.floor_materials[cell])
		if id<1 or id>3 or not painter.floor_cells.has(cell): _fail(context+" contains invalid/default/orphan material map entry.")
		if layer.get_cell_source_id(cell)!=0 or layer.get_cell_atlas_coords(cell)!=Vector2i(id,0):
			_fail(context+" ordinary material source/coordinate differs from its id.")
	var state: Dictionary=painter.snapshot()
	if int(state.get("version",0))!=3 or not state.has("materials"): _fail("Snapshot does not explicitly save material version3.")
	var last:=Vector2i(-2147483647,-2147483647)
	for entry: Array in state.get("materials",[]):
		var cell:=Vector2i(int(entry[0]),int(entry[1]))
		if cell.y<last.y or (cell.y==last.y and cell.x<last.x): _fail("Saved material entries are not in stable coordinate order.")
		last=cell


func _compare_full(painter: Node2D,context: String) -> void:
	var compiler=_new_compiler()
	var expected: Dictionary=compiler.build_visual_layers(painter.floor_cells,painter.bridge_cells,painter.bounds_cells,painter.floor_materials)
	if _visual_hash(expected)!=_visual_hash(painter.last_build): _fail(context+" incremental RGBA differs from fresh full-domain compilation.")
	report.runtime.full_rgba_comparisons=int(report.runtime.get("full_rgba_comparisons",0))+1


func _compare_outside(before: Dictionary,painter: Node2D,context: String) -> void:
	var dirty: Rect2i=painter.last_dirty_bounds
	var excluded:=Rect2i((dirty.position-painter.bounds_cells.position)*TILE,dirty.size*TILE)
	if _outside_hash(before,excluded)!=_outside_hash(painter.last_build,excluded): _fail(context+" changes artist pixels outside its declared dirty region.")


func _test_scene_roundtrip(painter: Node2D) -> void:
	var state: String=JSON.stringify(painter.snapshot())
	var image_hash:=_visual_hash(painter.last_build)
	var packed:=PackedScene.new()
	var path:=OUTPUT+"independent_scene_roundtrip_v003.tscn"
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
		_fail("Scene reload loses material ids or changes artist RGBA.")
	_validate_material_input(restored,"saved scene reload")
	report.runtime.material_scene_roundtrip=true
	restored.free()


func _topology(painter: Node2D) -> String:
	var state: Dictionary=painter.snapshot()
	return JSON.stringify({"floor":state.floor,"bridge":state.bridge,"bounds":state.bounds})


func _clone_images(images: Dictionary) -> Dictionary:
	var result: Dictionary={}
	for id in LAYERS+ ["coverage"]: result[id]=images[id].duplicate()
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
	for id in LAYERS+ ["coverage"]:
		if not images.has(id): return "MISSING_LAYER"
		hashing.update(images[id].get_data())
	return hashing.finish().hex_encode()


func _outside_hash(images: Dictionary,excluded: Rect2i) -> String:
	var floor_image: Image=images.floor
	var size:=floor_image.get_size()
	var regions: Array=[Rect2i(0,0,size.x,excluded.position.y),Rect2i(0,excluded.end.y,size.x,size.y-excluded.end.y),Rect2i(0,excluded.position.y,excluded.position.x,excluded.size.y),Rect2i(excluded.end.x,excluded.position.y,size.x-excluded.end.x,excluded.size.y)]
	var hashing:=HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256)
	for id in LAYERS+ ["coverage"]:
		var image: Image=images[id]
		for region: Rect2i in regions:
			if region.size.x>0 and region.size.y>0: hashing.update(image.get_region(region).get_data())
	return hashing.finish().hex_encode()


func _finish() -> void:
	report.failures=failures
	report.status="PASS" if failures.is_empty() else "FAIL"
	var file:=FileAccess.open(OUTPUT+"independent_validation_v003.json",FileAccess.WRITE)
	if file!=null: file.store_string(JSON.stringify(report,"\t")+"\n")
	print(JSON.stringify(report))
	quit(0 if failures.is_empty() else 1)


func _fail(message: String) -> void:
	if failures.size()<100: failures.append(message)
