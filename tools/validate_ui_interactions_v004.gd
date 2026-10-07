extends SceneTree
## 真正向Viewport分发鼠标/键盘；覆盖焦点栈、遮罩、设置事务、断线及重挂。
const FLOW = preload("res://scenes/ember/ui_edge_v004/interaction_ui.tscn")
const OUT := "res://art-source/ember/ui-interactions-v004/"
var checks: Array[Dictionary] = []
var view: SubViewport
var ui: Control
var world_clicks := 0
var restarts := 0

func _initialize() -> void:
	_run.call_deferred()

func check(id: String, condition: bool) -> void:
	checks.append({"id":id,"pass":condition})
	if not condition:
		print("FAIL ", id)

func click(point: Vector2) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = point
	view.push_input(motion, true)
	for pressed in [true,false]:
		var event := InputEventMouseButton.new()
		event.position = point
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		view.push_input(event, true)

func key(code: Key, shift: bool = false) -> void:
	for pressed in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.shift_pressed = shift
		event.pressed = pressed
		view.push_input(event, true)

func button(name: String) -> Button:
	return ui.window.body.get_node(name) as Button

func choose(name: String) -> void:
	var target := button(name)
	ui.window.scroll.ensure_control_visible(target)
	await process_frame
	click(target.get_global_rect().get_center())
	await process_frame
	await process_frame

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	view = SubViewport.new()
	view.size = Vector2i(720,720)
	root.add_child(view)
	var world := Button.new()
	world.size = Vector2(720,720)
	world.focus_mode = Control.FOCUS_NONE
	view.add_child(world)
	world.pressed.connect(func(): world_clicks += 1)
	ui = FLOW.instantiate()
	ui.settings_path = ""
	view.add_child(ui)
	ui.restart_requested.connect(func(): restarts += 1)
	await process_frame
	await process_frame
	ui.set_game_state({"life":2,"max_life":3,"energy":145.0,"energy_goal":380.0,"seconds":78.0})
	var life: Control = ui.hud.get("_life")
	var slots: Array = life.get("_slots")
	check("life.horizontal3", slots.size() == 3 and slots[0].position.y == slots[2].position.y and slots[2].position.x > slots[1].position.x)
	check("life.two_filled_one_empty", slots[0].get_child(0).visible and slots[1].get_child(0).visible and not slots[2].get_child(0).visible)
	click(Vector2(300,400))
	check("hud.world_click_passthrough", world_clicks == 1)
	ui.details_button.grab_focus()
	click(ui.details_button.get_global_rect().get_center())
	await process_frame
	await process_frame
	check("details.mouse_opens", ui.page == "details" and ui.is_blocking())
	check("details.correct_percent", "38%" in ui._detail_values.text)
	click(Vector2(8,8))
	check("modal.backdrop_blocks_world", world_clicks == 1 and ui.page == "details")
	for index in range(12):
		key(KEY_TAB)
		var focused := view.gui_get_focus_owner()
		check("modal.focus_trap.%d" % index, focused != null and ui.window.is_ancestor_of(focused))
	ui.set_game_state({"station_connected":false})
	check("details.disconnect_clears_portrait", ui._detail_portrait.texture == null and ui._terminal_action.disabled and not ui.station_button.visible)
	ui.set_game_state({"station_connected":true,"station_state":2})
	check("details.live_state_update", "爆发" in ui._detail_status.text and ui._detail_portrait.texture != null)
	key(KEY_ESCAPE)
	check("modal.escape_restores_entry_focus", ui.page.is_empty() and ui.details_button.has_focus())
	ui.open_details()
	await process_frame
	await choose("Terminal")
	check("details.pin_terminal", ui.page.is_empty() and ui.hud.is_drawer_open())
	key(KEY_ESCAPE)
	check("drawer.escape_closes", not ui.hud.is_drawer_open())
	click(ui.menu_button.get_global_rect().get_center())
	await process_frame
	check("pause.mouse_opens", ui.page == "pause")
	await choose("Settings")
	check("settings.opens", ui.page == "settings")
	var slider := ui.window.body.get_node("SafeMargin") as HSlider
	slider.value = 52
	await choose("Markers")
	await choose("Cancel")
	check("settings.cancel_transaction", ui.page == "pause" and ui.preferences.safe_margin == 36 and ui.preferences.show_markers)
	check("settings.cancel_restores_focus", button("Settings").has_focus())
	await choose("Settings")
	slider = ui.window.body.get_node("SafeMargin") as HSlider
	slider.value = 52
	await choose("Markers")
	await choose("Save")
	check("settings.save_applies", ui.preferences.safe_margin == 52 and not ui.preferences.show_markers and ui.hud.safe_margin == 52)
	await choose("Restart")
	check("confirm.default_cancel_focus", ui.page == "confirm_restart" and button("Cancel").has_focus())
	key(KEY_ENTER)
	await process_frame
	check("confirm.enter_cancels", ui.page == "pause" and restarts == 0)
	await choose("Restart")
	await choose("Confirm")
	check("confirm.single_restart", ui.page.is_empty() and restarts == 1)
	ui.open_pause()
	await process_frame
	await choose("Help")
	check("help.back_stack", ui.page == "help")
	key(KEY_ESCAPE)
	await process_frame
	check("help.escape_restores_menu_focus", ui.page == "pause" and button("Help").has_focus())
	ui.show_result(true)
	await process_frame
	key(KEY_ESCAPE)
	check("result.cannot_escape_to_finished_round", ui.page == "success" and ui.is_blocking())
	await choose("Retry")
	check("result.retry", restarts == 2 and not ui.is_blocking())
	ui.show_result(false)
	await process_frame
	await choose("Title")
	check("result.to_title", ui.page == "title")
	await choose("Start")
	check("title.start", ui.page.is_empty())
	# 不同屏幕真实几何、生命条与时钟互不重叠，正文可滚动而标题固定。
	for dimensions in [Vector2i(320,480),Vector2i(480,640),Vector2i(720,720),Vector2i(960,540),Vector2i(1280,720),Vector2i(1920,1080)]:
		view.size = dimensions
		await process_frame
		await process_frame
		ui.set_game_state({"max_life":10,"life":7})
		for drawer_open in [false,true]:
			ui.hud.set_drawer_open(drawer_open)
			await process_frame
			var timer: Control = ui.hud.get("_timer")
			check("layout.life_timer.%s.%s" % [dimensions,drawer_open], not life.visible or not life.get_global_rect().intersects(timer.get_global_rect()))
		ui.hud.set_drawer_open(false)
		for target_page in ["details","pause","settings","help","confirm_restart","title","success","failure"]:
			ui._open(target_page, false, true)
			await process_frame
			await process_frame
			check("layout.window.%s.%s" % [dimensions,target_page], Rect2(Vector2.ZERO,Vector2(dimensions)).encloses(ui.window.panel.get_global_rect()))
			check("layout.body_width.%s.%s" % [dimensions,target_page], ui.window.body.size.x <= ui.window.scroll.size.x + 1)
	ui.close_all()
	view.size = Vector2i(720,720)
	ui.open_pause()
	await process_frame
	var same_window: int = ui.window.get_instance_id()
	view.remove_child(ui)
	check("lifecycle.detached_not_blocking", not ui.is_blocking())
	ui.close_all()
	view.add_child(ui)
	await process_frame
	check("lifecycle.closed_during_detach_stays_closed", ui.page.is_empty() and not ui.window.visible and ui.window.get_instance_id() == same_window)
	ui.open_pause()
	await process_frame
	ui.details_button.grab_focus()
	key(KEY_TAB)
	check("modal.external_focus_recovered_before_dispatch", ui.window.is_ancestor_of(view.gui_get_focus_owner()))
	# 设置落盘后重新创建组件读取；使用专项证据目录，不改玩家默认偏好文件。
	ui.close_all()
	ui.settings_path = OUT + "test-preferences.cfg"
	ui.open_pause()
	await process_frame
	await choose("Settings")
	slider = ui.window.body.get_node("SafeMargin") as HSlider
	slider.value = 44
	await choose("Save")
	var restored: Control = FLOW.instantiate()
	restored.settings_path = OUT + "test-preferences.cfg"
	view.add_child(restored)
	check("settings.disk_round_trip", restored.preferences.safe_margin == 44 and not restored.preferences.show_markers)
	restored.free()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(OUT + "test-preferences.cfg"))
	ui.free()
	var demo: Node2D = load("res://scenes/ember/ui_edge_interactive_v004.tscn").instantiate()
	demo.use_saved_preferences = false
	view.add_child(demo)
	demo.reset_session()
	var seconds: float = demo.current_seconds
	var energy: float = demo.current_energy
	demo.ui.open_pause()
	demo.advance_simulation(2)
	check("host.modal_freezes_clock_and_collection", demo.current_seconds == seconds and demo.current_energy == energy)
	demo.ui.close_all()
	demo.advance_simulation(2)
	check("host.resume_advances_once", demo.current_seconds == seconds - 2 and demo.current_energy == energy + 6)
	demo.current_energy = 379
	demo.advance_simulation(1)
	check("host.target_opens_success", demo.ui.page == "success" and not demo.live_simulation)
	demo.ui._restart()
	demo.current_seconds = 0.5
	demo.advance_simulation(1)
	check("host.timer_opens_failure", demo.ui.page == "failure" and not demo.live_simulation)
	var failures := checks.filter(func(item: Dictionary): return not item["pass"])
	var hashes := {}
	for file in ["interaction_ui.gd","modal_window.gd","toast.gd","interactive_preview.gd"]:
		var path := "res://scripts/ember/ui_edge_v004/" + String(file)
		hashes[path] = FileAccess.get_sha256(path)
	for file in ["life_indicator.gd","edge_hud.gd"]:
		var path := "res://scripts/ember/ui_edge_v001/" + String(file)
		hashes[path] = FileAccess.get_sha256(path)
	var report := {"status":"PASS" if failures.is_empty() else "FAIL","check_count":checks.size(),"failures":failures,"checks":checks,"source_sha256":hashes}
	var output := FileAccess.open(OUT + "interaction-validation.json",FileAccess.WRITE)
	output.store_string(JSON.stringify(report,"\t"))
	output.close()
	print("UI_INTERACTIONS ", report.status, " checks=", checks.size(), " failures=",failures.size())
	view.free()
	quit(0 if failures.is_empty() else 1)
