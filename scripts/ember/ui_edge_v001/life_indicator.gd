extends Control
## 横向生命槽。轮廓和填充独立，损失生命只隐藏填充，保留空槽。

const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
var life: int = 2
var max_life: int = 3
var _title: Label
var _count: Label
var _slots: Array[Control] = []
var _slot_budget: int = 6

func _ready() -> void:
	STYLE.prepare(self)
	_title = STYLE.label(self, "生命", 20)
	_count = STYLE.label(self, "", 16)
	STYLE.add_world_text_outline(_title)
	STYLE.add_world_text_outline(_count)
	_count.position = Vector2(0, 70)
	_rebuild()

func set_data(current: int, maximum: int = 3) -> void:
	var next_maximum := maxi(0, maximum)
	var next_life := clampi(current, 0, next_maximum)
	# 能量等其他HUD字段逐帧变化时，不重复更新未变化的生命组件。
	if next_maximum == max_life and next_life == life:
		return
	max_life = next_maximum
	life = next_life
	if _title != null:
		_rebuild()

func set_slot_budget(max_slots: int = 6) -> void:
	# HUD按顶部可用宽度分配0..6格；空间不足时数字保留完整生命值。
	var next_budget := clampi(max_slots, 0, 6)
	if next_budget == _slot_budget:
		return
	_slot_budget = next_budget
	if _title != null:
		_rebuild()

func _rebuild() -> void:
	# 保留已有槽节点：生命变化只切换fill，只有显示格数变化才增删节点。
	var displayed_count := mini(max_life, _slot_budget)
	while _slots.size() > displayed_count:
		var removed_slot: Control = _slots.pop_back()
		removed_slot.free()
	while _slots.size() < displayed_count:
		var index := _slots.size()
		var slot := Control.new()
		slot.position = Vector2(index * 32, 32)
		slot.size = Vector2(24, 32)
		STYLE.prepare(slot)
		add_child(slot)
		var fill := STYLE.texture(slot, "life_fill_24x32")
		fill.size = slot.size
		var outline := STYLE.texture(slot, "life_outline_24x32")
		outline.size = slot.size
		_slots.append(slot)
	for index in range(_slots.size()):
		_slots[index].get_child(0).visible = index < life
	_count.text = "%d / %d" % [life, max_life] if max_life > displayed_count else ("—" if max_life == 0 else "")
	_count.position.y = 70 if displayed_count > 0 else 32
	# 文本变短时同步收回旧宽度，避免大生命值留下超出组件的空白子矩形。
	_count.size = Vector2(_count.get_combined_minimum_size().x, 24)
	var required_width := maxf(64, displayed_count * 32 - 8)
	if not _count.text.is_empty():
		required_width = maxf(required_width, _count.get_combined_minimum_size().x)
	custom_minimum_size = Vector2(required_width, _count.position.y + 24 if not _count.text.is_empty() else 64)
