extends SceneTree
## 离线构建 Terrain、可编辑场景，并用真实 Godot 铺设结果检查连接。
## 用法：godot --headless --path . -s res://tools/build_ember_autotiles.gd

var revision := "v002"
var output_dir := "res://assets/ember/environment/autotiles_v002/"
var scene_path := "res://scenes/ember/autotile_sandbox_v002.tscn"
var texture_tile_size := 32
const DIRECTIONS := [Vector2i.UP, Vector2i(1,-1), Vector2i.RIGHT, Vector2i(1,1), Vector2i.DOWN, Vector2i(-1,1), Vector2i.LEFT, Vector2i(-1,-1)]
const BITS := [TileSet.CELL_NEIGHBOR_TOP_SIDE, TileSet.CELL_NEIGHBOR_TOP_RIGHT_CORNER, TileSet.CELL_NEIGHBOR_RIGHT_SIDE, TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER, TileSet.CELL_NEIGHBOR_BOTTOM_SIDE, TileSet.CELL_NEIGHBOR_BOTTOM_LEFT_CORNER, TileSet.CELL_NEIGHBOR_LEFT_SIDE, TileSet.CELL_NEIGHBOR_TOP_LEFT_CORNER]
var failures: Array[String] = []
var checked := 0

func _initialize() -> void:
	if "--revision=v003" in OS.get_cmdline_user_args():
		revision = "v003"
		output_dir = "res://assets/ember/environment/autotiles_v003/"
		scene_path = "res://scenes/ember/autotile_sandbox_v003.tscn"
	if "--revision=v004" in OS.get_cmdline_user_args():
		revision = "v004"
		output_dir = "res://assets/ember/environment/autotiles_v004/"
		scene_path = "res://scenes/ember/autotile_sandbox_v004.tscn"
	if "--revision=v005" in OS.get_cmdline_user_args():
		revision = "v005"
		output_dir = "res://assets/ember/environment/autotiles_v005/"
		scene_path = "res://scenes/ember/autotile_sandbox_v005.tscn"
	if "--revision=v006" in OS.get_cmdline_user_args():
		revision = "v006"
		output_dir = "res://assets/ember/environment/autotiles_v006/"
		scene_path = "res://scenes/ember/autotile_sandbox_v006.tscn"
	if "--revision=v007" in OS.get_cmdline_user_args():
		revision = "v007"
		output_dir = "res://assets/ember/environment/autotiles_v007/"
		scene_path = "res://scenes/ember/autotile_sandbox_v007.tscn"
	call_deferred("_run")

func _run() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(output_dir + "catalog.json"))
	texture_tile_size = int(catalog.get("tile_size",32))
	var scene := Node2D.new()
	scene.name = "EmberAutotileSandbox"
	scene.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	scene.set_script(load("res://scripts/ember/autotile_painter.gd"))
	scene.set_meta("enable_zoom",revision in ["v004","v005","v006","v007"])
	root.add_child(scene)
	var names := {"floor":"地板", "wall":"墙体", "water":"水面", "bank":"岸沿", "pipe":"管线", "rail":"栏杆", "bridge":"栈桥"}
	var preview_scale := 2 if revision in ["v004","v005","v006","v007"] else 1
	var preview_tile := 32 * preview_scale
	var preview := Image.create(640*preview_scale, 640*preview_scale, false, Image.FORMAT_RGBA8)
	preview.fill(Color("182631"))
	var report := {"engine": Engine.get_version_info().string, "patterns": {}, "checked_cells": 0, "failures": []}
	for index in range(catalog.atlases.size()):
		var atlas: Dictionary = catalog.atlases[index]
		var tile_set := _make_tileset(atlas)
		var path: String = output_dir + atlas.id + "_terrain_" + revision + ".tres"
		assert(ResourceSaver.save(tile_set, path) == OK)
		# 从磁盘重新读取，确保不是仅内存配置正确。
		tile_set = ResourceLoader.load(path, "TileSet", ResourceLoader.CACHE_MODE_IGNORE)
		report.patterns[atlas.id] = atlas.tiles.size()
		_test_patterns(tile_set, atlas)
		var layer := TileMapLayer.new()
		layer.name = str(atlas.id).to_pascal_case()
		layer.tile_set = tile_set
		# 贴图分辨率与逻辑格尺寸解耦。v004 保留 128px 美术，世界格仍为 32。
		layer.scale = Vector2.ONE * 32.0 / texture_tile_size
		# 水面与岸沿共用坐标，供分别挂水面 shader 与静态岸沿材质。
		var slot := index if index < 3 else index - 1
		if atlas.id == "bank": slot = 2
		var offset := Vector2i(16 + (slot % 2) * 320, 40 + (slot / 2) * 208)
		layer.position = offset
		scene.add_child(layer)
		layer.owner = scene
		var cells: Array[Vector2i] = []
		var rows := ["11111111", "11011001", "11111001", "00101111", "11101001"]
		if atlas.mode == "sides" and atlas.id != "floor":
			rows = ["11111111", "10001000", "11111101", "00100101", "11100111"]
		for y in range(rows.size()):
			for x in range(rows[y].length()):
				if rows[y][x] == "1": cells.append(Vector2i(x,y))
		layer.set_cells_terrain_connect(cells, 0, 0, false)
		_check(layer, cells, atlas.mode)
		var src := tile_set.get_source(0) as TileSetAtlasSource
		var pixels := src.texture.get_image()
		for cell in layer.get_used_cells():
			# 先裁单块再缩放。整张 atlas 缩放会跨边采到相邻图块，制造假裂缝。
			var tile_pixels := pixels.get_region(Rect2i(layer.get_cell_atlas_coords(cell)*texture_tile_size,Vector2i(texture_tile_size,texture_tile_size)))
			if texture_tile_size != preview_tile:
				tile_pixels.resize(preview_tile,preview_tile,Image.INTERPOLATE_LANCZOS)
			preview.blend_rect(tile_pixels,Rect2i(0,0,preview_tile,preview_tile),offset*preview_scale+cell*preview_tile)
		if atlas.id != "bank":
			var label := Label.new()
			label.text = str(names[atlas.id]) + " · Terrain 自动连接"
			label.position = Vector2(offset) - Vector2(0,26)
			scene.add_child(label)
			label.owner = scene
	var packed := PackedScene.new()
	assert(packed.pack(scene) == OK)
	# 常规重建不覆盖用户已绘制的沙盒；显式传 --rebuild-demo 才重建。
	if not FileAccess.file_exists(scene_path) or "--rebuild-demo" in OS.get_cmdline_user_args():
		assert(ResourceSaver.save(packed, scene_path) == OK)
	preview.save_png(output_dir + "layout_preview.png")
	report.checked_cells = checked
	report.failures = failures
	var output := FileAccess.open(output_dir + "validation.json", FileAccess.WRITE)
	output.store_string(JSON.stringify(report,"\t") + "\n")
	print(JSON.stringify(report))
	scene.queue_free()
	quit(0 if failures.is_empty() else 1)

func _make_tileset(atlas: Dictionary) -> TileSet:
	var result := TileSet.new()
	result.tile_size = Vector2i(texture_tile_size,texture_tile_size)
	result.add_terrain_set()
	result.set_terrain_set_mode(0, TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES if atlas.mode == "blob" else TileSet.TERRAIN_MODE_MATCH_SIDES)
	result.add_terrain(0)
	result.set_terrain_name(0,0,str(atlas.id).capitalize())
	result.set_terrain_color(0,0,Color("51c5c2"))
	var source := TileSetAtlasSource.new()
	source.texture = load(atlas.texture)
	source.texture_region_size = Vector2i(texture_tile_size,texture_tile_size)
	# 引擎采样独立扩展每块边缘，避免 atlas 相邻块串色。
	source.use_texture_padding = true
	result.add_source(source,0)
	for entry in atlas.tiles:
		var coord := Vector2i(entry.coord[0],entry.coord[1])
		source.create_tile(coord)
		var data := source.get_tile_data(coord,0)
		data.terrain_set = 0
		data.terrain = 0
		var step := 1 if atlas.mode == "blob" else 2
		for bit in range(0,8,step):
			var active: bool = int(entry.mask) & (1 << (bit / step)) != 0
			data.set_terrain_peering_bit(BITS[bit],0 if active else -1)
	return result

func _test_patterns(tile_set: TileSet, atlas: Dictionary) -> void:
	var layer := TileMapLayer.new()
	layer.tile_set = tile_set
	root.add_child(layer)
	# 穷举中心格全部 256 种邻域；四邻接系列穷举 16 种。
	var total := 256 if atlas.mode == "blob" else 16
	var step := 1 if atlas.mode == "blob" else 2
	for mask in range(total):
		layer.clear()
		var cells: Array[Vector2i] = [Vector2i.ZERO]
		for bit in range(0,8,step):
			if mask & (1 << (bit / step)):
				cells.append(DIRECTIONS[bit])
		layer.set_cells_terrain_connect(cells,0,0,false)
		_check(layer,cells,atlas.mode)
	# 固定种子随机区域，覆盖多个凹洞、孤立点、窄连接；测试结果可复现。
	var rng := RandomNumberGenerator.new()
	rng.seed = 20261004
	for trial in range(32):
		layer.clear()
		var cells: Array[Vector2i] = []
		for y in range(10):
			for x in range(10):
				if rng.randf() < 0.6: cells.append(Vector2i(x,y))
		layer.set_cells_terrain_connect(cells,0,0,false)
		_check(layer,cells,atlas.mode)
		# 模拟擦除半数格子后批量重建，检查端头是否正确收口。
		cells.resize(cells.size()/2)
		layer.clear()
		layer.set_cells_terrain_connect(cells,0,0,false)
		_check(layer,cells,atlas.mode)
	layer.free()

func _check(layer: TileMapLayer, cells: Array[Vector2i], mode: String) -> void:
	var occupied := {}
	for cell in cells: occupied[cell] = true
	if layer.get_used_cells().size() != cells.size():
		failures.append(str(layer.name) + ": cell count mismatch")
	for cell in cells:
		var data := layer.get_cell_tile_data(cell)
		if data == null:
			failures.append("Missing tile: " + str(cell))
			continue
		checked += 1
		for bit in range(0,8,1 if mode == "blob" else 2):
			var connected := occupied.has(cell + DIRECTIONS[bit])
			if bit % 2 == 1:
				connected = connected and occupied.has(cell+DIRECTIONS[(bit+7)%8]) and occupied.has(cell+DIRECTIONS[(bit+1)%8])
			if data.get_terrain_peering_bit(BITS[bit]) != (0 if connected else -1):
				if failures.size() < 20: failures.append(str(layer.name)+": wrong connection at "+str(cell)+" bit "+str(bit))
