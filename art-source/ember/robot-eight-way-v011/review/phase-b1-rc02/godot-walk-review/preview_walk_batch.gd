extends Node2D
## 独立八方向演示。WASD/方向键选择朝向，空格暂停，Tab切换造型/行走，B换底，SLOW勾选慢放。
## 未制作方向的 walk 明确退回 pose 候选；不把单张造型冒充该方向完成的动画。
const DIRECTIONS := ["down","down_left","left","up_left","up","up_right","right","down_right"]
var frames := preload("res://robot_walk_batch_v011.tres")
var robot: AnimatedSprite2D
var native_robot: AnimatedSprite2D
var status_label: Label
var direction := "up_left"
var action := "walk"
var light := true
var paused := false

func _ready() -> void:
	RenderingServer.set_default_clear_color(Color("ece9d8"))
	robot = _new_robot(Vector2(370,460),4)
	native_robot = _new_robot(Vector2(700,360),1)
	var title := Label.new()
	title.text = "ROBOT v011 / WALK BATCH - CANDIDATE"
	title.position = Vector2(28,18)
	title.add_theme_font_size_override("font_size",24)
	add_child(title)
	status_label = Label.new()
	status_label.position = Vector2(28,550)
	add_child(status_label)
	for i in DIRECTIONS.size():
		var button := Button.new()
		button.text = DIRECTIONS[i]
		button.position = Vector2(20+i*116,64)
		button.size = Vector2(112,36)
		button.pressed.connect(func(): direction=DIRECTIONS[i]; _apply_clip())
		add_child(button)
	var slow := CheckButton.new()
	slow.text="SLOW 0.25x"
	slow.position=Vector2(700,410)
	slow.toggled.connect(func(on:bool): robot.speed_scale=0.25 if on else 1.0; native_robot.speed_scale=robot.speed_scale)
	add_child(slow)
	_apply_clip()

func _new_robot(at: Vector2, pixel_scale: int) -> AnimatedSprite2D:
	var sprite:=AnimatedSprite2D.new()
	sprite.sprite_frames=frames
	sprite.centered=false
	sprite.offset=Vector2(-32,-80)
	sprite.position=at
	sprite.scale=Vector2.ONE*pixel_scale
	sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(sprite)
	return sprite

func _apply_clip() -> void:
	var clip:=action+"_"+direction
	var unavailable:=not frames.has_animation(clip)
	if unavailable: clip="pose_"+direction
	var previous:=robot.frame
	for sprite in [robot,native_robot]:
		sprite.play(clip)
		sprite.frame=previous%frames.get_frame_count(clip)
		if paused: sprite.pause()
	status_label.text="%s | %s | fixed root (32,80) | %s\nTab: pose/walk  Space: pause  Left/Right while paused: frame  B: background"%[direction,clip,"walk not produced yet; static candidate shown" if unavailable else "new assets pending art review"]

func _unhandled_key_input(event: InputEvent) -> void:
	if not event.is_pressed() or event.is_echo(): return
	if event.keycode==KEY_SPACE:
		paused=not paused
		_apply_clip()
	elif event.keycode==KEY_TAB:
		action="pose" if action=="walk" else "walk"
		_apply_clip()
	elif event.keycode==KEY_B:
		light=not light
		RenderingServer.set_default_clear_color(Color("ece9d8" if light else "182631"))
	elif paused and event.keycode in [KEY_LEFT,KEY_RIGHT]:
		robot.frame=posmod(robot.frame+(-1 if event.keycode==KEY_LEFT else 1),frames.get_frame_count(robot.animation))
		native_robot.frame=robot.frame
	else:
		var input:=Vector2(float(Input.is_physical_key_pressed(KEY_D))-float(Input.is_physical_key_pressed(KEY_A)),float(Input.is_physical_key_pressed(KEY_S))-float(Input.is_physical_key_pressed(KEY_W)))
		if input!=Vector2.ZERO:
			var mapping:={Vector2(0,1):"down",Vector2(-1,1):"down_left",Vector2(-1,0):"left",Vector2(-1,-1):"up_left",Vector2(0,-1):"up",Vector2(1,-1):"up_right",Vector2(1,0):"right",Vector2(1,1):"down_right"}
			direction=mapping[input]
			_apply_clip()
