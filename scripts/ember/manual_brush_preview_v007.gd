extends Node2D
## 左侧 67 个完整笔刷，点击选择；右侧左键画、右键擦。
## TileSet 为 128px 美术，TileMapLayer 缩放为 32 世界单位。
const DIR := "res://assets/ember/environment/tilesets_v007/"
const PALETTE := Vector2(16,72)
const PAINT_ORIGIN := Vector2(680,88)
var entries: Array[Dictionary] = []
var selected := 0
var canvas: TileMapLayer
var title: Label

func _ready() -> void:
	# 仅此预览窗口使用完整笔刷面板尺寸，不改 project.godot 全局设置。
	get_window().size = Vector2i(1280,900)
	get_window().content_scale_size = Vector2i(1280,900)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIR + "catalog.json"))
	for atlas in catalog.atlases:
		var texture: Texture2D = load(atlas.texture)
		for entry in atlas.tiles:
			entries.append({"source":int(atlas.source_id),"coord":Vector2i(int(entry.coord[0]),int(entry.coord[1])),"id":entry.id,"name":entry.name})
			var index := entries.size()-1
			var sprite := Sprite2D.new()
			sprite.texture = texture
			sprite.region_enabled = true
			sprite.region_rect = Rect2(Vector2(entries[index].coord)*128.0,Vector2(128,128))
			sprite.centered = false
			sprite.scale = Vector2.ONE*.5
			sprite.position = PALETTE+Vector2((index%8)*80,(index/8)*88)
			add_child(sprite)
			var label := Label.new()
			label.text = str(entry.name)
			label.add_theme_font_size_override("font_size",11)
			label.position = sprite.position+Vector2(0,64)
			add_child(label)
	var floor_layer := TileMapLayer.new()
	floor_layer.tile_set = load(DIR + "ember_common_tileset_v007.tres")
	floor_layer.scale = Vector2.ONE*.25
	floor_layer.position = PAINT_ORIGIN
	add_child(floor_layer)
	canvas = TileMapLayer.new()
	canvas.tile_set = load(DIR + "ember_common_tileset_v007.tres")
	canvas.scale = Vector2.ONE*.25
	canvas.position = PAINT_ORIGIN
	add_child(canvas)
	title = Label.new()
	title.position = Vector2(16,12)
	add_child(title)
	# 用新地板预铺测试区，让透明贴花可以直接叠加查看。
	for y in range(18):
		for x in range(18):
			floor_layer.set_cell(Vector2i(x,y),0,Vector2i.ZERO)
	_update_title()
	queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(0,0,1280,900),Color("182631"))
	draw_rect(Rect2(PAINT_ORIGIN,Vector2(576,576)),Color("203542"))
	if not entries.is_empty():
		var pos := PALETTE+Vector2((selected%8)*80,(selected/8)*88)
		draw_rect(Rect2(pos-Vector2(3,3),Vector2(70,70)),Color("e6b66a"),false,2)

func _update_title() -> void:
	title.text = "统一风格笔刷 67 项  ·  " + str(entries[selected].name) + "  |  左侧选笔刷 · 右侧左键画 / 右键擦"

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var point := get_local_mouse_position()-PALETTE
		var col := int(floor(point.x/80.0))
		var row := int(floor(point.y/88.0))
		var index := row*8+col
		if col >= 0 and col < 8 and row >= 0 and index < entries.size() and fmod(point.x,80) < 64 and fmod(point.y,88) < 64:
			selected = index
			_update_title()
			queue_redraw()
			return
	var dragging: bool = event is InputEventMouseMotion and (Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT))
	var clicking: bool = event is InputEventMouseButton and event.pressed and event.button_index in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_RIGHT]
	if not dragging and not clicking:
		return
	var cell := canvas.local_to_map(canvas.get_local_mouse_position())
	if Rect2i(0,0,18,18).has_point(cell):
		if Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
			canvas.erase_cell(cell)
		else:
			canvas.set_cell(cell,entries[selected].source,entries[selected].coord)
