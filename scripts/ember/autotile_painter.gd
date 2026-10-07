extends Node2D
## 独立素材沙盒：在各面板内左键画、右键擦；不接入正式游戏逻辑。
## 地形笔刷在编辑器中也可用。此脚本演示运行时传格子数组批量连接。
var preview_camera: Camera2D

func _ready() -> void:
	# 仅高分辨率保真样板启用缩放，不改变历史沙盒。
	if get_meta("enable_zoom",false):
		preview_camera = Camera2D.new()
		preview_camera.position = Vector2(320,320)
		add_child(preview_camera)
		var hint := Label.new()
		hint.text = "左键画 / 右键擦 · 滚轮缩放 / 中键拖动"
		var hud := CanvasLayer.new()
		add_child(hud)
		hud.add_child(hint)
		hint.position = Vector2(12,4)

func _unhandled_input(event: InputEvent) -> void:
	if preview_camera != null:
		if event is InputEventMouseButton and event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:
			var factor := 1.25 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 0.8
			preview_camera.zoom = Vector2.ONE * clampf(preview_camera.zoom.x*factor,0.5,4.0)
			get_viewport().set_input_as_handled()
			return
		if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_MIDDLE):
			preview_camera.position -= event.relative / preview_camera.zoom
			get_viewport().set_input_as_handled()
			return
	var painting := event is InputEventMouseMotion and (Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT))
	if event is InputEventMouseButton:
		painting = event.pressed and event.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]
	if not painting:
		return
	for child in get_children():
		if not child is TileMapLayer or child.name == "Bank":
			continue
		var layer := child as TileMapLayer
		var cell := layer.local_to_map(layer.get_local_mouse_position())
		if not Rect2i(0,0,8,5).has_point(cell):
			continue
		var cells := layer.get_used_cells()
		if Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
			cells.erase(cell)
		elif not cells.has(cell):
			cells.append(cell)
		# 小沙盒整层重建：保证擦除后重新计算端头与凹角，结果只依赖占用格。
		rebuild(layer, cells)
		if layer.name == "Water":
			rebuild($Bank, cells)
		get_viewport().set_input_as_handled()
		break

static func rebuild(layer: TileMapLayer, occupied_cells: Array[Vector2i]) -> void:
	## 每一类 Terrain 用独立层；水面和岸沿传入同一份坐标。
	layer.clear()
	if not occupied_cells.is_empty():
		# false：把外围空格纳入匹配，否则可能选到开放边而不是端头。
		layer.set_cells_terrain_connect(occupied_cells, 0, 0, false)
