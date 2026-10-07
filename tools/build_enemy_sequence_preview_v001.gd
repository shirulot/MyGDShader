extends SceneTree
## 复制导出资源到隔离工程，再检验 SpriteFrames 并拍摄真实 Godot 播放。
## 本脚本不修改主 project.godot，也不装配敌人 AI、伤害或碰撞。
## 独立工程 --script <本脚本绝对路径> -- --workspace=<工作区> --assemble
## 导入：Godot --headless --editor --path <preview-project> --quit
## 验证：同上 --script <本脚本> -- --workspace=<工作区> --validate
## GPU：省略 --headless，-- --workspace=<工作区> --capture

const RESOURCE_ROOT := "res://assets/ember/characters/enemies_v001/"
const CATALOG_NAME := "sequence_catalog_v001.json"
const SCENE := "res://scenes/enemy_sequences_review_v001.tscn"
var workspace := ""
var source_dir := ""
var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	workspace = _argument("workspace", ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir().get_base_dir().get_base_dir().get_base_dir()).replace("\\", "/").trim_suffix("/")
	source_dir = workspace + "/art-source/ember/enemy-sequences-v001/"
	if "--assemble" in OS.get_cmdline_user_args():
		_assemble()
		quit(0 if failures.is_empty() else 1)
		return
	if not FileAccess.file_exists(RESOURCE_ROOT + CATALOG_NAME):
		push_error("Run --assemble first, then import the isolated preview project.")
		quit(1)
		return
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RESOURCE_ROOT + CATALOG_NAME))
	var validation := _validate(catalog)
	_write_json(source_dir + "qa/sequence_resource_validation_v001.json", validation)
	if "--validate" in OS.get_cmdline_user_args():
		print("ENEMY_RESOURCE_VALIDATION_", validation.status)
		quit(0 if failures.is_empty() else 1)
		return
	if not "--capture" in OS.get_cmdline_user_args():
		push_error("Choose --assemble, --validate, or --capture.")
		quit(1)
		return
	if DisplayServer.get_name() == "headless":
		push_error("--capture requires an actual GPU renderer; do not use --headless.")
		quit(1)
		return
	await _capture(catalog, validation)
	quit(0 if failures.is_empty() else 1)


func _assemble() -> void:
	var asset_source := workspace + "/assets/ember/characters/enemies_v001/"
	if not FileAccess.file_exists(asset_source + CATALOG_NAME):
		failures.append("Export a batch before assembling the preview project.")
		return
	var destination := ProjectSettings.globalize_path(RESOURCE_ROOT)
	# 场景只依赖本独立工程中的控制器与复制的正式资源路径。
	var scene_text := '[gd_scene load_steps=2 format=3]\n\n[ext_resource type="Script" path="res://enemy_preview_controller.gd" id="1_controller"]\n\n[node name="EnemySequenceReview" type="Node2D"]\ntexture_filter = 1\nscript = ExtResource("1_controller")\n'
	_write_text(ProjectSettings.globalize_path(SCENE), scene_text)
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(asset_source + CATALOG_NAME))
	var output := {"status": "PASS" if failures.is_empty() else "FAIL", "scene": SCENE,
		"preview_project": ProjectSettings.globalize_path("res://project.godot"),
		"copied_asset_root": destination, "clips_available": catalog.clips.size(),
		"main_project_modified": false, "source_rgba_edited": false,
		"controls": {"Space": "pause/resume", "R": "restart clips", "B": "industrial/black/white background", "Escape": "close preview"},
		"failures": failures}
	_build_frame_contacts(catalog, asset_source)
	_build_html(catalog, asset_source)
	_copy_directory(asset_source, destination)
	output["status"] = "PASS" if failures.is_empty() else "FAIL"
	output["frame_contacts_report"] = source_dir + "qa/sequence_frame_contacts_v001.json"
	output["html_player"] = source_dir + "previews/enemy_sequences_player_v001.html"
	_write_json(source_dir + "qa/sequence_preview_assembly_v001.json", output)
	print("ENEMY_PREVIEW_ASSEMBLY_", output.status, " ", catalog.clips.size(), " clips")


func _validate(catalog: Dictionary) -> Dictionary:
	var records: Array = []
	if ProjectSettings.has_setting("autoload/Game"):
		failures.append("Preview project must not load the main Game autoload.")
	for unit: Dictionary in catalog.unit_resources:
		var frames := load(str(unit.sprite_frames)) as SpriteFrames
		var packed := load(str(unit.scene)) as PackedScene
		if frames == null or packed == null:
			failures.append("Cannot load imported SpriteFrames/scene: " + str(unit.unit_id))
			continue
		var sprite := packed.instantiate() as AnimatedSprite2D
		if sprite == null:
			failures.append("Reusable scene root must be AnimatedSprite2D.")
			continue
		if sprite.centered or sprite.offset != Vector2(-64, -104) or sprite.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST:
			failures.append("Fixed pivot/nearest scene properties mismatch: " + str(unit.unit_id))
		for clip: Dictionary in catalog.clips:
			if str(clip.unit_id) != str(unit.unit_id) or str(clip.technical_status) != "PASS":
				continue
			var animation := str(clip.animation)
			if FileAccess.get_sha256(str(clip.atlas)) != str(clip.atlas_sha256):
				failures.append("Preview atlas differs from exported catalog SHA256: " + str(clip.id))
			if not frames.has_animation(animation):
				failures.append("Missing animation " + animation)
				continue
			var count := frames.get_frame_count(animation)
			var fps := frames.get_animation_speed(animation)
			var looping := frames.get_animation_loop(animation)
			if count != int(clip.frame_count) or not is_equal_approx(fps, float(clip.fps)) or looping != bool(clip.loop):
				failures.append("Frame count/FPS/loop mismatch for " + str(clip.id))
			for index in range(count):
				var texture := frames.get_frame_texture(animation, index)
				if texture == null or texture.get_size() != Vector2(128, 128):
					failures.append("Missing or wrong fixed canvas texture: " + str(clip.id) + " f" + str(index))
			records.append({"clip_id": clip.id, "animation": animation, "frames": count, "fps": fps, "loop": looping, "canvas_px": [128, 128], "pivot_px": [64, 104]})
		sprite.free()
	return {"status": "PASS" if failures.is_empty() else "FAIL", "engine": Engine.get_version_info().string,
		"catalog_sha256": FileAccess.get_sha256(RESOURCE_ROOT + CATALOG_NAME),
		"tool_sha256": FileAccess.get_sha256(workspace + "/tools/build_enemy_sequence_preview_v001.gd"),
		"controller_sha256": FileAccess.get_sha256("res://enemy_preview_controller.gd"),
		"visual_acceptance": "PENDING_ART_REVIEW", "checks": "Imported SpriteFrames count/FPS/loop; fixed canvas; reusable scene pivot/nearest; no Game autoload",
		"records": records, "failures": failures.duplicate()}


func _capture(catalog: Dictionary, validation: Dictionary) -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1536, 1024)
	viewport.disable_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var scene: Node2D = (load(SCENE) as PackedScene).instantiate()
	viewport.add_child(scene)
	var preview_dir := workspace + "/assets/ember/characters/enemies_v001/previews/"
	DirAccess.make_dir_recursive_absolute(preview_dir)
	var captures: Array = []
	var elapsed := 0.0
	for target_seconds: float in [0.04, 0.29, 0.59, 0.99, 1.49, 2.29, 3.49]:
		await create_timer(maxf(0.01, target_seconds - elapsed)).timeout
		await RenderingServer.frame_post_draw
		elapsed = target_seconds
		var image := viewport.get_texture().get_image()
		var name := "gpu_playback_%04dms_v001.png" % roundi(target_seconds * 1000)
		var path := preview_dir + name
		if image.save_png(path) != OK:
			failures.append("Cannot save GPU screenshot " + name)
		var shown: Array = []
		for sprite: AnimatedSprite2D in scene.get("sprites"):
			shown.append({"id": str(sprite.name), "animation": str(sprite.animation), "frame": sprite.frame, "frame_progress": sprite.frame_progress, "playing": sprite.is_playing()})
		captures.append({"requested_elapsed_seconds": target_seconds, "png": path, "sha256": FileAccess.get_sha256(path), "shown_frames": shown})
		if target_seconds == 0.29:
			image.save_png(preview_dir + "enemy_sequences_contact_sheet_v001.png")
	var playback: Dictionary = scene.get("playback_records")
	# 在同一实际帧停止播放，黑/白背景各拍一张，便于识别灰边或伪背景。
	# 改的只是预览 UI 背景，源 alpha 与贴图像素原封不动。
	scene.set("paused", true)
	for sprite: AnimatedSprite2D in scene.get("sprites"):
		sprite.pause()
	var alpha_background_captures: Array = []
	for mode: String in ["black", "white"]:
		scene.set("background_mode", mode)
		scene.queue_redraw()
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		var path := preview_dir + "gpu_alpha_" + mode + "_v001.png"
		if viewport.get_texture().get_image().save_png(path) != OK:
			failures.append("Cannot save alpha background capture " + mode)
		alpha_background_captures.append({"background": mode, "png": path, "sha256": FileAccess.get_sha256(path)})
	for record: Dictionary in playback.values():
		var expected_clip: Dictionary = {}
		for clip: Dictionary in catalog.clips:
			if str(clip.unit_id) == str(record.unit_id) and str(clip.animation) == str(record.animation):
				expected_clip = clip
				break
		var expected_count := int(expected_clip.get("frame_count", 0))
		record.frames_seen.sort()
		if record.frames_seen.size() != expected_count:
			failures.append("Actual playback did not visit every frame: " + str(record.unit_id) + " " + str(record.animation))
		if bool(expected_clip.get("loop", false)) and int(record.looped_count) < 1:
			failures.append("Expected looping clip did not emit animation_looped.")
		if not bool(expected_clip.get("loop", false)) and int(record.finished_count) < 1:
			failures.append("Expected one-shot clip did not emit animation_finished.")
	var report := {"status": "PASS" if failures.is_empty() else "FAIL", "visual_acceptance": "PENDING_ART_REVIEW",
		"catalog_sha256": FileAccess.get_sha256(RESOURCE_ROOT + CATALOG_NAME),
		"tool_sha256": FileAccess.get_sha256(workspace + "/tools/build_enemy_sequence_preview_v001.gd"),
		"controller_sha256": FileAccess.get_sha256("res://enemy_preview_controller.gd"),
		"engine": Engine.get_version_info().string, "renderer": RenderingServer.get_current_rendering_method(),
		"adapter": RenderingServer.get_video_adapter_name(), "capture_kind": "Actual Godot GPU SubViewport playing imported SpriteFrames and AnimatedSprite2D",
		"capture_canvas_px": [1536, 1024], "nearest_display_scale": 2,
		"one_shot_resource_looping": false, "one_shot_replays": "Preview controller only; death final frame holds 1.25 seconds",
		"resource_validation_status": validation.status, "captures": captures,
		"alpha_background_captures": alpha_background_captures,
		"playback_records": playback, "failures": failures}
	_write_json(source_dir + "qa/sequence_gpu_playback_v001.json", report)
	_write_json(preview_dir + "sequence_gpu_playback_v001.json", report)
	print("ENEMY_GPU_PLAYBACK_", report.status, " ", playback.size(), " clips")
	viewport.queue_free()
	await process_frame


func _build_html(catalog: Dictionary, asset_source: String) -> void:
	# 自包含浏览器播放器只复用导出的透明 atlas，保持 nearest；不生成美术帧。
	var clips: Array = []
	for clip: Dictionary in catalog.clips:
		if str(clip.technical_status) != "PASS":
			continue
		var item := clip.duplicate(true)
		var local_path := asset_source + str(clip.atlas).trim_prefix(RESOURCE_ROOT)
		item["image_data"] = "data:image/png;base64," + Marshalls.raw_to_base64(FileAccess.get_file_as_bytes(local_path))
		item.erase("frame_metrics")
		clips.append(item)
	var html := FileAccess.get_file_as_string("res://player_template.html")
	_write_text(source_dir + "previews/enemy_sequences_player_v001.html", html.replace("__CLIPS__", JSON.stringify(clips)))


func _build_frame_contacts(catalog: Dictionary, asset_source: String) -> void:
	## 完整联系图只排列已有 128×128 透明帧；未画标签、基线、阴影或新像素。
	## 五行依次待机、移动、攻击、受击、死亡，八列从 f00 开始；多余列透明。
	var preview_dir := asset_source + "previews/"
	DirAccess.make_dir_recursive_absolute(preview_dir)
	var actions := ["idle", "move", "attack", "hit", "death"]
	var sheets: Array = []
	var identity_checks := 0
	for unit: Dictionary in catalog.unit_resources:
		var contact := Image.create(8 * 128, 5 * 128, false, Image.FORMAT_RGBA8)
		contact.fill(Color.TRANSPARENT)
		var cells: Array = []
		for clip: Dictionary in catalog.clips:
			if str(clip.unit_id) != str(unit.unit_id) or str(clip.direction) != "down" or str(clip.technical_status) != "PASS":
				continue
			var row := actions.find(str(clip.action))
			var atlas_path := asset_source + str(clip.atlas).trim_prefix(RESOURCE_ROOT)
			var atlas := Image.load_from_file(atlas_path)
			atlas.convert(Image.FORMAT_RGBA8)
			for index in range(int(clip.frame_count)):
				var frame := atlas.get_region(Rect2i((index % int(clip.columns)) * 128, floori(float(index) / int(clip.columns)) * 128, 128, 128))
				var position := Vector2i(index * 128, row * 128)
				contact.blit_rect(frame, Rect2i(0, 0, 128, 128), position)
				if contact.get_region(Rect2i(position, Vector2i(128, 128))).get_data() != frame.get_data():
					failures.append("Contact sheet changed source RGBA: " + str(clip.id) + " f" + str(index))
				identity_checks += 1
				cells.append({"clip_id": clip.id, "action": clip.action, "frame": index, "row": row, "column": index,
					"region_1x_px": [position.x, position.y, 128, 128], "fps": clip.fps, "events": clip.frame_metrics[index].events,
					"source_atlas_sha256": clip.atlas_sha256})
		var stem := str(unit.unit_id) + "_all_frames_down_"
		var native_path := preview_dir + stem + "1x_v001.png"
		if contact.save_png(native_path) != OK:
			failures.append("Cannot save complete native contact sheet.")
		var enlarged: Image = contact.duplicate()
		enlarged.resize(contact.get_width() * 4, contact.get_height() * 4, Image.INTERPOLATE_NEAREST)
		var enlarged_path := preview_dir + stem + "4x_v001.png"
		if enlarged.save_png(enlarged_path) != OK:
			failures.append("Cannot save nearest x4 contact sheet.")
		sheets.append({"unit_id": unit.unit_id, "native": native_path, "native_sha256": FileAccess.get_sha256(native_path),
			"nearest_x4": enlarged_path, "nearest_x4_sha256": FileAccess.get_sha256(enlarged_path),
			"native_size_px": [1024, 640], "nearest_x4_size_px": [4096, 2560], "cells": cells})
		if str(unit.unit_id) == "enemy_patrol":
			var strip := contact.get_region(Rect2i(0, 128, 1024, 128))
			var strip_path := preview_dir + "enemy_patrol_move_down_strip_1x_v001.png"
			strip.save_png(strip_path)
			strip.resize(4096, 512, Image.INTERPOLATE_NEAREST)
			strip.save_png(preview_dir + "enemy_patrol_move_down_strip_4x_v001.png")
	var report := {"status": "PASS" if failures.is_empty() else "FAIL", "catalog_sha256": FileAccess.get_sha256(asset_source + CATALOG_NAME),
		"scope": "Complete down-direction fixed-canvas frame contacts; 5 action rows by 8 frame columns",
		"row_order": actions, "native_cell_px": [128, 128], "magnification": 4,
		"processing": "RGBA full fixed-cell arrangement; whole contact one nearest x4 resize only",
		"sprite_pixel_repaint_recolour_matte": "NONE", "exact_rgba_identity_checks": identity_checks,
		"sheets": sheets, "patrol_move_strip_native": preview_dir + "enemy_patrol_move_down_strip_1x_v001.png",
		"patrol_move_strip_x4": preview_dir + "enemy_patrol_move_down_strip_4x_v001.png", "failures": failures}
	_write_json(source_dir + "qa/sequence_frame_contacts_v001.json", report)
	_write_json(preview_dir + "sequence_frame_contacts_v001.json", report)


func _copy_directory(source: String, destination: String) -> void:
	DirAccess.make_dir_recursive_absolute(destination)
	var directory := DirAccess.open(source)
	if directory == null:
		failures.append("Cannot read asset directory: " + source)
		return
	directory.list_dir_begin()
	var name := directory.get_next()
	while not name.is_empty():
		if not name.begins_with(".") and not name.ends_with(".import"):
			if directory.current_is_dir():
				_copy_directory(source.path_join(name), destination.path_join(name))
			elif DirAccess.copy_absolute(source.path_join(name), destination.path_join(name)) != OK:
				failures.append("Cannot copy preview resource: " + name)
		name = directory.get_next()
	directory.list_dir_end()


func _argument(name: String, fallback: String) -> String:
	var args := OS.get_cmdline_user_args()
	for index in range(args.size()):
		if args[index].begins_with("--" + name + "="):
			return args[index].trim_prefix("--" + name + "=")
		if args[index] == "--" + name and index + 1 < args.size():
			return args[index + 1]
	return fallback


func _write_json(path: String, data: Variant) -> void:
	_write_text(path, JSON.stringify(data, "\t"))


func _write_text(path: String, content: String) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		failures.append("Cannot write " + path)
		return
	file.store_string(content)
	file.close()

