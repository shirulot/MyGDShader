extends SceneTree
const Rig=preload("res://rig.gd")
func _initialize()->void:call_deferred("run")
func run()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(128,128)
 viewport.transparent_bg=true
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 for direction:String in spec.configs:
  var rig:=Rig.new()
  rig.direction=direction
  viewport.add_child(rig)
  for node:Node2D in rig.parts.values():node.visible=false
  for node:Node2D in rig.links.values():node.visible=false
  DirAccess.make_dir_recursive_absolute("res://qa/parts/"+direction)
  for id:String in rig.parts:
   rig.parts[id].visible=true
   await process_frame
   await RenderingServer.frame_post_draw
   viewport.get_texture().get_image().save_png("res://qa/parts/"+direction+"/"+id+".png")
   rig.parts[id].visible=false
  rig.queue_free()
  await process_frame
 quit()
