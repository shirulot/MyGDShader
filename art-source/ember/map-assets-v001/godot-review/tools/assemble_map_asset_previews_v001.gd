extends SceneTree
## 把独立精灵装到真实 TileMap 场景，再由 Godot GPU 拍摄。
## -- --assemble 只保存摆放；-- --capture 截图并检查改刷后像素。
## 本工具只组装原始 RGBA，不重绘、改色或抠图。

const ROOT := "res://assets/ember/map_assets_v001/"
const FLOOR := ROOT+"floors/"
const OUT := ROOT+"previews/"
const MAPS := ["tidal_port","dry_mine","overgrown_lab"]
const LABELS := {"tidal_port":"TIDAL PORT","dry_mine":"DRY MINE","overgrown_lab":"OVERGROWN LAB"}
const LAYERS := ["water","facade","floor","rim","bridge","heads"]
const SPECS := "res://art-source/ember/map-assets-v001/source_specs_v001.json"
const REGISTRATION := ROOT+"sprite_registration_v001.json"
var entries: Dictionary = {}
var placement_report: Array = []
var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var registry: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(REGISTRATION))
	assert(registry.status=="PASS","All sprite exports must pass before assembly")
	for item: Dictionary in registry.sprites: entries[item.id]=item
	if "--assemble" in OS.get_cmdline_user_args():
		for map_id: String in MAPS: _assemble(map_id)
		_write_json(ROOT+"map_placements_v001.json",{"status":"PASS" if failures.is_empty() else "FAIL","tool_sha256":FileAccess.get_sha256("res://tools/assemble_map_asset_previews_v001.gd"),"placements":placement_report,"scope":"Static visual placement. No collision, navigation, animation or automatic pipe/wall Terrain.","failures":failures})
		print("MAP_ASSEMBLY_", "PASS" if failures.is_empty() else "FAIL")
		quit(0 if failures.is_empty() else 1)
		return
	if "--capture" not in OS.get_cmdline_user_args():
		push_error("Use -- --assemble or -- --capture")
		quit(1)
		return
	var captures: Array=[]
	for map_id: String in MAPS: captures.append(await _capture_map(map_id))
	await _capture_library()
	await _capture_floors()
	_write_json(FLOOR+"gpu_capture_v001.json",{
		"status":"PASS" if failures.is_empty() else "FAIL","engine":Engine.get_version_info().string,
		"tool_sha256":FileAccess.get_sha256("res://tools/assemble_map_asset_previews_v001.gd"),
		"painter_sha256":FileAccess.get_sha256("res://scripts/ember/map_asset_painter_v001.gd"),
		"compiler_sha256":FileAccess.get_sha256("res://scripts/ember/reference_floor_compiler_v002.gd"),
		"source_specs_sha256":FileAccess.get_sha256(SPECS),"sprite_registration_sha256":FileAccess.get_sha256(REGISTRATION),
		"capture_size":[1536,1024],"scene_entries":captures,"gpu_edit_tolerance_rgb8":3,"failures":failures})
	print("MAP_GPU_CAPTURE_", "PASS" if failures.is_empty() else "FAIL")
	quit(0 if failures.is_empty() else 1)


func _scene_path(map_id: String) -> String:
	return "res://scenes/ember/map_assets_"+map_id+"_v001.tscn"


func _assemble(map_id: String) -> void:
	var map: Node2D=(load(_scene_path(map_id)) as PackedScene).instantiate()
	# 重复执行装配时替换上一批公共装饰，保证场景不会叠加护栏和格栅。
	for child: Node in map.get_children():
		var legacy_decor: bool=(String(child.name)=="SharedDecor" or String(child.name).begins_with("@Node2D@")) and child.get_child_count()>0
		if child.get_meta("assembler_shared_decor",false) or legacy_decor: child.free()
	var props: Node2D=map.get_node("Props")
	for child in props.get_children(): child.free()
	props.y_sort_enabled=true
	var objects: Array=[]
	if map_id=="tidal_port":
		objects=[["energy_station",21.2,8.0],["console",19.2,10.4],["pump",21.7,9.8],
			["cargo_crate_blue",2.3,3.2],["cargo_crate_olive",2.4,5.2],["cargo_crate_brown",2.5,7.1],
			["winch",17.1,13.7],["drum",3.2,10.1],["door",2.2,14.4],["wall_vertical",1.6,10.0],
			["wall_module",10.0,3.0],["wall_corner",4.8,14.4]]
	elif map_id=="dry_mine":
		objects=[["energy_station",19.6,5.3],["console",17.5,5.1],["pump",21.9,8.5],
			["ore_bin",4.9,3.8],["ore_bin",4.9,5.8],["conveyor",4.8,12.9],
			["cargo_crate_blue",7.4,4.6],["cargo_crate_olive",20.7,12.6],["cargo_crate_brown",22.4,13.0],
			["drum",2.6,7.1],["drum",21.8,10.6],["wall_module",12.3,2.1],["door",14.2,3.2],
			["wall_vertical",2.0,10.7],["rock_cluster",12.2,5.8],["rock_cluster",12.9,10.6]]
	else:
		objects=[["energy_station",18.6,5.0],["console",16.2,4.7],["research_cabinet",21.1,3.2],
			["research_cabinet",22.1,5.1],["sample_tank",3.6,3.4],["sample_tank",3.6,5.3],
			["sample_tank",11.5,9.2],["pump",21.1,13.3],["cargo_crate_olive",5.3,12.8],
			["door",7.0,3.1],["wall_module",3.5,1.9],["wall_vertical",19.3,9.6],
			["reed_cluster",9.1,6.7],["reed_cluster",15.8,11.7],
			["lily_patch",10.4,5.7],["lily_patch",15.6,6.8],["lily_patch",3.0,9.0],
			["rock_cluster",2.4,12.1]]
	for object: Array in objects: _place(map,props,map_id,String(object[0]),Vector2(float(object[1]),float(object[2]))*32)
	# 小机器人沿用现有正式资源。底脚对齐落点，缩放为相同原生显示尺度。
	var robot:=Sprite2D.new(); robot.name="ExistingRobot"; robot.texture=load("res://assets/ember/characters/robot/robot_idle_down_v001.png")
	robot.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST; robot.scale=Vector2(0.65,0.65)
	robot.offset=Vector2(0,-robot.texture.get_height()*0.5)
	robot.position=Vector2(5.4,8.5)*32 if map_id=="tidal_port" else (Vector2(8.3,8.2)*32 if map_id=="dry_mine" else Vector2(9.2,12.7)*32)
	props.add_child(robot); robot.owner=map
	# 老规范的格栅盖与护栏继续使用原画；不从概念截图里带地板切图。
	var decor:=Node2D.new(); decor.name="SharedDecor"; decor.z_index=6; decor.set_meta("assembler_shared_decor",true); map.add_child(decor); decor.owner=map
	var hatch_points: Array=[Vector2(8.5,3.4),Vector2(8.5,8.6)] if map_id=="tidal_port" else ([Vector2(8.0,12.7),Vector2(20.0,10.0)] if map_id=="dry_mine" else [Vector2(7.6,8.0),Vector2(18.5,12.5)])
	for point: Vector2 in hatch_points: _shared(map,decor,"grate_hatch",point*32,Vector2(0.18,0.18))
	var rail_points: Array=[Vector2(9.0,2.0),Vector2(10.7,2.0),Vector2(8.5,12.0),Vector2(10.2,12.0)] if map_id=="tidal_port" else ([Vector2(10.6,4.0),Vector2(13.0,4.0)] if map_id=="dry_mine" else [Vector2(7.0,11.0),Vector2(20.5,11.0)])
	for point: Vector2 in rail_points: _shared(map,decor,"rail_horizontal",point*32,Vector2(0.18,0.18))
	# 管道组件是明确的独立美术件。此版只作人工装饰，不宣称接口自动拼接。
	for pipe_id: String in ["pipe_horizontal","pipe_vertical","pipe_terminal_h"]:
		if entries.has(pipe_id):
			var point:=Vector2(7.4,8.2) if map_id=="tidal_port" else (Vector2(18.0,13.0) if map_id=="dry_mine" else Vector2(17.4,5.3))
			point.x+=float(["pipe_horizontal","pipe_vertical","pipe_terminal_h"].find(pipe_id))*1.2
			_place(map,props,map_id,pipe_id,point*32)
	var packed:=PackedScene.new(); assert(packed.pack(map)==OK); assert(ResourceSaver.save(packed,_scene_path(map_id))==OK)
	map.free()


func _place(map: Node2D,props: Node2D,map_id: String,id: String,point: Vector2) -> void:
	if not entries.has(id):
		failures.append("Missing registered sprite "+id)
		return
	var path:=ROOT+"scene_library/"+id+".tscn"
	var sprite: Node2D=(load(path) as PackedScene).instantiate()
	sprite.name=id.to_pascal_case()+str(props.get_child_count()); sprite.position=point
	props.add_child(sprite); sprite.owner=map
	placement_report.append({"map_id":map_id,"id":id,"scene":path,"anchor_world":[point.x,point.y]})


func _shared(map: Node2D,parent: Node2D,id: String,point: Vector2,factor: Vector2) -> void:
	var sprite:=Sprite2D.new(); sprite.name=id.to_pascal_case()+str(parent.get_child_count())
	sprite.texture=load("res://assets/ember/environment/reference_floor_v002/"+id+"_artist_v002.png")
	sprite.position=point; sprite.scale=factor; sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	parent.add_child(sprite); sprite.owner=map


func _new_view(size: Vector2i) -> SubViewport:
	var view:=SubViewport.new(); view.size=size; view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	view.transparent_bg=false; view.canvas_item_default_texture_filter=Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	root.add_child(view)
	return view


func _frames() -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw


func _capture_map(map_id: String) -> Dictionary:
	var view:=_new_view(Vector2i(1536,1024))
	var map: Node2D=(load(_scene_path(map_id)) as PackedScene).instantiate(); view.add_child(map)
	await _frames()
	map.set_process(false)
	if map.get("_help_label")!=null: map.get("_help_label").get_parent().hide()
	await _frames()
	var screenshot:=OUT+"gpu_"+map_id+"_v001.png"
	assert(view.get_texture().get_image().save_png(screenshot)==OK)
	# 检查摆放道具后的同一场景仍可改刷；用六层 RGBA 合成值核对 GPU。
	var cell:=Vector2i(10,3) if map_id=="tidal_port" else (Vector2i(8,2) if map_id=="dry_mine" else Vector2i(14,12))
	var edits: Array=[9,4] if map_id=="tidal_port" else ([11,12] if map_id=="dry_mine" else [5,6])
	var maximum:=0; var samples:=0; var cycles: Array=[]
	for material_id: int in edits:
		# 连续两次更换验证初建 ImageTexture 与其后的 update() 都刷新了Atlas缓存。
		map.paint_material(cell,material_id); map.synchronize()
		await _frames()
		var image:=view.get_texture().get_image(); image.convert(Image.FORMAT_RGBA8)
		var cycle_max:=0
		for relative: Vector2i in [Vector2i(12,12),Vector2i(64,64),Vector2i(112,108)]:
			var tex:=cell*128+relative
			var screen:=Vector2i(floori(float(tex.x)*0.5),floori(float(tex.y)*0.5))
			var actual:=image.get_pixelv(screen); var best:=255
			# 每显示像素覆盖2×2源像素，nearest在Atlas归一化浮点边界上可取其中任一点。
			# 四个合法源样本比较沿用v006 GPU校验；不放宽颜色误差，也不跨显示像素搜索。
			for dy in range(2):
				for dx in range(2):
					var point:=screen*2+Vector2i(dx,dy)
					var expected:=Color(0,0,0,1)
					for layer: String in LAYERS: expected=expected.blend(map.last_build[layer].get_pixelv(point))
					var error:=roundi(maxf(absf(expected.r-actual.r),maxf(absf(expected.g-actual.g),absf(expected.b-actual.b)))*255)
					best=mini(best,error)
			cycle_max=maxi(cycle_max,best); samples+=1
		maximum=maxi(maximum,cycle_max)
		cycles.append({"material_id":material_id,"max_rgb8":cycle_max,"rebuild_ms":map.last_rebuild_ms})
		assert(image.save_png(OUT+"gpu_dynamic_"+map_id+"_v001.png")==OK)
	if maximum>3: failures.append("GPU edit RGB mismatch "+map_id+" "+str(maximum))
	var entry: Dictionary={"map_id":map_id,"scene":_scene_path(map_id),"scene_sha256":FileAccess.get_sha256(_scene_path(map_id)),"screenshot":screenshot,"screenshot_sha256":FileAccess.get_sha256(screenshot),"gpu_edit_samples":samples,"gpu_edit_cycles":cycles,"gpu_edit_max_rgb8":maximum,"capture_kind":"Actual Godot SubViewport, imported production PNG and TileMapLayer; no painted mockup"}
	view.queue_free(); await process_frame
	return entry


func _label(parent: Node,text: String,point: Vector2) -> void:
	var label:=Label.new(); label.text=text; label.position=point; label.add_theme_font_size_override("font_size",18)
	parent.add_child(label)


func _capture_library() -> void:
	var ids:=entries.keys(); ids.sort()
	var view:=_new_view(Vector2i(1536,ceili(float(ids.size())/6.0)*288))
	for index in range(ids.size()):
		var item: Dictionary=entries[ids[index]]
		var sprite:=Sprite2D.new(); sprite.texture=load(item.texture); sprite.scale=Vector2(2,2)
		sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
		sprite.position=Vector2((index%6)*256+128,floori(float(index)/6.0)*288+138)
		view.add_child(sprite)
		_label(view,String(item.id),Vector2((index%6)*256+12,floori(float(index)/6.0)*288+260))
	await _frames()
	assert(view.get_texture().get_image().save_png(OUT+"sprite_library_v001.png")==OK)
	view.queue_free(); await process_frame


func _capture_floors() -> void:
	var catalog: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(FLOOR+"catalog.json"))
	var view:=_new_view(Vector2i(1536,1632)); var index:=0
	for item: Dictionary in catalog.materials:
		if not item.new_master: continue
		var sprite:=Sprite2D.new(); sprite.texture=load(item.texture); sprite.centered=false; sprite.scale=Vector2(0.5,0.5)
		sprite.position=Vector2((index%3)*512,floori(float(index)/3.0)*544); sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
		view.add_child(sprite); _label(view,String(item.key),sprite.position+Vector2(12,514)); index+=1
	await _frames()
	assert(view.get_texture().get_image().save_png(OUT+"floor_library_v001.png")==OK)
	view.queue_free(); await process_frame


func _write_json(path: String,data: Dictionary) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE); assert(file!=null)
	file.store_string(JSON.stringify(data,"\t")+"\n")

