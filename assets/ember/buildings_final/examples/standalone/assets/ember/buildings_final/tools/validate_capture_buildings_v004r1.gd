extends SceneTree
## 验证完整母图显示、门状态和真碰撞；截图来自实际 Godot 视口。
## 数值报告只证明实现，不能替代用户/技术美术对原图连续转角的审阅。

const DEMO := preload("res://assets/ember/buildings_final/scenes/demo.tscn")
const OUT := "res://assets/ember/buildings_final/textures/previews/"
var checks: Array[Dictionary] = []
var captures: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("_run")

func _check(name: String, result: bool) -> void:
	checks.append({"check": name, "pass": result})
	if not result: push_error(name)

func _settle() -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw

func _capture(filename: String, title: String, scene: Node2D) -> void:
	scene.title_label.text = title
	await _settle()
	var path := OUT + filename
	root.get_texture().get_image().save_png(path)
	captures.append({"path": path, "sha256": FileAccess.get_sha256(path), "kind": "ACTUAL_GODOT_GPU"})

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("此验收需要真实GPU视口")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	root.size = Vector2i(1408, 800)
	var scene = DEMO.instantiate()
	root.add_child(scene)
	scene.capture_mode = true
	scene.set_process(false)
	scene.actor.input_enabled = false
	scene.help_label.visible = false
	scene.status_label.visible = false
	scene.toast_label.visible = false
	_validate_coverage()
	await _verify_demo_ui(scene)
	for building in scene.buildings:
		building.set_process(false)
		_check(building.building_id + ": initialize", building.initialized && building.load_errors.is_empty())
		_check(building.building_id + ": one intact architecture", building.intact_sprite.scale.x == building.intact_sprite.scale.y)
		await _verify_identity(building)
	await _capture("gpu_intact_closed_v004r1.png", "v004r1 / INTACT ARCHITECTURE / CLOSED", scene)
	# 门前身体穿行使用实际CharacterBody2D测试，避免仅看disabled字段。
	for building in scene.buildings:
		for id: String in building.doors:
			var door: Dictionary = building.doors[id]
			var label: String = building.building_id + "/" + id
			var start: Vector2 = building.global_position + Vector2(door.center_x, 27)
			await physics_frame
			_check(label + ": closed blocks actor", scene.actor.test_move(Transform2D(0.0, start), Vector2(0, -42)))
			building.set_locked(id, true)
			_check(label + ": locked denies open", not building.request_door(id, true, Vector2.INF, true))
			building.set_locked(id, false)
			_check(label + ": open command", building.request_door(id, true, Vector2.INF, true))
			building.advance_state(building.motion_seconds * 0.5)
			await process_frame
			_check(label + ": half open retains collision", not door.collision.disabled)
			building.set_power(false)
			var paused: float = door.progress
			building.advance_state(1.0)
			_check(label + ": power loss freezes motion", is_equal_approx(paused, door.progress))
			building.set_power(true)
			building.advance_state(building.motion_seconds)
			await physics_frame
			await physics_frame
			_check(label + ": fully open clears actor path", not scene.actor.test_move(Transform2D(0.0, start), Vector2(0, -42)))
			building.set_actor_rects([Rect2(building.global_position + Vector2(door.center_x - 9, -6), Vector2(18, 12))])
			_check(label + ": occupied aperture refuses closing", not building.request_door(id, false, Vector2.INF, true))
			building.set_actor_rects([])
			building.request_door(id, false, Vector2.INF, true)
			building.advance_state(building.motion_seconds * 0.35)
			building.set_actor_rects([Rect2(building.global_position + Vector2(door.center_x - 9, -6), Vector2(18, 12))])
			building.advance_state(0.0)
			_check(label + ": closing reverses on occupant", door.target == 1.0 && door.obstructed)
			building.set_actor_rects([])
			building.advance_state(building.motion_seconds)
		building.set_interior_visible(false)
	await _capture("gpu_intact_open_v004r1.png", "v004r1 / OPEN DOORS / SAME FIXED CORNERS", scene)
	for building in scene.buildings:
		for id: String in building.doors:
			building.request_door(id, false, Vector2.INF, true)
		building.advance_state(building.motion_seconds * 0.5)
	await _capture("gpu_intact_half_v004r1.png", "v004r1 / HALF CLOSED / FIXED FRAMES", scene)
	# 回归此前读档顺序故障：保存门半关闭且人远离，读档前把人放在门口。
	scene.actor.position = Vector2(160, 660)
	scene.save_state("user://v004r1_validation_save.json")
	var saved: Dictionary = scene.buildings[0].snapshot()
	scene.actor.position = scene.buildings[0].position
	scene.buildings[0].set_actor_rects([scene.actor.ground_rect()])
	scene.load_state("user://v004r1_validation_save.json")
	_check("save load restores player before safety probe", scene.actor.position == Vector2(160, 660))
	_check("save load preserves closing target", scene.buildings[0].doors.personnel.target == saved.doors.personnel.target)
	_check("save load preserves partial progress", is_equal_approx(scene.buildings[0].doors.personnel.progress, saved.doors.personnel.progress))
	for building in scene.buildings:
		building.set_fault(true)
		if building.definition.has("service_rect"):
			_check(building.building_id + ": cover required for repair", not building.repair_device(Vector2.INF, true))
			_check(building.building_id + ": maintenance opens", building.toggle_maintenance(Vector2.INF, true))
		_check(building.building_id + ": repair clears fault", building.repair_device(Vector2.INF, true) && not building.faulted)
		building.set_roof_hatch_inspection(true)
		building.set_glass_lit(true)
	await _capture("gpu_intact_service_v004r1.png", "v004r1 / MAINTENANCE + TOWER HATCH / INSPECTION", scene)
	for building in scene.buildings:
		building.set_power(false)
	await _capture("gpu_intact_power_off_v004r1.png", "v004r1 / POWER OFF / MOTION FROZEN", scene)
	for building in scene.buildings:
		building.set_power(true)
		building.set_interior_visible(true)
		_check(building.building_id + ": whole shell occlusion", is_equal_approx(building.intact_sprite.modulate.a, 0.14))
	await _capture("gpu_intact_occlusion_v004r1.png", "v004r1 / WHOLE SHELL FADES ON ENTRY", scene)
	await _reference_board()
	await _capture_coverage_edges()
	var passed := 0
	for entry: Dictionary in checks:
		if entry.pass: passed += 1
	var report := {"checks": checks, "passed": passed, "total": checks.size(), "captures": captures,
		"visual_acceptance": "PENDING_USER_AND_TA_REVIEW", "renderer": RenderingServer.get_video_adapter_name()}
	var output := FileAccess.open(OUT + "validation_v004r1.json", FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "\t"))
	print("INTACT_BUILDING_VALIDATION ", passed, "/", checks.size())
	quit(0 if passed == checks.size() else 1)

func _verify_identity(building: Node2D) -> void:
	# 相同视口/变换下，生产Shader关闭状态必须逐字节等于纯Sprite2D。
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1254, 1254)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var test_sprite := Sprite2D.new()
	test_sprite.texture = building.intact_sprite.texture
	test_sprite.centered = false
	test_sprite.material = building.intact_material
	test_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	viewport.add_child(test_sprite)
	await _settle()
	var actual := viewport.get_texture().get_image().get_data()
	test_sprite.material = null
	await _settle()
	var expected := viewport.get_texture().get_image().get_data()
	_check(building.building_id + ": closed shader equals complete master render", actual == expected)
	# 可选拆件也要实际复合一次。功能区域互不重叠，不能靠两层半透明描边遮缝。
	test_sprite.visible = false
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ember/buildings_final/textures/functional_layers_v004r1.json"))
	var split_sprites: Array[Sprite2D] = []
	for entry: Dictionary in manifest.buildings:
		if entry.building_id != building.building_id: continue
		var paths: Array[String] = [entry.fixed_architecture]
		for layer: Dictionary in entry.layers: paths.append(layer.texture)
		for path: String in paths:
			var split := Sprite2D.new()
			split.texture = load(path) as Texture2D
			split.centered = false
			split.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			viewport.add_child(split)
			split_sprites.append(split)
	await _settle()
	_check(building.building_id + ": exported layers reassemble identical master render", viewport.get_texture().get_image().get_data() == expected)
	for split: Sprite2D in split_sprites: split.queue_free()
	test_sprite.visible = true
	# 真实绘制变化不得越过活动区域，屋顶/檐口转角全画布一起覆盖。
	test_sprite.material = building.intact_material
	for id: String in building.doors: building.doors[id].progress = 0.5
	building.advance_state(0.0)
	await _settle()
	var opened := viewport.get_texture().get_image()
	var closed := Image.create_from_data(1254, 1254, false, opened.get_format(), expected)
	var changed_outside := 0
	var changed_inside := 0
	for y: int in 1254:
		for x: int in 1254:
			if opened.get_pixel(x, y) == closed.get_pixel(x, y): continue
			var allowed := false
			for spec: Dictionary in building.definition.doors:
				var r: Array = spec.source_rect_px
				if Rect2i(r[0], r[1], r[2], r[3]).has_point(Vector2i(x, y)): allowed = true
			# 运动指示灯也可改变；所有其他像素（包括每一处圆角）必须不变。
			for r: Array in building.definition.lens_rects:
				if Rect2i(r[0], r[1], r[2], r[3]).has_point(Vector2i(x, y)): allowed = true
			if allowed: changed_inside += 1
			else: changed_outside += 1
	_check(building.building_id + ": moving doors do not change any fixed pixel", changed_outside == 0 && changed_inside > 0)
	for id: String in building.doors: building.doors[id].progress = 0.0
	building.advance_state(0.0)
	viewport.queue_free()
	await process_frame

func _validate_coverage() -> void:
	var path := "res://assets/ember/buildings_final/textures/"
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path + "catalog_v004r1.json"))
	var previous: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ember/buildings_final/source/building-assets-v004/registration_baseline_v004.json"))
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path + "functional_layers_v004r1.json"))
	for b: Dictionary in catalog.buildings:
		var source := Image.load_from_file(ProjectSettings.globalize_path(b.source_master))
		source.convert(Image.FORMAT_RGBA8)
		var raw := source.get_data()
		var production := Image.load_from_file(ProjectSettings.globalize_path(b.complete_texture))
		production.convert(Image.FORMAT_RGBA8)
		var pixels := production.get_data()
		var mask := Image.load_from_file(ProjectSettings.globalize_path(b.coverage_mask))
		mask.convert(Image.FORMAT_RGBA8)
		var coverage := mask.get_data()
		var coverage_errors := 0
		var color_errors := 0
		for i: int in range(0, pixels.size(), 4):
			var expected_alpha := 255 if raw[i + 3] >= 128 else 0
			if pixels[i + 3] != expected_alpha or coverage[i + 3] != expected_alpha: coverage_errors += 1
			for channel: int in 3:
				var expected_color: int = raw[i + channel] if expected_alpha == 255 else 0
				if pixels[i + channel] != expected_color: color_errors += 1
		_check(String(b.id) + ": production and mask have exact shared binary coverage", coverage_errors == 0)
		_check(String(b.id) + ": coverage keeps source RGB without geometry edits", color_errors == 0)
		_check(String(b.id) + ": original master file unchanged", FileAccess.get_sha256(b.source_master) == b.source_master_sha256)
		for old: Dictionary in previous.buildings:
			if old.id == b.id:
				_check(String(b.id) + ": registration and apertures unchanged", old.uniform_scale == b.uniform_scale && old.source_pivot_px == b.source_pivot_px && old.footprint_px == b.footprint_px && old.doors == b.doors)
		for entry: Dictionary in manifest.buildings:
			if entry.building_id != b.id: continue
			var parts: Array[String] = [entry.fixed_architecture]
			for layer: Dictionary in entry.layers: parts.append(layer.texture)
			for texture_path: String in parts:
				var part := Image.load_from_file(ProjectSettings.globalize_path(texture_path))
				part.convert(Image.FORMAT_RGBA8)
				var data := part.get_data()
				var wrong := false
				for i: int in range(3, data.size(), 4):
					if data[i] != 0 and data[i] != 255:
						wrong = true
						break
				_check(String(b.id) + ": binary functional PNG " + texture_path.get_file(), not wrong)

func _verify_demo_ui(scene: Node2D) -> void:
	# 通过实际按键分发触发锁门反馈，确认提示确实显示在当前800高视口内。
	scene.capture_mode = false
	scene.set_process(true)
	scene.help_label.visible = true
	scene.status_label.visible = true
	var building = scene.buildings[0]
	building.set_locked("personnel", true)
	scene.actor.position = building.position + Vector2(building.doors.personnel.center_x, 34)
	var key := InputEventKey.new()
	key.pressed = true
	key.physical_keycode = KEY_E
	scene._unhandled_key_input(key)
	await _settle()
	_check("demo real E input displays locked-door feedback", scene.toast_label.visible && scene.toast_label.text == "门已锁定")
	var view := scene.get_viewport_rect()
	var controls: Array[Control] = [scene.help_label, scene.toast_label, scene.status_label]
	for label: Label in scene.building_labels: controls.append(label)
	for index: int in controls.size():
		_check("demo UI visible in viewport " + str(index), controls[index].is_visible_in_tree() && view.encloses(controls[index].get_global_rect()))
	await _capture("gpu_demo_ui_v004r1.png", "v004r1 / INTERACTIVE DEMO / VISIBLE CONTROLS", scene)
	building.set_locked("personnel", false)
	scene.actor.position = Vector2(160, 650)
	scene.capture_mode = true
	scene.set_process(false)
	scene.help_label.visible = false
	scene.status_label.visible = false
	scene.toast_label.visible = false
	for label: Label in scene.building_labels: label.visible = false
	for item in scene.buildings:
		item.set_process(false)
		item.set_actor_rects([])

func _capture_coverage_edges() -> void:
	var ids := ["control_tower", "repair_workshop", "logistics_warehouse"]
	var boxes := [[Vector2(274, 467), Vector2(868, 467)], [Vector2(66, 627), Vector2(1057, 627)], [Vector2(87, 604), Vector2(1039, 604)]]
	for index: int in 3:
		var viewport := SubViewport.new()
		viewport.size = Vector2i(2144, 1192)
		viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(viewport)
		for row: int in 2:
			for col: int in 4:
				var origin := Vector2(16 + col * 532, 48 + row * 584)
				var panel := ColorRect.new()
				panel.color = Color("17212a") if col < 2 else Color("e6e2d6")
				panel.position = origin
				panel.size = Vector2(512, 512)
				viewport.add_child(panel)
				var path: String = "res://assets/ember/buildings_final/source/building-assets-v004/masters/" + ids[index] + "_intact_v004.png" if col % 2 == 0 else "res://assets/ember/buildings_final/textures/complete/" + ids[index] + "_closed_v004r1.png"
				var sprite := Sprite2D.new()
				sprite.texture = load(path)
				sprite.centered = false
				sprite.region_enabled = true
				sprite.region_rect = Rect2(boxes[index][row], Vector2(128, 128))
				sprite.position = origin
				sprite.scale = Vector2(4, 4)
				sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
				viewport.add_child(sprite)
				var label := Label.new()
				label.text = ("RAW MASTER" if col % 2 == 0 else "PRODUCTION COVERAGE") + (" / LEFT" if row == 0 else " / RIGHT") + " / 4X"
				label.position = origin - Vector2(0, 28)
				viewport.add_child(label)
		await _settle()
		var filename: String = OUT + ids[index] + "_coverage_edges_4x_v004r1.png"
		viewport.get_texture().get_image().save_png(filename)
		captures.append({"path": filename, "sha256": FileAccess.get_sha256(filename), "kind": "ACTUAL_GPU_DARK_LIGHT_SOURCE_VS_COVERAGE_4X"})
		viewport.queue_free()
	await process_frame

func _reference_board() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1500, 1120)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var bg := ColorRect.new()
	bg.color = Color("415766")
	bg.size = Vector2(1500, 1120)
	viewport.add_child(bg)
	var ids := ["control_tower", "repair_workshop", "logistics_warehouse"]
	# 边界来自最初完整图和新透明母图，仅用于对照版式等比缩放。
	var original_bounds := [Rect2(344, 163, 565, 830), Rect2(132, 268, 994, 605), Rect2(90, 274, 1080, 642)]
	var master_bounds := [Rect2(270, 104, 730, 1050), Rect2(66, 298, 1126, 681), Rect2(87, 272, 1087, 635)]
	for row: int in 2:
		for col: int in 3:
			var source: String = "res://assets/ember/buildings_final/source/selected-buildings-v001/references/" + ids[col] + "_user_selected.png" if row == 0 else "res://assets/ember/buildings_final/textures/complete/" + ids[col] + "_closed_v004r1.png"
			var box: Rect2 = original_bounds[col] if row == 0 else master_bounds[col]
			var sprite := Sprite2D.new()
			sprite.texture = load(source)
			sprite.centered = false
			sprite.region_enabled = true
			sprite.region_rect = box
			var scale_value := minf(454.0 / box.size.x, 464.0 / box.size.y)
			sprite.scale = Vector2.ONE * scale_value
			sprite.position = Vector2(col * 500 + (500 - box.size.x * scale_value) * 0.5, row * 550 + 70 + (464 - box.size.y * scale_value))
			sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			viewport.add_child(sprite)
			var label := Label.new()
			label.text = ("ORIGINAL / " if row == 0 else "v004r1 INTACT / ") + ids[col]
			label.position = Vector2(col * 500 + 24, row * 550 + 28)
			viewport.add_child(label)
	await _settle()
	var path := OUT + "gpu_original_vs_intact_v004r1.png"
	viewport.get_texture().get_image().save_png(path)
	captures.append({"path": path, "sha256": FileAccess.get_sha256(path), "kind": "REFERENCE_VS_ACTUAL_INTACT_RENDER"})
	viewport.queue_free()
