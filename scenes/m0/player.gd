extends CharacterBody2D


const SPEED = 300.0
const JUMP_VELOCITY = -400.0

var is_hit_flash = false
var flashProgress = 0.0

func _ready() -> void:
	Game.gameReset.connect(game_reset.bind())

func game_reset()->void:
	is_hit_flash = false
	$Timer.stop()
	_stop_flahs()
	position = Vector2(360,360)
	
func _physics_process(delta: float) -> void:
	if !Game.isGameStarting : return
	var moveHorizontal = Input.get_axis("move_left","move_right")
	var moveVertical = Input.get_axis("move_up","move_down")
	if moveHorizontal != 0.0 and moveVertical != 0.0 :
		velocity.x = moveHorizontal * 0.7  * SPEED
		velocity.y = moveVertical * 0.7 * SPEED
	else :
		velocity.x = moveHorizontal  * SPEED
		velocity.y = moveVertical * SPEED
	if is_hit_flash :
		_hint_flash(delta)
		
	move_and_slide()
	
func _hint_flash(delta:float) ->void:
	flashProgress += delta / $Timer.wait_time
	if flashProgress > 1.0 :
		_stop_flahs()
	else:
		var t : int = flashProgress / 0.125
		var isPlus = t % 2 >= 1
		var newProgress = flashProgress - t * 0.125 if isPlus else 0.125 - (flashProgress- t * 0.125)
		$Sprite2D.material.set_shader_parameter("progress",newProgress*8)

func _stop_flahs()->void:
	is_hit_flash = false
	flashProgress = 0.0
	$Sprite2D.material.set_shader_parameter("progress",0)
	
func take_damage(damage:int)->void:
	if !Game.isGameStarting : return
	if !$Timer.is_stopped() : 
		return
	Game.update_life_point(maxi(Game.lifePoint - damage, 0))
	if !Game.isGameStarting: 
		_stop_flahs()
		Game.lifePoint = 0
		print("收到伤害 剩余生命 0 玩家死亡")
		Game.player_deatch()
		return
	else :
		is_hit_flash = true
	print("收到伤害 剩余生命",Game.lifePoint)
	$Timer.start()
