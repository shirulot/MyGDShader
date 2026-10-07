extends Node2D
## 首阶段斜向移动样片。每个部件只有一个固定源区域，没有逐帧重画。
var unit_id:String
var spec:Dictionary
var parts:Dictionary={}
var fans:Dictionary={}
var body:Node2D
var texture:Texture2D
var materials:Array[ShaderMaterial]=[]

func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func xy(p:Vector2)->Array:return [p.x,p.y]
func polygon(a:Array)->PackedVector2Array:
 var result:=PackedVector2Array()
 for item:Array in a:result.append(point(item))
 return result

func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://pilot_rigs.json"))
 for candidate:Dictionary in data.units:
  if candidate.unit==unit_id:spec=candidate
 texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(str(spec.source))))
 if unit_id=="enemy_scout_drone":
  build_drone()
  return
 var excluded:Array=spec.get("remove_polygons",[]).duplicate(true)
 for definition:Dictionary in spec.parts:excluded.append(definition.polygon)
 body=make_part("body",Vector2.ZERO,[],excluded,5,"res://masked_part.gdshader")
 for definition:Dictionary in spec.parts:
  var shader:="res://pilot_tread.gdshader" if unit_id=="enemy_tracked_heavy" else "res://masked_part.gdshader"
  make_part(definition.id,point(definition.pivot),[definition.polygon]+definition.get("overlap_polygons",[]),definition.exclude,definition.z,shader)
 if unit_id=="enemy_cutter":
  for leg:Dictionary in spec.legs:
   if leg.get("registered",false):continue
   var node:=Sprite2D.new()
   var atlas:=AtlasTexture.new()
   var r:Array=leg.source_rect
   atlas.atlas=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(str(spec.leg_source))))
   atlas.region=Rect2(r[0],r[1],r[2],r[3])
   node.texture=atlas
   node.centered=false
   node.position=point(leg.target_origin)
   node.scale=Vector2.ONE*float(leg.scale)
   node.z_index=leg.z
   var material:=ShaderMaterial.new()
   material.shader=load("res://entity_cutout.gdshader")
   node.material=material
   add_child(node)
   parts[leg.id]=node

func make_part(id:String,pivot:Vector2,includes:Array,excludes:Array,z:int,shader_path:String)->Node2D:
 # 这张单通道遮罩是源区域归属数据，不产生或修改美术 RGB。
 var ownership:=Image.create(128,128,false,Image.FORMAT_R8)
 ownership.fill(Color.BLACK)
 for y in range(128):
  for x in range(128):
   var p:=Vector2(x+0.5,y+0.5)
   var visible:=includes.is_empty()
   for shape:Array in includes:
    if Geometry2D.is_point_in_polygon(p,polygon(shape)):visible=true
   for shape:Array in excludes:
    if Geometry2D.is_point_in_polygon(p,polygon(shape)):visible=false
   if visible:ownership.set_pixel(x,y,Color.WHITE)
 var node:=Node2D.new()
 node.position=pivot
 node.z_index=z
 var sprite:=Sprite2D.new()
 sprite.centered=false
 sprite.texture=texture
 sprite.position=-pivot
 var material:=ShaderMaterial.new()
 material.shader=load(shader_path)
 material.set_shader_parameter("ownership",ImageTexture.create_from_image(ownership))
 sprite.material=material
 materials.append(material)
 node.add_child(sprite)
 add_child(node)
 parts[id]=node
 return node

func build_drone()->void:
 body=Node2D.new()
 add_child(body)
 var sprite:=Sprite2D.new()
 sprite.centered=false
 sprite.texture=texture
 sprite.z_index=2
 var body_material:=ShaderMaterial.new()
 body_material.shader=load("res://pilot_fan_body.gdshader")
 sprite.material=body_material
 body.add_child(sprite)
 for fan:Dictionary in spec.fans:
  var plane:=Node2D.new()
  plane.position=point(fan.center)
  plane.scale=point(fan.radius)/6.5
  body.add_child(plane)
  for layer:String in ["well","rotor"]:
   var node:=Polygon2D.new()
   var r:Array=spec[layer+"_rect"]
   node.polygon=PackedVector2Array([Vector2(-6.5,-6.5),Vector2(6.5,-6.5),Vector2(6.5,6.5),Vector2(-6.5,6.5)])
   node.uv=PackedVector2Array([Vector2(r[0],r[1]),Vector2(r[0]+r[2],r[1]),Vector2(r[0]+r[2],r[1]+r[3]),Vector2(r[0],r[1]+r[3])])
   node.texture=load(str(spec.fan_source))
   var material:=ShaderMaterial.new()
   material.shader=load("res://pilot_fan.gdshader")
   node.material=material
   plane.add_child(node)
   if layer=="rotor":fans[fan.id]=node

func reset_bind()->void:
 body.position=Vector2.ZERO
 for definition:Dictionary in spec.parts:parts[definition.id].transform=Transform2D(0,point(definition.pivot))
 if unit_id=="enemy_cutter":
  for leg:Dictionary in spec.legs:
   if not leg.get("registered",false):parts[leg.id].position=point(leg.target_origin)
 elif unit_id=="enemy_tracked_heavy":
  for material:ShaderMaterial in materials:
   if material.shader.resource_path.ends_with("pilot_tread.gdshader"):material.set_shader_parameter("phase",0.0)
 elif unit_id=="enemy_scout_drone":
  for rotor:Polygon2D in fans.values():rotor.rotation=0

func pose(index:int)->Dictionary:
 reset_bind()
 var record:Dictionary={"unit":unit_id,"action":"move_down_right","frame":index,"root":[64,104],"supports":{},"part_transforms":{}}
 if unit_id=="enemy_patrol":pose_patrol(index,record)
 elif unit_id=="enemy_tracked_heavy":
  body.position.y=[0,0,1,0,0,0,1,0][index]
  for material:ShaderMaterial in materials:
   if material.shader.resource_path.ends_with("pilot_tread.gdshader"):material.set_shader_parameter("phase",index*2.0)
  record.tread_phase_px=index*2
  record.supports={"near":[44,104],"far":[97,93]}
 elif unit_id=="enemy_cutter":
  body.position.y=[0,0,-1,0,0,0,-1,0][index]
  for leg:Dictionary in spec.legs:
   var phase:int=posmod(index+int(leg.phase_offset),8)
   var depth:float=[2,1,0,-1,-2,-1,0,1][phase]
   var lift:float=[0,0,0,0,0,1,2,1][phase]
   var travel:=Vector2(roundf(depth*0.7),roundf(depth*0.25-lift))
   parts[leg.id].position+=travel
   record.supports[leg.id]={"sole":xy(point(leg.sole)+travel),"support":lift==0,"lift":lift,"depth":depth,"hidden_mount_travel":xy(travel)}
 elif unit_id=="enemy_scout_drone":
  body.position.y=[0,-1,-1,0,1,1,0,0][index]
  for fan:Dictionary in spec.fans:fans[fan.id].rotation=deg_to_rad(index*11.25*float(fan.spin))
  record.rotor_angle_deg=index*11.25
  record.rotor_count=2
  record.blades_per_rotor=4
  record.hover_body_y=body.position.y
 record.body_translation=xy(body.position)
 for id:String in parts:
  var node:Node2D=parts[id]
  record.part_transforms[id]={"position":xy(node.position),"basis_x":xy(node.transform.x),"basis_y":xy(node.transform.y)}
 return record

func world_knee(bob:float,depth:float,lift:float)->Vector2:
 var hip:=Vector2(32-bob/0.75,0)
 var ankle:=Vector2(8+lift,depth)
 var axis:=ankle-hip
 var distance:=axis.length()
 var outward:=sqrt(maxf(0.0,169-distance*distance/4.0))
 var direction:=axis/distance
 return hip+direction*distance/2.0+Vector2(direction.y,-direction.x)*outward

func project_delta(v:Vector2)->Vector2:
 return Vector2(roundf(v.y*0.7071*0.7),roundf(-v.x*0.75+v.y*0.35*0.7071))

func pose_patrol(index:int,record:Dictionary)->void:
 var phase:Dictionary=spec.phases[index]
 body.position.y=phase.body_y
 var rest_knee:=world_knee(0,0,0)
 for side:String in ["right","left"]:
  var leg:Dictionary=spec.legs[side]
  var foot:Dictionary=phase[side]
  var hip:=point(leg.hip)+body.position
  var knee:=point(leg.knee)+project_delta(world_knee(phase.body_y,foot.depth,foot.lift)-rest_knee)
  var ankle:=point(leg.ankle)+project_delta(Vector2(foot.lift,foot.depth))
  apply_segment(side+"_thigh",hip,knee)
  apply_segment(side+"_shin",knee,ankle)
  parts[side+"_cap"].position=knee
  parts[side+"_foot"].position=ankle
  record.supports[side]={"hip":xy(hip),"knee":xy(knee),"ankle":xy(ankle),"sole":xy(ankle+point(leg.sole_offset)),"ground":xy(point(leg.ankle)+point(leg.sole_offset)+project_delta(Vector2(0,foot.depth))),"support":foot.support,"depth":foot.depth,"lift":foot.lift}

func apply_segment(id:String,start:Vector2,end:Vector2)->void:
 for definition:Dictionary in spec.parts:
  if definition.id!=id:continue
  var rest:=point(definition.end)-point(definition.pivot)
  var current:=end-start
  var rest_axis:=rest.normalized()
  var rest_normal:=Vector2(-rest_axis.y,rest_axis.x)
  var target_axis:=current/rest.length()
  var target_normal:=Vector2(-current.y,current.x).normalized()
  parts[id].transform=Transform2D(target_axis*rest_axis.x+target_normal*rest_normal.x,target_axis*rest_axis.y+target_normal*rest_normal.y,start)
  assert((parts[id].transform*rest).distance_to(end)<0.0001)
