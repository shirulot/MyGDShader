extends SceneTree
## 共同画布ROI包括受击倾转后的边界；不按每帧bbox重新对齐。
func _initialize()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 for direction:String in spec.configs:
  for action:String in spec.actions:
   var contact:=Image.create(320,48,false,Image.FORMAT_RGBA8)
   contact.fill(Color.WHITE)
   for index in range(4):
    var path:="res://output/enemy_scout_drone/%s_%s/f%02d.png"%[action,direction,index]
    var frame:=Image.load_from_file(ProjectSettings.globalize_path(path))
    contact.blend_rect(frame,Rect2i(24,44,80,48),Vector2i(index*80,0))
   contact.resize(1920,288,Image.INTERPOLATE_NEAREST)
   contact.save_png("res://qa/detail_"+action+"_"+direction+"_6x.png")
 quit()
