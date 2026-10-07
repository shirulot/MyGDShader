extends SceneTree
## 只拼装已认可的小图，生成固定格布局参考；不重新绘画或改色。
## 帧姿态变化随后全部交由 imagegen 生成。

func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var source_dir := ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	var specs: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(source_dir + "/sequence_specs_v001.json"))
	DirAccess.make_dir_recursive_absolute(source_dir + "/templates")
	DirAccess.make_dir_recursive_absolute(source_dir + "/masters")
	DirAccess.make_dir_recursive_absolute(source_dir + "/prompts")
	DirAccess.make_dir_recursive_absolute(source_dir + "/qa")
	var units: Dictionary = {}
	var records: Array = []
	for unit: Dictionary in specs.units:
		var original := Image.load_from_file(str(unit.reference_scale_example))
		assert(original != null and not original.is_empty())
		original.convert(Image.FORMAT_RGBA8)
		var canonical := Image.create(128, 128, false, Image.FORMAT_RGBA8)
		canonical.fill(Color.TRANSPARENT)
		var offset := Vector2i(64 - int(unit.source_pivot[0]), 104 - int(unit.source_pivot[1]))
		# 侦察机的固定锚点是地面投影，正常姿态留24原生像素悬浮高度。
		if str(unit.id) == "enemy_scout_drone":
			offset.y -= 24
		canonical.blit_rect(original, Rect2i(Vector2i.ZERO, original.get_size()), offset)
		assert(canonical.save_png(source_dir + "/templates/" + str(unit.id) + "_canonical_down_v001.png") == OK)
		units[str(unit.id)] = canonical
	for clip: Dictionary in specs.clips:
		var atlas := Image.create(int(clip.columns) * 128, int(clip.rows) * 128, false, Image.FORMAT_RGBA8)
		atlas.fill(Color.TRANSPARENT)
		var base: Image = units[str(clip.unit_id)]
		for frame_index in range(int(clip.frame_count)):
			var position := Vector2i((frame_index % int(clip.columns)) * 128, (frame_index / int(clip.columns)) * 128)
			atlas.blit_rect(base, Rect2i(Vector2i.ZERO, Vector2i(128, 128)), position)
		# 整页统一放大4倍作为布局母板；各格画布、接地点与本体体量不变。
		atlas.resize(atlas.get_width() * 4, atlas.get_height() * 4, Image.INTERPOLATE_NEAREST)
		assert(atlas.save_png(str(clip.template_path)) == OK)
		records.append({"id": clip.id, "template": clip.template_path, "size": [atlas.get_width(), atlas.get_height()], "status": "STATIC_LAYOUT_ONLY_NOT_ANIMATION"})
	var report := FileAccess.open(source_dir + "/qa/template_registration_v001.json", FileAccess.WRITE)
	report.store_string(JSON.stringify({"status": "PASS", "canvas": [128,128], "pivot": [64,104], "copies_existing_accepted_RGBA": true, "colour_editing": "none", "templates": records}, "\t"))
	report.close()
	print("ENEMY_SEQUENCE_TEMPLATES_READY ", records.size())
	quit(0)
