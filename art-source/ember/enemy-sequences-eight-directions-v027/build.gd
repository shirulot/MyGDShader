extends SceneTree
## 从保存的相对路径SpriteFrames逐帧核对原PNG，不重绘或重新编码图集。
func _initialize()->void:
 var recipe:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assembly_recipe.json"))
 var resources:Dictionary={};var rows:Array=[];var passed:=true
 for unit:String in recipe.units:
  resources[unit]=ResourceLoader.load("res://output/"+unit+".tres","SpriteFrames",ResourceLoader.CACHE_MODE_IGNORE)
  assert(resources[unit]!=null)
 for clip:Dictionary in recipe.clips:
  var frames:SpriteFrames=resources[clip.unit]
  var meta:bool=frames.get_frame_count(clip.action)==int(clip.frame_count) and frames.get_animation_speed(clip.action)==float(clip.fps) and frames.get_animation_loop(clip.action)==bool(clip.loop)
  passed=passed and meta and FileAccess.get_sha256(clip.atlas)==str(clip.atlas_sha256)
  for index in range(clip.frame_count):
   var path:="res://output/%s/%s/f%02d.png"%[clip.unit,clip.action,index]
   var source:=Image.load_from_file(ProjectSettings.globalize_path(path));source.convert(Image.FORMAT_RGBA8)
   var saved:Image=frames.get_frame_texture(clip.action,index).get_image();saved.convert(Image.FORMAT_RGBA8)
   var equal:bool=source.get_data()==saved.get_data()
   var hash_equal:bool=FileAccess.get_sha256(path)==str(clip.frame_hashes[index])
   passed=passed and equal and hash_equal
   rows.append({"unit":clip.unit,"action":clip.action,"frame":index,"original_png_sha256_equal":hash_equal,"saved_resource_rgba_equal":equal})
 var report:Dictionary={"status":"PASS" if passed else "FAIL","scope":"file assembly only, no additional art approval","texture_binding":"relative PNG atlas paths","clip_count":recipe.clips.size(),"frame_count":rows.size(),"recipe_sha256":FileAccess.get_sha256("res://assembly_recipe.json"),"frames":rows}
 FileAccess.open("res://qa/assembly_integrity.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("ASSEMBLY_160_CLIPS_960_FRAMES_",report.status)
 quit(0 if passed else 1)
