extends SceneTree
## 独立 headless 资源冷加载及代表采集结束行为；不捕获 GPU 或复跑完整切向矩阵。
var errors:Array=[]
var completion_events:Array=[]

func _initialize() -> void:
	call_deferred("_audit")

func _audit() -> void:
	var meta:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://full-action-metadata.json"))
	var frames:SpriteFrames=load("res://robot_eight_way_v011.tres")
	var scene:PackedScene=load("res://preview_full_actions.tscn")
	if frames==null or scene==null:
		printerr("TA resource load failed")
		quit(1)
		return
	var atlas:=Image.new()
	atlas.load_png_from_buffer(FileAccess.get_file_as_bytes("res://assets/robot_eight_way_actions_atlas_v011.png"))
	atlas.convert(Image.FORMAT_RGBA8)
	var clip_checks:Array=[]
	var loaded_frames:int=0
	for clip:Dictionary in meta.clips:
		var name:String=clip.name
		if not frames.has_animation(name):
			errors.append("missing "+name)
			continue
		if frames.get_frame_count(name)!=clip.frames.size() or frames.get_animation_speed(name)!=clip.fps or frames.get_animation_loop(name)!=clip.loop:
			errors.append("configuration "+name)
		for f:Dictionary in clip.frames:
			var index:int=int(f.frame)
			var texture:AtlasTexture=frames.get_frame_texture(name,index)
			var region:=Rect2i(int(f.region[0]),int(f.region[1]),int(f.region[2]),int(f.region[3]))
			if texture==null or texture.region!=Rect2(region) or texture.atlas.get_size()!=Vector2(512,2304) or frames.get_frame_duration(name,index)!=1.0:
				errors.append("registration "+name+str(index))
				continue
			var decoded:Image=texture.get_image()
			decoded.convert(Image.FORMAT_RGBA8)
			if decoded.get_data()!=atlas.get_region(region).get_data():
				errors.append("embedded RGBA "+name+str(index))
			loaded_frames+=1
		clip_checks.append({"name":name,"frames":frames.get_frame_count(name),"fps":frames.get_animation_speed(name),"loop":frames.get_animation_loop(name)})
	if frames.get_animation_names().size()!=24 or loaded_frames!=112:
		errors.append("expected 24 actions and 112 cells")
	if Vector2(meta.root_anchor[0],meta.root_anchor[1])!=Vector2(32,80) or Vector2(meta.canvas[0],meta.canvas[1])!=Vector2(64,96):
		errors.append("metadata root/canvas")
	var preview=scene.instantiate()
	root.add_child(preview)
	var sprite_checks:Array=[]
	for actor:AnimatedSprite2D in [preview.robot,preview.native]:
		if actor.centered or actor.offset!=Vector2(-32,-80) or actor.texture_filter!=CanvasItem.TEXTURE_FILTER_NEAREST:
			errors.append("actor root/nearest registration")
		sprite_checks.append({"centered":actor.centered,"offset":[actor.offset.x,actor.offset.y],"filter":actor.texture_filter,"position":[actor.position.x,actor.position.y],"scale":[actor.scale.x,actor.scale.y]})
	preview.robot.animation_finished.connect(func():completion_events.append({"animation_at_observer":str(preview.robot.animation),"frame_at_observer":preview.robot.frame}))
	var recovery_checks:Array=[]
	# 正/背纵向腕投影与侧向动作各抽一个代表；不是八向完整播放器复验。
	for direction:int in [7]:
		preview.set_direction(direction)
		var before_position:Vector2=preview.robot.position
		var before_events:int=completion_events.size()
		preview.play_action("collect")
		var clip:String=str(preview.robot.animation)
		preview.set_direction(direction+1)
		var direction_locked:bool=preview.direction_index==direction and str(preview.robot.animation)==clip
		var seen:Array=[]
		var deadline:int=Time.get_ticks_msec()+2500
		while Time.get_ticks_msec()<deadline and preview.action=="collect":
			var index:int=preview.robot.frame
			if seen.is_empty() or seen[-1]!=index:seen.append(index)
			await process_frame
		var expected:String="idle_"+str(preview.DIRECTIONS[direction])
		var event_count:int=completion_events.size()-before_events
		var passed:bool=seen==[0,1,2,3] and event_count==1 and preview.action=="idle" and str(preview.robot.animation)==expected and str(preview.native.animation)==expected and preview.robot.frame==0 and preview.native.frame==0 and preview.robot.position==before_position and direction_locked
		if not passed:errors.append("actual collect recovery "+clip)
		recovery_checks.append({"clip":clip,"sequence":seen,"finished_events":event_count,"direction_locked_while_collect":direction_locked,"result_animation":str(preview.robot.animation),"result_frame":preview.robot.frame,"native_animation":str(preview.native.animation),"native_frame":preview.native.frame,"root_position_unchanged":preview.robot.position==before_position,"passed":passed})
	var result:Dictionary={"status":"PASS" if errors.is_empty() else "FAIL","scope":"Fresh independent headless import and 24-action/112-cell RGBA resource load, nearest/root registration and actual SE collect finish-to-idle with direction lock. No GPU capture, full loop or transition matrix replay.","engine":Engine.get_version_info(),"frames":loaded_frames,"clips":clip_checks,"actors":sprite_checks,"representative_collect_recovery":recovery_checks,"completion_events":completion_events,"errors":errors}
	FileAccess.open("res://../../technical-minimal-cold-load.json",FileAccess.WRITE).store_string(JSON.stringify(result,"\t"))
	print("TA_MINIMAL_COLD_RESULT "+result.status)
	quit(0 if errors.is_empty() else 1)
