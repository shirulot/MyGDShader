extends SceneTree
## 新地板的独立装饰：不把油渍、掉漆和检修盖烘焙进每个地形格。
## 运行：Godot --headless --path . --script res://tools/build_pixel_floor_details_v001.gd
## 所有形状在32px原生网格中绘制；不读取或覆盖旧生产图片。

const OUTPUT := "res://assets/ember/environment/pixel_floor_v001/"
const TILE := 32
const IDS := ["oil_small", "oil_long", "wear_small", "wear_long", "rust_patch", "fine_crack", "service_hatch_closed", "service_hatch_open"]
const COLORS := {
	"oil": Color("405763"), "oil_dark": Color("3d535e"),
	"wear": Color("526a76"), "wear_light": Color("586f7a"),
	"rust": Color("655b4d"), "rust_dark": Color("56514a"),
	"crack": Color("364e5b"), "steel": Color("4d6470"),
	"frame": Color("344b58"), "edge": Color("6d848d"),
	"dark": Color("182631"), "brass": Color("9c784e")
}

func _initialize() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	var atlas := Image.create(TILE * 8, TILE, false, Image.FORMAT_RGBA8)
	atlas.fill(Color.TRANSPARENT)
	var entries: Array = []
	for index in range(IDS.size()):
		var tile := _draw_detail(index)
		atlas.blit_rect(tile, Rect2i(0, 0, TILE, TILE), Vector2i(index * TILE, 0))
		entries.append({"id": IDS[index], "coord": [index, 0], "type": "decal" if index < 6 else "service_hatch", "terrain": false})
	assert(atlas.save_png(OUTPUT + "details_atlas_v001.png") == OK)
	var review := atlas.duplicate()
	review.resize(TILE * 8 * 4, TILE * 4, Image.INTERPOLATE_NEAREST)
	review.save_png(OUTPUT + "details_atlas_review_4x.png")
	# 直接用未导入Image构建资源，避免本轮必须依赖既有Godot导入缓存。
	var tiles := TileSet.new()
	tiles.tile_size = Vector2i(TILE, TILE)
	var source := TileSetAtlasSource.new()
	source.texture = ImageTexture.create_from_image(atlas)
	source.texture_region_size = Vector2i(TILE, TILE)
	source.use_texture_padding = true
	tiles.add_source(source, 0)
	for index in range(IDS.size()): source.create_tile(Vector2i(index, 0))
	assert(ResourceSaver.save(tiles, OUTPUT + "details_tileset_v001.tres") == OK)
	var file := FileAccess.open(OUTPUT + "details_catalog.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"tile_size": TILE, "texture": OUTPUT + "details_atlas_v001.png", "tiles": entries, "note": "Independent decorations, no Terrain bits or game collision."}, "\t") + "\n")
	print("DETAILS_BUILD_PASS: " + str(IDS.size()) + " independent details")
	quit()

func _draw_detail(index: int) -> Image:
	var image := Image.create(TILE, TILE, false, Image.FORMAT_RGBA8)
	image.fill(Color.TRANSPARENT)
	match index:
		0:
			_patch(image, Rect2i(10, 11, 12, 9), "oil", 1)
			_patch(image, Rect2i(13, 13, 6, 4), "oil_dark", 2)
		1:
			_patch(image, Rect2i(5, 14, 22, 6), "oil", 3)
			_patch(image, Rect2i(12, 13, 12, 4), "oil_dark", 7)
		2:
			_patch(image, Rect2i(10, 12, 10, 7), "wear", 2)
			_patch(image, Rect2i(13, 13, 5, 4), "wear_light", 5)
		3:
			_patch(image, Rect2i(4, 15, 24, 4), "wear", 9)
			_patch(image, Rect2i(9, 14, 12, 2), "wear_light", 4)
		4:
			_patch(image, Rect2i(10, 12, 10, 8), "rust_dark", 7)
			_patch(image, Rect2i(12, 14, 7, 5), "rust", 3)
		5:
			# 细裂痕有完整端点，不跨出装饰格，也不形成重复大网格。
			for step in range(16):
				var x := 8 + step
				var y := 10 + step / 2
				image.set_pixel(x, y, COLORS.crack)
			for step in range(5): image.set_pixel(16 - step, 14 + step, COLORS.crack)
		6, 7:
			# 开关态安装框完全相同；开放检修口仅是视觉道具，尚不提供掉落判定。
			image.fill_rect(Rect2i(3, 3, 26, 26), COLORS.frame)
			image.fill_rect(Rect2i(4, 4, 24, 24), COLORS.steel)
			image.fill_rect(Rect2i(4, 4, 24, 1), COLORS.edge)
			image.fill_rect(Rect2i(4, 4, 1, 24), COLORS.edge)
			if index == 6:
				image.fill_rect(Rect2i(7, 7, 18, 18), Color("465f6c"))
				image.fill_rect(Rect2i(13, 10, 7, 3), COLORS.dark)
				image.fill_rect(Rect2i(14, 10, 5, 1), COLORS.edge)
			else:
				image.fill_rect(Rect2i(7, 7, 18, 18), COLORS.dark)
				for y in range(10, 25, 4): image.fill_rect(Rect2i(12, y, 8, 1), Color("566b78"))
				image.fill_rect(Rect2i(11, 8, 1, 17), COLORS.frame)
				image.fill_rect(Rect2i(20, 8, 1, 17), COLORS.frame)
			for pos in [Vector2i(5,5), Vector2i(26,5), Vector2i(5,26), Vector2i(26,26)]: image.set_pixelv(pos, COLORS.brass)
	return image

func _patch(image: Image, bounds: Rect2i, color_id: String, seed_value: int) -> void:
	## 固定种子形状使生产结果可复现；低对比成簇补丁由用户局部摆放。
	for y in range(bounds.position.y, bounds.end.y):
		for x in range(bounds.position.x, bounds.end.x):
			var nx := float(x - bounds.position.x) / maxi(bounds.size.x - 1, 1) * 2.0 - 1.0
			var ny := float(y - bounds.position.y) / maxi(bounds.size.y - 1, 1) * 2.0 - 1.0
			var threshold := 0.79 + float((x * 7 + y * 11 + seed_value * 3) % 7) * 0.045
			if nx * nx + ny * ny < threshold and (x / 2 + y / 2 + seed_value) % 9 != 0:
				image.set_pixel(x, y, COLORS[color_id])
