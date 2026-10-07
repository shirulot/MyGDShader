extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var dirs:=["down_left","left","up_left","up","up_right","right","down_right","down"]
 var sheet:=Image.create(1024,512,false,Image.FORMAT_RGBA8)
 sheet.fill(Color("eeeeee"))
 for index in range(dirs.size()):
  var image:=Image.load_from_file(ProjectSettings.globalize_path("res://source/"+dirs[index]+".png"))
  var crop:=image.get_region(Rect2i(24,44,80,64))
  crop.resize(320,256,Image.INTERPOLATE_NEAREST)
  crop.save_png("res://qa/source_"+dirs[index]+"_4x.png")
  image.resize(256,256,Image.INTERPOLATE_NEAREST)
  sheet.blend_rect(image,Rect2i(0,0,256,256),Vector2i(index%4*256,index/4*256))
 sheet.save_png("res://qa/source_eight_views_2x.png")
 quit()
