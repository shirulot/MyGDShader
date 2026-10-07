extends SceneTree
## 共同 ROI 联系图供逐帧检查履带、轮盖及悬挂；不修改源帧。
func _initialize()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 for direction:String in spec.configs:
  var contact:=Image.create(352,96,false,Image.FORMAT_RGBA8)
  contact.fill(Color.WHITE)
  for index in range(8):
   var image:=Image.load_from_file(ProjectSettings.globalize_path("res://output/enemy_tracked_heavy/move_%s/f%02d.png"%[direction,index]))
   contact.blend_rect(image,Rect2i(20,58,88,48),Vector2i(index%4*88,index/4*48))
  contact.resize(1408,384,Image.INTERPOLATE_NEAREST)
  contact.save_png("res://qa/treads_"+direction+"_4x.png")
 quit()
