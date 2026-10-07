@tool
extends RefCounted
## 原画像素编译器。Floor / Bridge 保存语义占用，边界由联合脚印自动派生。
## 输出可以切成普通 TileSetAtlasSource；跨材质上下文不参与 Terrain 随机选块。
## 128 texture pixels / 32 world pixels；只取 artist 像素，不程序生成材质。

const TILE := 128
const CAP := 32
const INSET := 48
const FACE_DEPTH := 128
const ASSET := "res://assets/ember/environment/reference_floor_v002/"
const DIRS := [Vector2i.UP,Vector2i(1,-1),Vector2i.RIGHT,Vector2i(1,1),Vector2i.DOWN,Vector2i(-1,1),Vector2i.LEFT,Vector2i(-1,-1)]
const CLEAR := Color(0,0,0,0)
var materials: Dictionary = {}
var corners: Dictionary = {}
var width := 0
var height := 0
var bounds := Rect2i()
var floor_cells: Dictionary = {}
var bridge_cells: Dictionary = {}
var coverage := PackedByteArray()
var floor_coverage := PackedByteArray()
var distance := PackedInt32Array()
var nearest_x := PackedInt32Array()
var nearest_y := PackedInt32Array()


func load_materials() -> void:
	# runtime 只依赖正式包中的模块，无需读取 approved 效果图或生成器原稿。
	for key in ["floor_albedo_period","north_cap_source","south_cap_source","east_cap_source","south_face_source","east_face_source","water_artist_period","bridge_horizontal_artist","bridge_vertical_artist","bridge_head_left_artist","bridge_head_right_artist","bridge_head_north_artist","bridge_head_south_artist","bridge_grate_period","bridge_beam_n","bridge_beam_s","bridge_beam_w","bridge_beam_e"]:
		var path: String = ASSET+key+"_v002.png"
		if FileAccess.file_exists(path): materials[key] = _read_png(path)
	for id in ["outer_nw","outer_ne","outer_sw","outer_se","inner_nw","inner_ne","inner_sw","inner_se"]:
		var path: String = ASSET+id+"_artist_v002.png"
		if FileAccess.file_exists(path): corners[id] = _read_png(path)


func _read_png(path: String) -> Image:
	var image := Image.new()
	assert(image.load_png_from_buffer(FileAccess.get_file_as_bytes(path)) == OK)
	return image


func mask_at(occupied: Dictionary,cell: Vector2i) -> int:
	var mask := 0
	for bit in range(8):
		if occupied.has(cell+DIRS[bit]): mask |= 1<<bit
	for bit in [1,3,5,7]:
		if (mask&(1<<((bit+7)%8))) == 0 or (mask&(1<<((bit+1)%8))) == 0: mask &= ~(1<<bit)
	return mask


func floor_inside(p: Vector2i,mask: int) -> bool:
	if (mask&1)==0 and (mask&64)==0 and p.x+p.y < CAP: return false
	if (mask&1)==0 and (mask&4)==0 and TILE-1-p.x+p.y < CAP: return false
	if (mask&16)==0 and (mask&4)==0 and TILE-1-p.x+TILE-1-p.y < CAP: return false
	if (mask&16)==0 and (mask&64)==0 and p.x+TILE-1-p.y < CAP: return false
	return true


func bridge_inside(p: Vector2i,cell: Vector2i,walkable: Dictionary) -> bool:
	# 默认二格宽；外露边每侧退 12world，保留 40world 可见桥面。
	# 一格窄支线采用每侧6world，保留20world，避免仅剩8world。
	var n := not walkable.has(cell+Vector2i.UP)
	var s := not walkable.has(cell+Vector2i.DOWN)
	var w := not walkable.has(cell+Vector2i.LEFT)
	var e := not walkable.has(cell+Vector2i.RIGHT)
	var iy := 24 if n and s else INSET
	var ix := 24 if w and e else INSET
	if n and p.y < iy: return false
	if s and p.y >= TILE-iy: return false
	if w and p.x < ix: return false
	if e and p.x >= TILE-ix: return false
	return true


func footprint_at(pixel: Vector2i) -> int:
	if pixel.x < 0 or pixel.y < 0 or pixel.x >= width or pixel.y >= height: return 0
	return coverage[pixel.y*width+pixel.x]


func build_visual_layers(floor_input: Dictionary,bridge_input: Dictionary,area: Rect2i) -> Dictionary:
	if materials.is_empty(): load_materials()
	bounds = area
	width = area.size.x*TILE
	height = area.size.y*TILE
	floor_cells = floor_input.duplicate()
	bridge_cells = bridge_input.duplicate()
	# Floor 优先；编辑器和保存文件中的重叠也先清除，再计算邻接。
	for cell: Vector2i in floor_cells: bridge_cells.erase(cell)
	_build_coverage()
	_build_distance()
	var images := {}
	for id in ["water","facade","floor","rim","bridge","heads"]:
		var image := Image.create(width,height,false,Image.FORMAT_RGBA8)
		image.fill(CLEAR)
		images[id] = image
	var water: Image = images.water
	var water_source: Image = materials.water_artist_period
	for y in range(height):
		for x in range(width): water.set_pixel(x,y,water_source.get_pixel(posmod(x+bounds.position.x*TILE,water_source.get_width()),posmod(y+bounds.position.y*TILE,water_source.get_height())))
	_draw_facades(images.facade)
	var albedo: Image = materials.floor_albedo_period
	for y in range(height):
		for x in range(width):
			var i := y*width+x
			if coverage[i] == 0: continue
			var world_pixel := Vector2i(x,y)+bounds.position*TILE
			if coverage[i] == 2:
				images.bridge.set_pixel(x,y,bridge_color(world_pixel,Vector2i(floori(float(world_pixel.x)/TILE),floori(float(world_pixel.y)/TILE))))
				continue
			images.floor.set_pixel(x,y,albedo.get_pixel(posmod(world_pixel.x,albedo.get_width()),posmod(world_pixel.y,albedo.get_height())))
			if distance[i] <= CAP:
				images.rim.set_pixel(x,y,_cap_color(world_pixel,x,y,i))
	_draw_heads(images.heads)
	var footprint := Image.create(width,height,false,Image.FORMAT_RGBA8)
	for y in range(height):
		for x in range(width):
			var v := coverage[y*width+x]
			footprint.set_pixel(x,y,Color(1.0 if v==1 else 0.0,1.0 if v==2 else 0.0,0.0,1.0 if v!=0 else 0.0))
	images["coverage"] = footprint
	images["pixel_origin"] = bounds.position*TILE
	return images


func _build_coverage() -> void:
	coverage.resize(width*height)
	floor_coverage.resize(width*height)
	coverage.fill(0)
	floor_coverage.fill(0)
	var walkable := floor_cells.duplicate()
	for cell: Vector2i in bridge_cells: walkable[cell] = true
	for cell: Vector2i in floor_cells:
		if not bounds.has_point(cell): continue
		var mask := mask_at(floor_cells,cell)
		var origin := (cell-bounds.position)*TILE
		for y in range(TILE):
			for x in range(TILE):
				if not floor_inside(Vector2i(x,y),mask): continue
				var at := (origin.y+y)*width+origin.x+x
				coverage[at] = 1
				floor_coverage[at] = 1
	for cell: Vector2i in bridge_cells:
		if not bounds.has_point(cell): continue
		var origin := (cell-bounds.position)*TILE
		for y in range(TILE):
			for x in range(TILE):
				if bridge_inside(Vector2i(x,y),cell,walkable): coverage[(origin.y+y)*width+origin.x+x] = 2


func _build_distance() -> void:
	distance.resize(width*height)
	nearest_x.resize(width*height)
	nearest_y.resize(width*height)
	for y in range(height):
		for x in range(width):
			var i := y*width+x
			distance[i] = 9999 if coverage[i]!=0 else 0
			nearest_x[i] = x
			nearest_y[i] = y
	for y in range(height):
		for x in range(width):
			var i := y*width+x
			if x>0: _relax(i,i-1)
			if y>0: _relax(i,i-width)
	for y in range(height-1,-1,-1):
		for x in range(width-1,-1,-1):
			var i := y*width+x
			if x+1<width: _relax(i,i+1)
			if y+1<height: _relax(i,i+width)


func _relax(i: int,j: int) -> void:
	if distance[j]+1 < distance[i]:
		distance[i] = distance[j]+1
		nearest_x[i] = nearest_x[j]
		nearest_y[i] = nearest_y[j]


func _draw_facades(image: Image) -> void:
	var south: Image = materials.south_face_source
	var east: Image = materials.east_face_source
	for y in range(height-1):
		for x in range(width-1):
			var i := y*width+x
			if floor_coverage[i] == 0: continue
			if coverage[i+width] == 0:
				for depth in range(FACE_DEPTH):
					if y+1+depth>=height: break
					if footprint_at(Vector2i(x,y+1+depth))!=0: continue
					image.set_pixel(x,y+1+depth,south.get_pixel(posmod(x+bounds.position.x*TILE,south.get_width()),depth))
			if coverage[i+1] == 0:
				for depth in range(east.get_width()):
					if x+1+depth>=width: break
					if footprint_at(Vector2i(x+1+depth,y))!=0: continue
					image.set_pixel(x+1+depth,y,east.get_pixel(depth,posmod(y+bounds.position.y*TILE,east.get_height())))


func _cap_color(world: Vector2i,x: int,y: int,i: int) -> Color:
	var dx := nearest_x[i]-x
	var dy := nearest_y[i]-y
	var depth := clampi(distance[i]-1,0,CAP-1)
	var image: Image
	var color: Color
	if abs(dx)>abs(dy):
		if dx>0:
			image = materials.east_cap_source
			color = image.get_pixel(CAP-1-depth,posmod(world.y,image.get_height()))
		else:
			image = materials.north_cap_source
			color = image.get_pixel(posmod(world.y,image.get_width()),depth)
	else:
		image = materials.south_cap_source if dy>0 else materials.north_cap_source
		color = image.get_pixel(posmod(world.x,image.get_width()),CAP-1-depth if dy>0 else depth)
	# 明确方向的真转角 RGBA 替换对角带的取样条纹；source 背景已在裁切时遮罩。
	var cell := Vector2i(floori(float(world.x)/TILE),floori(float(world.y)/TILE))
	var p := Vector2i(posmod(world.x,TILE),posmod(world.y,TILE))
	var mask := mask_at(floor_cells,cell)
	var quadrant := ""
	var q := Vector2i.ZERO
	if p.x<64 and p.y<64: quadrant="nw"; q=p
	elif p.x>=64 and p.y<64: quadrant="ne"; q=Vector2i(p.x-64,p.y)
	elif p.x<64 and p.y>=64: quadrant="sw"; q=Vector2i(p.x,p.y-64)
	elif p.x>=64 and p.y>=64: quadrant="se"; q=p-Vector2i(64,64)
	var bits: Array = {"nw":[0,6,7],"ne":[0,2,1],"sw":[4,6,5],"se":[4,2,3]}[quadrant]
	var a := (mask&(1<<int(bits[0])))!=0
	var b := (mask&(1<<int(bits[1])))!=0
	var d := (mask&(1<<int(bits[2])))!=0
	var id := "outer_"+quadrant if not a and not b else "inner_"+quadrant if a and b and not d else ""
	if corners.has(id):
		var artist: Image = corners[id]
		var pixel := artist.get_pixel(q.x,q.y)
		if pixel.a>0.5: color=pixel
	return color


func bridge_color(world: Vector2i,cell: Vector2i) -> Color:
	# 全部方向共用一个真格栅period；方向变化不能把带闭合框的直桥整图塞入交叉口。
	var grate: Image=materials.bridge_grate_period
	var color:=grate.get_pixel(posmod(world.x,grate.get_width()),posmod(world.y,grate.get_height()))
	var local:=world-bounds.position*TILE
	var i:=local.y*width+local.x
	if distance[i]>24: return color
	# 真边梁只出现在实际union空域的边缘；floor接入口和T/X内部完全没有封路梁。
	var dx:=nearest_x[i]-local.x; var dy:=nearest_y[i]-local.y
	var depth:=clampi(distance[i]-1,0,23)
	var beam: Image
	if abs(dx)>abs(dy):
		beam=materials.bridge_beam_e if dx>0 else materials.bridge_beam_w
		return beam.get_pixel(23-depth if dx>0 else depth,posmod(world.y,beam.get_height()))
	beam=materials.bridge_beam_s if dy>0 else materials.bridge_beam_n
	return beam.get_pixel(posmod(world.x,beam.get_width()),23-depth if dy>0 else depth)


func _draw_heads(image: Image) -> void:
	# 仅完整二格横向桥口放真实盖板；南北桥口使用相同盖板 nearest 转向。
	# corner/T/X仍由底图脚印补全，不把单个盖板扩成封路的整格岸线。
	if not materials.has("bridge_head_left_artist"): return
	for cell: Vector2i in bridge_cells:
		if not bridge_cells.has(cell+Vector2i.DOWN) or bridge_cells.has(cell+Vector2i.UP): continue
		var origin := (cell-bounds.position)*TILE+Vector2i(0,INSET)
		if floor_cells.has(cell+Vector2i.LEFT) and floor_cells.has(cell+Vector2i.LEFT+Vector2i.DOWN):
			image.blit_rect(materials.bridge_head_left_artist,Rect2i(0,0,48,160),origin+Vector2i(-24,0))
		if floor_cells.has(cell+Vector2i.RIGHT) and floor_cells.has(cell+Vector2i.RIGHT+Vector2i.DOWN):
			image.blit_rect(materials.bridge_head_right_artist,Rect2i(0,0,48,160),origin+Vector2i(TILE-24,0))
	if not materials.has("bridge_head_north_artist"): return
	for cell: Vector2i in bridge_cells:
		if not bridge_cells.has(cell+Vector2i.RIGHT) or bridge_cells.has(cell+Vector2i.LEFT): continue
		var origin := (cell-bounds.position)*TILE+Vector2i(INSET,0)
		if floor_cells.has(cell+Vector2i.UP) and floor_cells.has(cell+Vector2i.UP+Vector2i.RIGHT):
			image.blit_rect(materials.bridge_head_north_artist,Rect2i(0,0,160,48),origin+Vector2i(0,-24))
		if floor_cells.has(cell+Vector2i.DOWN) and floor_cells.has(cell+Vector2i.DOWN+Vector2i.RIGHT):
			image.blit_rect(materials.bridge_head_south_artist,Rect2i(0,0,160,48),origin+Vector2i(0,TILE-24))


func flatten_layers(images: Dictionary) -> Image:
	# 输入也可能是helper拼回的全图缓存，而本compiler最近一次只编了dirty片段。
	var size: Vector2i=images.floor.get_size()
	var composed := Image.create(size.x,size.y,false,Image.FORMAT_RGBA8)
	for id in ["water","facade","floor","rim","bridge","heads"]:
		composed.blend_rect(images[id],Rect2i(Vector2i.ZERO,size),Vector2i.ZERO)
	return composed
