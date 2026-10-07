extends SceneTree
## 用引擎实际运行新版手工笔刷页并截图；检修口和贴花叠加在独立地板层。
func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1280,900)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var packed := load("res://scenes/ember/manual_brush_preview_v007.tscn") as PackedScene
	var scene := packed.instantiate() as Node2D
	viewport.add_child(scene)
	await process_frame
	assert(scene.entries.size() == 67)
	assert(scene.canvas.tile_set.tile_size == Vector2i(128,128))
	assert(scene.canvas.scale == Vector2.ONE*.25)
	# 预铺几个透明附件，核对完整 ID 与坐标能实际显示并正常擦除。
	for index in range(4,12):
		var entry: Dictionary = scene.entries[index]
		var cell := Vector2i(2+(index-4)%4*4,3+(index-4)/4*5)
		scene.canvas.set_cell(cell,entry.source,entry.coord)
		assert(scene.canvas.get_cell_tile_data(cell).get_custom_data("tile_id") == entry.id)
	scene.canvas.set_cell(Vector2i(0,0),0,Vector2i(4,0))
	scene.canvas.erase_cell(Vector2i(0,0))
	assert(scene.canvas.get_cell_source_id(Vector2i(0,0)) == -1)
	await process_frame
	await RenderingServer.frame_post_draw
	assert(viewport.get_texture().get_image().save_png("res://assets/ember/environment/tilesets_v007/godot_brush_preview.png") == OK)
	print("MANUAL_PREVIEW_RUNTIME_AND_RENDER_OK")
	quit()
