extends Node


# 复用你在 11.1 写通的表现端；这里只把血量状态转成显示，不扣血。
@onready var robot: Sprite2D = $"../Robot"
@onready var hp_label: Label = $"../HPLabel"
@onready var proxy = $"../DamageProxy"

var tween: Tween = null

func _ready() -> void:
	proxy.damage.connect(_on_damaged);
	proxy.health_changed.connect(_update_hp)
	proxy.died.connect(_on_died)
	_update_hp(proxy.hp, proxy.max_hp)
	# 连接 health_changed；连接后主动同步一次初始 HP 和画面。

func _update_hp(hp:int , max_hp:int) -> void :
	hp_label.text = "HP：%d（满血 %d）"%[hp,max_hp]
	if hp == 0 : return
	var danger_progress = clamp(1.0 - hp * 1.0 / max_hp,0.0,1.0);
	robot.material.set_shader_parameter("danger_progress", danger_progress);

func _on_damaged() -> void:
	# 以下是你已完成的闪白逻辑，继续只控制瞬时 white_flash。
	if tween != null && tween.is_valid():
		tween.kill()
	tween = create_tween()
	robot.material.set_shader_parameter("white_flash", 1.0 );
	tween.tween_property(robot.material, "shader_parameter/white_flash", 0.0, 0.3);

func _on_died() :
	if tween != null && tween.is_valid():
		tween.kill()
		robot.material.set_shader_parameter("white_flash", 0.0 );
	tween = create_tween()
	robot.material.set_shader_parameter("dissolve_progress", 1.0 );
	tween.tween_property(robot.material, "shader_parameter/dissolve_progress", 0.0, 1.0);
	tween.finished.connect(_on_death_finished)

func _on_death_finished():
	robot.visible = false 
