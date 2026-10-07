extends SceneTree
const Rig=preload("res://pilot_rig.gd")
func _initialize()->void:call_deferred("run")
func difference(a:Image,b:Image)->int:
 var aa:=a.get_data()
 var bb:=b.get_data()
 var count:=0
 for i in range(aa.size()):
  if aa[i]!=bb[i]:count+=1
 return count
func run()->void:
 var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/pilot_catalog_v013.json"))
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(128,128)
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 var background:=ColorRect.new()
 # 背景必须低于 rig 内的远侧肢体层，避免测试背景挡住负 z 的部件。
 background.z_index=-100
 background.size=Vector2(128,128)
 viewport.add_child(background)
 var png:=Sprite2D.new()
 png.centered=false
 png.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 viewport.add_child(png)
 var records:Array=[]
 var passed:=true
 for clip:Dictionary in data.clips:
  var rig:=Rig.new()
  rig.unit_id=clip.unit
  viewport.add_child(rig)
  var saved:=load(str(clip.tres)) as SpriteFrames
  for index in range(8):
   var path:="res://output/%s/move_down_right/f%02d.png"%[clip.unit,index]
   var image:=Image.load_from_file(ProjectSettings.globalize_path(path))
   image.convert(Image.FORMAT_RGBA8)
   var embedded:=saved.get_frame_texture("move_down_right",index).get_image()
   embedded.convert(Image.FORMAT_RGBA8)
   var resource_diff:=difference(image,embedded)
   passed=passed and resource_diff==0
   for color:String in ["white","black"]:
    background.color=Color.WHITE if color=="white" else Color.BLACK
    rig.visible=true
    png.visible=false
    rig.pose(index)
    await process_frame
    await RenderingServer.frame_post_draw
    var live:=viewport.get_texture().get_image()
    live.convert(Image.FORMAT_RGBA8)
    rig.visible=false
    png.visible=true
    png.texture=ImageTexture.create_from_image(image)
    await process_frame
    await RenderingServer.frame_post_draw
    var rendered_png:=viewport.get_texture().get_image()
    rendered_png.convert(Image.FORMAT_RGBA8)
    var gpu_diff:=difference(live,rendered_png)
    passed=passed and gpu_diff==0
    records.append({"unit":clip.unit,"frame":index,"background":color,"tres_vs_png_differing_channels":resource_diff,"live_rig_vs_png_differing_channels":gpu_diff})
  rig.queue_free()
  await process_frame
 var report:Dictionary={"status":"PASS" if passed else "FAIL","scope":"author GPU and saved resource roundtrip, not TA approval","catalog_sha256":FileAccess.get_sha256("res://output/pilot_catalog_v013.json"),"records":records}
 FileAccess.open("res://qa/pilot_gpu_roundtrip.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 print("PILOT_GPU_ROUNDTRIP_",report.status," | comparisons=",records.size())
 quit(0 if passed else 1)
