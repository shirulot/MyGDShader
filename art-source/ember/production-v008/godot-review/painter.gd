extends Node2D
## 两侧共享占用格，分别让 Godot 从各自图集选择相同语义图块。
## 层始终缩放0.25；滚轮只改变相机，不伪改128px纹理尺寸。

const Helpers := preload("res://terrain_helpers.gd")
var layers: Array[TileMapLayer] = []
var occupied: Dictionary = {}
var camera: Camera2D
var active_button := 0
var panning := false
var paint_event_count := 0
var erase_event_count := 0
var zoom_event_count := 0
var baseline_count := 47
var trial_new_count := 0
var trial_reused_count := 47

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var catalog := Helpers.read_catalog()
	for index in range(catalog.atlases.size()):
		var atlas: Dictionary = catalog.atlases[index]
		var layer := TileMapLayer.new()
		layer.name = str(atlas.id).to_pascal_case()
		layer.tile_set = load("res://"+str(atlas.id)+"_terrain.tres")
		layer.scale = Vector2.ONE*0.25
		# map_to_local(0,0)已在格中心，节点位置直接对齐网格左上。
		layer.position = Vector2(40+index*768,132)
		add_child(layer)
		layers.append(layer)
		if str(atlas.id) == "trial":
			trial_new_count = int(atlas.get("new_sample_count",0))
			trial_reused_count = int(atlas.get("reused_v007_count",47))
		var label := Label.new()
		label.text = "BASELINE · 47 reused v007" if str(atlas.id) == "baseline" else "TRIAL · %d reused + %d new samples" % [trial_reused_count,trial_new_count]
		label.position = Vector2(40+index*768,90)
		label.add_theme_font_size_override("font_size",20)
		add_child(label)
	var heading := Label.new()
	heading.text = "Official 12x4 · 47 masks · Match Corners And Sides · texture128 / world32"
	heading.position = Vector2(40,24)
	heading.add_theme_font_size_override("font_size",24)
	add_child(heading)
	var help := Label.new()
	help.text = "Left: paint | Right: erase | Wheel: zoom | Middle: pan | R: reset · Visual approval pending"
	help.position = Vector2(40,58)
	add_child(help)
	var note := Label.new()
	note.text = "Views: center / north edge / hole / L / narrow / erase end. Mixed trial is NOT 47 newly generated tiles."
	note.position = Vector2(40,632)
	add_child(note)
	camera = Camera2D.new()
	camera.position = Vector2(768,450)
	add_child(camera)
	occupied = Helpers.initial_cells()
	_rebuild()

func _rebuild() -> void:
	for layer in layers: Helpers.rebuild(layer,occupied)
	queue_redraw()

func _draw() -> void:
	# 仅绘制背景网格诊断，不处理构件像素或连接边缘。
	for index in range(layers.size()):
		var origin := Vector2(40+index*768,132)
		for x in range(21): draw_line(origin+Vector2(x*32,0),origin+Vector2(x*32,448),Color(0.12,0.18,0.21),1)
		for y in range(15): draw_line(origin+Vector2(0,y*32),origin+Vector2(640,y*32),Color(0.12,0.18,0.21),1)

func _screen_to_cell(screen_position: Vector2) -> Variant:
	var world := get_viewport().get_canvas_transform().affine_inverse()*screen_position
	for layer in layers:
		var local := layer.to_local(world)
		var cell := layer.local_to_map(local)
		if cell.x >= 0 and cell.x < 20 and cell.y >= 0 and cell.y < 14:
			return cell
	return null

func screen_position_for_cell(cell: Vector2i, panel: int=0) -> Vector2:
	var layer := layers[panel]
	return get_viewport().get_canvas_transform()*(layer.global_transform*layer.map_to_local(cell))

func _apply_brush(screen_position: Vector2, button: int) -> void:
	var cell = _screen_to_cell(screen_position)
	if cell == null: return
	if button == MOUSE_BUTTON_LEFT:
		occupied[cell] = true
		paint_event_count += 1
	elif button == MOUSE_BUTTON_RIGHT:
		occupied.erase(cell)
		erase_event_count += 1
	_rebuild()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_R:
		occupied = Helpers.initial_cells()
		_rebuild()
	elif event is InputEventMouseButton:
		if event.button_index in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_RIGHT]:
			active_button = event.button_index if event.pressed else 0
			if event.pressed: _apply_brush(event.position,event.button_index)
		elif event.button_index == MOUSE_BUTTON_MIDDLE:
			panning = event.pressed
		elif event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:
			var factor := 1.25 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 0.8
			camera.zoom = (camera.zoom*factor).clamp(Vector2.ONE*0.5,Vector2.ONE*4)
			zoom_event_count += 1
	elif event is InputEventMouseMotion:
		if panning: camera.position -= event.relative/camera.zoom
		elif active_button != 0: _apply_brush(event.position,active_button)
