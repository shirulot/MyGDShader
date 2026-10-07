extends SceneTree
## 只整理交付覆盖格式：原始母图不改。先建立一份实体覆盖，再导出完整PNG；
## 可选功能层随后从这张生产图分配像素，禁止每个部件单独阈值或修轮廓。

const OUT := "res://assets/ember/buildings_final/textures/"
const SOURCE := "res://assets/ember/buildings_final/source/building-assets-v004/masters/"
const COVERAGE_THRESHOLD := 128

func _initialize() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ember/buildings_final/source/building-assets-v004/registration_baseline_v004.json"))
	catalog.revision = "building_assets_v004r1"
	catalog.status = "COVERAGE_AND_DEMO_FIX_PENDING_TA"
	catalog.coverage_rule = "One source mask: alpha >= 128 becomes 255, otherwise 0; retain covered RGB; canonical empty RGBA=0. No geometry, scale or anchor changes."
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT + "complete"))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT + "coverage"))
	var records: Array[Dictionary] = []
	for building: Dictionary in catalog.buildings:
		var master: String = SOURCE + String(building.id) + "_intact_v004.png"
		var source := Image.load_from_file(ProjectSettings.globalize_path(master))
		source.convert(Image.FORMAT_RGBA8)
		var rgba := source.get_data()
		var mask := PackedByteArray()
		mask.resize(rgba.size())
		var solid_count := 0
		var discarded_semitransparent := 0
		for i: int in range(0, rgba.size(), 4):
			if rgba[i + 3] >= COVERAGE_THRESHOLD:
				rgba[i + 3] = 255
				for channel: int in 4: mask[i + channel] = 255
				solid_count += 1
			else:
				if rgba[i + 3] > 0: discarded_semitransparent += 1
				for channel: int in 4: rgba[i + channel] = 0
		var image := Image.create_from_data(source.get_width(), source.get_height(), false, Image.FORMAT_RGBA8, rgba)
		var mask_image := Image.create_from_data(source.get_width(), source.get_height(), false, Image.FORMAT_RGBA8, mask)
		building.source_master = master
		building.source_master_sha256 = FileAccess.get_sha256(master)
		building.complete_texture = OUT + "complete/" + String(building.id) + "_closed_v004r1.png"
		building.coverage_mask = OUT + "coverage/" + String(building.id) + "_coverage_v004r1.png"
		image.save_png(building.complete_texture)
		mask_image.save_png(building.coverage_mask)
		building.complete_sha256 = FileAccess.get_sha256(building.complete_texture)
		building.coverage_sha256 = FileAccess.get_sha256(building.coverage_mask)
		records.append({"building": building.id, "master_sha256": building.source_master_sha256,
			"production_sha256": building.complete_sha256, "covered_pixels": solid_count,
			"discarded_low_alpha_pixels": discarded_semitransparent, "threshold": COVERAGE_THRESHOLD,
			"rgb_rule": "Exact source RGB on shared coverage; no recoloring, smoothing, resizing, morphology or new outlines."})
	var file := FileAccess.open(OUT + "catalog_v004r1.json", FileAccess.WRITE)
	# 保留原目录double数值，避免JSON默认有限精度使未改的注册出现舍入差。
	file.store_string(JSON.stringify(catalog, "\t", true, true))
	file = FileAccess.open(OUT + "coverage_export_v004r1.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"revision": "v004r1", "source_masters_unchanged": true, "records": records}, "\t"))
	print("EXPORTED_SHARED_BINARY_COVERAGE")
	quit()
