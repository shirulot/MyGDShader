extends SceneTree
const Rig=preload("res://action_rig.gd")
func _initialize()->void: call_deferred("run")
func run()->void:
	var viewport:=SubViewport.new()
	viewport.size=Vector2i(128,128)
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var backdrop:=ColorRect.new()
	backdrop.size=Vector2(128,128)
	viewport.add_child(backdrop)
	var rig:=Rig.new()
	viewport.add_child(rig)
	var sprite:=Sprite2D.new()
	sprite.centered=false
	sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	viewport.add_child(sprite)
	var records:Array=[]
	var diagnostics:Array=[]
	var passed:=true
	var max_rigid_error:=0.0
	var max_strut_error:=0.0
	for action:String in Rig.CLIPS:
		for index in range(Rig.CLIPS[action].poses.size()):
			var raw:=read_image("res://output/%s/f%02d.png"%[action,index])
			var islands:=components(raw)
			passed=passed and islands.size()==1
			var pose:Dictionary=rig.pose_action(action,index)
			for side:String in pose.strut_endpoints:
				var ends:Dictionary=pose.strut_endpoints[side]
				var data:Dictionary=pose.part_transforms[side+"_strut"]
				var actual_start:=Vector2(data.position[0],data.position[1])
				var actual_end:=actual_start+Vector2(data.basis_x[0],data.basis_x[1])*float(ends.rest_local_end[0])+Vector2(data.basis_y[0],data.basis_y[1])*float(ends.rest_local_end[1])
				max_strut_error=maxf(max_strut_error,maxf(actual_start.distance_to(Vector2(ends.start[0],ends.start[1])),actual_end.distance_to(Vector2(ends.end[0],ends.end[1]))))
			for id:String in pose.part_transforms:
				if id.ends_with('_strut'): continue
				var data:Dictionary=pose.part_transforms[id]
				var x:=Vector2(data.basis_x[0],data.basis_x[1])
				var y:=Vector2(data.basis_y[0],data.basis_y[1])
				max_rigid_error=maxf(max_rigid_error,maxf(absf(x.length()-1),maxf(absf(y.length()-1),absf(x.dot(y)))))
			diagnostics.append({"action":action,"frame":index,"components":islands,"contacts":pose.contacts,"root":pose.root_px})
			for background:String in ["black","white"]:
				backdrop.color=Color.BLACK if background=="black" else Color.WHITE
				rig.pose_action(action,index)
				rig.visible=true
				sprite.visible=false
				await process_frame
				await RenderingServer.frame_post_draw
				var rendered:=viewport.get_texture().get_image()
				rendered.convert(Image.FORMAT_RGBA8)
				rig.visible=false
				sprite.texture=ImageTexture.create_from_image(raw)
				sprite.visible=true
				await process_frame
				await RenderingServer.frame_post_draw
				var exported:=viewport.get_texture().get_image()
				exported.convert(Image.FORMAT_RGBA8)
				var channels:=difference(rendered,exported)
				passed=passed and channels==0
				records.append({"action":action,"frame":index,"background":background,"differing_channels":channels})
				var pair:=Image.create(160,80,false,Image.FORMAT_RGBA8)
				pair.blit_rect(rendered,Rect2i(24,32,80,80),Vector2i.ZERO)
				pair.blit_rect(exported,Rect2i(24,32,80,80),Vector2i(80,0))
				pair.resize(640,320,Image.INTERPOLATE_NEAREST)
				pair.save_png("res://qa/roundtrip_%s_f%02d_%s.png"%[action,index,background])
	var neutral:=read_image("res://output/idle_down/f00.png")
	var attack_return:=difference(neutral,read_image("res://output/attack_down/f05.png"))
	var hit_return:=difference(neutral,read_image("res://output/hit_down/f03.png"))
	var death_hold:=difference(read_image("res://output/death_down/f06.png"),read_image("res://output/death_down/f07.png"))
	passed=passed and attack_return==0 and hit_return==0 and death_hold==0 and max_rigid_error<0.00001
	passed=passed and max_strut_error<0.00001
	var report:Dictionary={"status":"PASS" if passed else "FAIL","scope":"rigid source parts, topology, PNG/GPU and runtime checks; not TA approval","catalog_sha256":FileAccess.get_sha256("res://output/catalog_v011.json"),"max_rigid_basis_error":max_rigid_error,"attack_return_diff":attack_return,"hit_return_diff":hit_return,"death_hold_diff":death_hold,"roundtrip":records,"frame_diagnostics":diagnostics}
	report["max_strut_endpoint_error_px"]=max_strut_error
	FileAccess.open("res://qa/verification.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print(JSON.stringify(report))
	quit(0 if passed else 1)
func read_image(path:String)->Image:
	return Image.load_from_file(ProjectSettings.globalize_path(path))
func difference(first:Image,second:Image)->int:
	var a:=first.get_data()
	var b:=second.get_data()
	var count:=0
	for index in range(a.size()):
		if a[index]!=b[index]: count+=1
	return count

func components(frame: Image) -> Array:
	var visited := PackedByteArray()
	visited.resize(128*128)
	var result: Array = []
	for y in range(128):
		for x in range(128):
			if visited[y*128+x] or frame.get_pixel(x,y).a<0.5: continue
			var queue: Array[Vector2i] = [Vector2i(x,y)]
			visited[y*128+x]=1
			var cursor:=0
			var minimum:=Vector2i(x,y)
			var maximum:=Vector2i(x,y)
			while cursor<queue.size():
				var point:=queue[cursor]
				cursor+=1
				minimum=minimum.min(point)
				maximum=maximum.max(point)
				for dy in range(-1,2):
					for dx in range(-1,2):
						var next:=point+Vector2i(dx,dy)
						if next.x<0 or next.y<0 or next.x>=128 or next.y>=128: continue
						if visited[next.y*128+next.x] or frame.get_pixelv(next).a<0.5: continue
						visited[next.y*128+next.x]=1
						queue.append(next)
			result.append({"pixels":queue.size(),"bbox":[minimum.x,minimum.y,maximum.x-minimum.x+1,maximum.y-minimum.y+1]})
	return result




