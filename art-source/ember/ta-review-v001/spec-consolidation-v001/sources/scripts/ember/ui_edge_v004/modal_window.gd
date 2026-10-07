extends Control
## 可复用模态壳：遮罩、九宫格底板、标题、可滚动正文、关闭按钮分层。
## 所有页面共用一个壳；显式焦点循环，避免 Tab/手柄方向跳到被遮盖的 HUD。

signal close_requested
const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
const BUTTON = preload("res://scripts/ember/ui_edge_v001/bracket_button.gd")
var panel: Panel
var title_label: Label
var body: VBoxContainer
var scroll: ScrollContainer
var close_button: Button
var controls: Array[Control] = []
var allow_close := true
var preferred_height := 620.0

func _ready() -> void:
	STYLE.prepare(self, true)
	var shade := ColorRect.new()
	shade.color = Color(0.025, 0.045, 0.06, 0.80)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(shade)
	panel = STYLE.panel(self)
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	title_label = STYLE.label(panel, "", 28)
	title_label.clip_text = true
	title_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	close_button = BUTTON.new()
	close_button.text = "关闭"
	panel.add_child(close_button)
	close_button.custom_minimum_size = Vector2(84, 48)
	close_button.add_theme_font_size_override("font_size", 18)
	close_button.pressed.connect(func(): close_requested.emit())
	scroll = ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.follow_focus = true
	panel.add_child(scroll)
	var rail := StyleBoxFlat.new()
	rail.bg_color = Color("182631")
	rail.content_margin_left = 4
	rail.content_margin_right = 4
	scroll.get_v_scroll_bar().add_theme_stylebox_override("scroll", rail)
	var thumb := StyleBoxFlat.new()
	thumb.bg_color = Color("4d6470")
	for state in ["grabber", "grabber_highlight", "grabber_pressed"]:
		scroll.get_v_scroll_bar().add_theme_stylebox_override(state, thumb)
	body = VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 16)
	scroll.add_child(body)
	resized.connect(_layout)
	_layout()
	hide()

func reset_page(caption: String, closable: bool = true) -> void:
	# 先释放焦点，再同步移除旧页，避免延迟释放的按钮接收第二次确认。
	var focused := get_viewport().gui_get_focus_owner()
	if focused != null and is_ancestor_of(focused):
		focused.release_focus()
	for child in body.get_children():
		# 正在发pressed信号的按钮处于Godot对象锁内；先离树使其不可交互，帧末释放。
		body.remove_child(child)
		child.queue_free()
	controls.clear()
	title_label.text = caption
	allow_close = closable
	close_button.visible = closable
	scroll.scroll_vertical = 0
	show()
	_layout()

func paragraph(text: String, color: Color = Color("ece9d8"), font_size: int = 20) -> Label:
	var label := STYLE.label(body, text, font_size, color)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return label

func action(identifier: String, caption: String, callback: Callable) -> Button:
	var button := BUTTON.new()
	button.name = identifier
	button.text = caption
	body.add_child(button)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.pressed.connect(callback)
	button.focus_entered.connect(_queue_reveal_focus)
	controls.append(button)
	return button

func register_control(control: Control) -> void:
	controls.append(control)
	control.focus_mode = Control.FOCUS_ALL
	control.focus_entered.connect(_queue_reveal_focus)

func _queue_reveal_focus() -> void:
	# 跨Viewport重挂后也从当前Viewport读取焦点，不依赖旧视口的focus信号连接。
	# 只在焦点变化时滚动；不逐帧吸回，用户仍可自由用滚轮查看正文。
	_reveal_focus.call_deferred()

func _reveal_focus() -> void:
	if not is_inside_tree() or not is_visible_in_tree():
		return
	var focused := get_viewport().gui_get_focus_owner()
	if focused != null and scroll.is_ancestor_of(focused) and focused.is_visible_in_tree():
		scroll.ensure_control_visible(focused)

func focus_first(identifier: String = "") -> void:
	if not visible or not is_inside_tree():
		return
	for control in controls:
		if is_instance_valid(control) and control.is_visible_in_tree() and not (control is BaseButton and control.disabled):
			if identifier.is_empty() or control.name == identifier:
				control.grab_focus()
				return
	if not identifier.is_empty():
		focus_first()
	elif allow_close:
		close_button.grab_focus()

func cycle_focus(backwards: bool) -> void:
	var available: Array[Control] = []
	for control in controls:
		if is_instance_valid(control) and control.is_visible_in_tree() and not (control is BaseButton and control.disabled):
			available.append(control)
	if allow_close:
		available.append(close_button)
	if available.is_empty():
		return
	var index := available.find(get_viewport().gui_get_focus_owner())
	index = posmod(index + (-1 if backwards else 1), available.size())
	available[index].grab_focus()

func _layout() -> void:
	if panel == null:
		return
	# 320×480 起均有独立滚动正文，标题及关闭入口不随正文滚走。
	panel.size = Vector2(minf(600, maxf(272, size.x - 48)), minf(preferred_height, maxf(300, size.y - 48)))
	panel.position = ((size - panel.size) * 0.5).floor()
	title_label.position = Vector2(24, 22)
	title_label.size = Vector2(panel.size.x - (136 if allow_close else 48), 44)
	close_button.position = Vector2(panel.size.x - 108, 20)
	close_button.size = Vector2(84, 48)
	scroll.position = Vector2(24, 88)
	scroll.size = Vector2(panel.size.x - 48, panel.size.y - 112)
