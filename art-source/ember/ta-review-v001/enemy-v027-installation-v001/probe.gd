extends SceneTree
## 独立冷包验证：真实保存的资源、预览控制函数、自然计时播放器。
const UNITS=["enemy_patrol","enemy_tracked_heavy","enemy_cutter","enemy_scout_drone"]
const DIRS=["down","down_left","left","up_left","up","up_right","right","down_right"]
const ACTIONS=["idle","move","attack","hit","death"]
const COUNTS=[4,8,6,4,8]
const RATES=[4,8,10,12,10]
func _initialize()->void:call_deferred("audit")
func audit()->void:
 var errors:Array=[]
 var resources:Dictionary={}
 var cells:Array=[]
 for unit:String in UNITS:
  var sf:SpriteFrames=load("res://assets/ember/characters/enemies_v003/"+unit+".tres")
  if sf==null:errors.append("missing "+unit);continue
  resources[unit]=sf
  if sf.get_animation_names().size()!=40:errors.append("clip count "+unit)
  for a:int in range(5):
   for d:String in DIRS:
    var name:String=ACTIONS[a]+"_"+d
    if not sf.has_animation(name):errors.append("missing animation "+unit+name);continue
    if sf.get_frame_count(name)!=COUNTS[a] or sf.get_animation_speed(name)!=RATES[a] or sf.get_animation_loop(name)!=(a<2):errors.append("timing "+unit+name)
    for i:int in range(COUNTS[a]):
     var texture:AtlasTexture=sf.get_frame_texture(name,i)
     var source:=Image.load_from_file(ProjectSettings.globalize_path("res://assets/ember/characters/enemies_v003/%s/%s/f%02d.png"%[unit,name,i]))
     source.convert(Image.FORMAT_RGBA8)
     var actual:Image=texture.get_image();actual.convert(Image.FORMAT_RGBA8)
     var ok:bool=actual.get_data()==source.get_data() and texture.region==Rect2(i*128,0,128,128) and texture.atlas.get_size()==Vector2(COUNTS[a]*128,128) and sf.get_frame_duration(name,i)==1
     if not ok:errors.append("cell "+unit+name+str(i))
     cells.append({"unit":unit,"animation":name,"frame":i,"rgba_and_region":ok})
 var result={"status":"PASS" if errors.is_empty() else "FAIL","cells":cells,"errors":errors,"scope":"Actual main-project res paths; headless resource RGBA, region and timing validation; no GPU or gameplay test."}
 FileAccess.open("E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-v027-installation-v001/resource-load.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "))
 print("TA_INSTALLED ",result.status," cells=",cells.size())
 quit(0 if errors.is_empty() else 1)
