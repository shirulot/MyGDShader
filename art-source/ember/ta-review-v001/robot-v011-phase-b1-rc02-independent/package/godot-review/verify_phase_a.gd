extends SceneTree
## 实际GPU + AnimatedSprite2D核对。技术一致性和自然播放证据不代替美术审查。
const SIZE := Vector2i(64,96)
const ANCHOR := Vector2(32,80)
var resource: SpriteFrames
var metadata: Dictionary
var source_root := ""
var errors: Array = []
var entries: Array = []
var playback: Array = []
var loops := 0
var signals: Array = []
var start_ms := 0

func _initialize() -> void: call_deferred("_run")

func _run() -> void:
	if DisplayServer.get_name()=="headless": push_error("此验证必须使用实际GPU");quit(1);return
	source_root=ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	metadata=JSON.parse_string(FileAccess.get_file_as_string("res://phase-a-metadata.json"))
	resource=load("res://robot_phase_a_v011.tres") as SpriteFrames
	if resource==null: push_error("SpriteFrames未导入");quit(1);return
	if resource.get_animation_names().size()!=metadata.clips.size():errors.append("clip count mismatch")
	for clip:Dictionary in metadata.clips:
		var name:String=clip.name
		if resource.get_frame_count(name)!=clip.frames.size() or resource.get_animation_speed(name)!=clip.fps or resource.get_animation_loop(name)!=clip.loop:
			errors.append("clip contract mismatch: "+name)
		for f:Dictionary in clip.frames:
			var source:=Image.load_from_file(source_root.path_join(f.file));source.convert(Image.FORMAT_RGBA8)
			if FileAccess.get_sha256(source_root.path_join(f.file))!=f.sha256:errors.append("source hash changed: "+f.file)
			var texture:=resource.get_frame_texture(name,int(f.frame)) as AtlasTexture
			var rect:=Rect2i(int(f.region[0]),int(f.region[1]),64,96)
			var imported:=texture.atlas.get_image();imported.convert(Image.FORMAT_RGBA8)
			if texture.region!=Rect2(rect) or imported.get_region(rect).get_data()!=source.get_data():errors.append("imported region mismatch: "+name+str(f.frame))
			for pixel_scale in [1,4]:
				var image:=await _capture(name,int(f.frame),pixel_scale)
				var expected:=source.duplicate() as Image;expected.resize(64*pixel_scale,96*pixel_scale,Image.INTERPOLATE_NEAREST)
				var exact:=image.get_data()==expected.get_data()
				var file:="gpu-playback/%s_f%02d_%dx.png"%[name,int(f.frame),pixel_scale]
				_save(image,file)
				entries.append({"clip":name,"frame":f.frame,"scale":pixel_scale,"file":file,"rgba_exact":exact})
				if not exact:errors.append("GPU RGBA mismatch: "+file)
		if clip.action=="walk":await _play_twice(name)
	await _direction_board()
	await _walk_phase_board()
	var report:={"technical_checks":"PASS" if errors.is_empty() else "FAIL","errors":errors,"engine":Engine.get_version_info(),"gpu":RenderingServer.get_video_adapter_name(),"scope":metadata.phase_scope,"atlas_sha256":FileAccess.get_sha256("res://assets/robot_phase_a_atlas_v011.png"),"cases":entries,"natural_playback":playback,"art_acceptance":"NOT_CLAIMED"}
	var out:=FileAccess.open(source_root.path_join("qa/godot_phase_a_v011.json"),FileAccess.WRITE);out.store_string(JSON.stringify(report,"\t",false,true)+"\n")
	print("ROBOT_V011_PHASE_A ",report.technical_checks," GPU cases=",entries.size()," natural clips=",playback.size())
	for error:String in errors:push_error(error)
	quit(0 if errors.is_empty() else 1)

func _view(size:Vector2i)->SubViewport:
	var view:=SubViewport.new();view.size=size;view.transparent_bg=true
	view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	view.canvas_item_default_texture_filter=Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	root.add_child(view);return view

func _sprite(clip:String,index:int,pixel_scale:int)->AnimatedSprite2D:
	var sprite:=AnimatedSprite2D.new();sprite.sprite_frames=resource;sprite.animation=clip;sprite.frame=index
	sprite.centered=false;sprite.offset=-ANCHOR;sprite.position=ANCHOR*pixel_scale;sprite.scale=Vector2.ONE*pixel_scale
	sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var material:=CanvasItemMaterial.new();material.light_mode=CanvasItemMaterial.LIGHT_MODE_UNSHADED;sprite.material=material
	return sprite

func _read(view:SubViewport)->Image:
	await process_frame;await process_frame;await RenderingServer.frame_post_draw
	var image:=view.get_texture().get_image();image.convert(Image.FORMAT_RGBA8)
	view.free();return image

func _capture(clip:String,index:int,pixel_scale:int)->Image:
	var view:=_view(SIZE*pixel_scale);view.add_child(_sprite(clip,index,pixel_scale));return await _read(view)

func _save(image:Image,file:String)->void:
	var absolute:=source_root.path_join(file);DirAccess.make_dir_recursive_absolute(absolute.get_base_dir());image.save_png(absolute)

func _play_twice(clip:String)->void:
	var view:=_view(SIZE);var sprite:=_sprite(clip,0,1);view.add_child(sprite)
	loops=0;signals=[{"frame":0,"elapsed_ms":0}];start_ms=Time.get_ticks_msec()
	sprite.frame_changed.connect(func():signals.append({"frame":sprite.frame,"elapsed_ms":Time.get_ticks_msec()-start_ms}))
	sprite.animation_looped.connect(func():loops+=1)
	sprite.play(clip);await create_timer(2.15).timeout;sprite.pause()
	if loops<2:errors.append("missing natural loops: "+clip)
	for i in range(1,signals.size()):
		if signals[i].frame!=(signals[i-1].frame+1)%8:errors.append("bad natural frame sequence: "+clip)
	playback.append({"clip":clip,"actual_loops":loops,"sequence":signals.duplicate(true)})
	view.free()

func _direction_board()->void:
	var view:=_view(Vector2i(1024,768))
	for i in metadata.direction_order.size():
		var sprite:=_sprite("pose_"+metadata.direction_order[i],0,4)
		sprite.position+=Vector2((i%4)*256,(i/4)*384)
		view.add_child(sprite)
	_save(await _read(view),"gpu-playback/direction_board_4x.png")

func _walk_phase_board()->void:
	var view:=_view(Vector2i(2048,768))
	for row in 2:
		for i in 8:
			var sprite:=_sprite("walk_down" if row==0 else "walk_down_left",i,4)
			sprite.position+=Vector2(i*256,row*384);view.add_child(sprite)
	_save(await _read(view),"gpu-playback/down_to_down_left_same_phase_4x.png")
