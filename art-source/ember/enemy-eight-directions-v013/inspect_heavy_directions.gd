extends SceneTree
func _initialize()->void:
 var directions:Array[String]=["down_left","left","up_left","up","up_right","right"]
 for pair in range(3):
  var contact:=Image.create(256,128,false,Image.FORMAT_RGBA8)
  contact.fill(Color.WHITE)
  for column in range(2):
   var path:="res://output/enemy_tracked_heavy/neutral_"+directions[pair*2+column]+".png"
   var image:=Image.load_from_file(ProjectSettings.globalize_path(path))
   contact.blend_rect(image,Rect2i(0,0,128,128),Vector2i(column*128,0))
  contact.resize(1536,768,Image.INTERPOLATE_NEAREST)
  contact.save_png("res://qa/heavy_static_pair_%d.png"%pair)
 quit()
