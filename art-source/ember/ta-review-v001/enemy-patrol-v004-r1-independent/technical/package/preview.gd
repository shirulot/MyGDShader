extends Node2D
## 正式预览播放已经导出的原生PNG；整数放大保持每一像素。
## 可编辑rig仅用于export.gd生成来源，避免放大几何重新采样伪装原生图。
var actors: Array[AnimatedSprite2D] = []
var time := 0.0
var paused := false
var frame_index := 0
var status: Label

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	text("PATROL MOVE v004 | NATIVE PNG PLAYBACK | PENDING TA",Vector2(24,20),24)
	status=text("8 FPS | Space pause | arrows step | R restart",Vector2(24,60),18)
	var frames := load("res://output/patrol_move_frames_v004.tres") as SpriteFrames
	for index in range(8):
		var sprite:=actor(frames)
		sprite.frame=index
		sprite.position=Vector2(20+(index%4)*310,110+(index/4)*220)-Vector2(40,45)*3
		text("f%02d"%index,Vector2(40+(index%4)*310,115+(index/4)*220),16)
	for index in range(2):
		var sprite:=actor(frames)
		sprite.position=Vector2(350+index*380,575)-Vector2(40,45)*3
		sprite.speed_scale=1.0 if index==0 else 0.125
		sprite.play("move_down")
		actors.append(sprite)
	text("8 FPS",Vector2(355,570),18)
	text("1 FPS",Vector2(735,570),18)

func actor(frames: SpriteFrames) -> AnimatedSprite2D:
	var sprite:=AnimatedSprite2D.new()
	sprite.sprite_frames=frames
	sprite.animation="move_down"
	sprite.centered=false
	sprite.scale=Vector2(3,3)
	sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(sprite)
	return sprite

func _process(delta: float) -> void:
	if not paused: time+=delta
	frame_index=actors[0].frame
	status.text=("PAUSED" if paused else "PLAYING")+" f%02d | Space pause | arrows step | R restart"%frame_index

func _unhandled_key_input(event: InputEvent) -> void:
	if not event.is_pressed(): return
	if event.keycode==KEY_SPACE:
		paused=not paused
		for sprite in actors:
			if paused: sprite.pause()
			else: sprite.play()
	if event.keycode==KEY_RIGHT or event.keycode==KEY_LEFT:
		paused=true
		frame_index=posmod(frame_index+(1 if event.keycode==KEY_RIGHT else -1),8)
		for sprite in actors:
			sprite.pause()
			sprite.set_frame_and_progress(frame_index,0)
	if event.keycode==KEY_R:
		time=0
		for sprite in actors:
			sprite.set_frame_and_progress(0,0)
	if event.keycode==KEY_ESCAPE: get_tree().quit()

func text(value: String,position_value: Vector2,size: int) -> Label:
	var label:=Label.new()
	label.text=value
	label.position=position_value
	label.add_theme_font_size_override("font_size",size)
	add_child(label)
	return label
