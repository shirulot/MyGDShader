extends Node2D

# Chapter 10.3：复用学习者已完成的 10.2 控制逻辑，只操作左侧 Robot。
# Robot 和 RobotB 在新场景中引用同一个 ShaderMaterial，先观察共享现象。
# 本起点没有预写材质隔离逻辑，后续由学习者实现。
@onready var robot :Sprite2D = $Robot

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.

#
## Called every frame. 'delta' is the elapsed time since the previous frame.
#func _process(delta: float) -> void:
	#if Input.is_action_just_pressed("flash") :
		#robot.material.set_shader_parameter("white_flash",1.0);
var tween:Tween = null
func _unhandled_key_input(event: InputEvent) -> void:
	if !event.is_pressed() or event.is_echo() : return;
	kill_tween()
	if event.physical_keycode == KEY_SPACE :
		set_shader_parameter("hit_color",Color(1.0, 1.0, 1.0, 1.0));
		set_shader_parameter("white_flash",1.0);
		new_tween()
		tween_shader_param("white_flash",0.0,0.3);
	elif event.physical_keycode == KEY_B: 
		set_shader_parameter("white_flash",0.0);
		set_shader_parameter("hit_color",Color(1.0, 1.0, 1.0, 1.0));
	elif event.physical_keycode == KEY_C:
		set_shader_parameter("hit_color",Color(1.0, 0.35, 0.15, 1.0));
		set_shader_parameter("white_flash",1.0);
		new_tween()
		tween_shader_param("white_flash",0.0,0.3);
		tween_shader_param("hit_color",Color(1.0, 1.0, 1.0, 1.0),0.3);
	print(robot.material.get_shader_parameter("white_flash"));

func set_shader_parameter(name,value) -> void :
		robot.material.set_shader_parameter(name,value);
		
func tween_shader_param(name,end,time) -> void :
		tween.tween_property(robot.material,"shader_parameter/"+name,end,time);

func kill_tween() ->void:
	if tween != null and tween.is_valid():
			tween.kill()
func new_tween() -> void:
	tween = create_tween();
	tween.set_trans(Tween.TRANS_QUAD)
	tween.set_ease(Tween.EASE_OUT)
