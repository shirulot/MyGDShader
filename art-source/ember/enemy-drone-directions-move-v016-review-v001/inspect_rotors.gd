extends SceneTree
## 六个方向统一ROI；并列母版与实际绑定，供比对外壳和轴心。
func _initialize()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 var bind_sheet:=Image.create(6*80,2*48,false,Image.FORMAT_RGBA8)
 bind_sheet.fill(Color.WHITE)
 var column:=0
 for direction:String in spec.configs:
  var contact:=Image.create(320,96,false,Image.FORMAT_RGBA8)
  contact.fill(Color.WHITE)
  var source:=Image.load_from_file(ProjectSettings.globalize_path("res://source/"+direction+".png"))
  var bind:=Image.load_from_file(ProjectSettings.globalize_path("res://qa/bind_"+direction+".png"))
  bind_sheet.blend_rect(source,Rect2i(24,44,80,48),Vector2i(column*80,0))
  bind_sheet.blend_rect(bind,Rect2i(24,44,80,48),Vector2i(column*80,48))
  for index in range(8):
   var path:="res://output/enemy_scout_drone/move_%s/f%02d.png"%[direction,index]
   var frame:=Image.load_from_file(ProjectSettings.globalize_path(path))
   contact.blend_rect(frame,Rect2i(24,44,80,48),Vector2i(index%4*80,index/4*48))
  contact.resize(1920,576,Image.INTERPOLATE_NEAREST)
  contact.save_png("res://qa/rotors_"+direction+"_6x.png")
  column+=1
 bind_sheet.resize(1920,384,Image.INTERPOLATE_NEAREST)
 bind_sheet.save_png("res://qa/six_direction_source_bind_4x.png")
 quit()
