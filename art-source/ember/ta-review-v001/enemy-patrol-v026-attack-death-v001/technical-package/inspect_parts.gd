extends SceneTree
## 输出实际固定遮罩分片的Nearest检查图，不重新绘制任何角色像素。
const Rig=preload("res://rig.gd")
func _initialize()->void:call_deferred("run")
func run()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 var viewport:=SubViewport.new();viewport.size=Vector2i(128,128);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 var background:=ColorRect.new();background.size=Vector2(128,128);background.color=Color("eeeeee");viewport.add_child(background)
 for direction:String in spec.configs:
  var rig:=Rig.new();rig.direction=direction;viewport.add_child(rig)
  var parts:Dictionary=rig.raw.parts.duplicate();parts.merge(rig.arms)
  for node:Node2D in parts.values():node.visible=false
  for node:Node2D in rig.links.values():node.visible=false
  DirAccess.make_dir_recursive_absolute("res://qa/parts/"+direction)
  for id:String in parts:
   parts[id].visible=true
   await process_frame;await RenderingServer.frame_post_draw
   var im:=viewport.get_texture().get_image();im.resize(512,512,Image.INTERPOLATE_NEAREST)
   im.save_png("res://qa/parts/"+direction+"/"+id+".png")
   parts[id].visible=false
  rig.queue_free();await process_frame
 print("P26_PARTS_INSPECTED")
 quit()
