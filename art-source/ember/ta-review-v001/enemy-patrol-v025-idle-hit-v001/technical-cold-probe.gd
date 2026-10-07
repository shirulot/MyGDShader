extends SceneTree
## P25 最小 headless 冷资源和原 rig 数据读回；不重复作者 GPU/循环矩阵。
func _initialize()->void:call_deferred("_audit")
func _audit()->void:
	var errors:Array=[]
	var cat:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog.json"))
	var sf:SpriteFrames=load(cat.tres)
	var scene:PackedScene=load("res://preview.tscn")
	var count:int=0
	var clips:Array=[]
	for c:Dictionary in cat.clips:
		var fps:float=4.0 if c.action.begins_with("idle_") else 12.0
		var loop:bool=c.action.begins_with("idle_")
		if not sf.has_animation(c.action) or sf.get_frame_count(c.action)!=4 or sf.get_animation_speed(c.action)!=fps or sf.get_animation_loop(c.action)!=loop:errors.append("clip parameters "+c.action)
		var atlas:Image=Image.load_from_file(ProjectSettings.globalize_path(c.atlas))
		atlas.convert(Image.FORMAT_RGBA8)
		for i:int in range(4):
			var texture:AtlasTexture=sf.get_frame_texture(c.action,i)
			var region:=Rect2i(i*128,0,128,128)
			if texture.region!=Rect2(region) or texture.atlas.get_size()!=Vector2(512,128) or sf.get_frame_duration(c.action,i)!=1.0:errors.append("atlas registration "+c.action+str(i))
			var image:Image=texture.get_image()
			image.convert(Image.FORMAT_RGBA8)
			if image.get_data()!=atlas.get_region(region).get_data():errors.append("embedded RGBA "+c.action+str(i))
			count+=1
		clips.append({"name":c.action,"fps":fps,"loop":loop,"frames":4})
	if sf.get_animation_names().size()!=16 or count!=64:errors.append("clip/frame count")
	var preview:Node2D=scene.instantiate()
	root.add_child(preview)
	var actors:Array=[]
	for sprite:AnimatedSprite2D in [preview.target,preview.approved]:
		sprite.pause()
		if sprite.centered or sprite.texture_filter!=CanvasItem.TEXTURE_FILTER_NEAREST or sprite.sprite_frames.get_animation_names().size()!=16:errors.append("preview parameters")
		actors.append({"centered":sprite.centered,"nearest":sprite.texture_filter,"clips":sprite.sprite_frames.get_animation_names().size()})
	var Rig=load("res://rig.gd")
	var rig_checks:Array=[]
	for direction:String in ["down_left","left","up_left","up","up_right","right","down_right"]:
		var rig=Rig.new()
		rig.direction=direction
		root.add_child(rig)
		var masks:Array=[]
		var textures:Array=[]
		for id:String in rig.base.parts:
			var node:Node2D=rig.base.parts[id]
			if node is Sprite2D:
				var sprite:Sprite2D=node
				var image:Image=sprite.texture.get_image()
				var path:String="res://../technical-runtime-texture-"+direction+"-"+id+".png"
				image.save_png(path)
				textures.append({"id":id,"path":path,"position":[sprite.position.x,sprite.position.y],"scale":[sprite.scale.x,sprite.scale.y],"centered":sprite.centered,"z":sprite.z_index})
			else:
				var sprite:Sprite2D=node.get_child(0)
				var mask:Image=sprite.material.get_shader_parameter("ownership").get_image()
				var path:String="res://../technical-runtime-mask-"+direction+"-"+id+".png"
				mask.save_png(path)
				var source_image:Image=sprite.texture.get_image()
				source_image.save_png("res://../technical-runtime-source-"+direction+"-"+id+".png")
				masks.append({"id":id,"path":path,"z":node.z_index})
		var poses:Array=[]
		for action:String in ["idle","hit"]:
			for i:int in range(4):poses.append(rig.pose_action(action,i))
		rig_checks.append({"direction":direction,"masks":masks,"textures":textures,"poses":poses})
		rig.queue_free()
	var result:Dictionary={"status":"PASS" if errors.is_empty() else "FAIL","scope":"Fresh full-ZIP headless import;16 clips64 atlas cells RGBA, preview,7 rigs56 pose readbacks plus source masks/registered SE textures. No GPU or full playback matrix.","engine":Engine.get_version_info(),"frames":count,"clips":clips,"actors":actors,"rig_cpu_checks":rig_checks,"errors":errors}
	FileAccess.open("res://../technical-minimal-cold-load.json",FileAccess.WRITE).store_string(JSON.stringify(result,"\t"))
	print("TA_MINIMAL_COLD_RESULT "+result.status)
	quit(0 if errors.is_empty() else 1)
