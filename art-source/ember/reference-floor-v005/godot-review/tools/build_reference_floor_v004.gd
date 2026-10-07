extends SceneTree
## 三种新表面共享已认可v002的几何、压顶、立面和桥口。
## 仅裁切/nearest注册真实生图，按统一世界相位拼装；不程序重绘材质。
## 默认生成PNG缓存；导入后 -- --resources 创建实际铺刷场景。

const OUT := "res://assets/ember/environment/reference_floor_v004/"
const SOURCE := "res://art-source/ember/reference-floor-v004/"
const BASE := "res://assets/ember/environment/reference_floor_v002/"
const PRIOR := "res://assets/ember/environment/reference_floor_v003/"
const COMPILER := preload("res://scripts/ember/reference_floor_compiler_v002.gd")
const LAYERS := ["water","facade","floor","rim","bridge","heads"]
const IDS := ["steel","control","service","rust","concrete","teal","ceramic"]
const NAMES := ["蓝灰涂装钢板","浅灰控制区地板","深灰检修区防滑钢板","锈褐旧仓区钢板","浅砂混凝土地板","青绿旧涂层地板","磨损灰白地砖"]
const NEW_IDS := [4,5,6]
const SCENE := "res://scenes/ember/reference_floor_sandbox_v004.tscn"
var floor_cells: Dictionary = {}
var bridge_cells: Dictionary = {}
var material_maps: Dictionary = {}
var catalog: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	_read_layout()
	if "--resources" in OS.get_cmdline_user_args():
		catalog = JSON.parse_string(FileAccess.get_file_as_string(OUT+"catalog.json"))
		_create_resources()
		var ok := true
		if "--capture" in OS.get_cmdline_user_args(): ok = await _capture()
		print("REFERENCE_V004_RESOURCES_PASS" if ok else "REFERENCE_V004_GPU_FAIL")
		quit(0 if ok else 1)
		return
	_prepare_textures()
	var compiler := _compiler()
	var started := Time.get_ticks_msec()
	var images: Dictionary = compiler.build_visual_layers(floor_cells,bridge_cells,Rect2i(0,0,24,16),material_maps.mixed)
	for id: String in LAYERS: images[id].save_png(OUT+id+"_context_atlas_v004.png")
	images.coverage.save_png(OUT+"union_coverage_v004.png")
	# 同构地图只替换floor图层，结构的其它五层直接复用，保持接口标准完全一致。
	for index: int in NEW_IDS:
		var image := _surface(compiler,images.coverage,index)
		image.save_png(OUT+IDS[index]+"_floor_context_atlas_v004.png")
	var old: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(BASE+"catalog.json"))
	catalog = {"revision":"reference_floor_v004","status":"VISUAL_CANDIDATE","user_accepted":false,
		"texture_tile_size":128,"world_cell_size":[32,32],"layer_scale":[0.25,0.25],
		"atlases":old.atlases,"material_index_tileset":OUT+"floor_materials_v004.tres",
		"materials":[],"layout_cache":{},"demo_bounds":[0,0,24,16],
		"bridge_visible_width_world":40,"bridge_shoulders_world":12,
		"shared_geometry":"v002 Floor/Bridge 47 masks; all materials share coping, facade, bridge heads and coverage",
		"demo_rebuild_ms":Time.get_ticks_msec()-started}
	for index in range(IDS.size()):
		var texture: String = _material_texture(index)
		catalog.materials.append({"id":index,"key":IDS[index],"name":NAMES[index],"texture":texture,"sha256":FileAccess.get_sha256(texture),"period_texture_px":[1024,1024]})
	for id: String in material_maps:
		catalog.layout_cache[id] = {"signature":JSON.stringify(_snapshot(material_maps[id])).sha256_text(),"scene":SCENE if id=="mixed" else SCENE.replace("sandbox_v004",""+id+"_sandbox_v004")}
	catalog["demo_layout_signature"] = catalog.layout_cache.mixed.signature
	_write_json(OUT+"catalog.json",catalog)
	print("REFERENCE_V004_IMAGES_PASS: 3 new actual textures, 7 materials, 4 maps, "+str(catalog.demo_rebuild_ms)+"ms")
	quit(0)


func _read_layout() -> void:
	var original := load("res://scenes/ember/reference_floor_sandbox_v002.tscn").instantiate() as Node2D
	for cell in (original.get_node("Floor") as TileMapLayer).get_used_cells(): floor_cells[cell]=true
	for cell in (original.get_node("Bridge") as TileMapLayer).get_used_cells(): bridge_cells[cell]=true
	original.free()
	var mixed := {}
	for cell: Vector2i in floor_cells:
		if cell.x<3: mixed[cell]=3
		elif cell.y<=4 and cell.x<14: mixed[cell]=5
		elif cell.y<=5 and cell.x>=14 and cell.x<17: mixed[cell]=1
		elif cell.y<=7 and cell.x>=17: mixed[cell]=6
		elif cell.y>=8 and cell.y<=10 and cell.x>=14 and cell.x<17: mixed[cell]=2
		elif cell.y>=8 and cell.y<=13: mixed[cell]=4
	material_maps["mixed"]=mixed
	for index: int in NEW_IDS:
		var cells := {}
		for cell: Vector2i in floor_cells: cells[cell]=index
		material_maps[IDS[index]]=cells


func _prepare_textures() -> void:
	var entries: Array = []
	for index: int in NEW_IDS:
		var source_path: String = SOURCE+"floor_"+IDS[index]+"_master_v004.png"
		var image := Image.load_from_file(ProjectSettings.globalize_path(source_path))
		assert(image!=null,"Missing actual imagegen master: "+source_path)
		var original_size := image.get_size()
		image.convert(Image.FORMAT_RGBA8)
		if image.get_size()!=Vector2i(1024,1024): image.resize(1024,1024,Image.INTERPOLATE_NEAREST)
		var output_path: String = OUT+"floor_"+IDS[index]+"_period_v004.png"
		assert(image.save_png(output_path)==OK)
		entries.append({"id":index,"source":source_path,"source_size":[original_size.x,original_size.y],"source_sha256":FileAccess.get_sha256(source_path),"output":output_path,"output_size":[1024,1024],"processing":"Full-image nearest registration, original artist RGB and alpha retained; no recolouring or palette quantization"})
	_write_json(OUT+"source_processing_v004.json",{"sources":entries,"shared_geometry_revision":"reference_floor_v002"})
	var index_image := Image.create(IDS.size()*128,128,false,Image.FORMAT_RGBA8)
	for index in range(IDS.size()):
		var path: String = _material_texture(index)
		var texture := Image.load_from_file(ProjectSettings.globalize_path(path))
		index_image.blit_rect(texture,Rect2i(0,0,128,128),Vector2i(index*128,0))
	index_image.save_png(OUT+"floor_material_index_v004.png")


func _compiler() -> RefCounted:
	var compiler := COMPILER.new()
	compiler.load_materials()
	for index in range(1,IDS.size()): compiler.floor_material_periods[index]=Image.load_from_file(ProjectSettings.globalize_path(_material_texture(index)))
	return compiler


func _material_texture(index: int) -> String:
	# 旧四份PNG不复制改色，直接引用已交付资源；新增材质只写新目录。
	if index==0: return BASE+"floor_albedo_period_v002.png"
	if index<=3: return PRIOR+"floor_"+IDS[index]+"_period_v003.png"
	return OUT+"floor_"+IDS[index]+"_period_v004.png"


func _surface(compiler: RefCounted,footprint: Image,material_id: int) -> Image:
	var image := Image.create(3072,2048,false,Image.FORMAT_RGBA8)
	var period: Image = compiler.floor_material_periods[material_id]
	for cell: Vector2i in floor_cells:
		for y in range(128):
			for x in range(128):
				var p := cell*128+Vector2i(x,y)
				if footprint.get_pixelv(p).r>0.5: image.set_pixelv(p,period.get_pixel(posmod(p.x,1024),posmod(p.y,1024)))
	return image


func _snapshot(materials: Dictionary) -> Dictionary:
	return {"version":3,"bounds":[0,0,24,16],"floor":_ordered(floor_cells,false),"bridge":_ordered(bridge_cells,false),"materials":_ordered(materials,true)}


func _ordered(cells: Dictionary,with_material: bool) -> Array:
	var keys := cells.keys()
	keys.sort_custom(func(a: Vector2i,b: Vector2i)->bool: return a.y<b.y if a.y!=b.y else a.x<b.x)
	var result: Array=[]
	for cell: Vector2i in keys: result.append([cell.x,cell.y,int(cells[cell])] if with_material else [cell.x,cell.y])
	return result


func _make_tileset(path: String,size: Vector2i) -> TileSet:
	var set := TileSet.new(); set.tile_size=Vector2i(128,128)
	var source := TileSetAtlasSource.new(); source.texture=load(path); source.texture_region_size=Vector2i(128,128)
	assert(source.texture!=null,"Run --import before --resources")
	set.add_source(source,0)
	for y in range(size.y):
		for x in range(size.x): source.create_tile(Vector2i(x,y))
	return set


func _create_resources() -> void:
	assert(ResourceSaver.save(_make_tileset(OUT+"floor_material_index_v004.png",Vector2i(IDS.size(),1)),OUT+"floor_materials_v004.tres")==OK)
	for id: String in LAYERS:
		assert(ResourceSaver.save(_make_tileset(OUT+id+"_context_atlas_v004.png",Vector2i(24,16)),OUT+id+"_context_v004.tres")==OK)
	for index: int in NEW_IDS:
		assert(ResourceSaver.save(_make_tileset(OUT+IDS[index]+"_floor_context_atlas_v004.png",Vector2i(24,16)),OUT+IDS[index]+"_floor_context_v004.tres")==OK)
	for id: String in material_maps:
		var demo := load("res://scenes/ember/reference_floor_sandbox_v002.tscn").instantiate() as Node2D
		demo.set_script(load("res://scripts/ember/reference_floor_painter_v004.gd"))
		demo.name="ReferenceFloor"+id.capitalize()+"V004"
		demo.set("baked_layout_id",id)
		var input := TileMapLayer.new(); input.name="FloorMaterials"; input.scale=Vector2(0.25,0.25); input.visible=false
		input.tile_set=load(OUT+"floor_materials_v004.tres")
		demo.add_child(input); input.owner=demo
		for cell: Vector2i in material_maps[id]: input.set_cell(cell,0,Vector2i(int(material_maps[id][cell]),0))
		for layer_id: String in LAYERS:
			var path: String=OUT+(id+"_" if layer_id=="floor" and id!="mixed" else "")+layer_id+"_context_v004.tres"
			(demo.get_node(layer_id.capitalize()+"Context") as TileMapLayer).tile_set=load(path)
		var packed := PackedScene.new(); assert(packed.pack(demo)==OK)
		assert(ResourceSaver.save(packed,catalog.layout_cache[id].scene)==OK)
		demo.free()


func _capture() -> bool:
	root.size=Vector2i(1536,1024); root.content_scale_size=Vector2i(1536,1024)
	var edits: Array=[]
	for id in ["mixed","concrete","teal","ceramic"]:
		var demo := load(catalog.layout_cache[id].scene).instantiate() as Node2D
		root.add_child(demo)
		(demo.get_node("Help") as CanvasLayer).visible=false
		await process_frame; await process_frame; await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		image.save_png(OUT+"gpu_"+id+"_scene_v004.png")
		if id=="mixed":
			for material_id in NEW_IDS:
				demo.paint_material(Vector2i(12,4),material_id); demo.synchronize()
				await process_frame; await process_frame; await RenderingServer.frame_post_draw
				image=root.get_texture().get_image()
				var point := Vector2i(800,288); var color := image.get_pixelv(point)
				var expected: Image=demo.last_build.floor; var best:=99.0
				for dy in range(2):
					for dx in range(2):
						var sample:=expected.get_pixelv(point*2+Vector2i(dx,dy))
						best=minf(best,maxf(absf(color.r-sample.r),maxf(absf(color.g-sample.g),absf(color.b-sample.b))))
				edits.append({"material_id":material_id,"pure_material_edit":true,"gpu_matches_cpu":best<=3.0/255.0,"max_rgb_error":best,"rebuild_ms":demo.last_rebuild_ms})
			image.save_png(OUT+"gpu_dynamic_material_v004.png")
		demo.free()
	# 对比板只组合实际GPU截图：三种新地板和七材质混铺，不合成新效果图。
	var comparison := Image.create(1536,1024,false,Image.FORMAT_RGBA8)
	var paths: Array=[OUT+"gpu_concrete_scene_v004.png",OUT+"gpu_teal_scene_v004.png",OUT+"gpu_ceramic_scene_v004.png",OUT+"gpu_mixed_scene_v004.png"]
	for index in range(4):
		var image := Image.load_from_file(ProjectSettings.globalize_path(paths[index]))
		image.resize(768,512,Image.INTERPOLATE_NEAREST)
		comparison.blit_rect(image,Rect2i(0,0,768,512),Vector2i((index%2)*768,(index/2)*512))
	comparison.save_png(OUT+"gpu_material_comparison_v004.png")
	var pass_all: bool=edits.all(func(item: Dictionary)->bool: return item.gpu_matches_cpu)
	_write_json(OUT+"gpu_capture_v004.json",{"status":"PASS" if pass_all else "FAIL","actual_tilemap_scenes":4,"dynamic_material_edits":edits,"render_contract":"Actual TileMapLayer + source sprites; same geometry and scale as v002", "renderer":RenderingServer.get_current_rendering_method(),"painter_sha256":FileAccess.get_sha256("res://scripts/ember/reference_floor_painter_v004.gd"),"compiler_sha256":FileAccess.get_sha256("res://scripts/ember/reference_floor_compiler_v002.gd")})
	return pass_all


func _write_json(path: String,data: Dictionary) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	assert(file!=null)
	file.store_string(JSON.stringify(data,"\t")+"\n")

