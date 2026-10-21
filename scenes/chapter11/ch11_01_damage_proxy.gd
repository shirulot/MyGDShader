extends Node

# 事件发起者：只通知发生了受击，不读取机器人或 Shader 参数。
# TODO：由你声明本节的 damaged 信号。

signal damage();

func _on_simulate_damage_pressed() -> void:
	# 按钮已连接到这里；由你发送受击通知。
	damage.emit();
	pass
