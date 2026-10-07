extends SceneTree
## 三种新表面共享已认可v002的几何、压顶、立面和桥口。
## 仅裁切/nearest注册真实生图，按统一世界相位拼装；不程序重绘材质。
## 默认生成PNG缓存；导入后 -- --resources 创建实际铺刷场景。

const OUT := "res://assets/ember/environment/reference_floor_v005/"
const SOURCE := "res://art-source/ember/reference-floor-v005/"
const BASE := "res://assets/ember/environment/reference_floor_v002/"
const EARLY := "res://assets/ember/environment/reference_floor_v003/"
const PRIOR := "res://assets/ember/environment/reference_floor_v004/"
const COMPILER := preload("res://scripts/ember/reference_floor_compiler_v002.gd")
const LAYERS := ["water","facade","floor","rim","bridge","heads"]
const IDS := ["steel","control","service","rust","concrete","teal","ceramic","asphalt","brick","wood"]
const NAMES := ["蓝灰涂装钢板","浅灰控制区地板","深灰检修区防滑钢板","锈褐旧仓区钢板","浅砂混凝土地板","青绿旧涂层地板","磨损灰白地砖","旧沥青地板","砖红工业铺装","灰褐木栈道"]
const NEW_IDS := [7,8,9]
const SCENE := "res://scenes/ember/reference_floor_sandbox_v005.tscn"
var floor_cells: Dictionary = {}
var bridge_cells: Dictionary = {}
var material_maps: Dictionary = {}
var catalog: Dictionary = {}
var registration_details: Dictionary = {}


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
		print("REFERENCE_V005_RESOURCES_PASS" if ok else "REFERENCE_V005_GPU_FAIL")
		quit(0 if ok else 1)
		return
	_prepare_textures()
	var compiler := _compiler()
	var started := Time.get_ticks_msec()
	var images: Dictionary = compiler.build_visual_layers(floor_cells,bridge_cells,Rect2i(0,0,24,16),material_maps.mixed)
	for id: String in LAYERS: images[id].save_png(OUT+id+"_context_atlas_v005.png")
	images.coverage.save_png(OUT+"union_coverage_v005.png")
	# 同构地图只替换floor图层，结构的其它五层直接复用，保持接口标准完全一致。
	for index: int in NEW_IDS:
		var image := _surface(compiler,images.coverage,index)
		image.save_png(OUT+IDS[index]+"_floor_context_atlas_v005.png")
	var old: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(BASE+"catalog.json"))
	catalog = {"revision":"reference_floor_v005","status":"VISUAL_CANDIDATE","user_accepted":false,
		"texture_tile_size":128,"world_cell_size":[32,32],"layer_scale":[0.25,0.25],
		"atlases":old.atlases,"material_index_tileset":OUT+"floor_materials_v005.tres",
		"materials":[],"layout_cache":{},"demo_bounds":[0,0,24,16],
		"bridge_visible_width_world":40,"bridge_shoulders_world":12,
		"shared_geometry":"v002 Floor/Bridge 47 masks; all materials share coping, facade, bridge heads and coverage",
		"demo_rebuild_ms":Time.get_ticks_msec()-started}
	for index in range(IDS.size()):
		var texture: String = _material_texture(index)
		catalog.materials.append({"id":index,"key":IDS[index],"name":NAMES[index],"texture":texture,"sha256":FileAccess.get_sha256(texture),"period_texture_px":[1024,1024]})
	for id: String in material_maps:
		catalog.layout_cache[id] = {"signature":JSON.stringify(_snapshot(material_maps[id])).sha256_text(),"scene":SCENE if id=="mixed" else SCENE.replace("sandbox_v005",""+id+"_sandbox_v005")}
	catalog["demo_layout_signature"] = catalog.layout_cache.mixed.signature
	_write_json(OUT+"catalog.json",catalog)
	print("REFERENCE_V005_IMAGES_PASS: 3 new actual textures, 10 materials, 4 maps, "+str(catalog.demo_rebuild_ms)+"ms")
	quit(0)


func _read_layout() -> void:
	var original := load("res://scenes/ember/reference_floor_sandbox_v002.tscn").instantiate() as Node2D
	for cell in (original.get_node("Floor") as TileMapLayer).get_used_cells(): floor_cells[cell]=true
	for cell in (original.get_node("Bridge") as TileMapLayer).get_used_cells(): bridge_cells[cell]=true
	original.free()
	var mixed := {}
	for cell: Vector2i in floor_cells:
		# 混铺地图保留十种表面各自区域，结构仍完全读取原v002占用。
		if cell.x<3: mixed[cell]=9
		elif cell.y<=4:
			mixed[cell]=9 if cell.x<14 else (7 if cell.x<17 else 8)
		elif cell.y<=7:
			if cell.x<11: mixed[cell]=3
			elif cell.x<14: mixed[cell]=5
			elif cell.x<17: mixed[cell]=1
			elif cell.x<20: mixed[cell]=6
		elif cell.y<=10:
			mixed[cell]=2 if cell.x<17 else (4 if cell.x<20 else 8)
		elif cell.y<=13:
			mixed[cell]=3 if cell.x<14 else (7 if cell.x<17 else 5)
	var material_counts: Dictionary={}
	for cell: Vector2i in floor_cells:
		var material_id:=int(mixed.get(cell,0))
		material_counts[material_id]=int(material_counts.get(material_id,0))+1
	assert(material_counts.size()==IDS.size(),"Mixed example must actually contain all ten materials")
	material_maps["mixed"]=mixed
	for index: int in NEW_IDS:
		var cells := {}
		for cell: Vector2i in floor_cells: cells[cell]=index
		material_maps[IDS[index]]=cells


func _prepare_textures() -> void:
	var entries: Array = []
	for index: int in NEW_IDS:
		var source_path: String = SOURCE+"floor_"+IDS[index]+"_master_v005.png"
		var image := Image.load_from_file(ProjectSettings.globalize_path(source_path))
		assert(image!=null,"Missing actual imagegen master: "+source_path)
		var original_size := image.get_size()
		image.convert(Image.FORMAT_RGBA8)
		# 母稿的实际砖数/板数不等于提示词数字；按真实接缝裁艺术片，再注册到统一周期。
		# 所有颜色仍取自母稿。这里只切片、nearest缩放和拼装，不画缝线或重新上色。
		if index==8: image=_register_brick(image)
		elif index==9: image=_register_wood(image)
		elif image.get_size()!=Vector2i(1024,1024): image.resize(1024,1024,Image.INTERPOLATE_NEAREST)
		var output_path: String = OUT+"floor_"+IDS[index]+"_period_v005.png"
		assert(image.save_png(output_path)==OK)
		entries.append({"id":index,"source":source_path,"source_size":[original_size.x,original_size.y],"source_sha256":FileAccess.get_sha256(source_path),"output":output_path,"output_size":[1024,1024],"processing":"Artist fragment crop and nearest registration" if index in [8,9] else "Full-image nearest registration","registration":registration_details.get(IDS[index],{}),"pixel_policy":"Original artist RGBA samples only; no recolouring, procedural painting or palette quantization"})
	_write_json(OUT+"source_processing_v005.json",{"sources":entries,"shared_geometry_revision":"reference_floor_v002"})
	var index_image := Image.create(IDS.size()*128,128,false,Image.FORMAT_RGBA8)
	for index in range(IDS.size()):
		var path: String = _material_texture(index)
		var texture := Image.load_from_file(ProjectSettings.globalize_path(path))
		index_image.blit_rect(texture,Rect2i(0,0,128,128),Vector2i(index*128,0))
	index_image.save_png(OUT+"floor_material_index_v005.png")


func _find_joint(source: Image,expected: int,horizontal: bool,brick: bool,scan_start: int,scan_end: int) -> int:
	# 只测量真实像素：砖缝比红砖偏灰；木板接缝比木面暗，用局部平均锁定裁切中心。
	var limit:=source.get_height() if horizontal else source.get_width()
	var best_score: float=-INF
	var best:=clampi(expected,0,limit-1)
	for position in range(maxi(0,best-10),mini(limit-1,best+10)+1):
		var score:=0.0
		var count:=0
		for along in range(scan_start,scan_end,4):
			var color:=source.get_pixel(along,position) if horizontal else source.get_pixel(position,along)
			score+=(color.g+color.b-color.r) if brick else -(color.r+color.g+color.b)
			count+=1
		if count>0 and score/count>best_score:
			best_score=score/count
			best=position
	return best


func _register_brick(source: Image) -> Image:
	# 实际1254母稿有约14行和6列。取中间12行、每行5块完整砖，保留60种艺术磨损。
	# 输出严格8列×16行，每块128×64，奇数行偏移64；边界的半砖由同一艺术片循环闭合。
	var anchors: Array=[86,174,262,350,438,525,613,701,789,878,967,1056,1145]
	var rows: Array[int]=[]
	for anchor: int in anchors:
		rows.append(_find_joint(source,roundi(anchor*source.get_height()/1254.0),true,true,16,source.get_width()-16))
	var pieces: Array[Image]=[]
	var rects: Array=[]
	for row in range(12):
		var columns: Array[int]=[]
		for column in range(6):
			var anchor_x: int=(38 if row%2==0 else 135)+column*210
			columns.append(_find_joint(source,roundi(anchor_x*source.get_width()/1254.0),false,true,rows[row]+6,rows[row+1]-6))
		for column in range(5):
			var rect:=Rect2i(columns[column],rows[row],columns[column+1]-columns[column],rows[row+1]-rows[row])
			assert(rect.size.x>100 and rect.size.y>40,"Invalid brick joint registration")
			var fragment:=source.get_region(rect)
			fragment.resize(128,64,Image.INTERPOLATE_NEAREST)
			pieces.append(fragment)
			rects.append([rect.position.x,rect.position.y,rect.size.x,rect.size.y])
	var result:=Image.create(1024,1024,false,Image.FORMAT_RGBA8)
	var placement: Array=[]
	for row in range(16):
		for column in range(8):
			var piece_id: int=(row%12)*5+posmod(column+row*2,5)
			var at:=Vector2i(column*128-(64 if row%2 else 0),row*64)
			_blit_wrapped_x(result,pieces[piece_id],at)
			placement.append([row,column,piece_id])
	registration_details.brick={"unit_texture_px":[128,64],"rows":16,"columns":8,"alternate_row_offset":64,"source_fragments":rects,"placements":placement,"method":"Measured mortar centre crop; original nearest RGBA; cyclic half-brick at period boundary"}
	return result


func _blit_wrapped_x(target: Image,fragment: Image,at: Vector2i) -> void:
	# 跨周期的艺术半砖连续取同一完整砖；不另画边框，也不丢掉外边缘64像素。
	var canvas:=Rect2i(Vector2i.ZERO,target.get_size())
	for offset in [0,-target.get_width(),target.get_width()]:
		var destination:=Rect2i(at+Vector2i(offset,0),fragment.get_size())
		var visible:=destination.intersection(canvas)
		if visible.has_area(): target.blit_rect(fragment,Rect2i(visible.position-destination.position,visible.size),visible.position)


func _register_wood(source: Image) -> Image:
	# 实际母稿是15条板，按真实暗接缝裁15份纹理，再对齐16条64px板带。
	# 板内的木纹、结疤和接头均保留；跨相邻128格始终是两条板，避免逐格相位漂移。
	var boundaries: Array[int]=[]
	for row in range(16):
		boundaries.append(_find_joint(source,roundi(row*source.get_height()/15.0),true,false,16,source.get_width()-16))
	var result:=Image.create(1024,1024,false,Image.FORMAT_RGBA8)
	var rects: Array=[]
	for row in range(16):
		var index: int=row%15
		var rect:=Rect2i(0,boundaries[index],source.get_width(),boundaries[index+1]-boundaries[index])
		assert(rect.size.y>40,"Invalid wood board registration")
		var fragment:=source.get_region(rect)
		fragment.resize(1024,64,Image.INTERPOLATE_NEAREST)
		result.blit_rect(fragment,Rect2i(0,0,1024,64),Vector2i(0,row*64))
		rects.append([rect.position.x,rect.position.y,rect.size.x,rect.size.y])
	registration_details.wood={"board_height_texture_px":64,"rows":16,"source_row_fragments":rects,"method":"Measured dark joint centre crop; original nearest RGBA; aligned board bands"}
	return result


func _compiler() -> RefCounted:
	var compiler := COMPILER.new()
	compiler.load_materials()
	for index in range(1,IDS.size()): compiler.floor_material_periods[index]=Image.load_from_file(ProjectSettings.globalize_path(_material_texture(index)))
	return compiler


func _material_texture(index: int) -> String:
	# 旧七份PNG不复制改色，直接引用已交付资源；新增材质只写新目录。
	if index==0: return BASE+"floor_albedo_period_v002.png"
	if index<=3: return EARLY+"floor_"+IDS[index]+"_period_v003.png"
	if index<=6: return PRIOR+"floor_"+IDS[index]+"_period_v004.png"
	return OUT+"floor_"+IDS[index]+"_period_v005.png"


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
	assert(ResourceSaver.save(_make_tileset(OUT+"floor_material_index_v005.png",Vector2i(IDS.size(),1)),OUT+"floor_materials_v005.tres")==OK)
	for id: String in LAYERS:
		assert(ResourceSaver.save(_make_tileset(OUT+id+"_context_atlas_v005.png",Vector2i(24,16)),OUT+id+"_context_v005.tres")==OK)
	for index: int in NEW_IDS:
		assert(ResourceSaver.save(_make_tileset(OUT+IDS[index]+"_floor_context_atlas_v005.png",Vector2i(24,16)),OUT+IDS[index]+"_floor_context_v005.tres")==OK)
	for id: String in material_maps:
		var demo := load("res://scenes/ember/reference_floor_sandbox_v002.tscn").instantiate() as Node2D
		demo.set_script(load("res://scripts/ember/reference_floor_painter_v005.gd"))
		demo.name="ReferenceFloor"+id.capitalize()+"V005"
		demo.set("baked_layout_id",id)
		var input := TileMapLayer.new(); input.name="FloorMaterials"; input.scale=Vector2(0.25,0.25); input.visible=false
		input.tile_set=load(OUT+"floor_materials_v005.tres")
		demo.add_child(input); input.owner=demo
		for cell: Vector2i in material_maps[id]: input.set_cell(cell,0,Vector2i(int(material_maps[id][cell]),0))
		for layer_id: String in LAYERS:
			var path: String=OUT+(id+"_" if layer_id=="floor" and id!="mixed" else "")+layer_id+"_context_v005.tres"
			(demo.get_node(layer_id.capitalize()+"Context") as TileMapLayer).tile_set=load(path)
		var packed := PackedScene.new(); assert(packed.pack(demo)==OK)
		assert(ResourceSaver.save(packed,catalog.layout_cache[id].scene)==OK)
		demo.free()


func _capture() -> bool:
	root.size=Vector2i(1536,1024); root.content_scale_size=Vector2i(1536,1024)
	var edits: Array=[]
	for id in ["mixed","asphalt","brick","wood"]:
		var demo := load(catalog.layout_cache[id].scene).instantiate() as Node2D
		root.add_child(demo)
		(demo.get_node("Help") as CanvasLayer).visible=false
		await process_frame; await process_frame; await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		image.save_png(OUT+"gpu_"+id+"_scene_v005.png")
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
			image.save_png(OUT+"gpu_dynamic_material_v005.png")
		demo.free()
	# 对比板只组合实际GPU截图：三种新地板和十材质混铺，不合成新效果图。
	var comparison := Image.create(1536,1024,false,Image.FORMAT_RGBA8)
	var paths: Array=[OUT+"gpu_asphalt_scene_v005.png",OUT+"gpu_brick_scene_v005.png",OUT+"gpu_wood_scene_v005.png",OUT+"gpu_mixed_scene_v005.png"]
	for index in range(4):
		var image := Image.load_from_file(ProjectSettings.globalize_path(paths[index]))
		image.resize(768,512,Image.INTERPOLATE_NEAREST)
		comparison.blit_rect(image,Rect2i(0,0,768,512),Vector2i((index%2)*768,(index/2)*512))
	comparison.save_png(OUT+"gpu_material_comparison_v005.png")
	var pass_all: bool=edits.all(func(item: Dictionary)->bool: return item.gpu_matches_cpu)
	_write_json(OUT+"gpu_capture_v005.json",{"status":"PASS" if pass_all else "FAIL","actual_tilemap_scenes":4,"dynamic_material_edits":edits,"render_contract":"Actual TileMapLayer + source sprites; same geometry and scale as v002", "renderer":RenderingServer.get_current_rendering_method(),"painter_sha256":FileAccess.get_sha256("res://scripts/ember/reference_floor_painter_v005.gd"),"compiler_sha256":FileAccess.get_sha256("res://scripts/ember/reference_floor_compiler_v002.gd")})
	return pass_all


func _write_json(path: String,data: Dictionary) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	assert(file!=null)
	file.store_string(JSON.stringify(data,"\t")+"\n")


