extends SceneTree
## 从同一母图按登记的像素区域导出可选功能层。只分配像素所有权，
## 不重画、不缩放任何屋檐或圆角；实际场景使用完整母图的单载体渲染。

const ROOT := "res://assets/ember/buildings_final/textures/"

func _initialize() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ROOT + "catalog_v004r1.json"))
	var manifest: Array[Dictionary] = []
	for building: Dictionary in catalog.buildings:
		var source := Image.load_from_file(ProjectSettings.globalize_path(building.complete_texture))
		source.convert(Image.FORMAT_RGBA8)
		var fixed := source.duplicate() as Image
		var layers: Array[Dictionary] = []
		for door: Dictionary in building.doors:
			layers.append({"id": door.id + "_leaf", "regions": [door.source_rect_px], "chamfer": door.get("chamfer_px", 0)})
		for pair: Array in [["maintenance_cover", "service_rect"], ["roof_hatch", "hatch_rect"]]:
			if building.has(pair[1]): layers.append({"id": pair[0], "regions": [building[pair[1]]], "chamfer": 0})
		if not building.lens_rects.is_empty(): layers.append({"id": "status_lenses", "regions": building.lens_rects, "chamfer": 0})
		if not building.glass_rects.is_empty(): layers.append({"id": "glass", "regions": building.glass_rects, "chamfer": 0})
		var folder := ROOT + "functional/" + String(building.id) + "/"
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
		for layer: Dictionary in layers:
			var output := Image.create(source.get_width(), source.get_height(), false, Image.FORMAT_RGBA8)
			for box: Array in layer.regions:
				var rect := Rect2i(box[0], box[1], box[2], box[3])
				for y: int in range(rect.position.y, rect.end.y):
					for x: int in range(rect.position.x, rect.end.x):
						var p := Vector2(x + 0.5, y + 0.5) - Vector2(rect.position)
						if p.x + p.y < float(layer.chamfer) or rect.size.x - p.x + p.y < float(layer.chamfer): continue
						output.set_pixel(x, y, source.get_pixel(x, y))
						fixed.set_pixel(x, y, Color.TRANSPARENT)
			var filename := folder + String(layer.id) + ".png"
			output.save_png(filename)
			layer.texture = filename
			layer.sha256 = FileAccess.get_sha256(filename)
		fixed.save_png(folder + "fixed_architecture.png")
		manifest.append({"building_id": building.id, "canvas_px": building.canvas_px,
			"source_pivot_px": building.source_pivot_px, "uniform_scale": building.uniform_scale,
			"complete_texture": building.complete_texture, "fixed_architecture": folder + "fixed_architecture.png",
			"fixed_sha256": FileAccess.get_sha256(folder + "fixed_architecture.png"), "layers": layers})
	var file := FileAccess.open(ROOT + "functional_layers_v004r1.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"revision": "v004r1", "method": "same_master_disjoint_pixel_ownership", "buildings": manifest}, "\t", true, true))
	print("EXPORTED_SAME_MASTER_FUNCTIONAL_LAYERS")
	quit()
