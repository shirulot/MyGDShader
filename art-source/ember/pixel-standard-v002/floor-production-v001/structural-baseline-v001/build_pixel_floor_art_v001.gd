extends SceneTree
## 32px 原生地板生产器：可重复的像素绘制规则，不修改任何既有 PNG。
## 正式轮廓由 47 / 16 邻接清单决定，材质和固定光照共用一套规则。
## 运行：godot --headless --path . -s res://tools/build_pixel_floor_art_v001.gd

const TILE := 32
const OUT := "res://assets/ember/environment/pixel_floor_v001/"
const REVIEW := "res://art-source/ember/pixel-standard-v002/floor-production-v001/"
const SPEC := "res://docs/shader-learning/autotile-neighborhoods-v002.json"
const AREA_DIRS := [Vector2i(0,-1), Vector2i(1,-1), Vector2i(1,0), Vector2i(1,1), Vector2i(0,1), Vector2i(-1,1), Vector2i(-1,0), Vector2i(-1,-1)]
const SIDE_DIRS := [Vector2i(0,-1), Vector2i(1,0), Vector2i(0,1), Vector2i(-1,0)]
const LAYER_IDS := ["floor", "rim", "grate", "seam", "bridge"]
const CLEAR := Color(0,0,0,0)

var _tiles: Dictionary = {}
var _area_tiles: Array = []
var _network_tiles: Array = []
var _errors: Array[String] = []
var _pixels_checked := 0
var _band_pixels_checked := 0
var _ports_checked := 0
var _landing_checked := 0
var _landing_entries: Array = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(REVIEW))
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SPEC))
	_area_tiles = spec.area.tiles
	_network_tiles = spec.network.tiles
	var catalog := {"revision":"pixel_floor_v001", "status":"PIXEL_FINISHED", "tile_size":TILE,
		"world_cell_size":[32,32], "layer_scale":[1,1], "atlases":[],
		"source_preview":"res://art-source/ember/pixel-standard-v002/previews/scene_preview_v001.png",
		"material_reference": REVIEW + "floor_material_master_v001.png",
		"construction":"Godot 原生 Image；确定性邻域几何、固定左上光照、共享周期材质；参考母稿没有缩小/裁切进入 atlas。"}
	for layer_id in LAYER_IDS:
		var area_mode: bool = layer_id in ["floor","rim","grate"]
		var entries: Array = _area_tiles if area_mode else _network_tiles
		var atlas := Image.create(256, 192 if area_mode else 64, false, Image.FORMAT_RGBA8)
		atlas.fill(CLEAR)
		var registration: Array = []
		_tiles[layer_id] = {}
		for entry: Dictionary in entries:
			var mask := int(entry.mask)
			var coord := Vector2i(int(entry.atlas_coord[0]), int(entry.atlas_coord[1]))
			var tile := _render_tile(layer_id, mask)
			_tiles[layer_id][mask] = tile
			atlas.blit_rect(tile, Rect2i(0,0,TILE,TILE), coord * TILE)
			registration.append({"mask":mask, "coord":[coord.x,coord.y]})
		var path: String = OUT + layer_id + "_atlas_v001.png"
		assert(atlas.save_png(path) == OK)
		var enlarged := atlas.duplicate() as Image
		enlarged.resize(atlas.get_width()*4, atlas.get_height()*4, Image.INTERPOLATE_NEAREST)
		assert(enlarged.save_png(REVIEW + layer_id + "_atlas_review_4x_v001.png") == OK)
		catalog.atlases.append({"id":layer_id, "mode":"blob" if area_mode else "sides", "texture":path,
			"tiles":registration, "description":_layer_description(layer_id)})
	_build_landings(catalog)
	_validate_alpha_and_shape()
	_validate_interfaces()
	_validate_material_period()
	_validate_landings()
	_write_json(OUT + "catalog.json", catalog)
	var validation := {"status":"CONNECTIVITY_PASS" if _errors.is_empty() else "FAIL",
		"engine":Engine.get_version_info().string, "tile_size":32,
		"atlas_counts":{"floor":47,"rim":47,"grate":47,"seam":16,"bridge":16,"floor_landing":89,"rim_landing":89},
		"checked_pixels":_pixels_checked, "checked_adjacent_band_pixels":_band_pixels_checked,
		"checked_ports":_ports_checked, "band_width_pixels":4,
		"checked_landing_pixels":_landing_checked,
		"checks":["所有 173 块二值 alpha 与形状", "47型末槽透明", "floor 满格实体", "rim mask255真实透明且注册", "bridge 24px端口及2px边梁", "16型主体 flood-fill连通", "实际 4×3 / 3×4 邻域的接口及两侧4px连续带", "格栅和桥面共享4px世界相位", "低对比板材32px周期"],
		"validation_method":"穷举相邻两格周围10格的1024种布局；相邻带与同一完整世界邻域的独立几何取样一致。不是只比较边缘一排，也不以强制复制边缘过关。",
		"material_geometry":{"floor_cut_px":2,"rim_cap_px":4,"rim_south_total_px":7,"rim_east_total_px":6,"grate_period_px":4,"seam_width_px":1,"bridge_width_px":24,"bridge_side_rail_px":2,"landing_shoulder_px":4,"landing_grate_tongue_px":4},
		"errors":_errors}
	_write_json(OUT + "pixel_validation.json", validation)
	_write_reviews()
	print(JSON.stringify(validation,"\t"))
	quit(0 if _errors.is_empty() else 1)


func _build_landings(catalog: Dictionary) -> void:
	# Floor与桥脚印是不同的占用语义：不能把24px桥错误提升为整格邻接。
	# 非零bridge_ports仅允许出现在floor_mask原本没有的四条正交边。
	for entry: Dictionary in _area_tiles:
		var floor_mask := int(entry.mask)
		var missing_ports := 0
		for side in range(4):
			if (floor_mask & (1 << (side*2))) == 0: missing_ports |= 1 << side
		for ports in range(1,16):
			if (ports & ~missing_ports) != 0: continue
			var index := _landing_entries.size()
			_landing_entries.append({"floor_mask":floor_mask,"bridge_ports":ports,"coord":[index%8,index/8]})
	assert(_landing_entries.size() == 89)
	for layer_id in ["floor_landing","rim_landing"]:
		_tiles[layer_id] = {}
		var atlas := Image.create(256,384,false,Image.FORMAT_RGBA8)
		atlas.fill(CLEAR)
		for entry: Dictionary in _landing_entries:
			var floor_mask := int(entry.floor_mask)
			var ports := int(entry.bridge_ports)
			var image := Image.create(32,32,false,Image.FORMAT_RGBA8)
			for y in range(32):
				for x in range(32):
					var p := Vector2i(x,y)
					image.set_pixelv(p,_landing_color(layer_id,p,floor_mask,ports))
			var key := "%d:%d" % [floor_mask,ports]
			_tiles[layer_id][key] = image
			var coord := Vector2i(int(entry.coord[0]),int(entry.coord[1]))
			atlas.blit_rect(image,Rect2i(0,0,32,32),coord*32)
		var path: String = OUT+layer_id+"_atlas_v001.png"
		assert(atlas.save_png(path) == OK)
		atlas.resize(1024,1536,Image.INTERPOLATE_NEAREST)
		assert(atlas.save_png(REVIEW+layer_id+"_atlas_review_4x_v001.png") == OK)
		catalog.atlases.append({"id":layer_id,"mode":"context","texture":path,"tiles":_landing_entries,
			"description":"89个合法非零桥口上下文普通图块，不参与Terrain随机选块；ports0复用base47。4px格栅短踏板、24px无rim通道、两侧4px肩口。",
			"geometry":{"bridge_port_interval":[4,28],"shoulder_px":4,"grate_tongue_depth_px":4,"corridor":"按桥24px占用集合从rim扣除，覆盖孤岛对向口/L/T/X中心；floor始终满格实体"}})


func _landing_boundary(p: Vector2i,mask: int,ports: int) -> Vector3:
	var nearest := Vector3(99,0,0)
	for i in range(8):
		if (mask & (1 << i)) != 0: continue
		var origin: Vector2i = AREA_DIRS[i]*32
		var rectangles: Array[Rect2i] = [Rect2i(origin,Vector2i(32,32))]
		if i % 2 == 0 and (ports & (1 << (i/2))) != 0:
			# 桥的中央24px已实体连通，空地只剩两侧4px肩部。
			if i in [0,4]:
				rectangles = [Rect2i(origin,Vector2i(4,32)),Rect2i(origin+Vector2i(28,0),Vector2i(4,32))]
			else:
				rectangles = [Rect2i(origin,Vector2i(32,4)),Rect2i(origin+Vector2i(0,28),Vector2i(32,4))]
		for rect: Rect2i in rectangles:
			var q := Vector2i(clampi(p.x,rect.position.x,rect.end.x-1),clampi(p.y,rect.position.y,rect.end.y-1))
			nearest = _pick_boundary(nearest,Vector2(q-p))
	return nearest


func _landing_color(layer_id: String,p: Vector2i,floor_mask: int,ports: int) -> Color:
	var corridor := _bridge_on(p,ports)
	if layer_id == "rim_landing":
		# 不止擦去最外一排：24px通道一直开放到中心，孤岛对向口也不被闭岸夹窄。
		if corridor: return CLEAR
		return _area_color("rim",p,_landing_boundary(p,floor_mask,ports))
	if corridor:
		# 四向桥口都有4px短踏板，在共享接口保持桥格栅、梁宽和世界相位。
		if ((ports & 1) != 0 and p.y < 4) or ((ports & 2) != 0 and p.x >= 28) or ((ports & 4) != 0 and p.y >= 28) or ((ports & 8) != 0 and p.x < 4):
			return _bridge_color(p,ports)
		return _plate_color(p)
	return _area_color("floor",p,_landing_boundary(p,floor_mask,ports))


func _layer_description(layer_id: String) -> String:
	match layer_id:
		"floor": return "连续蓝灰涂装钢；仅周界2px面板切边；无逐格亮框、铆钉或烘焙油渍。"
		"rim": return "独立可选结构收边：约4px浅压顶，南向3px/东向2px暗立面；全在所属格内。mask255透明。"
		"grate": return "检修区透明功能覆盖层；4px共享条距；只在外露周界收边。"
		"seam": return "独立1px低对比板缝网络，16型自动接续；不每格强制围框。"
		"bridge": return "24px宽格栅桥面；两侧2px边梁；交汇按统一占用轮廓重画，不叠封口梁。深色孔底与桥面同为实体。"
	return ""


func _render_tile(layer_id: String, mask: int) -> Image:
	var image := Image.create(TILE,TILE,false,Image.FORMAT_RGBA8)
	image.fill(CLEAR)
	for y in range(TILE):
		for x in range(TILE):
			var p := Vector2i(x,y)
			var color := CLEAR
			if layer_id in ["floor","rim","grate"]:
				var nearest := _area_boundary(p,mask)
				color = _area_color(layer_id,p,nearest)
			elif layer_id == "seam":
				color = _seam_color(p,mask)
			elif layer_id == "bridge":
				color = _bridge_color(p,mask)
			image.set_pixel(x,y,color)
	return image


func _area_boundary(p: Vector2i, mask: int) -> Vector3:
	# 寻找最近的空地像素；凹角来自真正缺失的对角格，不能用两条直边覆盖。
	var nearest := Vector3(99,0,0)
	for i in range(AREA_DIRS.size()):
		if (mask & (1 << i)) != 0:
			continue
		var origin: Vector2i = AREA_DIRS[i] * TILE
		var external := Vector2i(clampi(p.x,origin.x,origin.x+31),clampi(p.y,origin.y,origin.y+31))
		nearest = _pick_boundary(nearest,Vector2(external-p))
	return nearest


func _pick_boundary(current: Vector3, delta: Vector2) -> Vector3:
	var distance := delta.length()
	var candidate := Vector3(distance,delta.x,delta.y)
	if distance < current.x - 0.001 or (is_equal_approx(distance,current.x) and _light_rank(candidate) < _light_rank(current)):
		return candidate
	return current


func _direction(nearest: Vector3) -> int:
	# 法线定向光照：上/左亮、下/右暗；不旋转已经上色的最终图块。
	if absf(nearest.z) >= absf(nearest.y):
		return 0 if nearest.z < 0 else 2
	return 3 if nearest.y < 0 else 1


func _light_rank(nearest: Vector3) -> int:
	return [0,2,3,1][_direction(nearest)]


func _area_color(layer_id: String,p: Vector2i,nearest: Vector3) -> Color:
	var distance := nearest.x
	var side := _direction(nearest)
	if layer_id == "floor":
		if distance <= 1.01:
			return Color("405764")
		if distance <= 2.01:
			return Color("58707A") if side in [0,3] else Color("455D68")
		return _plate_color(p)
	if layer_id == "rim":
		# 与 floor 的2px切边分离；这是可选择的码头结构压顶/立面。
		var band := int(ceil(distance))
		var ramps := [
			["8FA3A4","B5C0B8","AAB8B1","687F85"],
			["223542","304754","6A8086","98A69F","98A69F","60757D"],
			["182631","293E4A","354F5E","6D8287","A7B3AC","A7B3AC","627981"],
			["70898E","A5B2AC","A5B2AC","667C83"]]
		if band < 1 or band > ramps[side].size():
			return CLEAR
		return Color(ramps[side][band-1])
	if layer_id == "grate":
		if distance <= 1.01:
			return Color("344B58")
		if distance <= 2.01:
			return Color("748C93") if side in [0,3] else Color("4C6673")
		# 条距4px，周期恰好整除32；孔隙真实透明，可叠到基础地板。
		var xphase := posmod(p.x,4)
		var yphase := posmod(p.y,4)
		if xphase == 0 and yphase == 0:
			return Color("789096")
		if xphase == 0 or yphase == 0:
			return Color("607985")
		if (xphase == 1 and yphase > 0) or (yphase == 1 and xphase > 0):
			return Color("354D5B")
	return CLEAR


func _plate_color(p: Vector2i) -> Color:
	# 母稿启发的成簇色阶：只有1~3 RGB阶差，不把随机污点固定在每格。
	# 四周4px保持中性色，周期无明暗斜坡；这些簇不是逐格独立的噪声。
	var x := posmod(p.x,TILE)
	var y := posmod(p.y,TILE)
	if x < 4 or x >= 28 or y < 4 or y >= 28:
		return Color("4D6470")
	var cell_x := int(x/3)
	var cell_y := int(y/2)
	var hash_value := posmod(cell_x*17 + cell_y*13 + cell_x*cell_y*7,23)
	if hash_value < 3:
		return Color("4B626E")
	if hash_value > 19:
		return Color("506773")
	if (x >= 9 and x <= 14 and y >= 8 and y <= 10) or (x >= 20 and x <= 24 and y >= 23 and y <= 24):
		return Color("4C636F")
	return Color("4D6470")


func _seam_on(p: Vector2i,mask: int) -> bool:
	if p == Vector2i(16,16):
		return true
	return (p.x == 16 and ((p.y < 16 and (mask & 1) != 0) or (p.y > 16 and (mask & 4) != 0))) or (p.y == 16 and ((p.x > 16 and (mask & 2) != 0) or (p.x < 16 and (mask & 8) != 0)))


func _seam_color(p: Vector2i,mask: int) -> Color:
	return Color("405762") if _seam_on(p,mask) else CLEAR


func _bridge_on(p: Vector2i,mask: int) -> bool:
	if p.x >= 4 and p.x < 28 and p.y >= 4 and p.y < 28:
		return true
	return (p.x >= 4 and p.x < 28 and ((p.y < 4 and (mask & 1) != 0) or (p.y >= 28 and (mask & 4) != 0))) or (p.y >= 4 and p.y < 28 and ((p.x >= 28 and (mask & 2) != 0) or (p.x < 4 and (mask & 8) != 0)))


func _bridge_boundary(p: Vector2i,mask: int) -> Vector3:
	var nearest := Vector3(99,0,0)
	# 开放端沿同宽截面延伸至少4px；实体内部交汇按一次周界求解。
	for dy in range(-2,3):
		for dx in range(-2,3):
			var q := p + Vector2i(dx,dy)
			var inside := _bridge_on(q,mask)
			if q.y < 0: inside = (mask & 1) != 0 and q.x >= 4 and q.x < 28
			if q.x >= TILE: inside = (mask & 2) != 0 and q.y >= 4 and q.y < 28
			if q.y >= TILE: inside = (mask & 4) != 0 and q.x >= 4 and q.x < 28
			if q.x < 0: inside = (mask & 8) != 0 and q.y >= 4 and q.y < 28
			if not inside:
				nearest = _pick_boundary(nearest,Vector2(dx,dy))
	return nearest


func _bridge_color(p: Vector2i,mask: int) -> Color:
	if not _bridge_on(p,mask):
		return CLEAR
	var nearest := _bridge_boundary(p,mask)
	if nearest.x <= 1.01:
		return Color("93A49F") if _direction(nearest) in [0,3] else Color("304753")
	if nearest.x <= 2.01:
		return Color("6C858C") if _direction(nearest) in [0,3] else Color("566E79")
	var xphase := posmod(p.x,4)
	var yphase := posmod(p.y,4)
	if xphase == 0 and yphase == 0: return Color("81989E")
	if xphase == 0 or yphase == 0: return Color("6B848E")
	if xphase == 1 or yphase == 1: return Color("344B59")
	return Color("243B49")


func _validate_alpha_and_shape() -> void:
	for layer_id in LAYER_IDS:
		for mask in _tiles[layer_id]:
			var image: Image = _tiles[layer_id][mask]
			var opaque := 0
			for y in range(TILE):
				for x in range(TILE):
					var alpha := image.get_pixel(x,y).a8
					_pixels_checked += 1
					if alpha != 0 and alpha != 255:
						_fail("非二值Alpha: %s mask%d %d,%d" % [layer_id,mask,x,y])
					if alpha == 255: opaque += 1
					if layer_id == "bridge" and (alpha == 255) != _bridge_on(Vector2i(x,y),mask):
						_fail("bridge实体形状不符")
					if layer_id == "seam" and (alpha == 255) != _seam_on(Vector2i(x,y),mask):
						_fail("seam形状不符")
			if layer_id == "floor" and opaque != 1024:
				_fail("floor非满格实体")
			if layer_id == "rim" and mask == 255 and opaque != 0:
				_fail("rim内部255不是透明")
			if layer_id in ["bridge","seam"]:
				_validate_connected(layer_id,mask,image,opaque)
				_validate_ports(layer_id,mask,image)
	# 正式atlas每个面积图的第48槽必须保持透明，未注册。
	for layer_id in ["floor","rim","grate"]:
		var atlas := Image.load_from_file(ProjectSettings.globalize_path(OUT + layer_id + "_atlas_v001.png"))
		var spare := atlas.get_region(Rect2i(224,160,32,32))
		for y in range(32):
			for x in range(32):
				if spare.get_pixel(x,y).a8 != 0: _fail("末槽非透明")


func _validate_connected(layer_id: String,mask: int,image: Image,opaque_count: int) -> void:
	var seen := {Vector2i(16,16):true}
	var queue: Array[Vector2i] = [Vector2i(16,16)]
	var head := 0
	while head < queue.size():
		var p := queue[head]
		head += 1
		for direction: Vector2i in SIDE_DIRS:
			var q := p+direction
			if q.x < 0 or q.x >= 32 or q.y < 0 or q.y >= 32 or seen.has(q): continue
			if image.get_pixelv(q).a8 == 255:
				seen[q] = true
				queue.append(q)
	if seen.size() != opaque_count:
		_fail("主体不连通：%s mask%d %d/%d" % [layer_id,mask,seen.size(),opaque_count])


func _validate_ports(layer_id: String,mask: int,image: Image) -> void:
	for side in range(4):
		for offset in range(32):
			var p := _port_pixel(side,offset,0)
			var expected: bool = (mask & (1 << side)) != 0 and ((offset >= 4 and offset < 28) if layer_id == "bridge" else offset == 16)
			_ports_checked += 1
			if (image.get_pixelv(p).a8 == 255) != expected:
				_fail("端口未贯通或封端：%s mask%d side%d" % [layer_id,mask,side])


func _port_pixel(side: int,offset: int,depth: int) -> Vector2i:
	match side:
		0: return Vector2i(offset,depth)
		1: return Vector2i(31-depth,offset)
		2: return Vector2i(offset,31-depth)
	return Vector2i(depth,offset)


func _mask_at(cells: Dictionary,cell: Vector2i,area_mode: bool) -> int:
	var dirs: Array = AREA_DIRS if area_mode else SIDE_DIRS
	var mask := 0
	for i in range(dirs.size()):
		if cells.has(cell+dirs[i]): mask |= 1 << i
	if area_mode:
		for triplet in [[1,0,2],[3,2,4],[5,4,6],[7,6,0]]:
			if (mask & (1 << triplet[1])) == 0 or (mask & (1 << triplet[2])) == 0:
				mask &= ~(1 << triplet[0])
	return mask


func _world_area_boundary(p: Vector2i,cells: Dictionary,cell: Vector2i) -> Vector3:
	# 独立世界几何采样：直接访问完整布局，不读取tile mask或atlas。
	var nearest := Vector3(99,0,0)
	for dy in range(-1,2):
		for dx in range(-1,2):
			var neighbor := cell + Vector2i(dx,dy)
			if cells.has(neighbor): continue
			var origin := neighbor*TILE
			var q := Vector2i(clampi(p.x,origin.x,origin.x+31),clampi(p.y,origin.y,origin.y+31))
			nearest = _pick_boundary(nearest,Vector2(q-p))
	return nearest


func _validate_interfaces() -> void:
	# 相邻两中心固定存在，周围10格穷举1024种，水平/垂直各一次。
	for axis in [Vector2i(1,0),Vector2i(0,1)]:
		var around: Array[Vector2i] = []
		var extent := Vector2i(4,3) if axis.x == 1 else Vector2i(3,4)
		for y in range(-1,extent.y-1):
			for x in range(-1,extent.x-1):
				var q := Vector2i(x,y)
				if q != Vector2i.ZERO and q != axis: around.append(q)
		for pattern in range(1024):
			var cells := {Vector2i.ZERO:true,axis:true}
			for i in range(10):
				if (pattern & (1 << i)) != 0: cells[around[i]] = true
			for cell: Vector2i in [Vector2i.ZERO,axis]:
				var mask := _mask_at(cells,cell,true)
				var side := (1 if cell == Vector2i.ZERO else 3) if axis.x == 1 else (2 if cell == Vector2i.ZERO else 0)
				for offset in range(32):
					for depth in range(4):
						var local := _port_pixel(side,offset,depth)
						var world := cell*TILE+local
						var nearest := _world_area_boundary(world,cells,cell)
						for layer_id in ["floor","rim","grate"]:
							var actual: Color = _tiles[layer_id][mask].get_pixelv(local)
							var expected := _area_color(layer_id,world,nearest)
							_band_pixels_checked += 1
							if actual.to_rgba32() != expected.to_rgba32():
								_fail("4px邻域带不连续: %s mask%d cell%s local%s pattern%d" % [layer_id,mask,cell,local,pattern])
	# 网络同宽开放端两侧4px带完全匹配，格栅按全局周期延续。
	for layer_id in ["seam","bridge"]:
		for side in range(4):
			for mask in range(16):
				if (mask & (1 << side)) == 0: continue
				var opposite := (side+2)%4
				for other in range(16):
					if (other & (1 << opposite)) == 0: continue
					for offset in range(32):
						for depth in range(4):
							var a := _port_pixel(side,offset,depth)
							var b := _port_pixel(opposite,offset,depth)
							var ca: Color = _tiles[layer_id][mask].get_pixelv(a)
							var cb: Color = _tiles[layer_id][other].get_pixelv(b)
							_band_pixels_checked += 1
							# 形状/边梁对称；mesh色在延续的世界相位独立验证。
							if ca.a8 != cb.a8: _fail("网络4px连接带Alpha不匹配")
							if layer_id == "seam" and ca.to_rgba32() != cb.to_rgba32(): _fail("板缝4px带颜色不匹配")
							if layer_id == "bridge" and ca.a8 == 255:
								var boundary := _bridge_boundary(a,mask)
								if boundary.x <= 2.01 and ca.to_rgba32() != cb.to_rgba32(): _fail("桥边梁4px截面不匹配")


func _validate_material_period() -> void:
	for y in range(32):
		for x in range(32):
			var p := Vector2i(x,y)
			if _plate_color(p) != _plate_color(p+Vector2i(32,32)): _fail("板材周期失败")
			for shift in [Vector2i(32,0),Vector2i(0,32)]:
				if _area_color("grate",p,Vector3(99,0,0)) != _area_color("grate",p+shift,Vector3(99,0,0)):
					_fail("格栅世界相位失败")


func _validate_landings() -> void:
	for entry: Dictionary in _landing_entries:
		var floor_mask := int(entry.floor_mask)
		var ports := int(entry.bridge_ports)
		var key := "%d:%d" % [floor_mask,ports]
		var floor_image: Image = _tiles.floor_landing[key]
		var rim_image: Image = _tiles.rim_landing[key]
		for y in range(32):
			for x in range(32):
				_landing_checked += 2
				if floor_image.get_pixel(x,y).a8 != 255: _fail("landing地板非满格实体")
				if rim_image.get_pixel(x,y).a8 not in [0,255]: _fail("landing rim非二值alpha")
				if x >= 4 and x < 28 and y >= 4 and y < 28 and rim_image.get_pixel(x,y).a8 != 0:
					_fail("landing中心24×24未完整开放")
		for side in range(4):
			if (ports & (1 << side)) == 0: continue
			for offset in range(4,28):
				for depth in range(16):
					var p := _port_pixel(side,offset,depth)
					_landing_checked += 1
					if rim_image.get_pixelv(p).a8 != 0:
						_fail("landing24px通道到中心被岸体挡住")
				for depth in range(4):
					var p := _port_pixel(side,offset,depth)
					var color := floor_image.get_pixelv(p)
					# 所有可能的相邻桥16型都应拥有同一开口2px梁截面。
					for neighbor_mask in range(16):
						var opposite := (side+2)%4
						if (neighbor_mask & (1 << opposite)) == 0: continue
						var q := _port_pixel(opposite,offset,depth)
						var neighbor: Color = _tiles.bridge[neighbor_mask].get_pixelv(q)
						_landing_checked += 1
						if color.a8 != neighbor.a8: _fail("landing桥前后4pxAlpha截面不匹配")
						if offset in [4,5,26,27] and color.to_rgba32() != neighbor.to_rgba32():
							_fail("landing桥前后4px边梁色阶不匹配")
			# 两侧4px肩口还在收边；此检查抓住误把桥提升成32px邻居的旧方案。
			for offset in [0,1,2,3,28,29,30,31]:
				var p := _port_pixel(side,offset,0)
				_landing_checked += 1
				if rim_image.get_pixelv(p).a8 != 255: _fail("landing4px肩口消失")


func _write_reviews() -> void:
	# 一张原生尺寸实铺示意：区域外轮廓、洞、狭路、功能铺装和完整桥L/T/X。
	var floor_rows := ["00000000000000000000","01111000111111111110","01111000111111111110","01111000111001111110","01111000111001111110","00000000111111111110","00000000111111111110","00000000111110011110","00000000111110011110","00000000111110011110","00000000111111111110","00000000111111111110","00000000000000000000","00000000000000000000"]
	var floors := _cells_from_rows(floor_rows)
	var bridges := {}
	for x in range(5,8): bridges[Vector2i(x,3)] = true
	# 展示bridge四向连通，左右与floor开放落点。
	for x in range(2,7): bridges[Vector2i(x,9)] = true
	for y in range(7,12): bridges[Vector2i(4,y)] = true
	var grate := {}
	for y in range(2,4):
		for x in range(15,18): grate[Vector2i(x,y)] = true
	var seams := {}
	for y in range(2,12): seams[Vector2i(11,y)] = true
	for x in range(10,19): seams[Vector2i(x,6)] = true
	# 先裁占用再求邻接，避免孔洞的不可见笔迹误使可见板缝延伸进收边。
	for cell: Vector2i in seams.keys():
		if not floors.has(cell): seams.erase(cell)
	var image := Image.create(640,448,false,Image.FORMAT_RGBA8)
	image.fill(Color("183644"))
	for y in range(image.get_height()):
		for x in range(image.get_width()):
			# 低对比水面只为观察透明形状，非本次正式水资源。
			if posmod(x/3+y/2,47) < 2 and posmod(y,7) == 0: image.set_pixel(x,y,Color("204451"))
	for cell: Vector2i in floors:
		var mask := _mask_at(floors,cell,true)
		var ports := 0
		for side in range(4):
			if bridges.has(cell+SIDE_DIRS[side]) and not floors.has(cell+SIDE_DIRS[side]): ports |= 1 << side
		if ports != 0:
			var key := "%d:%d" % [mask,ports]
			image.blend_rect(_tiles.floor_landing[key],Rect2i(0,0,32,32),cell*32)
			image.blend_rect(_tiles.rim_landing[key],Rect2i(0,0,32,32),cell*32)
		else:
			image.blend_rect(_tiles.floor[mask],Rect2i(0,0,32,32),cell*32)
			image.blend_rect(_tiles.rim[mask],Rect2i(0,0,32,32),cell*32)
	for cell: Vector2i in bridges:
		var expanded := bridges.duplicate()
		for direction: Vector2i in SIDE_DIRS:
			if floors.has(cell+direction): expanded[cell+direction] = true
		image.blend_rect(_tiles.bridge[_mask_at(expanded,cell,false)],Rect2i(0,0,32,32),cell*32)
	for cell: Vector2i in grate:
		image.blend_rect(_tiles.grate[_mask_at(grate,cell,true)],Rect2i(0,0,32,32),cell*32)
	for cell: Vector2i in seams:
		if floors.has(cell): image.blend_rect(_tiles.seam[_mask_at(seams,cell,false)],Rect2i(0,0,32,32),cell*32)
	assert(image.save_png(REVIEW+"connected_floor_review_native_v001.png") == OK)
	image.resize(2560,1792,Image.INTERPOLATE_NEAREST)
	assert(image.save_png(REVIEW+"connected_floor_review_4x_v001.png") == OK)


func _cells_from_rows(rows: Array) -> Dictionary:
	var cells := {}
	for y in range(rows.size()):
		for x in range(rows[y].length()):
			if rows[y][x] == "1": cells[Vector2i(x,y)] = true
	return cells


func _write_json(path: String,data: Dictionary) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	assert(file != null)
	file.store_string(JSON.stringify(data,"\t"))


func _fail(message: String) -> void:
	# 重复症状保留前20条，不输出百万行像素日志。
	if _errors.size() < 20: _errors.append(message)
