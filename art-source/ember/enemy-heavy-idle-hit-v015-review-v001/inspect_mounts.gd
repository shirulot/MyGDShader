extends SceneTree
## 每条动作四帧采用同一安装区ROI，审查固定安装座是否断裂或露出多余条纹。
func _initialize()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 for direction:String in spec.configs:
  for action:String in spec.actions:
   var contact:=Image.create(288,50,false,Image.FORMAT_RGBA8)
   contact.fill(Color.WHITE)
   for index in range(4):
    var path:="res://output/enemy_tracked_heavy/%s_%s/f%02d.png"%[action,direction,index]
    var frame:=Image.load_from_file(ProjectSettings.globalize_path(path))
    contact.blend_rect(frame,Rect2i(28,50,72,50),Vector2i(index*72,0))
   contact.resize(1728,300,Image.INTERPOLATE_NEAREST)
   contact.save_png("res://qa/mount_"+action+"_"+direction+"_6x.png")
 quit()
