extends SceneTree
## A 稿 UI 的独立 headless 逻辑验证；不修改组件和现有玩法。
## 运行：Godot --headless --path <项目> --script res://tools/validate_ui_edge_logic_v001.gd

const HUD_SCENE = preload("res://scenes/ember/ui_edge_v001/components/edge_hud.tscn")
const BINDING = preload("res://scripts/ember/ui_edge_binding_v001.gd")
const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
const REPORT_PATH := "res://art-source/ember/ui-edge-v001/logic-validation.json"

class MockGame:
	extends Node
	var lifePoint: int = 2
	var energyPoint: float = 145.0
	var countdown: int = 78
	var isGameStarting: bool = true

class MockStation:
	extends Node2D
	var enrgyState: int = 0
	var player: CharacterBody2D

var _checks: Array[Dictionary] = []
var _closed_signals: int = 0
var _viewport: SubViewport
var _hud: Control

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	# 独立 viewport 确保两种验证尺寸不受用户编辑器窗口影响。
	_viewport = SubViewport.new()
	_viewport.size = Vector2i(720, 720)
	root.add_child(_viewport)
	var canvas := CanvasLayer.new()
	_viewport.add_child(canvas)
	_hud = HUD_SCENE.instantiate()
	canvas.add_child(_hud)
	_hud.drawer_closed.connect(_on_drawer_closed)
	await _settle()
	_test_life_and_time()
	_test_energy()
	_test_states()
	_test_copy_and_partial_updates()
	await _test_drawer_and_marker()
	await _test_layouts()
	_test_collecting_truth_table()
	await _test_binding()
	_write_report()
	var failures := _failure_count()
	print("UI_EDGE_LOGIC %s: %d checks, %d failures" % ["PASS" if failures == 0 else "FAIL", _checks.size(), failures])
	_viewport.free()
	quit(0 if failures == 0 else 1)

func _settle() -> void:
	await process_frame
	await process_frame

func _check(id: String, ok: bool, details: Dictionary = {}) -> void:
	_checks.append({"id": id, "pass": ok, "details": details})
	if not ok:
		print("FAIL ", id, ": ", JSON.stringify(details))

func _test_life_and_time() -> void:
	var indicator: Control = _hud.get("_life")
	for sample in [[3, 3, 3], [2, 3, 2], [0, 3, 0], [-5, 3, 0], [9, 3, 3], [4, 0, 0], [8, 8, 8]]:
		_hud.set_game_state({"life": sample[0], "max_life": sample[1]})
		var snapshot: Dictionary = _hud.get_game_state()
		var slots: Array = indicator.get("_slots")
		var lit := 0
		for slot: Control in slots:
			if slot.get_child(0).visible:
				lit += 1
			_check("life.outline.%s.%s" % [sample[0], lit], slot.get_child(1).visible and slot.get_child_count() == 2)
		_check("life.clamp.%s.%s" % [sample[0], sample[1]], snapshot.life == sample[2] and indicator.get("life") == sample[2], {"snapshot": snapshot.life})
		_check("life.fill_count.%s.%s" % [sample[0], sample[1]], lit == mini(sample[2], 6), {"lit": lit, "slots": slots.size()})
		if sample[1] > 6:
			_check("life.large_count_label", indicator.get("_count").text == "8 / 8")
	var timer: Control = _hud.get("_timer")
	for sample in [[120.0, "02:00"], [78.0, "01:18"], [0.0, "00:00"], [-7.0, "00:00"], [1.1, "00:02"], [NAN, "00:00"], [INF, "00:00"]]:
		_hud.set_game_state({"seconds": sample[0]})
		_check("timer.%s" % sample[1], timer.get("_value").text == sample[1], {"text": timer.get("_value").text})
	_hud.set_game_state({"life": 2, "max_life": 3, "seconds": 78.0})

func _test_energy() -> void:
	var bar: Control = _hud.get_energy_progress()
	for sample in [[0.0, 380.0, 0.0], [145.0, 380.0, 145.0 / 380.0], [380.0, 380.0, 1.0], [999.0, 380.0, 1.0], [145.0, 0.0, 0.0], [-3.0, 380.0, 0.0], [NAN, 380.0, 0.0], [INF, 380.0, 0.0], [145.0, NAN, 0.0], [145.0, INF, 0.0], [145.0, -1.0, 0.0]]:
		_hud.set_game_state({"energy": sample[0], "energy_goal": sample[1]})
		var ratio: float = bar.get("ratio")
		var fill_clip: Control = bar.get_fill_clip()
		var interior := maxi(0, int(roundf(bar.size.x)) - 20)
		_check("energy.ratio.%d" % _checks.size(), is_finite(ratio) and is_equal_approx(ratio, sample[2]), {"ratio": ratio})
		_check("energy.integer_fill.%d" % _checks.size(), bar.get_fill_pixels() == int(roundf(interior * sample[2])) and fill_clip.size.x == float(bar.get_fill_pixels()), {"pixels": bar.get_fill_pixels(), "interior": interior})
		_check("energy.fill_only_clip.%d" % _checks.size(), fill_clip.clip_contents and not bar.clip_contents and bar.get("_fill").get_parent() == fill_clip)
		_check("energy.fixed_caps_siblings.%d" % _checks.size(), bar.get("_left_clamp").get_parent() == bar and bar.get("_right_clamp").get_parent() == bar and bar.get("_track").get_parent() == bar)
		_check("energy.outer_caps_visible.%d" % _checks.size(), bar.get("_left_clamp").visible and bar.get("_right_clamp").visible)
		if is_equal_approx(sample[2], 1.0):
			_check("energy.full_does_not_clip_caps.%d" % _checks.size(), not fill_clip.is_ancestor_of(bar.get("_left_clamp")) and not fill_clip.is_ancestor_of(bar.get("_right_clamp")) and fill_clip.size.x == interior)
	_hud.set_game_state({"energy": 145.0, "energy_goal": 380.0})
	_check("energy.145_display", bar.get("_value").text == "145 / 380" and bar.get("_percent").text == "38%")

func _test_states() -> void:
	var drawer: Control = _hud.get_drawer()
	for state_value in [0, 1, 2, 3, -1, 4]:
		_hud.set_station_state(state_value, true)
		var snapshot: Dictionary = _hud.get_game_state()
		var rows: Array = drawer.get("_rows")
		var active_indices: Array[int] = []
		for index in range(rows.size()):
			var row: Control = rows[index]
			if row.get("active"):
				active_indices.append(index)
			_check("state.readonly_row.%s.%s" % [state_value, index], row.mouse_filter == Control.MOUSE_FILTER_IGNORE and row.focus_mode == Control.FOCUS_NONE)
		var valid: bool = state_value >= 0 and state_value <= 3
		_check("state.active_exact.%s" % state_value, active_indices == [state_value] if valid else active_indices.is_empty(), {"active": active_indices})
		_check("state.collecting.%s" % state_value, bool(snapshot.collecting) == (state_value in [0, 1]))
		if not valid:
			_check("state.invalid_unknown.%s" % state_value, snapshot.station_state == -1 and not STATE.can_collect(snapshot.station_state) and "未知" in drawer.get("_hint").text)
	_hud.set_station_state(0, true)

func _test_copy_and_partial_updates() -> void:
	var before: Dictionary = _hud.get_game_state()
	var external: Dictionary = _hud.get_game_state()
	external["life"] = 0
	external["injected"] = true
	_check("data.get_returns_copy", _hud.get_game_state() == before)
	_hud.set_data({"seconds": 40.0, "not_in_contract": 42})
	var after: Dictionary = _hud.get_game_state()
	_check("data.partial_updates", after.seconds == 40.0 and after.life == before.life and not after.has("not_in_contract"))
	_hud.set_game_state({"seconds": 78.0})

func _test_drawer_and_marker() -> void:
	_hud.close_drawer()
	await _settle()
	var full_energy_width: float = _hud.get_energy_progress().size.x
	var drawer: Control = _hud.get_drawer()
	var button: Button = drawer.get_back_button()
	_hud.set_station_state(0, true)
	_hud.set_marker_screen_position(Vector2(560, 240), true)
	_check("marker.closed_visible", _hud.get_marker().visible)
	_hud.open_drawer()
	await _settle()
	_check("drawer.open_stop", drawer.visible and drawer.mouse_filter == Control.MOUSE_FILTER_STOP and _hud.is_drawer_open())
	_check("drawer.open_focus", button.has_focus())
	_check("drawer.open_energy_shorter", _hud.get_energy_progress().size.x < full_energy_width)
	_check("drawer.timer_outside", _hud.get_available_world_rect().encloses(_hud.get("_timer").get_rect()))
	_check("marker.drawer_occlusion", not _hud.get_marker().visible)
	_hud.close_drawer()
	await _settle()
	_check("drawer.close_hidden_ignore", not drawer.visible and drawer.mouse_filter == Control.MOUSE_FILTER_IGNORE and not _hud.is_drawer_open())
	_check("drawer.close_focus_released", not button.has_focus() and _viewport.gui_get_focus_owner() == null)
	_check("marker.close_auto_restore", _hud.get_marker().visible and _hud.get_marker().position == Vector2(560, 240))
	_hud.open_drawer()
	await _settle()
	var signal_before := _closed_signals
	button.pressed.emit()
	await _settle()
	_check("drawer.return_signal", _closed_signals == signal_before + 1 and not drawer.visible and not _hud.is_drawer_open())
	_hud.open_drawer()
	await _settle()
	_hud.set_drawer_open(false)
	await _settle()
	_check("drawer.external_close_releases_focus", not button.has_focus() and not drawer.visible and drawer.mouse_filter == Control.MOUSE_FILTER_IGNORE)

func _test_layouts() -> void:
	for requested_size in [Vector2i(720, 720), Vector2i(960, 540)]:
		_viewport.size = requested_size
		_hud.size = Vector2(requested_size)
		_hud.set_game_state({"station_name": "采能站 01", "life": 2, "max_life": 3})
		_hud.open_drawer()
		await _settle()
		var bounds := Rect2(Vector2.ZERO, Vector2(requested_size))
		var drawer: Control = _hud.get_drawer()
		_check("layout.hud_size.%s" % requested_size, _hud.size == Vector2(requested_size), {"size": _vec(_hud.size)})
		for key in ["_life", "_timer", "_energy", "_drawer"]:
			var widget: Control = _hud.get(key)
			_check("layout.in_bounds.%s.%s" % [requested_size, key], bounds.encloses(widget.get_rect()), {"rect": _rect(widget.get_rect())})
		_check("layout.drawer_minimum.%s" % requested_size, drawer.get_combined_minimum_size().x <= drawer.size.x and drawer.get_combined_minimum_size().y <= drawer.size.y)
		for key in ["_title", "_portrait", "_portrait_frame", "_goal_label", "_goal_value", "_progress", "_hint", "_back"]:
			var widget: Control = drawer.get(key)
			_check("layout.drawer_content.%s.%s" % [requested_size, key], Rect2(Vector2.ZERO, drawer.size).encloses(widget.get_rect()), {"rect": _rect(widget.get_rect()), "drawer_size": _vec(drawer.size)})
		# 铜色把手允许伸到抽屉外；正文在独立 ContentClip 内裁切即可。
		var content_clip: Control = drawer.get_node_or_null("ContentClip")
		var clips_content := drawer.clip_contents or (content_clip != null and content_clip.clip_contents and content_clip.size == drawer.size)
		_check("layout.drawer_clips.%s" % requested_size, clips_content)
		if content_clip != null:
			_check("layout.clip_contains_all_text.%s" % requested_size, content_clip.is_ancestor_of(drawer.get("_title")) and content_clip.is_ancestor_of(drawer.get("_hint")) and content_clip.is_ancestor_of(drawer.get("_back")))
		var hint: Label = drawer.get("_hint")
		var back: Button = drawer.get_back_button()
		_check("layout.hint_button_no_overlap.%s" % requested_size, hint.position.y + hint.size.y <= back.position.y, {"hint_rect": _rect(hint.get_rect()), "button_rect": _rect(back.get_rect())})
		_hud.set_game_state({"station_name": "采能站 01 / 超长名称压力测试：蓝灰工业旧港设备终端与更多文字"})
		await _settle()
		var title: Label = drawer.get("_title")
		_check("layout.long_title_clip.%s" % requested_size, title.clip_text or title.text_overrun_behavior != TextServer.OVERRUN_NO_TRIMMING)
		_check("layout.long_title_contained.%s" % requested_size, Rect2(Vector2.ZERO, drawer.size).encloses(title.get_rect()), {"title_rect": _rect(title.get_rect()), "title_min": _vec(title.get_combined_minimum_size()), "drawer_size": _vec(drawer.size)})
	_hud.set_game_state({"station_name": "采能站 01"})
	_hud.close_drawer()
	_viewport.size = Vector2i(720, 720)
	_hud.size = Vector2(720, 720)
	await _settle()

func _test_collecting_truth_table() -> void:
	# 每个真实状态覆盖 active / in_area / still 的 8 种组合，另含两个非法状态。
	for state_value in [0, 1, 2, 3, -1, 4]:
		for mask in range(8):
			var active := bool(mask & 1)
			var in_area := bool(mask & 2)
			var still := bool(mask & 4)
			var expected: bool = active and in_area and still and state_value in [0, 1]
			_check("binding.collecting.%s.%s" % [state_value, mask], BINDING.should_show_collecting(active, in_area, still, state_value) == expected)

func _test_binding() -> void:
	var game := MockGame.new()
	var station := MockStation.new()
	station.position = Vector2(220, 240)
	var player := CharacterBody2D.new()
	station.player = player
	var adapter := BINDING.new()
	adapter.set_process(false)
	_viewport.add_child(game)
	_viewport.add_child(station)
	_viewport.add_child(player)
	_viewport.add_child(adapter)
	adapter.bind_sources(_hud, game, station)
	await _settle()
	_check("binding.live_source", _hud.get_game_state().collecting and _hud.get_game_state().energy == 145.0 and _hud.get_marker().visible)
	station.enrgyState = 1
	adapter.refresh()
	_check("binding.warning_collects", _hud.get_game_state().station_state == 1 and _hud.get_game_state().collecting)
	player.velocity = Vector2(1, 0)
	adapter.refresh()
	_check("binding.moving_hides", not _hud.get_game_state().collecting and not _hud.get_marker().visible)
	player.velocity = Vector2.ZERO
	game.isGameStarting = false
	adapter.refresh()
	_check("binding.ended_hides", not _hud.get_game_state().collecting and not _hud.get_marker().visible)
	game.isGameStarting = true
	adapter.select_station(null)
	_check("binding.null_station_clears", _cleared_station())
	adapter.select_station(station, "采能站真实绑定")
	_hud.open_drawer()
	station.free()
	adapter.refresh()
	_check("binding.freed_station_clears", _cleared_station())
	game.free()
	adapter.refresh()
	_check("binding.freed_game_hides", not _hud.get_marker().visible and not _hud.is_drawer_open() and not _hud.get_game_state().collecting)
	player.free()
	adapter.free()

func _cleared_station() -> bool:
	var snapshot: Dictionary = _hud.get_game_state()
	return snapshot.station_state == -1 and not snapshot.collecting and snapshot.station_name == "未连接设备" and not _hud.get_marker().visible and not _hud.is_drawer_open()

func _on_drawer_closed() -> void:
	_closed_signals += 1

func _failure_count() -> int:
	var count := 0
	for result: Dictionary in _checks:
		if not result.pass:
			count += 1
	return count

func _vec(value: Vector2) -> Array:
	return [value.x, value.y]

func _rect(value: Rect2) -> Dictionary:
	return {"position": _vec(value.position), "size": _vec(value.size)}

func _write_report() -> void:
	var failures := _failure_count()
	var source_hashes := {}
	for filename in ["edge_hud.gd", "energy_progress.gd", "life_indicator.gd", "timer_badge.gd", "station_drawer.gd", "state_row.gd", "station_marker.gd", "bracket_button.gd", "edge_ui_state.gd", "edge_ui_style.gd"]:
		var path: String = "res://scripts/ember/ui_edge_v001/" + filename
		source_hashes[path] = FileAccess.get_sha256(path)
	source_hashes["res://scripts/ember/ui_edge_binding_v001.gd"] = FileAccess.get_sha256("res://scripts/ember/ui_edge_binding_v001.gd")
	var report := {"status": "PASS" if failures == 0 else "FAIL", "check_count": _checks.size(), "failure_count": failures, "engine_version": Engine.get_version_info().string, "generated_utc": Time.get_datetime_string_from_system(true), "source_sha256": source_hashes, "checks": _checks}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(REPORT_PATH.get_base_dir()))
	var output := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
	if output == null:
		print("FAIL report_write: ", FileAccess.get_open_error())
		quit(2)
		return
	output.store_string(JSON.stringify(report, "\t") + "\n")
	output.close()
