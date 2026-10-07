extends SceneTree
## 截取真实候选播放场景；等待自然F03，再暂停保留证据。
var workspace := ""
func _initialize() -> void: call_deferred("_run")
func _run() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--workspace="): workspace=arg.trim_prefix("--workspace=")
	if workspace.is_empty() or DisplayServer.get_name()=="headless": push_error("需要--workspace及GPU窗口"); quit(1); return
	var scene:=load("res://preview_fixed_rig_v007.tscn") as PackedScene
	var preview:=scene.instantiate(); root.add_child(preview)
	var native_sprite: AnimatedSprite2D=preview.native_sprite
	while native_sprite.frame!=3: await native_sprite.frame_changed
	preview.native_sprite.pause(); preview.zoom_sprite.pause()
	await process_frame; await RenderingServer.frame_post_draw
	var image:=root.get_texture().get_image(); image.convert(Image.FORMAT_RGBA8)
	var file:=workspace.path_join("art-source/ember/robot-fixed-rig-v007/gpu-playback/review_scene_f03_v007.png")
	image.save_png(file)
	print("REVIEW_SCENE_V007 actual_frame=",native_sprite.frame," size=",image.get_size()," sha256=",FileAccess.get_sha256(file))
	quit()
