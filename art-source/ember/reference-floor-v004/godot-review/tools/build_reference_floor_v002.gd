extends SceneTree
## v002 真实 artist 像素拼装器。这里仅做原图裁切、nearest 缩放和占用遮罩。
## 不减去局部均值，不量化色阶，不以平色重画生图中的材质。
## 逻辑世界格 32，纹理格 128：成品 TileMapLayer 缩放 0.25。
## 当前默认导出两岛实拼；补全资源在相同来源模块上构建。

const TILE := 128
const WORLD_TILE := 32
const OUT := "res://assets/ember/environment/reference_floor_v002/"
const SOURCE := "res://art-source/ember/reference-floor-v002/platform_modules_master_v001.png"
const BRIDGE_SOURCE := "res://art-source/ember/reference-floor-v002/bridge_modules_master_v001.png"
const CORNER_SOURCE := "res://art-source/ember/reference-floor-v002/corner_modules_master_v001.png"
const COMPILER := preload("res://scripts/ember/reference_floor_compiler_v002.gd")
const SPEC := "res://docs/shader-learning/autotile-neighborhoods-v002.json"
const PEERING := [TileSet.CELL_NEIGHBOR_TOP_SIDE,TileSet.CELL_NEIGHBOR_TOP_RIGHT_CORNER,TileSet.CELL_NEIGHBOR_RIGHT_SIDE,TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER,TileSet.CELL_NEIGHBOR_BOTTOM_SIDE,TileSet.CELL_NEIGHBOR_BOTTOM_LEFT_CORNER,TileSet.CELL_NEIGHBOR_LEFT_SIDE,TileSet.CELL_NEIGHBOR_TOP_LEFT_CORNER]
const LAYERS := ["water","facade","floor","rim","bridge","heads"]
var source_rois: Array = []
var tile_lookup: Dictionary = {}
var catalog: Dictionary = {}
const APPROVED := "res://art-source/ember/pixel-standard-v002/previews/scene_preview_v001.png"
const WATER_SOURCE := "res://art-source/ember/reference-floor-v002/water_texture_master_v001.png"
const CLEAR := Color(0,0,0,0)
const DIRECTIONS := [Vector2i.UP,Vector2i(1,-1),Vector2i.RIGHT,Vector2i(1,1),Vector2i.DOWN,Vector2i(-1,1),Vector2i.LEFT,Vector2i(-1,-1)]
const FACE_DEPTH := 128
const CAP := 32
const BRIDGE_INSET := 48
const W := 24*TILE
const H := 16*TILE

var _floor: Dictionary = {}
var _bridge: Dictionary = {}
func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	_seed_layout()
	if "--resources" in OS.get_cmdline_user_args():
		catalog = JSON.parse_string(FileAccess.get_file_as_string(OUT+"catalog.json"))
		for atlas: Dictionary in catalog.atlases:
			var set := _terrain_set(atlas)
			assert(ResourceSaver.save(set,OUT+atlas.id+"_terrain_v002.tres")==OK)
		_create_scene()
		var capture_ok := true
		if "--capture" in OS.get_cmdline_user_args(): capture_ok = await _capture_scene()
		print("REFERENCE_RESOURCES_PASS" if capture_ok else "REFERENCE_GPU_CAPTURE_FAIL")
		quit(0 if capture_ok else 1)
		return
	_prepare_modules()
	var compiler := COMPILER.new()
	compiler.load_materials()
	var started := Time.get_ticks_msec()
	var images := compiler.build_visual_layers(_floor,_bridge,Rect2i(0,0,24,16))
	var elapsed := Time.get_ticks_msec()-started
	for id: String in LAYERS: images[id].save_png(OUT+id+"_context_atlas_v002.png")
	images.coverage.save_png(OUT+"union_coverage_v002.png")
	var composed := compiler.flatten_layers(images)
	composed.save_png(OUT+"two_islands_native_v002.png")
	composed.resize(1536,1024,Image.INTERPOLATE_NEAREST)
	composed.save_png(OUT+"two_islands_display_v002.png")
	catalog = {"revision":"reference_floor_v002","status":"VISUAL_CANDIDATE","user_accepted":false,
		"texture_tile_size":128,"tile_size":128,"world_cell_size":[32,32],"layer_scale":[0.25,0.25],
		"context_contract":"Ordinary derived TileMap tiles from shared compiler after semantic Floor/Bridge edits; not native Terrain candidates.",
		"demo_layout_signature":_seed_signature(),
		"atlases":[],"context_layers":[],"source_rois":source_rois,"demo_rebuild_ms":elapsed,
		"demo_bounds":[0,0,24,16],"bridge_default_brush_width":2,"bridge_visible_width_world":40,"bridge_single_width_world":20}
	_build_base_atlases(compiler)
	for id: String in LAYERS: catalog.context_layers.append({"id":id,"texture":OUT+id+"_context_atlas_v002.png","tile_size":128,"mode":"ordinary_derived"})
	_write_json(OUT+"catalog.json",catalog)
	_write_json(OUT+"source_processing_v002.json",{"status":"VISUAL_CANDIDATE","source_rois":source_rois,
		"source_sha256":FileAccess.get_sha256(SOURCE),"bridge_source_sha256":FileAccess.get_sha256(BRIDGE_SOURCE),"corner_source_sha256":FileAccess.get_sha256(CORNER_SOURCE),
		"processing":"Actual artist RGBA crop, nearest resize, binary alpha masking; no local mean removal or palette quantization.",
		"floor_period_texture_px":1024,"demo_rebuild_ms":elapsed,"world_cell_size":32,"texture_tile_size":128,
		"cap_world_px":8,"south_facade_world_px":32,"water_scope":"independent reference-based artist water source; auxiliary display"})
	print("REFERENCE_IMAGES_PASS: floor47 bridge47, demo "+str(elapsed)+"ms")
	quit(0)


func _save_module(source: Image,source_path: String,id: String,rect: Rect2i,size: Vector2i) -> Image:
	var image := _crop(source,rect,size)
	assert(image.save_png(OUT+id+"_v002.png")==OK)
	source_rois.append({"id":id,"source":source_path,"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"output_size":[size.x,size.y],"resampling":"nearest"})
	return image


func _prepare_modules() -> void:
	var source := Image.load_from_file(ProjectSettings.globalize_path(SOURCE))
	_save_module(source,SOURCE,"floor_albedo_period",Rect2i(32,32,448,442),Vector2i(1024,1024))
	_save_module(source,SOURCE,"south_cap_source",Rect2i(536,262,461,47),Vector2i(512,32))
	_save_module(source,SOURCE,"north_cap_source",Rect2i(32,710,448,60),Vector2i(512,32))
	_save_module(source,SOURCE,"east_cap_source",Rect2i(878,552,62,390),Vector2i(32,512))
	_save_module(source,SOURCE,"south_face_source",Rect2i(536,309,461,158),Vector2i(512,128))
	_save_module(source,SOURCE,"east_face_source",Rect2i(946,534,31,452),Vector2i(32,512))
	var water := Image.load_from_file(ProjectSettings.globalize_path(WATER_SOURCE))
	_save_module(water,WATER_SOURCE,"water_artist_period",Rect2i(Vector2i.ZERO,water.get_size()),water.get_size()*2)
	var bridge := Image.load_from_file(ProjectSettings.globalize_path(BRIDGE_SOURCE))
	_save_module(bridge,BRIDGE_SOURCE,"bridge_horizontal_artist",Rect2i(90,166,590,178),Vector2i(512,160))
	_save_module(bridge,BRIDGE_SOURCE,"bridge_vertical_artist",Rect2i(1066,52,168,368),Vector2i(160,512))
	# 将桥的真实主体与真实方向边梁分离；所有L/T/X共用world phase，内部不保留整框。
	# 原始格栅是接近正方形的网孔；保持ROI的横纵比例，不能把48px高拉到128px。
	_save_module(bridge,BRIDGE_SOURCE,"bridge_grate_period",Rect2i(100,202,290,48),Vector2i(512,84))
	_save_module(bridge,BRIDGE_SOURCE,"bridge_beam_n",Rect2i(92,166,580,27),Vector2i(512,24))
	_save_module(bridge,BRIDGE_SOURCE,"bridge_beam_s",Rect2i(92,296,580,47),Vector2i(512,24))
	_save_module(bridge,BRIDGE_SOURCE,"bridge_beam_w",Rect2i(1067,52,27,368),Vector2i(24,512))
	_save_module(bridge,BRIDGE_SOURCE,"bridge_beam_e",Rect2i(1209,52,25,368),Vector2i(24,512))
	var left := _save_module(bridge,BRIDGE_SOURCE,"bridge_head_left_artist",Rect2i(24,150,66,195),Vector2i(48,160))
	var right := _save_module(bridge,BRIDGE_SOURCE,"bridge_head_right_artist",Rect2i(680,150,66,195),Vector2i(48,160))
	var north := _save_module(bridge,BRIDGE_SOURCE,"bridge_head_north_artist",Rect2i(1060,8,190,48),Vector2i(160,48))
	var south := _save_module(bridge,BRIDGE_SOURCE,"bridge_head_south_artist",Rect2i(1060,422,190,64),Vector2i(160,48))
	for image: Image in [left,right]:
		for y in range(160):
			for x in range(48):
				if (y<8 or y>=152) and (x<6 or x>=42):
					var p := image.get_pixel(x,y); p.a=0; image.set_pixel(x,y,p)
	left.save_png(OUT+"bridge_head_left_artist_v002.png")
	right.save_png(OUT+"bridge_head_right_artist_v002.png")
	for image: Image in [north,south]:
		for y in range(48):
			for x in range(160):
				if (x<8 or x>=152) and (y<6 or y>=42):
					var p := image.get_pixel(x,y); p.a=0; image.set_pixel(x,y,p)
	north.save_png(OUT+"bridge_head_north_artist_v002.png")
	south.save_png(OUT+"bridge_head_south_artist_v002.png")
	_prepare_corners()


func _prepare_corners() -> void:
	var source := Image.load_from_file(ProjectSettings.globalize_path(CORNER_SOURCE))
	var rois := {"outer_nw":Rect2i(55,76,104,84),"outer_ne":Rect2i(610,76,112,84),"outer_sw":Rect2i(851,224,112,97),"outer_se":Rect2i(1346,227,104,97),"inner_nw":Rect2i(159,673,81,83),"inner_ne":Rect2i(545,673,81,83),"inner_sw":Rect2i(947,680,82,73),"inner_se":Rect2i(1276,680,82,73)}
	for id: String in rois:
		var image := source.get_region(rois[id])
		var mask := PackedByteArray(); mask.resize(image.get_width()*image.get_height())
		for y in range(image.get_height()):
			for x in range(image.get_width()):
				var c := image.get_pixel(x,y)
				mask[y*image.get_width()+x]=1 if c.r>0.38 and c.r>c.b*0.99 and c.g>c.b*0.98 else 0
		for y in range(image.get_height()):
			for x in range(image.get_width()):
				var keep := false
				for dy in range(-3,4):
					for dx in range(-3,4):
						var q := Vector2i(x+dx,y+dy)
						if q.x>=0 and q.y>=0 and q.x<image.get_width() and q.y<image.get_height() and mask[q.y*image.get_width()+q.x]==1: keep=true
				var c := image.get_pixel(x,y); c.a=1.0 if keep else 0.0; image.set_pixel(x,y,c)
		image.resize(64,64,Image.INTERPOLATE_NEAREST)
		image.save_png(OUT+id+"_artist_v002.png")
		source_rois.append({"id":id,"source":CORNER_SOURCE,"rect":[rois[id].position.x,rois[id].position.y,rois[id].size.x,rois[id].size.y],"output_size":[64,64],"alpha":"warm cap segmentation +3px dilation to retain actual bolts; original RGB retained"})


func _build_base_atlases(compiler: RefCounted) -> void:
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SPEC))
	for id in ["floor","bridge"]:
		var atlas := Image.create(1024,768,false,Image.FORMAT_RGBA8); atlas.fill(CLEAR)
		var tiles: Array = []
		for entry: Dictionary in spec.area.tiles:
			var cells := {Vector2i(1,1):true}
			for bit in range(8):
				if int(entry.mask)&(1<<bit): cells[Vector2i(1,1)+DIRECTIONS[bit]]=true
			var images: Dictionary = compiler.build_visual_layers(cells if id=="floor" else {},cells if id=="bridge" else {},Rect2i(0,0,3,3))
			var tile: Image = images.floor.get_region(Rect2i(128,128,128,128)) if id=="floor" else images.bridge.get_region(Rect2i(128,128,128,128))
			if id=="floor": tile.blend_rect(images.rim,Rect2i(128,128,128,128),Vector2i.ZERO)
			var coord := Vector2i(int(entry.atlas_coord[0]),int(entry.atlas_coord[1])); atlas.blit_rect(tile,Rect2i(0,0,128,128),coord*128)
			tiles.append({"mask":int(entry.mask),"coord":[coord.x,coord.y]})
		var path: String = OUT+id+"_atlas_v002.png"; atlas.save_png(path)
		catalog.atlases.append({"id":id,"mode":"blob","texture":path,"tiles":tiles,"texture_tile_size":128,"native_terrain_base":true})


func _terrain_set(atlas: Dictionary) -> TileSet:
	var set := TileSet.new(); set.tile_size=Vector2i(128,128); set.add_terrain_set(); set.set_terrain_set_mode(0,TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES); set.add_terrain(0); set.set_terrain_name(0,0,str(atlas.id).capitalize())
	var source := TileSetAtlasSource.new(); source.texture=load(atlas.texture); source.texture_region_size=Vector2i(128,128); set.add_source(source,0)
	assert(source.texture!=null,"先 editor --import PNG，再 -- --resources")
	var lookup := {}
	for entry: Dictionary in atlas.tiles:
		var coord := Vector2i(int(entry.coord[0]),int(entry.coord[1])); source.create_tile(coord)
		var data := source.get_tile_data(coord,0); data.terrain_set=0; data.terrain=0
		for bit in range(8): data.set_terrain_peering_bit(PEERING[bit],0 if int(entry.mask)&(1<<bit) else -1)
		lookup[int(entry.mask)]=coord
	tile_lookup[atlas.id]=lookup
	return set


func _ordinary_set(path: String) -> TileSet:
	var set := TileSet.new(); set.tile_size=Vector2i(128,128)
	var source := TileSetAtlasSource.new(); source.texture=load(path); source.texture_region_size=Vector2i(128,128); set.add_source(source,0)
	for y in range(16):
		for x in range(24): source.create_tile(Vector2i(x,y))
	return set


func _create_scene() -> void:
	var demo := Node2D.new(); demo.name="ReferenceFloorSandboxV002"; demo.set_script(load("res://scripts/ember/reference_floor_painter_v002.gd"))
	var compiler := COMPILER.new()
	for id in ["floor","bridge"]:
		var input := TileMapLayer.new(); input.name=id.capitalize(); input.tile_set=load(OUT+id+"_terrain_v002.tres"); input.scale=Vector2(0.25,0.25); input.visible=false
		demo.add_child(input); input.owner=demo
		var cells: Dictionary = _floor if id=="floor" else _bridge
		for cell: Vector2i in cells: input.set_cell(cell,0,tile_lookup[id][compiler.mask_at(cells,cell)])
	for id: String in LAYERS:
		var set := _ordinary_set(OUT+id+"_context_atlas_v002.png"); ResourceSaver.save(set,OUT+id+"_context_v002.tres")
		var layer := TileMapLayer.new(); layer.name=id.capitalize()+"Context"; layer.tile_set=set; layer.scale=Vector2(0.25,0.25); layer.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
		demo.add_child(layer); layer.owner=demo
		for y in range(16):
			for x in range(24): layer.set_cell(Vector2i(x,y),0,Vector2i(x,y))
	var camera := Camera2D.new(); camera.name="Camera2D"; camera.position=Vector2(384,256); camera.zoom=Vector2(2,2); demo.add_child(camera); camera.owner=demo
	_add_details(demo)
	var packed := PackedScene.new(); assert(packed.pack(demo)==OK); assert(ResourceSaver.save(packed,"res://scenes/ember/reference_floor_sandbox_v002.tscn")==OK); demo.free()


func _capture_scene() -> bool:
	# GPU预览仅从真实TileMapLayer场景取Viewport，不以两岛flatten图充作截图。
	root.size=Vector2i(1536,1024); root.content_scale_size=Vector2i(1536,1024)
	var demo:=load("res://scenes/ember/reference_floor_sandbox_v002.tscn").instantiate() as Node2D
	root.add_child(demo)
	var hud:=demo.get_node_or_null("Help") as CanvasLayer
	if hud!=null: hud.visible=false
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var image:=root.get_texture().get_image()
	assert(image!=null and image.get_size()==Vector2i(1536,1024))
	image.save_png(OUT+"gpu_reference_scene_v002.png")
	# 第二次编辑会走ImageTexture.update，实测派生atlas padding缓存是否更新。
	var edits: Array=[]
	for cell: Vector2i in [Vector2i(12,3),Vector2i(14,3)]:
		# 真正擦出2×2洞，再连续扩大它；单行洞会被32world深立面遮住，不能当水色探针。
		for dy in range(2):
			for dx in range(2): demo.erase_cell(cell+Vector2i(dx,dy))
		demo.synchronize(); await process_frame; await process_frame; await RenderingServer.frame_post_draw
		image=root.get_texture().get_image()
		var point: Vector2i=(cell+Vector2i(0,1))*64+Vector2i(32,32)
		var actual:=image.get_pixelv(point)
		var expected: Image=demo.last_build.water
		var best:=99.0
		var exposed := true
		for id: String in ["facade","floor","rim","bridge","heads"]:
			if demo.last_build[id].get_pixelv(point*2).a>0.01: exposed=false
		for dy in range(2):
			for dx in range(2):
				var color:=expected.get_pixelv(point*2+Vector2i(dx,dy))
				best=minf(best,maxf(absf(actual.r-color.r),maxf(absf(actual.g-color.g),absf(actual.b-color.b))))
		edits.append({"stamp_anchor":[cell.x,cell.y],"stamp_size":[2,2],"probe_display_pixel":[point.x,point.y],"cpu_probe_exposes_water":exposed,"gpu_water_hole_matches_cpu":exposed and best<=3.0/255.0,"max_rgb_error":best,"rebuild_ms":demo.last_rebuild_ms})
	image.save_png(OUT+"gpu_dynamic_erase_v002.png")
	var all_pass: bool=edits.all(func(check: Dictionary) -> bool: return check.gpu_water_hole_matches_cpu)
	_write_json(OUT+"gpu_capture_v002.json",{"status":"PASS" if all_pass else "FAIL","dynamic_edits":edits,"renderer":RenderingServer.get_current_rendering_method(),"size":[1536,1024],"camera_zoom":2,"context_layers":6,"input_terrain_layers":2,"scene":"res://scenes/ember/reference_floor_sandbox_v002.tscn","render_contract":"actual TileMapLayer + TileSet external PNGs + independent source sprites; no full-scene Sprite"})
	demo.free()
	return all_pass


func _sprite(demo: Node2D,id: String,path: String,p: Vector2,s: Vector2) -> void:
	if not ResourceLoader.exists(path): return
	var sprite := Sprite2D.new(); sprite.name=id; sprite.texture=load(path); sprite.position=p; sprite.scale=s; sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	# 细缝/检修口属于顶面，必须位于人物与设备下方，不能在玩家头部画出一条缝。
	sprite.z_index=3 if id.begins_with("Seam") or id=="Hatch" else 5
	demo.add_child(sprite); sprite.owner=demo


func _add_details(demo: Node2D) -> void:
	# 以实际非透明主体而非整张画布测比例：设备主体约116px高，2倍展示后接近参考267px。
	_sprite(demo,"Robot", "res://assets/ember/characters/robot/robot_idle_down_v001.png", Vector2(349,200),Vector2(0.8,0.8))
	_sprite(demo,"Station", "res://assets/ember/buildings/station/station_base_v001.png", Vector2(608,95),Vector2(1.15,1.15))
	_sprite(demo,"SeamA",OUT+"seam_horizontal_artist_v002.png",Vector2(311,146.5),Vector2(0.15,0.15))
	_sprite(demo,"SeamB",OUT+"seam_elbow_artist_v002.png",Vector2(555,260),Vector2(0.25,0.25))
	_sprite(demo,"Hatch",OUT+"grate_hatch_artist_v002.png",Vector2(700,187.5),Vector2(0.20,0.20))
	_sprite(demo,"LeftRailNorth",OUT+"rail_horizontal_artist_v002.png",Vector2(48,128),Vector2(0.2,0.2))
	_sprite(demo,"LeftRailSouth",OUT+"rail_horizontal_artist_v002.png",Vector2(48,240),Vector2(0.2,0.2))
	for index in range(4):
		_sprite(demo,"MainRailSouth"+str(index),OUT+"rail_horizontal_artist_v002.png",Vector2(376+90*index,464),Vector2(0.25,0.25))
	_sprite(demo,"MainRailBay",OUT+"rail_horizontal_artist_v002.png",Vector2(300,248),Vector2(0.125,0.125))


func _crop(source: Image,region: Rect2i,size: Vector2i) -> Image:
	assert(Rect2i(Vector2i.ZERO,source.get_size()).encloses(region))
	var image := source.get_region(region)
	if image.get_size() != size:
		image.resize(size.x,size.y,Image.INTERPOLATE_NEAREST)
	return image


func _seed_layout() -> void:
	# 参考构图：左侧小岛，中央二格桥，大平台南侧有凹湾和下层返回。
	for y in range(4,8):
		for x in range(0,3): _floor[Vector2i(x,y)] = true
	for y in range(1,15):
		for x in range(8,23):
			if x < 14 and y >= 8 and y < 12: continue
			if x < 10 and y >= 12: continue
			_floor[Vector2i(x,y)] = true
	for y in range(5,7):
		for x in range(3,8): _bridge[Vector2i(x,y)] = true


func _seed_signature() -> String:
	var arrays: Dictionary={}
	for id in ["floor","bridge"]:
		var cells: Dictionary=_floor if id=="floor" else _bridge
		var ordered:=cells.keys(); ordered.sort_custom(func(a: Vector2i,b: Vector2i)->bool: return a.y<b.y if a.y!=b.y else a.x<b.x)
		var result: Array=[]
		for cell: Vector2i in ordered: result.append([cell.x,cell.y])
		arrays[id]=result
	return JSON.stringify({"version":2,"bounds":[0,0,24,16],"floor":arrays.floor,"bridge":arrays.bridge}).sha256_text()


func _write_json(path: String,value: Dictionary) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	assert(file != null)
	file.store_string(JSON.stringify(value,"\t")+"\n")
