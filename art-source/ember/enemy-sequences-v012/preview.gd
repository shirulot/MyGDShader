extends Node2D
## 统一同一地面锚点；左侧正常2×，右侧1FPS原生1×。单次资源结束后仅演示重播。
var seen:Dictionary={}
var finished:Dictionary={}
var loops:Dictionary={}
var actors:Array[AnimatedSprite2D]=[]
var elapsed:=0.0
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 label("EMBER | FOUR UNITS / FIVE ACTIONS | FROZEN PNG ASSEMBLY",Vector2(24,16),24)
 label("Each cell: NORMAL 2x + 1 FPS native | front/down only",Vector2(24,50),16)
 var units:Array=["enemy_patrol","enemy_tracked_heavy","enemy_cutter","enemy_scout_drone"]
 var names:Array=["PATROL","HEAVY","CUTTER","SCOUT"]
 var actions:Array=["idle_down","move_down","attack_down","hit_down","death_down"]
 for column in range(4):
  label(names[column],Vector2(64+column*290,82),18)
  var frames:=load("res://output/"+str(units[column])+".tres") as SpriteFrames
  for row in range(5):
   var action:String=actions[row]
   label(action,Vector2(20+column*290,112+row*176),15)
   for slow in [false,true]:
    var sprite:=AnimatedSprite2D.new()
    var key:="%s/%s/%s"%[units[column],action,"slow" if slow else "normal"]
    sprite.sprite_frames=frames
    sprite.centered=false
    sprite.offset=Vector2(-64,-104)
    sprite.position=Vector2(225 if slow else 108,266+row*176)+Vector2(column*290,0)
    sprite.scale=Vector2.ONE if slow else Vector2(2,2)
    sprite.speed_scale=1.0/frames.get_animation_speed(action) if slow else 1.0
    sprite.set_meta("key",key)
    seen[key]=[]
    finished[key]=0
    loops[key]=0
    sprite.animation_finished.connect(func():
     finished[key]+=1
     await get_tree().create_timer(0.5).timeout
     if is_instance_valid(sprite):sprite.stop();sprite.play(action)
    )
    sprite.animation_looped.connect(func():loops[key]+=1)
    add_child(sprite)
    sprite.play(action)
    actors.append(sprite)
func _process(delta:float)->void:
 elapsed+=delta
 for sprite in actors:
  var key:String=sprite.get_meta("key")
  if not seen[key].has(sprite.frame):seen[key].append(sprite.frame)
func label(value:String,where:Vector2,size:int)->void:
 var node:=Label.new()
 node.text=value
 node.position=where
 node.add_theme_font_size_override("font_size",size)
 add_child(node)
