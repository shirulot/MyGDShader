extends Node2D
var actors:Array[AnimatedSprite2D]=[]
var finish_counts:Dictionary={}
var loop_counts:Dictionary={}
var seen:Dictionary={}
var elapsed:=0.0
func _ready() -> void:
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var frames:=load("res://output/cutter_actions_v010.tres") as SpriteFrames
	label("CUTTER v010 | ALL FIVE | FOUR LEGS + TWO TOOLS | PENDING TA",Vector2(20,16),24)
	label("Native PNG nearest | non-loop action holds 0.5 s then preview replays",Vector2(20,50),16)
	var row:=0
	for action:String in ["idle_down","move_down","attack_down","hit_down","death_down"]:
		label(action,Vector2(20,100+row*220),20)
		for column in range(2):
			var sprite:=AnimatedSprite2D.new()
			sprite.sprite_frames=frames
			sprite.centered=false
			sprite.offset=Vector2(-64,-104)
			sprite.position=Vector2(300+column*340,280+row*220)
			sprite.scale=Vector2(2,2)
			sprite.speed_scale=1.0 if column==0 else 1.0/frames.get_animation_speed(action)
			sprite.set_meta("key",action+("_normal" if column==0 else "_slow"))
			var key:String=sprite.get_meta("key")
			seen[key]=[]
			finish_counts[key]=0
			loop_counts[key]=0
			sprite.animation_finished.connect(func():
				finish_counts[key]+=1
				await get_tree().create_timer(0.5).timeout
				if is_instance_valid(sprite):
					sprite.stop()
					sprite.play(action)
			)
			sprite.animation_looped.connect(func(): loop_counts[key]+=1)
			add_child(sprite)
			sprite.play(action)
			actors.append(sprite)
			label("NORMAL" if column==0 else "1 FPS",Vector2(230+column*340,105+row*220),16)
		row+=1
func _process(delta:float)->void:
	elapsed+=delta
	for sprite in actors:
		var key:String=sprite.get_meta("key")
		if not seen[key].has(sprite.frame): seen[key].append(sprite.frame)
func label(value:String,position_value:Vector2,size:int)->void:
	var node:=Label.new()
	node.text=value
	node.position=position_value
	node.add_theme_font_size_override("font_size",size)
	add_child(node)


