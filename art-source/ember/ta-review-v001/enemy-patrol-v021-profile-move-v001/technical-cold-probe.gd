extends SceneTree
## TA 独立最小冷加载：资源/CPU 归属读取；不重跑 GPU、播放或切向矩阵。
func _initialize() -> void:
	call_deferred("_audit")

func _audit() -> void:
	var errors:Array=[]
	var cat:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog.json"))
	var sf:SpriteFrames=load(cat.tres)
	var scene:PackedScene=load("res://preview.tscn")
	if sf==null or scene==null:
		printerr("TA minimal resource load failed")
		quit(1)
		return
	var clips:Array=[]
	var checked:int=0
	for c:Dictionary in cat.clips:
		var key:String=c.action
		if not sf.has_animation(key):
			errors.append("missing "+key)
			continue
		if sf.get_frame_count(key)!=8 or sf.get_animation_speed(key)!=8.0 or not sf.get_animation_loop(key):
			errors.append("configuration "+key)
		var atlas:=Image.new()
		if atlas.load_png_from_buffer(FileAccess.get_file_as_bytes(c.atlas))!=OK:
			errors.append("PNG load "+key)
			continue
		atlas.convert(Image.FORMAT_RGBA8)
		for i:int in range(8):
			var tex:AtlasTexture=sf.get_frame_texture(key,i)
			var rect:=Rect2i(i*128,0,128,128)
			if tex==null or tex.region!=Rect2(rect) or tex.atlas.get_size()!=Vector2(1024,128) or sf.get_frame_duration(key,i)!=1.0:
				errors.append("registration "+key+str(i))
				continue
			var frame:Image=tex.get_image()
			frame.convert(Image.FORMAT_RGBA8)
			if frame.get_data()!=atlas.get_region(rect).get_data():
				errors.append("embedded RGBA "+key+str(i))
			checked+=1
		clips.append({"name":key,"frames":sf.get_frame_count(key),"fps":sf.get_animation_speed(key),"loop":sf.get_animation_loop(key)})
	if sf.get_animation_names().size()!=4:
		errors.append("unexpected saved move clip count")
	if sf.has_animation("move_up") or sf.has_animation("move_down_left") or sf.has_animation("move_up_left") or sf.has_animation("move_up_right"):
		errors.append("out-of-batch directions wrongly present")
	if Vector2(cat.root[0],cat.root[1])!=Vector2(64,104) or Vector2(cat.canvas[0],cat.canvas[1])!=Vector2(128,128):
		errors.append("root/canvas metadata")
	var instance:Node2D=scene.instantiate()
	root.add_child(instance)
	var sprites:Array=[]
	for n:Node in instance.get_children():
		if n is AnimatedSprite2D:
			var sprite:AnimatedSprite2D=n
			sprite.pause()
			if sprite.centered or sprite.texture_filter!=CanvasItem.TEXTURE_FILTER_NEAREST:
				errors.append("preview registration")
			if sprite.sprite_frames.get_animation_names().size()!=20:
				errors.append("preview cache expected 8 original + 8 neutral + 4 moves")
			sprites.append({"centered":sprite.centered,"texture_filter":sprite.texture_filter,"animation":sprite.animation,"frame":sprite.frame,"cached_animations":sprite.sprite_frames.get_animation_names()})
	if sprites.size()!=2:
		errors.append("preview actor count")
	var rig_checks:Array=[]
	var Rig=load("res://rig.gd")
	for direction:String in ["left","right"]:
		var rig=Rig.new()
		rig.direction=direction
		root.add_child(rig)
		var masks:Array=[]
		for id:String in rig.parts:
			var node:Node2D=rig.parts[id]
			var sprite:Sprite2D=node.get_child(0)
			if sprite.centered or sprite.position!=-Vector2(node.position):
				errors.append("rig texture registration "+direction+" "+id)
			var mask:Image=sprite.material.get_shader_parameter("ownership").get_image()
			var path:String="res://../technical-runtime-mask-"+direction+"-"+id+".png"
			mask.save_png(path)
			masks.append({"id":id,"path":path,"format":mask.get_format(),"z":node.z_index})
		var poses:Array=[]
		for i:int in range(8):
			poses.append(rig.pose(i))
		rig_checks.append({"direction":direction,"masks":masks,"poses":poses})
		rig.queue_free()
	var result:Dictionary={"status":"PASS" if errors.is_empty() else "FAIL","scope":"Independent fresh headless import; 4 moves / 32 embedded frames, 8 neutral dependencies, preview instantiation, 18 W/E CPU ownership masks and 16 W/E pose readbacks. No GPU, loops, turn replay, or visual verdict.","engine":Engine.get_version_info(),"frames":checked,"clips":clips,"sprites":sprites,"root":cat.root,"canvas":cat.canvas,"rig_cpu_checks":rig_checks,"errors":errors}
	FileAccess.open("res://../technical-minimal-cold-load.json",FileAccess.WRITE).store_string(JSON.stringify(result,"\t"))
	print("TA_MINIMAL_COLD_RESULT "+result.status)
	quit(0 if errors.is_empty() else 1)
