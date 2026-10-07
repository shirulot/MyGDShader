extends SceneTree
## 冻结包送审期间的补充复查，不修改组件：手柄事件与模态窗口跨视口重挂。
const FLOW = preload("res://scenes/ember/ui_edge_v004/interaction_ui.tscn")
var checks: Array[Dictionary] = []
var view: SubViewport

func _initialize() -> void:
	_run.call_deferred()

func _check(id: String, passed: bool) -> void:
	checks.append({"id":id,"pass":passed})

func _joy(button: JoyButton) -> void:
	for pressed in [true,false]:
		var event := InputEventJoypadButton.new()
		event.button_index = button
		event.pressed = pressed
		view.push_input(event,true)

func _run() -> void:
	view = SubViewport.new()
	view.size = Vector2i(720,720)
	root.add_child(view)
	var ui: Control = FLOW.instantiate()
	ui.settings_path = ""
	view.add_child(ui)
	ui.details_button.grab_focus()
	_joy(JOY_BUTTON_A)
	await process_frame
	_check("joy.hud_entry_confirm", ui.page == "details")
	_joy(JOY_BUTTON_B)
	await process_frame
	_check("joy.details_back", ui.page.is_empty())
	_joy(JOY_BUTTON_START)
	await process_frame
	_check("joy.start_opens_pause", ui.page == "pause")
	_joy(JOY_BUTTON_DPAD_DOWN)
	_check("joy.direction_focus", view.gui_get_focus_owner().name == "Settings")
	_joy(JOY_BUTTON_A)
	await process_frame
	_check("joy.accept_opens_settings", ui.page == "settings")
	if ui.page != "settings":
		quit(1)
		return
	var slider := ui.window.body.get_node("SafeMargin") as HSlider
	slider.grab_focus()
	_check("slider.focus_overlay_visible", slider.get_node("FocusOverlay").visible and slider.get_node("FocusOverlay").mouse_filter == Control.MOUSE_FILTER_IGNORE)
	ui.window.body.get_node("Markers").grab_focus()
	_check("slider.focus_overlay_hidden_when_unfocused", not slider.get_node("FocusOverlay").visible)
	slider.grab_focus()
	_joy(JOY_BUTTON_DPAD_RIGHT)
	_check("joy.slider_edit", slider.value == 40)
	_joy(JOY_BUTTON_B)
	await process_frame
	_check("joy.back_restores_parent_focus", ui.page == "pause" and view.gui_get_focus_owner().name == "Settings")
	_check("joy.back_discards_settings_draft", ui.preferences.safe_margin == 36)
	ui.hud.set_drawer_open(true)
	await process_frame
	_check("modal.drawer_cannot_keep_focus", ui.window.is_ancestor_of(view.gui_get_focus_owner()))
	view.remove_child(ui)
	var second := SubViewport.new()
	second.size = Vector2i(960,540)
	root.add_child(second)
	second.add_child(ui)
	await process_frame
	await process_frame
	_check("modal.reparent_restores_window_focus", ui.window.is_ancestor_of(second.gui_get_focus_owner()) and view.gui_get_focus_owner() == null)
	_check("modal.reparent_resizes", ui.size == Vector2(960,540) and Rect2(Vector2.ZERO,Vector2(960,540)).encloses(ui.window.panel.get_global_rect()))
	ui.close_all()
	_check("modal.close_after_reparent", not ui.is_blocking() and not ui.window.visible)
	# 小屏自动滚动后的取消仍可达，焦点角层不能挡住滑条/滚动输入。
	second.size = Vector2i(320,480)
	await process_frame
	await process_frame
	ui._open("settings",false,true)
	await process_frame
	await process_frame
	await process_frame
	var cancel: Button = ui.window.body.get_node("Cancel")
	ui.window.close_button.grab_focus()
	for pressed in [true,false]:
		var tab := InputEventKey.new()
		tab.keycode = KEY_TAB
		tab.shift_pressed = true
		tab.pressed = pressed
		second.push_input(tab,true)
	await process_frame
	await process_frame
	await process_frame
	_check("compact.cancel_focus_scrolls_inside", cancel.has_focus() and ui.window.scroll.get_global_rect().encloses(cancel.get_global_rect()))
	var failures := checks.filter(func(item: Dictionary): return not item["pass"])
	var report := {"status":"PASS" if failures.is_empty() else "FAIL","check_count":checks.size(),"checks":checks,"failures":failures,"ui_source_sha256":FileAccess.get_sha256("res://scripts/ember/ui_edge_v004/interaction_ui.gd")}
	var output := FileAccess.open("res://art-source/ember/ui-interactions-v004/navigation-supplement.json",FileAccess.WRITE)
	output.store_string(JSON.stringify(report,"\t"))
	output.close()
	print(JSON.stringify(report))
	view.free()
	second.free()
	quit(0 if failures.is_empty() else 1)
