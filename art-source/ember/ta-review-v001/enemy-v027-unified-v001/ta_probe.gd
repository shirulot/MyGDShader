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
  var sf:SpriteFrames=load("res://output/"+unit+".tres")
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
     var source:=Image.load_from_file(ProjectSettings.globalize_path("res://output/%s/%s/f%02d.png"%[unit,name,i]))
     source.convert(Image.FORMAT_RGBA8)
     var actual:Image=texture.get_image();actual.convert(Image.FORMAT_RGBA8)
     var ok:bool=actual.get_data()==source.get_data() and texture.region==Rect2(i*128,0,128,128) and texture.atlas.get_size()==Vector2(COUNTS[a]*128,128) and sf.get_frame_duration(name,i)==1
     if not ok:errors.append("cell "+unit+name+str(i))
     cells.append({"unit":unit,"animation":name,"frame":i,"rgba_and_region":ok})
 var preview:Node2D=load("res://preview.tscn").instantiate()
 root.add_child(preview)
 var switches:Array=[]
 for u:int in range(4):
  preview.select_unit(u)
  if preview.target.sprite_frames!=resources[UNITS[u]] or preview.original.sprite_frames!=resources[UNITS[u]]:errors.append("unit route "+UNITS[u])
  for a:int in range(5):
   preview.select_action(a)
   if preview.target.frame!=0 or preview.original.frame!=0:errors.append("action reset")
   for running:bool in [false,true]:
    for d:int in range(8):
     preview.target.play();preview.original.play()
     preview.target.set_frame_and_progress(2,.375);preview.original.set_frame_and_progress(2,.375)
     if not running:preview.target.pause();preview.original.pause()
     preview.select_direction(d)
     var ok:bool=preview.target.animation==ACTIONS[a]+"_"+DIRS[d] and preview.target.frame==2 and absf(preview.target.frame_progress-.375)<.0001 and preview.target.is_playing()==running and preview.original.frame==2 and absf(preview.original.frame_progress-.375)<.0001
     if not ok:errors.append("direction state "+UNITS[u]+ACTIONS[a]+DIRS[d])
     switches.append({"unit":UNITS[u],"action":ACTIONS[a],"direction":DIRS[d],"running":running,"pass":ok})
 for actor:AnimatedSprite2D in [preview.target,preview.original]:
  if actor.centered or actor.texture_filter!=CanvasItem.TEXTURE_FILTER_NEAREST:errors.append("preview registration")
 preview.queue_free();await process_frame
 var players:Array=[];var actors:Array[AnimatedSprite2D]=[]
 for unit:String in UNITS:
  var sf:SpriteFrames=resources[unit]
  for name:StringName in sf.get_animation_names():
   for slow:bool in [false,true]:
    var actor:=AnimatedSprite2D.new();actor.sprite_frames=sf;actor.visible=false
    var state:Dictionary={"unit":unit,"animation":str(name),"slow":slow,"seen":[0],"looped":0,"finished":0,"expected_count":sf.get_frame_count(name),"expected_loop":sf.get_animation_loop(name)}
    actor.frame_changed.connect(func():
     if not state.seen.has(actor.frame):state.seen.append(actor.frame))
    actor.animation_looped.connect(func():state.looped+=1)
    actor.animation_finished.connect(func():state.finished+=1)
    actor.speed_scale=1.0/sf.get_animation_speed(name) if slow else 1.0
    root.add_child(actor);actor.play(name);actors.append(actor);players.append(state)
 var start:=Time.get_ticks_msec()
 while Time.get_ticks_msec()-start<9300:await process_frame
 for i:int in range(actors.size()):
  var actor:AnimatedSprite2D=actors[i];var state:Dictionary=players[i]
  state.seen.sort();state.last_frame=actor.frame;state.playing=actor.is_playing()
  state.pass=state.seen.size()==state.expected_count and (state.looped>=1 and state.finished==0 and state.playing if state.expected_loop else state.finished==1 and state.looped==0 and not state.playing and state.last_frame==state.expected_count-1)
  if not state.pass:errors.append("playback "+state.unit+state.animation+str(state.slow))
 var result:Dictionary={"status":"PASS" if errors.is_empty() else "FAIL","engine":Engine.get_version_info(),"cells":cells,"switches":switches,"players":players,"errors":errors,"scope":"Actual saved resources, preview routes,320 paused/running direction switches,320 natural normal/1FPS players; headless, no GPU replay."}
 FileAccess.open("res://../technical-cold-result.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "))
 print("TA_V027 ",result.status," cells=",cells.size()," switches=",switches.size()," players=",players.size())
 quit(0 if errors.is_empty() else 1)
