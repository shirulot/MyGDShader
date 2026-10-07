extends SceneTree
## 对本次修改的32张采集帧执行实际1×/4×GPU检查，并播放八向采集回待机。
var errors: Array = []
var samples: Array = []
var recoveries: Array = []
var active_clip := ""
var sequence: Array = []
var finished := 0
var robot: AnimatedSprite2D
var native: AnimatedSprite2D

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("GPU validation needs a display renderer"); quit(1); return
	var scene: Node = load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	root.add_child(scene)
	await process_frame
	robot = scene.get("robot") as AnimatedSprite2D
	native = scene.get("native") as AnimatedSprite2D
	robot.frame_changed.connect(func():
		if robot.animation == active_clip and (sequence.is_empty() or sequence[-1] != robot.frame): sequence.append(robot.frame))
	robot.animation_finished.connect(func(): finished += 1)
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://full-action-metadata.json"))
	for direction_index in range(8):
		var direction: String = metadata.directions[direction_index]
		robot.pause(); native.pause()
		scene.call("set_direction", direction_index)
		scene.call("play_action", "collect")
		robot.pause(); native.pause()
		for frame_index in range(4):
			robot.frame = frame_index; native.frame = frame_index
			await process_frame
			await RenderingServer.frame_post_draw
			var screenshot := root.get_texture().get_image()
			screenshot.convert(Image.FORMAT_RGBA8)
			var source := Image.load_from_file(ProjectSettings.globalize_path("res://frames/collect/%s/robot_collect_%s_f%02d_v013.png" % [direction,direction,frame_index]))
			source.convert(Image.FORMAT_RGBA8)
			for sprite: AnimatedSprite2D in [robot,native]:
				var check := _compare(screenshot,source,sprite)
				check.direction=direction; check.frame=frame_index; samples.append(check)
				if check.mismatched_pixels: errors.append("GPU mismatch: %s F%d scale%d" % [direction,frame_index,check.scale])
		active_clip = "collect_" + direction; sequence=[0]; finished=0
		scene.call("play_action", "collect")
		scene.call("set_direction", (direction_index+1)%8)
		var locked: bool = scene.get("direction_index") == direction_index
		await create_timer(0.79).timeout
		var recovered: bool = robot.animation == "idle_"+direction and native.animation == "idle_"+direction and robot.frame==0 and native.frame==0
		var fixed: bool = robot.position==Vector2(430,490) and native.position==Vector2(800,365)
		recoveries.append({"direction":direction,"sequence":sequence.duplicate(),"finished":finished,"direction_locked":locked,"idle0":recovered,"roots_fixed":fixed})
		if sequence != [0,1,2,3] or finished!=1 or not recovered or not locked or not fixed: errors.append("Collection recovery: "+direction)
	var report := {"technical_checks":"PASS" if errors.is_empty() else "FAIL","gpu":RenderingServer.get_video_adapter_name(),"samples":samples,"recoveries":recoveries,"errors":errors,"scope":"32 changed-action frames at 1x/4x and eight single-shot completions; visual acceptance separate"}
	var out := FileAccess.open("res://evidence/collect-gpu-validation.json",FileAccess.WRITE)
	out.store_string(JSON.stringify(report,"\t",false,true)+"\n")
	print("COLLECT_GPU ",report.technical_checks," samples=",samples.size()," recoveries=",recoveries.size())
	for error: String in errors: push_error(error)
	quit(0 if errors.is_empty() else 1)

func _compare(screen: Image, source: Image, sprite: AnimatedSprite2D) -> Dictionary:
	var scale_pixels := int(sprite.scale.x)
	var origin := Vector2i(sprite.position+sprite.offset*sprite.scale)
	var checked := 0
	var mismatches := 0
	for y in range(96):
		for x in range(64):
			var expected := source.get_pixel(x,y)
			if expected.a == 0: continue
			for dy in range(scale_pixels):
				for dx in range(scale_pixels):
					checked += 1
					if screen.get_pixel(origin.x+x*scale_pixels+dx,origin.y+y*scale_pixels+dy).to_rgba32()!=expected.to_rgba32(): mismatches+=1
	return {"scale":scale_pixels,"checked_pixels":checked,"mismatched_pixels":mismatches}
