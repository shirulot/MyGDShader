extends Node2D
## 原图机壳完整保持。每个转子先在自身平面旋转，再投影到固定的椭圆风口。
var direction:String
var spec:Dictionary
var config:Dictionary
var body:Node2D
var rotors:Dictionary={}
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func source_texture(path:String)->ImageTexture:
 return ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(path)))
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 config=spec.configs[direction]
 body=Node2D.new()
 add_child(body)
 var shell:=Sprite2D.new()
 shell.centered=false
 shell.texture=source_texture(config.source)
 shell.z_index=2
 var shell_material:=ShaderMaterial.new()
 shell_material.shader=load("res://pilot_fan_body.gdshader")
 for index in range(2):
  var name:="fan_a" if index==0 else "fan_b"
  shell_material.set_shader_parameter(name+"_center",point(config.fans[index].center))
  shell_material.set_shader_parameter(name+"_radius",point(config.fans[index].radius))
 shell.material=shell_material
 body.add_child(shell)
 var fan_texture:=source_texture(spec.fan_source)
 for fan:Dictionary in config.fans:
  var plane:=Node2D.new()
  plane.position=point(fan.center)
  plane.scale=point(fan.radius)/6.5
  body.add_child(plane)
  for layer:String in ["well","rotor"]:
   var part:=Polygon2D.new()
   var r:Array=spec[layer+"_rect"]
   part.polygon=PackedVector2Array([Vector2(-6.5,-6.5),Vector2(6.5,-6.5),Vector2(6.5,6.5),Vector2(-6.5,6.5)])
   part.uv=PackedVector2Array([Vector2(r[0],r[1]),Vector2(r[0]+r[2],r[1]),Vector2(r[0]+r[2],r[1]+r[3]),Vector2(r[0],r[1]+r[3])])
   part.texture=fan_texture
   var material:=ShaderMaterial.new()
   material.shader=load("res://pilot_fan.gdshader")
   part.material=material
   plane.add_child(part)
   if layer=="rotor":rotors[fan.id]=part
func pose_action(action:String,index:int)->Dictionary:
 var state:Dictionary=spec.actions[action]
 var dy:float=state.body_y[index]
 var roll:float=state.roll[index]
 body.transform=Transform2D(deg_to_rad(roll),Vector2(64,67+dy))*Transform2D(0,Vector2(-64,-67))
 var angles:Dictionary={}
 var axes:Dictionary={}
 for fan:Dictionary in config.fans:
  var angle:float=float(state.rotor_angles[index])*float(fan.spin)
  rotors[fan.id].rotation=deg_to_rad(angle)
  angles[fan.id]=angle
  var center:Vector2=body.transform*point(fan.center)
  axes[fan.id]=[center.x,center.y]
 return {"action":action,"direction":direction,"frame":index,"body_y":dy,"body_roll_degrees":roll,"rotor_angles_degrees":angles,"axis_world":axes,"body_basis_x":[body.transform.x.x,body.transform.x.y],"body_basis_y":[body.transform.y.x,body.transform.y.y],"body_origin":[body.position.x,body.position.y],"fans":config.fans,"root":[64,104]}
