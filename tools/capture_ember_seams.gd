extends SceneTree
## GPU 实际渲染 TileMapLayer，独立于 CPU 拼图，验证导入和采样效果。
func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var revision := "v006" if "--revision=v006" in OS.get_cmdline_user_args() else "v005"
	if "--revision=v007" in OS.get_cmdline_user_args():
		revision = "v007"
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1280,1280)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var background := ColorRect.new()
	background.size = Vector2(1280,1280)
	background.color = Color("182631")
	viewport.add_child(background)
	var scene := load("res://scenes/ember/autotile_sandbox_" + revision + ".tscn").instantiate() as Node2D
	scene.set_meta("enable_zoom",false)
	scene.scale = Vector2.ONE*2
	viewport.add_child(scene)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var result := viewport.get_texture().get_image()
	assert(result.save_png("res://assets/ember/environment/autotiles_" + revision + "/godot_render.png") == OK)
	print("GPU_RENDER_SAVED")
	viewport.queue_free()
	quit()
