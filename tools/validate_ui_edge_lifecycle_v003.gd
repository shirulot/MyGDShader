extends SceneTree
## 生命周期实测：缓存HUD离树/复挂/跨视口后，状态、焦点、遮盖与布局保持一致。
## 原TA的before证据单独保留，本测试只读取生产组件并写自己的after报告。

const HUD = preload("res://scenes/ember/ui_edge_v001/components/edge_hud.tscn")
const DRAWER = preload("res://scripts/ember/ui_edge_v001/station_drawer.gd")
const BINDING = preload("res://scripts/ember/ui_edge_binding_v001.gd")
const REPORT := "res://art-source/ember/ui-edge-v001/lifecycle-validation-v003.json"
const SOURCES := [
	"res://scripts/ember/ui_edge_v001/edge_hud.gd",
	"res://scripts/ember/ui_edge_v001/station_drawer.gd",
	"res://scripts/ember/ui_edge_v001/energy_progress.gd",
	"res://scripts/ember/ui_edge_v001/bracket_button.gd",
	"res://scripts/ember/ui_edge_v001/state_row.gd",
	"res://scripts/ember/ui_edge_binding_v001.gd",
	"res://tools/validate_ui_edge_lifecycle_v003.gd",
]

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
var _hud: Control
var _view_a: SubViewport
var _view_b: SubViewport
var _canvas_a: CanvasLayer
var _canvas_b: CanvasLayer
var _closed_count: int = 0
var _original_ids: Array[int] = []
var _original_drawer_ids: Array[int] = []
var _source_before: Dictionary = {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	_source_before = _hash_sources()
	_view_a = _make_viewport(Vector2i(720, 720))
	_view_b = _make_viewport(Vector2i(960, 540))
	_canvas_a = CanvasLayer.new()
	_canvas_b = CanvasLayer.new()
	_view_a.add_child(_canvas_a)
	_view_b.add_child(_canvas_b)
	_hud = HUD.instantiate()
	_hud.drawer_closed.connect(func(): _closed_count += 1)
	_canvas_a.add_child(_hud)
	await _settle()
	_original_ids = _child_ids(_hud)
	_original_drawer_ids = _child_ids(_hud.get_drawer().get("_content_clip"))
	_hud.set_marker_screen_position(Vector2(560, 240), true)
	_hud.open_drawer()
	await _settle()
	_check("initial.open_focus", _hud.get_drawer().get_back_button().has_focus())
	_check("initial.marker_occluded", not _hud.get_marker().visible)
	_check_geometry("initial.open", _view_a, true)

	# 缓存组件离树，静默同步关闭，再挂回同一个CanvasLayer。
	_canvas_a.remove_child(_hud)
	var silent_count := _closed_count
	_hud.set_drawer_open(false)
	_check_closed("detached.silent_close")
	_check("detached.silent_close_no_signal", _closed_count == silent_count)
	_check("detached.focus_released", _view_a.gui_get_focus_owner() == null)
	_canvas_a.add_child(_hud)
	await _settle()
	_check_closed("same_parent.readd")
	_check_geometry("same_parent.readd", _view_a, false)
	_check("same_parent.marker_restored", _hud.get_marker().visible and _hud.get_marker().position == Vector2(560, 240))
	_check_reused("same_parent")

	# 离树期间修改数据及参数，目标CanvasLayer必须以自己的viewport排布。
	_canvas_a.remove_child(_hud)
	_hud.safe_margin = 52
	_hud.drawer_width = 288
	_hud.set_game_state({"life": 6, "max_life": 6, "energy": 320.0, "energy_goal": 640.0, "station_state": 1, "station_name": "跨视口复挂设备", "seconds": 3600.0})
	_hud.set_drawer_open(true)
	_check("cross.detached_open_flag", _hud.is_drawer_open() and _hud.get_drawer().visible and _hud.get_drawer().mouse_filter == Control.MOUSE_FILTER_STOP)
	_check("cross.detached_open_no_old_focus", _view_a.gui_get_focus_owner() == null and _view_b.gui_get_focus_owner() == null)
	_canvas_b.add_child(_hud)
	await _settle()
	_check_geometry("cross.readd_open", _view_b, true)
	_check("cross.readd_focus_new_viewport", _view_b.gui_get_focus_owner() == _hud.get_drawer().get_back_button() and _view_a.gui_get_focus_owner() == null)
	_check("cross.offtree_data_preserved", _hud.get_game_state().energy == 320.0 and _hud.get_game_state().station_name == "跨视口复挂设备" and _hud.get_game_state().station_state == 1)
	_check("cross.config_preserved", _hud.safe_margin == 52 and _hud.drawer_width == 288)
	_check("cross.marker_occluded", not _hud.get_marker().visible)
	_check_reused("cross_parent")
	_hud.close_drawer()
	await _settle()
	_check("cross.marker_close_restores", _hud.get_marker().visible and _hud.get_marker().position == Vector2(560, 240))
	_check_geometry("cross.closed", _view_b, false)

	# 已建组件的off-tree显式close只能通知一次，重复调用必须幂等。
	_hud.open_drawer()
	await _settle()
	_canvas_b.remove_child(_hud)
	var before_explicit := _closed_count
	_hud.close_drawer()
	_hud.close_drawer()
	_hud.close_drawer()
	_check_closed("detached.explicit_close")
	_check("detached.explicit_close_once", _closed_count == before_explicit + 1, {"before": before_explicit, "after": _closed_count})
	_canvas_b.add_child(_hud)
	await _settle()
	_check_closed("detached.explicit_close_readd")
	_check("detached.explicit_close_readd_no_focus", _view_b.gui_get_focus_owner() == null)

	# 已排队的restore须读取最新状态，不能用旧open快照覆盖同步close。
	_canvas_b.remove_child(_hud)
	_hud.open_drawer()
	_canvas_b.add_child(_hud)
	silent_count = _closed_count
	_hud.set_drawer_open(false)
	await _settle()
	_check_closed("deferred_restore.latest_flag_wins")
	_check("deferred_restore.silent_close_no_signal", _closed_count == silent_count)
	for cycle in range(3):
		_hud.open_drawer()
		await _settle()
		_canvas_b.remove_child(_hud)
		_hud.set_drawer_open(false)
		_canvas_b.add_child(_hud)
		await _settle()
		_check_closed("repeat_%d" % cycle)
		_check_reused("repeat_%d" % cycle)

	await _test_independent_drawer()
	await _test_binding_visibility()
	var hashes := _hash_sources()
	_check("sources.unchanged_during_run", hashes == _source_before)
	var failures := 0
	for check in _checks:
		if not check["pass"]:
			failures += 1
	var report := {
		"status": "PASS" if failures == 0 else "FAIL", "check_count": _checks.size(), "failure_count": failures,
		"source_sha256": hashes, "checks": _checks,
		"logical_viewports": [[720,720], [960,540]],
		"before_evidence": {
			"origin": "TA independent cold-project probe; unchanged original evidence, not rerun with fixed source",
			"report": "res://art-source/ember/ta-review-v001/ui-independent/cold-project/ta-independent-probe.json",
			"stderr": "res://art-source/ember/ta-review-v001/ui-independent/ta-probe.stderr.log",
			"known_failures": ["lifecycle.detached_hud_external_close_hides_drawer", "lifecycle.reinserted_hud_external_close_is_consistent"],
			"additional_layout_before": "res://art-source/ember/ui-edge-v001/lifecycle-layout-before-v003.json",
		},
	}
	var output := FileAccess.open(REPORT, FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "\t") + "\n")
	output.close()
	print("UI_EDGE_LIFECYCLE %s: %d checks, %d failures" % [report.status, _checks.size(), failures])
	_view_a.free()
	_view_b.free()
	quit(0 if failures == 0 else 1)

func _make_viewport(dimensions: Vector2i) -> SubViewport:
	var viewport := SubViewport.new()
	viewport.size = dimensions
	root.add_child(viewport)
	return viewport

func _settle() -> void:
	await process_frame
	await process_frame
	await process_frame

func _check(id: String, ok: bool, details: Dictionary = {}) -> void:
	_checks.append({"id": id, "pass": ok, "details": details})
	if not ok:
		print("FAIL ", id, ": ", JSON.stringify(details))

func _child_ids(parent: Node) -> Array[int]:
	var ids: Array[int] = []
	for child in parent.get_children():
		ids.append(child.get_instance_id())
	return ids

func _check_reused(prefix: String) -> void:
	_check(prefix + ".no_duplicate_hud_build", _child_ids(_hud) == _original_ids and _hud.get_child_count() == 5)
	_check(prefix + ".no_duplicate_drawer_build", _child_ids(_hud.get_drawer().get("_content_clip")) == _original_drawer_ids and (_hud.get_drawer().get("_rows") as Array).size() == 4)

func _check_closed(prefix: String) -> void:
	var drawer: Control = _hud.get_drawer()
	_check(prefix + ".flag_hidden_ignore", not _hud.is_drawer_open() and not drawer.visible and drawer.mouse_filter == Control.MOUSE_FILTER_IGNORE, {"flag": _hud.is_drawer_open(), "visible": drawer.visible, "filter": drawer.mouse_filter})
	_check(prefix + ".closed_world_width", _hud.get_available_world_rect().size == _hud.size, {"world": _rect(_hud.get_available_world_rect()), "hud": _rect(_hud.get_rect())})

func _check_geometry(prefix: String, viewport: SubViewport, opened: bool) -> void:
	var bounds := Rect2(Vector2.ZERO, Vector2(viewport.size))
	_check(prefix + ".hud_uses_parent_viewport", _hud.size == Vector2(viewport.size) and _hud.get_viewport() == viewport, {"hud": _rect(_hud.get_rect()), "viewport": [viewport.size.x, viewport.size.y]})
	for name in ["_life", "_timer", "_energy", "_drawer"]:
		var control: Control = _hud.get(name)
		_check(prefix + ".in_bounds." + name, not control.is_visible_in_tree() or bounds.encloses(control.get_global_rect()), {"rect": _rect(control.get_global_rect()), "visible": control.is_visible_in_tree()})
	var drawer: Control = _hud.get_drawer()
	var expected_world: float = viewport.size.x - drawer.size.x if opened else float(viewport.size.x)
	_check(prefix + ".world_matches_drawer", is_equal_approx(_hud.get_available_world_rect().size.x, expected_world) and _hud.get_available_world_rect().size.y == viewport.size.y)
	var energy: Control = _hud.get_energy_progress()
	var track: Control = energy.get("_track")
	_check(prefix + ".energy_children_use_current_size", is_equal_approx(track.size.x, energy.size.x - 16), {"energy_width": energy.size.x, "track_width": track.size.x})
	var expected_fill := int(roundf((energy.size.x - 20) * float(energy.get("ratio"))))
	_check(prefix + ".energy_fill_uses_current_size", energy.get_fill_pixels() == expected_fill, {"expected": expected_fill, "actual": energy.get_fill_pixels()})
	if opened:
		_check(prefix + ".drawer_right_edge", is_equal_approx(drawer.global_position.x + drawer.size.x, viewport.size.x))
		var content: Control = drawer.get("_content_clip")
		_check(prefix + ".drawer_clip_uses_current_size", content.size == drawer.size, {"content": _rect(content.get_rect()), "drawer": _rect(drawer.get_rect())})
		var back: Control = drawer.get_back_button()
		_check(prefix + ".back_visible_in_bounds", back.is_visible_in_tree() and drawer.get_global_rect().encloses(back.get_global_rect()), {"visible": back.is_visible_in_tree(), "back": _rect(back.get_global_rect()), "drawer": _rect(drawer.get_global_rect()), "local_back": _rect(back.get_rect())})
		var focus_layer: Control = back.get("_focus_layer")
		_check(prefix + ".back_focus_layer_matches_size", focus_layer.size == back.size, {"back_size": [back.size.x, back.size.y], "focus_size": [focus_layer.size.x, focus_layer.size.y]})
		var corners: Array = back.get("_corners")
		var positions := [Vector2.ZERO, Vector2(back.size.x - 16, 0), Vector2(0, back.size.y - 16), back.size - Vector2(16, 16)]
		var corners_match := corners.size() == 4
		var actual_corner_positions: Array = []
		for index in range(corners.size()):
			actual_corner_positions.append([corners[index].position.x, corners[index].position.y])
			corners_match = corners_match and corners[index].position == positions[index]
		_check(prefix + ".back_corners_match_size", corners_match, {"positions": actual_corner_positions, "back_size": [back.size.x, back.size.y]})
		var rows: Array = drawer.get("_rows")
		for index in range(rows.size()):
			var row: Control = rows[index]
			var plate: Control = row.get("_backplate")
			var label: Control = row.get("_label")
			_check(prefix + ".row%d_backplate_matches_size" % index, plate.size == row.size, {"row": _rect(row.get_rect()), "plate": _rect(plate.get_rect())})
			_check(prefix + ".row%d_label_matches_size" % index, label.size == Vector2(maxf(0, row.size.x - 80), row.size.y), {"row": _rect(row.get_rect()), "label": _rect(label.get_rect())})

func _rect(rect: Rect2) -> Dictionary:
	return {"x": rect.position.x, "y": rect.position.y, "w": rect.size.x, "h": rect.size.y}

func _test_independent_drawer() -> void:
	var drawer: Control = DRAWER.new()
	drawer.close()
	drawer.close()
	_canvas_a.add_child(drawer)
	await _settle()
	_check("independent.preTree_close_stays_ignore", not drawer.visible and drawer.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	_canvas_a.remove_child(drawer)
	drawer.open()
	_check("independent.offtree_open_no_focus", drawer.visible and _view_a.gui_get_focus_owner() == null)
	drawer.close()
	_canvas_a.add_child(drawer)
	await _settle()
	var back: Button = drawer.get_back_button()
	back.disabled = true
	drawer.open()
	_check("independent.disabled_button_not_focused", not back.has_focus())
	back.disabled = false
	drawer.open(false)
	_check("independent.no_focus_option", not back.has_focus())
	drawer.open()
	_check("independent.enabled_visible_button_focus", back.has_focus())
	drawer.close()
	_check("independent.close_releases_focus", _view_a.gui_get_focus_owner() == null)
	drawer.free()

func _test_binding_visibility() -> void:
	_hud.set_drawer_open(false)
	var game := MockGame.new()
	var station := MockStation.new()
	var player := CharacterBody2D.new()
	var binding := BINDING.new()
	root.add_child(game)
	_view_b.add_child(player)
	_view_b.add_child(station)
	station.position = Vector2(300, 300)
	station.player = player
	root.add_child(binding)
	binding.set_process(false)
	binding.bind_sources(_hud, game, station)
	await _settle()
	_check("binding.same_viewport_marker_visible", _hud.get_marker().visible)
	_canvas_b.remove_child(_hud)
	binding.refresh()
	_check("binding.detached_hud_hides_marker", not _hud.get_marker().visible)
	_canvas_b.add_child(_hud)
	await _settle()
	binding.refresh()
	_check("binding.hud_readd_restores_marker", _hud.get_marker().visible)
	_view_b.remove_child(station)
	binding.refresh()
	_check("binding.detached_station_hides_marker", not _hud.get_marker().visible)
	_view_a.add_child(station)
	binding.refresh()
	_check("binding.cross_viewport_hides_marker", not _hud.get_marker().visible)
	_view_a.remove_child(station)
	_view_b.add_child(station)
	binding.refresh()
	_check("binding.same_viewport_readd_restores_marker", _hud.get_marker().visible and _hud.get_marker().position == Vector2(330, 248))
	binding.free()
	station.free()
	player.free()
	game.free()

func _hash_sources() -> Dictionary:
	var hashes: Dictionary = {}
	for path in SOURCES:
		hashes[path] = FileAccess.get_sha256(path).to_lower()
	return hashes
