extends SceneTree
## 仅从已冻结图集重建辅助联系图，不运行rig、不写任何正式帧/图集。
func _initialize()->void:
 var catalog:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog_v010.json"))
 var roi:=Rect2i(24,32,80,80)
 var omissions:Array=[]
 for action:String in catalog.actions:
  var atlas:=Image.load_from_file(ProjectSettings.globalize_path(catalog.actions[action].atlas))
  var count:int=catalog.actions[action].frame_count
  for frame in range(count):
   var omitted:=0
   for y in range(128):
    for x in range(128):
     if atlas.get_pixel(frame*128+x,y).a>0.0 and not roi.has_point(Vector2i(x,y)):omitted+=1
   omissions.append({"action":action,"frame":frame,"omitted_visible_pixels":omitted})
  for background:String in ["black","white"]:
   var contact:=Image.create(80*count,80,false,Image.FORMAT_RGBA8)
   contact.fill(Color.BLACK if background=="black" else Color.WHITE)
   for frame in range(count):contact.blend_rect(atlas,Rect2i(frame*128+24,32,80,80),Vector2i(frame*80,0))
   contact.save_png("res://qa/%s_%s_1x.png"%[action,background])
   contact.resize(count*320,320,Image.INTERPOLATE_NEAREST)
   contact.save_png("res://qa/%s_%s_4x.png"%[action,background])
 var passed:=true
 for item:Dictionary in omissions:passed=passed and item.omitted_visible_pixels==0
 FileAccess.open("res://qa/preview_crop_audit_r1.json",FileAccess.WRITE).store_string(JSON.stringify({"status":"PASS" if passed else "FAIL","roi":[24,32,80,80],"frames":omissions,"formal_pngs_written":false},"\t"))
 quit(0 if passed else 1)
