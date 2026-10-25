extends Node2D
## 教师准备的观察连线：切换同一表面的法线，不包含自定义光照算法。

const KNOWN_NORMAL: Texture2D = preload("res://assets/ember/data/calibration/test_normal_v001.png")

@onready var surface: Sprite2D = $Surface
@onready var lamp: PointLight2D = $Lamp
@onready var status: Label = $HUD/Status

var normal_enabled: bool = false


func _ready() -> void:
	_update_surface()


func _unhandled_input(event: InputEvent) -> void:
	# 仅在本实验窗口中响应鼠标移动，不接管桌面输入。
	if event is InputEventMouseMotion:
		lamp.position = get_local_mouse_position()
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_N:
			normal_enabled = not normal_enabled
			_update_surface()


func _update_surface() -> void:
	# 切换时底色、位置、材质、灯位均不变，方便比较同一点的受光差别。
	var canvas_texture := surface.texture as CanvasTexture
	canvas_texture.normal_texture = KNOWN_NORMAL if normal_enabled else null
	status.text = "N：切换法线  |  当前：%s" % ("D07 已知法线" if normal_enabled else "平面")
