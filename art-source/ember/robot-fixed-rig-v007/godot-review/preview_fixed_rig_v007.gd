extends Node2D
## 独立候选播放页：两个倍率使用同一SpriteFrames，没有bbox自动对齐。
var native_sprite: AnimatedSprite2D
var zoom_sprite: AnimatedSprite2D
var frame_label: Label

func _ready() -> void:
	RenderingServer.set_default_clear_color(Color("#182631"))
	DisplayServer.window_set_title("固定骨架 v007 · CANDIDATE · walk_down 8 FPS")
	get_window().size=Vector2i(640,384)
	var frames:=load("res://robot_sprite_frames_v007.tres") as SpriteFrames
	native_sprite=_add_sprite(frames,Vector2(80,180),1)
	zoom_sprite=_add_sprite(frames,Vector2(360,320),4)
	_add_label("固定母稿 / 八步相位\n64×96 整格 · 锚点 (32,80)\n1× 原生 + 4× 最近邻\nCANDIDATE：尚未美术接收",Vector2(12,12))
	frame_label=_add_label("",Vector2(12,214))
	_add_label("空格：暂停 / 继续\n左右键：暂停并逐帧\n原生帧及倍率共用真实 SpriteFrames",Vector2(12,250))
	var guide:=Line2D.new(); guide.points=PackedVector2Array([Vector2(220,320),Vector2(500,320)]); guide.width=1; guide.default_color=Color("#566B78"); guide.z_index=-1; add_child(guide)
	var native_guide:=Line2D.new(); native_guide.points=PackedVector2Array([Vector2(42,180),Vector2(118,180)]); native_guide.width=1; native_guide.default_color=Color("#566B78"); native_guide.z_index=-1; add_child(native_guide)

func _add_sprite(frames: SpriteFrames,anchor: Vector2,multiplier: int) -> AnimatedSprite2D:
	var sprite:=AnimatedSprite2D.new(); sprite.sprite_frames=frames; sprite.centered=false; sprite.offset=Vector2(-32,-80)
	sprite.position=anchor; sprite.scale=Vector2.ONE*multiplier; sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var material:=CanvasItemMaterial.new(); material.light_mode=CanvasItemMaterial.LIGHT_MODE_UNSHADED; sprite.material=material
	add_child(sprite); sprite.play("walk_down"); return sprite

func _add_label(text: String,at: Vector2) -> Label:
	var label:=Label.new(); label.text=text; label.position=at; label.add_theme_font_size_override("font_size",14); add_child(label); return label

func _process(_delta: float) -> void:
	frame_label.text="F%02d / 07 · %s"%[native_sprite.frame,"播放" if native_sprite.is_playing() else "暂停"]

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
