extends Node2D
## 已通过腿部绑定上的轻动作：脚掌固定，膝甲仅做小幅刚性平移，蓝灰短杆连接髋膝踝。
const DirectionRig=preload("res://directions_rig.gd")
const PilotRig=preload("res://pilot_rig.gd")
var direction:String
var spec:Dictionary
var base:Node2D
var config:Dictionary
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func xy(v:Vector2)->Array:return [v.x,v.y]
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 var kind:String=spec.configs[direction].base
 if kind=="pilot":
  base=PilotRig.new();base.unit_id="enemy_patrol"
 elif kind=="profile":
  base=load("res://profile_rig.gd").new();base.direction=direction
 else:
  base=DirectionRig.new();base.direction=direction
 add_child(base)
 config=base.spec if kind=="pilot" else base.config
func pose_action(action:String,index:int)->Dictionary:
 base.reset_bind()
 var delta:=point(spec.actions[action].body[index])
 base.body.position=delta
 # 膝甲跟随半幅身体位移；踝与脚掌固定，沿用正向轻动作的受力关系。
 var knee_delta:=Vector2(roundf(delta.x*.5),roundf(delta.y*.5))
 for side:String in ["right","left"]:
  for p:Dictionary in config.parts:
   if p.id==side+"_thigh":base.apply_segment(p.id,point(p.pivot)+delta,point(p.end)+knee_delta)
   elif p.id==side+"_shin":base.apply_segment(p.id,point(p.pivot)+knee_delta,point(p.end))
   elif p.id==side+"_cap":base.parts[p.id].position+=knee_delta
 var record:Dictionary={"action":action,"direction":direction,"frame":index,"root":[64,104],"body_translation":xy(delta),"supports":{},"part_transforms":{}}
 for side:String in ["right","left"]:
  var leg:Dictionary=config.legs[side]
  var sole:=point(leg.ankle)+point(leg.sole_offset)
  record.supports[side]={"hip":xy(point(leg.hip)+delta),"knee":xy(point(leg.knee)+knee_delta),"ankle":leg.ankle,"sole":xy(sole),"ground":xy(sole),"support":true}
 for id:String in base.parts:
  var t:Transform2D=base.parts[id].transform
  record.part_transforms[id]={"position":xy(t.origin),"basis_x":xy(t.x),"basis_y":xy(t.y)}
 return record
