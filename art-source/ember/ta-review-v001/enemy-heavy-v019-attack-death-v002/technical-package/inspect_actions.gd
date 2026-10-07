extends SceneTree
func _initialize()->void:
 var catalog:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog.json"))
 for clip:Dictionary in catalog.clips:
  var roi:=Rect2i(20,40,88,66)
  var contact:=Image.create(88*clip.frame_count,66,false,Image.FORMAT_RGBA8)
  contact.fill(Color.WHITE)
  for index in range(clip.frame_count):
   var frame:=Image.load_from_file(ProjectSettings.globalize_path("res://output/enemy_tracked_heavy/%s/f%02d.png"%[clip.action,index]))
   contact.blend_rect(frame,roi,Vector2i(index*88,0))
  contact.resize(88*clip.frame_count*4,66*4,Image.INTERPOLATE_NEAREST)
  contact.save_png("res://qa/detail_"+clip.action+"_4x.png")
 quit()
