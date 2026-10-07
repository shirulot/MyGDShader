extends Node2D
## 独立原地动作预览：不添加采集判定或主工程输入映射。
const DIRECTIONS := ["down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right"]
var robot: AnimatedSprite2D
var native: AnimatedSprite2D
var info: Label
var direction_index := 0
var action := "idle"

func _ready() -> void:
	var frames := load("res://assets/ember/robot_v011/robot_eight_way_v011.tres") as SpriteFrames
	robot = _sprite(frames, 4, Vector2(430, 490))
	native = _sprite(frames, 1, Vector2(800, 365))
	var title := Label.new()
	title.text = "EIGHT DIRECTIONS — Q/E: direction  1: idle  2: walk  3: collect  Space: pause"
	title.position = Vector2(24, 24)
	add_child(title)
	info = Label.new()
	info.position = Vector2(24, 580)
	add_child(info)
	robot.animation_finished.connect(_on_finished)
	play_action("idle")

func _sprite(frames: SpriteFrames, size: int, at: Vector2) -> AnimatedSprite2D:
	var sprite := AnimatedSprite2D.new()
	sprite.sprite_frames = frames
	sprite.centered = false
	sprite.offset = Vector2(-32, -80)
	sprite.position = at
	sprite.scale = Vector2.ONE * size
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(sprite)
	return sprite

func play_action(next_action: String) -> void:
	action = next_action
	var clip: String = action + "_" + DIRECTIONS[direction_index]
	robot.play(clip)
	robot.frame = 0
	native.play(clip)
	native.frame = 0

func set_direction(index: int) -> void:
	# 采集进行中锁定朝向；循环动作切向保留相同步相。
	if action == "collect" and robot.is_playing(): return
	var phase := robot.frame
	direction_index = posmod(index, DIRECTIONS.size())
	play_action(action)
	robot.frame = phase
	native.frame = phase

func _on_finished() -> void:
	if action == "collect": play_action("idle")

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.is_pressed() or event.is_echo(): return
	match event.keycode:
		KEY_1: play_action("idle")
		KEY_2: play_action("walk")
		KEY_3: play_action("collect")
		KEY_Q: set_direction(direction_index - 1)
		KEY_E: set_direction(direction_index + 1)
		KEY_SPACE:
			if robot.is_playing(): robot.pause(); native.pause()
			else: robot.play(); native.play()

func _process(_delta: float) -> void:
	native.frame = robot.frame
	info.text = "%s / F%02d — root (32,80); 24 clips / 112 frames" % [robot.animation, robot.frame]
