extends SceneTree
## UI 尺寸审计：读取真实 Control 矩形和字体最小尺寸，不改生产组件。
## 运行 Godot --headless --path <项目> --script res://tools/probe_ui_edge_layout_v002.gd
## 逻辑 viewport 变化与 canvas_items 的物理窗口缩放是不同情形。

const HUD_SCENE = preload("res://scenes/ember/ui_edge_v001/components/edge_hud.tscn")
const PROGRESS = preload("res://scripts/ember/ui_edge_v001/energy_progress.gd")
const REPORT := "res://art-source/ember/ui-edge-v001/layout-audit-v002.json"

var _samples: Array[Dictionary] = []
var _findings: Array[Dictionary] = []
var _viewport: SubViewport
var _hud: Control

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	_viewport = SubViewport.new()
	root.add_child(_viewport)
	var canvas := CanvasLayer.new()
	_viewport.add_child(canvas)
	_hud = HUD_SCENE.instantiate()
	canvas.add_child(_hud)
	await _settle()
	for dimensions in [Vector2i(360, 640), Vector2i(480, 480), Vector2i(540, 540), Vector2i(720, 720), Vector2i(960, 540), Vector2i(1280, 720)]:
		_viewport.size = dimensions
		await _settle()
		for maximum in [1, 3, 6, 12]:
			for opened in [false, true]:
				_hud.set_game_state({"life": maximum, "max_life": maximum, "energy": 145.0, "energy_goal": 380.0, "seconds": 78.0, "station_name": "采能站 01"})
				_hud.set_drawer_open(opened)
				await _settle()
				_sample_hud("%dx%d.life%d.%s" % [dimensions.x, dimensions.y, maximum, "open" if opened else "closed"])
	# 内容增长在项目原生逻辑画布 720×720 中单独审计。
	_viewport.size = Vector2i(720, 720)
	_hud.set_drawer_open(true)
	_hud.set_game_state({"life": 2, "max_life": 3, "station_name": "潮汐港口东部补给维修站 · 第二采能模块 / 扩展设备名称", "energy": 9999999999.0, "energy_goal": 10000000000.0, "seconds": 6000.0})
	await _settle()
	_sample_hud("720x720.long_title.10digit_energy.100min")
	for seconds in [60000.0, 600000.0, 60000000.0]:
		_hud.set_game_state({"seconds": seconds, "energy": 1.0e20, "energy_goal": 2.0e20})
		await _settle()
		_sample_hud("720x720.timer_%dminutes.scientific_energy" % int(seconds / 60.0))
	await _sample_independent_progress(canvas)
	var geometry_errors := 0
	var limitations := 0
	for finding in _findings:
		if finding.severity == "geometry_error":
			geometry_errors += 1
		else:
			limitations += 1
	var report := {
		"kind": "actual_control_layout_probe", "version": 2,
		"tested_layout_result": "PASS" if geometry_errors == 0 else "FAIL",
		"sample_count": _samples.size(), "geometry_error_count": geometry_errors, "limitation_count": limitations,
		"logical_viewports_tested": [[360,640], [480,480], [540,540], [720,720], [960,540], [1280,720]],
		"project_logical_viewport": [720,720],
		"physical_scaling_note": "canvas_items 将720×720逻辑画布缩放到物理窗口；此探针的小尺寸是主动改变逻辑画布，不能直接等同于用户把窗口缩小。",
		"method": "SubViewport + CanvasLayer + 原生组件；等待3帧后读取实际Control global_rect / combined_minimum_size；字体使用组件真实SystemFont。",
		"limits": "只审计布局与字形最小尺寸，不以headless判断像素美术质量；长文本的省略属于安全降级但可能影响信息完整性。",
		"samples": _samples, "findings": _findings,
	}
	var file := FileAccess.open(REPORT, FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	print("UI_EDGE_LAYOUT_AUDIT: %d samples; %d geometry/content findings" % [_samples.size(), _findings.size()])
	for finding in _findings:
		print(JSON.stringify(finding))
	_viewport.free()
	quit()

func _settle() -> void:
	await process_frame
	await process_frame
	await process_frame

func _rect(rect: Rect2) -> Dictionary:
	return {"x": rect.position.x, "y": rect.position.y, "w": rect.size.x, "h": rect.size.y}

func _observed(control: Control) -> Dictionary:
	var result := {"rect": _rect(control.get_global_rect()), "local_rect": _rect(control.get_rect()), "minimum": [control.get_combined_minimum_size().x, control.get_combined_minimum_size().y], "visible": control.is_visible_in_tree()}
	if control is Label:
		var label := control as Label
		var font := label.get_theme_font("font")
		var font_size := label.get_theme_font_size("font_size")
		result["text"] = label.text
		result["clip_text"] = label.clip_text
		result["overrun_behavior"] = label.text_overrun_behavior
		result["unwrapped_text_width"] = font.get_string_size(label.text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	return result

func _finding(id: String, issue: String, details: Dictionary) -> void:
	var informational := issue in ["text_safely_elided", "requested_size_clamped_to_minimum"]
	_findings.append({"sample": id, "issue": issue, "severity": "limitation" if informational else "geometry_error", "details": details})

func _sample_hud(id: String) -> void:
	var life: Control = _hud.get("_life")
	var timer: Control = _hud.get("_timer")
	var energy: Control = _hud.get_energy_progress()
	var drawer: Control = _hud.get_drawer()
	var timer_value: Label = timer.get("_value")
	var snapshot := {"id": id, "viewport": [_viewport.size.x, _viewport.size.y], "hud": _observed(_hud), "world": _rect(_hud.get_available_world_rect()), "life": _observed(life), "timer": _observed(timer), "timer_value": _observed(timer_value), "energy": _observed(energy), "energy_value": _observed(energy.get("_value")), "energy_percent": _observed(energy.get("_percent")), "drawer": _observed(drawer)}
	var life_slots: Array = life.get("_slots")
	var life_count: Label = life.get("_count")
	snapshot["life"]["slot_count"] = life_slots.size()
	snapshot["life"]["quantity"] = _observed(life_count)
	if life.is_visible_in_tree() and int(life.get("max_life")) > life_slots.size() and life_count.text != "%d / %d" % [life.get("life"), life.get("max_life")]:
		_finding(id, "life_folded_without_accurate_quantity", {"slots": life_slots.size(), "count": life_count.text, "life": life.get("life"), "maximum": life.get("max_life")})
	var view_rect := Rect2(Vector2.ZERO, Vector2(_viewport.size))
	for pair in [["life", life], ["timer", timer], ["energy", energy]]:
		var control: Control = pair[1]
		if control.is_visible_in_tree() and not view_rect.encloses(control.get_global_rect()):
			_finding(id, "hud_outside_viewport", {"component": pair[0], "rect": _rect(control.get_global_rect())})
	if life.is_visible_in_tree() and energy.is_visible_in_tree() and life.get_global_rect().intersects(energy.get_global_rect()):
		_finding(id, "life_overlaps_bottom_progress", {"life": _rect(life.get_global_rect()), "energy": _rect(energy.get_global_rect())})
	if timer_value.is_visible_in_tree() and not timer.get_global_rect().encloses(timer_value.get_global_rect()):
		_finding(id, "timer_text_outside_badge", {"timer": _rect(timer.get_global_rect()), "value": _observed(timer_value)})
	elif timer_value.is_visible_in_tree() and timer_value.size.x > timer.size.x - 32:
		_finding(id, "timer_text_intrudes_corner_gutter", {"available_text_width": timer.size.x - 32, "actual_text_width": timer_value.size.x, "text": timer_value.text})
	if timer_value.is_visible_in_tree() and not _hud.get_available_world_rect().encloses(timer_value.get_global_rect()):
		_finding(id, "timer_text_outside_available_world", {"world": _rect(_hud.get_available_world_rect()), "value": _observed(timer_value)})
	_note_ellipsis(id, "hud_energy_value", energy.get("_value"))
	if "%" in (energy.get("_value") as Label).text:
		_finding(id, "quantity_format_placeholder_leaked", {"text": (energy.get("_value") as Label).text})
	if drawer.visible:
		if not view_rect.encloses(drawer.get_global_rect()):
			_finding(id, "drawer_outside_viewport", {"drawer": _observed(drawer)})
		var content: Control = drawer.get("_content_clip")
		var named: Dictionary = {"title": drawer.get("_title"), "portrait": drawer.get("_portrait"), "portrait_frame": drawer.get("_portrait_frame"), "goal_label": drawer.get("_goal_label"), "goal_value": drawer.get("_goal_value"), "progress": drawer.get("_progress"), "hint": drawer.get("_hint"), "back": drawer.get_back_button()}
		var rows: Array = drawer.get("_rows")
		for index in range(rows.size()):
			named["row%d" % index] = rows[index]
		var drawer_nodes: Dictionary = {}
		for name in named:
			var node: Control = named[name]
			drawer_nodes[name] = _observed(node)
			if node.is_visible_in_tree() and not content.get_global_rect().encloses(node.get_global_rect()):
				_finding(id, "drawer_content_clipped", {"component": name, "rect": _rect(node.get_global_rect()), "content": _rect(content.get_global_rect())})
			if node is Label:
				_note_ellipsis(id, name, node)
		for pair in [["title", "portrait_frame"], ["portrait_frame", "goal_label"], ["goal_label", "goal_value"], ["goal_value", "progress"], ["progress", "row0"], ["row0", "row1"], ["row1", "row2"], ["row2", "row3"], ["row3", "hint"], ["hint", "back"]]:
			var first: Control = named[pair[0]]
			var second: Control = named[pair[1]]
			if first.is_visible_in_tree() and second.is_visible_in_tree() and first.get_global_rect().intersects(second.get_global_rect()):
				# 标题及数值的上下字面框有2px设计交叉；只有显著交叉才报出。
				var intersection := first.get_global_rect().intersection(second.get_global_rect())
				if intersection.size.y > 2.0:
					_finding(id, "drawer_adjacent_regions_overlap", {"first": pair[0], "second": pair[1], "intersection": _rect(intersection)})
		snapshot["drawer_nodes"] = drawer_nodes
	_samples.append(snapshot)

func _note_ellipsis(id: String, name: String, label: Label) -> void:
	var info := _observed(label)
	if label.is_visible_in_tree() and label.clip_text and not label.text.is_empty() and label.autowrap_mode == TextServer.AUTOWRAP_OFF and float(info.unwrapped_text_width) > label.size.x:
		_finding(id, "text_safely_elided", {"component": name, "value": info})

func _sample_independent_progress(canvas: CanvasLayer) -> void:
	_hud.hide()
	for labels in [true, false]:
		var progress: Control = PROGRESS.new()
		progress.show_labels = labels
		canvas.add_child(progress)
		await _settle()
		for width in [64, 96, 120, 160, 200, 320]:
			progress.size = Vector2(width, 64 if labels else 24)
			progress.set_data(145.0, 380.0)
			await _settle()
			var id := "standalone_progress.request%d.labels%s" % [width, labels]
			_observe_independent_progress(progress, id, width, labels)
			if labels:
				# 100%字形比38%宽，能查出窄条满值时才发生的文字碰撞。
				progress.set_data(380.0, 380.0)
				await _settle()
				_observe_independent_progress(progress, id + ".full", width, labels)
		progress.free()

func _observe_independent_progress(progress: Control, id: String, width: int, labels: bool) -> void:
	var value: Label = progress.get("_value")
	var percent: Label = progress.get("_percent")
	var snapshot := {"id": id, "requested_width": width, "progress": _observed(progress), "value": _observed(value), "percent": _observed(percent), "fill": _observed(progress.get("_fill_clip")), "track": _observed(progress.get("_track"))}
	_samples.append(snapshot)
	if progress.size.x != width:
		_finding(id, "requested_size_clamped_to_minimum", {"requested": width, "actual": progress.size.x})
	if labels:
		_note_ellipsis(id, "value", value)
		# 根据真实字符串宽度比较占用区，避免将空白交叉误报为文字重叠。
		var value_info := _observed(value)
		var percent_info := _observed(percent)
		var value_width := minf(value.size.x, float(value_info.unwrapped_text_width))
		var percent_width := minf(percent.size.x, float(percent_info.unwrapped_text_width))
		var value_glyphs := Rect2(value.global_position, Vector2(value_width, value.size.y))
		var percent_glyphs := Rect2(percent.global_position + Vector2(percent.size.x - percent_width, 0), Vector2(percent_width, percent.size.y))
		if value_glyphs.intersects(percent_glyphs):
			_finding(id, "progress_value_percent_glyphs_overlap", {"value": _rect(value_glyphs), "percent": _rect(percent_glyphs)})
