extends SceneTree
const Rig = preload("res://action_rig.gd")
func _initialize() -> void: call_deferred("run")

func run() -> void:
	var viewport:=SubViewport.new()
	viewport.size=Vector2i(128,128)
	viewport.transparent_bg=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var rig:=Rig.new()
	viewport.add_child(rig)
	await process_frame
	var frames:=SpriteFrames.new()
	frames.remove_animation("default")
	var catalog: Dictionary={"version":"v008","status":"PENDING_TA","source_sha256":FileAccess.get_sha256("res://source/canonical.png"),"rig_sha256":FileAccess.get_sha256("res://rig.json"),"canvas":[128,128],"root":[64,104],"actions":{}}
	for action: String in Rig.CLIPS:
		var definition: Dictionary=Rig.CLIPS[action]
		var count:int=definition.poses.size()
		var atlas:=Image.create(128*count,128,false,Image.FORMAT_RGBA8)
		atlas.fill(Color.TRANSPARENT)
		var records:Array=[]
		var frame_hashes:Array=[]
		var pixel_reports:Array=[]
		DirAccess.make_dir_recursive_absolute("res://output/"+action)
		frames.add_animation(action)
		frames.set_animation_speed(action,definition.fps)
		frames.set_animation_loop(action,definition.loop)
		for index in range(count):
			records.append(rig.pose_action(action,index))
			await process_frame
			await RenderingServer.frame_post_draw
			var frame:=viewport.get_texture().get_image()
			frame.convert(Image.FORMAT_RGBA8)
			frame=straight_rgba(frame)
			var path:="res://output/%s/f%02d.png"%[action,index]
			frame.save_png(path)
			frame_hashes.append(FileAccess.get_sha256(path))
			pixel_reports.append(pixels(frame))
			atlas.blit_rect(frame,Rect2i(0,0,128,128),Vector2i(index*128,0))
		var atlas_path:="res://output/%s_v008.png"%action
		atlas.save_png(atlas_path)
		var shared:=ImageTexture.create_from_image(atlas)
		for index in range(count):
			var texture:=AtlasTexture.new()
			texture.atlas=shared
			texture.region=Rect2(128*index,0,128,128)
			frames.add_frame(action,texture)
		# 联系图始终使用同一观察区域，资产位置不变。
		for background: String in ["black","white"]:
			var contact:=Image.create(88*count,80,false,Image.FORMAT_RGBA8)
			contact.fill(Color.BLACK if background=="black" else Color.WHITE)
			for index in range(count):
				contact.blend_rect(atlas,Rect2i(index*128+32,32,88,80),Vector2i(index*88,0))
			contact.save_png("res://qa/%s_%s_1x.png"%[action,background])
			contact.resize(count*352,320,Image.INTERPOLATE_NEAREST)
			contact.save_png("res://qa/%s_%s_4x.png"%[action,background])
		catalog.actions[action]={"fps":definition.fps,"loop":definition.loop,"frame_count":count,"atlas":atlas_path,"atlas_sha256":FileAccess.get_sha256(atlas_path),"frame_hashes":frame_hashes,"poses":records,"pixel_reports":pixel_reports}
	ResourceSaver.save(frames,"res://output/patrol_actions_v008.tres")
	FileAccess.open("res://output/catalog_v008.json",FileAccess.WRITE).store_string(JSON.stringify(catalog,"\t"))
	print("EXPORTED_PATROL_ATTACK_DEATH_V006")
	quit()

func straight_rgba(frame: Image) -> Image:
	for y in range(frame.get_height()):
		for x in range(frame.get_width()):
			var p:=frame.get_pixel(x,y)
			if p.a8==0: frame.set_pixel(x,y,Color.TRANSPARENT)
			elif p.a8<255: frame.set_pixel(x,y,Color(minf(p.r/p.a,1),minf(p.g/p.a,1),minf(p.b/p.a,1),p.a))
	return frame

func pixels(frame: Image) -> Dictionary:
	var partial:=0
	var visible:=0
	var edges:=0
	for y in range(128):
		for x in range(128):
			var alpha:=frame.get_pixel(x,y).a8
			if alpha>0:
				visible+=1
				if x==0 or x==127 or y==0 or y==127: edges+=1
			if alpha>0 and alpha<255: partial+=1
	return {"visible":visible,"partial_alpha":partial,"edge_pixels":edges,"bounds":str(frame.get_used_rect())}
