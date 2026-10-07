extends SceneTree
## 使用同一个 AnimatedSprite2D 切换相邻方向，验证索引/锚点和实际 GPU 画面。
## 此记录保证换向没有错格；投影和动作是否自然仍由成品视觉审查判断。
var metadata: Dictionary
var frames: SpriteFrames
var base := ""
var errors: Array = []
var records: Array = []

func _initialize() -> void: call_deferred("_run")

func _run() -> void:
	if DisplayServer.get_name()=="headless": quit(1); return
	base=ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	metadata=JSON.parse_string(FileAccess.get_file_as_string("res://walk-batch-metadata.json"))
	frames=load("res://robot_walk_batch_v011.tres") as SpriteFrames
	for i in metadata.direction_order.size():
		var before:String=metadata.direction_order[i]
		var after:String=metadata.direction_order[(i+1)%8]
		if not metadata.walk_directions.has(before) or not metadata.walk_directions.has(after): continue
		var sheet:=Image.create(512,192,false,Image.FORMAT_RGBA8)
		for phase in 8:
			var view:=SubViewport.new();view.size=Vector2i(64,96);view.transparent_bg=true
			view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
			root.add_child(view)
			var sprite:=AnimatedSprite2D.new();sprite.sprite_frames=frames;sprite.centered=false
			sprite.offset=Vector2(-32,-80);sprite.position=Vector2(32,80)
			sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
			var material:=CanvasItemMaterial.new();material.light_mode=CanvasItemMaterial.LIGHT_MODE_UNSHADED;sprite.material=material
			view.add_child(sprite)
			sprite.play("walk_"+before);sprite.frame=phase;sprite.pause()
			var first:=await _capture(view)
			# 与预览页相同：先保存原索引，换向后再显式恢复该步相。
			var previous:=sprite.frame
			sprite.play("walk_"+after);sprite.frame=previous;sprite.pause()
			var second:=await _capture(view)
			var expected:Image
			for clip:Dictionary in metadata.clips:
				if clip.name=="walk_"+after:
					expected=Image.load_from_file(base.path_join(clip.frames[phase].file));expected.convert(Image.FORMAT_RGBA8)
			var exact:=expected!=null and second.get_data()==expected.get_data()
			var phase_ok:=sprite.frame==phase and sprite.animation=="walk_"+after
			if not exact or not phase_ok: errors.append("direction transition mismatch: "+before+"/"+after+"/"+str(phase))
			records.append({"from":before,"to":after,"phase":phase,"phase_preserved":phase_ok,"gpu_rgba_exact":exact})
			sheet.blit_rect(first,Rect2i(0,0,64,96),Vector2i(phase*64,0))
			sheet.blit_rect(second,Rect2i(0,0,64,96),Vector2i(phase*64,96))
			view.free()
		sheet.resize(2048,768,Image.INTERPOLATE_NEAREST)
		var folder:=base.path_join("gpu-walk-playback/transitions")
		DirAccess.make_dir_recursive_absolute(folder)
		sheet.save_png(folder.path_join(before+"_to_"+after+"_same_phase_4x.png"))
	var report:={"technical_checks":"PASS" if errors.is_empty() else "FAIL","atlas_sha256":metadata.atlas_sha256,"cases":records,"errors":errors,"art_acceptance":"NOT_CLAIMED"}
	var out:=FileAccess.open(base.path_join("qa/godot_walk_transitions_v011.json"),FileAccess.WRITE)
	out.store_string(JSON.stringify(report,"\t",false,true)+"\n")
	print("WALK_TRANSITIONS ",report.technical_checks," cases=",records.size())
	quit(0 if errors.is_empty() else 1)

func _capture(view:SubViewport)->Image:
	await process_frame;await process_frame;await RenderingServer.frame_post_draw
	var image:=view.get_texture().get_image();image.convert(Image.FORMAT_RGBA8);return image
