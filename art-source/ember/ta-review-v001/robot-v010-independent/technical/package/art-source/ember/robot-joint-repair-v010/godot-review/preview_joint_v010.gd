extends Node2D
## 空格暂停，左右键逐帧；B 切换深浅背景。
var light := false
func _ready() -> void:
	RenderingServer.set_default_clear_color(Color("182631"))
func _unhandled_key_input(event: InputEvent) -> void:
	if not event.is_pressed() or event.is_echo(): return
	var robot := $Robot as AnimatedSprite2D
	if event.keycode == KEY_SPACE:
		if robot.is_playing(): robot.pause()
		else: robot.play("walk_down")
	elif event.keycode == KEY_LEFT or event.keycode == KEY_RIGHT:
		robot.pause()
		robot.frame = posmod(robot.frame + (-1 if event.keycode == KEY_LEFT else 1),8)
	elif event.keycode == KEY_B:
		light = not light
		RenderingServer.set_default_clear_color(Color("ece9d8" if light else "182631"))
