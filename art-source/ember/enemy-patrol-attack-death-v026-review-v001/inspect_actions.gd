extends SceneTree
## 固定共同 ROI 的 4×2 联系图，用于检查所有帧的关节和工具归属。
func _initialize()->void:
 var catalog:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog.json"))
 for clip:Dictionary in catalog.clips:
  var roi:=Rect2i(8,40,112,80)
  var contact:=Image.create(112*4,80*2,false,Image.FORMAT_RGBA8)
  contact.fill(Color("eeeeee"))
  for index in range(int(clip.frame_count)):
   var frame:=Image.load_from_file(ProjectSettings.globalize_path("res://output/enemy_patrol/%s/f%02d.png"%[clip.action,index]))
   assert(roi.encloses(frame.get_used_rect()),"Inspection ROI clips silhouette")
   contact.blend_rect(frame,roi,Vector2i((index%4 )*112,(index/4 )*80))
  contact.resize(112*4*4,80*2*4,Image.INTERPOLATE_NEAREST)
  contact.save_png("res://qa/detail_"+clip.action+"_4x.png")
 quit()
