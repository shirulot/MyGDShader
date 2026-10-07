extends CharacterBody2D
## 复用原64×96机器人图，虚拟脚底(32,80)，sprite scale=0.65。
## 实际地面碰撞仅18×12 world；建筑门口按这个接触盒验收。

@export var speed := 92.0
@export var input_enabled := true


func _ready() -> void:
	collision_layer = 2
	collision_mask = 1
	var sprite := Sprite2D.new()
	sprite.name = "ExistingRobot"
	sprite.texture = load("res://assets/ember/characters/robot/robot_idle_down_v001.png") as Texture2D
	sprite.centered = false
	sprite.offset = Vector2(-32, -80)
	sprite.scale = Vector2(0.65, 0.65)
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(sprite)
	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(18, 12)
	collision.shape = shape
	collision.position = Vector2(0, -6)
	add_child(collision)


func _physics_process(_delta: float) -> void:
	if not input_enabled: return
	var direction := Vector2(
		float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),
		float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))
	velocity = direction.normalized() * speed
	move_and_slide()
	position = position.clamp(Vector2(12, 100), Vector2(1390, 785))


func ground_rect() -> Rect2:
	return Rect2(global_position + Vector2(-9, -12) * global_scale, Vector2(18, 12) * global_scale)
