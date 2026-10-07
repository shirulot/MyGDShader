extends Node2D
## 南西动作小样：采集结束回到同方向idle，不向主工程添加玩法。
var robot: AnimatedSprite2D
var native: AnimatedSprite2D
var info: Label

func _ready()->void:
	var frames=load("res://robot_action_pilot_v011.tres") as SpriteFrames
	robot=_sprite(frames,4,Vector2(440,490));native=_sprite(frames,1,Vector2(800,365))
	var title=Label.new();title.text="SW ACTION PILOT — 1 Idle / 2 Collect / 3 Walk / Space Pause";title.position=Vector2(24,24);add_child(title)
	info=Label.new();info.position=Vector2(24,580);add_child(info)
	robot.animation_finished.connect(_on_finished)
	_play("idle_down_left")

func _sprite(frames:SpriteFrames,size:int,position_at:Vector2)->AnimatedSprite2D:
	var s=AnimatedSprite2D.new();s.sprite_frames=frames;s.centered=false;s.offset=Vector2(-32,-80);s.position=position_at;s.scale=Vector2.ONE*size;s.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;add_child(s);return s

func _play(clip:String)->void:
	robot.play(clip);robot.frame=0;native.play(clip);native.frame=0

func _on_finished()->void:
	if robot.animation=="collect_down_left":_play("idle_down_left")

func _unhandled_key_input(event:InputEvent)->void:
	if not event is InputEventKey:return
	if not event.is_pressed() or event.is_echo():return
	if event.keycode==KEY_1:_play("idle_down_left")
	elif event.keycode==KEY_2:_play("collect_down_left")
	elif event.keycode==KEY_3:_play("walk_down_left")
	elif event.keycode==KEY_SPACE:
		if robot.is_playing():robot.pause();native.pause()
		else:robot.play();native.play()

func _process(_delta:float)->void:
	native.frame=robot.frame
	info.text="%s / F%02d — fixed root (32, 80); new idle/collect pending art review"%[robot.animation,robot.frame]
