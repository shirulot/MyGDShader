extends SceneTree
## 实际 Terrain 选择验证与真实 GPU 截图。技术结果不代替视觉审核。

const Helpers := preload("res://terrain_helpers.gd")
var failures: Array[String] = []
var checked_cells := 0
var checked_patterns := 0
var atlas_reports: Array[Dictionary] = []
var captures: Array[Dictionary] = []
var import_readbacks := {}
var scene: Node2D
var capture_enabled := false

func _initialize() -> void:
	capture_enabled = "--capture" in OS.get_cmdline_user_args()
	call_deferred("_run")

func _fail(condition: bool, message: String) -> void:
	if not condition and failures.size()<50: failures.append(message)

func _expected_mask(occupied: Dictionary, cell: Vector2i) -> int:
	# 独立按周围占用计算预期，不读当前TileData作为自己的答案。
	var value := 0
	for bit in range(8):
		var active := occupied.has(cell+Helpers.DIRECTIONS[bit])
		if bit%2 == 1:
			active = active and occupied.has(cell+Helpers.DIRECTIONS[(bit+7)%8]) and occupied.has(cell+Helpers.DIRECTIONS[(bit+1)%8])
		if active: value |= 1<<bit
	return value

func _check_layer(layer: TileMapLayer, occupied: Dictionary, tag: String) -> void:
	_fail(layer.get_used_cells().size()==occupied.size(),tag+": occupied count")
	for cell in occupied:
		var tile := layer.get_cell_tile_data(cell)
		_fail(tile != null,tag+": missing "+str(cell))
		if tile == null: continue
		checked_cells += 1
		var expected := _expected_mask(occupied,cell)
		_fail(int(tile.get_custom_data("blob_mask"))==expected,tag+": wrong selected mask "+str(cell))
		for bit in range(8):
			_fail(tile.get_terrain_peering_bit(Helpers.PEERING[bit])==(0 if expected&(1<<bit) else -1),tag+": peer "+str(cell)+" bit"+str(bit))

func _test_patterns(tile_set: TileSet, id: String) -> Dictionary:
	var layer := TileMapLayer.new()
	layer.tile_set = tile_set
	root.add_child(layer)
	var selected := {}
	for mask in range(256):
		var occupied := {Vector2i.ZERO:true}
		for bit in range(8):
			if mask&(1<<bit): occupied[Helpers.DIRECTIONS[bit]] = true
		Helpers.rebuild(layer,occupied)
		_check_layer(layer,occupied,id+" mask"+str(mask))
		var center := layer.get_cell_tile_data(Vector2i.ZERO)
		if center != null: selected[int(center.get_custom_data("blob_mask"))] = true
		checked_patterns += 1
	_fail(selected.size()==47,id+": complete47 masks not selected")
	var random := RandomNumberGenerator.new()
	random.seed = 20261005
	for trial in range(12):
		var occupied := {}
		for y in range(14):
			for x in range(20):
				if random.randf()<0.62: occupied[Vector2i(x,y)] = true
		Helpers.rebuild(layer,occupied)
		_check_layer(layer,occupied,id+" random draw"+str(trial))
		var erase_cells: Array = occupied.keys()
		for index in range(0,erase_cells.size(),3): occupied.erase(erase_cells[index])
		Helpers.rebuild(layer,occupied)
		_check_layer(layer,occupied,id+" random erase"+str(trial))
	layer.free()
	var masks: Array = selected.keys()
	masks.sort()
	return {"raw_neighborhood_cases":256,"canonical_masks_selected":masks,"random_draw_cases":12,"random_erase_cases":12}

func _verify_resource(tile_set: TileSet, atlas: Dictionary, catalog: Dictionary) -> void:
	var id := str(atlas.id)
	_fail(tile_set.tile_size==Vector2i(128,128),id+": tile size")
	_fail(tile_set.get_terrain_set_mode(0)==TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES,id+": terrain mode")
	var source := tile_set.get_source(0) as TileSetAtlasSource
	_fail(source.get_tiles_count()==47,id+":47tiles count")
	_fail(source.use_texture_padding,id+":padding disabled")
	_fail(source.texture_region_size==Vector2i(128,128),id+": region size")
	_fail(source.texture.get_size()==Vector2(1536,512),id+":12x4 dimensions")
	_fail(FileAccess.get_sha256("res://inputs/"+str(atlas.texture))==str(atlas.sha256),id+": copied PNG SHA")
	# 读取引擎实际纹理，与原始PNG逐像素比较Alpha和可见RGB。
	var original := Image.new()
	_fail(original.load_png_from_buffer(FileAccess.get_file_as_bytes("res://inputs/"+str(atlas.texture)))==OK,id+": raw PNG decode")
	var imported := source.texture.get_image()
	original.convert(Image.FORMAT_RGBA8)
	imported.convert(Image.FORMAT_RGBA8)
	var first := original.get_data()
	var second := imported.get_data()
	var alpha_differences := 0
	var visible_rgb_differences := 0
	_fail(first.size()==second.size(),id+": import pixel buffer size")
	if first.size()==second.size():
		for index in range(0,first.size(),4):
			if first[index+3] != second[index+3]: alpha_differences += 1
			if max(first[index+3],second[index+3])>0 and (first[index]!=second[index] or first[index+1]!=second[index+1] or first[index+2]!=second[index+2]): visible_rgb_differences += 1
	_fail(alpha_differences==0 and visible_rgb_differences==0,id+": import changes visible pixels")
	import_readbacks[id] = {"compared_pixels":1536*512,"alpha_differences":alpha_differences,"visible_rgb_differences":visible_rgb_differences,"unchanged":alpha_differences==0 and visible_rgb_differences==0}
	var coords := {}
	var masks := {}
	for entry in atlas.tiles:
		var coord := Vector2i(int(entry.coord[0]),int(entry.coord[1]))
		_fail(not coords.has(coord),id+": duplicated coordinate")
		_fail(not masks.has(int(entry.mask)),id+": duplicated mask")
		coords[coord] = true
		masks[int(entry.mask)] = true
		_fail(source.has_tile(coord),id+": missing official slot "+str(coord))
		if source.has_tile(coord): _fail(int(source.get_tile_data(coord,0).get_custom_data("blob_mask"))==int(entry.mask),id+": slot mask mismatch")
	var blank := Vector2i(int(catalog.blank_coord[0]),int(catalog.blank_coord[1]))
	_fail(not source.has_tile(blank),id+": official blank slot used")
	var blank_image := source.texture.get_image().get_region(Rect2i(blank*128,Vector2i(128,128)))
	for y in range(128):
		for x in range(128):
			if blank_image.get_pixel(x,y).a != 0:
				_fail(false,id+": blank slot contains alpha")
				return

func _wait_draw() -> void:
	await process_frame
	await process_frame
	if capture_enabled: await RenderingServer.frame_post_draw

func _capture(name: String) -> void:
	if not capture_enabled: return
	await _wait_draw()
	var image := root.get_texture().get_image()
	var filename := "res://"+name+".png"
	_fail(image.save_png(filename)==OK,"GPU save "+name)
	captures.append({"path":name+".png","size":[image.get_width(),image.get_height()],"sha256":FileAccess.get_sha256(filename),"render_backend":RenderingServer.get_current_rendering_method(),"source":"ViewportTexture GPU readback"})

func _mouse_button(position: Vector2, button: int, pressed: bool) -> void:
	var event := InputEventMouseButton.new()
	event.position = position
	event.global_position = position
	event.button_index = button
	event.pressed = pressed
	# 通过Viewport实际输入分发进入交互脚本，而非直接改占用数据。
	root.push_input(event)
	await process_frame

func _run() -> void:
	var catalog := Helpers.read_catalog()
	_fail(int(catalog.tile_size)==128 and int(catalog.logical_tile_size)==32,"catalog logical sizes")
	_fail(int(catalog.columns)==12 and int(catalog.rows)==4,"catalog official slots")
	for atlas in catalog.atlases:
		var tile_set := Helpers.make_tileset(atlas)
		var path := "res://"+str(atlas.id)+"_terrain.tres"
		_fail(ResourceSaver.save(tile_set,path)==OK,"save "+path)
		tile_set = ResourceLoader.load(path,"TileSet",ResourceLoader.CACHE_MODE_IGNORE)
		_verify_resource(tile_set,atlas,catalog)
		var checks := _test_patterns(tile_set,str(atlas.id))
		atlas_reports.append({"id":str(atlas.id),"texture":str(atlas.texture),"source_sha256":str(atlas.sha256),"saved_resource":path,"resource_sha256":FileAccess.get_sha256(path),"new_sample_count":int(atlas.get("new_sample_count",0)),"reused_v007_count":int(atlas.get("reused_v007_count",47)),"terrain_checks":checks,"source_import_readback":import_readbacks.get(str(atlas.id),{})})
	scene = load("res://review.tscn").instantiate()
	root.add_child(scene)
	await _wait_draw()
	for layer in scene.layers:
		_fail(layer.scale==Vector2.ONE*0.25,"layer scale")
		_check_layer(layer,scene.occupied,"interactive initial "+str(layer.name))
	await _capture("initial_gpu")
	var new_cell := Vector2i(19,13)
	var click_position: Vector2 = scene.screen_position_for_cell(new_cell)
	await _mouse_button(click_position,MOUSE_BUTTON_LEFT,true)
	await _mouse_button(click_position,MOUSE_BUTTON_LEFT,false)
	_fail(scene.occupied.has(new_cell),"left input paint failed")
	_fail(scene.paint_event_count>0,"left handler not dispatched")
	for layer in scene.layers: _check_layer(layer,scene.occupied,"interactive paint "+str(layer.name))
	await _capture("paint_gpu")
	await _mouse_button(click_position,MOUSE_BUTTON_RIGHT,true)
	await _mouse_button(click_position,MOUSE_BUTTON_RIGHT,false)
	_fail(not scene.occupied.has(new_cell),"right input erase failed")
	_fail(scene.erase_event_count>0,"right handler not dispatched")
	# 再擦一块内部格，真正检验新凹洞及周围角重选。
	var inner_cell := Vector2i(3,3)
	var inner_position: Vector2 = scene.screen_position_for_cell(inner_cell)
	await _mouse_button(inner_position,MOUSE_BUTTON_RIGHT,true)
	await _mouse_button(inner_position,MOUSE_BUTTON_RIGHT,false)
	_fail(not scene.occupied.has(inner_cell),"inner erase failed")
	for layer in scene.layers: _check_layer(layer,scene.occupied,"interactive erase "+str(layer.name))
	await _capture("erase_gpu")
	for count in range(7):
		await _mouse_button(Vector2(320,300),MOUSE_BUTTON_WHEEL_UP,true)
		await _mouse_button(Vector2(320,300),MOUSE_BUTTON_WHEEL_UP,false)
	_fail(scene.camera.zoom==Vector2.ONE*4,"wheel max4 zoom failed")
	_fail(scene.zoom_event_count>=7,"wheel handler not dispatched")
	scene.camera.position = Vector2(216,276)
	await _capture("baseline_zoom4_gpu")
	if scene.layers.size()>1:
		scene.camera.position = Vector2(984,276)
		await _capture("trial_zoom4_gpu")
	var report := {"status":"TECHNICAL_VALIDATION_PASSED_VISUAL_REVIEW_PENDING" if failures.is_empty() else "VALIDATION_FAILED","engine":Engine.get_version_info(),"catalog_sha256":FileAccess.get_sha256("res://inputs/catalog.json"),"standalone_project":true,"original_project_modified":false,"autoload_count":0,"official_layout":[12,4],"texture_tile_size":128,"logical_world_cell_size":32,"layer_scale":0.25,"padding":true,"terrain_mode":"Match Corners And Sides","checked_neighborhood_patterns":checked_patterns,"checked_cells":checked_cells,"atlases":atlas_reports,"actual_input":{"paint_events":scene.paint_event_count,"erase_events":scene.erase_event_count,"wheel_events":scene.zoom_event_count,"left_brush_checked":true,"right_brush_and_hole_rebuild_checked":true,"wheel_zoom4_checked":true},"gpu_capture_requested":capture_enabled,"gpu_captures":captures,"visual_review_approved":false,"user_visual_approval":false,"warning":"Trial is a mixed atlas:42 legacy v007 tiles +5 new visual samples; 47 masks coverage does not mean47 newly generated art or seamless interfaces.","failures":failures,"script_sha256":FileAccess.get_sha256("res://validate.gd"),"helper_sha256":FileAccess.get_sha256("res://terrain_helpers.gd"),"painter_sha256":FileAccess.get_sha256("res://painter.gd")}
	var file := FileAccess.open("res://validation.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t")+"\n")
	print(JSON.stringify({"status":report.status,"checked_cells":checked_cells,"captures":captures.size(),"failures":failures}))
	quit(0 if failures.is_empty() else 1)
