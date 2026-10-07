extends Node2D
## 素材预览专用控制器：没有接入旧玩家、碰撞、导航或课程 Shader。
## 十二个小样以原生像素整数 4 倍显示；采集资源本身不循环，展示时在结束后停顿重播。

const DIRECTIONS := ["down", "left", "right", "up"]
const DISPLAY_SIZE := Vector2i(1536, 1024)
const PLAYER_BOUNDS := Rect2(1224, 600, 176, 350)
const SPEED := 150.0
var facing := "down"
var collecting := false
var collect_restart_count: Dictionary = {}
@onready var actor: AnimatedSprite2D = $Interactive/Actor
@onready var status_label: Label = $Interactive/Status

func _ready() -> void:
	# 仅调整此独立预览窗口，不写入项目的显示设置。
	get_window().content_scale_size = DISPLAY_SIZE
	if DisplayServer.get_name() != "headless": get_window().size = DISPLAY_SIZE
	for direction: String in DIRECTIONS:
		var sample := get_node("Grid/Collect" + direction.capitalize()) as AnimatedSprite2D
		collect_restart_count[direction] = 0
		sample.animation_finished.connect(_replay_collect.bind(sample, direction))
	actor.animation_finished.connect(_finish_actor_collect)
	_update_status()

func _physics_process(delta: float) -> void:
	var move := Vector2(
		float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),
		float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))
	preview_step(move, delta)

func preview_step(move: Vector2, delta: float) -> void:
	# 同一公开入口也用于自动验证方向、动画切换和采集结束状态。
	if collecting: return
	if move != Vector2.ZERO:
		if absf(move.x) > absf(move.y): facing = "right" if move.x > 0.0 else "left"
		else: facing = "down" if move.y > 0.0 else "up"
		actor.position += move.normalized() * SPEED * delta
		actor.position.x = clampf(actor.position.x, PLAYER_BOUNDS.position.x, PLAYER_BOUNDS.end.x)
		actor.position.y = clampf(actor.position.y, PLAYER_BOUNDS.position.y, PLAYER_BOUNDS.end.y)
		actor.play("walk_" + facing)
	else:
		actor.play("idle_" + facing)
	_update_status()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode in [KEY_SPACE, KEY_E] or event.keycode in [KEY_SPACE, KEY_E]:
			start_collect()
			get_viewport().set_input_as_handled()

func start_collect() -> void:
	if collecting: return
	collecting = true
	actor.play("collect_" + facing)
	_update_status()

func _finish_actor_collect() -> void:
	if str(actor.animation).begins_with("collect_"):
		collecting = false
		actor.play("idle_" + facing)
		_update_status()

func _replay_collect(sample: AnimatedSprite2D, direction: String) -> void:
	# 资源是不循环动作；这个小样显式等待后重播，不能混淆两种语义。
	await get_tree().create_timer(0.35).timeout
	if is_instance_valid(sample) and sample.is_inside_tree():
		sample.set_frame_and_progress(0, 0.0)
		sample.play()
		collect_restart_count[direction] = int(collect_restart_count[direction]) + 1

func _update_status() -> void:
	status_label.text = "朝向: %s\n动作: %s" % [facing, str(actor.animation)]
