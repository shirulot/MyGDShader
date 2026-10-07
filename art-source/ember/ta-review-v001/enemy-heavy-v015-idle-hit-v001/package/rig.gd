extends Node2D
## 七个新方向使用固定源零件；中央壳体做悬挂和受击位移，履带保持支撑。
var direction:String
var spec:Dictionary
var config:Dictionary
var body:Sprite2D
var tracks:Sprite2D
var tread_material:ShaderMaterial

func as_polygon(values:Array)->PackedVector2Array:
 var points:=PackedVector2Array()
 for value:Array in values:points.append(Vector2(value[0],value[1]))
 return points

func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 spec=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 config=spec.configs[direction]
 var image:=Image.load_from_file(ProjectSettings.globalize_path(str(config.source)))
 assert(image!=null and image.get_size()==Vector2i(128,128))
 var texture:=ImageTexture.create_from_image(image)
 var track_mask:=Image.create(128,128,false,Image.FORMAT_R8)
 var body_mask:=Image.create(128,128,false,Image.FORMAT_R8)
 for y in range(128):
  for x in range(128):
   var owned:=false
   for shape:Array in config.track_polygons:
    if Geometry2D.is_point_in_polygon(Vector2(x+.5,y+.5),as_polygon(shape)):owned=true
   track_mask.set_pixel(x,y,Color.WHITE if owned else Color.BLACK)
   body_mask.set_pixel(x,y,Color.BLACK if owned else Color.WHITE)
 # 固定安装座沿用原图的少量重叠区，完全藏在中性壳体之下。
 # 此处只扩展源区域归属遮罩；不补画RGB，也不改变逐帧来源。
 var base_track_mask:=track_mask.duplicate()
 for y in range(int(spec.mount_overlap.y_min),int(spec.mount_overlap.y_max)+1):
  for x in range(128):
   var overlap:=false
   for dy in range(-int(spec.mount_overlap.radius_y),int(spec.mount_overlap.radius_y)+1):
    for dx in range(-int(spec.mount_overlap.radius_x),int(spec.mount_overlap.radius_x)+1):
     var p:=Vector2i(x+dx,y+dy)
     if p.x>=0 and p.x<128 and p.y>=0 and p.y<128 and base_track_mask.get_pixelv(p).r>0.5:overlap=true
   if overlap:track_mask.set_pixel(x,y,Color.WHITE)
 tracks=Sprite2D.new()
 tracks.centered=false
 tracks.texture=texture
 tread_material=ShaderMaterial.new()
 tread_material.shader=load("res://tread_flow.gdshader")
 tread_material.set_shader_parameter("ownership",ImageTexture.create_from_image(track_mask))
 var windows:Array[Vector4]=[]
 var parameters:Array[Vector4]=[]
 for window:Dictionary in config.windows:
  windows.append(Vector4(window.origin[0],window.origin[1],window.cross_width,window.period))
  parameters.append(Vector4(window.shear,window.sign,1 if window.horizontal else 0,window.thickness))
 while windows.size()<4:windows.append(Vector4.ZERO);parameters.append(Vector4.ZERO)
 tread_material.set_shader_parameter("window_count",config.windows.size())
 tread_material.set_shader_parameter("windows",windows)
 tread_material.set_shader_parameter("parameters",parameters)
 tracks.material=tread_material
 add_child(tracks)
 body=Sprite2D.new()
 body.centered=false
 body.texture=texture
 var body_material:=ShaderMaterial.new()
 body_material.shader=load("res://masked_part.gdshader")
 body_material.set_shader_parameter("ownership",ImageTexture.create_from_image(body_mask))
 body.material=body_material
 body.z_index=1
 add_child(body)

func pose_action(action:String,index:int)->Dictionary:
 var delta:Array=spec.actions[action].body[index]
 body.position=Vector2(delta[0],delta[1])
 tread_material.set_shader_parameter("phase",0.0)
 return {"action":action,"direction":direction,"frame":index,"body_translation":delta,"tread_phase":0,"supports":config.supports,"root":[64,104]}
