extends SceneTree
## 只读质量排查：比较源 PNG、当前导入纹理以及 AtlasTexture 实际 GPU 输出。
## 只写本次审计目录；不调用 ResourceSaver、不重建资源、不改项目设置。

const BASE := "res://art-source/ember/quality-audit-2026-10-04"
const CATALOG := "res://assets/ember/characters/robot/robot_frames_catalog_v001.json"
const FRAMES := "res://assets/ember/characters/robot/robot_sprite_frames_v001.tres"
var _imports: Array = []
var _renders: Array = []
var _errors: Array = []

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(BASE + "/engine"))
	_scan_pngs("res://assets/ember")
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
	var frames := load(FRAMES) as SpriteFrames
	if frames == null:
		_errors.append("SpriteFrames missing")
	else:
		for record: Dictionary in catalog["frames"]:
			var clip := str(record["state"]) + "_" + str(record["direction"])
			var index := int(record["frame_index"])
			var texture := frames.get_frame_texture(clip, index)
			var raw := _raw(str(record["file"]))
			for factor in [1, 2]:
				await _render_frame(texture, raw, str(record["id"]), factor)
	var report := {"status": "SOURCE_IMPORT_ATLAS_GPU_PIXEL_MATCH_PASS" if _errors.is_empty() else "ENGINE_PIXEL_MISMATCH",
		"engine": Engine.get_version_info(), "source_png_count": _imports.size(), "robot_gpu_cases": _renders.size(),
		"source_import": _imports, "robot_atlas_gpu": _renders, "errors": _errors,
		"scope": "Equality checks isolate import/rendering; matching pixels do not imply correct silhouette or joints."}
	var file := FileAccess.open(BASE + "/engine/import-render-report.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	print("Quality engine audit: %d PNG imports / %d atlas GPU cases / %d errors" % [_imports.size(), _renders.size(), _errors.size()])
	quit(0 if _errors.is_empty() else 1)

func _raw(path: String) -> Image:
	var source := Image.new()
	source.load_png_from_buffer(FileAccess.get_file_as_bytes(path))
	source.convert(Image.FORMAT_RGBA8)
	return source

func _scan_pngs(folder: String) -> void:
	var directory := DirAccess.open(folder)
	if directory == null:
		_errors.append("Missing directory: " + folder)
		return
	for child in directory.get_directories():
		_scan_pngs(folder.path_join(child))
	for name in directory.get_files():
		if not name.ends_with(".png"): continue
		var path := folder.path_join(name)
		var source := _raw(path)
		var texture := load(path) as Texture2D
		if texture == null:
			_errors.append("Missing imported texture: " + path)
			continue
		var imported := texture.get_image()
		if imported.get_size() != source.get_size():
			_errors.append("Imported dimensions changed: " + path)
			continue
		var alpha_changed := 0
		var visible_rgb_changed := 0
		var transparent_rgb_changed := 0
		for y in source.get_height():
			for x in source.get_width():
				var a := source.get_pixel(x, y)
				var b := imported.get_pixel(x, y)
				if absf(a.a - b.a) > 0.001: alpha_changed += 1
				if maxf(absf(a.r-b.r), maxf(absf(a.g-b.g), absf(a.b-b.b))) > 0.001:
					if a.a > 0.0: visible_rgb_changed += 1
					else: transparent_rgb_changed += 1
		_imports.append({"file": path, "sha256": FileAccess.get_sha256(path), "alpha_changed": alpha_changed,
			"visible_rgb_changed": visible_rgb_changed, "transparent_rgb_changed": transparent_rgb_changed})
		# 老艺术图 fix_alpha_border 可能填充透明域 RGB；它不改变轮廓，单独记录。
		if alpha_changed > 0 or visible_rgb_changed > 0:
			_errors.append("Visible imported pixels changed: " + path)

func _render_frame(texture: Texture2D, raw: Image, identifier: String, factor: int) -> void:
	var viewport := SubViewport.new()
	viewport.size = raw.get_size() * factor
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture = texture
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.texture_repeat = CanvasItem.TEXTURE_REPEAT_DISABLED
	sprite.scale = Vector2(factor, factor)
	var material := CanvasItemMaterial.new()
	material.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	sprite.material = material
	viewport.add_child(sprite)
	root.add_child(viewport)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var output := viewport.get_texture().get_image()
	var alpha_changed := 0
	var visible_rgb_changed := 0
	for y in output.get_height():
		for x in output.get_width():
			var source := raw.get_pixel(x / factor, y / factor)
			var actual := output.get_pixel(x, y)
			if absf(source.a - actual.a) > 0.001: alpha_changed += 1
			if source.a > 0.0 and maxf(absf(source.r-actual.r), maxf(absf(source.g-actual.g), absf(source.b-actual.b))) > 0.001:
				visible_rgb_changed += 1
	var path := BASE + "/engine/" + identifier + "_%dx.png" % factor
	output.save_png(path)
	_renders.append({"id": identifier, "factor": factor, "file": path, "alpha_changed": alpha_changed,
		"visible_rgb_changed": visible_rgb_changed, "source": "Actual SpriteFrames AtlasTexture through transparent SubViewport; Nearest and integer scale"})
	if alpha_changed > 0 or visible_rgb_changed > 0:
		_errors.append("Atlas GPU pixels changed: %s/%dx" % [identifier, factor])
	root.remove_child(viewport)
	viewport.free()
