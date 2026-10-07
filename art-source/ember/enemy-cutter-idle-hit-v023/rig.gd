extends Node2D
## 使用同一套固定腿与安装座。idle/hit 中脚底固定，只有机身轻微起伏或回弹。
const MoveRig=preload("res://move_rig.gd")
const PilotRig=preload("res://pilot_rig.gd")
var direction:String
var spec:Dictionary
var base:Node2D
func xy(v:Vector2)->Array:return [v.x,v.y]
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 if direction=="down_right":
  base=PilotRig.new()
  base.unit_id="enemy_cutter"
 else:
  base=MoveRig.new()
  base.direction=direction
 add_child(base)
func pose_action(action:String,index:int)->Dictionary:
 base.reset_bind()
 var delta:Array=spec.actions[action].body[index]
 base.body.position=Vector2(delta[0],delta[1])
 if direction!="down_right":
  for p:Dictionary in base.config.parts:base.update_socket(p,Vector2.ZERO)
 var record:Dictionary={"action":action,"direction":direction,"frame":index,"body_translation":delta,"root":[64,104],"part_transforms":{},"supports":{}}
 for id:String in base.parts:
  var t:Transform2D=base.parts[id].transform
  record.part_transforms[id]={"position":xy(t.origin),"basis_x":xy(t.x),"basis_y":xy(t.y)}
 if direction=="down_right":
  for leg:Dictionary in base.spec.legs:record.supports[leg.id]={"sole":leg.sole,"ground":leg.sole,"support":true}
 else:
  record.socket_polygons={}
  for p:Dictionary in base.config.parts:
   record.supports[p.id]={"sole":p.sole,"ground":p.sole,"support":true}
   record.socket_polygons[p.id]=[]
   for vertex:Vector2 in base.sockets[p.id].polygon:record.socket_polygons[p.id].append(xy(vertex))
 return record
