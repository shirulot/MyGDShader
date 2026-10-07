extends SceneTree
## v003返修回归：复用TA原8项探针，仅更换报告路径；当前执行由UI生产方完成，TA复审仍单独进行。

const HUD = preload("res://scenes/ember/ui_edge_v001/components/edge_hud.tscn")
var _world_clicks: int = 0
var _closed: int = 0
var _checks: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("_run")

func _check(id: String, passed: bool, detail: Dictionary = {}) -> void:
	_checks.append({"id": id, "pass": passed, "details": detail})

func _click(view: SubViewport, at: Vector2) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = at
	motion.global_position = at
	view.push_input(motion, true)
	for pressed_value in [true, false]:
		var event := InputEventMouseButton.new()
		event.position = at
		event.global_position = at
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed_value
		view.push_input(event, true)

func _run() -> void:
	var view := SubViewport.new()
	view.size = Vector2i(720, 720)
	root.add_child(view)
	var world := Button.new()
	world.size = Vector2(720, 720)
	world.focus_mode = Control.FOCUS_NONE
	view.add_child(world)
	world.pressed.connect(func(): _world_clicks += 1)
	var canvas := CanvasLayer.new()
	view.add_child(canvas)
	var hud: Control = HUD.instantiate()
	canvas.add_child(hud)
	hud.drawer_closed.connect(func(): _closed += 1)
	await process_frame
	await process_frame
	_click(view, Vector2(60, 340))
	_check("input.life_overlay_passes_click_to_world", _world_clicks == 1)
	_click(view, Vector2(100, 670))
	_check("input.energy_overlay_passes_click_to_world", _world_clicks == 2)
	hud.open_drawer()
	await process_frame
	_click(view, Vector2(620, 350))
	_check("input.drawer_blocks_world_click", _world_clicks == 2)
	var drawer: Control = hud.get_drawer()
	var back: Button = drawer.get_back_button()
	_click(view, back.global_position + back.size / 2)
	_check("input.back_real_mouse_click_closes_once", not hud.is_drawer_open() and _closed == 1)
	_click(view, Vector2(620, 350))
	_check("input.closed_drawer_restores_world_click", _world_clicks == 3)
	hud.open_drawer()
	await process_frame
	var key := InputEventKey.new()
	key.keycode = KEY_ENTER
	key.pressed = true
	view.push_input(key, true)
	key = InputEventKey.new()
	key.keycode = KEY_ENTER
	key.pressed = false
	view.push_input(key, true)
	_check("input.keyboard_confirm_closes_focus_button", not hud.is_drawer_open() and _closed == 2)
	# 保留 HUD 后从树中移出，再由外部状态同步关闭抽屉。此路径不同于新建未入树。
	hud.open_drawer()
	await process_frame
	canvas.remove_child(hud)
	hud.set_drawer_open(false)
	_check("lifecycle.detached_hud_external_close_hides_drawer", not drawer.visible, {"hud_open": hud.is_drawer_open(), "drawer_visible": drawer.visible})
	canvas.add_child(hud)
	await process_frame
	_check("lifecycle.reinserted_hud_external_close_is_consistent", not hud.is_drawer_open() and not drawer.visible, {"hud_open": hud.is_drawer_open(), "drawer_visible": drawer.visible})
	var failures: Array = _checks.filter(func(item: Dictionary): return not item["pass"])
	var report := {"checks": _checks, "check_count": _checks.size(), "failures": failures, "status": "PASS" if failures.is_empty() else "FAIL"}
	var output := FileAccess.open("res://art-source/ember/ui-edge-v001/ta-regression-v003.json", FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "\t"))
	output.close()
	print("TA_INDEPENDENT ", JSON.stringify(report))
	view.free()
	quit(0 if failures.is_empty() else 1)

