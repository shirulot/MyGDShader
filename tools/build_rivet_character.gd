extends SceneTree
## 从已审核帧清单建立 8 个动画，剔除工具换边帧，保留旧机器人资源。
const DIR := "res://assets/ember/characters/rivet/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIR+"rivet_catalog_v001.json"))
	var texture := load(catalog.texture) as Texture2D
	assert(texture.get_size() == Vector2(640,640))
	var frames := SpriteFrames.new()
	frames.remove_animation("default")
	var frame_map := {}
	for entry in catalog.frames: frame_map[entry.id] = entry
	for clip in catalog.animations:
		var data: Dictionary = catalog.animations[clip]
		frames.add_animation(clip)
		frames.set_animation_speed(clip,data.fps)
		frames.set_animation_loop(clip,true)
		for id in data.frames:
			var entry: Dictionary = frame_map[id]
			assert(entry.accepted)
			var region := AtlasTexture.new()
			region.atlas = texture
			region.region = Rect2(entry.coord[0]*128,entry.coord[1]*160,128,160)
			region.filter_clip = true
			frames.add_frame(clip,region)
	assert(ResourceSaver.save(frames,DIR+"rivet_sprite_frames_v001.tres") == OK)
	frames = load(DIR+"rivet_sprite_frames_v001.tres")
	assert(frames.get_animation_names().size() == 8)
	assert(frames.get_frame_count("walk_down") == 3)
	var scene := Node2D.new()
	scene.name = "RivetCharacterPreview"
	scene.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	root.add_child(scene)
	_label(scene,Vector2(24,20),"铆钉 · 新形象四向待机 / 履带移动",23)
	_label(scene,Vector2(24,54),"朝下移动保留 3 帧，其余方向 4 帧；未把错误工具换边帧加入动画。",14)
	var directions := ["down","left","right","up"]
	for i in range(4):
		_label(scene,Vector2(52+i*168,94),directions[i],18)
		for row in range(2):
			var sprite := AnimatedSprite2D.new()
			sprite.sprite_frames = frames
			sprite.position = Vector2(100+i*168,208+row*200)
			sprite.animation = ("idle_" if row==0 else "walk_")+directions[i]
			sprite.autoplay = sprite.animation
			scene.add_child(sprite); sprite.owner = scene
	_label(scene,Vector2(24,495),"下方角色可用 WASD / 方向键移动；旧角色与正式游戏入口保持不变。",15)
	var actor := Node2D.new()
	actor.name = "PlayableRivet"
	actor.set_script(load("res://scripts/ember/rivet_preview_controller.gd"))
	actor.position = Vector2(360,630)
	# 在加入场景树前构造子节点，使控制器的 @onready 可以正确取得精灵。
	var player_sprite := AnimatedSprite2D.new()
	player_sprite.name = "AnimatedSprite2D"
	player_sprite.sprite_frames = frames
	player_sprite.offset = Vector2(0,-56)
	player_sprite.scale = Vector2.ONE*0.5
	player_sprite.animation = "idle_down"
	player_sprite.autoplay = "idle_down"
	actor.add_child(player_sprite)
	scene.add_child(actor); actor.owner = scene; player_sprite.owner = scene
	var packed := PackedScene.new()
	assert(packed.pack(scene) == OK)
	assert(ResourceSaver.save(packed,"res://scenes/ember/rivet_character_preview.tscn") == OK)
	var report := {"engine":Engine.get_version_info().string,"animations":8,"accepted_frames":19,"excluded_frames":["down_03"],"sprite_frames_reloaded":true,"main_game_replaced":false}
	var file := FileAccess.open(DIR+"godot_validation.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t")+"\n")
	print(JSON.stringify(report))
	scene.queue_free()
	quit()

func _label(scene: Node2D,where: Vector2,value: String,size: int) -> void:
	var label := Label.new()
	label.position = where; label.text = value
	label.add_theme_font_size_override("font_size",size)
	scene.add_child(label); label.owner = scene
