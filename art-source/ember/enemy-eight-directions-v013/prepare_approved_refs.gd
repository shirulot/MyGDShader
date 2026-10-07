extends SceneTree
## 原生通过帧的整数倍参考；不重绘，不改比例或像素值。
func _initialize()->void:
 for unit:String in ["enemy_patrol","enemy_scout_drone"]:
  var frame:=Image.load_from_file(ProjectSettings.globalize_path("res://source/approved_down/"+unit+".png"))
  frame.resize(1024,1024,Image.INTERPOLATE_NEAREST)
  frame.save_png("res://source/approved_down/"+unit+"_8x.png")
 quit()
