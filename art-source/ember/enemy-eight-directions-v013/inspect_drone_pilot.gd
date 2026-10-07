extends SceneTree
## 审阅共同 ROI，不改动任何生产帧或已冻结静态包。
func _initialize()->void:
 var sheet:=Image.create(256,84,false,Image.FORMAT_RGBA8)
 sheet.fill(Color.WHITE)
 for index in range(8):
  var path:="res://output/enemy_scout_drone/move_down_right/f%02d.png"%index
  var frame:=Image.load_from_file(ProjectSettings.globalize_path(path))
  sheet.blend_rect(frame,Rect2i(32,46,64,42),Vector2i(index%4*64,index/4*42))
 sheet.resize(2048,672,Image.INTERPOLATE_NEAREST)
 sheet.save_png("res://qa/drone_se_eight_rotors_8x.png")
 quit()
