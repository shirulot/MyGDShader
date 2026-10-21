extends Node

# 表现接收者：接收通知后控制 Robot 的独立材质，不决定伤害规则。
# 本节点与 Robot、DamageProxy 同级，故使用 ../ 定位。
@onready var robot: Sprite2D = $"../Robot"

func _ready() -> void:
	# TODO：连接 DamageProxy 的受击通知与本脚本的接收方法。
	$"../DamageProxy".damage.connect(_on_damaged.bind());
	pass

var tween:Tween = null

func _on_damaged() -> void:
	# TODO：迁移 C10 的写参/Tween方法，实现白色闪光并用 0.3 秒恢复。
	if tween != null && tween.is_valid():
		tween.kill()
	tween = create_tween()
	robot.material.set_shader_parameter("white_flash",1.0);
	tween.tween_property(robot.material,"shader_parameter/white_flash",0.0,0.3);
	pass
