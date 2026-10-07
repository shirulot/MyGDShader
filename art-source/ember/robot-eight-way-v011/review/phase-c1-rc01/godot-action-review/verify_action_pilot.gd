extends SceneTree
## 用实际GPU验证小样，包含非循环采集结束事件与回idle；不修改主项目。
var frames:SpriteFrames
var metadata:Dictionary
var base:=""
var output_base:=""
var errors:Array=[]
var cases:Array=[]
var natural:Array=[]
var loops:=0
var sequence:Array=[]

func _initialize()->void:call_deferred("_run")

func _run()->void:
	if DisplayServer.get_name()=="headless":push_error("GPU required");quit(1);return
	base=ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	# 冷包验证可把报告写到包外；原素材与冻结登记载荷保持只读。
	output_base=base
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output-root="):output_base=argument.trim_prefix("--output-root=")
	DirAccess.make_dir_recursive_absolute(output_base.path_join("qa"))
	metadata=JSON.parse_string(FileAccess.get_file_as_string("res://action-pilot-metadata.json"))
	frames=load("res://robot_action_pilot_v011.tres") as SpriteFrames
	if frames==null:quit(1);return
	for clip:Dictionary in metadata.clips:
		if frames.get_frame_count(clip.name)!=clip.frames.size() or frames.get_animation_speed(clip.name)!=clip.fps or frames.get_animation_loop(clip.name)!=clip.loop:errors.append("clip contract: "+clip.name)
		for f:Dictionary in clip.frames:
			var source:=Image.load_from_file(base.path_join(f.file));source.convert(Image.FORMAT_RGBA8)
			if FileAccess.get_sha256(base.path_join(f.file))!=f.sha256:errors.append("source hash: "+f.file)
			for scale_value in [1,4]:
				var view:=_view(Vector2i(64,96)*scale_value);view.add_child(_sprite(clip.name,int(f.frame),scale_value))
				var image:=await _capture(view);view.free()
				var expected:=source.duplicate() as Image;expected.resize(64*scale_value,96*scale_value,Image.INTERPOLATE_NEAREST)
				var exact:=image.get_data()==expected.get_data();var file:="gpu-action-playback/%s_f%02d_%dx.png"%[clip.name,int(f.frame),scale_value]
				_save(image,file);cases.append({"clip":clip.name,"frame":f.frame,"scale":scale_value,"file":file,"rgba_exact":exact})
				if not exact:errors.append("GPU mismatch: "+file)
		if clip.loop:await _play_twice(clip)
	var transition:=await _collect_to_idle()
	# 实例化真实预览脚本，检出其资源/节点/信号错误。
	var preview:Node=load("res://preview_action_pilot.tscn").instantiate();root.add_child(preview);await process_frame;preview.queue_free()
	var report:={"technical_checks":"PASS" if errors.is_empty() else "FAIL","revision":metadata.revision,"atlas_sha256":FileAccess.get_sha256("res://assets/robot_action_pilot_atlas_v011.png"),"gpu":RenderingServer.get_video_adapter_name(),"cases":cases,"natural_playback":natural,"collect_to_idle":transition,"errors":errors,"art_acceptance":"NOT_CLAIMED"}
	var out:=FileAccess.open(output_base.path_join("qa/godot_action_pilot_v011.json"),FileAccess.WRITE);out.store_string(JSON.stringify(report,"\t",false,true)+"\n")
	print("ACTION_PILOT ",report.technical_checks," GPU=",cases.size()," collect-return=",transition)
	for error:String in errors:push_error(error)
	quit(0 if errors.is_empty() else 1)

func _view(size:Vector2i)->SubViewport:
	var v:=SubViewport.new();v.size=size;v.transparent_bg=true;v.render_target_update_mode=SubViewport.UPDATE_ALWAYS;v.canvas_item_default_texture_filter=Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST;root.add_child(v);return v

func _sprite(clip:String,index:int,scale_value:int)->AnimatedSprite2D:
	var s:=AnimatedSprite2D.new();s.sprite_frames=frames;s.animation=clip;s.frame=index;s.centered=false;s.offset=Vector2(-32,-80);s.position=Vector2(32,80)*scale_value;s.scale=Vector2.ONE*scale_value;s.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var material:=CanvasItemMaterial.new();material.light_mode=CanvasItemMaterial.LIGHT_MODE_UNSHADED;s.material=material;return s

func _capture(view:SubViewport)->Image:
	await process_frame;await process_frame;await RenderingServer.frame_post_draw
	var image:=view.get_texture().get_image();image.convert(Image.FORMAT_RGBA8);return image

func _save(image:Image,file:String)->void:
	var absolute:=output_base.path_join(file);DirAccess.make_dir_recursive_absolute(absolute.get_base_dir());image.save_png(absolute)

func _play_twice(clip:Dictionary)->void:
	var view:=_view(Vector2i(64,96));var s:=_sprite(clip.name,0,1);view.add_child(s);loops=0;sequence=[0]
	s.animation_looped.connect(func():loops+=1);s.frame_changed.connect(func():sequence.append(s.frame));s.play()
	await create_timer(2.15).timeout;s.pause()
	if loops<2:errors.append("missing loops: "+clip.name)
	for i in range(1,sequence.size()):
		if sequence[i]!=(sequence[i-1]+1)%clip.frames.size():errors.append("frame order: "+clip.name)
	natural.append({"clip":clip.name,"loops":loops,"sequence":sequence.duplicate()});view.free()

func _collect_to_idle()->Dictionary:
	var view:=_view(Vector2i(64,96));var s:=_sprite("collect_down_left",0,1);view.add_child(s)
	var finished:Array=[];var seen:Array=[0]
	s.frame_changed.connect(func():
		if s.animation=="collect_down_left":seen.append(s.frame))
	s.animation_finished.connect(func():
		if s.animation=="collect_down_left":
			finished.append({"frame":s.frame,"clip":String(s.animation)})
			s.play("idle_down_left");s.frame=0)
	s.play();await create_timer(.85).timeout;s.pause()
	var image:=await _capture(view);_save(image,"gpu-action-playback/collect_finished_to_idle0.png")
	var expected:=Image.load_from_file(base.path_join("frames/idle/down_left/robot_idle_down_left_f00_v011.png"));expected.convert(Image.FORMAT_RGBA8)
	var exact:=image.get_data()==expected.get_data()
	var result:={"finished_events":finished,"collect_sequence":seen,"result_animation":String(s.animation),"result_frame":s.frame,"idle0_rgba_exact":exact}
	if finished.size()!=1 or seen!=[0,1,2,3] or s.animation!="idle_down_left" or s.frame!=0 or not exact:errors.append("collect non-loop recovery failed")
	view.free();return result
