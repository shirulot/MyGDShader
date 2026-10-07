extends SceneTree
## TA 独立迁移探针：读真实主入口/已导入资源，证据输出到冷副本之外。
var errors: Array[String] = []
var collect_seen: Array[int] = []
var finished_count := 0
var loop_count := 0

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, description: String) -> void:
	if not ok: errors.append(description)

func run() -> void:
	check(DisplayServer.get_name() != "headless", "entry must use real display renderer")
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://full-action-metadata.json"))
	var frames := load("res://assets/ember/robot_v011/robot_eight_way_v011.tres") as SpriteFrames
	check(frames != null, "SpriteFrames loads through migrated path")
	var checked := 0
	var clip_count := 0
	for clip: Dictionary in metadata.clips:
		clip_count += 1
		check(frames.has_animation(clip.name), "missing animation " + clip.name)
		check(frames.get_frame_count(clip.name) == clip.frames.size(), "frame count " + clip.name)
		check(frames.get_animation_speed(clip.name) == clip.fps, "fps " + clip.name)
		check(frames.get_animation_loop(clip.name) == clip.loop, "loop " + clip.name)
		for f: Dictionary in clip.frames:
			var tex := frames.get_frame_texture(clip.name, int(f.frame)) as AtlasTexture
			var rect: Array = f.region
			check(tex.region == Rect2(rect[0], rect[1], rect[2], rect[3]), "region " + f.file)
			check(frames.get_frame_duration(clip.name, int(f.frame)) == 1.0, "duration " + f.file)
			var from_import := tex.get_image()
			var from_png := Image.load_from_file(ProjectSettings.globalize_path("res://" + f.file))
			from_import.convert(Image.FORMAT_RGBA8)
			from_png.convert(Image.FORMAT_RGBA8)
			check(from_import.get_size() == Vector2i(64, 96), "frame dimensions " + f.file)
			check(from_import.get_data() == from_png.get_data(), "import RGBA " + f.file)
			checked += 1
	check(checked == 112 and clip_count == 24 and frames.get_animation_names().size() == 24, "complete 24/112 resource")
	var main_path: String = ProjectSettings.get_setting("application/run/main_scene")
	check(main_path == "res://preview/preview_full_actions.tscn", "real migrated project entry")
	var scene: Node = load(main_path).instantiate()
	root.add_child(scene)
	await process_frame
	var large: AnimatedSprite2D = scene.get("robot")
	var native: AnimatedSprite2D = scene.get("native")
	var anchors: Array = [large.position, native.position]
	for sprite: AnimatedSprite2D in [large, native]:
		check(not sprite.centered and sprite.offset == Vector2(-32,-80), "foot anchor contract")
		check(sprite.texture_filter == CanvasItem.TEXTURE_FILTER_NEAREST, "nearest filter")
	check(large.scale == Vector2(4,4) and native.scale == Vector2(1,1), "preview display scales")
	large.animation_looped.connect(func(): loop_count += 1)
	# 等待真实动画信号；不以手动逐帧赋值冒充自然播放。
	scene.call("set_direction", 7)
	scene.call("play_action", "idle")
	await large.animation_looped
	var idle_loop_observed := loop_count == 1
	scene.call("play_action", "walk")
	await large.animation_looped
	var walk_loop_observed := loop_count == 2
	await large.frame_changed
	var prior_frame := large.frame
	scene.call("set_direction", 6)
	var frame_preserved := large.animation == "walk_right" and large.frame == prior_frame and native.frame == prior_frame
	large.animation_finished.connect(func(): finished_count += 1)
	large.frame_changed.connect(func():
		if large.animation == "collect_down_right" and (collect_seen.is_empty() or collect_seen[-1] != large.frame):
			collect_seen.append(large.frame))
	scene.call("set_direction", 7)
	scene.call("play_action", "collect")
	if collect_seen.is_empty(): collect_seen.append(0)
	scene.call("set_direction", 3)
	var locked := int(scene.get("direction_index")) == 7 and large.animation == "collect_down_right"
	while large.frame == 0:
		await large.frame_changed
	# 暂停当前真实采集帧，只为稳定本次迁移的单帧GPU读取；随后恢复自然完成。
	large.pause()
	native.pause()
	native.frame = large.frame
	var sample_frame := large.frame
	await process_frame
	await RenderingServer.frame_post_draw
	var gpu := root.get_texture().get_image()
	gpu.convert(Image.FORMAT_RGBA8)
	gpu.save_png("res://../technical-entry-collect.png")
	var png := Image.load_from_file(ProjectSettings.globalize_path("res://frames/collect/down_right/robot_collect_down_right_f%02d_v011.png" % sample_frame))
	png.convert(Image.FORMAT_RGBA8)
	var pixel_checks: Array = []
	for sprite: AnimatedSprite2D in [large,native]:
		var scale_factor := int(sprite.scale.x)
		var origin := Vector2i(sprite.position + sprite.offset * sprite.scale)
		var total := 0
		var mismatch := 0
		for y in range(96):
			for x in range(64):
				var expected := png.get_pixel(x,y)
				if expected.a == 0: continue
				for sy in range(scale_factor):
					for sx in range(scale_factor):
						total += 1
						if gpu.get_pixel(origin.x+x*scale_factor+sx,origin.y+y*scale_factor+sy).to_rgba32() != expected.to_rgba32(): mismatch += 1
		pixel_checks.append({"scale":scale_factor,"checked_opaque_pixels":total,"mismatches":mismatch})
		check(mismatch == 0, "actual entry GPU opaque colors")
	large.play()
	native.play()
	await large.animation_finished
	var recovery := large.animation == "idle_down_right" and native.animation == "idle_down_right" and large.frame == 0 and native.frame == 0
	var roots_fixed: bool = large.position == anchors[0] and native.position == anchors[1]
	check(idle_loop_observed and walk_loop_observed, "natural idle/walk loop")
	check(frame_preserved, "direction switch frame preserved")
	check(locked, "collect direction locked")
	check(collect_seen == [0,1,2,3] and finished_count == 1 and recovery, "natural collect once and idle0 recovery")
	check(roots_fixed, "root positions fixed")
	var result := {"status":"PASS" if errors.is_empty() else "FAIL","engine":Engine.get_version_info().string,"gpu":RenderingServer.get_video_adapter_name(),"display":DisplayServer.get_name(),"main_scene":main_path,"clips":clip_count,"frames_rgba_checked":checked,"natural_idle_loop":idle_loop_observed,"natural_walk_loop":walk_loop_observed,"direction_switch_frame_preserved":frame_preserved,"direction_switch_fractional_progress_checked":false,"collect_locked":locked,"collect_seen":collect_seen,"finished_events":finished_count,"both_idle0_recovered":recovery,"roots_fixed":roots_fixed,"node_positions":[[anchors[0].x,anchors[0].y],[anchors[1].x,anchors[1].y]],"sprite_offset":[-32,-80],"sample_frame":sample_frame,"gpu_checks":pixel_checks,"errors":errors}
	FileAccess.open("res://../technical-runtime-entry.json",FileAccess.WRITE).store_string(JSON.stringify(result,"\t")+"\n")
	print("TA_RUNTIME_ENTRY ",result.status," frames=",checked)
	for error in errors: push_error(error)
	quit(0 if errors.is_empty() else 1)
