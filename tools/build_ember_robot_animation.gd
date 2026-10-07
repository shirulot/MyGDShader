extends SceneTree
## 将 C01 的 20 张原生帧和 5×4 图集整理为可复用的 SpriteFrames。
## 先导入 PNG：godot --headless --editor --path . --import
## 构建：godot --headless --path . -s res://tools/build_ember_robot_animation.gd --
## 核验：在上述命令末尾添加 --verify-only（不重写 .tres 或示例场景）。
## 可选：--catalog=res://...json、--report=绝对路径或 res://...json。
## 可选：--rebuild-sandbox 明确覆盖示例；--screenshot=绝对路径需非 headless。
## 本工具不制作 PNG，不接入旧玩家、碰撞、移动、Shader 或主场景。

const ASSET_DIR := "res://assets/ember/characters/robot"
const DEFAULT_CATALOG := ASSET_DIR + "/robot_frames_catalog_v001.json"
const SHEET_PATH := ASSET_DIR + "/robot_animations_v001.png"
const SPRITE_FRAMES_PATH := ASSET_DIR + "/robot_sprite_frames_v001.tres"
const SANDBOX_PATH := "res://scenes/ember/robot_animation_sandbox.tscn"
const DEFAULT_REPORT := "res://art-source/ember/batch-02-robot/review/godot_validation_v001.json"
const FRAME_SIZE := Vector2i(64, 96)
const SHEET_SIZE := Vector2i(320, 384)
const FOOT_ANCHOR := Vector2i(32, 80)
const DIRECTIONS := ["down", "left", "right", "up"]
const DIRECTION_LABELS := ["下 / down", "左 / left", "右 / right", "上 / up"]
const ACCEPTED_IDLE_SHA256 := "c65f68455554edb03aea0a7b7b3cea6e1a779fa9d5aa49cba9b4aa5c4f6fbfff"
const PREVIEW_SIZE := Vector2i(1280, 800)

var _errors: PackedStringArray = []
var _catalog_path := DEFAULT_CATALOG
var _report_path := DEFAULT_REPORT
var _verify_only := false
var _rebuild_sandbox := false
var _screenshot_path := ""
var _frames: Dictionary = {}
var _animations: Dictionary = {}
var _observed: Dictionary = {}
var _scene_preserved := false


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	_parse_arguments()
	if not _errors.is_empty():
		_finish_failure()
		return
	var catalog := _read_catalog()
	_validate_inputs(catalog)
	if not _errors.is_empty():
		_finish_failure()
		return

	# 只有所有原生 PNG、哈希、图集与目录均通过输入检查后才写资源。
	if _verify_only:
		_scene_preserved = FileAccess.file_exists(SANDBOX_PATH)
	if not _verify_only:
		_build_sprite_frames()
		if _errors.is_empty() and (_rebuild_sandbox or not FileAccess.file_exists(SANDBOX_PATH)):
			_build_sandbox()
		elif _errors.is_empty():
			_scene_preserved = true
			print("保留已有动画审阅场景：", SANDBOX_PATH)
	if _errors.is_empty():
		_verify_resources()
	if _errors.is_empty():
		await _verify_runtime_and_capture()
	if not _errors.is_empty():
		_finish_failure()
		return

	var report := _base_report("GODOT_ROBOT_ANIMATION_VALIDATED")
	if not _screenshot_path.is_empty():
		report["screenshot"] = _screenshot_path
	_write_report(report)
	if not _errors.is_empty():
		_finish_failure()
		return
	print(JSON.stringify(report, "\t"))
	quit(0)


func _parse_arguments() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument == "--verify-only":
			_verify_only = true
		elif argument == "--rebuild-sandbox":
			_rebuild_sandbox = true
		elif argument.begins_with("--catalog="):
			_catalog_path = argument.trim_prefix("--catalog=")
		elif argument.begins_with("--report="):
			_report_path = argument.trim_prefix("--report=")
		elif argument.begins_with("--screenshot="):
			_screenshot_path = argument.trim_prefix("--screenshot=")
		else:
			_errors.append("不支持的参数：" + argument)
	if _catalog_path.is_empty() or _report_path.is_empty():
		_errors.append("catalog 与 report 路径不能为空。")
	if _verify_only and _rebuild_sandbox:
		_errors.append("--verify-only 与 --rebuild-sandbox 不能同时使用。")
	if not _screenshot_path.is_empty() and DisplayServer.get_name() == "headless":
		_errors.append("headless 不能生成真实渲染截图，请移除 --headless 后运行 --screenshot。")


func _read_catalog() -> Dictionary:
	if not FileAccess.file_exists(_catalog_path):
		_errors.append("生产 catalog 尚未就绪：" + _catalog_path)
		return {}
	var parser := JSON.new()
	if parser.parse(FileAccess.get_file_as_string(_catalog_path)) != OK or not parser.data is Dictionary:
		_errors.append("catalog 必须是有效 JSON 对象：" + parser.get_error_message())
		return {}
	return parser.data as Dictionary


func _validate_inputs(catalog: Dictionary) -> void:
	if catalog.is_empty():
		return
	if str(catalog.get("status", "")).contains("PLANNED"):
		_errors.append("规划目录不能作为完成的生产输入。")
	if catalog.get("schema_version") != 1:
		_errors.append("catalog.schema_version 必须为 1。")
	if not _pair_matches(catalog.get("canvas"), FRAME_SIZE) or not _pair_matches(catalog.get("anchor"), FOOT_ANCHOR):
		_errors.append("所有帧必须使用 64×96 画布及 (32,80) 脚底锚点。")
	if catalog.get("directions") != DIRECTIONS:
		_errors.append("方向顺序必须为 down / left / right / up。")
	_validate_frames(catalog.get("frames"))
	_validate_animations(catalog.get("animations"))
	_validate_sheet(catalog.get("sheet"))
	if not _errors.is_empty():
		return

	var sheet_texture := _load_imported_texture(SHEET_PATH, SHEET_SIZE)
	if sheet_texture == null:
		return
	_validate_import_config(SHEET_PATH)
	var sheet_image := _load_raw_image(SHEET_PATH)
	if sheet_image == null:
		return
	# 此检查比较原始 PNG 的 RGBA 字节，确保 atlas 没有缩放、错位或漏帧。
	# 使用绝对路径读原始文件，避免把裸 Image.load(res://...) 当正式导入资源。
	var hashes := {}
	var matched_regions := 0
	for frame_id in _frames:
		var record: Dictionary = _frames[frame_id]
		var frame_path := str(record["file"])
		if not FileAccess.file_exists(frame_path):
			_errors.append("原生单帧 PNG 尚未就绪：" + frame_path)
			continue
		var actual_hash := FileAccess.get_sha256(frame_path)
		if actual_hash != record["sha256"]:
			_errors.append("单帧 SHA256 与 catalog 不一致：" + str(frame_id))
		if frame_id == "robot_idle_down" and actual_hash != ACCEPTED_IDLE_SHA256:
			_errors.append("已验收的 down idle 原图发生变化。")
		hashes[frame_id] = actual_hash
		_load_imported_texture(frame_path, FRAME_SIZE)
		_validate_import_config(frame_path)
		var frame_image := _load_raw_image(frame_path)
		if frame_image == null:
			continue
		if frame_image.get_size() != FRAME_SIZE:
			_errors.append("原生单帧 PNG 必须为 64×96：" + frame_path)
			continue
		var region := sheet_image.get_region(Rect2i(_coordinate(record) * FRAME_SIZE, FRAME_SIZE))
		if region.get_data() != frame_image.get_data():
			_errors.append("图集区域与单帧 PNG 的原生像素不一致：" + str(frame_id))
		else:
			matched_regions += 1
	_observed["input_frame_count"] = _frames.size()
	_observed["native_regions_equal_to_source"] = matched_regions
	_observed["source_sha256"] = hashes
	_observed["sheet_sha256"] = FileAccess.get_sha256(SHEET_PATH)
	_observed["sheet_imported_size"] = [int(sheet_texture.get_width()), int(sheet_texture.get_height())]


func _validate_frames(value: Variant) -> void:
	if not value is Array or value.size() != 20:
		_errors.append("catalog.frames 必须包含完整 20 帧。")
		return
	var expected := _expected_frames()
	for entry in value:
		if not entry is Dictionary:
			_errors.append("frame 项必须是对象。")
			continue
		var frame: Dictionary = entry
		var frame_id := str(frame.get("id", ""))
		if not expected.has(frame_id) or _frames.has(frame_id):
			_errors.append("未知或重复 frame.id：" + frame_id)
			continue
		var rule: Dictionary = expected[frame_id]
		for field in ["direction", "state", "frame_index", "file"]:
			if frame.get(field) != rule[field]:
				_errors.append("frame.%s 不符：%s" % [field, frame_id])
		if not _pair_matches(frame.get("coord"), rule["coord"]) or not _pair_matches(frame.get("anchor"), FOOT_ANCHOR):
			_errors.append("坐标或锚点不符：" + frame_id)
		var frame_hash := str(frame.get("sha256", ""))
		if not frame.get("sha256") is String or frame_hash.length() != 64 or not frame_hash.is_valid_hex_number(false):
			_errors.append("完成帧必须提供 64 位 SHA256：" + frame_id)
		if str(frame.get("status", "")).contains("PLANNED"):
			_errors.append("帧仍标记为规划状态：" + frame_id)
		_frames[frame_id] = frame
	if _frames.size() != expected.size():
		_errors.append("完整帧目录缺失 ID。")


func _validate_animations(value: Variant) -> void:
	if not value is Array or value.size() != 8:
		_errors.append("catalog.animations 必须包含四方向 idle / walk 共 8 个 clip。")
		return
	for entry in value:
		if not entry is Dictionary:
			_errors.append("animation 项必须是对象。")
			continue
		var animation: Dictionary = entry
		var clip_id := str(animation.get("id", ""))
		var state := str(animation.get("state", ""))
		var direction := str(animation.get("direction", ""))
		if direction not in DIRECTIONS or state not in ["idle", "walk"] or clip_id != state + "_" + direction or _animations.has(clip_id):
			_errors.append("未知、重复或命名不一致的 animation：" + clip_id)
			continue
		var expected_ids: Array = []
		if state == "idle":
			expected_ids.append("robot_idle_" + direction)
		else:
			for index in range(4):
				expected_ids.append("robot_walk_%s_f%02d" % [direction, index])
		if animation.get("frame_ids") != expected_ids:
			_errors.append("动画帧顺序不符：" + clip_id)
		var expected_fps := 1.0 if state == "idle" else 8.0
		if animation.get("fps") != expected_fps or animation.get("loop") != true:
			_errors.append("idle 使用 1 FPS 单帧，walk 使用 8 FPS；本批 clip 循环标记均为 true：" + clip_id)
		_animations[clip_id] = animation
	if _animations.size() != 8:
		_errors.append("缺失四方向 idle / walk clip。")


func _validate_sheet(value: Variant) -> void:
	if not value is Dictionary:
		_errors.append("catalog.sheet 必须为对象。")
		return
	var sheet: Dictionary = value
	if sheet.get("texture") != SHEET_PATH or not _pair_matches(sheet.get("size"), SHEET_SIZE) or sheet.get("columns") != 5 or sheet.get("rows") != 4:
		_errors.append("图集必须使用固定 320×384、5 列 × 4 行及生产路径。")
	if not sheet.get("frames") is Array or sheet["frames"].size() != 20:
		_errors.append("sheet.frames 必须包含 20 个明确区域。")
		return
	var expected := _expected_frames()
	var seen := {}
	for entry in sheet["frames"]:
		if not entry is Dictionary:
			_errors.append("sheet.frames 项必须为对象。")
			continue
		var frame_id := str(entry.get("frame_id", ""))
		if not expected.has(frame_id) or seen.has(frame_id):
			_errors.append("图集出现未知或重复 frame_id：" + frame_id)
			continue
		if not _pair_matches(entry.get("coord"), expected[frame_id]["coord"]):
			_errors.append("图集坐标不符：" + frame_id)
		seen[frame_id] = true


func _expected_frames() -> Dictionary:
	var result := {}
	for row in range(DIRECTIONS.size()):
		var direction: String = DIRECTIONS[row]
		for column in range(5):
			var state := "idle" if column == 0 else "walk"
			var index := 0 if column == 0 else column - 1
			var frame_id := "robot_idle_" + direction if column == 0 else "robot_walk_%s_f%02d" % [direction, index]
			result[frame_id] = {"direction": direction, "state": state, "frame_index": index,
				"file": ASSET_DIR + "/" + frame_id + "_v001.png", "coord": Vector2i(column, row)}
	return result


func _pair_matches(value: Variant, expected: Vector2i) -> bool:
	if not value is Array or value.size() != 2:
		return false
	if typeof(value[0]) not in [TYPE_INT, TYPE_FLOAT] or typeof(value[1]) not in [TYPE_INT, TYPE_FLOAT]:
		return false
	return value[0] == expected.x and value[1] == expected.y


func _coordinate(record: Dictionary) -> Vector2i:
	return Vector2i(int(record["coord"][0]), int(record["coord"][1]))


func _load_imported_texture(path: String, size: Vector2i) -> Texture2D:
	if not FileAccess.file_exists(path) or not ResourceLoader.exists(path, "Texture2D"):
		_errors.append("PNG 不存在或尚未导入 Godot，请先运行 --headless --editor --import：" + path)
		return null
	var texture := ResourceLoader.load(path, "Texture2D") as Texture2D
	# Texture2D.get_size() 返回 Vector2，先转换再与原生整数尺寸比较。
	if texture == null or Vector2i(texture.get_size()) != size:
		_errors.append("导入纹理的原生尺寸不符：" + path)
		return null
	return texture


func _validate_import_config(path: String) -> void:
	var config := ConfigFile.new()
	if config.load(path + ".import") != OK:
		_errors.append("缺失 PNG 导入配置：" + path)
		return
	if config.get_value("params", "compress/mode", -1) != 0 or config.get_value("params", "mipmaps/generate", true) != false:
		_errors.append("像素图应使用 Lossless 压缩且关闭 mipmaps：" + path)


func _load_raw_image(path: String) -> Image:
	var image := Image.new()
	if image.load(ProjectSettings.globalize_path(path)) != OK:
		_errors.append("原始 PNG 无法读取：" + path)
		return null
	image.convert(Image.FORMAT_RGBA8)
	return image


func _build_sprite_frames() -> void:
	var sprite_frames := SpriteFrames.new()
	sprite_frames.resource_name = "EmberRobotC01V001"
	sprite_frames.remove_animation("default")
	var sheet := ResourceLoader.load(SHEET_PATH, "Texture2D") as Texture2D
	var regions := {}
	for frame_id in _frames:
		var region := AtlasTexture.new()
		region.resource_name = frame_id
		region.atlas = sheet
		region.region = Rect2(_coordinate(_frames[frame_id]) * FRAME_SIZE, FRAME_SIZE)
		region.margin = Rect2()
		region.filter_clip = true
		regions[frame_id] = region
	for clip_id in _animations:
		var animation: Dictionary = _animations[clip_id]
		sprite_frames.add_animation(clip_id)
		sprite_frames.set_animation_speed(clip_id, float(animation["fps"]))
		# 4.7 使用显式 LoopMode；单帧 idle 即使循环也不会制造额外姿态。
		sprite_frames.set_animation_loop_mode(clip_id, SpriteFrames.LOOP_LINEAR)
		for frame_id in animation["frame_ids"]:
			sprite_frames.add_frame(clip_id, regions[frame_id], 1.0)
	_save_resource(sprite_frames, SPRITE_FRAMES_PATH)


func _build_sandbox() -> void:
	var sprite_frames := ResourceLoader.load(SPRITE_FRAMES_PATH, "SpriteFrames", ResourceLoader.CACHE_MODE_IGNORE) as SpriteFrames
	if sprite_frames == null:
		_errors.append("构建示例之前无法重载 SpriteFrames。")
		return
	var scene := Node2D.new()
	scene.name = "EmberRobotAnimationSandbox"
	scene.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	# 示例单独运行时采用足够容纳 1× / 2× 的窗口，不修改项目的 720×720 配置。
	# 轻量脚本作为场景内嵌资源，仅调整本次预览窗口，不依赖旧 Game 或角色脚本。
	var preview_script := GDScript.new()
	preview_script.source_code = "extends Node2D\n## 仅本次独立动画预览采用 1280×800；不写 ProjectSettings。\nfunc _ready() -> void:\n\tget_window().content_scale_size = Vector2i(1280, 800)\n\tif DisplayServer.get_name() != \"headless\":\n\t\tget_window().size = Vector2i(1280, 800)\n"
	if preview_script.reload() != OK:
		_errors.append("动画审阅场景的窗口脚本编译失败。")
		scene.free()
		return
	scene.set_script(preview_script)
	_add_rect(scene, scene, "Background", Vector2.ZERO, Vector2(PREVIEW_SIZE), Color("101820"))
	_add_label(scene, scene, "Title", Vector2(32, 20), "C01 机器人 · 四方向待机与行走", 26)
	_add_label(scene, scene, "Hint", Vector2(32, 62), "64×96 固定画布 · 脚底锚点 (32,80) · 左上受光 · 十字标记便于检查站位", 17)
	for scale_index in range(2):
		var factor := scale_index + 1
		var group := Node2D.new()
		group.name = "Native" if factor == 1 else "Double"
		group.position = Vector2(32, 126) if factor == 1 else Vector2(568, 126)
		scene.add_child(group)
		group.owner = scene
		var panel_width := 480.0 if factor == 1 else 672.0
		_add_rect(group, scene, "Panel", Vector2.ZERO, Vector2(panel_width, 596), Color("182631"))
		_add_label(group, scene, "ScaleLabel", Vector2(18, 12), "原生 1× · 64×96 画布" if factor == 1 else "整数 2× · 128×192 画布", 20)
		_add_label(group, scene, "IdleLabel", Vector2(18, 50), "待机 · 单帧", 17)
		_add_label(group, scene, "WalkLabel", Vector2(18, 320), "行走 · 4 帧循环 / 8 FPS", 17)
		for column in range(DIRECTIONS.size()):
			var direction: String = DIRECTIONS[column]
			var foot_x := 74.0 + column * 110.0 if factor == 1 else 80.0 + column * 160.0
			_add_label(group, scene, "IdleDirection" + direction.capitalize(), Vector2(foot_x - 38, 82), DIRECTION_LABELS[column], 15)
			_add_label(group, scene, "WalkDirection" + direction.capitalize(), Vector2(foot_x - 38, 350), DIRECTION_LABELS[column], 15)
			for state in ["idle", "walk"]:
				var foot := Vector2(foot_x, 240 if state == "idle" else 520)
				_add_anchor_marker(group, scene, state.capitalize() + direction.capitalize() + "Anchor", foot)
				var sprite := AnimatedSprite2D.new()
				sprite.name = state.capitalize() + direction.capitalize()
				sprite.position = foot
				sprite.scale = Vector2(factor, factor)
				sprite.sprite_frames = sprite_frames
				sprite.centered = false
				sprite.offset = -Vector2(FOOT_ANCHOR)
				sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
				sprite.animation = state + "_" + direction
				sprite.autoplay = sprite.animation
				group.add_child(sprite)
				sprite.owner = scene
	_add_label(scene, scene, "ReuseHint", Vector2(32, 750), "可直接为 AnimatedSprite2D 指定外部 SpriteFrames；本示例只预览动画。", 17)
	var packed := PackedScene.new()
	if packed.pack(scene) != OK:
		_errors.append("动画审阅场景打包失败。")
	else:
		_save_resource(packed, SANDBOX_PATH)
	scene.free()


func _add_rect(parent: Node, owner_node: Node, node_name: String, position: Vector2, size: Vector2, color: Color) -> void:
	var rectangle := ColorRect.new()
	rectangle.name = node_name
	rectangle.position = position
	rectangle.size = size
	rectangle.color = color
	rectangle.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(rectangle)
	rectangle.owner = owner_node


func _add_label(parent: Node, owner_node: Node, node_name: String, position: Vector2, content: String, font_size: int) -> void:
	var label := Label.new()
	label.name = node_name
	label.position = position
	label.text = content
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Microsoft YaHei", "Noto Sans CJK SC", "PingFang SC", "Arial"])
	label.add_theme_font_override("font", font)
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", Color("BECBC4"))
	parent.add_child(label)
	label.owner = owner_node


func _add_anchor_marker(parent: Node, owner_node: Node, node_name: String, position: Vector2) -> void:
	var marker := Node2D.new()
	marker.name = node_name
	marker.position = position
	parent.add_child(marker)
	marker.owner = owner_node
	for axis in range(2):
		var line := Line2D.new()
		line.name = "Horizontal" if axis == 0 else "Vertical"
		line.points = PackedVector2Array([Vector2(-9, 0), Vector2(9, 0)]) if axis == 0 else PackedVector2Array([Vector2(0, -5), Vector2(0, 5)])
		line.width = 1.0
		line.default_color = Color("4D6470")
		line.antialiased = false
		marker.add_child(line)
		line.owner = owner_node


func _save_resource(resource: Resource, path: String) -> void:
	if DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir())) != OK:
		_errors.append("无法创建资源输出目录：" + path.get_base_dir())
		return
	var result := ResourceSaver.save(resource, path)
	if result != OK:
		_errors.append("资源保存失败 %s：%s" % [error_string(result), path])


func _verify_resources() -> void:
	var sprite_frames := ResourceLoader.load(SPRITE_FRAMES_PATH, "SpriteFrames", ResourceLoader.CACHE_MODE_IGNORE) as SpriteFrames
	if sprite_frames == null:
		_errors.append("SpriteFrames 无法重载：" + SPRITE_FRAMES_PATH)
		return
	var names := sprite_frames.get_animation_names()
	if names.size() != 8:
		_errors.append("SpriteFrames 必须只含完整 8 个 clip。")
	var clips := {}
	var observed_frame_count := 0
	for clip_id in _animations:
		var record: Dictionary = _animations[clip_id]
		if not sprite_frames.has_animation(clip_id):
			_errors.append("SpriteFrames 缺失 clip：" + clip_id)
			continue
		var frame_ids: Array = record["frame_ids"]
		var count := sprite_frames.get_frame_count(clip_id)
		observed_frame_count += count
		clips[clip_id] = {"frame_count": count, "fps": sprite_frames.get_animation_speed(clip_id),
			"loop_mode": sprite_frames.get_animation_loop_mode(clip_id)}
		if count != frame_ids.size() or sprite_frames.get_animation_speed(clip_id) != float(record["fps"]) or sprite_frames.get_animation_loop_mode(clip_id) != SpriteFrames.LOOP_LINEAR:
			_errors.append("clip 帧数、速度或循环方式不符：" + clip_id)
			continue
		for index in range(count):
			var region := sprite_frames.get_frame_texture(clip_id, index) as AtlasTexture
			var expected_rect := Rect2(_coordinate(_frames[frame_ids[index]]) * FRAME_SIZE, FRAME_SIZE)
			if region == null or region.atlas == null:
				_errors.append("动画帧没有引用有效 AtlasTexture：%s / %d" % [clip_id, index])
				continue
			if region.atlas.resource_path != SHEET_PATH or Vector2i(region.atlas.get_size()) != SHEET_SIZE or region.region != expected_rect or region.margin != Rect2() or not region.filter_clip:
				_errors.append("AtlasTexture 引用、区域或裁剪边界不符：%s / %d" % [clip_id, index])
			if not is_equal_approx(sprite_frames.get_frame_duration(clip_id, index), 1.0):
				_errors.append("动画帧应使用等长 duration=1：%s / %d" % [clip_id, index])
	_observed["sprite_frames_clip_count"] = names.size()
	_observed["sprite_frames_frame_count"] = observed_frame_count
	_observed["clips"] = clips
	var packed := ResourceLoader.load(SANDBOX_PATH, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	if packed == null:
		_errors.append("动画审阅场景无法重载：" + SANDBOX_PATH)
		return
	var scene := packed.instantiate()
	var sprites := scene.find_children("*", "AnimatedSprite2D", true, false)
	if sprites.size() != 16:
		_errors.append("审阅场景需要 8 个原生及 8 个 2× AnimatedSprite2D。")
	for group_name in ["Native", "Double"]:
		var factor := 1 if group_name == "Native" else 2
		for direction in DIRECTIONS:
			for state in ["idle", "walk"]:
				var node_path: String = group_name + "/" + state.capitalize() + direction.capitalize()
				var sprite := scene.get_node_or_null(node_path) as AnimatedSprite2D
				if sprite == null:
					_errors.append("缺失方向预览：" + node_path)
					continue
				if sprite.sprite_frames == null or sprite.sprite_frames.resource_path != SPRITE_FRAMES_PATH:
					_errors.append("预览应共享外部 SpriteFrames：" + node_path)
				if sprite.centered or sprite.offset != -Vector2(FOOT_ANCHOR) or sprite.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST or sprite.scale != Vector2(factor, factor):
					_errors.append("预览的锚点、Nearest 或整数倍率不符：" + node_path)
				if sprite.animation != state + "_" + direction or sprite.autoplay != sprite.animation or sprite.flip_h or sprite.flip_v:
					_errors.append("预览应使用对应 clip 及实际方向图像：" + node_path)
	if not scene.find_children("*", "CollisionObject2D", true, false).is_empty() or not scene.find_children("*", "CollisionShape2D", true, false).is_empty():
		_errors.append("独立动画审阅场景不应包含碰撞或旧游戏角色。")
	_observed["sandbox_animated_sprite_count"] = sprites.size()
	scene.free()


func _verify_runtime_and_capture() -> void:
	var packed := ResourceLoader.load(SANDBOX_PATH, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	var scene := packed.instantiate()
	var sprites := scene.find_children("*", "AnimatedSprite2D", true, false)
	var playback := {}
	for sprite in sprites:
		var key := str(scene.get_path_to(sprite))
		playback[key] = {"visited": {0: true}, "previous_frame": 0, "wrap_count": 0, "transitions": []}
		# 捕捉引擎真实发出的帧变化；比低频轮询更能避免漏掉中间帧。
		sprite.frame_changed.connect(func(): _record_playback_frame(sprite, playback[key]))
	root.add_child(scene)
	# autoplay 在节点进入 SceneTree 后启动；0.8 秒覆盖 8 FPS 四帧的完整 0.5 秒循环。
	# AnimatedSprite2D 没有 advance() 方法，此处仅观察真实 SceneTree 时序。
	var started := Time.get_ticks_msec()
	await create_timer(0.8).timeout
	var elapsed := Time.get_ticks_msec() - started
	var walk_cycled := 0
	var idle_static := 0
	var clip_observations := {}
	for sprite in sprites:
		if not sprite.is_playing():
			_errors.append("autoplay 未实际启动：" + str(sprite.get_path()))
		var key := str(scene.get_path_to(sprite))
		var record: Dictionary = playback[key]
		var visited: Array = record["visited"].keys()
		visited.sort()
		clip_observations[key] = {"animation": str(sprite.animation), "visited_frames": visited,
			"wrap_3_to_0_count": record["wrap_count"], "transitions": record["transitions"]}
		if str(sprite.animation).begins_with("walk_"):
			if visited == [0, 1, 2, 3] and record["wrap_count"] >= 1:
				walk_cycled += 1
			else:
				_errors.append("行走动画未在实际播放中访问完整四帧及 3→0 回环：" + key)
		elif sprite.frame == 0 and visited == [0]:
			idle_static += 1
		else:
			_errors.append("单帧 idle 的帧索引不是 0。")
	_observed["runtime_walk_complete_cycle_count"] = walk_cycled
	_observed["runtime_idle_static_count"] = idle_static
	_observed["runtime_observation_ms"] = elapsed
	_observed["runtime_playback"] = clip_observations
	if not _screenshot_path.is_empty() and _errors.is_empty():
		# 渲染截图保留每个原生像素与整数 2× 像素；不缩放或改写 PNG。
		root.content_scale_size = PREVIEW_SIZE
		root.size = PREVIEW_SIZE
		await process_frame
		await RenderingServer.frame_post_draw
		var screenshot := root.get_texture().get_image()
		if DirAccess.make_dir_recursive_absolute(_screenshot_path.get_base_dir()) != OK or screenshot.save_png(_screenshot_path) != OK:
			_errors.append("真实 Godot 截图写入失败：" + _screenshot_path)
	root.remove_child(scene)
	scene.free()


func _record_playback_frame(sprite: AnimatedSprite2D, record: Dictionary) -> void:
	var previous := int(record["previous_frame"])
	var current := sprite.frame
	record["visited"][current] = true
	if current != previous:
		record["transitions"].append([previous, current])
		if previous == 3 and current == 0:
			record["wrap_count"] += 1
	record["previous_frame"] = current


func _base_report(status: String) -> Dictionary:
	return {"status": status, "engine": Engine.get_version_info(), "catalog": _catalog_path,
		"sprite_frames": SPRITE_FRAMES_PATH, "sandbox_scene": SANDBOX_PATH,
		"verify_only": _verify_only, "existing_scene_preserved": _scene_preserved,
		"native_frame_size": [FRAME_SIZE.x, FRAME_SIZE.y], "foot_anchor": [FOOT_ANCHOR.x, FOOT_ANCHOR.y],
		"timestamp_utc": Time.get_datetime_string_from_system(true), "observed": _observed,
		"scope": "原生 PNG 哈希与图集逐像素一致性、SpriteFrames 重载、8 clips、锚点、Nearest、1×/2× 场景及真实计时播放；美术与步态质量由独立美术验收判断。"}


func _write_report(report: Dictionary) -> void:
	var directory := ProjectSettings.globalize_path(_report_path.get_base_dir())
	if DirAccess.make_dir_recursive_absolute(directory) != OK:
		_errors.append("报告目录无法创建：" + directory)
		return
	var file := FileAccess.open(_report_path, FileAccess.WRITE)
	if file == null:
		_errors.append("报告写入失败：" + _report_path)
		return
	file.store_string(JSON.stringify(report, "\t") + "\n")


func _finish_failure() -> void:
	for message in _errors:
		push_error(message)
	var report := _base_report("GODOT_ROBOT_ANIMATION_FAILED")
	report["errors"] = Array(_errors)
	# 未完成输入只产生明确的失败报告，不会保存半套生产资源或成功标记。
	if not _report_path.is_empty():
		_write_report(report)
	quit(1)
