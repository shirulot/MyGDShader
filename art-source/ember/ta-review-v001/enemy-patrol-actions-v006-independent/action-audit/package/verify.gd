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
	var catalog:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog_v006.json"))
	var records:Array=[]
	var maximum_endpoint_error:=0.0
	var segment_count:=0
	var maximum_foot_difference:=0
	var neutral_start_difference:=0
	var passed:=true
	var neutral:=Image.load_from_file(ProjectSettings.globalize_path("res://source/neutral_bind_v004.png"))
	for action:String in Rig.CLIPS:
		for index in range(Rig.CLIPS[action].poses.size()):
			var raw:=Image.load_from_file(ProjectSettings.globalize_path("res://output/%s/f%02d.png"%[action,index]))
			var foot_diff:=difference(neutral.get_region(Rect2i(50,98,29,7)),raw.get_region(Rect2i(50,98,29,7)))
			if action=="attack_down" or index<=2: maximum_foot_difference=maxi(maximum_foot_difference,foot_diff)
			if index==0: neutral_start_difference=maxi(neutral_start_difference,difference(neutral,raw))
			var pose:Dictionary=catalog.actions[action].poses[index]
			for part:Dictionary in rig.spec.parts:
				if not part.has("end"): continue
				var matrix:Dictionary=pose.part_transforms[part.id]
				var rest:=rig.point(part.end)-rig.point(part.pivot)
				var actual:=rig.point(matrix.position)+rig.point(matrix.basis_x)*rest.x+rig.point(matrix.basis_y)*rest.y
				var side:String=str(part.id).split("_")[0]
				var target:Vector2
				if str(part.id)=="right_upper_arm": target=rig.point(pose.arms.right.elbow_px)
				else: target=rig.point(pose.legs[side].knee_px if str(part.id).ends_with("thigh") else pose.legs[side].ankle_px)
				maximum_endpoint_error=maxf(maximum_endpoint_error,actual.distance_to(target))
				segment_count+=1
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
				# 保存全部16组实图，方便独立逐帧复核。
				var pair:=Image.create(176,80,false,Image.FORMAT_RGBA8)
				pair.blit_rect(rendered,Rect2i(32,32,88,80),Vector2i.ZERO)
				pair.blit_rect(exported,Rect2i(32,32,88,80),Vector2i(88,0))
				pair.resize(704,320,Image.INTERPOLATE_NEAREST)
				pair.save_png("res://qa/roundtrip_%s_f%02d_%s.png"%[action,index,background])
	var attack_end:=Image.load_from_file(ProjectSettings.globalize_path("res://output/attack_down/f05.png"))
	var neutral_diff:=difference(neutral,attack_end)
	var death_settle:=Image.load_from_file(ProjectSettings.globalize_path("res://output/death_down/f06.png"))
	var death_hold:=Image.load_from_file(ProjectSettings.globalize_path("res://output/death_down/f07.png"))
	var hold_diff:=difference(death_settle,death_hold)
	passed=passed and maximum_endpoint_error<0.0001 and maximum_foot_difference==0 and neutral_diff==0 and neutral_start_difference==0 and hold_diff==0 and segment_count==70
	var report:Dictionary={"status":"PASS" if passed else "FAIL","scope":"export, support-phase foot ROI and pose registration; not art acceptance","catalog_sha256":FileAccess.get_sha256("res://output/catalog_v006.json"),"segment_count":segment_count,"maximum_endpoint_error":maximum_endpoint_error,"maximum_support_foot_roi_differing_channels":maximum_foot_difference,"neutral_starts_vs_approved_bind_differing_channels":neutral_start_difference,"attack_end_vs_approved_bind_differing_channels":neutral_diff,"death_f06_f07_differing_channels":hold_diff,"roundtrip":records}
	FileAccess.open("res://qa/verification.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print(JSON.stringify(report))
	quit(0 if passed else 1)
func difference(first:Image,second:Image)->int:
	var a:=first.get_data()
	var b:=second.get_data()
	assert(a.size()==b.size())
	var differences:=0
	for index in range(a.size()):
		if a[index]!=b[index]: differences+=1
	return differences
