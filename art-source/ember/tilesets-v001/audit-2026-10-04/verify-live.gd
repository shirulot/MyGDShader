extends SceneTree
## 将实际完成的 32×32 atlas 整理为可在 TileMapLayer 中直接绘制的 TileSet。
## 运行：godot --headless --path . -s res://tools/build_ember_tilesets.gd --
## 可选：--verify-only 只核验；--rebuild-sandbox 明确重建示例（会覆盖示例布局）。
## 可选：--catalog=res://...json；--screenshot=绝对路径（截图需非 headless 渲染）。
## 此工具不绘制或修复 PNG，不配置碰撞、自动地形连接，也不修改现有游戏。

const DEFAULT_CATALOG := "res://assets/ember/environment/tilesets/ember_tiles_catalog_v001.json"
const OUTPUT_DIR := "res://assets/ember/environment/tilesets"
const COMMON_TILESET := OUTPUT_DIR + "/ember_common_tileset_v001.tres"
const SANDBOX_SCENE := "res://scenes/ember/tileset_layout_sandbox.tscn"
const VALIDATION_REPORT := "res://art-source/ember/tilesets-v001/audit-2026-10-04/verify-live.json"
const TILE_SIZE := 32
const ATLAS_RULES := {
	"ground_details": {"source_id": 0, "count": 12, "size": Vector2i(256, 64)},
	"structures": {"source_id": 1, "count": 26, "size": Vector2i(256, 128)},
	"utilities": {"source_id": 2, "count": 24, "size": Vector2i(256, 96)},
}

var _errors: PackedStringArray = []
var _catalog_path := DEFAULT_CATALOG
var _verify_only := false
var _rebuild_sandbox := false
var _screenshot_path := ""


func _initialize() -> void:
	# 延迟到 SceneTree 初始化后执行，便于核验生成后的场景和截取渲染结果。
	call_deferred("_run")


func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument == "--verify-only":
			_verify_only = true
		elif argument == "--rebuild-sandbox":
			_rebuild_sandbox = true
		elif argument.begins_with("--catalog="):
			_catalog_path = argument.trim_prefix("--catalog=")
		elif argument.begins_with("--screenshot="):
			_screenshot_path = argument.trim_prefix("--screenshot=")
		else:
			_errors.append("不支持的参数：" + argument)
	var catalog := _read_catalog()
	_validate_catalog(catalog)
	if not _errors.is_empty():
		_finish_failure()
		return

	if not _verify_only:
		_build_tilesets(catalog)
		if _errors.is_empty() and (_rebuild_sandbox or not FileAccess.file_exists(SANDBOX_SCENE)):
			_build_sandbox(catalog)
		elif _errors.is_empty():
			print("保留已存在的可编辑场景：", SANDBOX_SCENE)
	if _errors.is_empty():
		_verify_resources(catalog)
	if not _errors.is_empty():
		_finish_failure()
		return

	var report := {
		"status": "GODOT_RESOURCE_VALIDATED",
		"engine": Engine.get_version_info(),
		"catalog": _catalog_path,
		"tile_size": TILE_SIZE,
		"source_count": 3,
		"tile_count": 62,
		"common_tileset": COMMON_TILESET,
		"sandbox_scene": SANDBOX_SCENE,
		"timestamp_utc": Time.get_datetime_string_from_system(true),
		"scope": "TileSet 序列化、重载、数量、坐标、自定义数据与场景加载；美术质量由独立验收记录判断。",
	}
	if not _screenshot_path.is_empty():
		if DisplayServer.get_name() == "headless":
			_errors.append("headless 不提供实际渲染截图；请使用非 headless 运行 --screenshot。")
		else:
			await _capture_sandbox()
			report["screenshot"] = _screenshot_path
	if not _errors.is_empty():
		_finish_failure()
		return
	_write_report(report)
	if not _errors.is_empty():
		_finish_failure()
		return
	print(JSON.stringify(report, "\t"))
	quit(0)


func _read_catalog() -> Dictionary:
	if not FileAccess.file_exists(_catalog_path):
		_errors.append("catalog 尚未就绪：" + _catalog_path)
		return {}
	var parser := JSON.new()
	var parse_error := parser.parse(FileAccess.get_file_as_string(_catalog_path))
	if parse_error != OK or not parser.data is Dictionary:
		_errors.append("catalog 必须是 JSON 对象：" + parser.get_error_message())
		return {}
	return parser.data as Dictionary


func _validate_catalog(catalog: Dictionary) -> void:
	# 写入资源之前一次性检查全部输入，避免缺图时产出似乎可用的半套资源。
	if catalog.is_empty():
		return
	if catalog.get("tile_size") != TILE_SIZE:
		_errors.append("catalog.tile_size 必须为 32。")
	if not catalog.get("atlases") is Array:
		_errors.append("catalog.atlases 必须为数组。")
		return
	var atlases: Array = catalog["atlases"]
	if atlases.size() != ATLAS_RULES.size():
		_errors.append("必须提供 ground_details、structures、utilities 三套 atlas。")
	var atlas_ids := {}
	var all_tile_ids := {}
	for atlas_value in atlases:
		if not atlas_value is Dictionary:
			_errors.append("atlas 项必须为对象。")
			continue
		var atlas: Dictionary = atlas_value
		var atlas_id := str(atlas.get("id", ""))
		if not ATLAS_RULES.has(atlas_id) or atlas_ids.has(atlas_id):
			_errors.append("未知或重复 atlas.id：" + atlas_id)
			continue
		atlas_ids[atlas_id] = true
		var rule: Dictionary = ATLAS_RULES[atlas_id]
		if atlas.get("source_id") != rule["source_id"]:
			_errors.append("source_id 不符合固定约定：" + atlas_id)
		var texture_path := str(atlas.get("texture", ""))
		if texture_path != OUTPUT_DIR + "/" + atlas_id + "_v001.png":
			_errors.append("texture 路径不符合约定：" + texture_path)
			continue
		if not FileAccess.file_exists(texture_path):
			_errors.append("PNG 尚未就绪：" + texture_path)
			continue
		if not ResourceLoader.exists(texture_path, "Texture2D"):
			_errors.append("PNG 尚未导入 Godot；先运行 --headless --editor --import：" + texture_path)
			continue
		# 通过正式导入的 Texture2D 核对尺寸，与 TileSet 真正使用的资源一致。
		# 不直接 Image.load(res://PNG)，避免误触发仅适用于裸文件的导出警告。
		var texture := ResourceLoader.load(texture_path, "Texture2D") as Texture2D
		if texture == null or Vector2i(texture.get_size()) != rule["size"]:
			_errors.append("PNG 必须为规定的原生尺寸：" + texture_path)
		if not atlas.get("tiles") is Array:
			_errors.append("atlas.tiles 必须为数组：" + atlas_id)
			continue
		var tiles: Array = atlas["tiles"]
		if tiles.size() != rule["count"]:
			_errors.append("Tile 数量不符：" + atlas_id)
		var coordinates := {}
		for tile_value in tiles:
			if not tile_value is Dictionary:
				_errors.append("Tile 项必须为对象：" + atlas_id)
				continue
			var tile: Dictionary = tile_value
			var tile_id := str(tile.get("id", ""))
			if tile_id.is_empty() or all_tile_ids.has(tile_id):
				_errors.append("空或重复 tile.id：" + tile_id)
			all_tile_ids[tile_id] = true
			if str(tile.get("category", "")).is_empty():
				_errors.append("category 缺失：" + tile_id)
			var coordinate_value: Variant = tile.get("coord")
			if not coordinate_value is Array or coordinate_value.size() != 2:
				_errors.append("coord 必须为 [x, y]：" + tile_id)
				continue
			if not _is_integer(coordinate_value[0]) or not _is_integer(coordinate_value[1]):
				_errors.append("coord 必须为整数坐标：" + tile_id)
				continue
			var coordinate := Vector2i(int(coordinate_value[0]), int(coordinate_value[1]))
			var grid_size: Vector2i = rule["size"] / TILE_SIZE
			if coordinate.x < 0 or coordinate.y < 0 or coordinate.x >= grid_size.x or coordinate.y >= grid_size.y:
				_errors.append("coord 越出 atlas：" + tile_id)
			if coordinates.has(coordinate):
				_errors.append("coord 重复：" + tile_id)
			coordinates[coordinate] = true


func _is_integer(value: Variant) -> bool:
	return (value is int or value is float) and float(value) == floorf(float(value))


func _new_tileset(resource_label: String) -> TileSet:
	var tileset := TileSet.new()
	tileset.resource_name = resource_label
	tileset.tile_size = Vector2i(TILE_SIZE, TILE_SIZE)
	# 字符串标识便于在 Inspector 中辨认，不预设碰撞或课程 Shader 参数。
	for data_name in ["tile_id", "category"]:
		tileset.add_custom_data_layer()
		var layer_index := tileset.get_custom_data_layers_count() - 1
		tileset.set_custom_data_layer_name(layer_index, data_name)
		tileset.set_custom_data_layer_type(layer_index, TYPE_STRING)
	return tileset


func _add_atlas(tileset: TileSet, atlas: Dictionary) -> void:
	var source := TileSetAtlasSource.new()
	source.resource_name = str(atlas["id"])
	source.texture = ResourceLoader.load(str(atlas["texture"]), "Texture2D") as Texture2D
	source.texture_region_size = Vector2i(TILE_SIZE, TILE_SIZE)
	source.margins = Vector2i.ZERO
	source.separation = Vector2i.ZERO
	# 保持默认 padding，避免采样相邻图块产生细线；源 PNG 无额外 gutter。
	source.use_texture_padding = true
	tileset.add_source(source, int(atlas["source_id"]))
	for tile_value in atlas["tiles"]:
		var tile: Dictionary = tile_value
		var coordinate := _tile_coord(tile)
		# 只创建清单列出的实际 Tile，atlas 最后一行的透明空格不能成为画笔。
		source.create_tile(coordinate)
		var data := source.get_tile_data(coordinate, 0)
		data.set_custom_data("tile_id", str(tile["id"]))
		data.set_custom_data("category", str(tile["category"]))


func _build_tilesets(catalog: Dictionary) -> void:
	var combined := _new_tileset("Ember Common Tiles 32 px")
	for atlas_value in catalog["atlases"]:
		var atlas: Dictionary = atlas_value
		var individual := _new_tileset("Ember " + str(atlas["id"]))
		_add_atlas(individual, atlas)
		_save_resource(individual, _individual_path(atlas))
		_add_atlas(combined, atlas)
	_save_resource(combined, COMMON_TILESET)


func _build_sandbox(catalog: Dictionary) -> void:
	var tileset := ResourceLoader.load(COMMON_TILESET, "TileSet", ResourceLoader.CACHE_MODE_IGNORE) as TileSet
	var scene_root := Node2D.new()
	scene_root.name = "EmberTileSetLayoutSandbox"
	scene_root.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_add_label(scene_root, scene_root, "Title", Vector2(32, 20), "余烬采能站 · 32×32 通用瓦片集", 24)
	_add_label(scene_root, scene_root, "Usage", Vector2(32, 58), "选择 LayoutWorkspace 下的 TileMapLayer，在编辑器底部 TileMap 面板自由绘制。", 14)
	var catalog_node := Node2D.new()
	catalog_node.name = "TileCatalog"
	catalog_node.position = Vector2(32, 116)
	scene_root.add_child(catalog_node)
	catalog_node.owner = scene_root
	var atlas_positions := {"ground_details": Vector2.ZERO, "structures": Vector2(0, 136), "utilities": Vector2(320, 136)}
	var atlas_labels := {"ground_details": "地面与细节 · 12 块", "structures": "墙体 / 栏杆 / 桥面 · 26 块", "utilities": "管线 / 水渠岸线 · 24 块"}
	for atlas_value in catalog["atlases"]:
		var atlas: Dictionary = atlas_value
		var atlas_id := str(atlas["id"])
		var layer := _add_layer(catalog_node, scene_root, atlas_id.to_pascal_case(), tileset, atlas_positions[atlas_id], 0)
		for tile_value in atlas["tiles"]:
			var tile: Dictionary = tile_value
			layer.set_cell(_tile_coord(tile), int(atlas["source_id"]), _tile_coord(tile), 0)
		_add_label(catalog_node, scene_root, atlas_id.to_pascal_case() + "Label", atlas_positions[atlas_id] + Vector2(0, -26), atlas_labels[atlas_id], 16)
	# 画布只是一个小型可编辑起点，所有格子均序列化在场景中，运行时不会重画。
	var workspace := Node2D.new()
	workspace.name = "LayoutWorkspace"
	workspace.position = Vector2(32, 468)
	scene_root.add_child(workspace)
	workspace.owner = scene_root
	_add_label(workspace, scene_root, "WorkspaceLabel", Vector2(0, -30), "可编辑布局 · 地面 / 结构 / 管线 / 细节四层", 18)
	var ground := _add_layer(workspace, scene_root, "Ground", tileset, Vector2.ZERO, 0)
	var structures := _add_layer(workspace, scene_root, "Structures", tileset, Vector2.ZERO, 1)
	var utilities := _add_layer(workspace, scene_root, "Utilities", tileset, Vector2.ZERO, 2)
	# 检修口与贴花（T07 / T08）独立放在透明细节层，方便叠加与单独隐藏。
	var details := _add_layer(workspace, scene_root, "Details", tileset, Vector2.ZERO, 3)
	var first_atlas: Dictionary = catalog["atlases"][0]
	for atlas_value in catalog["atlases"]:
		if atlas_value["id"] == "ground_details":
			first_atlas = atlas_value
	var floor_tiles: Array = []
	for tile_value in first_atlas["tiles"]:
		if tile_value["category"] == "T01":
			floor_tiles.append(tile_value)
	if not floor_tiles.is_empty():
		for y in range(5):
			for x in range(8):
				var tile: Dictionary = floor_tiles[int(x / 2) % floor_tiles.size()]
				ground.set_cell(Vector2i(x, y), int(first_atlas["source_id"]), _tile_coord(tile), 0)
	# 首次创建时给出真正由TileMapLayer单元组成的连接样例；以后可以任意擦除/扩展。
	var wall_rows := [
		["wall_outer_nw", "wall_edge_n", "wall_outer_ne"],
		["wall_edge_w", "wall_center", "wall_edge_e"],
		["wall_outer_sw", "wall_edge_s", "wall_outer_se"],
	]
	var pipe_rows := [
		["pipe_elbow_se", "pipe_tee_s", "pipe_elbow_sw"],
		["pipe_tee_e", "pipe_cross", "pipe_tee_w"],
		["pipe_elbow_ne", "pipe_tee_n", "pipe_elbow_nw"],
	]
	for y in range(3):
		for x in range(3):
			_set_named_cell(structures, catalog, wall_rows[y][x], Vector2i(x, y))
			_set_named_cell(utilities, catalog, pipe_rows[y][x], Vector2i(x + 5, y))
	for x in range(5, 8):
		_set_named_cell(structures, catalog, "rail_straight_h", Vector2i(x, 3))
	_set_named_cell(details, catalog, "hatch_closed", Vector2i(0, 4))
	_set_named_cell(details, catalog, "hatch_open", Vector2i(1, 4))
	_set_named_cell(details, catalog, "decal_crack", Vector2i(2, 4))
	_set_named_cell(details, catalog, "decal_oil", Vector2i(3, 4))
	_set_named_cell(details, catalog, "decal_cable_loop", Vector2i(4, 4))
	_set_named_cell(details, catalog, "decal_debris", Vector2i(7, 4))
	_add_label(workspace, scene_root, "Hint", Vector2(292, 8), "Ground：地板\nStructures：墙体、栏杆、桥面\nUtilities：管线、水渠岸线\nDetails：检修口、贴花（T07 / T08）\n\n共享外部 TileSet，可画到任意范围。\n结构、管线与细节可叠在地板上。", 16)
	var packed_scene := PackedScene.new()
	if packed_scene.pack(scene_root) != OK:
		_errors.append("打包示例场景失败。")
	else:
		_save_resource(packed_scene, SANDBOX_SCENE)
	scene_root.free()


func _set_named_cell(layer: TileMapLayer, catalog: Dictionary, tile_id: String, map_coord: Vector2i) -> void:
	# 样例使用稳定ID查找atlas坐标，目录重排时不会悄悄指向别的图块。
	for atlas_value in catalog["atlases"]:
		var atlas: Dictionary = atlas_value
		for tile_value in atlas["tiles"]:
			var tile: Dictionary = tile_value
			if tile["id"] == tile_id:
				layer.set_cell(map_coord, int(atlas["source_id"]), _tile_coord(tile), 0)
				return
	_errors.append("样例图块ID不存在：" + tile_id)


func _add_layer(parent: Node, scene_root: Node, layer_name: String, tileset: TileSet, location: Vector2, z_layer: int) -> TileMapLayer:
	var layer := TileMapLayer.new()
	layer.name = layer_name
	layer.position = location
	layer.tile_set = tileset
	layer.z_index = z_layer
	layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	parent.add_child(layer)
	layer.owner = scene_root
	return layer


func _add_label(parent: Node, scene_root: Node, label_name: String, location: Vector2, content: String, font_size: int) -> void:
	var label := Label.new()
	label.name = label_name
	label.position = location
	label.text = content
	# 中文说明使用系统字体，不将本机字体文件复制进素材包。
	var display_font := SystemFont.new()
	display_font.font_names = PackedStringArray(["Microsoft YaHei", "Noto Sans CJK SC", "PingFang SC", "Arial"])
	label.add_theme_font_override("font", display_font)
	label.add_theme_font_size_override("font_size", font_size)
	parent.add_child(label)
	label.owner = scene_root


func _save_resource(resource: Resource, output_path: String) -> void:
	var directory := ProjectSettings.globalize_path(output_path.get_base_dir())
	if DirAccess.make_dir_recursive_absolute(directory) != OK:
		_errors.append("创建输出目录失败：" + directory)
		return
	var save_error := ResourceSaver.save(resource, output_path)
	if save_error != OK:
		_errors.append("保存失败 %s：%s" % [error_string(save_error), output_path])


func _verify_resources(catalog: Dictionary) -> void:
	var combined := ResourceLoader.load(COMMON_TILESET, "TileSet", ResourceLoader.CACHE_MODE_IGNORE) as TileSet
	if combined == null or combined.get_source_count() != 3 or combined.tile_size != Vector2i(TILE_SIZE, TILE_SIZE):
		_errors.append("合并 TileSet 无法重载或基础属性不符。")
		return
	for atlas_value in catalog["atlases"]:
		var atlas: Dictionary = atlas_value
		var individual := ResourceLoader.load(_individual_path(atlas), "TileSet", ResourceLoader.CACHE_MODE_IGNORE) as TileSet
		if individual == null or individual.get_source_count() != 1 or individual.tile_size != combined.tile_size:
			_errors.append("独立 TileSet 无法重载或基础属性不符：" + str(atlas["id"]))
			continue
		for tileset in [combined, individual]:
			if not tileset.has_source(int(atlas["source_id"])):
				_errors.append("缺失 source_id：" + str(atlas["id"]))
				continue
			var source := tileset.get_source(int(atlas["source_id"])) as TileSetAtlasSource
			if source == null or source.get_tiles_count() != atlas["tiles"].size() or source.has_tiles_outside_texture():
				_errors.append("Tile 数量或范围错误：" + str(atlas["id"]))
				continue
			for tile_value in atlas["tiles"]:
				var tile: Dictionary = tile_value
				var coordinate := _tile_coord(tile)
				if not source.has_tile(coordinate):
					_errors.append("缺失坐标：" + str(tile["id"]))
					continue
				var data := source.get_tile_data(coordinate, 0)
				if data.get_custom_data("tile_id") != tile["id"] or data.get_custom_data("category") != tile["category"]:
					_errors.append("自定义数据不符：" + str(tile["id"]))
	var packed_scene := ResourceLoader.load(SANDBOX_SCENE, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	if packed_scene == null:
		_errors.append("示例场景无法加载。")
		return
	var scene := packed_scene.instantiate()
	var tile_layers := scene.find_children("*", "TileMapLayer", true, false)
	if tile_layers.size() < 4:
		_errors.append("示例场景必须包含至少四个 TileMapLayer。")
	for layout_layer_name in ["Ground", "Structures", "Utilities", "Details"]:
		if not scene.get_node_or_null("LayoutWorkspace/" + layout_layer_name) is TileMapLayer:
			_errors.append("缺失布局图层：" + layout_layer_name)
	for layer in tile_layers:
		if layer.tile_set == null or layer.tile_set.resource_path != COMMON_TILESET:
			_errors.append("TileMapLayer 必须共享合并的外部 TileSet。")
	scene.free()


func _capture_sandbox() -> void:
	# 仅调整本次核验窗口，完整显示三套画笔；不写入项目的720×720配置。
	root.content_scale_size = Vector2i(1200, 720)
	root.size = Vector2i(1200, 720)
	var packed_scene := load(SANDBOX_SCENE) as PackedScene
	root.add_child(packed_scene.instantiate())
	# 等待已提交的 TileMapLayer 绘制结束，再保存真实 Godot 渲染结果。
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var screenshot := root.get_texture().get_image()
	var directory := _screenshot_path.get_base_dir()
	if DirAccess.make_dir_recursive_absolute(directory) != OK or screenshot.save_png(_screenshot_path) != OK:
		_errors.append("Godot 截图保存失败：" + _screenshot_path)


func _write_report(report: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(VALIDATION_REPORT.get_base_dir()))
	var file := FileAccess.open(VALIDATION_REPORT, FileAccess.WRITE)
	if file == null:
		_errors.append("核验报告写入失败。")
		return
	file.store_string(JSON.stringify(report, "\t") + "\n")


func _tile_coord(tile: Dictionary) -> Vector2i:
	return Vector2i(int(tile["coord"][0]), int(tile["coord"][1]))


func _individual_path(atlas: Dictionary) -> String:
	return OUTPUT_DIR + "/" + str(atlas["id"]) + "_tileset_v001.tres"


func _finish_failure() -> void:
	for message in _errors:
		push_error(message)
	quit(1)
