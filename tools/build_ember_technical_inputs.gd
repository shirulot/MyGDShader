extends SceneTree
## 技术输入的可复用资源与只读验收。这里只使用 Godot 内置材质，不提供课程 Shader 答案。
## 导入 PNG 后运行：--headless --path . --script res://tools/build_ember_technical_inputs.gd --
## --verify-only 保留已保存资源；--screenshots=绝对目录 启用真实 GPU 截图和法线方向检查。

const CATALOG := "res://assets/ember/data/technical_inputs_catalog_v001.json"
const SCENE := "res://scenes/ember/technical_inputs_sandbox.tscn"
const SIZE := Vector2i(1440, 1040)
const RESOURCES := {
	"station": "res://assets/ember/data/normals/station_canvas_texture_v001.tres",
	"console": "res://assets/ember/data/normals/console_canvas_texture_v001.tres",
	"floor_clean": "res://assets/ember/data/normals/floor_clean_canvas_texture_v001.tres",
	"metal": "res://assets/ember/three_d/materials/metal_technical_v001.tres",
	"concrete": "res://assets/ember/three_d/materials/concrete_technical_v001.tres",
}

var _assets: Array = []
var _by_id: Dictionary = {}
var _errors: PackedStringArray = []
var _readback: Array = []
var _light_checks: Array = []
var _light_diagnostics: Dictionary = {}
var _verify_only := false
var _rebuild := false
var _screenshots := ""
var _report := "res://art-source/ember/technical-inputs-v001/godot-validation.json"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument == "--verify-only": _verify_only = true
		elif argument == "--rebuild-sandbox": _rebuild = true
		elif argument.begins_with("--screenshots="): _screenshots = argument.trim_prefix("--screenshots=")
		elif argument.begins_with("--report="): _report = argument.trim_prefix("--report=")
		else: _errors.append("不支持参数：" + argument)
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
	if not parsed is Dictionary or not parsed.get("assets") is Array:
		_errors.append("缺少技术输入目录")
	else:
		_assets = parsed["assets"]
		if _assets.size() != 40: _errors.append("需要40个实际技术输入")
		_validate_inputs()
	if _errors.is_empty() and not _verify_only:
		_build_resources()
		if _rebuild or not FileAccess.file_exists(SCENE): _build_scene()
	if _errors.is_empty(): _verify_resources()
	if _errors.is_empty(): await _verify_scene()
	var result := {"status": "GODOT_TECHNICAL_40_PASS" if _errors.is_empty() else "GODOT_TECHNICAL_40_FAILED",
		"catalog_sha256": FileAccess.get_sha256(CATALOG),
		"engine": Engine.get_version_info(), "asset_count": _assets.size(), "resource_count": RESOURCES.size(),
		"scene": SCENE, "verify_only": _verify_only, "screenshots": _screenshots,
		"import_readback": _readback, "gpu_light_checks": _light_checks, "errors": Array(_errors)}
	result["light_diagnostics"] = _light_diagnostics
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(_report.get_base_dir()))
	var output := FileAccess.open(_report, FileAccess.WRITE)
	if output != null: output.store_string(JSON.stringify(result, "\t") + "\n")
	else: _errors.append("报告保存失败")
	for error in _errors: push_error(error)
	print(JSON.stringify(result))
	quit(0 if _errors.is_empty() else 1)

func _validate_inputs() -> void:
	for asset: Dictionary in _assets:
		var identifier := str(asset["id"])
		var path := str(asset["file"])
		if _by_id.has(identifier): _errors.append("ID重复：" + identifier)
		_by_id[identifier] = asset
		if FileAccess.get_sha256(path) != str(asset["sha256"]): _errors.append("PNG版本不符：" + identifier)
		var source := Image.new()
		if source.load_png_from_buffer(FileAccess.get_file_as_bytes(path)) != OK:
			_errors.append("PNG读取失败：" + identifier)
			continue
		var canvas: Array = asset["canvas"]
		if source.get_size() != Vector2i(int(canvas[0]), int(canvas[1])): _errors.append("尺寸不符：" + identifier)
		var texture := load(path) as Texture2D
		if texture == null:
			_errors.append("未实际导入：" + identifier)
			continue
		var imported := texture.get_image()
		var expects_mips := str(asset["manifest_id"]) in ["D11", "D12"]
		if imported.has_mipmaps() != expects_mips: _errors.append("Mipmaps不符：" + identifier)
		var config := ConfigFile.new()
		var import_values: Dictionary = {}
		if config.load(path + ".import") != OK:
			_errors.append("缺导入配置：" + identifier)
		else:
			# 0 并非所有选项的 Disabled；法线 Detect 会自动丢弃 B 通道。
			var expected_values := {"compress/mode": 0, "compress/normal_map": 2, "roughness/mode": 1, "detect_3d/compress_to": 0}
			for option: String in expected_values:
				import_values[option] = int(config.get_value("params", option, -1))
				if import_values[option] != expected_values[option]: _errors.append("导入转换不符：" + identifier + "/" + option)
			for option in ["process/fix_alpha_border", "process/premult_alpha", "process/normal_map_invert_y"]:
				if bool(config.get_value("params", option, true)): _errors.append("数据不应被导入器变换：" + identifier + "/" + option)
		# 比较每个原生像素，包括透明像素RGB。单通道PNG按.r读取，并保留L的复制通道语义。
		var mismatches := 0
		for y in source.get_height():
			for x in source.get_width():
				var a := source.get_pixel(x, y)
				var b := imported.get_pixel(x, y)
				if maxf(maxf(absf(a.r-b.r), absf(a.g-b.g)), maxf(absf(a.b-b.b), absf(a.a-b.a))) > 0.001:
					mismatches += 1
		_readback.append({"id": identifier, "pixels": source.get_width()*source.get_height(), "mismatched_pixels": mismatches, "mipmaps": expects_mips, "import_values": import_values})
		if mismatches != 0: _errors.append("导入像素发生改变：" + identifier)

func _tex(identifier: String) -> Texture2D:
	return load(str(_by_id[identifier]["file"])) as Texture2D

func _save(resource: Resource, path: String) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
	if ResourceSaver.save(resource, path) != OK: _errors.append("保存失败：" + path)

func _floor_diffuse() -> ImageTexture:
	# CanvasTexture槽内的AtlasTexture存在区域采样限制（Godot #67936）。
	# 把已验收atlas的实际32px区域嵌入资源，不新增/重画正式PNG，也不采样整张图集。
	var atlas := Image.new()
	atlas.load_png_from_buffer(FileAccess.get_file_as_bytes("res://assets/ember/environment/tilesets/ground_details_v001.png"))
	return ImageTexture.create_from_image(atlas.get_region(Rect2i(0, 0, 32, 32)))

func _build_resources() -> void:
	for identifier in ["station", "console", "floor_clean"]:
		var texture := CanvasTexture.new()
		texture.diffuse_texture = _floor_diffuse() if identifier == "floor_clean" else load("res://assets/ember/buildings/%s/%s_base_v001.png" % [identifier, identifier])
		texture.normal_texture = _tex(identifier + "_normal")
		texture.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		texture.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED if identifier == "floor_clean" else CanvasItem.TEXTURE_REPEAT_DISABLED
		_save(texture, RESOURCES[identifier])
	for identifier in ["metal", "concrete"]:
		var material := StandardMaterial3D.new()
		material.albedo_texture = load("res://assets/ember/three_d/textures/%s/%s_albedo_v001.png" % [identifier, identifier])
		material.normal_enabled = true
		material.normal_texture = _tex(identifier + "_normal")
		material.normal_scale = 1.0
		material.roughness_texture = _tex(identifier + "_roughness")
		material.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
		# 参数纹理含最终标量，因此乘数设1，而非再乘旧材质的.55/.65。
		material.roughness = 1.0
		material.metallic_texture = _tex(identifier + "_metallic")
		material.metallic_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
		material.metallic = 1.0
		material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS
		material.texture_repeat = true
		_save(material, RESOURCES[identifier])

func _attach(parent: Node, child: Node, owner_node: Node) -> void:
	parent.add_child(child)
	child.owner = owner_node

func _label(parent: Node, words: String, at: Vector2, owner_node: Node, font_size: int = 16) -> void:
	var label := Label.new()
	label.material = _unshaded()
	label.text = words
	label.position = at
	label.add_theme_font_size_override("font_size", font_size)
	_attach(parent, label, owner_node)

func _preview(parent: Node, texture: Texture2D, rectangle: Rect2, owner_node: Node) -> void:
	var display := TextureRect.new()
	display.material = _unshaded()
	# 先解除纹理的最小尺寸约束，再设目标矩形；否则512px输入会撑开卡片。
	display.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	display.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	display.texture = texture
	display.position = rectangle.position
	display.size = rectangle.size
	if texture.get_height() == 1:
		# 256×1 Ramp显示为40px高色带，仍使用原纹理，不改变输入的Y采样语义。
		display.stretch_mode = TextureRect.STRETCH_SCALE
		display.size.y = 40.0
	display.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_attach(parent, display, owner_node)

func _unshaded() -> CanvasItemMaterial:
	# CanvasModulate作用于同一canvas；校准色和说明文字必须保持本来颜色。
	var material := CanvasItemMaterial.new()
	material.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	return material

func _build_scene() -> void:
	var scene := Control.new()
	scene.name = "EmberTechnicalInputs"
	scene.size = SIZE
	scene.set_script(load("res://scenes/ember/technical_inputs_sandbox.gd"))
	var background := ColorRect.new()
	background.material = _unshaded()
	background.size = SIZE
	background.color = Color("182631")
	_attach(scene, background, scene)
	_label(scene, "技术输入库 · 40 PNG / 通道数据 / 内置灯光验收", Vector2(24, 12), scene, 26)
	_label(scene, "数据图按线性值读取；1通道采样.r。鼠标移动检修灯。资源准备不代表课程练习完成。", Vector2(24, 50), scene)
	var tabs := TabContainer.new()
	tabs.name = "InputTabs"
	tabs.position = Vector2(16, 86)
	tabs.size = Vector2(1408, 936)
	_attach(scene, tabs, scene)
	var pages: Array[Control] = []
	for title in ["校准与程序输入", "设备通道", "2D法线检修灯", "3D材质与草权重"]:
		var page := Control.new()
		page.name = title
		_attach(tabs, page, scene)
		pages.append(page)
	var basic_index := 0
	for asset: Dictionary in _assets:
		if str(asset["manifest_id"]) in ["D08", "D09", "D11", "D12"]: continue
		var at := Vector2(12 + (basic_index % 5)*276, 16 + (basic_index / 5)*214)
		_preview(pages[0], _tex(asset["id"]), Rect2(at, Vector2(256, 174)), scene)
		_label(pages[0], str(asset["id"]), at+Vector2(0, 178), scene, 14)
		basic_index += 1
	var mask_index := 0
	for asset: Dictionary in _assets:
		if asset["manifest_id"] != "D08": continue
		var at := Vector2(12 + (mask_index % 5)*276, 18 + (mask_index / 5)*406)
		_preview(pages[1], _tex(asset["id"]), Rect2(at, Vector2(252, 316)), scene)
		_label(pages[1], str(asset["id"]), at+Vector2(0, 322), scene)
		_label(pages[1], "R换色 G发光 B扰动 A轮廓", at+Vector2(0, 350), scene, 13)
		mask_index += 1
	_build_2d(pages[2], scene)
	_build_3d(pages[3], scene)
	var packed := PackedScene.new()
	if packed.pack(scene) == OK: _save(packed, SCENE)
	else: _errors.append("场景打包失败")
	scene.free()

func _white_texture(canvas: Vector2i = Vector2i(128, 128)) -> GradientTexture2D:
	var gradient := Gradient.new()
	gradient.colors = PackedColorArray([Color.WHITE, Color.WHITE])
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.width = canvas.x
	texture.height = canvas.y
	return texture

func _build_2d(page: Control, owner_node: Node) -> void:
	var modulation := CanvasModulate.new()
	modulation.color = Color(0.16, 0.16, 0.16)
	_attach(page, modulation, owner_node)
	for index in range(4):
		var sprite := Sprite2D.new()
		sprite.name = ["StationNormals", "ConsoleNormals", "FloorNormals", "AxisTest"][index]
		sprite.position = Vector2(185 + index*346, 348)
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		if index == 3:
			var texture := CanvasTexture.new()
			texture.diffuse_texture = _white_texture()
			texture.normal_texture = _tex("test_normal")
			sprite.texture = texture
		else:
			sprite.texture = load(RESOURCES[["station", "console", "floor_clean"][index]])
		sprite.scale = Vector2.ONE * (6.0 if index == 2 else 2.0)
		_attach(page, sprite, owner_node)
		_label(page, ["采能站", "控制台", "32px干净地板 ×6", "测试高度：凸 / 凹 / 轴向"][index], Vector2(40+index*346, 570), owner_node)
	var gradient := Gradient.new()
	gradient.colors = PackedColorArray([Color.WHITE, Color.TRANSPARENT])
	var light_texture := GradientTexture2D.new()
	light_texture.gradient = gradient
	light_texture.fill = GradientTexture2D.FILL_RADIAL
	light_texture.fill_from = Vector2(0.5, 0.5)
	light_texture.fill_to = Vector2(1.0, 0.5)
	light_texture.width = 512
	light_texture.height = 512
	var light := PointLight2D.new()
	light.name = "InspectionLight"
	light.texture = light_texture
	light.texture_scale = 4.0
	light.height = 100.0
	light.energy = 1.4
	light.position = Vector2(700, 200)
	_attach(page, light, owner_node)
	_label(page, "移动鼠标观察法线；底图本身含原有像素材质明暗，高度场仅是登记的浅浮雕代理。", Vector2(28, 800), owner_node)

func _build_3d(page: Control, owner_node: Node) -> void:
	var container := SubViewportContainer.new()
	container.size = Vector2(1000, 780)
	_attach(page, container, owner_node)
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1000, 780)
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
	environment.ambient_light_color = Color.WHITE
	environment.ambient_light_energy = 0.35
	environment_node.environment = environment
	_attach(world, environment_node, owner_node)
	var light := DirectionalLight3D.new()
	light.name = "SurfaceLight"
	light.rotation_degrees = Vector3(-45, -35, 0)
	_attach(world, light, owner_node)
	for index in range(2):
		var surface := MeshInstance3D.new()
		var plane := PlaneMesh.new()
		plane.size = Vector2(2.8, 4.0)
		surface.mesh = plane
		surface.position.x = -1.6 if index == 0 else 1.6
		surface.material_override = load(RESOURCES["metal" if index == 0 else "concrete"])
		_attach(world, surface, owner_node)
	var camera := Camera3D.new()
	camera.name = "SurfaceCamera"
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 7.0
	_attach(world, camera, owner_node)
	camera.look_at_from_position(Vector3(0, 5, 6), Vector3.ZERO, Vector3.UP)
	_preview(page, _tex("grass_height_weight"), Rect2(1100, 40, 256, 512), owner_node)
	_label(page, "草根像素119=0 / 顶部10=1", Vector2(1040, 575), owner_node)
	_label(page, "金属 / 混凝土：匹配法线 + .r 粗糙度/金属度；常量参数也保留为PNG，方便自行接入。", Vector2(28, 820), owner_node)

func _verify_resources() -> void:
	for identifier in ["station", "console", "floor_clean"]:
		var texture := load(RESOURCES[identifier]) as CanvasTexture
		if texture == null or texture.normal_texture != _tex(identifier+"_normal"):
			_errors.append("CanvasTexture法线不符：" + identifier)
		elif texture.get_size() != _tex(identifier+"_normal").get_size():
			_errors.append("CanvasTexture画布不符：" + identifier)
		if texture != null:
			if identifier == "floor_clean":
				var diffuse := texture.diffuse_texture as ImageTexture
				if diffuse == null or diffuse.get_size() != Vector2(32, 32) or diffuse.get_image().get_data() != _floor_diffuse().get_image().get_data():
					_errors.append("干净地板必须逐像素配对实际atlas左上32px单元")
			elif texture.diffuse_texture != load("res://assets/ember/buildings/%s/%s_base_v001.png" % [identifier, identifier]):
				_errors.append("CanvasTexture底图不符：" + identifier)
	for identifier in ["metal", "concrete"]:
		var material := load(RESOURCES[identifier]) as StandardMaterial3D
		if material == null:
			_errors.append("3D材质缺失：" + identifier)
			continue
		if not material.normal_enabled or material.normal_texture != _tex(identifier+"_normal"):
			_errors.append("3D法线未接入：" + identifier)
		if material.albedo_texture != load("res://assets/ember/three_d/textures/%s/%s_albedo_v001.png" % [identifier, identifier]):
			_errors.append("3D底色不符：" + identifier)
		if material.roughness_texture != _tex(identifier+"_roughness") or material.metallic_texture != _tex(identifier+"_metallic"):
			_errors.append("3D参数纹理不符：" + identifier)
		if material.roughness != 1.0 or material.metallic != 1.0: _errors.append("3D参数被重复相乘")
		if material.roughness_texture_channel != BaseMaterial3D.TEXTURE_CHANNEL_RED or material.metallic_texture_channel != BaseMaterial3D.TEXTURE_CHANNEL_RED:
			_errors.append("单通道材质必须采样.r")

func _capture(path: String) -> Image:
	await process_frame
	await RenderingServer.frame_post_draw
	var screenshot := root.get_texture().get_image()
	if screenshot.save_png(path) != OK: _errors.append("截图保存失败：" + path)
	return screenshot

func _verify_scene() -> void:
	var packed := load(SCENE) as PackedScene
	if packed == null:
		_errors.append("独立技术预览场景不存在")
		return
	var scene := packed.instantiate()
	root.add_child(scene)
	await process_frame
	# 进入场景树后才禁用普通鼠标跟随；初始化会自动启用脚本的_process回调。
	scene.set_process(false)
	var tabs := scene.get_node_or_null("InputTabs") as TabContainer
	if tabs == null or tabs.get_tab_count() != 4: _errors.append("技术预览页数不符")
	if not _screenshots.is_empty() and _errors.is_empty():
		if DisplayServer.get_name() == "headless": _errors.append("需真实GPU运行才能验收移动灯")
		else:
			DirAccess.make_dir_recursive_absolute(_screenshots)
			root.size = SIZE
			root.content_scale_size = SIZE
			for index in range(4):
				tabs.current_tab = index
				await _capture(_screenshots.path_join("inputs_page_%02d.png" % index))
			tabs.current_tab = 2
			await process_frame
			var light := scene.find_child("InspectionLight", true, false) as PointLight2D
			var test_sprite := scene.find_child("AxisTest", true, false) as Sprite2D
			if light == null or test_sprite == null: _errors.append("缺法线检修灯/测试对象")
			else:
				var light_image := light.texture.get_image()
				_light_diagnostics = {"enabled": light.enabled, "visible_in_tree": light.is_visible_in_tree(),
					"cull_mask": light.range_item_cull_mask, "test_light_mask": test_sprite.light_mask,
					"texture_center": str(light_image.get_pixel(256,256)), "texture_corner": str(light_image.get_pixel(0,0))}
				# 渐变本身作为源仍保留；显式上传ImageTexture，排除异步生成RID的状态。
				light.texture = ImageTexture.create_from_image(light_image)
				light.enabled = false
				light.enabled = true
				for entry in [["test_normal", "AxisTest"], ["station_normal", "StationNormals"], ["console_normal", "ConsoleNormals"], ["floor_clean_normal", "FloorNormals"]]:
					var target := scene.find_child(entry[1], true, false) as Sprite2D
					await _verify_gpu_axes(light, target, entry[0])
				# 用原配对底图实际观察检修灯；轴向定量检查临时白底，不改保存资源。
				for side in [["left", Vector2(240, 180)], ["right", Vector2(1100, 540)]]:
					light.position = side[1]
					await _capture(_screenshots.path_join("paired_normals_%s.png" % side[0]))
			tabs.current_tab = 3
			var camera := scene.find_child("SurfaceCamera", true, false) as Camera3D
			var surface_light := scene.find_child("SurfaceLight", true, false) as DirectionalLight3D
			for view in [["near", 4.5, -35.0], ["far", 12.0, 35.0]]:
				camera.size = view[1]
				surface_light.rotation_degrees.y = view[2]
				await _capture(_screenshots.path_join("surfaces_%s.png" % view[0]))
			camera.size = 7.0
			for side in [["left", -45.0], ["right", 45.0]]:
				surface_light.rotation_degrees.y = side[1]
				await _capture(_screenshots.path_join("surfaces_light_%s.png" % side[0]))
	root.remove_child(scene)
	scene.free()

func _verify_gpu_axes(light: PointLight2D, sprite: Sprite2D, identifier: String) -> void:
	var normal := _tex(identifier).get_image()
	var original_texture := sprite.texture
	var source_alpha := original_texture.get_image()
	var canvas := normal.get_size()
	var white := CanvasTexture.new()
	white.diffuse_texture = _white_texture(canvas)
	white.normal_texture = _tex(identifier)
	sprite.texture = white
	# 为每个轴选一个法线分量最大的可解释像素；灯在该点两侧等距，排除衰减差异。
	for axis in range(2):
		var best := Vector2i.ZERO
		var component := 0.0
		for y in range(1, canvas.y-1):
			for x in range(1, canvas.x-1):
				if source_alpha != null and source_alpha.get_pixel(x, y).a < 0.5: continue
				var color := normal.get_pixel(x, y)
				var value := (color.r if axis == 0 else color.g)*2.0-1.0
				if absf(value) > absf(component):
					best = Vector2i(x, y)
					component = value
		var sample_position := sprite.to_global(Vector2(best)+Vector2(0.5, 0.5)-Vector2(canvas)*0.5)
		var direction := Vector2.RIGHT if axis == 0 else Vector2.UP
		var brightness: Array[float] = []
		var actual_light_positions: Array = []
		for sign_value in [-1, 1]:
			light.global_position = sample_position+direction*300.0*sign_value
			var screenshot := await _capture(_screenshots.path_join("%s_axis_%s_%s.png" % [identifier, "x" if axis == 0 else "y", "negative" if sign_value == -1 else "positive"]))
			var pixel := screenshot.get_pixel(int(sample_position.x), int(sample_position.y))
			brightness.append((pixel.r+pixel.g+pixel.b)/3.0)
			actual_light_positions.append([light.global_position.x, light.global_position.y])
		var delta := brightness[1]-brightness[0]
		var passed := absf(component)>0.05 and delta*component>0.003
		_light_checks.append({"id": identifier, "axis": "X_RIGHT" if axis == 0 else "Y_UP", "source_pixel": [best.x, best.y], "normal_component": component,
			"screen_pixel": [int(sample_position.x), int(sample_position.y)], "brightness_delta": delta,
			"actual_light_positions": actual_light_positions,
			"brightness_negative_light": brightness[0], "brightness_positive_light": brightness[1], "pass": passed})
		if not passed: _errors.append("GPU移动灯方向验收失败：" + identifier+"/"+str(axis))
	sprite.texture = original_texture
