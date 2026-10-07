extends SceneTree
## 使用 Godot Image 拼装当前生产水中心 tile，原图和课程 Shader 均保持不变。
## 运行：Godot --headless --path <项目目录> --script res://art-source/ember/chapter06-water-preview/build_existing.gd

const SOURCE_PATH := "res://assets/ember/environment/autotiles_v007/water_autotile_v007.png"
const SOURCE_SHA256 := "01f7a950cc9d19ffc73562c2eca5550f6d6e2fce8697e72d7cf400ea6e451f92"
const SOURCE_RECT := Rect2i(768, 640, 128, 128)
const OUTPUT_PATH := "res://assets/ember/vfx/water/ch06_water_existing_v001.png"
const PROVENANCE_PATH := "res://art-source/ember/chapter06-water-preview/existing-provenance.json"
const GRID_COUNT := 4
const OUTPUT_SIZE := 512


func _init() -> void:
	# 先核对原 atlas 身份，避免误把另一版本或含岸边的格子当成纯水面。
	var source_hash := FileAccess.get_sha256(SOURCE_PATH)
	if source_hash != SOURCE_SHA256:
		_fail("原 atlas 的 SHA256 与已核对的 v007 不一致，停止拼装。")
		return
	var atlas := Image.new()
	var load_error := atlas.load_png_from_buffer(FileAccess.get_file_as_bytes(SOURCE_PATH))
	if load_error != OK or atlas.get_size() != Vector2i(1024, 768):
		_fail("无法读取预期的 1024×768 原 atlas，错误码：%s" % load_error)
		return

	# mask255 的中心格位于 atlas (6,5)，只截取这一个 128×128 原生区域。
	var tile := atlas.get_region(SOURCE_RECT)
	tile.convert(Image.FORMAT_RGBA8)
	var edge_counts := _edge_mismatches(tile)
	if edge_counts["x"] != 0 or edge_counts["y"] != 0:
		_fail("中心 tile 的相对边界不一致，停止拼装。")
		return
	for y in range(tile.get_height()):
		for x in range(tile.get_width()):
			if tile.get_pixel(x, y).a != 1.0:
				_fail("中心 tile 含透明像素，停止拼装。")
				return

	# blit_rect 是逐像素复制：4×4 格共 512×512，不拉伸、不插值、不重绘水纹。
	var assembled := Image.create(OUTPUT_SIZE, OUTPUT_SIZE, false, Image.FORMAT_RGBA8)
	for grid_y in range(GRID_COUNT):
		for grid_x in range(GRID_COUNT):
			assembled.blit_rect(tile, Rect2i(Vector2i.ZERO, tile.get_size()),
				Vector2i(grid_x * tile.get_width(), grid_y * tile.get_height()))

	# 每个复制区域必须与原生中心格完全相同，这只验证素材拼装，不验证 GPU 效果。
	var tile_bytes := tile.get_data()
	for grid_y in range(GRID_COUNT):
		for grid_x in range(GRID_COUNT):
			var copied_rect := Rect2i(grid_x * 128, grid_y * 128, 128, 128)
			if assembled.get_region(copied_rect).get_data() != tile_bytes:
				_fail("拼装区域与原 tile 不一致，停止保存。")
				return

	var directory_error := DirAccess.make_dir_recursive_absolute(
		ProjectSettings.globalize_path(OUTPUT_PATH.get_base_dir()))
	if directory_error != OK:
		_fail("无法准备派生素材目录，错误码：%s" % directory_error)
		return
	var save_error := assembled.save_png(OUTPUT_PATH)
	if save_error != OK:
		_fail("无法保存拼装 PNG，错误码：%s" % save_error)
		return
	var saved := Image.new()
	var reload_error := saved.load_png_from_buffer(FileAccess.get_file_as_bytes(OUTPUT_PATH))
	if reload_error != OK:
		_fail("无法回读拼装 PNG，错误码：%s" % reload_error)
		return
	saved.convert(Image.FORMAT_RGBA8)
	if saved.get_size() != Vector2i(OUTPUT_SIZE, OUTPUT_SIZE) or saved.get_data() != assembled.get_data():
		_fail("PNG 保存回读后像素不一致。")
		return

	# 留下明确的派生关系和核对范围；后续场景渲染由主教师单独检查。
	var provenance := {
		"schema_version": 1,
		"date": "2026-10-07",
		"status": "NATIVE_TILE_ASSEMBLY_PIXEL_VERIFIED",
		"source": {
			"path": SOURCE_PATH,
			"absolute_path": ProjectSettings.globalize_path(SOURCE_PATH),
			"sha256": source_hash,
			"image_size": [1024, 768],
			"catalog": "res://assets/ember/environment/autotiles_v007/catalog.json",
			"catalog_mask": 255,
			"atlas_coord": [6, 5],
			"region_px": [768, 640, 128, 128],
			"catalog_art_source": "assets/ember/environment/autotiles_v006/water_autotile_v006.png",
			"catalog_visual_status": "STYLE_UNIFICATION_CANDIDATE_PENDING_USER_REVIEW"
		},
		"assembly": {
			"grid": [GRID_COUNT, GRID_COUNT],
			"native_tile_size": [128, 128],
			"output_size": [OUTPUT_SIZE, OUTPUT_SIZE],
			"resampling": "NONE_NATIVE_PIXEL_BLIT",
			"source_modified": false,
			"new_ai_generation": false,
			"source_use": "DERIVED_BY_EXISTING_PRODUCTION_TILE_ASSEMBLY"
		},
		"output": {
			"path": OUTPUT_PATH,
			"absolute_path": ProjectSettings.globalize_path(OUTPUT_PATH),
			"sha256": FileAccess.get_sha256(OUTPUT_PATH),
			"mode": "RGBA8",
			"alpha": "ALL_OPAQUE"
		},
		"checks": {
			"source_sha256_matches": true,
			"tile_x_edge_rgba_mismatches": edge_counts["x"],
			"tile_y_edge_rgba_mismatches": edge_counts["y"],
			"all_16_regions_pixel_exact": true,
			"png_round_trip_pixel_exact": true,
			"gpu_render_validation": "NOT_PERFORMED",
			"game_application_validation": "NOT_PERFORMED"
		},
		"scene": {
			"path": "res://scenes/chapter06/ch06_02_water_existing.tscn",
			"shader": "res://scenes/chapter06/ch06_02_heat_haze.gdshader",
			"noise": "res://assets/ember/data/noise/noise_low_v001.png",
			"mask": "res://assets/ember/data/masks/circle_mask_v001.png",
			"noise_speed": 0.1,
			"display_size": [512, 512],
			"purpose": "INDEPENDENT_C06_EXISTING_WATER_PREVIEW"
		}
	}
	var record := FileAccess.open(PROVENANCE_PATH, FileAccess.WRITE)
	if record == null:
		_fail("无法写入来源记录，错误码：%s" % FileAccess.get_open_error())
		return
	record.store_string(JSON.stringify(provenance, "\t") + "\n")
	record.close()
	print("Existing water assembled: 512x512; 16 native tiles; PNG round-trip exact; source unchanged.")
	quit(0)


func _edge_mismatches(tile: Image) -> Dictionary:
	# 相对边界 RGBA 相同，保证重复拼装时没有数值断缝。
	var counts := {"x": 0, "y": 0}
	for y in range(tile.get_height()):
		if tile.get_pixel(0, y) != tile.get_pixel(tile.get_width() - 1, y):
			counts["x"] += 1
	for x in range(tile.get_width()):
		if tile.get_pixel(x, 0) != tile.get_pixel(x, tile.get_height() - 1):
			counts["y"] += 1
	return counts


func _fail(message: String) -> void:
	push_error(message)
	quit(1)
