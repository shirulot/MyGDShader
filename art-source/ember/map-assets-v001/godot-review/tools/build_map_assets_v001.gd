extends SceneTree
## 三张概念地图的真实地板生产。默认注册原图并生成六层 PNG；
## 导入后 -- --resources 创建可铺刷原生场景。Props 节点由独立道具装配器填充。
## floor/bridge 的拓扑、8world 压顶及40world 双格桥沿用已验证的原画像素 compiler。

const OUT := "res://assets/ember/map_assets_v001/floors/"
const SOURCE := "res://art-source/ember/map-assets-v001/masters/"
const BASE := "res://assets/ember/environment/reference_floor_v002/"
const COMPILER := preload("res://scripts/ember/reference_floor_compiler_v002.gd")
const PAINTER_PATH := "res://scripts/ember/map_asset_painter_v001.gd"
const IDS := ["steel","control","service","rust","concrete","teal","ceramic","asphalt","brick","wood","sand","gravel","moss"]
const NAMES := ["蓝灰涂装钢板","浅灰控制区地板","深灰检修区防滑钢板","锈褐旧仓区钢板","浅砂混凝土地板","青绿旧涂层地板","磨损灰白地砖","旧沥青地板","砖红工业铺装","灰褐木栈道","压实沙土地板","灰色碎石地板","苔石地坪"]
const NEW_IDS := [0,3,4,5,6,9,10,11,12]
const MAP_IDS := ["tidal_port","dry_mine","overgrown_lab"]
const LAYERS := ["water","facade","floor","rim","bridge","heads"]
const AREA := Rect2i(0,0,24,16)
var layouts: Dictionary = {}
var catalog: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	_make_layouts()
	if "--resources" in OS.get_cmdline_user_args():
		catalog=JSON.parse_string(FileAccess.get_file_as_string(OUT+"catalog.json"))
		_create_resources()
		print("MAP_ASSET_RESOURCES_PASS: 3 distinct native brush scenes; Props reserved")
		quit(0)
		return
	if not _prepare_textures():
		quit(1)
		return
	var old: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(BASE+"catalog.json"))
	catalog={"revision":"map_assets_v001","status":"VISUAL_CANDIDATE","user_accepted":false,
		"texture_tile_size":128,"world_cell_size":[32,32],"layer_scale":[0.25,0.25],
		"atlases":old.atlases,"materials":[],"layout_cache":{},
		"material_index_tileset":OUT+"floor_materials_v001.tres","demo_bounds":[0,0,24,16],
		"bridge_visible_width_world":40,"bridge_shoulders_world":12,
		"shared_geometry":"Unchanged v002 Floor / Bridge 47 masks; material boundaries do not add curbs",
		"processing":"Full-image nearest 1024 registration; artist RGBA samples only"}
	var active_maps:=_selected_maps()
	if active_maps.size()<MAP_IDS.size() and FileAccess.file_exists(OUT+"catalog.json"):
		var existing: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OUT+"catalog.json"))
		catalog.layout_cache=existing.get("layout_cache",{})
	for index in range(IDS.size()):
		var path:=_material_texture(index)
		catalog.materials.append({"id":index,"key":IDS[index],"name":NAMES[index],"texture":path,"sha256":FileAccess.get_sha256(path),"period_texture_px":[1024,1024],"new_master":index in NEW_IDS})
	var compiler:=_compiler()
	for map_id: String in active_maps:
		var layout: Dictionary=layouts[map_id]
		compiler.materials.water_artist_period=_raw_png(_material_texture(10)) if map_id=="dry_mine" else _raw_png(BASE+"water_artist_period_v002.png")
		var started:=Time.get_ticks_msec()
		var images: Dictionary=compiler.build_visual_layers(layout.floor,layout.bridge,AREA,layout.materials)
		for id: String in LAYERS: assert(images[id].save_png(_context_path(map_id,id))==OK)
		var coverage_path:=OUT+map_id+"_coverage_v001.png"
		assert(images.coverage.save_png(coverage_path)==OK)
		var state:=_snapshot(layout)
		var cache: Dictionary={"signature":JSON.stringify(state).sha256_text(),"scene":_scene_path(map_id),"coverage":coverage_path,
			"background_material_id":10 if map_id=="dry_mine" else -1,"default_material_id":10 if map_id=="dry_mine" else (12 if map_id=="overgrown_lab" else 0),
			"floor_cells":layout.floor.size(),"bridge_cells":layout.bridge.size(),"rebuild_ms":Time.get_ticks_msec()-started}
		if map_id=="dry_mine":
			cache["fixed_nonwalkable_pit_cells"]=[9,4,7,7]
			_make_pit_cache()
		catalog.layout_cache[map_id]=cache
		_write_json(OUT+map_id+"_layout_v001.json",state)
		print("Compiled ",map_id," ",cache.rebuild_ms,"ms")
	_write_json(OUT+"catalog.json",catalog)
	print("MAP_ASSET_IMAGES_PASS: 9 new periods; 13 compatible material ids; 3 distinct maps")
	quit(0)


func _selected_maps() -> Array:
	## 布局微调只重编选中地图，避免重做无关缓存；示例 -- --map=tidal_port。
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--map="):
			var map_id:=argument.trim_prefix("--map=")
			assert(map_id in MAP_IDS,"Unknown concept map: "+map_id)
			return [map_id]
	return MAP_IDS.duplicate()


func _rect(target: Dictionary,rect: Rect2i) -> void:
	for y in range(rect.position.y,rect.end.y):
		for x in range(rect.position.x,rect.end.x): target[Vector2i(x,y)]=true


func _assign(layout: Dictionary,rect: Rect2i,id: int) -> void:
	for y in range(rect.position.y,rect.end.y):
		for x in range(rect.position.x,rect.end.x):
			var cell:=Vector2i(x,y)
			if layout.floor.has(cell):
				if id==0: layout.materials.erase(cell)
				else: layout.materials[cell]=id


func _make_layouts() -> void:
	var port: Dictionary={"floor":{},"bridge":{},"materials":{}}
	for rect in [Rect2i(1,1,5,14),Rect2i(6,2,10,3),Rect2i(6,7,10,3),Rect2i(6,12,13,3),Rect2i(18,5,5,6)]: _rect(port.floor,rect)
	for rect in [Rect2i(13,5,2,2),Rect2i(13,10,2,2),Rect2i(16,7,2,2)]: _rect(port.bridge,rect)
	_assign(port,Rect2i(2,2,3,10),4)
	_assign(port,Rect2i(6,12,11,3),9)
	layouts.tidal_port=port
	var mine: Dictionary={"floor":{},"bridge":{},"materials":{}}
	_rect(mine.floor,Rect2i(1,1,22,13))
	# 固定岩坑是非步行空域，桥的40world可见脚印仍由真实 compiler 派生。
	for y in range(4,11):
		for x in range(9,16): mine.floor.erase(Vector2i(x,y))
	_rect(mine.floor,Rect2i(1,14,7,1)); _rect(mine.floor,Rect2i(18,14,5,1))
	_rect(mine.bridge,Rect2i(9,7,7,2))
	_assign(mine,AREA,10)
	_assign(mine,Rect2i(2,2,6,4),11)
	_assign(mine,Rect2i(17,2,5,5),3)
	_assign(mine,Rect2i(1,11,22,3),0)
	_assign(mine,Rect2i(1,14,7,1),4); _assign(mine,Rect2i(18,14,5,1),4)
	layouts.dry_mine=mine
	var lab: Dictionary={"floor":{},"bridge":{},"materials":{}}
	for rect in [Rect2i(1,1,8,5),Rect2i(14,1,9,5),Rect2i(6,6,3,5),Rect2i(17,6,3,5),Rect2i(4,11,19,3),Rect2i(10,7,4,3),Rect2i(10,14,3,2)]: _rect(lab.floor,rect)
	for rect in [Rect2i(9,3,5,2),Rect2i(14,8,3,2)]: _rect(lab.bridge,rect)
	_assign(lab,AREA,12)
	_assign(lab,Rect2i(15,1,6,4),6)
	_assign(lab,Rect2i(17,5,3,9),5)
	_assign(lab,Rect2i(7,11,6,3),6)
	_assign(lab,Rect2i(10,14,3,2),9)
	layouts.overgrown_lab=lab


func _prepare_textures() -> bool:
	var entries: Array=[]
	for index: int in NEW_IDS:
		var source: String=SOURCE+"floor_"+IDS[index]+".png"
		if not FileAccess.file_exists(source):
			push_error("Missing artist master: "+source)
			return false
		var image:=_raw_png(source)
		if image.is_empty(): return false
		var size:=image.get_size()
		if size!=Vector2i(1024,1024): image.resize(1024,1024,Image.INTERPOLATE_NEAREST)
		var output:=_material_texture(index)
		assert(image.save_png(output)==OK)
		entries.append({"id":index,"key":IDS[index],"source":source,"source_size":[size.x,size.y],"source_sha256":FileAccess.get_sha256(source),"output":output,"output_size":[1024,1024],"processing":"Full-image nearest registration","pixel_policy":"Original artist RGBA samples; no recolour, painting, palette quantization or invented joints","structured_seams":"World-phase continuous artist source; exact plank/tile counts are not asserted","period_wrap_observation":_wrap_metrics(image)})
	if not FileAccess.file_exists(SOURCE+"pit_rock.png"):
		push_error("Missing actual rock pit master")
		return false
	var pit:=_raw_png(SOURCE+"pit_rock.png")
	var pit_size:=pit.get_size()
	if pit_size!=Vector2i(1024,1024): pit.resize(1024,1024,Image.INTERPOLATE_NEAREST)
	assert(pit.save_png(OUT+"pit_rock_period_v001.png")==OK)
	entries.append({"key":"pit_rock","source":SOURCE+"pit_rock.png","source_size":[pit_size.x,pit_size.y],"source_sha256":FileAccess.get_sha256(SOURCE+"pit_rock.png"),"output":OUT+"pit_rock_period_v001.png","output_size":[1024,1024],"processing":"Full-image nearest registration"})
	_write_json(OUT+"source_processing_v001.json",{"sources":entries,"new_floor_ids":NEW_IDS,"unchanged_floor_ids":[1,2,7,8],"shared_compiler_sha256":FileAccess.get_sha256("res://scripts/ember/reference_floor_compiler_v002.gd")})
	var index_image:=Image.create(IDS.size()*128,128,false,Image.FORMAT_RGBA8)
	for index in range(IDS.size()): index_image.blit_rect(_raw_png(_material_texture(index)),Rect2i(0,0,128,128),Vector2i(index*128,0))
	assert(index_image.save_png(OUT+"floor_material_index_v001.png")==OK)
	return true


func _material_texture(index: int) -> String:
	if index in NEW_IDS: return OUT+"floor_"+IDS[index]+"_period_v001.png"
	var revision:="v003" if index<=2 else "v005"
	return "res://assets/ember/environment/reference_floor_"+revision+"/floor_"+IDS[index]+"_period_"+revision+".png"


func _raw_png(path: String) -> Image:
	var image:=Image.new()
	assert(image.load_png_from_buffer(FileAccess.get_file_as_bytes(path))==OK,"Invalid artist PNG: "+path)
	image.convert(Image.FORMAT_RGBA8)
	return image


func _wrap_metrics(image: Image) -> Dictionary:
	## 只观测周期边缘色差，不修改生图像素；数字不能取代实际地图视觉检查。
	var wrap_x:=0.0; var wrap_y:=0.0; var internal_x:=0.0; var internal_y:=0.0
	for index in range(1024):
		wrap_x+=_rgb_delta(image.get_pixel(1023,index),image.get_pixel(0,index))
		wrap_y+=_rgb_delta(image.get_pixel(index,1023),image.get_pixel(index,0))
		for seam in [127,255,383,511,639,767,895]:
			internal_x+=_rgb_delta(image.get_pixel(seam,index),image.get_pixel(seam+1,index))
			internal_y+=_rgb_delta(image.get_pixel(index,seam),image.get_pixel(index,seam+1))
	return {"mean_rgb_delta_wrap_x":wrap_x/1024.0,"mean_rgb_delta_wrap_y":wrap_y/1024.0,
		"mean_rgb_delta_internal_cell_x":internal_x/7168.0,"mean_rgb_delta_internal_cell_y":internal_y/7168.0,
		"interpretation":"Measured artist-period borders; requires actual GPU visual review, not a claim of exact artist seam matching"}


func _rgb_delta(a: Color,b: Color) -> float:
	return (absf(a.r-b.r)+absf(a.g-b.g)+absf(a.b-b.b))/3.0


func _compiler() -> RefCounted:
	var compiler:=COMPILER.new()
	compiler.load_materials()
	for index in range(IDS.size()): compiler.floor_material_periods[index]=_raw_png(_material_texture(index))
	return compiler


func _make_pit_cache() -> void:
	var period:=_raw_png(OUT+"pit_rock_period_v001.png")
	var image:=Image.create(7*128,7*128,false,Image.FORMAT_RGBA8)
	for y in range(image.get_height()):
		for x in range(image.get_width()): image.set_pixel(x,y,period.get_pixel(posmod(x+9*128,1024),posmod(y+4*128,1024)))
	assert(image.save_png(OUT+"dry_mine_fixed_pit_v001.png")==OK)


func _context_path(map_id: String,id: String) -> String:
	return OUT+map_id+"_"+id+"_context_v001.png"


func _scene_path(map_id: String) -> String:
	return "res://scenes/ember/map_assets_"+map_id+"_v001.tscn"


func _snapshot(layout: Dictionary) -> Dictionary:
	return {"version":3,"bounds":[0,0,24,16],"floor":_ordered(layout.floor,false),"bridge":_ordered(layout.bridge,false),"materials":_ordered(layout.materials,true)}


func _ordered(cells: Dictionary,with_material: bool) -> Array:
	var keys:=cells.keys()
	keys.sort_custom(func(a: Vector2i,b: Vector2i)->bool: return a.y<b.y if a.y!=b.y else a.x<b.x)
	var result: Array=[]
	for cell: Vector2i in keys: result.append([cell.x,cell.y,int(cells[cell])] if with_material else [cell.x,cell.y])
	return result


func _make_tileset(path: String,size: Vector2i) -> TileSet:
	var set:=TileSet.new(); set.tile_size=Vector2i(128,128)
	var source:=TileSetAtlasSource.new(); source.texture=load(path); source.texture_region_size=Vector2i(128,128)
	assert(source.texture!=null,"Run --import before --resources")
	set.add_source(source,0)
	for y in range(size.y):
		for x in range(size.x): source.create_tile(Vector2i(x,y))
	return set


func _create_resources() -> void:
	assert(ResourceSaver.save(_make_tileset(OUT+"floor_material_index_v001.png",Vector2i(IDS.size(),1)),OUT+"floor_materials_v001.tres")==OK)
	for map_id: String in _selected_maps():
		var layout: Dictionary=layouts[map_id]
		var demo:=Node2D.new(); demo.name="MapAssets"+map_id.to_pascal_case()+"V001"
		demo.set_script(load(PAINTER_PATH)); demo.set("baked_layout_id",map_id)
		for id in ["floor","bridge"]:
			var layer:=TileMapLayer.new(); layer.name=str(id).capitalize(); layer.scale=Vector2(0.25,0.25); layer.visible=false
			layer.tile_set=load(BASE+str(id)+"_terrain_v002.tres")
			demo.add_child(layer); layer.owner=demo
			var lookup: Dictionary={}
			for atlas: Dictionary in catalog.atlases:
				if atlas.id==id:
					for tile: Dictionary in atlas.tiles: lookup[int(tile.mask)]=Vector2i(int(tile.coord[0]),int(tile.coord[1]))
			var compiler:=COMPILER.new()
			for cell: Vector2i in layout[id]: layer.set_cell(cell,0,lookup[compiler.mask_at(layout[id],cell)])
		var inputs:=TileMapLayer.new(); inputs.name="FloorMaterials"; inputs.visible=false; inputs.scale=Vector2(0.25,0.25); inputs.tile_set=load(OUT+"floor_materials_v001.tres")
		demo.add_child(inputs); inputs.owner=demo
		for cell: Vector2i in layout.materials: inputs.set_cell(cell,0,Vector2i(int(layout.materials[cell]),0))
		for index in range(LAYERS.size()):
			var id: String=LAYERS[index]
			var path:=OUT+map_id+"_"+id+"_context_v001.tres"
			assert(ResourceSaver.save(_make_tileset(_context_path(map_id,id),AREA.size),path)==OK)
			var layer:=TileMapLayer.new(); layer.name=id.capitalize()+"Context"; layer.scale=Vector2(0.25,0.25); layer.z_index=index; layer.tile_set=load(path)
			demo.add_child(layer); layer.owner=demo
			for y in range(AREA.size.y):
				for x in range(AREA.size.x): layer.set_cell(Vector2i(x,y),0,Vector2i(x,y))
		if map_id=="dry_mine":
			# 绘制在 water 背景之上、facade / Floor 之下；空域保持非步行，用户后来铺Floor可覆盖岩坑。
			var pit:=Sprite2D.new(); pit.name="FixedNonwalkableRockPit"; pit.centered=false; pit.position=Vector2(9,4)*32; pit.scale=Vector2(0.25,0.25); pit.texture=load(OUT+"dry_mine_fixed_pit_v001.png"); pit.z_index=0
			demo.add_child(pit); pit.owner=demo
		var props:=Node2D.new(); props.name="Props"; props.z_index=6
		demo.add_child(props); props.owner=demo
		var camera:=Camera2D.new(); camera.name="Camera2D"; camera.position=Vector2(384,256); camera.zoom=Vector2(2,2)
		demo.add_child(camera); camera.owner=demo
		var packed:=PackedScene.new(); assert(packed.pack(demo)==OK); assert(ResourceSaver.save(packed,_scene_path(map_id))==OK)
		demo.free()


func _write_json(path: String,data: Dictionary) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	assert(file!=null)
	file.store_string(JSON.stringify(data,"\t")+"\n")
