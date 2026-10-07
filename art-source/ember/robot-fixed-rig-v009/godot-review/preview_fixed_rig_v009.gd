extends Node2D
## 独立候选播放页：两个倍率使用同一SpriteFrames，没有bbox自动对齐。
var native_sprite: AnimatedSprite2D
var zoom_sprite: AnimatedSprite2D
var frame_label: Label
var poses: Array = []
var markers: Node2D

func _ready() -> void:
	RenderingServer.set_default_clear_color(Color("#182631"))
	DisplayServer.window_set_title("固定骨架 v009 · CANDIDATE · walk_down 8 FPS")
	get_window().size=Vector2i(640,384)
	var frames:=load("res://robot_sprite_frames_v009.tres") as SpriteFrames
	if frames==null or not frames.has_animation("walk_down"):
		push_error("候选SpriteFrames尚未完成独立工程导入"); get_tree().quit(1); return
	native_sprite=_add_sprite(frames,Vector2(80,180),1)
	zoom_sprite=_add_sprite(frames,Vector2(360,320),4)
	_add_label("固定母稿 / 八步相位\n64×96 整格 · 锚点 (32,80)\n1× 原生 + 4× 最近邻\nCANDIDATE：尚未美术接收",Vector2(12,12))
	frame_label=_add_label("",Vector2(12,214))
	_add_label("空格：暂停 / 继续\n左右键：暂停并逐帧\n原生帧及倍率共用真实 SpriteFrames",Vector2(12,250))
	var pose_base:=ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir().path_join("poses")
	for index in 8: poses.append(JSON.parse_string(FileAccess.get_file_as_string(pose_base.path_join("walk_down_f%02d_v009.json"%index))))
	markers=Node2D.new(); markers.z_index=5; add_child(markers)

func _add_sprite(frames: SpriteFrames,anchor: Vector2,multiplier: int) -> AnimatedSprite2D:
	var sprite:=AnimatedSprite2D.new(); sprite.sprite_frames=frames; sprite.centered=false; sprite.offset=Vector2(-32,-80)
	sprite.position=anchor; sprite.scale=Vector2.ONE*multiplier; sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var material:=CanvasItemMaterial.new(); material.light_mode=CanvasItemMaterial.LIGHT_MODE_UNSHADED; sprite.material=material
	add_child(sprite); sprite.play("walk_down"); return sprite

func _add_label(text: String,at: Vector2) -> Label:
	var label:=Label.new(); label.text=text; label.position=at; label.add_theme_font_size_override("font_size",14); add_child(label); return label

func _process(_delta: float) -> void:
	if not is_instance_valid(native_sprite) or not is_instance_valid(markers): return
	frame_label.text="F%02d / 07 · %s"%[native_sprite.frame,"播放" if native_sprite.is_playing() else "暂停"]
	for marker in markers.get_children(): marker.queue_free()
	# root是固定整格锚点；鞋底触地标记使用pose投影登记，绝不画假定y80水平地面。
	for entry in [[Vector2(80,180),1],[Vector2(360,320),4]]:
		var origin: Vector2=entry[0]; var multiplier: int=entry[1]
		_marker(origin,Color("#B77C4B"))
		for side: String in ["left","right"]:
			var contact: Dictionary=poses[native_sprite.frame].contacts[side]
			if not contact.stance: continue
			# 抬跟/抬尖时中心高于地面，显示独立足部控制器的真实枢轴。
			var projected:=Vector2(contact.contact_projected[0],contact.contact_projected[1])
			_marker(origin+(projected-Vector2(32,80))*multiplier,Color("#BECBC4"))

func _marker(point: Vector2,color: Color) -> void:
	var horizontal:=Line2D.new(); horizontal.points=PackedVector2Array([point+Vector2(-3,0),point+Vector2(3,0)]); horizontal.width=1; horizontal.default_color=color; markers.add_child(horizontal)
	var vertical:=Line2D.new(); vertical.points=PackedVector2Array([point+Vector2(0,-3),point+Vector2(0,3)]); vertical.width=1; vertical.default_color=color; markers.add_child(vertical)

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo: return
	if event.keycode==KEY_SPACE:
		for sprite in [native_sprite,zoom_sprite]:
			if sprite.is_playing(): sprite.pause()
			else: sprite.play()
	if event.keycode in [KEY_LEFT,KEY_RIGHT]:
		var step:=1 if event.keycode==KEY_RIGHT else -1
		var selected: int=(native_sprite.frame+step+8)%8
		for sprite in [native_sprite,zoom_sprite]: sprite.pause(); sprite.frame=selected
