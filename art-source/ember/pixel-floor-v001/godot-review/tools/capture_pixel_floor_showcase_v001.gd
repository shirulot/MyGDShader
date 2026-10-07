extends SceneTree
## 实际素材的场景展示，不生成另一张概念图，不改变交互试铺工具。
## Floor 等仍是 TileMapLayer，角色 / 站点仍是现有原生 PNG，scale=(1,1)。
## 背景色与稀疏像素只用于衬托本次地板，不是已交付水域 Terrain。

const ASSETS := "res://assets/ember/environment/pixel_floor_v001/"
const SCENE := "res://scenes/ember/pixel_floor_showcase_v001.tscn"
const ROBOT := "res://assets/ember/characters/robot/robot_idle_down_v001.png"
const STATION := "res://assets/ember/buildings/station/station_base_v001.png"
const DIRECTIONS := [Vector2i.UP,Vector2i(1,-1),Vector2i.RIGHT,Vector2i(1,1),Vector2i.DOWN,Vector2i(-1,1),Vector2i.LEFT,Vector2i(-1,-1)]
var regions := {"floor":{},"bridge":{},"grate":{},"seam":{},"details":{}}
var seam_edges := {}
var lookup := {}
var layers := {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ASSETS + "catalog.json"))
	for atlas: Dictionary in catalog.atlases:
		lookup[atlas.id] = {}
		for entry: Dictionary in atlas.tiles:
			var key = "%d:%d" % [int(entry.floor_mask),int(entry.bridge_ports)] if atlas.mode == "context" else int(entry.mask)
			lookup[atlas.id][key] = Vector2i(int(entry.coord[0]),int(entry.coord[1]))
	_layout()
	var stage := Node2D.new()
	stage.name = "PixelFloorShowcaseV001"
	stage.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	root.add_child(stage)
	_background(stage)
	for id: String in ["floor_facade","floor","bridge","floor_landing","grate","seam","rim","details"]:
		var layer := TileMapLayer.new()
		layer.name = id.to_pascal_case()
		var family := "floor" if id == "floor_landing" else ("facade" if id == "floor_facade" else id)
		var resource_path := ASSETS + ("details_tileset_v001.tres" if id == "details" else family + "_terrain_v001.tres")
		layer.tile_set = ResourceLoader.load(resource_path,"TileSet",ResourceLoader.CACHE_MODE_IGNORE)
		if id == "floor_facade": layer.position = Vector2(0,16)
		stage.add_child(layer)
		layer.owner = stage
		layers[id] = layer
	_place_real_tiles()
	_add_native_sprite(stage,STATION,Vector2(848,285),Vector2(64,144),"ReferenceStation")
	_add_native_sprite(stage,ROBOT,Vector2(624,430),Vector2(32,80),"ReferenceRobot")
	var note := Label.new()
	note.name = "ShowcaseNote"
	note.text = "实际32px瓦片＋原生比例设备   ·   深水色背景仅作展示，不是新水域素材"
	note.position = Vector2(16,772)
	note.add_theme_color_override("font_color",Color("becbc4"))
	note.add_theme_font_size_override("font_size",15)
	stage.add_child(note)
	note.owner = stage
	var packed := PackedScene.new()
	assert(packed.pack(stage) == OK)
	assert(ResourceSaver.save(packed,SCENE) == OK)
	root.content_scale_size = Vector2i(1024,800)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	var captures: Array[Dictionary] = []
	for zoom in [1,2]:
		root.size = Vector2i(1024,800) * zoom
		await process_frame
		await RenderingServer.frame_post_draw
		var pixels := root.get_texture().get_image()
		var filename := "gpu_scene_showcase_%dx_v001.png" % zoom
		assert(pixels.save_png(ASSETS+filename) == OK)
		captures.append({"path":filename,"size":[pixels.get_width(),pixels.get_height()],"display_integer_scale":zoom})
	var report := {
		"engine":Engine.get_version_info().string,
		"renderer":RenderingServer.get_current_rendering_method(),
		"material_revision":catalog.get("material_revision","unrecorded"),
		"source":"actual TileMapLayer + delivered TileSet .tres; GPU viewport readback",
		"tile_native_size":[32,32],
		"tile_world_size":[32,32],
		"robot":{"path":ROBOT,"native_size":[64,96],"sprite_scale":[1,1]},
		"station":{"path":STATION,"native_size":[128,160],"sprite_scale":[1,1]},
		"background":"preview-only dark water colour and sparse procedural pixels; not a water atlas, shader, collision, or gameplay resource",
		"hole_count":2,
		"floor_cells":regions.floor.size(),
		"bridge_cells":regions.bridge.size(),
		"landing_cells":layers.floor_landing.get_used_cells().size(),
		"facade_cells":layers.floor_facade.get_used_cells().size(),
		"facade_projection_world_pixels":16,
		"captures":captures
	}
	var output := FileAccess.open(ASSETS+"showcase_validation.json",FileAccess.WRITE)
	output.store_string(JSON.stringify(report,"\t")+"\n")
	print(JSON.stringify(report))
	stage.free()
	quit()

func _layout() -> void:
	# L 形宽平台 + 两孔洞；四方向的接口仍取正式邻接图块。
	for y in range(4,23):
		for x in range(11,31):
			var cell := Vector2i(x,y)
			if Rect2i(11,16,6,6).has_point(cell): continue
			if Rect2i(20,9,3,3).has_point(cell): continue
			if Rect2i(27,15,2,3).has_point(cell): continue
			regions.floor[cell] = true
	for y in range(9,14):
		for x in range(3,7): regions.floor[Vector2i(x,y)] = true
	for x in range(7,11): regions.bridge[Vector2i(x,11)] = true
	for y in range(7,10):
		for x in range(24,28): regions.grate[Vector2i(x,y)] = true
	_add_seam_path([Vector2i(14,8),Vector2i(14,15),Vector2i(20,15)])
	_add_seam_path([Vector2i(23,6),Vector2i(29,6),Vector2i(29,13)])
	_add_seam_path([Vector2i(23,19),Vector2i(30,19)])
	for entry in [[18,14,0],[26,11,2],[18,17,6],[5,12,4],[29,21,3],[23,13,1]]:
		regions.details[Vector2i(entry[0],entry[1])] = int(entry[2])

func _edge_key(a: Vector2i,b: Vector2i) -> String:
	if a.y > b.y or (a.y == b.y and a.x > b.x):
		var temp := a; a = b; b = temp
	return "%d,%d:%d,%d" % [a.x,a.y,b.x,b.y]

func _add_seam_path(points: Array[Vector2i]) -> void:
	var previous: Vector2i = points[0]
	regions.seam[previous] = true
	for endpoint: Vector2i in points.slice(1):
		while previous != endpoint:
			var next := previous
			if next.x != endpoint.x: next.x += 1 if endpoint.x > next.x else -1
			else: next.y += 1 if endpoint.y > next.y else -1
			if regions.floor.has(next):
				regions.seam[next] = true
				if regions.floor.has(previous): seam_edges[_edge_key(previous,next)] = true
			previous = next

func _blob(cell: Vector2i,region: Dictionary) -> int:
	var mask := 0
	for bit in range(8):
		if region.has(cell+DIRECTIONS[bit]): mask |= 1 << bit
	for diagonal in [1,3,5,7]:
		if not (mask & (1 << ((diagonal+7)%8))) or not (mask & (1 << ((diagonal+1)%8))): mask &= ~(1 << diagonal)
	return mask

func _sides(cell: Vector2i,region: Dictionary) -> int:
	var mask := 0
	for bit in range(4):
		if region.has(cell+DIRECTIONS[bit*2]): mask |= 1 << bit
	return mask

func _place_real_tiles() -> void:
	var walkable: Dictionary = regions.floor.duplicate()
	for cell in regions.bridge: walkable[cell] = true
	for cell: Vector2i in regions.floor:
		var mask := _blob(cell,regions.floor)
		var ports := _sides(cell,regions.bridge)
		layers.floor.set_cell(cell,0,lookup.floor[mask])
		if ports:
			var key := "%d:%d" % [mask,ports]
			layers.floor_landing.set_cell(cell,1,lookup.floor_landing[key])
			layers.rim.set_cell(cell,1,lookup.rim_landing[key])
			layers.floor_facade.set_cell(cell,1,lookup.facade_landing[key])
		else:
			layers.rim.set_cell(cell,0,lookup.rim[mask])
			layers.floor_facade.set_cell(cell,0,lookup.facade[mask])
	for cell: Vector2i in regions.bridge: layers.bridge.set_cell(cell,0,lookup.bridge[_sides(cell,walkable)])
	for cell: Vector2i in regions.grate: layers.grate.set_cell(cell,0,lookup.grate[_blob(cell,regions.grate)])
	for cell: Vector2i in regions.seam:
		var mask := 0
		for bit in range(4):
			if seam_edges.has(_edge_key(cell,cell+DIRECTIONS[bit*2])): mask |= 1 << bit
		layers.seam.set_cell(cell,0,lookup.seam[mask])
	for cell: Vector2i in regions.details: layers.details.set_cell(cell,0,Vector2i(regions.details[cell],0))

func _background(stage: Node2D) -> void:
	var pixels := Image.create(1024,768,false,Image.FORMAT_RGBA8)
	pixels.fill(Color("122b33"))
	var rng := RandomNumberGenerator.new()
	rng.seed = 60106
	# 极稀疏、低对比的横向像素簇，避免掩盖地板材质判断。
	for cluster in range(220):
		var x := rng.randi_range(0,1013)
		var y := rng.randi_range(0,764)
		var width := rng.randi_range(2,9)
		for step in range(width): pixels.set_pixel(x+step,y,Color("1b3941"))
		if cluster % 4 == 0:
			for step in range(maxi(1,width-3)): pixels.set_pixel(x+2+step,y+1,Color("19353d"))
	var background := Sprite2D.new()
	background.name = "PreviewOnlyWaterColour"
	background.centered = false
	background.texture = ImageTexture.create_from_image(pixels)
	stage.add_child(background)
	background.owner = stage

func _add_native_sprite(stage: Node2D,path: String,anchor_position: Vector2,anchor: Vector2,node_name: String) -> void:
	var pixels := Image.new()
	assert(pixels.load_png_from_buffer(FileAccess.get_file_as_bytes(path)) == OK)
	var sprite := Sprite2D.new()
	sprite.name = node_name
	sprite.texture = ImageTexture.create_from_image(pixels)
	sprite.centered = false
	sprite.position = anchor_position - anchor
	sprite.scale = Vector2.ONE
	stage.add_child(sprite)
	sprite.owner = stage
