extends SceneTree
## 只生成像素坐标诊断图；不修改原生角色母稿。
func _initialize() -> void:
	var original := Image.load_from_file("res://source/canonical.png")
	var zoom := original.get_region(Rect2i(40, 48, 48, 60))
	zoom.resize(576, 720, Image.INTERPOLATE_NEAREST)
	zoom.save_png("res://qa/canonical_detail_x12.png")
	quit()
