extends SceneTree
## 最小组件审计：直接检查真实节点属性，不用镜像逻辑替代组件行为。
## --button-only 用于生产修改前记录 Godot 的原生禁用/焦点行为。

const BUTTON = preload("res://scripts/ember/ui_edge_v001/bracket_button.gd")
const DRAWER = preload("res://scripts/ember/ui_edge_v001/station_drawer.gd")
const PROGRESS = preload("res://scripts/ember/ui_edge_v001/energy_progress.gd")
const REPORT_PATH := "res://art-source/ember/ui-edge-v001/widget-audit-v002.json"

var _checks: Array[Dictionary] = []
var _failures: Array[String] = []
var _report: Dictionary = {}
var _drawer_closed_count: int = 0

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	if FileAccess.file_exists(REPORT_PATH):
		var previous: Variant = JSON.parse_string(FileAccess.get_file_as_string(REPORT_PATH))
		if previous is Dictionary:
			_report = previous
			if _report.get("mode", "") == "button_native_baseline":
				_report["button_before_change_validation"] = {
					"checks": _report.get("checks", []).duplicate(true),
					"failures": _report.get("failures", []).duplicate(true),
					"status": _report.get("status", ""),
				}
	root.size = Vector2i(960, 720)
	var host := Control.new()
	host.name = "WidgetProbeHost"
	host.size = Vector2(960, 720)
	root.add_child(host)
	await process_frame
	var button_observations: Dictionary = await _probe_button(host)
	var baseline_only := OS.get_cmdline_user_args().has("--button-only")
	_report["button_before_changes" if baseline_only else "button_after_changes"] = button_observations
	if not baseline_only:
		await _probe_drawer(host)
		await _probe_progress(host)
	_report["schema_version"] = 2
	_report["mode"] = "button_native_baseline" if baseline_only else "full_widget_regression"
	_report["engine"] = Engine.get_version_info()
	_report["button_disable_sync_contract"] = "Native disabled property is synchronized by the next process frame; immediate state is observed, not asserted."
	_report["checks"] = _checks
	_report["check_count"] = _checks.size()
	_report["failures"] = _failures
	_report["status"] = "PASS" if _failures.is_empty() else "FAIL"
	var report_file := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
	if report_file == null:
		push_error("无法写入独立组件审计报告。")
		quit(2)
		return
	report_file.store_string(JSON.stringify(_report, "\t"))
	report_file.close()
	print("Widget audit %s: %d checks, %d failures." % [_report["status"], _checks.size(), _failures.size()])
	host.free()
	quit(0 if _failures.is_empty() else 1)

func _probe_button(host: Control) -> Dictionary:
	var button := BUTTON.new()
	button.name = "NativeButtonProbe"
	button.size = Vector2(160, 52)
	host.add_child(button)
	await process_frame
	button.grab_focus()
	var focused: Dictionary = _button_snapshot(button)
	_check("button_focus_grabbed", bool(focused["has_focus"]))
	_check("button_focus_overlay_shown", bool(focused["focus_overlay_visible"]))
	button.disabled = true
	var disabled_immediate: Dictionary = _button_snapshot(button)
	await process_frame
	var disabled_next_frame: Dictionary = _button_snapshot(button)
	_check("button_disabled_property_set", bool(disabled_immediate["disabled"]))
	_check("button_disabled_overlay_hidden_next_frame", not bool(disabled_next_frame["focus_overlay_visible"]))
	_check("button_disabled_native_focus_released", not bool(disabled_next_frame["has_focus"]))
	button.disabled = false
	button.grab_focus()
	var enabled_refocused: Dictionary = _button_snapshot(button)
	_check("button_reenabled_can_focus", bool(enabled_refocused["has_focus"]))
	_check("button_reenabled_focus_overlay_shown", bool(enabled_refocused["focus_overlay_visible"]))
	button.release_focus()
	_check("button_explicit_release_hides_overlay", not button.get_node("FocusOverlay").visible)
	button.free()
	return {
		"focused": focused,
		"disabled_immediate": disabled_immediate,
		"disabled_next_frame": disabled_next_frame,
		"enabled_refocused": enabled_refocused,
	}

func _button_snapshot(button: Button) -> Dictionary:
	var owner := root.gui_get_focus_owner()
	return {
		"disabled": button.disabled,
		"has_focus": button.has_focus(),
		"focus_owner": str(owner.get_path()) if owner != null else "",
		"focus_overlay_visible": bool(button.get_node("FocusOverlay").visible),
	}

func _probe_drawer(host: Control) -> void:
	# 未入树节点没有 viewport；close 必须仍可安全执行且只在可见->隐藏时发信号。
	var drawer := DRAWER.new()
	drawer.name = "DrawerProbe"
	drawer.size = Vector2(248, 720)
	drawer.closed.connect(_on_drawer_closed)
	_drawer_closed_count = 0
	drawer.close()
	_check("drawer_pre_tree_close_hides", not drawer.visible)
	_check("drawer_pre_tree_close_emits_once", _drawer_closed_count == 1)
	drawer.close()
	_check("drawer_pre_tree_repeated_close_silent", _drawer_closed_count == 1)
	_check("drawer_pre_tree_close_ignores_pointer", drawer.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	host.add_child(drawer)
	await process_frame
	_check("drawer_ready_preserves_closed_visibility", not drawer.visible)
	drawer.open()
	var back: Button = drawer.get_back_button()
	_check("drawer_open_visible", drawer.visible)
	_check("drawer_open_stops_pointer", drawer.mouse_filter == Control.MOUSE_FILTER_STOP)
	_check("drawer_open_focuses_back_button", back.has_focus())
	drawer.close()
	_check("drawer_real_close_emits_once", _drawer_closed_count == 2)
	_check("drawer_real_close_hides", not drawer.visible)
	_check("drawer_real_close_releases_focus", not back.has_focus())
	_check("drawer_real_close_ignores_pointer", drawer.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	for index in range(5):
		drawer.close()
	_check("drawer_five_repeated_closes_silent", _drawer_closed_count == 2)
	drawer.open(false)
	_check("drawer_no_focus_open_visible", drawer.visible)
	_check("drawer_no_focus_open_preserves_focus", not back.has_focus())
	drawer.close()
	_check("drawer_second_real_close_emits_once", _drawer_closed_count == 3)
	host.remove_child(drawer)
	drawer.open(false)
	drawer.close()
	_check("drawer_removed_from_tree_close_safe", not drawer.visible and _drawer_closed_count == 4)
	drawer.close()
	_check("drawer_removed_from_tree_repeated_close_silent", _drawer_closed_count == 4)
	drawer.free()

func _probe_progress(host: Control) -> void:
	var progress := PROGRESS.new()
	progress.name = "ProgressProbe"
	progress.show_labels = false
	progress.show_clamps = false
	_check("progress_pre_tree_labels_false_minimum", progress.custom_minimum_size == Vector2(96, 24))
	progress.show_labels = true
	_check("progress_pre_tree_labels_true_minimum", progress.custom_minimum_size == Vector2(96, 64))
	progress.show_labels = false
	progress.size = Vector2(208, 24)
	host.add_child(progress)
	await process_frame
	_check_progress_display(progress, false, false, "ready_hidden")
	progress.set_data(145.0, 380.0)
	var baseline_fill: int = progress.get_fill_pixels()
	progress.show_labels = true
	_check_progress_display(progress, true, false, "labels_shown")
	_check("progress_label_toggle_preserves_fill_pixels", progress.get_fill_pixels() == baseline_fill)
	progress.show_clamps = true
	_check_progress_display(progress, true, true, "clamps_shown")
	progress.show_labels = false
	_check_progress_display(progress, false, true, "labels_hidden_again")
	progress.show_clamps = false
	_check_progress_display(progress, false, false, "clamps_hidden_again")
	_check("progress_toggles_preserve_minimum_width", progress.custom_minimum_size.x == 96)
	_check("progress_toggles_preserve_fill_ratio", is_equal_approx(progress.ratio, 145.0 / 380.0))
	# 独立数值条的紧凑宽度也不能让100%与左侧正文重叠。
	progress.show_labels = true
	progress.set_data(380.0, 380.0)
	for width in [200, 224]:
		progress.size = Vector2(width, 64)
		await process_frame
		var value: Label = progress.get("_value")
		var percent: Label = progress.get("_percent")
		_check("progress_full_%d_labels_keep_eight_pixel_gap" % width, value.position.x + value.size.x <= percent.position.x - 8)
	progress.free()

func _check_progress_display(progress: Control, labels: bool, clamps: bool, phase: String) -> void:
	var value: Label = progress.get("_value")
	var percent: Label = progress.get("_percent")
	var plate: Panel = progress.get("_value_plate")
	var track: Panel = progress.get("_track")
	var left_clamp: TextureRect = progress.get("_left_clamp")
	var right_clamp: TextureRect = progress.get("_right_clamp")
	_check("progress_%s_value_visibility" % phase, value.visible == labels)
	_check("progress_%s_percent_visibility" % phase, percent.visible == labels)
	_check("progress_%s_plate_visibility" % phase, plate.visible == labels)
	_check("progress_%s_minimum_height" % phase, progress.custom_minimum_size.y == (64 if labels else 24))
	_check("progress_%s_track_y" % phase, track.position.y == (42 if labels else 4))
	_check("progress_%s_left_clamp_visibility" % phase, left_clamp.visible == clamps)
	_check("progress_%s_right_clamp_visibility" % phase, right_clamp.visible == clamps)

func _on_drawer_closed() -> void:
	_drawer_closed_count += 1

func _check(identifier: String, passed: bool) -> void:
	_checks.append({"id": identifier, "passed": passed})
	if not passed:
		_failures.append(identifier)
