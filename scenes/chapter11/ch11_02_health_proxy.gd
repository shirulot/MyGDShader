extends Node

var max_hp := 100
@export var hp := max_hp
# 复用你在 11.1 写通的受击通知；本节点负责血量，不操作 Shader。
signal damage();
signal health_changed(hp,max_hp);
signal died();
# TODO：增加满血值、当前 HP，以及携带当前 HP / 满血值的 health_changed 信号。
# 本次满血 100，每次伤害 25；HP 的计算与通知顺序由你实现。

func _on_ready() :
	health_changed.emit(hp,max_hp)

func _on_simulate_damage_pressed() -> void:
	# TODO：先更新并限制 HP，再通知血量变化。下面保留原来的瞬时受击通知。
	if hp <= 0 : 
		return
	hp = clamp(hp - 25 , 0 , max_hp)
	health_changed.emit(hp,max_hp)
	if hp > 0 : 
		damage.emit();
	else :
		died.emit();
