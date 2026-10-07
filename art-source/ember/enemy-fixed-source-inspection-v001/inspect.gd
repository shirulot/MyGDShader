extends SceneTree
## 只读母稿的Godot原生显示检查，不修改源PNG；供固定UV分区判读。
func _initialize()->void: call_deferred("run")
func run()->void:
	var viewport:=SubViewport.new()
	viewport.size=Vector2i(512,512)
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var backdrop:=ColorRect.new()
	backdrop.size=Vector2(512,512)
	backdrop.color=Color.WHITE
	viewport.add_child(backdrop)
	var sprite:=Sprite2D.new()
	sprite.centered=false
	sprite.scale=Vector2(4,4)
	sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var material:=ShaderMaterial.new()
	material.shader=load("res://entity_cutout.gdshader")
	sprite.material=material
	viewport.add_child(sprite)
	for unit:String in ["enemy_tracked_heavy","enemy_cutter","enemy_scout_drone"]:
		var path:=ProjectSettings.globalize_path("res://../enemy-sequences-v001/templates/%s_canonical_down_v001.png"%unit)
		sprite.texture=ImageTexture.create_from_image(Image.load_from_file(path))
		await process_frame
		await RenderingServer.frame_post_draw
		viewport.get_texture().get_image().save_png("res://%s_4x.png"%unit)
	quit()
