@tool
extends Node2D
## 编辑器 Floor / Bridge 原生 Terrain 输入 + 同一 artist 编译器自动派生 context。
## 输入只保存占用；Floor 优先，bridge默认2×2面积笔刷；context不参加Terrain随机选块。
## 完整重建保留8格材质相位；source纹理只加载一次，changed采用debounce，笔划结束才编译。

const COMPILER := preload("res://scripts/ember/reference_floor_compiler_v002.gd")
const ASSET := "res://assets/ember/environment/reference_floor_v002/"
const LAYERS := ["water","facade","floor","rim","bridge","heads"]
@export var bounds_cells := Rect2i(0,0,24,16)
@export var refresh_in_editor := true
var floor_cells: Dictionary = {}
var bridge_cells: Dictionary = {}
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
var last_dirty_bounds := Rect2i()
var _baked_signature := ""


func _ready() -> void:
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	compiler.load_materials()
	_load_lookup()
	_adopt_inputs()
	_fingerprint=JSON.stringify(snapshot())
	_observed_fingerprint=_fingerprint
	for id in ["Floor","Bridge"]:
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
	if _baked_signature!=_fingerprint.sha256_text(): has_context=false; last_build.clear()
	if has_context:
		var footprint:=Image.new()
		footprint.load_png_from_buffer(FileAccess.get_file_as_bytes(ASSET+"union_coverage_v002.png"))
		last_build["coverage"]=footprint; last_build["pixel_origin"]=bounds_cells.position*128
		_rendered_floor=floor_cells.duplicate(); _rendered_bridge=bridge_cells.duplicate()
	if not has_context: call_deferred("_synchronize_from_inputs")
	if not Engine.is_editor_hint(): _build_help()
	set_process(true)


func _load_lookup() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ASSET+"catalog.json"))
	_baked_signature=str(catalog.get("demo_layout_signature",""))
	for atlas: Dictionary in catalog.atlases:
		var lookup := {}
		for entry: Dictionary in atlas.tiles: lookup[int(entry.mask)]=Vector2i(int(entry.coord[0]),int(entry.coord[1]))
		_lookup[atlas.id]=lookup


func _adopt_inputs() -> void:
	floor_cells.clear(); bridge_cells.clear()
	var floor_layer := get_node_or_null("Floor") as TileMapLayer
	var bridge_layer := get_node_or_null("Bridge") as TileMapLayer
	if floor_layer!=null:
		for cell in floor_layer.get_used_cells(): floor_cells[cell]=true
	if bridge_layer!=null:
		for cell in bridge_layer.get_used_cells():
			if not floor_cells.has(cell): bridge_cells[cell]=true


func _input_changed() -> void:
	if _writing or not refresh_in_editor: return
	_pending=true; _changed_at=Time.get_ticks_msec()


func _synchronize_from_inputs() -> void:
	# 在首帧deferred期间原生输入可能已改变，先读取最新源层，不能用_ready旧快照覆盖它。
	_adopt_inputs(); synchronize()


func _process(_delta: float) -> void:
	# 实测headless/programmatic Terrain批改有未发changed的路径；120ms轻量占用轮询兜底。
	# 只比较输入格列表，不每帧读取PNG或重建艺术像素；持续变化则重新计debounce。
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
	_writing=false


func synchronize() -> void:
	if _lookup.is_empty(): _load_lookup()
	# 清除重叠和界外输入后计算一次联合脚印，避免不同遍历顺序留下旧收口。
	for cell: Vector2i in floor_cells.keys():
		if not bounds_cells.has_point(cell): floor_cells.erase(cell)
	for cell: Vector2i in bridge_cells.keys():
		if floor_cells.has(cell) or not bounds_cells.has_point(cell): bridge_cells.erase(cell)
	_write_inputs()
	var started := Time.get_ticks_msec()
	var changed:=_changed_rect()
	var full: bool=last_build.is_empty() or not last_build.has("coverage") or last_build.floor.get_size()!=bounds_cells.size*128
	if full:
		last_dirty_bounds=bounds_cells
		last_build=compiler.build_visual_layers(floor_cells,bridge_cells,bounds_cells)
	elif changed.size!=Vector2i.ZERO:
		# 两格受影响区包含相邻收口及向南一格的厚立面，外再加一格halo屏蔽人工编译边缘。
		var patch:=changed.grow(2).intersection(bounds_cells)
		var area:=patch.grow(1).intersection(bounds_cells)
		last_dirty_bounds=area
		var fragment:=compiler.build_visual_layers(floor_cells,bridge_cells,area)
		var source_rect:=Rect2i((patch.position-area.position)*128,patch.size*128)
		var target:=(patch.position-bounds_cells.position)*128
		for id: String in LAYERS+ ["coverage"]: last_build[id].blit_rect(fragment[id],source_rect,target)
	else:
		last_dirty_bounds=Rect2i()
		_pending=false; _fingerprint=JSON.stringify(snapshot()); return
	for id: String in LAYERS: _apply_context(id,last_build[id])
	last_rebuild_ms=Time.get_ticks_msec()-started
	_rendered_floor=floor_cells.duplicate(); _rendered_bridge=bridge_cells.duplicate()
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
		if existing.texture is ImageTexture and Vector2i(existing.texture.get_size())==image.get_size():
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


func paint_floor(cell: Vector2i) -> void:
	if not bounds_cells.has_point(cell): return
	floor_cells[cell]=true; bridge_cells.erase(cell); _write_inputs()


func paint_bridge(cell: Vector2i,width_cells: int=2) -> void:
	# 锚点是左上格，默认2×2 stamp；连续拖拽合成二格宽直线、L、T、X。
	for y in range(clampi(width_cells,1,2)):
		for x in range(clampi(width_cells,1,2)):
			var p := cell+Vector2i(x,y)
			if bounds_cells.has_point(p) and not floor_cells.has(p): bridge_cells[p]=true
	_write_inputs()


func erase_cell(cell: Vector2i) -> void:
	floor_cells.erase(cell); bridge_cells.erase(cell); _write_inputs()


func snapshot() -> Dictionary:
	return {"version":2,"bounds":[bounds_cells.position.x,bounds_cells.position.y,bounds_cells.size.x,bounds_cells.size.y],"floor":_cells_array(floor_cells),"bridge":_cells_array(bridge_cells)}


func _cells_array(cells: Dictionary) -> Array:
	var ordered := cells.keys()
	ordered.sort_custom(func(a: Vector2i,b: Vector2i) -> bool: return a.y<b.y if a.y!=b.y else a.x<b.x)
	var result: Array=[]
	for cell: Vector2i in ordered: result.append([cell.x,cell.y])
	return result


func restore_snapshot(state: Dictionary) -> void:
	floor_cells.clear(); bridge_cells.clear()
	var area: Array=state.get("bounds",[0,0,24,16]); bounds_cells=Rect2i(int(area[0]),int(area[1]),int(area[2]),int(area[3]))
	for xy: Array in state.get("floor",[]): floor_cells[Vector2i(int(xy[0]),int(xy[1]))]=true
	for xy: Array in state.get("bridge",[]): bridge_cells[Vector2i(int(xy[0]),int(xy[1]))]=true
	synchronize()


func commit_edit(before: Dictionary) -> void:
	if JSON.stringify(before)!=JSON.stringify(snapshot()): _undo.append(before.duplicate(true)); _redo.clear()


func undo_edit() -> bool:
	if _undo.is_empty(): return false
	_redo.append(snapshot()); restore_snapshot(_undo.pop_back()); return true


func redo_edit() -> bool:
	if _redo.is_empty(): return false
	_undo.append(snapshot()); restore_snapshot(_redo.pop_back()); return true


func save_layout(path: String="user://reference_floor_v002_layout.json") -> bool:
	var file := FileAccess.open(path,FileAccess.WRITE)
	if file==null: return false
	file.store_string(JSON.stringify(snapshot(),"\t")+"\n"); return true


func load_layout(path: String="user://reference_floor_v002_layout.json") -> bool:
	if not FileAccess.file_exists(path): return false
	var state=JSON.parse_string(FileAccess.get_file_as_string(path))
	if not state is Dictionary or int(state.get("version",0))!=2: return false
	restore_snapshot(state); return true


func _unhandled_input(event: InputEvent) -> void:
	if Engine.is_editor_hint(): return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.ctrl_pressed:
			if event.keycode==KEY_Z: undo_edit()
			elif event.keycode==KEY_Y: redo_edit()
			elif event.keycode==KEY_S: save_layout()
			elif event.keycode==KEY_L: load_layout()
		elif event.keycode in [KEY_1,KEY_2,KEY_3]: _brush=int(event.keycode-KEY_1)+1
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
	elif _brush==1: paint_floor(cell)
	else: paint_bridge(cell,2 if _brush==2 else 1)


func _build_help() -> void:
	var hud:=CanvasLayer.new(); hud.name="Help"; add_child(hud)
	var label:=Label.new(); label.text="1 Floor   2 Bridge 2x2   3 Bridge 1x1   |   Left paint / Right erase   |   Ctrl Z/Y/S/L"
	label.position=Vector2(12,8); label.add_theme_font_size_override("font_size",17); label.add_theme_color_override("font_outline_color",Color(0,0,0,1)); label.add_theme_constant_override("outline_size",3)
	hud.add_child(label)
