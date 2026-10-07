extends Node2D
## 06.2 的两个水面版本并排展示；具体效果仍由各自场景中的同一个 Shader 提供。

const VIEW_SIZE := Vector2i(1112, 680)


func _ready() -> void:
	# 项目平时使用 720×720。只在直接运行这个对比场景时调整当前窗口，
	# 不修改 project.godot；两个 512×512 图区在初始窗口中按 1:1 显示。
	# GPU 捕获把本场景放入 SubViewport，此时无需调整主窗口。
	if get_viewport() is Window:
		var window := get_window()
		window.content_scale_size = VIEW_SIZE
		window.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
		window.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP
		if DisplayServer.get_name() != "headless":
			DisplayServer.window_set_size(VIEW_SIZE, window.get_window_id())
