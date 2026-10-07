extends Node2D
const Rig = preload("res://fixed_rig.gd")
var rigs: Array = []
var time := 0.0
var paused := false
var frame_index := 0
var status: Label
func _ready() -> void:
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	text("PATROL MOVE v003 | FIXED PART CANDIDATE | NOT APPROVED",Vector2(24,20),24)
	status=text("8 FPS | Space pause | arrows step | R restart",Vector2(24,60),18)
	for index in range(8):
		var rig := Rig.new()
		add_child(rig)
		rig.pose(index)
		rig.position=Vector2(20+(index%4)*310,110+(index/4)*220)-Vector2(40,45)*3
		rig.scale=Vector2(3,3)
		text("f%02d"%index,Vector2(40+(index%4)*310,115+(index/4)*220),16)
	for index in range(2):
		var rig := Rig.new()
		add_child(rig)
		rig.position=Vector2(350+index*380,575)-Vector2(40,45)*3
		rig.scale=Vector2(3,3)
		rigs.append(rig)
	text("8 FPS",Vector2(355,570),18)
	text("1 FPS",Vector2(735,570),18)
func _process(delta: float) -> void:
	if not paused:
		time+=delta
		frame_index=int(time*8)%8
	rigs[0].pose(frame_index)
	rigs[1].pose(frame_index if paused else int(time)%8)
	status.text=("PAUSED" if paused else "PLAYING")+" f%02d | Space pause | arrows step | R restart"%frame_index
func _unhandled_key_input(event: InputEvent) -> void:
	if not event.is_pressed(): return
	if event.keycode==KEY_SPACE: paused=not paused
	if event.keycode==KEY_RIGHT: paused=true; frame_index=(frame_index+1)%8
	if event.keycode==KEY_LEFT: paused=true; frame_index=posmod(frame_index-1,8)
	if event.keycode==KEY_R: time=0; frame_index=0
	if event.keycode==KEY_ESCAPE: get_tree().quit()
func text(value: String,position_value: Vector2,size: int) -> Label:
	var label:=Label.new()
	label.text=value
	label.position=position_value
	label.add_theme_font_size_override("font_size",size)
	add_child(label)
	return label
