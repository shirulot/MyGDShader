extends Node2D


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	$CanvasLayer/Control/VBoxContainer/LastTimer.text = "Timer:%.2f" % Game.countdown
	$CanvasLayer/Control/VBoxContainer/Energy.text = "Energy:%.2f" % Game.energyPoint
	$CanvasLayer/Control/VBoxContainer/LifePoint.text = "HP:%.d"%Game.lifePoint
	$CanvasLayer/Control/VBoxContainer/Result.text = get_result_type()

func get_result_type() -> String:
	if Game.result == Game.ResultType.PLAYER_DEATH :
		return "玩家死亡"
	elif Game.result == Game.ResultType.POINT_WIN :
		return "得分胜利"
	else  :
		return "时间结束"

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
