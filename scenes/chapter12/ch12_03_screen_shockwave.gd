extends Control

# 脚本挂在当前实验根节点；ScreenEffect有本场景独立的ShaderMaterial。
@onready var effect_material: ShaderMaterial = $ScreenEffect.material as ShaderMaterial

var tween :Tween = null

func _ready() :
	$ScreenEffect.material.set_shader_parameter("refraction_px",0.0);

func _unhandled_input(event: InputEvent) -> void:
	# 当前仅预留输入入口。
	# 本步由你判断鼠标左键按下，将点击的viewport位置转换为center_uv并传入材质。
	# 后续再接Tween重播与结束，不在这里提前代写。
	if event is InputEventMouseButton && event.is_pressed() && event.button_index == MOUSE_BUTTON_LEFT:
		var visible_rect := get_viewport().get_visible_rect();
		if tween!= null && tween.is_valid():
			tween.kill();
		tween = create_tween();
		# 后面添加的两条动画同时开始。
		tween.set_parallel(true);
		var click_point = event.position;
		var click_uv = click_point / Vector2(visible_rect.size);
		$ScreenEffect.material.set_shader_parameter("center_uv",click_uv);
		$ScreenEffect.material.set_shader_parameter("ring_radius",0.0);
		tween.tween_property($ScreenEffect.material,"shader_parameter/ring_radius",0.6,0.6)
		tween.tween_property($ScreenEffect.material,"shader_parameter/refraction_px",0.0,0.6)
		$ScreenEffect.material.set_shader_parameter("refraction_px",12.0);
		pass
