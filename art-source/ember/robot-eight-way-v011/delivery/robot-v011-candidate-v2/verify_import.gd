extends SceneTree
## 精简交付只改变资源路径；在真实Godot导入后核对112个裁切区域和动作参数。
func _initialize() -> void:
	call_deferred("_verify")

func _verify() -> void:
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://full-action-metadata.json"))
	var frames := load("res://assets/ember/robot_v011/robot_eight_way_v011.tres") as SpriteFrames
	var errors: Array = []
	var checked := 0
	if frames == null:
		push_error("Missing SpriteFrames"); quit(1); return
	if FileAccess.get_sha256("res://" + metadata.atlas) != metadata.atlas_sha256:
		errors.append("Atlas hash mismatch")
	for clip: Dictionary in metadata.clips:
		if frames.get_frame_count(clip.name) != clip.frames.size() or frames.get_animation_speed(clip.name) != clip.fps or frames.get_animation_loop(clip.name) != clip.loop:
			errors.append("Clip parameters: " + clip.name)
		for frame: Dictionary in clip.frames:
			var texture := frames.get_frame_texture(clip.name, int(frame.frame)) as AtlasTexture
			if texture == null:
				errors.append("Missing frame texture"); continue
			var actual := texture.get_image()
			var expected := Image.load_from_file(ProjectSettings.globalize_path("res://" + frame.file))
			actual.convert(Image.FORMAT_RGBA8)
			expected.convert(Image.FORMAT_RGBA8)
			if actual.get_size() != Vector2i(64,96) or actual.get_data() != expected.get_data() or FileAccess.get_sha256("res://" + frame.file) != frame.sha256:
				errors.append("Frame mismatch: " + frame.file)
			checked += 1
	var preview: Node = load("res://preview/preview_full_actions.tscn").instantiate()
	root.add_child(preview)
	await process_frame
	preview.queue_free()
	if checked != 112 or frames.get_animation_names().size() != 24: errors.append("Incomplete action set")
	var report := {"technical_checks": "PASS" if errors.is_empty() else "FAIL", "checked_frames": checked, "clips": frames.get_animation_names().size(), "atlas_sha256": metadata.atlas_sha256, "errors": errors, "actual_gpu_playback": "REUSED_UNCHANGED_C2_SOURCE_VALIDATION"}
	var output := FileAccess.open("res://evidence/runtime-import-validation.json", FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "\t", false, true) + "\n")
	print("FINAL_RUNTIME_IMPORT ", report.technical_checks, " frames=", checked)
	for error: String in errors: push_error(error)
	quit(0 if errors.is_empty() else 1)
