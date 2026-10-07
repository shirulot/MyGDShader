extends SceneTree
## 独立实际播放审核：读取Godot导入后的SpriteFrames，固定整格读取GPU像素。
## 只验证运行资源与渲染一致性；动作/结构是否满意仍交给独立美术审阅。

const BASE := "art-source/ember/robot-fixed-rig-v009/"
const SIZE := Vector2i(64,96)
const ANCHOR := Vector2(32,80)
var workspace := ""
var frames: SpriteFrames
var source_images: Array[Image] = []
var source_hashes := {}
var errors: Array = []
var entries: Array = []
var played: Array = []
var loops := 0
var playback_start := 0
var imported_regions: Array = []

func _initialize() -> void: call_deferred("_run")
func _abs(file: String) -> String: return workspace.path_join(file.trim_prefix("res://"))
func _save(image: Image,file: String) -> void:
	DirAccess.make_dir_recursive_absolute(_abs(file).get_base_dir())
	image.save_png(_abs(file))
func _write(file: String,value: Dictionary) -> void:
	var output := FileAccess.open(_abs(file),FileAccess.WRITE)
	output.store_string(JSON.stringify(value,"\t",false,true)+"\n")

func _run() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--workspace="): workspace=arg.trim_prefix("--workspace=")
	if workspace.is_empty() or DisplayServer.get_name()=="headless": push_error("需要独立GPU工程及--workspace"); quit(1); return
	frames=load("res://robot_sprite_frames_v009.tres") as SpriteFrames
	if frames==null: push_error("SpriteFrames未正确导入"); quit(1); return
	if frames.get_animation_names()!=PackedStringArray(["walk_down"]) or frames.get_frame_count("walk_down")!=8 or frames.get_animation_speed("walk_down")!=8 or not frames.get_animation_loop("walk_down"):
		errors.append("SpriteFrames clips/count/FPS/loop错误")
	for index in 8:
		var file:=BASE+"frames/robot_walk_down_f%02d_v009.png"%index
		var image:=Image.load_from_file(_abs(file)); image.convert(Image.FORMAT_RGBA8); source_images.append(image)
		source_hashes[file]=FileAccess.get_sha256(_abs(file))
		var texture:=frames.get_frame_texture("walk_down",index) as AtlasTexture
		if texture==null or texture.region!=Rect2(index*64,0,64,96): errors.append("AtlasTexture region错误: "+str(index))
		else:
			# AtlasTexture.get_image在当前引擎返回底图；明确按登记region取格，而非bbox。
			var imported_atlas:=texture.atlas.get_image(); imported_atlas.convert(Image.FORMAT_RGBA8)
			var imported_frame:=imported_atlas.get_region(Rect2i(texture.region))
			var exact:=_same(imported_frame,image)
			imported_regions.append({"frame":index,"atlas_image_size":[imported_atlas.get_width(),imported_atlas.get_height()],"registered_region":[index*64,0,64,96],"rgba_exact":exact})
			if not exact: errors.append("实际导入AtlasTexture登记region与原生PNG不一致: "+str(index))
	source_hashes[BASE+"source/rig_down_v009.json"]=FileAccess.get_sha256(_abs(BASE+"source/rig_down_v009.json"))
	source_hashes[BASE+"robot_walk_down_atlas_v009.png"]=FileAccess.get_sha256(_abs(BASE+"robot_walk_down_atlas_v009.png"))
	source_hashes[BASE+"godot-review/assets/robot_walk_down_atlas_v009.png"]=FileAccess.get_sha256("res://assets/robot_walk_down_atlas_v009.png")
	source_hashes[BASE+"godot-review/robot_sprite_frames_v009.tres"]=FileAccess.get_sha256("res://robot_sprite_frames_v009.tres")
	for index in 8:
		for scale in [1,4]:
			var image:=await _capture(index,scale)
			var exact:=_same_scaled(image,source_images[index],scale)
			var file:=BASE+"gpu-playback/robot_walk_down_f%02d_%dx_v009.png"%[index,scale]
			_save(image,file)
			var entry:={"frame":index,"scale":scale,"file":file,"sha256":FileAccess.get_sha256(_abs(file)),"rgba_exact_to_native_png":exact,"size":[image.get_width(),image.get_height()]}
			entries.append(entry)
			if not exact: errors.append("实际GPU SpriteFrames读取与源PNG不一致: f%d/%dx"%[index,scale])
	for scale in [1,4]:
		var board:=await _capture_board(scale)
		_save(board,BASE+"gpu-playback/walk_down_board_%dx_v009.png"%scale)
	await _timed_playback()
	var visited:=[]
	for item: Dictionary in played:
		if not item.frame in visited: visited.append(item.frame)
	if visited!=[0,1,2,3,4,5,6,7] or loops<2: errors.append("实际AnimatedSprite2D未完整播放两次循环")
	for i in range(1,played.size()):
		if int(played[i].frame)!=(int(played[i-1].frame)+1)%8: errors.append("实际播放顺序不连续")
	for file: String in source_hashes:
		if FileAccess.get_sha256(_abs(file))!=source_hashes[file]: errors.append("审核期间资源改变: "+file)
	_write(BASE+"fixed_rig_playback_v009.json",{"status":"CANDIDATE","technical_checks":"PASS" if errors.is_empty() else "FAIL","errors":errors,
		"source_hashes":source_hashes,"verifier_sha256":FileAccess.get_sha256(get_script().resource_path),"engine":Engine.get_version_info(),
		"gpu_renderer":RenderingServer.get_video_adapter_name(),"canvas":[64,96],"root_anchor":[32,80],"frame_count":8,"fps":8,"loop":true,
		"imported_atlas_regions":imported_regions,"gpu_entries":entries,"gpu_cases":entries.size(),"playback":{"kind":"actual_timed_AnimatedSprite2D_signals","sequence":played,"visited_frames":visited,"actual_loops":loops},
		"art_acceptance":"NOT_CLAIMED","old_assets_changed":false})
	print("FIXED_RIG_PLAYBACK_V009 CANDIDATE technical=", "PASS" if errors.is_empty() else "FAIL", " cases=",entries.size()," loops=",loops)
	for error: String in errors: push_error(error)
	quit(0 if errors.is_empty() else 1)

func _viewport(size: Vector2i) -> SubViewport:
	var viewport:=SubViewport.new(); viewport.size=size; viewport.transparent_bg=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS; viewport.msaa_2d=Viewport.MSAA_DISABLED
	viewport.canvas_item_default_texture_filter=Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	root.add_child(viewport); return viewport

func _sprite(index: int,scale: int) -> AnimatedSprite2D:
	var sprite:=AnimatedSprite2D.new(); sprite.sprite_frames=frames; sprite.animation="walk_down"; sprite.frame=index
	sprite.centered=false; sprite.offset=-ANCHOR; sprite.position=ANCHOR*scale; sprite.scale=Vector2.ONE*scale
	sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var material:=CanvasItemMaterial.new(); material.light_mode=CanvasItemMaterial.LIGHT_MODE_UNSHADED; sprite.material=material
	return sprite

func _read(viewport: SubViewport) -> Image:
	await process_frame; await process_frame; await RenderingServer.frame_post_draw
	var image:=viewport.get_texture().get_image(); image.convert(Image.FORMAT_RGBA8)
	root.remove_child(viewport); viewport.free(); return image

func _capture(index: int,scale: int) -> Image:
	var viewport:=_viewport(SIZE*scale); viewport.add_child(_sprite(index,scale)); return await _read(viewport)

func _capture_board(scale: int) -> Image:
	var viewport:=_viewport(Vector2i(512,96)*scale)
	for index in 8:
		var sprite:=_sprite(index,scale); sprite.position.x+=index*64*scale; viewport.add_child(sprite)
	return await _read(viewport)

func _timed_playback() -> void:
	var viewport:=_viewport(SIZE); var sprite:=_sprite(0,1); viewport.add_child(sprite)
	playback_start=Time.get_ticks_msec(); played.append({"frame":0,"elapsed_ms":0})
	sprite.frame_changed.connect(func(): played.append({"frame":sprite.frame,"elapsed_ms":Time.get_ticks_msec()-playback_start}))
	sprite.animation_looped.connect(func(): loops+=1)
	sprite.play("walk_down")
	await create_timer(2.2).timeout
	# pause保留最终自然帧；stop会重置到F00并发出非计时播放的frame_changed。
	sprite.pause(); root.remove_child(viewport); viewport.free()

func _same(first: Image,second: Image) -> bool:
	first.convert(Image.FORMAT_RGBA8); second.convert(Image.FORMAT_RGBA8)
	return first.get_size()==second.get_size() and first.get_data()==second.get_data()

func _same_scaled(image: Image,source: Image,scale: int) -> bool:
	if image.get_size()!=source.get_size()*scale: return false
	for y in image.get_height():
		for x in image.get_width():
			if image.get_pixel(x,y)!=source.get_pixel(x/scale,y/scale): return false
	return true
