extends SceneTree
## 只跑独立冷资源导入与 W/E 定点属性。没有 GPU 截图或自然循环复跑。
var records: Array = []
func check(label: String, passed: bool) -> void:
	records.append({"check": label, "pass": passed})
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var args := OS.get_cmdline_user_args()
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var sf := load("res://robot_walk_batch_v011.tres") as SpriteFrames
	check("SpriteFrames loads", sf != null)
	if sf != null:
		check("16 clips: 8 walks + 8 single identity poses", sf.get_animation_names().size() == 16)
		var dependency_ok := true
		for dep: String in ResourceLoader.get_dependencies("res://robot_walk_batch_v011.tres"):
			dependency_ok = dependency_ok and FileAccess.file_exists(dep.get_slice("::", dep.get_slice_count("::")-1))
		check("external atlas dependency exists inside cold project", dependency_ok)
		for clip: Dictionary in spec.clips:
			var name := StringName(clip.name)
			check(String(name)+" fps/loop/frame count", sf.has_animation(name) and sf.get_frame_count(name)==clip.frames.size() and sf.get_animation_speed(name)==float(clip.fps) and sf.get_animation_loop(name)==bool(clip.loop))
			# 72个图集切片的CPU get_image读回；不渲染屏幕。
			for entry: Dictionary in clip.frames:
				var tex := sf.get_frame_texture(name, int(entry.frame)) as AtlasTexture
				var native := Image.load_from_file(entry.absolute_file)
				var region := Rect2(float(entry.region[0]),float(entry.region[1]),float(entry.region[2]),float(entry.region[3]))
				var exact := tex!=null and tex.region==region and sf.get_frame_duration(name,int(entry.frame))==1.0
				if exact:
					var imported := tex.atlas.get_image().get_region(Rect2i(region))
					exact = imported.get_data()==native.get_data()
				check(String(name)+" f%d imported region RGBA"%int(entry.frame),exact)
	var scene := load("res://preview_walk_batch.tscn") as PackedScene
	check("review scene loads", scene != null)
	if scene != null:
		var preview := scene.instantiate()
		root.add_child(preview)
		await process_frame
		await process_frame
		check("scene root/Nearest", preview.robot.centered==false and preview.robot.offset==Vector2(-32,-80) and preview.robot.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST)
		check("native/4x preview scale",preview.robot.scale==Vector2(4,4) and preview.native_robot.scale==Vector2.ONE)
		preview.paused=true
		preview.robot.pause()
		preview.native_robot.pause()
		preview.robot.set_frame_and_progress(3,0.0)
		preview.direction="right"
		preview._apply_clip()
		check("W to E pause retains f03",preview.robot.animation=="walk_right" and preview.robot.frame==3 and preview.native_robot.frame==3 and not preview.robot.is_playing())
		preview.direction="left"
		preview._apply_clip()
		check("E to W pause retains f03",preview.robot.animation=="walk_left" and preview.robot.frame==3 and preview.native_robot.frame==3 and not preview.robot.is_playing())
		preview.queue_free()
	var failed := records.filter(func(r): return not r["pass"])
	var report := {"status":"PASS" if failed.is_empty() else "FAIL", "scope":"TA independent headless cold SpriteFrames/imported atlas CPU RGBA, scene root/filter and W/E f03 only; no GPU framebuffer, natural two loops, or 64 direction suite", "engine":Engine.get_version_info()["string"], "display_server":DisplayServer.get_name(), "checks":records,"passed":records.size()-failed.size(),"total":records.size(),"failed":failed}
	FileAccess.open(args[1],FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("TA_ROBOT_B2_COLD ",report.status," ",report.passed,"/",report.total)
	quit(0 if failed.is_empty() else 1)
