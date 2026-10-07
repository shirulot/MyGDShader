extends SceneTree
## TA 最小资源冷载与实际 rig 节点读取，不重跑作者 GPU 矩阵。
func _initialize()->void:call_deferred("audit")
func vec(v:Vector2)->Array:return [v.x,v.y]
func audit()->void:
	var errors:Array=[]
	var cat:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog.json"))
	var sf:SpriteFrames=load(cat.tres)
	var count:=0
	var clips:Array=[]
	for c:Dictionary in cat.clips:
		var expected_count:int=6 if c.action.begins_with("attack_") else 8
		if not sf.has_animation(c.action) or sf.get_frame_count(c.action)!=expected_count or sf.get_animation_speed(c.action)!=10 or sf.get_animation_loop(c.action):errors.append("clip "+c.action)
		var atlas:=Image.load_from_file(ProjectSettings.globalize_path(c.atlas))
		atlas.convert(Image.FORMAT_RGBA8)
		for i:int in range(expected_count):
			var texture:AtlasTexture=sf.get_frame_texture(c.action,i)
			var region:=Rect2i(i*128,0,128,128)
			if texture.region!=Rect2(region) or texture.atlas.get_size()!=Vector2(expected_count*128,128) or sf.get_frame_duration(c.action,i)!=1:errors.append("region "+c.action+str(i))
			var image:=texture.get_image()
			image.convert(Image.FORMAT_RGBA8)
			if image.get_data()!=atlas.get_region(region).get_data():errors.append("RGBA "+c.action+str(i))
			count+=1
		clips.append({"action":c.action,"frames":expected_count,"fps":10,"loop":false})
	if sf.get_animation_names().size()!=16 or count!=112:errors.append("count")
	var preview:Node2D=load("res://preview.tscn").instantiate()
	root.add_child(preview)
	var actors:Array=[]
	for sprite:AnimatedSprite2D in [preview.target,preview.approved]:
		sprite.pause()
		if sprite.centered or sprite.texture_filter!=CanvasItem.TEXTURE_FILTER_NEAREST or sprite.sprite_frames.get_animation_names().size()!=16:errors.append("preview parameters")
		actors.append({"centered":sprite.centered,"filter":sprite.texture_filter,"clips":sprite.sprite_frames.get_animation_names().size()})
	var Rig=load("res://rig.gd")
	var checks:Array=[]
	for direction:String in ["down_left","left","up_left","up","up_right","right","down_right"]:
		var rig=Rig.new()
		rig.direction=direction
		root.add_child(rig)
		var masks:Array=[]
		var all_parts:Dictionary=rig.raw.parts.duplicate()
		all_parts.merge(rig.arms)
		for id:String in all_parts:
			var node:Node2D=all_parts[id]
			var sprite:Sprite2D=node.get_child(0)
			var mask:Image=sprite.material.get_shader_parameter("ownership").get_image()
			mask.save_png("res://../technical-runtime-mask-"+direction+"-"+id+".png")
			sprite.texture.get_image().save_png("res://../technical-runtime-source-"+direction+"-"+id+".png")
			masks.append({"id":id,"z":node.z_index,"sprite_position":vec(sprite.position),"pivot":vec(-sprite.position),"centered":sprite.centered,"filter":rig.texture_filter})
		var links:Array=[]
		for id:String in rig.links:
			var link:Polygon2D=rig.links[id]
			var uv:Array=[]
			for v:Vector2 in link.uv:uv.append(vec(v))
			links.append({"id":id,"z":link.z_index,"uv":uv,"filter":rig.texture_filter,"texture_size":vec(link.texture.get_size())})
		var poses:Array=[]
		for action:String in ["attack","death"]:
			for i:int in range(6 if action=="attack" else 8):
				var p:Dictionary=rig.pose_action(action,i)
				var powers:Array=[]
				powers.append(rig.body_material.get_shader_parameter("sensor_power"))
				poses.append({"pose":p,"actual_material_powers":powers})
		checks.append({"direction":direction,"masks":masks,"links":links,"poses":poses})
		rig.queue_free()
	var result:Dictionary={"status":"PASS" if errors.is_empty() else "FAIL","scope":"16 clips112 embedded RGBA cells, two preview actors,7 rigs98 poses and actual masks/UV/pivots/material power; no GPU replay or full player matrix.","engine":Engine.get_version_info(),"frames":count,"clips":clips,"actors":actors,"rig_checks":checks,"errors":errors}
	FileAccess.open("res://../technical-minimal-cold-load.json",FileAccess.WRITE).store_string(JSON.stringify(result,"\t"))
	print("TA_MINIMAL_COLD_RESULT "+result.status)
	quit(0 if errors.is_empty() else 1)
