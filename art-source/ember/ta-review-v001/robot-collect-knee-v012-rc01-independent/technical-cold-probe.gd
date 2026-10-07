extends SceneTree
## TA 实际入口最小复核：112 imported RGBA、八向采集自然完成、一个新帧 GPU 样本。
var errors:Array=[]
var active_clip:String=""
var seen:Array=[]
var finished_count:=0
func _initialize()->void:call_deferred("audit")
func check(ok:bool,text:String)->void:
	if not ok:errors.append(text)
func audit()->void:
	check(DisplayServer.get_name()!="headless","real renderer")
	var meta:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://full-action-metadata.json"))
	var frames:SpriteFrames=load("res://assets/ember/robot_v012/robot_eight_way_v012.tres")
	var count:=0
	for clip:Dictionary in meta.clips:
		check(frames.has_animation(clip.name) and frames.get_frame_count(clip.name)==clip.frames.size() and frames.get_animation_speed(clip.name)==clip.fps and frames.get_animation_loop(clip.name)==clip.loop,"parameters "+clip.name)
		for f:Dictionary in clip.frames:
			var tex:AtlasTexture=frames.get_frame_texture(clip.name,f.frame)
			var rect:Array=f.region
			check(tex.region==Rect2(rect[0],rect[1],rect[2],rect[3]) and frames.get_frame_duration(clip.name,f.frame)==1,"region "+f.file)
			var actual:=tex.get_image()
			var png:=Image.load_from_file(ProjectSettings.globalize_path("res://"+f.file))
			actual.convert(Image.FORMAT_RGBA8)
			png.convert(Image.FORMAT_RGBA8)
			check(actual.get_size()==Vector2i(64,96) and actual.get_data()==png.get_data(),"import RGBA "+f.file)
			count+=1
	check(count==112 and frames.get_animation_names().size()==24,"24/112")
	var main:String=ProjectSettings.get_setting("application/run/main_scene")
	check(main=="res://preview/preview_full_actions.tscn","real entry")
	var scene:Node=load(main).instantiate()
	root.add_child(scene)
	await process_frame
	var large:AnimatedSprite2D=scene.robot
	var native:AnimatedSprite2D=scene.native
	var anchors:Array=[large.position,native.position]
	for sprite:AnimatedSprite2D in [large,native]:check(not sprite.centered and sprite.offset==Vector2(-32,-80) and sprite.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST,"root/nearest")
	check(large.scale==Vector2(4,4) and native.scale==Vector2.ONE,"scales")
	large.animation_finished.connect(func():finished_count+=1)
	large.frame_changed.connect(func():
		if large.animation==active_clip and (seen.is_empty() or seen[-1]!=large.frame):seen.append(large.frame))
	var recoveries:Array=[]
	var gpu_checks:Array=[]
	for index:int in range(8):
		var d:String=meta.directions[index]
		scene.play_action("idle")
		scene.set_direction(index)
		active_clip="collect_"+d
		seen=[]
		var initial_finished:=finished_count
		scene.play_action("collect")
		if seen.is_empty():seen.append(0)
		scene.set_direction((index+1)%8)
		var locked:bool=scene.direction_index==index and large.animation==active_clip
		if d=="down_right":
			while large.frame==0:await large.frame_changed
			large.pause()
			native.pause()
			native.frame=large.frame
			var sample_frame:=large.frame
			await process_frame
			await RenderingServer.frame_post_draw
			var gpu:=root.get_texture().get_image()
			gpu.convert(Image.FORMAT_RGBA8)
			gpu.save_png("res://../../technical-entry-collect-se-f01.png")
			var png:=Image.load_from_file(ProjectSettings.globalize_path("res://frames/collect/down_right/robot_collect_down_right_f%02d_v012.png"%sample_frame))
			png.convert(Image.FORMAT_RGBA8)
			for sprite:AnimatedSprite2D in [large,native]:
				var factor:=int(sprite.scale.x)
				var origin:=Vector2i(sprite.position+sprite.offset*sprite.scale)
				var checked:=0
				var mismatch:=0
				for y in range(96):
					for x in range(64):
						var color:=png.get_pixel(x,y)
						if color.a==0:continue
						for sy in range(factor):
							for sx in range(factor):
								checked+=1
								if gpu.get_pixel(origin.x+x*factor+sx,origin.y+y*factor+sy).to_rgba32()!=color.to_rgba32():mismatch+=1
				gpu_checks.append({"direction":d,"frame":sample_frame,"scale":factor,"opaque_samples":checked,"mismatch":mismatch})
				check(mismatch==0,"GPU sample")
			large.play()
			native.play()
		await large.animation_finished
		var recovered:bool=large.animation=="idle_"+d and native.animation=="idle_"+d and large.frame==0 and native.frame==0
		var roots_fixed:bool=large.position==anchors[0] and native.position==anchors[1]
		check(locked and seen==[0,1,2,3] and finished_count==initial_finished+1 and recovered and roots_fixed,"natural once recovery "+d)
		recoveries.append({"direction":d,"seen":seen.duplicate(),"finished_once":finished_count==initial_finished+1,"direction_locked":locked,"both_idle0_recovered":recovered,"roots_fixed":roots_fixed})
	var result:Dictionary={"status":"PASS" if errors.is_empty() else "FAIL","engine":Engine.get_version_info().string,"renderer":RenderingServer.get_video_adapter_name(),"clips":24,"frames_rgba_checked":count,"root_anchor":[32,80],"main":main,"recoveries":recoveries,"independent_gpu_samples":gpu_checks,"scope":"Full isolated ZIP import and112 frames;8 natural collect completions;one SE revised F01 at1x/4x. Not64-sample author matrix replay.","errors":errors}
	FileAccess.open("res://../../technical-runtime-entry.json",FileAccess.WRITE).store_string(JSON.stringify(result,"\t"))
	print("TA_COLD_V012 "+result.status)
	quit(0 if errors.is_empty() else 1)
