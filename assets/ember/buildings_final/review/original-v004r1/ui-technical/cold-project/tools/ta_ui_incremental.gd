extends SceneTree
## 独立冷包 UI 增量：走 Input.parse_input_event，不直接调用 toast 或键盘回调。
const DEMO = preload("res://scripts/ember/building_demo_v004r1.gd")
var scene
var checks: Array[Dictionary] = []
var rectangles: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("_run")

func record(name: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": name, "pass": passed, "detail": detail})
	if not passed: print("TA_FAIL: ", name, " ", detail)

func rect_data(control: Control) -> Dictionary:
	var r := control.get_global_rect()
	return {"position": [r.position.x, r.position.y], "size": [r.size.x, r.size.y], "text": control.text, "visible": control.visible}

func key_press(code: Key) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = true
	Input.parse_input_event(event)
	await process_frame
	await process_frame
	event = InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = false
	Input.parse_input_event(event)
	await process_frame

func capture(path: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(path)

func _run() -> void:
	root.size = Vector2i(1408, 800)
	scene = DEMO.new()
	root.add_child(scene)
	scene.actor.set_physics_process(false)
	for building in scene.buildings: building.set_process(false)
	await process_frame
	await process_frame
	var viewport := Rect2(Vector2.ZERO, Vector2(root.size))
	# 旧失效的两个控件与3个建筑名字均要求完整落在视口内，不只相交。
	for control: Control in [scene.help_label, scene.toast_label]:
		var data := rect_data(control)
		rectangles.append(data)
		record("inside_viewport_" + control.name, viewport.encloses(control.get_global_rect()), data)
	for index: int in scene.building_labels.size():
		var control: Control = scene.building_labels[index]
		var data := rect_data(control)
		rectangles.append(data)
		record("building_label_inside_" + str(index), viewport.encloses(control.get_global_rect()), data)
	record("help_content", scene.help_label.text.contains("F5/F9") and scene.help_label.text.contains("E 人门"))
	# 构造真实门锁状态，并从原键盘路由按E，以检查拒绝信号→toast→自然_process可见链。
	var building = scene.buildings[0]
	scene.actor.position = building.position + Vector2(float(building.doors.personnel.center_x), 27)
	building.set_locked("personnel", true)
	await process_frame
	await key_press(KEY_E)
	record("actual_E_routes_to_locked_door", scene.toast_label.text == "门已锁定", rect_data(scene.toast_label))
	record("actual_E_toast_is_visible", scene.toast_label.visible)
	record("actual_E_toast_unclipped", viewport.encloses(scene.toast_label.get_global_rect()), rect_data(scene.toast_label))
	record("actual_E_does_not_open_locked_door", building.doors.personnel.locked and is_zero_approx(float(building.doors.personnel.target)) and is_zero_approx(float(building.doors.personnel.progress)))
	record("help_and_toast_do_not_overlap", not scene.help_label.get_global_rect().intersects(scene.toast_label.get_global_rect()))
	await capture("res://ta-ui-locked-E.png")
	await key_press(KEY_F5)
	record("actual_F5_feedback", scene.toast_label.visible and scene.toast_label.text == "已保存建筑状态", rect_data(scene.toast_label))
	await capture("res://ta-ui-saved-F5.png")
	var failed: Array[Dictionary] = []
	for item: Dictionary in checks:
		if not item["pass"]: failed.append(item)
	var report := {"scope": "v004r1 UI P2 closure only; actual E/F5 input pipeline and unclipped labels",
		"total": checks.size(), "passed": checks.size() - failed.size(), "checks": checks, "failures": failed,
		"initial_control_rectangles": rectangles, "engine": Engine.get_version_info(),
		"renderer": RenderingServer.get_video_adapter_name()}
	var file := FileAccess.open("res://ta-ui-incremental-result.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	print("TA_UI_R1: ", report.passed, "/", report.total)
	quit(0 if failed.is_empty() else 1)
