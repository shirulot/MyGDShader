extends Control
## 完整窗口路由。UI只发玩法请求；宿主负责暂停自己的计时/移动，避免擅改全局Game。
## 同一套皮肤用于HUD、详情、暂停、设置、帮助、确认和结算；文字均为动态节点。

signal blocking_changed(blocked: bool)
signal restart_requested
signal title_requested
signal session_requested
signal preferences_changed(preferences: Dictionary)
const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
const BUTTON = preload("res://scripts/ember/ui_edge_v001/bracket_button.gd")
const MODAL = preload("res://scripts/ember/ui_edge_v004/modal_window.gd")
const TOAST = preload("res://scripts/ember/ui_edge_v004/toast.gd")
const HUD = preload("res://scenes/ember/ui_edge_v001/components/edge_hud.tscn")
const PORTRAIT = preload("res://assets/ember/map_assets_v001/buildings/energy_station.png")

@export var settings_path := "user://ember_edge_ui_v004.cfg"
@export var gamepad_confirm_button: JoyButton = JOY_BUTTON_A
@export var gamepad_back_button: JoyButton = JOY_BUTTON_B
var hud: Control
var window: Control
var toast: Control
var details_button: Button
var menu_button: Button
var station_button: Button
var page := ""
var preferences := {"safe_margin":36, "show_markers":true}
var _draft: Dictionary = {}
var _history: Array[Dictionary] = []
var _return_focus: WeakRef
var _data: Dictionary = {}
var _detail_status: Label
var _detail_values: Label
var _detail_title: Label
var _terminal_action: Button
var _portrait: Texture2D = PORTRAIT
var _detail_portrait: TextureRect
var _station_rect := Rect2()
var _station_visible := false
var _station_connected := true
var _has_result := false
var _built := false

func _ready() -> void:
	STYLE.prepare(self)
	hud = HUD.instantiate()
	hud.name = "HUD"
	add_child(hud)
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	station_button = _entry("StationHitTarget", "查看设备", open_details)
	details_button = _entry("DetailsEntry", "设备详情", open_details)
	menu_button = _entry("MenuEntry", "菜单", open_pause)
	window = MODAL.new()
	window.name = "ModalWindow"
	add_child(window)
	window.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	window.close_requested.connect(back)
	toast = TOAST.new()
	toast.name = "Toast"
	add_child(toast)
	resized.connect(_layout)
	_built = true
	_load_preferences()
	_apply_preferences()
	set_game_state(_data)
	_layout()

func _enter_tree() -> void:
	if _built:
		_restore_tree.call_deferred()

func _restore_tree() -> void:
	if not is_inside_tree():
		return
	_layout()
	blocking_changed.emit(is_blocking())
	if is_blocking():
		window.focus_first()

func _exit_tree() -> void:
	# 离树期间不留下焦点或宿主的暂停锁；重挂由当前页面决定是否重新阻断。
	if _built:
		var focused := get_viewport().gui_get_focus_owner()
		if focused != null and is_ancestor_of(focused):
			focused.release_focus()
		blocking_changed.emit(false)

func _entry(identifier: String, caption: String, callback: Callable) -> Button:
	var button := BUTTON.new()
	button.name = identifier
	button.text = caption
	add_child(button)
	button.custom_minimum_size = Vector2(120, 44)
	button.add_theme_font_size_override("font_size", 18)
	# 世界背景有亮地板：入口常态必须有深色衬底，不能仅靠白字与角标。
	button.add_theme_stylebox_override("normal", STYLE.box("panel_backplate_96"))
	button.pressed.connect(callback)
	return button

func set_game_state(data: Dictionary) -> void:
	_data.merge(data, true)
	_station_connected = bool(_data.get("station_connected", true))
	if not _built:
		return
	hud.set_game_state(_data)
	_data.merge(hud.get_game_state(), true)
	details_button.disabled = not _station_connected
	if not _station_connected:
		hud.set_station_portrait(null)
		hud.set_drawer_open(false)
	else:
		hud.set_station_portrait(_portrait)
	_refresh_details()
	_layout()

func set_station_portrait(portrait: Texture2D) -> void:
	_portrait = portrait
	if _built:
		hud.set_station_portrait(portrait if _station_connected else null)
		_refresh_details()

func set_station_screen_rect(rect: Rect2, should_show: bool = true) -> void:
	_station_rect = rect
	_station_visible = should_show and is_finite(rect.position.x) and is_finite(rect.position.y) and is_finite(rect.size.x) and is_finite(rect.size.y)
	if _built:
		_layout()

func is_blocking() -> bool:
	return _built and is_inside_tree() and not page.is_empty()

func open_details() -> void:
	if not _station_connected or _has_result or not page.is_empty():
		return
	_open("details")

func open_pause() -> void:
	if _has_result or not page.is_empty():
		return
	_open("pause")

func show_title() -> void:
	_has_result = false
	_open("title", false, true)

func show_result(won: bool) -> void:
	# 结果替换整条栈，Esc不能绕过失败/胜利后返回仍在运行的旧局。
	_has_result = true
	_open("success" if won else "failure", false, true)

func _open(next_page: String, push: bool = false, replace: bool = false) -> void:
	if not _built or not is_inside_tree():
		return
	if page.is_empty():
		var focused := get_viewport().gui_get_focus_owner()
		_return_focus = weakref(focused) if focused != null else weakref(details_button)
	elif push:
		var focused := get_viewport().gui_get_focus_owner()
		_history.append({"page":page, "focus":String(focused.name) if focused != null else ""})
	if replace:
		_history.clear()
	page = next_page
	_build_page()
	blocking_changed.emit(true)
	_layout()
	window.focus_first.call_deferred()

func back() -> void:
	if not _built or not is_inside_tree() or page.is_empty():
		return
	if page in ["title", "success", "failure"]:
		return
	if not _history.is_empty():
		var previous: Dictionary = _history.pop_back()
		page = previous.page
		_build_page()
		window.focus_first.call_deferred(String(previous.focus))
	else:
		close_all()

func close_all() -> void:
	_history.clear()
	page = ""
	if not _built:
		return
	window.hide()
	if is_inside_tree():
		var focused := get_viewport().gui_get_focus_owner()
		if focused != null and window.is_ancestor_of(focused):
			focused.release_focus()
		var previous: Control = _return_focus.get_ref() as Control if _return_focus != null else null
		if is_instance_valid(previous) and previous.is_inside_tree() and previous.get_viewport() == get_viewport() and previous.is_visible_in_tree() and not (previous is BaseButton and previous.disabled):
			previous.grab_focus()
	blocking_changed.emit(false)
	_layout()

func _build_page() -> void:
	_detail_status = null
	_detail_values = null
	_detail_title = null
	_detail_portrait = null
	_terminal_action = null
	window.preferred_height = {"details":520.0,"pause":556.0,"settings":520.0,"confirm_restart":360.0,"confirm_title":360.0,"title":440.0,"success":440.0,"failure":440.0}.get(page,620.0)
	match page:
		"details":
			window.reset_page("设备详情")
			var summary := HBoxContainer.new()
			summary.add_theme_constant_override("separation",16)
			window.body.add_child(summary)
			_detail_portrait = STYLE.texture(summary, "")
			_detail_portrait.custom_minimum_size = Vector2(96, 144)
			_detail_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			var info := VBoxContainer.new()
			info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			info.add_theme_constant_override("separation",10)
			summary.add_child(info)
			_detail_title = STYLE.label(info,"",24)
			_detail_status = STYLE.label(info,"",20)
			_detail_values = STYLE.label(info,"",18)
			for label in [_detail_title,_detail_status,_detail_values]:
				label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			window.paragraph("进入采集范围并停下后自动采集。预警时留意撤离，爆发与冷却期间无法采集。", STATE.MUTED_COLOR)
			_terminal_action = window.action("Terminal", "固定到侧边终端", _show_terminal)
			window.action("Help", "采集与操作说明", func(): _open("help", true))
			_refresh_details()
		"pause":
			window.reset_page("暂停")
			window.paragraph("现场已暂停", STATE.MUTED_COLOR)
			window.action("Resume", "继续巡检", close_all)
			window.action("Settings", "界面设置", func(): _open("settings", true))
			window.action("Help", "操作说明", func(): _open("help", true))
			window.action("Restart", "重新开始", func(): _open("confirm_restart", true))
			window.action("Title", "返回起始页", func(): _open("confirm_title", true))
		"settings":
			window.reset_page("界面设置")
			_draft = preferences.duplicate(true)
			var margin_label: Label = window.paragraph("屏幕留边  ·  %d px" % _draft.safe_margin)
			var slider := HSlider.new()
			slider.name = "SafeMargin"
			slider.min_value = 16
			slider.max_value = 60
			slider.step = 4
			slider.value = _draft.safe_margin
			slider.custom_minimum_size.y = 44
			window.body.add_child(slider)
			_style_slider(slider)
			window.register_control(slider)
			slider.value_changed.connect(func(value: float):
				_draft.safe_margin = int(value)
				margin_label.text = "屏幕留边  ·  %d px" % int(value))
			var marker: Button = window.action("Markers", "", func():
				_draft.show_markers = not bool(_draft.show_markers)
				_update_marker_caption())
			marker.text = _marker_caption()
			window.paragraph("保存后生效。关闭或返回将放弃本次调整。", STATE.MUTED_COLOR)
			window.action("Save", "保存设置", _save_preferences)
			window.action("Cancel", "取消", back)
		"help":
			window.reset_page("操作说明")
			window.paragraph("01  设备与窗口", STATE.DEFINITIONS[0].color, 24)
			window.paragraph("点击设备上的「查看设备」或左上角「设备详情」打开详情；可将状态固定在右侧终端。关闭详情后继续现场操作。")
			window.paragraph("02  采集与危险", STATE.DEFINITIONS[1].color, 24)
			window.paragraph("停下自动采集，移动会中断。安全与预警可以采集；爆发时及时撤离，冷却后再靠近。能量达到目标完成巡检，生命或倒计时耗尽则巡检失败。")
			window.paragraph("03  窗口操作", STATE.DEFINITIONS[0].color, 24)
			window.paragraph("Esc 返回上一层；Tab 切换焦点；方向键选择；Enter 确认。手柄方向键选择、A 确认、B 返回。长内容可滚动。")
			window.action("Back", "返回", back)
		"confirm_restart", "confirm_title":
			var restarting := page == "confirm_restart"
			window.reset_page("重新开始？" if restarting else "返回起始页？")
			window.paragraph("本次巡检进度将清空。", STATE.DEFINITIONS[1].color, 26)
			window.paragraph("当前采集：%s / %s" % [STATE.format_quantity(float(_data.get("energy", 0))), STATE.format_quantity(float(_data.get("energy_goal", 0)))])
			# 默认焦点在取消，避免连续确认键误触重置。
			window.action("Cancel", "继续当前巡检", back)
			window.action("Confirm", "确认重新开始" if restarting else "确认返回", _confirm)
		"title":
			window.reset_page("余烬 · 采能站", false)
			window.paragraph("潮汐维护站", STATE.DEFINITIONS[0].color, 28)
			window.paragraph("收集能源，观察设备状态，在危险爆发前撤离。", STATE.MUTED_COLOR)
			window.action("Start", "开始巡检", _start)
			window.action("Settings", "界面设置", func(): _open("settings", true))
			window.action("Help", "操作说明", func(): _open("help", true))
		"success", "failure":
			var won := page == "success"
			window.reset_page("巡检完成" if won else "巡检中止", false)
			window.paragraph("能源目标已达成" if won else ("生命已耗尽" if int(_data.get("life", 0)) <= 0 else "巡检时间已结束"), STATE.DEFINITIONS[0 if won else 2].color, 28)
			window.paragraph("采集能源  %s / %s\n剩余生命  %d / %d\n剩余时间  %d 秒" % [STATE.format_quantity(float(_data.get("energy", 0))), STATE.format_quantity(float(_data.get("energy_goal", 0))), int(_data.get("life", 0)), int(_data.get("max_life", 0)), int(_data.get("seconds", 0))])
			window.action("Retry", "再次巡检", _restart)
			window.action("Title", "返回起始页", _return_to_title)

func _refresh_details() -> void:
	if page != "details" or _detail_status == null:
		return
	var state := int(_data.get("station_state", -1)) if _station_connected else -1
	var definition := STATE.definition(state)
	_detail_title.text = str(_data.get("station_name", "未连接设备")) if _station_connected else "设备已断开"
	_detail_status.text = "◆  状态：" + String(definition.label)
	_detail_status.add_theme_color_override("font_color", definition.color)
	_detail_values.text = "采集目标  %s / %s\n当前进度  %d%%" % [STATE.format_quantity(float(_data.get("energy", 0))), STATE.format_quantity(float(_data.get("energy_goal", 0))), int(STATE.safe_ratio(float(_data.get("energy", 0)), float(_data.get("energy_goal", 0))) * 100.0)]
	_detail_portrait.texture = _portrait if _station_connected else null
	_terminal_action.disabled = not _station_connected
	if _terminal_action.disabled and _terminal_action.has_focus():
		window.focus_first()

func _show_terminal() -> void:
	if not _station_connected:
		return
	close_all()
	hud.set_drawer_open(true)
	toast.notify("设备状态已固定到右侧终端")
	_layout()

func _start() -> void:
	_has_result = false
	close_all()
	session_requested.emit()

func _restart() -> void:
	_has_result = false
	close_all()
	restart_requested.emit()
	toast.notify("新的巡检已开始")

func _return_to_title() -> void:
	title_requested.emit()
	show_title()

func _confirm() -> void:
	if page == "confirm_restart":
		_restart()
	elif page == "confirm_title":
		_return_to_title()

func _marker_caption() -> String:
	return "设备标签  ·  " + ("显示" if bool(_draft.show_markers) else "隐藏")

func _update_marker_caption() -> void:
	var control := window.body.get_node_or_null("Markers") as Button
	if control != null:
		control.text = _marker_caption()

func _load_preferences() -> void:
	if settings_path.is_empty():
		return
	var config := ConfigFile.new()
	if config.load(settings_path) == OK:
		preferences.safe_margin = clampi(int(config.get_value("ui", "safe_margin", 36)), 16, 60)
		preferences.show_markers = bool(config.get_value("ui", "show_markers", true))

func _save_preferences() -> void:
	if not settings_path.is_empty():
		var config := ConfigFile.new()
		config.set_value("ui", "safe_margin", _draft.safe_margin)
		config.set_value("ui", "show_markers", _draft.show_markers)
		if config.save(settings_path) != OK:
			toast.notify("设置保存失败，请重试")
			return
	preferences = _draft.duplicate(true)
	_apply_preferences()
	preferences_changed.emit(preferences.duplicate(true))
	back()
	toast.notify("界面设置已保存")

func _apply_preferences() -> void:
	hud.safe_margin = int(preferences.safe_margin)
	_layout()

func _style_slider(slider: HSlider) -> void:
	var track := StyleBoxFlat.new()
	track.bg_color = Color("2b3e4b")
	track.content_margin_top = 4
	track.content_margin_bottom = 4
	slider.add_theme_stylebox_override("slider", track)
	var fill := track.duplicate() as StyleBoxFlat
	fill.bg_color = Color("51c5c2")
	slider.add_theme_stylebox_override("grabber_area", fill)
	slider.add_theme_stylebox_override("grabber_area_highlight", fill)
	slider.add_theme_icon_override("grabber", STYLE.skin("bracket_corner_16"))
	slider.add_theme_icon_override("grabber_highlight", STYLE.skin("bracket_corner_16"))
	# 轨道和抓手保留原造型。独立角层表示键盘/手柄焦点，不能只改变值。
	var focus_overlay := STYLE.panel(slider, "button_focus_96")
	focus_overlay.name = "FocusOverlay"
	focus_overlay.modulate = Color("51c5c2")
	focus_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	focus_overlay.visible = slider.has_focus()
	slider.focus_entered.connect(func(): focus_overlay.show())
	slider.focus_exited.connect(func(): focus_overlay.hide())

func _layout() -> void:
	if not _built:
		return
	var world_rect: Rect2 = hud.get_available_world_rect()
	var timer: Control = hud.get("_timer")
	var life: Control = hud.get("_life")
	var margin := life.position.x
	var entry_y := maxf(timer.position.y + timer.size.y, life.position.y + life.size.y) + 20
	details_button.position = Vector2(floorf(margin), entry_y)
	details_button.size = Vector2(124, 44)
	menu_button.position = Vector2(floorf(margin), entry_y + 56)
	menu_button.size = Vector2(124, 44)
	details_button.visible = world_rect.size.x >= 224
	menu_button.visible = world_rect.size.x >= 224
	station_button.position = _station_rect.position.round()
	station_button.size = Vector2(124, 44)
	station_button.visible = _station_visible and _station_connected and bool(preferences.show_markers) and page.is_empty() and world_rect.encloses(Rect2(station_button.position, station_button.size))
	toast.size = Vector2(minf(420, size.x - 48), 84)
	toast.position = Vector2(floorf((size.x - toast.size.x) * 0.5), maxf(16, size.y - 194))

func _input(event: InputEvent) -> void:
	if not is_visible_in_tree():
		return
	# 此项目的Godot内置ui_accept/ui_cancel只有键盘事件。局部映射手柄按钮，
	# 不改写全局InputMap；按钮可由宿主导出属性更换。每次pressed只触发一次。
	if event is InputEventJoypadButton:
		if _gamepad_input(event):
			get_viewport().set_input_as_handled()
			return
	if page.is_empty():
		return
	# 外部宿主/跨视口重挂可能夺走焦点；确认键派发前先收回到当前窗口。
	var focused := get_viewport().gui_get_focus_owner()
	if focused == null or not window.is_ancestor_of(focused):
		window.focus_first()
	if event.is_action_pressed("ui_cancel"):
		back()
		get_viewport().set_input_as_handled()

	elif event.is_action_pressed("ui_focus_next") or event.is_action_pressed("ui_focus_prev") or event.is_action_pressed("ui_down") or event.is_action_pressed("ui_up"):
		window.cycle_focus(event.is_action_pressed("ui_focus_prev") or event.is_action_pressed("ui_up"))
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_left") or event.is_action_pressed("ui_right"):
		if not get_viewport().gui_get_focus_owner() is Slider:
			window.cycle_focus(event.is_action_pressed("ui_left"))
			get_viewport().set_input_as_handled()

func _gamepad_input(event: InputEventJoypadButton) -> bool:
	var current_focus := get_viewport().gui_get_focus_owner()
	if event.button_index in [JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_DPAD_RIGHT] and current_focus is HSlider and window.is_ancestor_of(current_focus) and not page.is_empty():
		if event.pressed:
			current_focus.value += current_focus.step * (-1 if event.button_index == JOY_BUTTON_DPAD_LEFT else 1)
		return true
	if event.button_index == JOY_BUTTON_START:
		if event.pressed and page.is_empty():
			open_pause()
		return true
	if event.button_index == gamepad_back_button:
		if event.pressed:
			if not page.is_empty():
				back()
			elif hud.is_drawer_open():
				hud.close_drawer()
		return not page.is_empty() or hud.is_drawer_open() or event.pressed
	if event.button_index != gamepad_confirm_button:
		return false
	var focused := get_viewport().gui_get_focus_owner()
	if not page.is_empty() and (focused == null or not window.is_ancestor_of(focused)):
		window.focus_first()
		focused = get_viewport().gui_get_focus_owner()
	if focused is Button and is_ancestor_of(focused) and focused.is_visible_in_tree() and not focused.disabled:
		if event.pressed:
			focused.pressed.emit()
		return true
	return not page.is_empty()

func _process(_delta: float) -> void:
	if is_visible_in_tree() and is_blocking():
		var focused := get_viewport().gui_get_focus_owner()
		if focused == null or not window.is_ancestor_of(focused):
			window.focus_first()

func _unhandled_key_input(event: InputEvent) -> void:
	if not is_visible_in_tree():
		return
	if not page.is_empty():
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_cancel"):
		if hud.is_drawer_open():
			hud.close_drawer()
		else:
			open_pause()
		get_viewport().set_input_as_handled()
