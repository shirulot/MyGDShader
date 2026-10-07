extends Control
## 独立资源检查窗口；不修改游戏的主场景、Autoload 或课程练习。

const VIEW_SIZE := Vector2i(1440, 1040)

func _ready() -> void:
	get_window().size = VIEW_SIZE
	get_window().content_scale_size = VIEW_SIZE

func _process(_delta: float) -> void:
	# 普通运行时，鼠标就是检修灯。验收工具会关闭此回调以固定光源位置。
	var light := find_child("InspectionLight", true, false) as PointLight2D
	if light != null:
		light.global_position = get_global_mouse_position()
