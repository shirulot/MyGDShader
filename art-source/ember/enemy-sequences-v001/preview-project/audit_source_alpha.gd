extends SceneTree
## 只读源 PNG 的真实 RGBA，统计四角和每格边缘的 alpha；不依赖截图的黑底。
## 此工具不 save_png、不删除或修补任何像素，旧版本也保留并分别记录。


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var source_dir := ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	var specs: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(source_dir + "/sequence_specs_v001.json"))
	var master_dir := source_dir + "/masters/"
	var records: Array = []
	for clip: Dictionary in specs.clips:
		for filename: String in DirAccess.get_files_at(master_dir):
			if not filename.begins_with(str(clip.id) + "_master_") or not filename.ends_with(".png"):
				continue
			var path := master_dir + filename
			var image := Image.load_from_file(path)
			if image == null or image.is_empty():
				continue
			image.convert(Image.FORMAT_RGBA8)
			var bytes := image.get_data()
			var width := image.get_width()
			var height := image.get_height()
			var zero := 0
			var partial := 0
			var opaque := 0
			var visible := 0
			for index in range(width * height):
				var alpha := int(bytes[index * 4 + 3])
				if alpha == 0:
					zero += 1
				elif alpha == 255:
					opaque += 1
				else:
					partial += 1
				if alpha >= 26:
					visible += 1
			var cells: Array = []
			var columns := int(clip.columns)
			var rows := int(clip.rows)
			for row in range(rows):
				for column in range(columns):
					var x0 := floori(float(column * width) / columns)
					var x1 := floori(float((column + 1) * width) / columns)
					var y0 := floori(float(row * height) / rows)
					var y1 := floori(float((row + 1) * height) / rows)
					var band := maxi(1, mini(x1 - x0, y1 - y0) / 128)
					var corner := maxi(2, mini(x1 - x0, y1 - y0) * 4 / 128)
					var border_pixels := 0
					var border_nonzero := 0
					var border_visible := 0
					var corner_pixels := 0
					var corner_nonzero := 0
					var corner_visible := 0
					var maximum_corner := 0
					for y in range(y0, y1):
						# 只读上/下整条薄边，左右边内带；不遍历每格内部第二遍。
						var runs: Array = [[x0, x1]] if y - y0 < band or y1 - y <= band else [[x0, x0 + band], [x1 - band, x1]]
						for run: Array in runs:
							for x in range(int(run[0]), int(run[1])):
								var alpha := int(bytes[(y * width + x) * 4 + 3])
								border_pixels += 1
								if alpha > 0:
									border_nonzero += 1
								if alpha >= 26:
									border_visible += 1
					for cy: int in [y0, y1 - corner]:
						for cx: int in [x0, x1 - corner]:
							for y in range(cy, cy + corner):
								for x in range(cx, cx + corner):
									var alpha := int(bytes[(y * width + x) * 4 + 3])
									corner_pixels += 1
									maximum_corner = maxi(maximum_corner, alpha)
									if alpha > 0:
										corner_nonzero += 1
									if alpha >= 26:
										corner_visible += 1
					cells.append({"frame": row * columns + column, "source_region_px": [x0, y0, x1 - x0, y1 - y0],
						"border_nonzero_fraction": float(border_nonzero) / border_pixels,
						"border_visible_fraction": float(border_visible) / border_pixels,
						"corner_nonzero_fraction": float(corner_nonzero) / corner_pixels,
						"corner_visible_fraction": float(corner_visible) / corner_pixels,
						"corner_max_alpha": maximum_corner})
			var count := float(width * height)
			var record := {"id": clip.id, "filename": filename, "source_master": path, "source_sha256": FileAccess.get_sha256(path),
				"is_selected_master": path == str(clip.master_path), "source_size_px": [width, height],
				"alpha_zero_pixels": zero, "alpha_opaque_pixels": opaque, "alpha_partial_pixels": partial,
				"alpha_ge_0_1_pixels": visible, "alpha_zero_fraction": zero / count,
				"alpha_opaque_fraction": opaque / count, "alpha_partial_fraction": partial / count, "cells": cells}
			records.append(record)
			print("SOURCE_ALPHA_READ_ONLY ", filename, " transparent=", record.alpha_zero_fraction, " opaque=", record.alpha_opaque_fraction)
	var output := FileAccess.open(source_dir + "/qa/source_raw_alpha_audit_v001.json", FileAccess.WRITE)
	output.store_string(JSON.stringify({"status": "READ_ONLY_SOURCE_RGBA_AUDIT", "method": "Godot PNG decoded raw RGBA alpha; no image writing/editing; source versions separate", "clips": records}, "\t"))
	output.close()
	quit(0)
