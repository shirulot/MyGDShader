extends SceneTree
## 敌人序列的固定网格导出器，只切图和最近邻缩放，不重绘或修补美术。
## 在独立预览工程运行，避免正式游戏 Game 单例被载入。
## Godot --headless --path <preview-project> --script <本脚本绝对路径>
##       -- --workspace=<正式工作区> --ids=enemy_patrol_idle_down,enemy_cutter
## --ids 同时接受单位 ID 和 clip ID；省略时处理全部规格。

const ASSET_ROOT := "res://assets/ember/characters/enemies_v001/"
const ALPHA_THRESHOLD := 0.1
const REVISION := "enemy_sequences_v001"
var workspace := ""
var output_root := ""
var failures: Array[String] = []
var warnings: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	workspace = _argument("workspace", ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir().get_base_dir().get_base_dir().get_base_dir())
	workspace = workspace.replace("\\", "/").trim_suffix("/")
	var specs_path := workspace + "/art-source/ember/enemy-sequences-v001/sequence_specs_v001.json"
	var specs_variant: Variant = JSON.parse_string(FileAccess.get_file_as_string(specs_path))
	if not specs_variant is Dictionary:
		push_error("Cannot read enemy sequence specification: " + specs_path)
		quit(1)
		return
	var specs: Dictionary = specs_variant
	if "--measure-candidates" in OS.get_cmdline_user_args():
		_measure_candidates(specs)
		quit(0 if failures.is_empty() else 1)
		return
	if "--measure" in OS.get_cmdline_user_args():
		_measure_source_grids(specs)
		quit(0 if failures.is_empty() else 1)
		return
	output_root = workspace + "/assets/ember/characters/enemies_v001/"
	DirAccess.make_dir_recursive_absolute(output_root)
	var catalog_path := output_root + "sequence_catalog_v001.json"
	var previous: Variant = JSON.parse_string(FileAccess.get_file_as_string(catalog_path)) if FileAccess.file_exists(catalog_path) else {}
	var entries_by_id: Dictionary = {}
	if previous is Dictionary:
		for item: Dictionary in previous.get("clips", []):
			entries_by_id[str(item.id)] = item
	var requested := _argument("ids", "").split(",", false)
	var processed: Array[String] = []
	var unit_specs: Dictionary = {}
	for unit: Dictionary in specs.get("units", []):
		unit_specs[str(unit.id)] = unit
	for clip: Dictionary in specs.get("clips", []):
		var id := str(clip.id)
		if not requested.is_empty() and not id in requested and not str(clip.unit_id) in requested:
			continue
		var entry := _export_clip(clip, unit_specs.get(str(clip.unit_id), {}), specs)
		entries_by_id[id] = entry
		processed.append(id)
		print("ENEMY_SEQUENCE_EXPORTED ", id, " ", entry.technical_status)
	if processed.is_empty():
		failures.append("No matching clips processed.")
	var entries: Array = []
	# 目录顺序沿用规格中的单位、动作顺序，不依靠文件名排序。
	for clip: Dictionary in specs.get("clips", []):
		if entries_by_id.has(str(clip.id)):
			entries.append(entries_by_id[str(clip.id)])
	for entry: Dictionary in entries:
		if str(entry.technical_status) != "PASS" and not str(entry.id) in processed:
			failures.append("Earlier catalog clip still requires attention: " + str(entry.id))
	var resources: Array = []
	for unit: Dictionary in specs.get("units", []):
		var unit_clips: Array = []
		for entry: Dictionary in entries:
			if str(entry.unit_id) == str(unit.id) and str(entry.technical_status) == "PASS":
				unit_clips.append(entry)
		if not unit_clips.is_empty():
			resources.append(_write_unit_resources(unit, unit_clips, specs))
	var catalog := {
		"revision": REVISION, "technical_status": "PASS" if failures.is_empty() else "FAIL",
		"visual_acceptance": "PENDING_ART_REVIEW", "scope": specs.get("scope", ""),
		"engine": Engine.get_version_info().string, "canvas_px": specs.canvas_px,
		"pivot_px": specs.pivot_px, "source_specs": specs_path,
		"source_specs_sha256": FileAccess.get_sha256(specs_path),
		"tool_sha256": FileAccess.get_sha256(workspace + "/tools/export_enemy_sequences_v001.gd"),
		"processing": "One nearest-neighbour resize of whole source atlas to explicit clip cell_canvas_px, fixed cells, common clip offset blit to 128px canvases; unchanged source RGBA",
		"per_frame_crop_resize_reposition": "NONE", "repaint_recolour_matte": "NONE",
		"root_motion": "NONE", "gameplay_ai_damage_collision": "NOT_INCLUDED",
		"alpha_bbox_threshold": ALPHA_THRESHOLD, "processed_ids": processed,
		"planned_clip_count": specs.clips.size(), "catalog_clip_count": entries.size(),
		"batch_complete": entries.size() == specs.clips.size(),
		"clips": entries, "unit_resources": resources, "warnings": warnings, "failures": failures
	}
	_write_json(catalog_path, catalog)
	_write_json(workspace + "/art-source/ember/enemy-sequences-v001/qa/sequence_export_v001.json", catalog)
	print("ENEMY_SEQUENCE_EXPORT_", catalog.technical_status, " ", processed.size(), " clips / ", entries.size(), " catalog clips")
	for failure: String in failures:
		printerr(failure)
	quit(0 if failures.is_empty() else 1)


func _export_clip(clip: Dictionary, unit: Dictionary, specs: Dictionary) -> Dictionary:
	var id := str(clip.id)
	var unit_id := str(clip.unit_id)
	var action := str(clip.action)
	var direction := str(clip.direction)
	var frame_count := int(clip.frame_count)
	var columns := int(clip.columns)
	var rows := int(clip.rows)
	var canvas := Vector2i(int(specs.canvas_px[0]), int(specs.canvas_px[1]))
	var source_path := _resolve_workspace_path(str(clip.master_path), specs)
	var entry := {
		"id": id, "unit_id": unit_id, "name": clip.get("name", unit_id),
		"action": action, "direction": direction, "animation": action + "_" + direction,
		"frame_count": frame_count, "columns": columns, "rows": rows,
		"fps": clip.fps, "loop": clip.loop, "events": clip.get("events", []),
		"canvas_px": specs.canvas_px, "pivot_px": specs.pivot_px,
		"source_master": source_path, "prompt_path": _resolve_workspace_path(str(clip.get("prompt_path", "")), specs),
		"technical_status": "FAIL", "visual_acceptance": "PENDING_ART_REVIEW",
		"source_part_identity": unit.get("identity", ""), "frame_metrics": [], "warnings": []
	}
	if not id.is_valid_identifier() or not unit_id.is_valid_identifier() or not action.is_valid_identifier() or not direction.is_valid_identifier():
		return _reject(entry, "Invalid stable unit/clip ID.")
	if frame_count <= 0 or columns <= 0 or rows <= 0 or frame_count != columns * rows:
		return _reject(entry, "Frame count must exactly match full uniform grid.")
	if not FileAccess.file_exists(source_path):
		return _reject(entry, "Source master is not available: " + source_path)
	var atlas := Image.new()
	if atlas.load_png_from_buffer(FileAccess.get_file_as_bytes(source_path)) != OK or atlas.is_empty():
		return _reject(entry, "Cannot read source PNG.")
	entry["source_sha256"] = FileAccess.get_sha256(source_path)
	entry["source_size_px"] = [atlas.get_width(), atlas.get_height()]
	var source_cell := Vector2i(int(specs.source_cell_px[0]), int(specs.source_cell_px[1]))
	var expected_source := Vector2i(columns * source_cell.x, rows * source_cell.y)
	entry["expected_source_size_px"] = [expected_source.x, expected_source.y]
	entry["source_size_matches_template"] = atlas.get_size() == expected_source
	var registration: Dictionary = clip.get("registration", {})
	if registration.is_empty():
		return _reject(entry, "Explicit clip registration is required before resource export. Use --measure first; do not publish uncalibrated 128px cells.")
	if int(registration.get("reference_frame", 0)) != 0:
		return _reject(entry, "This batch uses only f00 for a common clip registration reference.")
	var scaled_cell := Vector2i(int(registration.get("cell_canvas_px", [128, 128])[0]), int(registration.get("cell_canvas_px", [128, 128])[1]))
	var offset := Vector2i(int(registration.get("offset_px", [0, 0])[0]), int(registration.get("offset_px", [0, 0])[1]))
	if scaled_cell.x <= 0 or scaled_cell.y <= 0 or scaled_cell.x != scaled_cell.y:
		return _reject(entry, "Clip registration must use positive uniform square cell_canvas_px.")
	entry["registration"] = registration
	entry["registration_status"] = "EXPLICIT_CLIP_COMMON_TRANSFORM" if not registration.is_empty() else "UNREGISTERED_DIAGNOSTIC"
	entry["whole_atlas_resize_ratio"] = [float(columns * scaled_cell.x) / atlas.get_width(), float(rows * scaled_cell.y) / atlas.get_height()]
	entry["normalized_cell_common_scale"] = [float(scaled_cell.x) / canvas.x, float(scaled_cell.y) / canvas.y]
	entry["common_frame_offset_px"] = [offset.x, offset.y]
	if atlas.get_size() != expected_source:
		entry.warnings.append("Source dimensions differ from 512px-per-cell template. Inspect grid/registration; no per-frame correction was applied.")
	# 全页只执行一次最近邻缩放。此后完整格切出，并统一 offset 放入透明画布。
	# offset/scale 由同一个参考 f00 登记；其余帧不按 bbox 修正，保留来源抖动。
	atlas.convert(Image.FORMAT_RGBA8)
	atlas.resize(columns * scaled_cell.x, rows * scaled_cell.y, Image.INTERPOLATE_NEAREST)
	var native_atlas := Image.create(columns * canvas.x, rows * canvas.y, false, Image.FORMAT_RGBA8)
	native_atlas.fill(Color.TRANSPARENT)
	var unit_folder := output_root + unit_id + "/"
	var frames_folder := unit_folder + "frames/" + action + "_" + direction + "/"
	DirAccess.make_dir_recursive_absolute(frames_folder)
	var atlas_path := unit_folder + action + "_" + direction + "_v001.png"
	entry["atlas"] = ASSET_ROOT + unit_id + "/" + action + "_" + direction + "_v001.png"
	entry["atlas_file"] = atlas_path
	entry["atlas_size_px"] = [native_atlas.get_width(), native_atlas.get_height()]
	var previous_hash := ""
	var first: Dictionary = {}
	var duplicate_pairs: Array = []
	var clip_errors: Array[String] = []
	var output_frames: Array = []
	for index in range(frame_count):
		var grid := Vector2i(index % columns, floori(float(index) / columns))
		var region := Rect2i(grid * canvas, canvas)
		var scaled_region := Rect2i(grid * scaled_cell, scaled_cell)
		var scaled_frame := atlas.get_region(scaled_region)
		var scaled_metric := _frame_metrics(scaled_frame)
		var image := Image.create(canvas.x, canvas.y, false, Image.FORMAT_RGBA8)
		image.fill(Color.TRANSPARENT)
		image.blit_rect(scaled_frame, Rect2i(Vector2i.ZERO, scaled_cell), offset)
		native_atlas.blit_rect(image, Rect2i(Vector2i.ZERO, canvas), grid * canvas)
		var frame_path := frames_folder + ("f%02d.png" % index)
		if image.save_png(frame_path) != OK:
			clip_errors.append("Cannot save frame " + str(index))
		var metric := _frame_metrics(image)
		metric["frame"] = index
		metric["row"] = grid.y
		metric["column"] = grid.x
		metric["atlas_region_px"] = [region.position.x, region.position.y, region.size.x, region.size.y]
		metric["scaled_source_cell_bbox_px"] = scaled_metric.visible_bbox_px
		metric["clipped_nonzero_alpha_pixels"] = int(scaled_metric.nonzero_alpha_pixels) - int(metric.nonzero_alpha_pixels)
		metric["clipped_visible_alpha_pixels"] = int(scaled_metric.visible_pixels) - int(metric.visible_pixels)
		metric["baseline_bottom_px"] = int(metric.visible_bbox_px[1]) + int(metric.visible_bbox_px[3])
		metric["baseline_delta_from_pivot_px"] = int(metric.baseline_bottom_px) - int(specs.pivot_px[1])
		metric["png_sha256"] = FileAccess.get_sha256(frame_path)
		metric["rgba_sha256"] = _bytes_sha256(image.get_data())
		metric["events"] = _events_at(clip.get("events", []), index)
		if index == 0:
			first = metric
		metric["bbox_delta_from_f00_px"] = _bbox_delta(metric.visible_bbox_px, first.visible_bbox_px)
		metric["bbox_extent_ratio_from_f00"] = _extent_ratio(metric.visible_bbox_px, first.visible_bbox_px)
		metric["visible_area_ratio_from_f00"] = float(metric.visible_pixels) / maxi(1, int(first.visible_pixels))
		metric["centroid_delta_from_f00_px"] = [float(metric.alpha_centroid_px[0]) - float(first.alpha_centroid_px[0]), float(metric.alpha_centroid_px[1]) - float(first.alpha_centroid_px[1])]
		if int(metric.visible_pixels) == 0:
			clip_errors.append("Empty frame f%02d." % index)
		if int(metric.fully_transparent_pixels) == 0:
			clip_errors.append("Frame f%02d has no fully transparent pixel; opaque background suspected." % index)
		if bool(metric.touches_canvas_border):
			clip_errors.append("Frame f%02d visible pixels touch fixed canvas boundary; clipping requires art review." % index)
		if int(metric.clipped_visible_alpha_pixels) > 0:
			clip_errors.append("Frame f%02d common transform clips %d visible alpha>=0.1 pixels; inspect entity boundary and whole clip registration." % [index, int(metric.clipped_visible_alpha_pixels)])
		elif int(metric.clipped_nonzero_alpha_pixels) > 0:
			entry.warnings.append("Frame f%02d common canvas omits %d alpha<0.1 source-fringe pixels outside the canvas; recorded separately from entity clipping, source master unchanged." % [index, int(metric.clipped_nonzero_alpha_pixels)])
		if str(metric.rgba_sha256) == previous_hash:
			duplicate_pairs.append([index - 1, index])
		previous_hash = str(metric.rgba_sha256)
		entry.frame_metrics.append(metric)
		output_frames.append({"frame": index, "path": ASSET_ROOT + unit_id + "/frames/" + action + "_" + direction + "/" + ("f%02d.png" % index), "sha256": metric.png_sha256})
	entry["frames"] = output_frames
	if native_atlas.save_png(atlas_path) != OK:
		return _reject(entry, "Cannot save native atlas.")
	entry["atlas_sha256"] = FileAccess.get_sha256(atlas_path)
	entry["adjacent_exact_duplicate_pairs"] = duplicate_pairs
	var row_baselines: Array = []
	for row_index in range(rows):
		var bottoms: Array = []
		for metric: Dictionary in entry.frame_metrics:
			if int(metric.row) == row_index:
				bottoms.append(int(metric.baseline_bottom_px))
		row_baselines.append({"row": row_index, "frame_bottoms_px": bottoms,
			"minimum_bottom_px": bottoms.min(), "maximum_bottom_px": bottoms.max(),
			"delta_from_f00_range_px": [int(bottoms.min()) - int(first.baseline_bottom_px), int(bottoms.max()) - int(first.baseline_bottom_px)],
			"delta_from_pivot_range_px": [int(bottoms.min()) - int(specs.pivot_px[1]), int(bottoms.max()) - int(specs.pivot_px[1])]})
	entry["row_baseline_summary"] = row_baselines
	entry["loop_end_start_rgba_equal"] = str(entry.frame_metrics[frame_count - 1].rgba_sha256) == str(first.rgba_sha256)
	entry["gross_extent_metrics_notice"] = "BBox/centroid changes include intended limb motion or death collapse. They flag visual review and do not prove rigid-body scale drift. No automatic art correction."
	if not duplicate_pairs.is_empty():
		entry.warnings.append("Exact adjacent repeated frames recorded. Death hold may be intentional; inspect motion manually.")
	entry["technical_status"] = "PASS" if clip_errors.is_empty() else "FAIL"
	entry["failures"] = clip_errors
	for message: String in clip_errors:
		failures.append(id + ": " + message)
	for message: String in entry.warnings:
		warnings.append(id + ": " + message)
	_write_json(unit_folder + action + "_" + direction + "_metadata_v001.json", entry)
	return entry


func _frame_metrics(image: Image) -> Dictionary:
	# 统计 alpha，不阈值删除像素。0.1 只用于可见范围诊断。
	var data := image.get_data()
	var width := image.get_width()
	var height := image.get_height()
	var minimum := Vector2i(width, height)
	var maximum := Vector2i(-1, -1)
	var visible := 0
	var transparent := 0
	var partial := 0
	var alpha_weight := 0.0
	var weighted_position := Vector2.ZERO
	var threshold := ceili(ALPHA_THRESHOLD * 255.0)
	for pixel in range(width * height):
		var alpha := int(data[pixel * 4 + 3])
		if alpha == 0:
			transparent += 1
		elif alpha < 255:
			partial += 1
		if alpha < threshold:
			continue
		var point := Vector2i(pixel % width, floori(float(pixel) / width))
		minimum.x = mini(minimum.x, point.x)
		minimum.y = mini(minimum.y, point.y)
		maximum.x = maxi(maximum.x, point.x)
		maximum.y = maxi(maximum.y, point.y)
		visible += 1
		alpha_weight += alpha
		weighted_position += Vector2(point) * alpha
	var bbox := [0, 0, 0, 0] if visible == 0 else [minimum.x, minimum.y, maximum.x - minimum.x + 1, maximum.y - minimum.y + 1]
	var centroid := Vector2.ZERO if alpha_weight == 0 else weighted_position / alpha_weight
	return {"visible_bbox_px": bbox, "visible_pixels": visible, "nonzero_alpha_pixels": width * height - transparent, "fully_transparent_pixels": transparent,
		"partial_alpha_pixels": partial, "partial_alpha_fraction": float(partial) / (width * height),
		"alpha_centroid_px": [centroid.x, centroid.y],
		"touches_canvas_border": visible > 0 and (minimum.x == 0 or minimum.y == 0 or maximum.x == width - 1 or maximum.y == height - 1)}


func _measure_source_grids(specs: Dictionary) -> void:
	# 诊断模式只输出 QA 数值，不把未标定来源发布为正式资源。
	var requested := _argument("ids", "").split(",", false)
	var path := workspace + "/art-source/ember/enemy-sequences-v001/qa/source_grid_measurement_v001.json"
	var entries_by_id: Dictionary = {}
	if FileAccess.file_exists(path):
		var previous: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		if previous is Dictionary:
			for record: Dictionary in previous.get("clips", []):
				entries_by_id[str(record.id)] = record
	var canonical: Array = []
	for unit: Dictionary in specs.units:
		var canonical_path := workspace + "/art-source/ember/enemy-sequences-v001/templates/" + str(unit.id) + "_canonical_down_v001.png"
		if not FileAccess.file_exists(canonical_path):
			continue
		var image := Image.load_from_file(canonical_path)
		image.convert(Image.FORMAT_RGBA8)
		canonical.append({"unit_id": unit.id, "path": canonical_path, "metrics": _frame_metrics(image)})
	for clip: Dictionary in specs.clips:
		if not requested.is_empty() and not str(clip.id) in requested and not str(clip.unit_id) in requested:
			continue
		var source_path := _resolve_workspace_path(str(clip.master_path), specs)
		if not FileAccess.file_exists(source_path):
			continue
		var image := Image.load_from_file(source_path)
		if image == null or image.is_empty():
			failures.append("Cannot measure " + str(clip.id))
			continue
		var source_size := image.get_size()
		image.convert(Image.FORMAT_RGBA8)
		image.resize(int(clip.columns) * 128, int(clip.rows) * 128, Image.INTERPOLATE_NEAREST)
		var frames: Array = []
		for index in range(int(clip.frame_count)):
			var region := Rect2i((index % int(clip.columns)) * 128, floori(float(index) / int(clip.columns)) * 128, 128, 128)
			var metric := _frame_metrics(image.get_region(region))
			metric["frame"] = index
			metric["row"] = floori(float(index) / int(clip.columns))
			metric["baseline_bottom_px"] = int(metric.visible_bbox_px[1]) + int(metric.visible_bbox_px[3])
			frames.append(metric)
		entries_by_id[str(clip.id)] = {"id": clip.id, "source_master": source_path, "source_sha256": FileAccess.get_sha256(source_path), "source_size_px": [source_size.x, source_size.y], "diagnostic_cell_px": [128, 128], "registration": "NONE", "frames": frames}
		print("ENEMY_SOURCE_MEASURED ", clip.id, " f00 bbox ", frames[0].visible_bbox_px)
	var records: Array = []
	for clip: Dictionary in specs.clips:
		if entries_by_id.has(str(clip.id)):
			records.append(entries_by_id[str(clip.id)])
	_write_json(path, {"status": "DIAGNOSTIC_ONLY", "method": "Whole source grid nearest resize to 128px cells, then fixed-grid alpha metrics. No production frames written.", "canonical_units": canonical, "clips": records, "failures": failures})


func _measure_candidates(specs: Dictionary) -> void:
	## 只读候选，规格与正式 PNG 都不改；所有候选帧共用 f00 得出的倍率/偏移。
	var source_dir := workspace + "/art-source/ember/enemy-sequences-v001/"
	var candidates: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(source_dir + "qa/revision_candidates_v001.json"))
	var selected_catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(workspace + "/assets/ember/characters/enemies_v001/sequence_catalog_v001.json"))
	var results: Array = []
	for candidate: Dictionary in candidates.candidates:
		var clip: Dictionary = {}
		for item: Dictionary in specs.clips:
			if str(item.id) == str(candidate.id):
				clip = item
				break
		if clip.is_empty():
			failures.append("Unknown candidate ID " + str(candidate.id))
			continue
		var canonical := Image.load_from_file(source_dir + "templates/" + str(clip.unit_id) + "_canonical_down_v001.png")
		canonical.convert(Image.FORMAT_RGBA8)
		var canonical_bbox: Array = _frame_metrics(canonical).visible_bbox_px
		var raw := Image.load_from_file(str(candidate.master_path))
		if raw == null or raw.is_empty():
			failures.append("Cannot read candidate " + str(candidate.master_path))
			continue
		raw.convert(Image.FORMAT_RGBA8)
		var raw_size := raw.get_size()
		var diagnostic: Image = raw.duplicate()
		diagnostic.resize(int(clip.columns) * 128, int(clip.rows) * 128, Image.INTERPOLATE_NEAREST)
		var reference: Dictionary = _frame_metrics(diagnostic.get_region(Rect2i(0, 0, 128, 128)))
		var bbox: Array = reference.visible_bbox_px
		var cell := floori(128.0 * minf(float(canonical_bbox[2]) / maxi(1, int(bbox[2])), float(canonical_bbox[3]) / maxi(1, int(bbox[3]))))
		var ratio := float(cell) / 128.0
		var offset := Vector2i(roundi(float(canonical_bbox[0]) + float(canonical_bbox[2]) / 2.0 - (float(bbox[0]) + float(bbox[2]) / 2.0) * ratio), roundi(float(canonical_bbox[1]) + float(canonical_bbox[3]) - (float(bbox[1]) + float(bbox[3])) * ratio))
		var registration := {"cell_canvas_px": [cell, cell], "offset_px": [offset.x, offset.y], "reference_frame": 0, "reference_bbox_px": bbox, "target_canonical_bbox_px": canonical_bbox}
		# 这份临时 Image 与 export 相同：直接从 raw 整页一次 resize，再统一注册。
		var scaled: Image = raw.duplicate()
		scaled.resize(int(clip.columns) * cell, int(clip.rows) * cell, Image.INTERPOLATE_NEAREST)
		var metrics: Array = []
		var bottoms: Array = []
		var source_edge_frames: Array = []
		var clipped_visible := 0
		for index in range(int(clip.frame_count)):
			var col := index % int(clip.columns)
			var row := floori(float(index) / int(clip.columns))
			var source_metric := _frame_metrics(diagnostic.get_region(Rect2i(col * 128, row * 128, 128, 128)))
			var border := _raw_cell_boundary(raw, col, row, int(clip.columns), int(clip.rows))
			var frame := scaled.get_region(Rect2i(col * cell, row * cell, cell, cell))
			var original_metric := _frame_metrics(frame)
			var native := Image.create(128, 128, false, Image.FORMAT_RGBA8)
			native.fill(Color.TRANSPARENT)
			native.blit_rect(frame, Rect2i(0, 0, cell, cell), offset)
			var metric := _frame_metrics(native)
			metric["frame"] = index
			metric["row"] = row
			metric["source_unregistered_bbox_128_px"] = source_metric.visible_bbox_px
			metric["source_boundary"] = border
			metric["baseline_bottom_px"] = int(metric.visible_bbox_px[1]) + int(metric.visible_bbox_px[3])
			metric["delta_from_ground_anchor_px"] = int(metric.baseline_bottom_px) - 104
			metric["visible_pixels_clipped_by_common_transform"] = int(original_metric.visible_pixels) - int(metric.visible_pixels)
			clipped_visible += int(metric.visible_pixels_clipped_by_common_transform)
			if int(border.visible_boundary_pixels) > 0:
				source_edge_frames.append(index)
			metrics.append(metric)
			bottoms.append(int(metric.baseline_bottom_px))
		var rows: Array = []
		for row_index in range(int(clip.rows)):
			var row_bottoms: Array = []
			for metric: Dictionary in metrics:
				if int(metric.row) == row_index:
					row_bottoms.append(int(metric.baseline_bottom_px))
			rows.append({"row": row_index, "native_bottoms_px": row_bottoms, "median_bottom_px": _median(row_bottoms), "median_delta_from_f00_px": _median(row_bottoms) - float(bottoms[0])})
		var blockers: Array = []
		if not source_edge_frames.is_empty():
			blockers.append("Visible entity pixels reach raw fixed-cell boundary; may already be clipped by source grid. Inspect source outline; common transform cannot restore missing pixels.")
		if clipped_visible > 0:
			blockers.append("Common registration clips visible entity pixels from target 128 canvas.")
		if str(clip.unit_id) == "enemy_scout_drone" and str(clip.action) == "death" and absi(int(bottoms.back()) - 104) > 1:
			blockers.append("Drone final wreck is not at ground anchor 104: bottom=" + str(bottoms.back()) + "; landing requirement failed.")
		if str(clip.action) in ["idle", "move"] and int(bottoms.max()) - int(bottoms.min()) > 2:
			blockers.append("Native visible-bottom range exceeds 2px; requires visual root/support registration review.")
		if str(clip.action) in ["attack", "hit"] and absi(int(bottoms.back()) - int(bottoms[0])) > 1:
			blockers.append("Last neutral/recovery bottom differs from f00 by more than 1px; transition requires art review.")
		var previous: Dictionary = {}
		for entry: Dictionary in selected_catalog.get("clips", []):
			if str(entry.id) == str(candidate.id):
				previous = entry
				break
		results.append({"id": candidate.id, "source_master": candidate.master_path,
			"source_sha256": FileAccess.get_sha256(str(candidate.master_path)), "source_size_px": [raw_size.x, raw_size.y],
			"registration_proposal": registration, "native_f00_bbox_px": metrics[0].visible_bbox_px,
			"native_bottoms_px": bottoms, "native_row_baselines": rows, "frame_metrics": metrics,
			"source_entity_boundary_frames": source_edge_frames, "visible_pixels_clipped_by_common_transform": clipped_visible,
			"current_selected_master": previous.get("source_master", ""),
			"current_selected_native_bottoms_px": previous.get("frame_metrics", []).map(func(item: Dictionary) -> int: return int(item.baseline_bottom_px)),
			"candidate_verdict": "NEEDS_ART_REVIEW" if blockers.is_empty() else "ART_REGISTRATION_BLOCKERS_REMAIN",
			"registration_acceptance": "NOT_GRANTED_BY_MEASUREMENT", "blockers": blockers})
		print("CANDIDATE_MEASURED ", candidate.id, " cell=", cell, " offset=", offset, " bottoms=", bottoms, " source_edge=", source_edge_frames)
	_write_json(source_dir + "qa/candidate_registration_review_v001.json", {"status": "READ_ONLY_CANDIDATE_DIAGNOSTIC", "candidates": results,
		"method": "Only f00-derived common scale/offset. Diagnostic images are in memory only; no PNG or spec writes. Raw alpha>=0.1 source-edge entity check. Not a registration PASS declaration.", "failures": failures})


func _raw_cell_boundary(image: Image, column: int, row: int, columns: int, rows: int) -> Dictionary:
	var x0 := floori(float(column * image.get_width()) / columns)
	var x1 := floori(float((column + 1) * image.get_width()) / columns)
	var y0 := floori(float(row * image.get_height()) / rows)
	var y1 := floori(float((row + 1) * image.get_height()) / rows)
	var sides := {"top": 0, "bottom": 0, "left": 0, "right": 0}
	for x in range(x0, x1):
		if image.get_pixel(x, y0).a >= ALPHA_THRESHOLD: sides.top += 1
		if image.get_pixel(x, y1 - 1).a >= ALPHA_THRESHOLD: sides.bottom += 1
	for y in range(y0, y1):
		if image.get_pixel(x0, y).a >= ALPHA_THRESHOLD: sides.left += 1
		if image.get_pixel(x1 - 1, y).a >= ALPHA_THRESHOLD: sides.right += 1
	return {"region_px": [x0, y0, x1 - x0, y1 - y0], "visible_alpha_threshold": ALPHA_THRESHOLD, "side_counts": sides,
		"visible_boundary_pixels": int(sides.top) + int(sides.bottom) + int(sides.left) + int(sides.right)}


func _median(values: Array) -> float:
	var ordered := values.duplicate()
	ordered.sort()
	var middle := floori(float(ordered.size()) / 2.0)
	if ordered.size() % 2 == 1:
		return float(ordered[middle])
	return (float(ordered[middle - 1]) + float(ordered[middle])) / 2.0


func _write_unit_resources(unit: Dictionary, clips: Array, specs: Dictionary) -> Dictionary:
	var unit_id := str(unit.id)
	var folder := output_root + unit_id + "/"
	var resource_path := ASSET_ROOT + unit_id + "/" + unit_id + "_frames_v001.tres"
	var scene_path := ASSET_ROOT + unit_id + "/" + unit_id + "_v001.tscn"
	var external := ""
	var subresources := ""
	var animations := PackedStringArray()
	var sub_count := 0
	for clip_index in range(clips.size()):
		var clip: Dictionary = clips[clip_index]
		var texture_id := "atlas_%02d" % clip_index
		external += '[ext_resource type="Texture2D" path="%s" id="%s"]\n' % [clip.atlas, texture_id]
		var textures := PackedStringArray()
		for index in range(int(clip.frame_count)):
			var sub_id := "frame_%02d_%02d" % [clip_index, index]
			var rect: Array = clip.frame_metrics[index].atlas_region_px
			subresources += '\n[sub_resource type="AtlasTexture" id="%s"]\natlas = ExtResource("%s")\nregion = Rect2(%d, %d, %d, %d)\nfilter_clip = true\n' % [sub_id, texture_id, int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])]
			textures.append('{"duration": 1.0, "texture": SubResource("%s")}' % sub_id)
			sub_count += 1
		animations.append('{"frames": [%s], "loop": %s, "name": &"%s", "speed": %.1f}' % [", ".join(textures), "true" if clip.loop else "false", clip.animation, float(clip.fps)])
	var resource_text := '[gd_resource type="SpriteFrames" load_steps=%d format=3]\n\n' % (1 + clips.size() + sub_count)
	resource_text += external + subresources + '\n[resource]\nanimations = [%s]\n' % ",\n".join(animations)
	_write_text(folder + unit_id + "_frames_v001.tres", resource_text)
	var default_animation := str(clips[0].animation)
	for clip: Dictionary in clips:
		if str(clip.animation) == "idle_down":
			default_animation = "idle_down"
	var pivot: Array = specs.pivot_px
	var scene_text := '[gd_scene load_steps=2 format=3]\n\n[ext_resource type="SpriteFrames" path="%s" id="1_frames"]\n\n[node name="%s" type="AnimatedSprite2D"]\ntexture_filter = 1\nsprite_frames = ExtResource("1_frames")\nanimation = &"%s"\ncentered = false\noffset = Vector2(%d, %d)\nmetadata/frame_canvas_px = Vector2i(128, 128)\nmetadata/pivot_px = Vector2i(%d, %d)\nmetadata/visual_acceptance = "PENDING_ART_REVIEW"\n' % [resource_path, unit_id, default_animation, -int(pivot[0]), -int(pivot[1]), int(pivot[0]), int(pivot[1])]
	_write_text(folder + unit_id + "_v001.tscn", scene_text)
	return {"unit_id": unit_id, "sprite_frames": resource_path, "sprite_frames_sha256": FileAccess.get_sha256(folder + unit_id + "_frames_v001.tres"), "scene": scene_path, "scene_sha256": FileAccess.get_sha256(folder + unit_id + "_v001.tscn"), "animation_count": clips.size(), "animation_names": clips.map(func(item: Dictionary) -> String: return str(item.animation))}


func _argument(name: String, fallback: String) -> String:
	var args := OS.get_cmdline_user_args()
	for index in range(args.size()):
		if args[index].begins_with("--" + name + "="):
			return args[index].trim_prefix("--" + name + "=")
		if args[index] == "--" + name and index + 1 < args.size():
			return args[index + 1]
	return fallback


func _resolve_workspace_path(value: String, specs: Dictionary) -> String:
	# 原规格保存完整来源路径；换目录解压后只替换工作区前缀，不猜素材文件名。
	var source_directory := str(specs.get("source_directory", "")).replace("\\", "/").trim_suffix("/")
	var suffix := "/art-source/ember/enemy-sequences-v001"
	var original_workspace := source_directory.trim_suffix(suffix) if source_directory.ends_with(suffix) else ""
	var normalized := value.replace("\\", "/")
	if not original_workspace.is_empty() and normalized.begins_with(original_workspace + "/"):
		return workspace + normalized.trim_prefix(original_workspace)
	return normalized


func _events_at(events: Array, frame: int) -> Array:
	var found: Array = []
	for event: Dictionary in events:
		if int(event.get("frame", -1)) == frame:
			found.append(str(event.get("name", "")))
	return found


func _bbox_delta(current: Array, first: Array) -> Array:
	return [int(current[0]) - int(first[0]), int(current[1]) - int(first[1]), int(current[2]) - int(first[2]), int(current[3]) - int(first[3])]


func _extent_ratio(current: Array, first: Array) -> Array:
	return [float(current[2]) / maxi(1, int(first[2])), float(current[3]) / maxi(1, int(first[3]))]


func _bytes_sha256(data: PackedByteArray) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(data)
	return context.finish().hex_encode()


func _reject(entry: Dictionary, message: String) -> Dictionary:
	entry["failures"] = [message]
	failures.append(str(entry.id) + ": " + message)
	return entry


func _write_json(path: String, data: Variant) -> void:
	_write_text(path, JSON.stringify(data, "\t"))


func _write_text(path: String, content: String) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		failures.append("Cannot write " + path)
		return
	file.store_string(content)
	file.close()
