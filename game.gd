extends Node

var lifePoint:int = 3
var energyPoint :float = 0
var countdown :int = 120
var isGameStarting = true

signal lifeChange()
signal energyPointChange()
signal gameReset()

var gameTimer : Timer = null
var result :ResultType = -1

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	if Input.is_action_just_pressed("reset"):
		gameReset.emit()
		game_reset()

func game_reset()->void:
	lifePoint = 3
	energyPoint = 0
	countdown = 120
	isGameStarting = true
	lifeChange.emit()
	energyPointChange.emit()
	if gameTimer !=null :
		gameTimer.start()
	get_tree().change_scene_to_file("res://scenes/m0/ember_harvest.tscn")
	

func update_energy_point(point:float) ->void:
	energyPoint = point
	energyPointChange.emit()
	if energyPoint >= 380:
		point_win()
	
func update_life_point(hp :float)->void:
	lifePoint = hp
	lifeChange.emit()
	if lifePoint <= 0 :
		player_deatch()
	
func countdown_tick() -> void:
	countdown = maxi(countdown - 1,0)
	if countdown <= 0 :
		timer_out()

func player_deatch() -> void:
	isGameStarting = false
	print("玩家死亡")
	if gameTimer != null :
		gameTimer.stop()
	result = ResultType.PLAYER_DEATH
	to_result()
	
func point_win() -> void:
	isGameStarting = false
	print("得分胜利")
	if gameTimer != null :
		gameTimer.stop()
	result = ResultType.POINT_WIN
	to_result()
	
func timer_out() -> void:
	isGameStarting = false
	print("倒计时归零")
	if gameTimer != null :
		gameTimer.stop()
	result = ResultType.TIME_OUT
	to_result()
	
func to_result() -> void:
	get_tree().change_scene_to_file("res://scenes/m0/game_result.tscn")

enum ResultType {
	PLAYER_DEATH,POINT_WIN,TIME_OUT
}
