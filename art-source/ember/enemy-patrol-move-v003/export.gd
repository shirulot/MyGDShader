extends SceneTree
## 在真实 Godot 渲染器中拍摄固定部件场景，切图不作独立注册。
const Rig = preload("res://fixed_rig.gd")
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(128,128)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var rig := Rig.new()
	viewport.add_child(rig)
	await process_frame
	var records: Array = []
	var atlas := Image.create(1024,128,false,Image.FORMAT_RGBA8)
	atlas.fill(Color.TRANSPARENT)
	var frames := SpriteFrames.new()
	frames.remove_animation("default")
	frames.add_animation("move_down")
	frames.set_animation_speed("move_down",8)
	frames.set_animation_loop("move_down",true)
	for index in range(-1,8):
		if index < 0:
			rig.bind_pose()
		else:
			records.append(rig.pose(index))
		await process_frame
		await RenderingServer.frame_post_draw
		var frame := viewport.get_texture().get_image()
		frame.convert(Image.FORMAT_RGBA8)
		var path := "res://output/bind_pose.png" if index < 0 else "res://output/f%02d.png" % index
		frame.save_png(path)
		if index >= 0:
			atlas.blit_rect(frame,Rect2i(0,0,128,128),Vector2i(index*128,0))
		else:
			frame.resize(768,768,Image.INTERPOLATE_NEAREST)
			frame.save_png("res://qa/bind_pose_x6.png")
	atlas.save_png("res://output/move_down_v003.png")
	var enlarged := atlas.duplicate()
	enlarged.resize(4096,512,Image.INTERPOLATE_NEAREST)
	enlarged.save_png("res://qa/move_down_4x.png")
	var shared_atlas := ImageTexture.create_from_image(atlas)
	for index in range(8):
		var texture := AtlasTexture.new()
		texture.atlas = shared_atlas
		texture.region = Rect2(128*index,0,128,128)
		frames.add_frame("move_down",texture)
	ResourceSaver.save(frames,"res://output/patrol_move_frames_v003.tres")
	var report := {"version":"v003","status":"CANDIDATE_NOT_TA_APPROVED","canvas":[128,128],"root":[64,104],"fps":8,"loop":true,"frame_count":8,"source_sha256":FileAccess.get_sha256("res://source/canonical.png"),"rig_sha256":FileAccess.get_sha256("res://rig.json"),"atlas_sha256":FileAccess.get_sha256("res://output/move_down_v003.png"),"renderer":RenderingServer.get_video_adapter_name(),"poses":records,"limitations":["Source alpha retained; native polish pending","Part separation and joint overlap require visual review","No complete movement approval from numeric IK alone"]}
	FileAccess.open("res://output/catalog_v003.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("FIXED_RIG_EXPORTED_8_FRAMES")
	quit()
