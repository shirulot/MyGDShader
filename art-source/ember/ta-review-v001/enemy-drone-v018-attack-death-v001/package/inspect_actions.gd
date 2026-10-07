extends SceneTree
## 统一裁剪区包含悬浮与落地，方便逐帧观察同一位置的几何变化。
func _initialize()->void:
 var catalog:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog.json"))
 for clip:Dictionary in catalog.clips:
  var roi:=Rect2i(24,44,80,62)
  var contact:=Image.create(80*clip.frame_count,62,false,Image.FORMAT_RGBA8)
  contact.fill(Color.WHITE)
  for index in range(clip.frame_count):
   var frame:=Image.load_from_file(ProjectSettings.globalize_path("res://output/enemy_scout_drone/%s/f%02d.png"%[clip.action,index]))
   contact.blend_rect(frame,roi,Vector2i(index*80,0))
  contact.resize(80*clip.frame_count*4,62*4,Image.INTERPOLATE_NEAREST)
  contact.save_png("res://qa/detail_"+clip.action+"_4x.png")
 quit()
