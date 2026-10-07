extends SceneTree
## 技术审图：只截取固定ROI并Nearest放大，不改变生产纹理。
func _initialize()->void:
 var paths:={
  "patrol_se":"res://static_preflight_v002_patrol/neutral_down_right.png",
  "drone_se":"res://calibration_check_c003_drone/neutral_down_right.png"
 }
 for key:String in paths:
  var source:=Image.load_from_file(ProjectSettings.globalize_path(paths[key]))
  var full:=Image.create(128,128,false,Image.FORMAT_RGBA8)
  full.fill(Color.WHITE)
  full.blend_rect(source,Rect2i(0,0,128,128),Vector2i.ZERO)
  full.resize(1024,1024,Image.INTERPOLATE_NEAREST)
  full.save_png("res://qa/"+key+"_8x.png")
  var roi:=Rect2i(42,78,44,28) if key=="patrol_se" else Rect2i(32,46,64,42)
  var close:=Image.create(roi.size.x,roi.size.y,false,Image.FORMAT_RGBA8)
  close.fill(Color.WHITE)
  close.blend_rect(source,roi,Vector2i.ZERO)
  close.resize(roi.size.x*16,roi.size.y*16,Image.INTERPOLATE_NEAREST)
  close.save_png("res://qa/"+key+"_detail_16x.png")
 # 全部八帧用共同ROI排列为两行，避免超宽预览被缩小后看不清关节。
 var patrol_frames:=Image.create(4*44,2*30,false,Image.FORMAT_RGBA8)
 patrol_frames.fill(Color.WHITE)
 for index in range(8):
  var path:="res://output/enemy_patrol/move_down_right/f%02d.png"%index
  var frame:=Image.load_from_file(ProjectSettings.globalize_path(path))
  patrol_frames.blend_rect(frame,Rect2i(42,78,44,30),Vector2i(index%4*44,index/4*30))
 patrol_frames.resize(1408,480,Image.INTERPOLATE_NEAREST)
 patrol_frames.save_png("res://qa/patrol_se_eight_legs_8x.png")
 if FileAccess.file_exists("res://static_preflight_s004_drone/neutral_left.png"):
  var profiles:=Image.create(68,45,false,Image.FORMAT_RGBA8)
  profiles.fill(Color.WHITE)
  for index in range(2):
   var direction:="left" if index==0 else "right"
   var source:=Image.load_from_file(ProjectSettings.globalize_path("res://static_preflight_s004_drone/neutral_"+direction+".png"))
   profiles.blend_rect(source,Rect2i(48,45,34,45),Vector2i(index*34,0))
  profiles.resize(1088,720,Image.INTERPOLATE_NEAREST)
  profiles.save_png("res://static_preflight_s004_drone/profiles_roi_white_16x.png")
 quit()
