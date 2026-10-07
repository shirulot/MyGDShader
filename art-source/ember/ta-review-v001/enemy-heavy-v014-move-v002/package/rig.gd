extends Node2D
## 固定源部件组成六个新方向；履带外框和轮轴落地，中央壳体只有1px悬挂。
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

func pose(index:int)->Dictionary:
 body.position.y=float(spec.body_y[index])
 tread_material.set_shader_parameter("phase",index*2.0)
 return {"direction":direction,"frame":index,"body_translation":[0,body.position.y],"tread_phase":index*2,"supports":config.supports,"root":[64,104]}
