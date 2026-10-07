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
	var neutral:=read_image("res://output/attack_down/f00.png")
	var source:=read_image("res://source/canonical.png")
	var source_diff:=0
	for y in range(128):
		for x in range(128):
			var original:=source.get_pixel(x,y)
			var actual:=neutral.get_pixel(x,y)
			if (original.a8>=128)!=(actual.a8==255): source_diff+=1
			elif actual.a8==255 and (original.r8!=actual.r8 or original.g8!=actual.g8 or original.b8!=actual.b8): source_diff+=1
	var records:Array=[]
	var frame_records:Array=[]
	var passed:=source_diff==0
	var max_shoe_alpha_diff:=0
	var max_sole_diff:=0
	var max_static_shoe_rgb_diff:=0
	for action:String in Rig.CLIPS:
		for index in range(Rig.CLIPS[action].poses.size()):
			var raw:=read_image("res://output/%s/f%02d.png"%[action,index])
			var alpha_diff:=0
			var static_rgb_diff:=0
			for x_start in [24,86]:
				for y in range(64,104):
					for x in range(x_start,x_start+18):
						if neutral.get_pixel(x,y).a8!=raw.get_pixel(x,y).a8: alpha_diff+=1
						if action!="move_down" and neutral.get_pixel(x,y)!=raw.get_pixel(x,y): static_rgb_diff+=1
			var sole_diff:=difference(neutral.get_region(Rect2i(24,102,80,2)),raw.get_region(Rect2i(24,102,80,2)))
			max_shoe_alpha_diff=maxi(max_shoe_alpha_diff,alpha_diff)
			max_sole_diff=maxi(max_sole_diff,sole_diff)
			max_static_shoe_rgb_diff=maxi(max_static_shoe_rgb_diff,static_rgb_diff)
			var islands:=components(raw)
			passed=passed and islands.size()==1
			frame_records.append({"action":action,"frame":index,"shoe_roi_alpha_diff":alpha_diff,"static_shoe_rgb_diff":static_rgb_diff,"sole_diff":sole_diff,"components":islands})
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
				var pair:=Image.create(192,80,false,Image.FORMAT_RGBA8)
				pair.blit_rect(rendered,Rect2i(16,32,96,80),Vector2i.ZERO)
				pair.blit_rect(exported,Rect2i(16,32,96,80),Vector2i(96,0))
				pair.resize(768,320,Image.INTERPOLATE_NEAREST)
				pair.save_png("res://qa/roundtrip_%s_f%02d_%s.png"%[action,index,background])
	var terminal_diff:=difference(neutral,read_image("res://output/attack_down/f05.png"))
	passed=passed and max_shoe_alpha_diff==0 and max_sole_diff==0 and max_static_shoe_rgb_diff==0 and terminal_diff==0
	var report:Dictionary={"status":"PASS" if passed else "FAIL","scope":"native source, tread coverage, source/export and runtime registration; not art approval","catalog_sha256":FileAccess.get_sha256("res://output/catalog_v009.json"),"neutral_source_coverage_rgb_differences":source_diff,"maximum_track_shoe_roi_alpha_differences":max_shoe_alpha_diff,"maximum_static_shoe_rgb_differences":max_static_shoe_rgb_diff,"maximum_sole_differing_channels":max_sole_diff,"attack_terminal_vs_neutral_diff":terminal_diff,"roundtrip":records,"frame_diagnostics":frame_records}
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


