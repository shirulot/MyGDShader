extends Node2D

# 脚本挂在当前实验根节点；ScreenEffect有本场景独立的ShaderMaterial。
@onready var effect_material: ShaderMaterial = $ScreenEffect.material as ShaderMaterial


func _unhandled_input(event: InputEvent) -> void:
	# 当前仅预留输入入口。
	# 本步由你判断鼠标左键按下，将点击的viewport位置转换为center_uv并传入材质。
	# 后续再接Tween重播与结束，不在这里提前代写。
	pass
