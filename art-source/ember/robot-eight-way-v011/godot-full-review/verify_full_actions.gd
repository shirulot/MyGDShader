extends SceneTree
## 实际GPU检查112帧、自然循环、采集完成、相邻切向和同方向动作切换。
var frames: SpriteFrames
var metadata: Dictionary
var base := ""
var output_base := ""
var errors: Array = []
var cases: Array = []
var natural: Array = []
var transitions: Array = []
var recoveries: Array = []
var loops := 0
var sequence: Array = []

func _initialize() -> void: call_deferred("_run")

func _run() -> void:
	if DisplayServer.get_name() == "headless": push_error("GPU required"); quit(1); return
	base = ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	output_base = base
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output-root="): output_base = argument.trim_prefix("--output-root=")
	DirAccess.make_dir_recursive_absolute(output_base.path_join("qa"))
	metadata = JSON.parse_string(FileAccess.get_file_as_string("res://full-action-metadata.json"))
	frames = load("res://robot_eight_way_v011.tres") as SpriteFrames
	if frames == null: quit(1); return
	for clip: Dictionary in metadata.clips:
		if frames.get_frame_count(clip.name) != clip.frames.size() or frames.get_animation_speed(clip.name) != clip.fps or frames.get_animation_loop(clip.name) != clip.loop: errors.append("clip contract: " + clip.name)
		for frame: Dictionary in clip.frames:
			var expected := _source(frame.file)
			if FileAccess.get_sha256(base.path_join(frame.file)) != frame.sha256: errors.append("source hash: " + frame.file)
			for size in [1, 4]:
				var view := _view(Vector2i(64, 96) * size)
				view.add_child(_sprite(clip.name, int(frame.frame), size))
				var image := await _capture(view)
				view.free()
				var scaled := expected.duplicate() as Image
				scaled.resize(64 * size, 96 * size, Image.INTERPOLATE_NEAREST)
				var exact := image.get_data() == scaled.get_data()
				var file := "gpu-full-playback/%s_f%02d_%dx.png" % [clip.name, int(frame.frame), size]
				_save(image, file)
				cases.append({"clip": clip.name, "frame": frame.frame, "scale": size, "file": file, "rgba_exact": exact})
				if not exact: errors.append("GPU mismatch: " + file)
		if clip.loop: await _play_twice(clip)
		if clip.action == "collect": recoveries.append(await _collect_to_idle(clip.direction))
		print("VERIFIED ", clip.name)
	# 各动作的相邻45度切向覆盖每个相位；同时检查同方向动作切换后实际纹理。
	for i in range(metadata.directions.size()):
		var direction: String = metadata.directions[i]
		var next: String = metadata.directions[(i + 1) % metadata.directions.size()]
		for action in ["idle", "walk", "collect"]:
			var from: String = action + "_" + direction
			var to: String = action + "_" + next
			for phase in range(frames.get_frame_count(from)): await _switch(from, phase, to, phase)
		for pair in [["idle", "walk"], ["walk", "idle"], ["idle", "collect"]]:
			await _switch(pair[0] + "_" + direction, 0, pair[1] + "_" + direction, 0)
	var preview: Node = load("res://preview_full_actions.tscn").instantiate()
	root.add_child(preview)
	await process_frame
	preview.queue_free()
	var report := {"technical_checks": "PASS" if errors.is_empty() else "FAIL", "revision": metadata.revision,
		"atlas_sha256": FileAccess.get_sha256("res://assets/robot_eight_way_actions_atlas_v011.png"),
		"gpu": RenderingServer.get_video_adapter_name(), "cases": cases, "natural_playback": natural,
		"collect_to_idle": recoveries, "transitions": transitions, "errors": errors, "art_acceptance": "NOT_CLAIMED"}
	var file := FileAccess.open(output_base.path_join("qa/godot_full_actions_v011.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t", false, true) + "\n")
	print("FULL_ACTIONS ", report.technical_checks, " GPU=", cases.size(), " transitions=", transitions.size(), " recoveries=", recoveries.size())
	for error: String in errors: push_error(error)
	quit(0 if errors.is_empty() else 1)

func _source(file: String) -> Image:
	var image := Image.load_from_file(base.path_join(file))
	image.convert(Image.FORMAT_RGBA8)
	return image

func _view(size: Vector2i) -> SubViewport:
	var view := SubViewport.new()
	view.size = size
	view.transparent_bg = true
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	view.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	root.add_child(view)
	return view

func _sprite(clip: String, index: int, size: int) -> AnimatedSprite2D:
	var sprite := AnimatedSprite2D.new()
	sprite.sprite_frames = frames
	sprite.animation = clip
	sprite.frame = index
	sprite.centered = false
	sprite.offset = Vector2(-32, -80)
	sprite.position = Vector2(32, 80) * size
	sprite.scale = Vector2.ONE * size
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var material := CanvasItemMaterial.new()
	material.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	sprite.material = material
	return sprite

func _capture(view: SubViewport) -> Image:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var image := view.get_texture().get_image()
	image.convert(Image.FORMAT_RGBA8)
	return image

func _save(image: Image, file: String) -> void:
	var absolute := output_base.path_join(file)
	DirAccess.make_dir_recursive_absolute(absolute.get_base_dir())
	image.save_png(absolute)

func _play_twice(clip: Dictionary) -> void:
	var view := _view(Vector2i(64, 96))
	var sprite := _sprite(clip.name, 0, 1)
	view.add_child(sprite)
	loops = 0
	sequence = [0]
	sprite.animation_looped.connect(func(): loops += 1)
	sprite.frame_changed.connect(func(): sequence.append(sprite.frame))
	sprite.play()
	await create_timer(2.15).timeout
	sprite.pause()
	if loops < 2: errors.append("missing loops: " + clip.name)
	for i in range(1, sequence.size()):
		if sequence[i] != (sequence[i - 1] + 1) % clip.frames.size(): errors.append("frame order: " + clip.name)
	natural.append({"clip": clip.name, "loops": loops, "sequence": sequence.duplicate()})
	view.free()

func _collect_to_idle(direction: String) -> Dictionary:
	var collect := "collect_" + direction
	var idle := "idle_" + direction
	var view := _view(Vector2i(64, 96))
	var sprite := _sprite(collect, 0, 1)
	view.add_child(sprite)
	var finished: Array = []
	var seen: Array = [0]
	sprite.frame_changed.connect(func():
		if sprite.animation == collect: seen.append(sprite.frame))
	sprite.animation_finished.connect(func():
		if sprite.animation == collect:
			finished.append({"frame": sprite.frame, "clip": String(sprite.animation)})
			sprite.play(idle)
			sprite.frame = 0)
	sprite.play()
	await create_timer(.85).timeout
	sprite.pause()
	var image := await _capture(view)
	_save(image, "gpu-full-playback/collect_" + direction + "_finished_to_idle0.png")
	var expected := _source("frames/idle/%s/robot_idle_%s_f00_v011.png" % [direction, direction])
	var exact := image.get_data() == expected.get_data()
	var result := {"direction": direction, "finished_events": finished, "sequence": seen, "result_animation": String(sprite.animation), "result_frame": sprite.frame, "idle0_rgba_exact": exact}
	if finished.size() != 1 or seen != [0, 1, 2, 3] or sprite.animation != idle or sprite.frame != 0 or not exact: errors.append("collect recovery: " + direction)
	view.free()
	return result

func _switch(from: String, source_frame: int, to: String, target_frame: int) -> void:
	var view := _view(Vector2i(64, 96))
	var sprite := _sprite(from, source_frame, 1)
	view.add_child(sprite)
	await process_frame
	sprite.play(to)
	sprite.pause()
	sprite.frame = target_frame
	var image := await _capture(view)
	var target: Dictionary = {}
	for clip: Dictionary in metadata.clips:
		if clip.name == to: target = clip.frames[target_frame]; break
	var exact := image.get_data() == _source(target.file).get_data()
	transitions.append({"from": from, "from_frame": source_frame, "to": to, "to_frame": target_frame, "rgba_exact": exact, "root_unchanged": sprite.position == Vector2(32, 80)})
	if not exact: errors.append("transition: " + from + " -> " + to)
	view.free()
