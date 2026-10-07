extends SceneTree
## 根据既定地板占用派生南向平台立面，不改核心351块、走面或桥截面。
## 图块上16px透明，下16px绘图；使用层 position=(0,16)，投影位于格下缘。
## 运行：godot --headless --path . -s res://tools/build_pixel_floor_facade_v001.gd
## 小样：附加 -- --sample-only，只导出真实图块拼样，不改正式catalog。

const OUT := "res://assets/ember/environment/pixel_floor_v001/"
const REVIEW := "res://art-source/ember/pixel-standard-v002/floor-production-v001/"
const SPEC := "res://docs/shader-learning/autotile-neighborhoods-v002.json"
const CLEAR := Color(0,0,0,0)
var _errors: Array[String] = []
var _checked_alpha := 0
var _checked_ports := 0
var _checked_bands := 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	_write_sample()
	if "--sample-only" in OS.get_cmdline_user_args():
		quit(0)
		return
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OUT+"catalog.json"))
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SPEC))
	var core_sha := _core_hashes(catalog)
	var area_entries: Array = []
	for entry: Dictionary in spec.area.tiles:
		area_entries.append({"mask":int(entry.mask),"coord":entry.atlas_coord})
	var contexts: Array = []
	for atlas: Dictionary in catalog.atlases:
		if atlas.id == "floor_landing": contexts = atlas.tiles
	assert(area_entries.size() == 47 and contexts.size() == 89)
	# 只替换自身注册；重跑不会反复追加source，也不会修改核心351图像。
	var preserved: Array = []
	for atlas: Dictionary in catalog.atlases:
		if atlas.id not in ["facade","facade_landing"]: preserved.append(atlas)
	catalog.atlases = preserved
	for atlas_id in ["facade","facade_landing"]:
		var is_context: bool = atlas_id == "facade_landing"
		var entries: Array = contexts if is_context else area_entries
		var atlas := Image.create(256,384 if is_context else 192,false,Image.FORMAT_RGBA8)
		atlas.fill(CLEAR)
		for entry: Dictionary in entries:
			var mask := int(entry.floor_mask if is_context else entry.mask)
			var ports := int(entry.bridge_ports) if is_context else 0
			var coord := Vector2i(int(entry.coord[0]),int(entry.coord[1]))
			var tile := _tile(mask,ports)
			_validate_tile(tile,mask,ports)
			atlas.blit_rect(tile,Rect2i(0,0,32,32),coord*32)
		var path: String = OUT+atlas_id+"_atlas_v001.png"
		assert(atlas.save_png(path) == OK)
		catalog.atlases.append({"id":atlas_id,"mode":"context" if is_context else "blob","texture":path,"tiles":entries,
			"description":"由地板邻域派生的南向平台立面；S邻格为地板时透明；南桥口24px全高透明。不是额外占用笔刷。",
			"geometry":{"transparent_top_px":16,"face_height_px":16,"layer_offset":[0,16],"south_bridge_gap":[4,28],"shoulder_px":4},
			"native_terrain_editable":false,"material_status":"VISUAL_CANDIDATE"})
		atlas.resize(atlas.get_width()*4,atlas.get_height()*4,Image.INTERPOLATE_NEAREST)
		assert(atlas.save_png(REVIEW+atlas_id+"_atlas_review_4x_v001.png") == OK)
	_validate_bands()
	if core_sha != _core_hashes(catalog): _fail("核心351图像被改动")
	catalog["facade_revision"] = "v001"
	_write_json(OUT+"catalog.json",catalog)
	var report := {"status":"CONNECTIVITY_PASS" if _errors.is_empty() else "FAIL","engine":Engine.get_version_info().string,
		"counts":{"facade":47,"facade_landing":89},"checked_alpha_pixels":_checked_alpha,"checked_south_bridge_gap_pixels":_checked_ports,
		"checked_neighbor_band_pixels":_checked_bands,"geometry":{"tile_size":32,"face_start_in_tile":16,"face_height":16,"layer_offset":[0,16],"south_bridge_gap":[4,28]},
		"checks":["136图块二值Alpha","每块上16px透明","有S地板邻居整块透明","无S地板下16px有立面","南桥24px全高透空与4px肩部完整","相邻面板边缘/4px截面/32px切向周期","原351图块SHA256保持"],
		"core_sha256":core_sha,"errors":_errors}
	_write_json(OUT+"facade_validation.json",report)
	print(JSON.stringify(report,"\t"))
	quit(0 if _errors.is_empty() else 1)


func _tile(floor_mask: int,bridge_ports: int) -> Image:
	var tile := Image.create(32,32,false,Image.FORMAT_RGBA8)
	tile.fill(CLEAR)
	if (floor_mask & 16) != 0: return tile
	for y in range(16,32):
		for x in range(32):
			# 南桥开口贯穿16px投影高度，不只擦掉顶端或底端一排。
			if (bridge_ports & 4) != 0 and x >= 4 and x < 28: continue
			tile.set_pixel(x,y,_face_color(x,y-16))
	return tile


func _face_color(x: int,depth: int) -> Color:
	var phase := posmod(x,32)
	var border_distance := mini(phase,31-phase)
	# 参考场景的深钢前面：内暗唇、低亮金属折面、分段面板、接水暗线。
	if depth == 0: return Color("111F2A")
	if depth == 1: return Color("40545F")
	if depth == 2: return Color("314653")
	if depth == 14: return Color("172731")
	if depth == 15: return Color("0E1A24")
	if border_distance == 0 or phase == 16: return Color("12212C")
	if border_distance == 1 or phase == 17: return Color("1B2D39")
	if depth == 3: return Color("2B3E4B")
	if depth == 4: return Color("253946")
	if depth == 13: return Color("1B2E3A")
	var color := Color("233541")
	if phase >= 4 and phase <= 14: color = Color("273A47")
	if phase >= 18 and phase <= 27: color = Color("233541")
	# 少量边紧固件，体积不足1px时不制造发光高光；不做四角铆钉阵列。
	if depth == 6 and phase in [7,23]: return Color("40535E")
	if depth == 7 and phase in [7,23]: return Color("162732")
	if depth == 11 and phase in [8,24]: return Color("1C303C")
	return color


func _validate_tile(tile: Image,mask: int,ports: int) -> void:
	for y in range(32):
		for x in range(32):
			_checked_alpha += 1
			var alpha := tile.get_pixel(x,y).a8
			if alpha not in [0,255]: _fail("立面Alpha不是二值")
			var expected := y >= 16 and (mask & 16) == 0 and not ((ports & 4) != 0 and x >= 4 and x < 28)
			if (alpha == 255) != expected: _fail("S邻接/投影/开口不符合登记")
			if y >= 16 and (ports & 4) != 0 and (mask & 16) == 0:
				_checked_ports += 1
				if x >= 4 and x < 28 and alpha != 0: _fail("南桥24px通道被立面覆盖")
				if (x < 4 or x >= 28) and alpha != 255: _fail("桥口4px肩柱缺失")


func _validate_bands() -> void:
	# 外露南面相邻时，切向接口的前后4px同截面；颜色固定世界相位。
	for y in range(16):
		for depth in range(4):
			_checked_bands += 1
			if _face_color(depth,y) != _face_color(31-depth,y): _fail("邻面4px截面不一致")
		for x in range(32):
			_checked_bands += 1
			if _face_color(x,y) != _face_color(x+32,y): _fail("切向32px相位不连续")
	# 桥肩采用同颜色函数，开口两侧位置4/28完全登记，无临时擦图补缝。
	for y in range(16,32):
		var landing := _tile(0,4)
		var base := _tile(0,0)
		for x in [0,1,2,3,28,29,30,31]:
			_checked_bands += 1
			if landing.get_pixel(x,y) != base.get_pixel(x,y): _fail("桥肩与普通面板截面不一致")


func _write_sample() -> void:
	var image := Image.create(288,176,false,Image.FORMAT_RGBA8)
	image.fill(Color("183644"))
	var floor_atlas := Image.load_from_file(ProjectSettings.globalize_path(OUT+"floor_atlas_v001.png"))
	var rim_atlas := Image.load_from_file(ProjectSettings.globalize_path(OUT+"rim_atlas_v001.png"))
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SPEC))
	var coordinates := {}
	for entry: Dictionary in spec.area.tiles:
		coordinates[int(entry.mask)] = Vector2i(int(entry.atlas_coord[0]),int(entry.atlas_coord[1]))
	# 六格平台，内部5排是真正地板图块；立面同源图块投影至地板下缘。
	for y in range(3):
		for x in range(6):
			var mask := 255
			if y == 0: mask &= ~(1|2|128)
			if y == 2: mask &= ~(16|8|32)
			if x == 0: mask &= ~(64|128|32)
			if x == 5: mask &= ~(4|2|8)
			var origin := Vector2i(24+x*32,16+y*32)
			image.blend_rect(_tile(mask,0),Rect2i(0,0,32,32),origin+Vector2i(0,16))
			image.blend_rect(floor_atlas,Rect2i(coordinates[mask]*32,Vector2i(32,32)),origin)
			image.blend_rect(rim_atlas,Rect2i(coordinates[mask]*32,Vector2i(32,32)),origin)
	# 右方单独示例说明：全南面、24px桥口、南侧有floor时全透明。
	for i in range(3):
		image.blend_rect(_tile([0,0,16][i],[0,4,0][i]),Rect2i(0,0,32,32),Vector2i(232,8+i*48))
	assert(image.save_png(REVIEW+"facade_sample_native_v001.png") == OK)
	image.resize(1152,704,Image.INTERPOLATE_NEAREST)
	assert(image.save_png(REVIEW+"facade_sample_4x_v001.png") == OK)


func _core_hashes(catalog: Dictionary) -> Dictionary:
	var result := {}
	for atlas: Dictionary in catalog.atlases:
		if atlas.id in ["floor","rim","grate","seam","bridge","floor_landing","rim_landing"]:
			result[atlas.id] = FileAccess.get_sha256(atlas.texture)
	return result


func _write_json(path: String,value: Dictionary) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	assert(file != null)
	file.store_string(JSON.stringify(value,"\t"))


func _fail(message: String) -> void:
	if _errors.size() < 20: _errors.append(message)
