extends Area2D

var player :CharacterBody2D = null
var damageTarget :CharacterBody2D = null
@export
var initTimer:float = 0

var getPointSpeed :float= 5.0
#安全
var enrgyState :EnergyStatus = EnergyStatus.SAFE 
var lastState :EnergyStatus= -1
@onready
var stateTimer:Timer = $Timer
var progress:float = 0.0
@onready
var spriteMaterial = $Sprite2D.material
signal energy_collected(point:float )
var isGetPoint = false
# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	stateTimer.timeout.connect(startStatusChange.bind(false))
	enrgyState = randi_range(2,3)
	startStatusChange(true)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _physics_process(delta: float) -> void:
	spriteMaterial.set_shader_parameter("collecting",Game.isGameStarting&& isGetPoint)
	if !Game.isGameStarting : return
	var isPlayerNoMove = player != null && player.velocity.is_zero_approx()
	var isCanGet = enrgyState == EnergyStatus.SAFE || enrgyState == EnergyStatus.WARNING
	if isPlayerNoMove && isCanGet:
		if !isGetPoint:
			isGetPoint = true
			print("开始采集")
		if Game.isGameStarting :	
			energy_collected.emit(delta * getPointSpeed)
	elif isGetPoint:
		isGetPoint = false;
		print("停止采集")
	_update_color(delta)	
	
	if damageTarget != null && enrgyState == EnergyStatus.BURST:
		damageTarget.take_damage(1)
	
func _update_color(delta: float)->void:
	if lastState != enrgyState:
		progress = 0.0
		spriteMaterial.set_shader_parameter("stateProgress",progress)
		spriteMaterial.set_shader_parameter("state",enrgyState)
		lastState = enrgyState
	
	progress += delta / _getDalte(); 
	spriteMaterial.set_shader_parameter("stateProgress",progress)
	
	
func _on_player_enter(body :Node2D) -> void:
	print("玩家进入采能区")
	if body is CharacterBody2D :
		player = body


func _on_player_exite(body :Node2D) -> void:
	if body == player:
		print("玩家离开采能区")
		player = null
		isGetPoint = false

var dalteTime = 0.0
var isInitState = false
func startStatusChange(isInit:bool) -> void:
	if isInit:
		set_physics_process(false)
		print("init")
		isInitState = true
		dalteTime = randf_range(0,_getDalte())
		await get_tree().create_timer(dalteTime).timeout
		set_physics_process(true)
	elif enrgyState == EnergyStatus.SAFE:
		enrgyState = EnergyStatus.WARNING
	elif enrgyState == EnergyStatus.WARNING:
		enrgyState = EnergyStatus.BURST
	elif enrgyState == EnergyStatus.BURST:
		enrgyState = EnergyStatus.COOLDOWN
	elif enrgyState == EnergyStatus.COOLDOWN:
		enrgyState = EnergyStatus.SAFE
	
	# name 是当前站点实例的节点名称。
	print("%s 当前状态：%s" % [name, enrgyState])	
	
	stateTimer.start(_getDalte())
	
func _getDalte()->float:
	return 3.0 if enrgyState == EnergyStatus.SAFE else 2.0
	
enum EnergyStatus{
	SAFE,WARNING,BURST,COOLDOWN
}

func _on_damage_area_body_entered(body: Node2D) -> void:
	damageTarget = body


func _on_damage_area_body_exited(body: Node2D) -> void:
	if damageTarget == body :
		damageTarget = null
