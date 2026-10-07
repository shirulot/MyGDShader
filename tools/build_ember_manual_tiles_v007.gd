extends SceneTree
## 创建新版完整手工笔刷集；使用独立目录，不覆盖历史资源。
const DIR := "res://assets/ember/environment/tilesets_v007/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIR + "catalog.json"))
	var common := TileSet.new()
	common.tile_size = Vector2i(128,128)
	common.add_custom_data_layer()
	common.set_custom_data_layer_name(0,"tile_id")
	common.set_custom_data_layer_type(0,TYPE_STRING)
	var count := 0
	for atlas in catalog.atlases:
		var source := TileSetAtlasSource.new()
		source.texture = load(atlas.texture)
		source.texture_region_size = Vector2i(128,128)
		source.use_texture_padding = true
		common.add_source(source,int(atlas.source_id))
		for entry in atlas.tiles:
			var coord := Vector2i(int(entry.coord[0]),int(entry.coord[1]))
			source.create_tile(coord)
			source.get_tile_data(coord,0).set_custom_data("tile_id",str(entry.id))
			count += 1
	assert(count == 67)
	assert(ResourceSaver.save(common,DIR + "ember_common_tileset_v007.tres") == OK)
	# 从磁盘重新载入并逐个核对自定义 ID，避免只验证内存对象。
	var reloaded := ResourceLoader.load(DIR + "ember_common_tileset_v007.tres","TileSet",ResourceLoader.CACHE_MODE_IGNORE) as TileSet
	for atlas in catalog.atlases:
		var source := reloaded.get_source(int(atlas.source_id)) as TileSetAtlasSource
		for entry in atlas.tiles:
			var coord := Vector2i(int(entry.coord[0]),int(entry.coord[1]))
			assert(source.has_tile(coord))
			assert(source.get_tile_data(coord,0).get_custom_data("tile_id") == str(entry.id))
	var scene := Node2D.new()
	scene.name = "EmberUnifiedBrushes"
	var preview_script := load("res://scripts/ember/manual_brush_preview_v007.gd") as Script
	assert(preview_script != null and preview_script.can_instantiate())
	scene.set_script(preview_script)
	var packed := PackedScene.new()
	assert(packed.pack(scene) == OK)
	assert(ResourceSaver.save(packed,"res://scenes/ember/manual_brush_preview_v007.tscn") == OK)
	scene.free()
	var file := FileAccess.open(DIR + "godot_validation.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine":Engine.get_version_info().string,"verified_ids":count,"source_count":3,"failures":[]},"  "))
	print("MANUAL_BRUSHES_VERIFIED: ",count)
	quit()
