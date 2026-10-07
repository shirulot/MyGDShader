extends SceneTree
## 将已通过原生/视觉验收的40资产整理成可复用资源与独立预览。
## 导入PNG后运行 --headless --path . --script res://tools/build_ember_asset_library.gd --
## --verify-only 保留资源和场景；--rebuild-sandbox 才重建已有示例。
## --screenshots=绝对目录 使用真实渲染截图；不在headless模式截取图像。
## 纹理与材质示例不代表技术Mask/Normal或课程Shader已完成。

const CATALOG := "res://assets/ember/ember_additional_catalog_v001.json"
const SCENE := "res://scenes/ember/asset_library_sandbox.tscn"
const REPORT := "res://art-source/ember/full-art-v001/godot-validation-v001.json"
const VIEW_SIZE := Vector2i(1440, 1040)
const RESOURCES := {
	"panel": "res://assets/ember/ui/panels/panel_style_v001.tres",
	"screen": "res://assets/ember/buildings/terminal/screen_style_v001.tres",
	"door": "res://assets/ember/buildings/door/door_states_v001.tres",
	"grass": "res://assets/ember/three_d/materials/grass_leaf_v001.tres",
	"metal": "res://assets/ember/three_d/materials/metal_v001.tres",
	"concrete": "res://assets/ember/three_d/materials/concrete_v001.tres",
}

var _assets: Array = []
var _by_id: Dictionary = {}
var _errors: PackedStringArray = []
var _verify_only := false
var _rebuild := false
var _screenshots := ""
var _report := REPORT

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument == "--verify-only": _verify_only = true
		elif argument == "--rebuild-sandbox": _rebuild = true
		elif argument.begins_with("--screenshots="): _screenshots = argument.trim_prefix("--screenshots=")
		elif argument.begins_with("--report="): _report = argument.trim_prefix("--report=")
		else: _errors.append("不支持参数：" + argument)
	var file := FileAccess.open(CATALOG, FileAccess.READ)
	if file == null:
		_errors.append("缺少已验收的40资产生产目录")
	else:
		var parsed: Variant = JSON.parse_string(file.get_as_text())
		if not parsed is Dictionary or not parsed.get("assets") is Array:
			_errors.append("目录格式不正确")
		else:
			_assets = parsed["assets"]
			if str(parsed.get("status", "")).contains("PLANNED") or _assets.size() != 40:
				_errors.append("必须是已验收40项，而不是规划目录")
			_validate_inputs()
	if _errors.is_empty() and not _verify_only:
		_build_resources()
		if _errors.is_empty() and (_rebuild or not FileAccess.file_exists(SCENE)):
			_build_scene()
	if _errors.is_empty():
		_verify_resources()
	if _errors.is_empty():
		await _verify_scene_and_render()
	var report := {"status": "GODOT_ADDITIONAL_40_VALIDATED" if _errors.is_empty() else "GODOT_ADDITIONAL_40_FAILED",
		"engine": Engine.get_version_info(), "asset_count": _assets.size(), "resource_count": RESOURCES.size(),
		"scene": SCENE, "verify_only": _verify_only, "screenshots": _screenshots,
		"errors": Array(_errors), "timestamp_utc": Time.get_datetime_string_from_system(true)}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(_report.get_base_dir()))
	var output := FileAccess.open(_report, FileAccess.WRITE)
	if output != null: output.store_string(JSON.stringify(report, "\t") + "\n")
	else: _errors.append("报告保存失败")
	for error in _errors: push_error(error)
	print(JSON.stringify(report))
	quit(0 if _errors.is_empty() else 1)

func _validate_inputs() -> void:
	for asset: Dictionary in _assets:
		var identifier := str(asset["id"])
		var path := str(asset["file"])
		if _by_id.has(identifier): _errors.append("ID重复：" + identifier)
		_by_id[identifier] = asset
		if not path.begins_with("res://assets/ember/") or not FileAccess.file_exists(path):
			_errors.append("正式PNG不存在：" + identifier)
			continue
		if FileAccess.get_sha256(path) != str(asset["sha256"]): _errors.append("PNG版本已变：" + identifier)
		# 验收工具读PNG字节，避免把生产纹理按未导入Image资源加载的警告。
		var image := Image.new()
		var image_error := image.load_png_from_buffer(FileAccess.get_file_as_bytes(path))
		var canvas: Array = asset["canvas"]
		if image_error != OK or image.get_size() != Vector2i(int(canvas[0]), int(canvas[1])):
			_errors.append("画布不符：" + identifier)
		var texture := ResourceLoader.load(path) as Texture2D
		if texture == null:
			_errors.append("纹理未实际导入：" + identifier)
		else:
			if texture.get_size() != Vector2(int(canvas[0]), int(canvas[1])): _errors.append("导入后尺寸不符：" + identifier)
			var expects_mips := str(asset["manifest_id"]).begins_with("X")
			if texture.get_image().has_mipmaps() != expects_mips: _errors.append("实际Mipmaps策略不符：" + identifier)
			var import_config := ConfigFile.new()
			if import_config.load(path + ".import") != OK or import_config.get_value("params", "compress/mode", -1) != 0:
				_errors.append("实际Lossless导入设置不符：" + identifier)

func _texture(identifier: String) -> Texture2D:
	return load(str(_by_id[identifier]["file"])) as Texture2D

func _save(resource: Resource, path: String) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
	if ResourceSaver.save(resource, path) != OK: _errors.append("资源保存失败：" + path)

func _build_resources() -> void:
	var panel := StyleBoxTexture.new()
	panel.texture = _texture("panel_9slice")
	panel.set_texture_margin_all(8)
	_save(panel, RESOURCES["panel"])
	var screen := StyleBoxTexture.new()
	screen.texture = _texture("screen_frame")
	var region: Array = _by_id["screen_frame"].get("slice_region", [16, 16, 64, 64])
	screen.region_rect = Rect2(region[0], region[1], region[2], region[3])
	screen.set_texture_margin_all(8)
	screen.draw_center = false
	_save(screen, RESOURCES["screen"])
	var door := SpriteFrames.new()
	door.remove_animation("default")
	for state in ["closed", "open"]:
		door.add_animation(state)
		door.set_animation_speed(state, 1.0)
		door.add_frame(state, _texture("door_" + state))
	_save(door, RESOURCES["door"])
	# PBR常量仅作复用起点；没有伪造D11法线/粗糙度贴图。
	for entry in [["grass", "grass_leaf"], ["metal", "metal_albedo"], ["concrete", "concrete_albedo"]]:
		var material := StandardMaterial3D.new()
		material.albedo_texture = _texture(entry[1])
		material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS
		material.texture_repeat = entry[0] != "grass"
		material.roughness = 0.65 if entry[0] == "metal" else 1.0
		material.metallic = 0.55 if entry[0] == "metal" else 0.0
		if entry[0] == "grass":
			material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			material.alpha_scissor_threshold = 0.5
			material.cull_mode = BaseMaterial3D.CULL_DISABLED
		_save(material, RESOURCES[entry[0]])

func _attach(parent: Node, child: Node, owner_node: Node) -> void:
	parent.add_child(child)
	child.owner = owner_node

func _label(parent: Node, text: String, at: Vector2, owner_node: Node, font_size: int = 18) -> void:
	var label := Label.new()
	label.text = text
	label.position = at
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", Color("becbc4"))
	_attach(parent, label, owner_node)

func _sprite(parent: Node, asset: Dictionary, at: Vector2, owner_node: Node, scale_factor: float = 1.0) -> void:
	var sprite := Sprite2D.new()
	sprite.name = str(asset["id"])
	sprite.texture = _texture(asset["id"])
	sprite.position = at
	sprite.scale = Vector2.ONE * scale_factor
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_attach(parent, sprite, owner_node)

func _build_scene() -> void:
	var scene := Control.new()
	scene.name = "EmberAssetLibrary"
	scene.size = VIEW_SIZE
	scene.set_script(load("res://scenes/ember/asset_library_sandbox.gd"))
	var backdrop := ColorRect.new()
	backdrop.color = Color("101820")
	backdrop.size = VIEW_SIZE
	_attach(scene, backdrop, scene)
	_label(scene, "余烬采能站 · 可复用素材库", Vector2(24, 12), scene, 26)
	_label(scene, "原生图片、门状态、九宫格与3D材质预览", Vector2(24, 44), scene)
	var tabs := TabContainer.new()
	tabs.name = "LibraryTabs"
	tabs.position = Vector2(16, 80)
	tabs.size = Vector2(1408, 936)
	tabs.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_attach(scene, tabs, scene)
	var pages: Dictionary = {}
	for title in ["建筑与道具", "UI与九宫格", "特效与纹理", "3D材质"]:
		var page := Control.new()
		page.name = title
		_attach(tabs, page, scene)
		pages[title] = page
	var object_index := 0
	var ui_index := 0
	var texture_index := 0
	for asset: Dictionary in _assets:
		var category := str(asset["manifest_id"])
		if category.begins_with("B"):
			var at := Vector2(110 + (object_index % 6) * 230, 130 + (object_index / 6) * 290)
			_sprite(pages["建筑与道具"], asset, at, scene)
			_label(pages["建筑与道具"], str(asset.get("label", asset["id"])), at + Vector2(-102, 132), scene, 15)
			object_index += 1
		elif category.begins_with("U"):
			if asset["id"] == "panel_9slice": continue
			var at := Vector2(90 + (ui_index % 7) * 194, 78 + (ui_index / 7) * 170)
			_sprite(pages["UI与九宫格"], asset, at, scene, 2.0)
			_label(pages["UI与九宫格"], str(asset.get("label", asset["id"])), at + Vector2(-75, 42), scene, 16)
			ui_index += 1
		else:
			var at := Vector2(168 + (texture_index % 4) * 346, 160 + (texture_index / 4) * 340)
			_sprite(pages["特效与纹理"], asset, at, scene)
			_label(pages["特效与纹理"], str(asset.get("label", asset["id"])), at + Vector2(-150, 132), scene, 16)
			texture_index += 1
	for rectangle in [Rect2(28, 390, 192, 96), Rect2(258, 390, 400, 180), Rect2(710, 390, 600, 300)]:
		var panel := Panel.new()
		panel.position = rectangle.position
		panel.size = rectangle.size
		panel.add_theme_stylebox_override("panel", load(RESOURCES["panel"]))
		_attach(pages["UI与九宫格"], panel, scene)
	_label(pages["UI与九宫格"], "面板九宫格：三种尺寸；固定8px边角", Vector2(30, 728), scene)
	var screen := Panel.new()
	screen.position = Vector2(48, 774)
	screen.size = Vector2(640, 96)
	screen.add_theme_stylebox_override("panel", load(RESOURCES["screen"]))
	_attach(pages["UI与九宫格"], screen, scene)
	_build_3d_preview(pages["3D材质"], scene)
	var packed := PackedScene.new()
	if packed.pack(scene) != OK: _errors.append("场景打包失败")
	else: _save(packed, SCENE)
	scene.free()

func _build_3d_preview(page: Control, owner_node: Node) -> void:
	var container := SubViewportContainer.new()
	container.position = Vector2(0, 0)
	container.size = Vector2(1400, 880)
	_attach(page, container, owner_node)
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1400, 880)
	viewport.own_world_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_attach(container, viewport, owner_node)
	var world := Node3D.new()
	_attach(viewport, world, owner_node)
	var environment_node := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("182631")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("becbc4")
	environment.ambient_light_energy = 0.8
	environment_node.environment = environment
	_attach(world, environment_node, owner_node)
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-48, -35, 0)
	_attach(world, light, owner_node)
	for index in range(2):
		var surface := MeshInstance3D.new()
		var plane := PlaneMesh.new()
		plane.size = Vector2(2.6, 3.0)
		surface.mesh = plane
		surface.position = Vector3(-1.7 if index == 0 else 1.7, 0, 0)
		surface.material_override = load(RESOURCES["metal" if index == 0 else "concrete"])
		_attach(world, surface, owner_node)
	for index in range(3):
		var leaf := MeshInstance3D.new()
		var quad := QuadMesh.new()
		quad.size = Vector2(0.75, 1.5)
		leaf.mesh = quad
		# 根部位于PNG的y120边界，底部8px透明留白不应把草根抬离地面。
		leaf.position = Vector3(-2.0 + index * 2.0, 1.5 * (120.0 / 128.0 - 0.5), 1.2)
		leaf.material_override = load(RESOURCES["grass"])
		_attach(world, leaf, owner_node)
	var camera := Camera3D.new()
	camera.name = "PreviewCamera"
	camera.position = Vector3(0, 4.5, 6)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 7.0
	_attach(world, camera, owner_node)
	camera.look_at_from_position(camera.position, Vector3(0, 0.5, 0), Vector3.UP)
	_label(page, "金属 / 混凝土与草片：标准材质、Alpha Scissor、Mipmaps；未制作Normal贴图或风摆Shader", Vector2(24, 850), owner_node, 17)

func _verify_resources() -> void:
	for key in RESOURCES:
		if ResourceLoader.load(RESOURCES[key], "", ResourceLoader.CACHE_MODE_REPLACE) == null:
			_errors.append("保存后重载失败：" + key)
	var panel := load(RESOURCES["panel"]) as StyleBoxTexture
	if panel == null or panel.texture != _texture("panel_9slice"):
		_errors.append("panel九宫格不符")
	var screen := load(RESOURCES["screen"]) as StyleBoxTexture
	if screen == null or screen.draw_center or screen.region_rect != Rect2(16, 16, 64, 64):
		_errors.append("screen frame区域/透明中心不符")
	for style in [panel, screen]:
		if style == null: continue
		for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
			if style.get_texture_margin(side) != 8: _errors.append("九宫格四边必须各8px")
	var door := load(RESOURCES["door"]) as SpriteFrames
	if door == null: return
	for state in ["closed", "open"]:
		if door.get_frame_count(state) != 1 or door.get_frame_texture(state, 0) != _texture("door_" + state):
			_errors.append("门状态重载不符：" + state)
	for entry in [["grass", "grass_leaf"], ["metal", "metal_albedo"], ["concrete", "concrete_albedo"]]:
		var material := load(RESOURCES[entry[0]]) as StandardMaterial3D
		if material == null or material.albedo_texture != _texture(entry[1]) or material.texture_filter != BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS:
			_errors.append("3D材质不符：" + entry[0])
		elif not material.albedo_texture.get_image().has_mipmaps():
			_errors.append("3D纹理缺实际mipmaps：" + entry[0])
		if material != null:
			if material.texture_repeat != (entry[0] != "grass"): _errors.append("3D纹理重复设置不符：" + entry[0])
			if entry[0] == "grass" and (material.transparency != BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR or material.alpha_scissor_threshold != 0.5 or material.cull_mode != BaseMaterial3D.CULL_DISABLED):
				_errors.append("草片透明裁切/双面设置不符")

func _verify_scene_and_render() -> void:
	var packed := load(SCENE) as PackedScene
	if packed == null:
		_errors.append("缺独立素材库场景")
		return
	var scene := packed.instantiate()
	root.add_child(scene)
	await process_frame
	var tabs := scene.get_node_or_null("LibraryTabs") as TabContainer
	if tabs == null or tabs.get_tab_count() != 4: _errors.append("四个素材页未实际加载")
	if not _screenshots.is_empty() and _errors.is_empty():
		if DisplayServer.get_name() == "headless": _errors.append("截图必须实际渲染")
		else:
			DirAccess.make_dir_recursive_absolute(_screenshots)
			root.size = VIEW_SIZE
			root.content_scale_size = VIEW_SIZE
			for index in range(4):
				tabs.current_tab = index
				await process_frame
				await RenderingServer.frame_post_draw
				var path := _screenshots.path_join("library_page_%02d.png" % index)
				if root.get_texture().get_image().save_png(path) != OK: _errors.append("截图保存失败：" + path)
			# 同一实际3D场景切换观察距离，核对mipmaps下叶缘与底色；不修改保存场景。
			var camera := scene.find_child("PreviewCamera", true, false) as Camera3D
			if camera == null:
				_errors.append("3D观察相机缺失")
			else:
				for view in [["near", 4.0], ["far", 14.0]]:
					camera.size = view[1]
					await process_frame
					await RenderingServer.frame_post_draw
					var path := _screenshots.path_join("materials_%s.png" % view[0])
					if root.get_texture().get_image().save_png(path) != OK: _errors.append("近远材质截图保存失败：" + path)
				camera.size = 7.0
	root.remove_child(scene)
	scene.free()
