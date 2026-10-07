extends SceneTree
## v002审计回归：验证复用时的生命周期、长数值、动态配置与无效投影。
## 原245项常规验证保留在validate_ui_edge_logic_v001.gd，本文件只补遗漏边界。

const HUD = preload("res://scenes/ember/ui_edge_v001/components/edge_hud.tscn")
const DRAWER = preload("res://scripts/ember/ui_edge_v001/station_drawer.gd")
const BINDING = preload("res://scripts/ember/ui_edge_binding_v001.gd")
const STATE = preload("res://scripts/ember/ui_edge_v001/edge_ui_state.gd")
const REPORT_PATH := "res://art-source/ember/ui-edge-v001/reuse-validation-v002.json"

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

class MockUnprojectableStation:
	extends Node
	var enrgyState: int = 0
	var player: CharacterBody2D

var _checks: Array[Dictionary] = []
var _viewport: SubViewport
var _hud: Control
var _closed_count: int = 0

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var before_tree := DRAWER.new()
	before_tree.close()
	before_tree.close()
	_check("drawer.close_before_tree", not before_tree.visible and before_tree.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	before_tree.free()
	_viewport = SubViewport.new()
	_viewport.size = Vector2i(720, 720)
	root.add_child(_viewport)
	var canvas := CanvasLayer.new()
	_viewport.add_child(canvas)
	_hud = HUD.instantiate()
	_hud.set_game_state({"life": 3, "max_life": 3, "seconds": 120.0})
	_hud.set_marker_screen_position(Vector2(NAN, INF))
	canvas.add_child(_hud)
	_hud.drawer_closed.connect(func(): _closed_count += 1)
	await _settle()
	_check("hud.before_tree_data", _hud.get_game_state().life == 3)
	_check("marker.invalid_coordinates", not _hud.get_marker().visible and _hud.get_marker().position.is_finite())
	_hud.close_drawer()
	_hud.close_drawer()
	_check("drawer.already_closed_signal", _closed_count == 0, {"count": _closed_count})
	_hud.open_drawer()
	await _settle()
	_hud.close_drawer()
	_hud.close_drawer()
	_hud.close_drawer()
	_check("drawer.close_exactly_once", _closed_count == 1, {"count": _closed_count})
	_check("drawer.close_releases_focus", _viewport.gui_get_focus_owner() == null)
	_test_node_reuse()
	_test_large_values()
	await _test_layout_and_configuration()
	await _test_binding_lifetime()
	var failed := 0
	for check in _checks:
		if not check["pass"]:
			failed += 1
	var report := {"status": "PASS" if failed == 0 else "FAIL", "check_count": _checks.size(), "failure_count": failed, "checks": _checks}
	var output := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "\t"))
	output.close()
	print("UI_EDGE_REUSE %s: %d checks, %d failures" % [report.status, _checks.size(), failed])
	_viewport.free()
	quit(0 if failed == 0 else 1)

func _settle() -> void:
	await process_frame
	await process_frame

func _check(id: String, ok: bool, details: Dictionary = {}) -> void:
	_checks.append({"id": id, "pass": ok, "details": details})
	if not ok:
		print("FAIL ", id, ": ", JSON.stringify(details))

func _slot_ids(indicator: Control) -> Array[int]:
	var result: Array[int] = []
	for slot: Control in indicator.get("_slots"):
		result.append(slot.get_instance_id())
	return result

func _test_node_reuse() -> void:
	var life: Control = _hud.get("_life")
	var original_slots := _slot_ids(life)
	for index in range(20):
		_hud.set_game_state({"energy": 100.0 + index})
	_check("life.energy_updates_reuse_slots", _slot_ids(life) == original_slots)
	_hud.set_game_state({"life": 1})
	_check("life.life_change_reuses_slots", _slot_ids(life) == original_slots)
	var lit := 0
	for slot: Control in life.get("_slots"):
		if slot.get_child(0).visible:
			lit += 1
	_check("life.reused_fill_is_updated", lit == 1)
	_hud.set_game_state({"max_life": 12, "life": 8})
	life.set_slot_budget(2)
	_check("life.folded_count_is_exact", life.get("_slots").size() == 2 and life.get("_count").text == "8 / 12")
	life.set_slot_budget(0)
	_check("life.zero_slot_budget_keeps_count", life.get("_slots").is_empty() and life.get("_count").text == "8 / 12")
	_hud.set_game_state({"max_life": 3, "life": 2})

func _test_large_values() -> void:
	for value in [1.0e15, 1.0e20, 1.0e30, 1.0e300]:
		var formatted: String = STATE.format_quantity(value)
		_check("quantity.finite_scientific.%s" % str(value), formatted.contains("e") and not formatted.contains("%") and not formatted.contains("nan"), {"formatted": formatted})
		_hud.set_game_state({"energy_goal": value, "energy": value * 0.5})
		_check("quantity.raw_goal_preserved.%s" % str(value), _hud.get_game_state().energy_goal == value and is_equal_approx(_hud.get_energy_progress().get("ratio"), 0.5))
	var timer: Control = _hud.get("_timer")
	for value in [5999.0, 6000.0, 359999.0, 360000.0, 1.0e9, 1.0e30, 1.0e300, NAN, INF]:
		timer.set_data(value)
		var label: Label = timer.get("_value")
		var formatted := label.text
		var font: Font = label.get_theme_font("font")
		var font_size := label.get_theme_font_size("font_size")
		var glyph_width := font.get_string_size(formatted, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
		_check("timer.safe_value.%s" % str(value), is_finite(float(timer.get("seconds"))) and float(timer.get("seconds")) >= 0 and not formatted.contains("%"), {"formatted": formatted})
		_check("timer.long_text_contained.%s" % str(value), label.clip_text and label.size.x <= timer.size.x - 32 and glyph_width <= label.size.x, {"text": formatted, "width": glyph_width, "allocated": label.size.x})
	_hud.set_game_state({"seconds": 78.0, "energy": 145.0, "energy_goal": 380.0})

func _test_layout_and_configuration() -> void:
	_hud.open_drawer()
	_hud.drawer_width = 280
	_check("hud.drawer_width_updates_immediately", _hud.get_drawer().size.x == 280)
	_hud.safe_margin = 64
	_check("hud.safe_margin_updates_immediately", _hud.get_energy_progress().position.x == 44)
	_hud.drawer_width = 248
	_hud.safe_margin = 36
	for viewport_size in [Vector2i(480, 480), Vector2i(960, 540), Vector2i(360, 640)]:
		_viewport.size = viewport_size
		await _settle()
		_hud.set_game_state({"max_life": 12, "life": 8})
		var life: Control = _hud.get("_life")
		var energy: Control = _hud.get_energy_progress()
		_check("layout.life_avoids_bottom.%s" % str(viewport_size), not life.visible or life.position.y + life.size.y <= energy.position.y - 12, {"life_bottom": life.position.y + life.size.y, "energy_top": energy.position.y})
		var drawer: Control = _hud.get_drawer()
		_check("layout.drawer_bounds.%s" % str(viewport_size), Rect2(Vector2.ZERO, Vector2(viewport_size)).encloses(drawer.get_rect()))
		if viewport_size.x < 448:
			_check("layout.narrow_drawer_prioritizes_contents", not life.visible and not energy.visible and not _hud.get("_timer").visible)
	_viewport.size = Vector2i(720, 720)
	await _settle()
	_hud.close_drawer()
	_hud.set_game_state({"max_life": 3, "life": 2})
	_check("layout.world_hud_restored", _hud.get("_life").visible and _hud.get_energy_progress().visible and _hud.get("_timer").visible)

func _test_binding_lifetime() -> void:
	var game := MockGame.new()
	var pawn := CharacterBody2D.new()
	var station := MockStation.new()
	var data_station := MockUnprojectableStation.new()
	var binding := BINDING.new()
	for node in [game, pawn, station, data_station, binding]:
		_viewport.add_child(node)
	station.player = pawn
	data_station.player = pawn
	station.position = Vector2(200, 250)
	binding.bind_sources(_hud, game, station)
	_check("binding.projectable_marker", _hud.get_marker().visible)
	binding.select_station(data_station, "没有世界坐标的数据源")
	_check("binding.unprojectable_marker_is_hidden", not _hud.get_marker().visible)
	binding.select_station(station)
	binding.max_life = 6
	binding.refresh()
	_check("binding.max_life_is_configurable", _hud.get_game_state().max_life == 6)
	binding.station_portrait = null
	binding.refresh()
	_check("binding.runtime_portrait_is_updated", _hud.get_drawer().get("_portrait").texture == null)
	_hud.open_drawer()
	var previous_count := _closed_count
	station.free()
	for index in range(20):
		binding.refresh()
	_check("binding.freed_station_closes_once", _closed_count == previous_count + 1, {"closed_events": _closed_count - previous_count})
	previous_count = _closed_count
	game.free()
	for index in range(20):
		binding.refresh()
	_check("binding.freed_game_does_not_reclose", _closed_count == previous_count)
	binding.free()
	pawn.free()
	data_station.free()
