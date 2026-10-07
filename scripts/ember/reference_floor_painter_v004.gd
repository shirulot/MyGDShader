@tool
extends Node2D
## v004 从catalog注册材质，在已验证的v003基础上扩展输入而不改变 Floor / Bridge 占用。
## FloorMaterials 是普通图块索引；材质交界不参与 Terrain，也不会生成内压顶或立面。
## Floor 优先，bridge默认2×2面积笔刷；context不参加Terrain随机选块。
## 完整重建保留8格材质相位；source纹理只加载一次，changed采用debounce，笔划结束才编译。

const COMPILER := preload("res://scripts/ember/reference_floor_compiler_v002.gd")
const ASSET := "res://assets/ember/environment/reference_floor_v004/"
const INPUT_LAYERS := ["Floor","Bridge","FloorMaterials"]
const LAYERS := ["water","facade","floor","rim","bridge","heads"]
## 快捷键保留旧0..3材质；扩展材质可用方括号循环，不受数字键数量限制。
const MATERIAL_SHORTCUTS := {KEY_4:0,KEY_5:1,KEY_6:2,KEY_7:3,KEY_8:4,KEY_9:5,KEY_0:6}
@export var bounds_cells := Rect2i(0,0,24,16)
@export var refresh_in_editor := true
## 同构独立展示地图使用各自的缓存签名；实际像素仍取场景自己的外部context PNG。
@export var baked_layout_id := "mixed"
var floor_cells: Dictionary = {}
var bridge_cells: Dictionary = {}
## 只保存非零材质；0为旧钢面，其余合法ID和名称来自catalog.materials。
var floor_materials: Dictionary = {}
var compiler := COMPILER.new()
var last_build: Dictionary = {}
var last_rebuild_ms := 0
var _lookup: Dictionary = {}
var _pending := false
var _changed_at := 0
var _writing := false
var _fingerprint := ""
var _observed_fingerprint := ""
var _last_poll_at := 0
var _dragging := false
var _brush := 1
var _stroke_before: Dictionary = {}
var _stroke_cells: Dictionary = {}
var _undo: Array = []
var _redo: Array = []
var _rendered_floor: Dictionary = {}
var _rendered_bridge: Dictionary = {}
var _rendered_materials: Dictionary = {}
var last_dirty_bounds := Rect2i()
var _baked_signature := ""
var _material_cache_valid := true
var _material_index_tileset := ASSET+"floor_materials_v004.tres"
var _material_names: Dictionary = {0:"Steel"}
var _material_keys: Dictionary = {0:"steel"}
var _material_ids: Array[int] = [0]
var _selected_material_id := 0
var _help_label: Label


func _ready() -> void:
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	compiler.load_materials()
	_load_lookup()
	_ensure_material_layer()
	_adopt_inputs()
	_fingerprint=JSON.stringify(snapshot())
	_observed_fingerprint=_fingerprint
	for id: String in INPUT_LAYERS:
		var layer := get_node_or_null(id) as TileMapLayer
		if layer!=null and not layer.changed.is_connected(_input_changed): layer.changed.connect(_input_changed)
	# 派生块是缓存，不把每次编辑的新ImageTexture嵌入用户的.tscn，避免几十MB文本膨胀。
	# 首次成品scene带external PNG缓存；用户保存后仅保留原生输入，下次打开由compiler恢复。
	var has_context := true
	for id: String in LAYERS:
		var layer := get_node_or_null(id.capitalize()+"Context") as TileMapLayer
		if layer==null or layer.tile_set==null or not layer.tile_set.has_source(0): has_context=false
		else:
			layer.owner=null
			var source := layer.tile_set.get_source(0) as TileSetAtlasSource
			# import的fix_alpha_border可能改变透明RGB；CPU缓存必须读原生产PNG保持逐字节一致。
			var pixels:=Image.new()
			var path:=source.texture.resource_path
			if path.ends_with(".png") and FileAccess.file_exists(path):
				pixels.load_png_from_buffer(FileAccess.get_file_as_bytes(path))
			else:
				pixels=source.texture.get_image()
			pixels.convert(Image.FORMAT_RGBA8)
			last_build[id]=pixels
	# 只有artist PNG缓存确实由同一语义布局编出才预热；不能把初始图套到用户新布局。
	if not _material_cache_valid or _baked_signature!=_fingerprint.sha256_text(): has_context=false; last_build.clear()
	if has_context:
		var footprint:=Image.new()
		footprint.load_png_from_buffer(FileAccess.get_file_as_bytes(ASSET+"union_coverage_v004.png"))
		last_build["coverage"]=footprint; last_build["pixel_origin"]=bounds_cells.position*128
		_rendered_floor=floor_cells.duplicate(); _rendered_bridge=bridge_cells.duplicate()
		_rendered_materials=floor_materials.duplicate()
	if not has_context: call_deferred("_synchronize_from_inputs")
	if not Engine.is_editor_hint(): _build_help()
	set_process(true)


func _load_lookup() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ASSET+"catalog.json"))
	_material_cache_valid=true
	_baked_signature=str(catalog.get("demo_layout_signature",""))
	var layout_cache: Dictionary=catalog.get("layout_cache",{})
	if layout_cache.has(baked_layout_id):
		_baked_signature=str(layout_cache[baked_layout_id].get("signature",_baked_signature))
	_material_index_tileset=str(catalog.get("material_index_tileset",_material_index_tileset))
	_lookup.clear()
	for atlas: Dictionary in catalog.atlases:
		var lookup := {}
		for entry: Dictionary in atlas.tiles: lookup[int(entry.mask)]=Vector2i(int(entry.coord[0]),int(entry.coord[1]))
		_lookup[atlas.id]=lookup
	_material_names={0:"Steel"}; _material_keys={0:"steel"}; _material_ids=[0]
	_selected_material_id=0
	# 每种period仅在启动时读取一次。鼠标拖刷和输入轮询不做PNG文件IO。
	for entry: Dictionary in catalog.get("materials",[]):
		var id:=int(entry.get("id",0))
		if id<0: continue
		if not _material_ids.has(id): _material_ids.append(id)
		_material_names[id]=str(entry.get("name","Material "+str(id)))
		_material_keys[id]=str(entry.get("key",_material_names[id]))
		# 独立材质地图启动即选中对应笔刷；mixed始终默认钢面。
		if baked_layout_id!="mixed" and str(_material_keys[id])==baked_layout_id: _selected_material_id=id
		var path:=str(entry.get("texture",""))
		if not FileAccess.file_exists(path):
			_material_cache_valid=false
			push_error("Floor material PNG missing: "+path)
			continue
		# 布局签名相同也不能复用修改过材质的旧context。SHA只在启动载入时核对。
		# 旧catalog未记录sha256时保持兼容；有记录则必须匹配原始生产PNG字节。
		var expected_sha:=str(entry.get("sha256",""))
		if not expected_sha.is_empty() and FileAccess.get_sha256(path)!=expected_sha:
			_material_cache_valid=false
		var image:=Image.new()
		if image.load_png_from_buffer(FileAccess.get_file_as_bytes(path))!=OK:
			_material_cache_valid=false
			push_error("Cannot read floor material PNG: "+path)
			continue
		image.convert(Image.FORMAT_RGBA8)
		compiler.floor_material_periods[id]=image
	_material_ids.sort()


func _ensure_material_layer() -> void:
	var layer:=get_node_or_null("FloorMaterials") as TileMapLayer
	if layer==null:
		layer=TileMapLayer.new(); layer.name="FloorMaterials"; add_child(layer)
	# 材质索引属于用户输入，必须随场景保存，不能像context缓存那样owner=null。
	if layer.owner==null:
		layer.owner=owner if owner!=null else self
	layer.visible=false
	layer.scale=Vector2(0.25,0.25)
	layer.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	if _material_tileset_valid(layer.tile_set): return
	if FileAccess.file_exists(_material_index_tileset):
		layer.tile_set=load(_material_index_tileset) as TileSet
	if _material_tileset_valid(layer.tile_set): return
	# 从零创建测试节点或复用刷器时的兜底：只裁真实纹理样片，不绘制程序颜色。
	# coord(id,0)以ID作为列号，最大ID决定宽度，未来非连续ID也不会被重新编号。
	var palette:=Image.create((_material_ids.back()+1)*128,128,false,Image.FORMAT_RGBA8)
	for id: int in _material_ids:
		var period: Image=compiler.floor_material_periods.get(id,compiler.materials.floor_albedo_period)
		palette.blit_rect(period,Rect2i(0,0,128,128),Vector2i(id*128,0))
	var set:=TileSet.new(); set.tile_size=Vector2i(128,128)
	var source:=TileSetAtlasSource.new()
	source.texture=ImageTexture.create_from_image(palette)
	source.texture_region_size=Vector2i(128,128)
	set.add_source(source,0)
	for id: int in _material_ids: source.create_tile(Vector2i(id,0))
	layer.tile_set=set


func _material_tileset_valid(set: TileSet) -> bool:
	# 复用旧v003场景时四格索引集不够用，应升级到当前catalog的索引集而保留格坐标。
	if set==null or set.tile_size!=Vector2i(128,128) or not set.has_source(0): return false
	var source:=set.get_source(0) as TileSetAtlasSource
	if source==null or source.texture_region_size!=Vector2i(128,128): return false
	for id: int in _material_ids:
		if not source.has_tile(Vector2i(id,0)): return false
	return true


func _adopt_inputs() -> void:
	floor_cells.clear(); bridge_cells.clear(); floor_materials.clear()
	var floor_layer := get_node_or_null("Floor") as TileMapLayer
	var bridge_layer := get_node_or_null("Bridge") as TileMapLayer
	if floor_layer!=null:
		for cell in floor_layer.get_used_cells(): floor_cells[cell]=true
	if bridge_layer!=null:
		for cell in bridge_layer.get_used_cells():
			if not floor_cells.has(cell): bridge_cells[cell]=true
	var material_layer:=get_node_or_null("FloorMaterials") as TileMapLayer
	if material_layer!=null:
		var was_writing:=_writing
		_writing=true
		for cell: Vector2i in material_layer.get_used_cells():
			var coord:=material_layer.get_cell_atlas_coords(cell)
			var valid:=floor_cells.has(cell) and bounds_cells.has_point(cell)
			valid=valid and material_layer.get_cell_source_id(cell)==0 and coord.y==0 and _material_ids.has(coord.x)
			if valid and coord.x!=0:
				floor_materials[cell]=coord.x
			else:
				# 0材质没有必要存索引；界外及无Floor占用的索引也及时清除，避免擦后残留。
				material_layer.erase_cell(cell)
		_writing=was_writing


func _input_changed() -> void:
	if _writing or not refresh_in_editor: return
	_pending=true; _changed_at=Time.get_ticks_msec()


func _synchronize_from_inputs() -> void:
	# 在首帧deferred期间原生输入可能已改变，先读取最新源层，不能用_ready旧快照覆盖它。
	_adopt_inputs(); synchronize()


func _process(_delta: float) -> void:
	# 实测headless/programmatic Terrain批改有未发changed的路径；120ms轻量占用轮询兜底。
	# 比较占用和材质索引，不每帧读取PNG或重建艺术像素；持续变化则重新计debounce。
	var now:=Time.get_ticks_msec()
	if not _dragging and not _writing and refresh_in_editor and now-_last_poll_at>=120:
		_last_poll_at=now
		_adopt_inputs()
		var observed:=JSON.stringify(snapshot())
		if observed!=_observed_fingerprint:
			_observed_fingerprint=observed; _pending=true; _changed_at=now
	if _pending and not _dragging and Time.get_ticks_msec()-_changed_at>=120:
		_pending=false
		_adopt_inputs()
		if JSON.stringify(snapshot())!=_fingerprint: synchronize()


func _write_inputs() -> void:
	_writing=true
	for id in ["floor","bridge"]:
		var layer := get_node_or_null(id.capitalize()) as TileMapLayer
		if layer==null: continue
		layer.clear()
		var cells: Dictionary = floor_cells if id=="floor" else bridge_cells
		for cell: Vector2i in cells: layer.set_cell(cell,0,_lookup[id][compiler.mask_at(cells,cell)])
	var material_layer:=get_node_or_null("FloorMaterials") as TileMapLayer
	if material_layer!=null:
		material_layer.clear()
		for cell: Vector2i in floor_materials:
			material_layer.set_cell(cell,0,Vector2i(int(floor_materials[cell]),0))
	_writing=false


func synchronize() -> void:
	if _lookup.is_empty(): _load_lookup()
	# 清除重叠和界外输入后计算一次联合脚印，避免不同遍历顺序留下旧收口。
	for cell: Vector2i in floor_cells.keys():
		if not bounds_cells.has_point(cell): floor_cells.erase(cell)
	for cell: Vector2i in bridge_cells.keys():
		if floor_cells.has(cell) or not bounds_cells.has_point(cell): bridge_cells.erase(cell)
	for cell: Vector2i in floor_materials.keys():
		if not floor_cells.has(cell) or int(floor_materials[cell])==0 or not _material_ids.has(int(floor_materials[cell])): floor_materials.erase(cell)
	_write_inputs()
	var started := Time.get_ticks_msec()
	var changed:=_changed_rect()
	var full: bool=last_build.is_empty() or not last_build.has("coverage") or last_build.floor.get_size()!=bounds_cells.size*128
	# context像素相对画布原点保存，世界纹理也按该原点取相位；同尺寸移动原点必须全编译。
	if not full:
		full=not last_build.has("pixel_origin") or last_build.pixel_origin!=bounds_cells.position*128
	if full:
		last_dirty_bounds=bounds_cells
		last_build=compiler.build_visual_layers(floor_cells,bridge_cells,bounds_cells,floor_materials)
	elif changed.size!=Vector2i.ZERO:
		# 两格受影响区包含相邻收口及向南一格的厚立面，外再加一格halo屏蔽人工编译边缘。
		var patch:=changed.grow(2).intersection(bounds_cells)
		var area:=patch.grow(1).intersection(bounds_cells)
		last_dirty_bounds=area
		var fragment:=compiler.build_visual_layers(floor_cells,bridge_cells,area,floor_materials)
		var source_rect:=Rect2i((patch.position-area.position)*128,patch.size*128)
		var target:=(patch.position-bounds_cells.position)*128
		for id: String in LAYERS+ ["coverage"]: last_build[id].blit_rect(fragment[id],source_rect,target)
	else:
		last_dirty_bounds=Rect2i()
		_pending=false; _fingerprint=JSON.stringify(snapshot()); _observed_fingerprint=_fingerprint; return
	for id: String in LAYERS: _apply_context(id,last_build[id])
	last_rebuild_ms=Time.get_ticks_msec()-started
	_rendered_floor=floor_cells.duplicate(); _rendered_bridge=bridge_cells.duplicate()
	_rendered_materials=floor_materials.duplicate()
	_fingerprint=JSON.stringify(snapshot())
	_observed_fingerprint=_fingerprint
	_pending=false


func _changed_rect() -> Rect2i:
	var dirty: Dictionary={}
	for cell: Vector2i in floor_cells:
		if not _rendered_floor.has(cell): dirty[cell]=true
	for cell: Vector2i in _rendered_floor:
		if not floor_cells.has(cell): dirty[cell]=true
	for cell: Vector2i in bridge_cells:
		if not _rendered_bridge.has(cell): dirty[cell]=true
	for cell: Vector2i in _rendered_bridge:
		if not bridge_cells.has(cell): dirty[cell]=true
	# 纯换材质没有改变has(cell)，必须比较材质值，才能触发局部艺术编译。
	for cell: Vector2i in floor_materials:
		if int(floor_materials[cell])!=int(_rendered_materials.get(cell,0)): dirty[cell]=true
	for cell: Vector2i in _rendered_materials:
		if int(_rendered_materials[cell])!=int(floor_materials.get(cell,0)): dirty[cell]=true
	if dirty.is_empty(): return Rect2i()
	var first: Vector2i=dirty.keys()[0]; var area:=Rect2i(first,Vector2i.ONE)
	for cell: Vector2i in dirty: area=area.expand(cell)
	return area


func _apply_context(id: String,image: Image) -> void:
	var layer := get_node_or_null(id.capitalize()+"Context") as TileMapLayer
	if layer==null:
		layer=TileMapLayer.new(); layer.name=id.capitalize()+"Context"; add_child(layer)
		# 默认owner=null；派生数据可恢复，布局由原生Floor/Bridge节点保存。
	layer.scale=Vector2(0.25,0.25); layer.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	layer.z_index=int(LAYERS.find(id))
	if layer.tile_set!=null and layer.tile_set.has_source(0):
		var existing:=layer.tile_set.get_source(0) as TileSetAtlasSource
		# 原点改变时需重建派生格坐标，不能只更新纹理后继续显示在旧bounds位置。
		if existing.texture is ImageTexture and Vector2i(existing.texture.get_size())==image.get_size() and layer.get_used_rect()==bounds_cells:
			existing.texture.update(image)
			# 使AtlasSource的padding缓存同样失效；GPU动态验收检查第二次update而非仅初建。
			existing.emit_changed()
			return
	var set := TileSet.new(); set.tile_size=Vector2i(128,128)
	var source := TileSetAtlasSource.new(); source.texture=ImageTexture.create_from_image(image); source.texture_region_size=Vector2i(128,128)
	set.add_source(source,0)
	layer.clear(); layer.tile_set=set
	for y in range(bounds_cells.size.y):
		for x in range(bounds_cells.size.x):
			var coord := Vector2i(x,y); source.create_tile(coord); layer.set_cell(coord+bounds_cells.position,0,coord)


func paint_floor(cell: Vector2i,material_id: int=0) -> void:
	if not bounds_cells.has_point(cell): return
	if not _valid_material_id(material_id): return
	if floor_cells.has(cell) and int(floor_materials.get(cell,0))==material_id: return
	floor_cells[cell]=true; bridge_cells.erase(cell)
	_set_material_id(cell,material_id)
	_write_inputs()


func paint_material(cell: Vector2i,material_id: int) -> void:
	## 只换已有地板的表面，不创建新的Floor占用，也不影响桥或外轮廓。
	if not bounds_cells.has_point(cell) or not floor_cells.has(cell): return
	if not _valid_material_id(material_id): return
	if int(floor_materials.get(cell,0))==material_id: return
	_set_material_id(cell,material_id)
	_write_inputs()


func _set_material_id(cell: Vector2i,material_id: int) -> void:
	if material_id==0: floor_materials.erase(cell)
	else: floor_materials[cell]=material_id


func _valid_material_id(material_id: int) -> bool:
	if _material_ids.has(material_id): return true
	push_warning("Floor material id is not registered in catalog: "+str(material_id))
	return false


func paint_bridge(cell: Vector2i,width_cells: int=2) -> void:
	# 锚点是左上格，默认2×2 stamp；连续拖拽合成二格宽直线、L、T、X。
	for y in range(clampi(width_cells,1,2)):
		for x in range(clampi(width_cells,1,2)):
			var p := cell+Vector2i(x,y)
			if bounds_cells.has_point(p) and not floor_cells.has(p): bridge_cells[p]=true
	_write_inputs()


func erase_cell(cell: Vector2i) -> void:
	if not floor_cells.has(cell) and not bridge_cells.has(cell) and not floor_materials.has(cell): return
	floor_cells.erase(cell); bridge_cells.erase(cell); floor_materials.erase(cell); _write_inputs()


func snapshot() -> Dictionary:
	return {"version":3,"bounds":[bounds_cells.position.x,bounds_cells.position.y,bounds_cells.size.x,bounds_cells.size.y],"floor":_cells_array(floor_cells),"bridge":_cells_array(bridge_cells),"materials":_materials_array()}


func _cells_array(cells: Dictionary) -> Array:
	var ordered := cells.keys()
	ordered.sort_custom(func(a: Vector2i,b: Vector2i) -> bool: return a.y<b.y if a.y!=b.y else a.x<b.x)
	var result: Array=[]
	for cell: Vector2i in ordered: result.append([cell.x,cell.y])
	return result


func _materials_array() -> Array:
	# 确定排序保证undo比较、JSON存档和构建器的warm-cache SHA不受Dictionary遍历顺序影响。
	var ordered:=floor_materials.keys()
	ordered.sort_custom(func(a: Vector2i,b: Vector2i) -> bool: return a.y<b.y if a.y!=b.y else a.x<b.x)
	var result: Array=[]
	for cell: Vector2i in ordered:
		var id:=int(floor_materials[cell])
		if id!=0 and floor_cells.has(cell): result.append([cell.x,cell.y,id])
	return result


func restore_snapshot(state: Dictionary) -> void:
	floor_cells.clear(); bridge_cells.clear(); floor_materials.clear()
	var area: Array=state.get("bounds",[0,0,24,16]); bounds_cells=Rect2i(int(area[0]),int(area[1]),int(area[2]),int(area[3]))
	for xy: Array in state.get("floor",[]): floor_cells[Vector2i(int(xy[0]),int(xy[1]))]=true
	for xy: Array in state.get("bridge",[]): bridge_cells[Vector2i(int(xy[0]),int(xy[1]))]=true
	# version2没有材质字段，按默认钢面恢复；version3仅接受合法且确实有Floor的非零ID。
	if int(state.get("version",2))>=3:
		for entry: Array in state.get("materials",[]):
			if entry.size()<3: continue
			var cell:=Vector2i(int(entry[0]),int(entry[1]))
			var id:=int(entry[2])
			if floor_cells.has(cell) and id!=0 and _material_ids.has(id): floor_materials[cell]=id
	synchronize()


func commit_edit(before: Dictionary) -> void:
	if JSON.stringify(before)!=JSON.stringify(snapshot()): _undo.append(before.duplicate(true)); _redo.clear()


func undo_edit() -> bool:
	if _undo.is_empty(): return false
	_redo.append(snapshot()); restore_snapshot(_undo.pop_back()); return true


func redo_edit() -> bool:
	if _redo.is_empty(): return false
	_undo.append(snapshot()); restore_snapshot(_redo.pop_back()); return true


func save_layout(path: String="user://reference_floor_v004_layout.json") -> bool:
	var file := FileAccess.open(path,FileAccess.WRITE)
	if file==null: return false
	file.store_string(JSON.stringify(snapshot(),"\t")+"\n"); return true


func load_layout(path: String="user://reference_floor_v004_layout.json") -> bool:
	if not FileAccess.file_exists(path): return false
	var state=JSON.parse_string(FileAccess.get_file_as_string(path))
	if not state is Dictionary or int(state.get("version",0)) not in [2,3]: return false
	restore_snapshot(state); return true


func _unhandled_input(event: InputEvent) -> void:
	if Engine.is_editor_hint(): return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.ctrl_pressed:
			if event.keycode==KEY_Z: undo_edit()
			elif event.keycode==KEY_Y: redo_edit()
			elif event.keycode==KEY_S: save_layout()
			elif event.keycode==KEY_L: load_layout()
		elif event.keycode in [KEY_1,KEY_2,KEY_3]:
			_brush=int(event.keycode-KEY_1)+1
			_update_help()
		elif MATERIAL_SHORTCUTS.has(event.keycode):
			_select_material(int(MATERIAL_SHORTCUTS[event.keycode]))
		elif event.keycode in [KEY_BRACKETLEFT,KEY_BRACKETRIGHT]:
			_cycle_material(-1 if event.keycode==KEY_BRACKETLEFT else 1)
	if event is InputEventMouseButton and event.button_index in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_RIGHT]:
		if event.pressed:
			_dragging=true; _stroke_before=snapshot(); _stroke_cells.clear(); _paint_mouse(event.button_index==MOUSE_BUTTON_RIGHT)
		else:
			_dragging=false; commit_edit(_stroke_before)
			if JSON.stringify(snapshot())!=_fingerprint: synchronize()
	if event is InputEventMouseMotion and _dragging: _paint_mouse(Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT))


func _paint_mouse(erase: bool) -> void:
	var mouse:=get_local_mouse_position(); var cell:=Vector2i(floori(mouse.x/32),floori(mouse.y/32))
	if _stroke_cells.has(cell): return
	_stroke_cells[cell]=true
	if erase:
		var size:=2 if _brush==2 else 1
		for y in range(size):
			for x in range(size): erase_cell(cell+Vector2i(x,y))
	elif _brush==1: paint_floor(cell,_selected_material_id)
	else: paint_bridge(cell,2 if _brush==2 else 1)


func _build_help() -> void:
	var hud:=CanvasLayer.new(); hud.name="Help"; add_child(hud)
	_help_label=Label.new()
	_help_label.position=Vector2(12,8); _help_label.add_theme_font_size_override("font_size",17); _help_label.add_theme_color_override("font_outline_color",Color(0,0,0,1)); _help_label.add_theme_constant_override("outline_size",3)
	hud.add_child(_help_label)
	_update_help()


func _select_material(material_id: int) -> void:
	if not _material_ids.has(material_id): return
	_selected_material_id=material_id
	_brush=1
	_update_help()


func _cycle_material(step: int) -> void:
	var current:=_material_ids.find(_selected_material_id)
	if current<0: current=0
	var next_index:=posmod(current+step,_material_ids.size())
	_select_material(_material_ids[next_index])


func _update_help() -> void:
	if not is_instance_valid(_help_label): return
	var material_label:=str(_material_keys.get(_selected_material_id,"material")).capitalize()
	var mode:="Floor: "+material_label+" ("+str(_selected_material_id)+")" if _brush==1 else ("Bridge 2x2" if _brush==2 else "Bridge 1x1")
	_help_label.text="1 Floor  2 Bridge 2x2  3 Bridge 1x1  |  4-9/0 Material  [ ] Cycle\n"+mode+"  |  Left paint / Right erase  |  Ctrl Z/Y/S/L"
