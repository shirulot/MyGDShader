extends Control


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	Game.energyPointChange.connect(update_energy_point.bind())
	Game.lifeChange.connect(update_life_point_ui.bind())
	update_energy_point()
	update_life_point_ui()
	Game.gameTimer = $"../../GameTimer"

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
	
func update_energy_point() -> void:
	$VBoxContainer/EnergyLabel.text = "Energy:%.2f" % Game.energyPoint

func update_life_point_ui() -> void :
	$VBoxContainer/LifeLabel.text = "HP:%.d"%Game.lifePoint


func _on_game_timer_timeout() -> void:
	Game.countdown_tick()
	$Countdown.text = "Timer:%.d"%Game.countdown
	if !Game.isGameStarting :
		$Countdown.text = "时间到"
		$"../../GameTimer".stop()
