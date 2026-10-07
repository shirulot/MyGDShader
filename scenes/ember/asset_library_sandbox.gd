extends Control
## 独立素材库预览：只调整本次预览窗口，不改 project.godot 或游戏状态。

func _ready() -> void:
	get_window().size = Vector2i(1440, 1040)
	get_window().content_scale_size = Vector2i(1440, 1040)
