extends RefCounted
## 位序与官方模板一致；对角只在它两侧正交均存在时有效。

const TILE_SIZE := 128
const LOGICAL_SIZE := 32
const DIRECTIONS := [Vector2i.UP,Vector2i(1,-1),Vector2i.RIGHT,Vector2i(1,1),Vector2i.DOWN,Vector2i(-1,1),Vector2i.LEFT,Vector2i(-1,-1)]
const PEERING := [TileSet.CELL_NEIGHBOR_TOP_SIDE,TileSet.CELL_NEIGHBOR_TOP_RIGHT_CORNER,TileSet.CELL_NEIGHBOR_RIGHT_SIDE,TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER,TileSet.CELL_NEIGHBOR_BOTTOM_SIDE,TileSet.CELL_NEIGHBOR_BOTTOM_LEFT_CORNER,TileSet.CELL_NEIGHBOR_LEFT_SIDE,TileSet.CELL_NEIGHBOR_TOP_LEFT_CORNER]

static func read_catalog() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string("res://inputs/catalog.json"))

static func make_tileset(atlas: Dictionary) -> TileSet:
	var result := TileSet.new()
	result.tile_size = Vector2i(TILE_SIZE,TILE_SIZE)
	result.add_terrain_set()
	result.set_terrain_set_mode(0,TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES)
	result.add_terrain(0)
	result.set_terrain_name(0,0,"Floor")
	result.set_terrain_color(0,0,Color("51c5c2"))
	result.add_custom_data_layer()
	result.set_custom_data_layer_name(0,"blob_mask")
	result.set_custom_data_layer_type(0,TYPE_INT)
	var source := TileSetAtlasSource.new()
	source.texture = load("res://inputs/"+str(atlas.texture))
	source.texture_region_size = Vector2i(TILE_SIZE,TILE_SIZE)
	# 每个完整图块独立扩展采样，防止图集邻格串色。
	source.use_texture_padding = true
	result.add_source(source,0)
	for entry in atlas.tiles:
		var coord := Vector2i(int(entry.coord[0]),int(entry.coord[1]))
		source.create_tile(coord)
		var tile := source.get_tile_data(coord,0)
		tile.terrain_set = 0
		tile.terrain = 0
		tile.set_custom_data("blob_mask",int(entry.mask))
		for bit in range(8):
			tile.set_terrain_peering_bit(PEERING[bit],0 if int(entry.mask)&(1<<bit) else -1)
	return result

static func expected_mask(occupied: Dictionary, cell: Vector2i) -> int:
	var mask := 0
	for bit in range(8):
		var active := occupied.has(cell+DIRECTIONS[bit])
		if bit%2 == 1:
			active = active and occupied.has(cell+DIRECTIONS[(bit+7)%8]) and occupied.has(cell+DIRECTIONS[(bit+1)%8])
		if active: mask |= 1<<bit
	return mask

static func rebuild(layer: TileMapLayer, occupied: Dictionary) -> void:
	var cells: Array[Vector2i] = []
	for cell in occupied: cells.append(cell)
	# 重建当前占用表，可以同时处理画入与擦除后的边角收口。
	layer.clear()
	if not cells.is_empty(): layer.set_cells_terrain_connect(cells,0,0,false)
	layer.update_internals()

static func initial_cells() -> Dictionary:
	var occupied := {}
	# 六类视觉样例：中心、长北边、L、完整内洞、窄条、可擦除收口。
	for y in range(1,6):
		for x in range(1,8): occupied[Vector2i(x,y)] = true
	for y in range(1,7):
		for x in range(10,18):
			if not (x in range(12,15) and y in range(3,5)): occupied[Vector2i(x,y)] = true
	for y in range(8,13): occupied[Vector2i(2,y)] = true
	for x in range(2,8): occupied[Vector2i(x,12)] = true
	for x in range(10,18): occupied[Vector2i(x,9)] = true
	for x in range(10,15):
		for y in range(11,13): occupied[Vector2i(x,y)] = true
	occupied[Vector2i(15,12)] = true
	occupied[Vector2i(16,12)] = true
	return occupied
