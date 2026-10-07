extends SceneTree
const Rig=preload("res://rig.gd")
func _initialize()->void:call_deferred("run")
func differences(a:Image,b:Image)->int:
 a.convert(Image.FORMAT_RGBA8)
 b.convert(Image.FORMAT_RGBA8)
 var aa:=a.get_data()
 var bb:=b.get_data()
 var result:=0
 for index in range(aa.size()):
  if aa[index]!=bb[index]:result+=1
 return result
func run()->void:
 var catalog:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog.json"))
 var saved:=load(str(catalog.tres)) as SpriteFrames
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(128,128)
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 var backdrop:=ColorRect.new()
 backdrop.size=Vector2(128,128)
 backdrop.z_index=-100
 viewport.add_child(backdrop)
 var png:=Sprite2D.new()
 png.centered=false
 png.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 viewport.add_child(png)
 var records:Array=[]
 var passed:=true
 for clip:Dictionary in catalog.clips:
  var rig:Node2D=null
  if clip.status!="PRESERVED_TA_APPROVED":
   rig=Rig.new()
   rig.direction=clip.direction
   viewport.add_child(rig)
  for index in range(8):
   var path:="res://output/%s/%s/f%02d.png"%[clip.unit,clip.action,index]
   var frame:=Image.load_from_file(ProjectSettings.globalize_path(path))
   var difference:=differences(frame,saved.get_frame_texture(clip.action,index).get_image())
   passed=passed and difference==0
   if rig==null:
    records.append({"action":clip.action,"frame":index,"preserved":true,"tres_vs_png":difference})
    continue
   for color:String in ["white","black"]:
    backdrop.color=Color.WHITE if color=="white" else Color.BLACK
    rig.visible=true
    png.visible=false
    rig.pose(index)
    await process_frame
    await RenderingServer.frame_post_draw
    var live:=viewport.get_texture().get_image()
    rig.visible=false
    png.visible=true
    png.texture=ImageTexture.create_from_image(frame)
    await process_frame
    await RenderingServer.frame_post_draw
    var gpu_difference:=differences(live,viewport.get_texture().get_image())
    passed=passed and gpu_difference==0
    records.append({"action":clip.action,"frame":index,"background":color,"tres_vs_png":difference,"live_rig_vs_png":gpu_difference})
  if rig!=null:rig.queue_free()
  await process_frame
 var report:Dictionary={"status":"PASS" if passed else "FAIL","catalog_sha256":FileAccess.get_sha256("res://output/catalog.json"),"records":records}
 FileAccess.open("res://qa/gpu_roundtrip.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
 print("HEAVY_GPU_",report.status," | records=",records.size())
 quit(0 if passed else 1)
