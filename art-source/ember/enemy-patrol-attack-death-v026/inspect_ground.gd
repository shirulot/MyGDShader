extends SceneTree
## 从固定零件的不透明源像素寻找接触候选；只输出测量，不逐帧移动、缩放或修改图像。
const Rig=preload("res://rig.gd")
func _initialize()->void:call_deferred("run")
func run()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 var records:Array=[]
 for direction:String in spec.configs:
  var rig:=Rig.new()
  rig.direction=direction
  root.add_child(rig)
  for frame in range(3,8):
   rig.pose_action("death",frame)
   var candidates:Dictionary=rig.raw.parts.duplicate()
   candidates.merge(rig.arms)
   var deepest:Dictionary={"world_pixel_center":[0,-INF]}
   for id:String in candidates:
    var node:Node2D=candidates[id]
    var sprite:Sprite2D=node.get_child(0)
    var source:Image=sprite.texture.get_image()
    var mask:Image=sprite.material.get_shader_parameter("ownership").get_image()
    var matrix:Transform2D=rig.whole.transform*node.transform*Transform2D(0,sprite.position)
    for y in range(source.get_height()):
     for x in range(source.get_width()):
      if source.get_pixel(x,y).a<.5 or mask.get_pixel(x,y).r<.5:continue
      var center:=matrix*Vector2(x+.5,y+.5)
      if center.y>float(deepest.world_pixel_center[1]):
       deepest={"part":id,"source_pixel":[x,y],"source_pixel_center":[x+.5,y+.5],"world_pixel_center":[center.x,center.y]}
   records.append({"direction":direction,"frame":frame,"contact_candidate":deepest})
  rig.queue_free()
  await process_frame
 var file:=FileAccess.open("res://qa/ground_registration_measurements.json",FileAccess.WRITE)
 file.store_string(JSON.stringify(records,"  "))
 print("GROUND_CONTACT_MEASURED ",records.size())
 quit()
