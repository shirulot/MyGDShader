extends SceneTree
## TA独立小探针：资源和场景加载；不调用制作方GPU捕获、导出或全播放器测试。
var records:Array=[]
func check(name:String,passed:bool,detail:Variant=null)->void:
 records.append({"check":name,"pass":passed,"detail":detail})
func _initialize()->void:
 call_deferred("run")
func run()->void:
 var sf=load("res://output/enemy_patrol_pilot_v013.tres") as SpriteFrames
 check("embedded SpriteFrames loads",sf!=null)
 if sf!=null:
  check("only SE pilot animation",sf.get_animation_names()==PackedStringArray(["move_down_right"]))
  check("8 frames",sf.get_frame_count("move_down_right")==8)
  check("8FPS",sf.get_animation_speed("move_down_right")==8.0)
  check("loop",sf.get_animation_loop("move_down_right"))
  check("embedded resource external dependencies empty",ResourceLoader.get_dependencies("res://output/enemy_patrol_pilot_v013.tres").is_empty())
  for i in range(8):
   var tex=sf.get_frame_texture("move_down_right",i) as AtlasTexture
   var valid=tex!=null and tex.region==Rect2(i*128,0,128,128) and tex.atlas.get_width()==1024 and tex.atlas.get_height()==128
   check("frame%d atlas registration"%i,valid)
   check("frame%d duration"%i,sf.get_frame_duration("move_down_right",i)==1.0)
 var packed=load("res://preview.tscn") as PackedScene
 check("preview scene loads",packed!=null)
 if packed!=null:
  var preview=packed.instantiate()
  root.add_child(preview)
  await process_frame
  await process_frame
  check("preview enabled unit patrol",preview.unit_index==0)
  check("preview contains2 made+8 static animations",preview.target.sprite_frames.get_animation_names().size()==10)
  check("preview Nearest",preview.target.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST)
  preview.playing=false
  preview.approved.pause()
  preview.target.pause()
  preview.approved.set_frame_and_progress(3,0.375)
  preview.select_direction(7)
  check("SE switch preserves made phase",preview.target.animation=="move_down_right" and preview.target.frame==3 and is_equal_approx(preview.target.frame_progress,0.375))
  preview.select_direction(5)
  check("unmade NE uses static",preview.target.animation=="neutral_up_right" and preview.target.frame==0)
  check("unmade NE preserves down reference phase",preview.approved.frame==3 and is_equal_approx(preview.approved.frame_progress,0.375))
  preview.queue_free()
 var failed=records.filter(func(r):return not r["pass"])
 var report={"status":"PASS" if failed.is_empty() else "FAIL","scope":"TA independent headless cold resource/scene/property checks only; no GPU framebuffer or natural-loop test", "engine":Engine.get_version_info()["string"],"display_server":DisplayServer.get_name(),"checks":records,"passed":records.size()-failed.size(),"total":records.size(),"failed":failed}
 var report_path:String=OS.get_cmdline_user_args()[0]
 FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 print("TA_COLD_MINIMAL ",report.status," ",report.passed,"/",report.total)
 quit(0 if failed.is_empty() else 1)
