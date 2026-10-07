extends SceneTree
## 只汇总已经冻结的PNG，绝不重新生成或渲染角色。以保存后资源的原生像素逐帧核对。
func _initialize()->void:
 var recipe:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assembly_recipe.json"))
 var resources:Dictionary={}
 var passed:=true
 var rows:Array=[]
 for clip:Dictionary in recipe.clips:
  var unit:String=clip.unit
  if not resources.has(unit):
   resources[unit]=SpriteFrames.new()
   resources[unit].remove_animation("default")
  var frames:SpriteFrames=resources[unit]
  var atlas:=Image.load_from_file(ProjectSettings.globalize_path(clip.atlas))
  passed=passed and FileAccess.get_sha256(clip.atlas)==str(clip.atlas_sha256)
  var texture:=ImageTexture.create_from_image(atlas)
  frames.add_animation(clip.action)
  frames.set_animation_speed(clip.action,clip.fps)
  frames.set_animation_loop(clip.action,clip.loop)
  for index in range(clip.frame_count):
   var region:=AtlasTexture.new()
   region.atlas=texture
   region.region=Rect2(index*128,0,128,128)
   frames.add_frame(clip.action,region)
 for unit:String in resources:
  passed=passed and ResourceSaver.save(resources[unit],"res://output/"+unit+".tres")==OK
 for clip:Dictionary in recipe.clips:
  var frames:=ResourceLoader.load("res://output/"+str(clip.unit)+".tres","SpriteFrames",ResourceLoader.CACHE_MODE_IGNORE) as SpriteFrames
  passed=passed and frames.get_frame_count(clip.action)==int(clip.frame_count) and frames.get_animation_speed(clip.action)==float(clip.fps) and frames.get_animation_loop(clip.action)==bool(clip.loop)
  for index in range(clip.frame_count):
   var path:="res://output/%s/%s/f%02d.png"%[clip.unit,clip.action,index]
   var source:=Image.load_from_file(ProjectSettings.globalize_path(path))
   var saved:Image=frames.get_frame_texture(clip.action,index).get_image()
   saved.convert(Image.FORMAT_RGBA8)
   source.convert(Image.FORMAT_RGBA8)
   var equal:=source.get_data()==saved.get_data()
   var hash_equal:=FileAccess.get_sha256(path)==str(clip.frame_hashes[index])
   passed=passed and equal and hash_equal
   rows.append({"unit":clip.unit,"action":clip.action,"frame":index,"original_png_sha256_equal":hash_equal,"saved_resource_rgba_equal":equal})
 FileAccess.open("res://qa/assembly_integrity.json",FileAccess.WRITE).store_string(JSON.stringify({"status":"PASS" if passed else "FAIL","scope":"file assembly only, no additional art approval","clip_count":recipe.clips.size(),"frame_count":rows.size(),"recipe_sha256":FileAccess.get_sha256("res://assembly_recipe.json"),"frames":rows},"\t"))
 print("ASSEMBLY_20_CLIPS_120_FRAMES_", "PASS" if passed else "FAIL")
 quit(0 if passed else 1)
