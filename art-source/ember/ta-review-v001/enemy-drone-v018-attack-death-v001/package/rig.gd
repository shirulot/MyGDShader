extends Node2D
## 每个方向只使用批准母版和固定转子。坠落不缩放壳体，也不凭空补隐藏连接结构。
var direction:String
var spec:Dictionary
var config:Dictionary
var body:=Node2D.new()
var probe:Sprite2D
var shell_material:ShaderMaterial
var rotors:Dictionary={}
func point(a:Array)->Vector2:return Vector2(a[0],a[1])
func rect_vector(a:Array)->Vector4:return Vector4(a[0],a[1],a[2],a[3])
func source_texture(path:String)->ImageTexture:
 return ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(path)))
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 config=spec.configs[direction]
 add_child(body)
 var shell:=Sprite2D.new()
 shell.centered=false
 shell.texture=source_texture(config.source)
 shell.z_index=2
 shell_material=ShaderMaterial.new()
 shell_material.shader=load("res://pilot_fan_body.gdshader")
 for index in range(2):
  var name:="fan_a" if index==0 else "fan_b"
  shell_material.set_shader_parameter(name+"_center",point(config.fans[index].center))
  shell_material.set_shader_parameter(name+"_radius",point(config.fans[index].radius))
 shell_material.set_shader_parameter("sensor_rect",rect_vector(config.sensor_rect))
 shell.material=shell_material
 body.add_child(shell)
 # 原静态探头作为固定套筒。仅前斜向露出的短尖端做两像素伸缩，后方保持遮挡。
 if config.probe_rect[2]>0:
  probe=Sprite2D.new()
  probe.centered=false
  probe.texture=shell.texture
  probe.z_index=3
  var tip_material:=ShaderMaterial.new()
  tip_material.shader=load("res://probe_tip.gdshader")
  tip_material.set_shader_parameter("source_rect",rect_vector(config.probe_rect))
  probe.material=tip_material
  body.add_child(probe)
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
 var dy:int=roundi(float(config.fall_distance)*float(state.drop_fraction[index])) if action=="death" else int(state.body_y[index])
 body.position=Vector2(0,dy)
 if probe!=null:probe.position.y=state.probe_y[index]
 shell_material.set_shader_parameter("sensor_power",float(state.power[index]))
 var angles:Dictionary={}
 var axes:Dictionary={}
 for fan:Dictionary in config.fans:
  var angle:float=float(state.rotor_angles[index])*float(fan.spin)
  rotors[fan.id].rotation=deg_to_rad(angle)
  angles[fan.id]=angle
  axes[fan.id]=[fan.center[0],fan.center[1]+dy]
 return {"action":action,"direction":direction,"frame":index,"body_y":dy,"probe_y":state.probe_y[index],"probe_visibility":config.probe_visibility,"sensor_power":state.power[index],"rotor_angles_degrees":angles,"axis_world":axes,"body_basis_x":[1,0],"body_basis_y":[0,1],"body_origin":[0,dy],"fans":config.fans,"root":[64,104],"ground_edge_y":config.ground_edge_y+dy}
