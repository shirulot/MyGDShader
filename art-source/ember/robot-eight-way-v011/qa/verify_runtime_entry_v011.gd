extends SceneTree
## 在新工程真正的main_scene运行：循环、切向、采集完成及主视口GPU像素。
var errors: Array = []
var idle_loops := 0
var walk_loops := 0
var collect_finished := 0
var collect_frames: Array = [0]
var robot: AnimatedSprite2D
var native: AnimatedSprite2D

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Actual GPU entry validation requires a display renderer"); quit(1); return
	var scene_path: String = ProjectSettings.get_setting("application/run/main_scene")
	var scene: Node = load(scene_path).instantiate()
	root.add_child(scene)
	await process_frame
	robot = scene.get("robot") as AnimatedSprite2D
	native = scene.get("native") as AnimatedSprite2D
	var root4 := robot.position
	var root1 := native.position
	robot.animation_looped.connect(func():
		if String(robot.animation).begins_with("idle_"): idle_loops += 1
		if String(robot.animation).begins_with("walk_"): walk_loops += 1)
	robot.frame_changed.connect(func():
		if robot.animation == "collect_down_right" and collect_frames[-1] != robot.frame: collect_frames.append(robot.frame))
	# 原场景的finished回调会先切到idle，因此此处只计事件，不依赖回调后的动画名。
	robot.animation_finished.connect(func(): collect_finished += 1)
	scene.call("set_direction", 7)
	scene.call("play_action", "idle")
	await create_timer(1.12).timeout
	scene.call("play_action", "walk")
	await create_timer(1.12).timeout
	var phase := robot.frame
	scene.call("set_direction", 6)
	var same_phase := robot.frame == phase and native.frame == phase and robot.animation == "walk_right"
	scene.call("set_direction", 7)
	scene.call("play_action", "collect")
	scene.call("set_direction", 6)
	var locked := int(scene.get("direction_index")) == 7 and robot.animation == "collect_down_right"
	await create_timer(0.22).timeout
	await RenderingServer.frame_post_draw
	var sample_frame := robot.frame
	var screenshot := root.get_texture().get_image()
	screenshot.convert(Image.FORMAT_RGBA8)
	screenshot.save_png("res://evidence/runtime-entry-collect.png")
	var source := Image.load_from_file(ProjectSettings.globalize_path("res://frames/collect/down_right/robot_collect_down_right_f%02d_v011.png" % sample_frame))
	source.convert(Image.FORMAT_RGBA8)
	var pixel_checks := [_compare_opaque(screenshot, source, robot), _compare_opaque(screenshot, source, native)]
	await create_timer(0.58).timeout
	var recovered := robot.animation == "idle_down_right" and native.animation == "idle_down_right" and robot.frame == 0 and native.frame == 0
	var roots_fixed := robot.position == root4 and native.position == root1
	if idle_loops < 1 or walk_loops < 1: errors.append("Natural loop missing")
	if not same_phase: errors.append("Direction change lost phase")
	if not locked: errors.append("Collection direction was not locked")
	if collect_frames != [0,1,2,3] or collect_finished != 1 or not recovered: errors.append("Collection recovery failed")
	if not roots_fixed: errors.append("Preview root moved")
	for check: Dictionary in pixel_checks:
		if check.mismatched_pixels != 0: errors.append("Actual entry GPU pixels differ")
	var report := {"technical_checks":"PASS" if errors.is_empty() else "FAIL", "main_scene":scene_path,
		"actual_gpu":RenderingServer.get_video_adapter_name(), "idle_loops":idle_loops, "walk_loops":walk_loops,
		"same_phase_direction_change":same_phase, "collect_direction_locked":locked, "collect_frames":collect_frames,
		"collect_finished_events":collect_finished, "both_sprites_recovered_idle0":recovered, "roots_fixed":roots_fixed,
		"sample_collect_frame":sample_frame, "gpu_opaque_pixel_checks":pixel_checks, "errors":errors}
	var output := FileAccess.open("res://evidence/runtime-entry-validation.json",FileAccess.WRITE)
	output.store_string(JSON.stringify(report,"\t",false,true)+"\n")
	print("RUNTIME_ENTRY ", report.technical_checks)
	for error: String in errors: push_error(error)
	quit(0 if errors.is_empty() else 1)

func _compare_opaque(screenshot: Image, source: Image, sprite: AnimatedSprite2D) -> Dictionary:
	var scale_pixels := int(sprite.scale.x)
	var origin := Vector2i(sprite.position + sprite.offset * sprite.scale)
	var checked := 0
	var mismatches := 0
	for y in range(96):
		for x in range(64):
			var expected := source.get_pixel(x,y)
			if expected.a == 0: continue
			for dy in range(scale_pixels):
				for dx in range(scale_pixels):
					checked += 1
					var actual := screenshot.get_pixel(origin.x+x*scale_pixels+dx,origin.y+y*scale_pixels+dy)
					if actual.to_rgba32() != expected.to_rgba32(): mismatches += 1
	return {"scale":scale_pixels,"checked_pixels":checked,"mismatched_pixels":mismatches}
