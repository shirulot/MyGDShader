extends SceneTree
## 从真实项目目标的绝对路径加载四个已安装资源，逐帧比对；不启动或修改主游戏。
func _initialize()->void:
 var args:=OS.get_cmdline_user_args()
 var bundle_root:String=args[0] if not args.is_empty() else ProjectSettings.globalize_path("res://")
 var recipe:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(bundle_root.path_join("assembly_recipe.json")))
 var destination:="E:/dev/shader/godot-shader/godot-shader-simple/assets/ember/characters/enemies_v003"
 var resources:Dictionary={};var records:Array=[];var passed:=true
 for unit:String in recipe.units:
  resources[unit]=ResourceLoader.load(destination+"/"+unit+".tres","SpriteFrames",ResourceLoader.CACHE_MODE_IGNORE)
  assert(resources[unit]!=null)
 for clip:Dictionary in recipe.clips:
  var frames:SpriteFrames=resources[clip.unit]
  var meta_ok:bool=frames.get_frame_count(clip.action)==int(clip.frame_count) and frames.get_animation_speed(clip.action)==float(clip.fps) and frames.get_animation_loop(clip.action)==bool(clip.loop)
  passed=passed and meta_ok
  for i in range(clip.frame_count):
   var path:="%s/%s/%s/f%02d.png"%[destination,clip.unit,clip.action,i]
   var png:=Image.load_from_file(path);png.convert(Image.FORMAT_RGBA8)
   var saved:Image=frames.get_frame_texture(clip.action,i).get_image();saved.convert(Image.FORMAT_RGBA8)
   var okay:bool=saved.get_data()==png.get_data() and FileAccess.get_sha256(path)==str(clip.frame_hashes[i])
   passed=passed and okay;records.append({"unit":clip.unit,"action":clip.action,"frame":i,"passed":okay})
 var report:Dictionary={"status":"PASS" if passed else "FAIL","destination":destination,"clips":160,"frames":records.size(),"records":records,"scope":"Actual installed absolute-path SpriteFrames loading and pixel equality; main gameplay not launched."}
 FileAccess.open(bundle_root.path_join("qa/installed_resource_load.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("INSTALLED_RESOURCE_",report.status," | clips=160 | frames=",records.size())
 quit(0 if passed else 1)
