extends Node2D
## 独立角色预览控制器，不替换课程玩家或 Shader。
@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
var facing := "down"

func _process(delta: float) -> void:
	var direction := Input.get_vector("move_left","move_right","move_up","move_down")
	if direction != Vector2.ZERO:
		if absf(direction.x) > absf(direction.y):
			facing = "right" if direction.x > 0 else "left"
		else:
			facing = "down" if direction.y > 0 else "up"
		position += direction * 100.0 * delta
		position = position.clamp(Vector2(40,535),Vector2(680,700))
		sprite.play("walk_"+facing)
	else:
		sprite.play("idle_"+facing)
