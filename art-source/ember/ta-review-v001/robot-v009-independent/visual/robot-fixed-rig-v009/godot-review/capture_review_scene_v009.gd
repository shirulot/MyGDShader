extends SceneTree
## 截取真实候选播放场景；等待自然F03，再暂停保留证据。
var workspace := ""
func _initialize() -> void: call_deferred("_run")
func _run() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--workspace="): workspace=arg.trim_prefix("--workspace=")
	if workspace.is_empty() or DisplayServer.get_name()=="headless": push_error("需要--workspace及GPU窗口"); quit(1); return
	var scene:=load("res://preview_fixed_rig_v009.tscn") as PackedScene
	var preview:=scene.instantiate(); root.add_child(preview)
	var native_sprite: AnimatedSprite2D=preview.native_sprite
	if native_sprite==null: push_error("预览未成功加载独立资源"); quit(1); return
	while native_sprite.frame!=3: await native_sprite.frame_changed
	preview.native_sprite.pause(); preview.zoom_sprite.pause()
	await process_frame; await RenderingServer.frame_post_draw
	var image:=root.get_texture().get_image(); image.convert(Image.FORMAT_RGBA8)
	var file:=workspace.path_join("art-source/ember/robot-fixed-rig-v009/gpu-playback/review_scene_f03_v009.png")
	image.save_png(file)
	var report_file:=workspace.path_join("art-source/ember/robot-fixed-rig-v009/review_scene_capture_v009.json")
	var report:={"status":"CANDIDATE","kind":"actual_Godot_main_viewport_after_natural_frame_signal","actual_frame":native_sprite.frame,"canvas":[image.get_width(),image.get_height()],
		"file":file,"sha256":FileAccess.get_sha256(file),"capture_script_sha256":FileAccess.get_sha256(get_script().resource_path),
		"preview_script_sha256":FileAccess.get_sha256("res://preview_fixed_rig_v009.gd"),"spriteframes_sha256":FileAccess.get_sha256("res://robot_sprite_frames_v009.tres"),
		"engine":Engine.get_version_info(),"gpu_renderer":RenderingServer.get_video_adapter_name(),"art_acceptance":"NOT_CLAIMED"}
	var output:=FileAccess.open(report_file,FileAccess.WRITE); output.store_string(JSON.stringify(report,"\t",false,true)+"\n")
	print("REVIEW_SCENE_V009 actual_frame=",native_sprite.frame," size=",image.get_size()," sha256=",FileAccess.get_sha256(file))
	quit()
