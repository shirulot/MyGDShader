extends SceneTree
## 检查最终四个SpriteFrames在实际GPU上的960帧，不依赖原分批rig的自检结果。
const UNITS=["enemy_patrol","enemy_tracked_heavy","enemy_cutter","enemy_scout_drone"]
const DIRS=["down","down_left","left","up_left","up","up_right","right","down_right"]
const ACTIONS=["idle","move","attack","hit","death"]
func _initialize()->void:call_deferred("run")
func run()->void:
 var recipe:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assembly_recipe.json"))
 var viewport:=SubViewport.new();viewport.size=Vector2i(1024,1024)
 viewport.transparent_bg=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 var backdrop:=ColorRect.new();backdrop.size=Vector2(1024,1024);viewport.add_child(backdrop)
 var records:Array=[];var passed:=true
 for unit:String in UNITS:
  var frames:SpriteFrames=load("res://output/"+unit+".tres")
  assert(frames.get_animation_names().size()==40)
  for kind:String in ACTIONS:
   var sprites:Array[AnimatedSprite2D]=[]
   for row in range(8):
    var action:String=kind+"_"+DIRS[row]
    for index in range(frames.get_frame_count(action)):
     var actor:=AnimatedSprite2D.new();actor.sprite_frames=frames;actor.centered=false
     actor.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;actor.position=Vector2(index*128,row*128)
     viewport.add_child(actor);actor.play(action);actor.pause();actor.set_frame_and_progress(index,0)
     sprites.append(actor)
   for background:String in ["white","black"]:
    backdrop.color=Color.WHITE if background=="white" else Color.BLACK
    await process_frame;await RenderingServer.frame_post_draw
    var rendered:=viewport.get_texture().get_image();rendered.convert(Image.FORMAT_RGBA8)
    for actor:AnimatedSprite2D in sprites:
     var path:="res://output/%s/%s/f%02d.png"%[unit,actor.animation,actor.frame]
     var source:=Image.load_from_file(ProjectSettings.globalize_path(path));source.convert(Image.FORMAT_RGBA8)
     var bad:=0
     for y in range(128):
      for x in range(128):
       var expected:Color=source.get_pixel(x,y)
       if expected.a8==0:expected=backdrop.color
       var actual:Color=rendered.get_pixel(x+int(actor.position.x),y+int(actor.position.y))
       if actual.to_rgba32()!=expected.to_rgba32():bad+=1
     passed=passed and bad==0
     records.append({"unit":unit,"action":actor.animation,"frame":actor.frame,"background":background,"rgba_differences":bad,"passed":bad==0})
    rendered.save_png("res://qa/"+unit+"_"+kind+"_"+background+"_native_grid.png")
   for actor:AnimatedSprite2D in sprites:actor.queue_free()
   await process_frame
 var report:Dictionary={"status":"PASS" if passed else "FAIL","catalog_sha256":FileAccess.get_sha256("res://output/catalog.json"),"records":records,"renderer":RenderingServer.get_video_adapter_name(),"clip_count":recipe.clips.size(),"frame_count":960}
 FileAccess.open("res://qa/gpu_roundtrip.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("ASSEMBLY_GPU_",report.status," | records=1920")
 quit(0 if passed else 1)
