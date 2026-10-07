extends SceneTree
## 固定画布并排比较，不按各图的包围盒重新缩放。
func _initialize()->void:call_deferred("run")
func run()->void:
 var sheet:=Image.create(1024,512,false,Image.FORMAT_RGBA8)
 sheet.fill(Color("dddddd"))
 for row in range(2):
  var direction:String=["left","right"][row]
  for column in range(4):
   var original:bool=column%2==0
   var image:=Image.load_from_file(ProjectSettings.globalize_path(("res://source/"+direction+".png") if original else ("res://qa/bind_"+direction+".png")))
   var panel:=Image.create(128,128,false,Image.FORMAT_RGBA8)
   panel.fill(Color("dddddd") if column<2 else Color("080b10"))
   panel.blend_rect(image,Rect2i(0,0,128,128),Vector2i.ZERO)
   panel.resize(256,256,Image.INTERPOLATE_NEAREST)
   sheet.blit_rect(panel,Rect2i(0,0,256,256),Vector2i(column*256,row*256))
 sheet.save_png("res://qa/bind_original_candidate_2x.png")
 quit()
