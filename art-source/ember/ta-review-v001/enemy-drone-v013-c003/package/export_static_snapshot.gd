extends SceneTree
## 静态返修登记导出：每个输入图集只定一次源像素密度；批准 PNG 直接复制。
class AxisOverlay extends Node2D:
 var points:PackedVector2Array
 func _draw()->void:
  if points.size()!=2:return
  var a:=points[0]
  var b:=points[1]
  var elbow:=Vector2(b.x,a.y)
  draw_line(a,elbow,Color("469cce"),0.45)
  draw_line(elbow,b,Color("469cce"),0.45)
  draw_line(a,b,Color("2ce08b"),0.6)
  draw_circle(a,0.85,Color("e8449c"))
  draw_circle(b,0.85,Color("e8449c"))

func _initialize()->void:call_deferred("run")
func run()->void:
 assert(OS.get_cmdline_user_args().size()==1,"Pass one snapshot registration JSON")
 var spec_path:String=OS.get_cmdline_user_args()[0]
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(spec_path))
 var directory:="res://"+str(spec.output_directory)
 DirAccess.make_dir_recursive_absolute(directory)
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(128,128)
 viewport.transparent_bg=true
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 var sprite:=Sprite2D.new()
 sprite.centered=false
 sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 var material:=ShaderMaterial.new()
 material.shader=load("res://entity_cutout.gdshader")
 sprite.material=material
 viewport.add_child(sprite)
 var guide:=AxisOverlay.new()
 guide.z_index=10
 viewport.add_child(guide)
 var records:Array=[]
 var axis_images:Array[Image]=[]
 for entry:Dictionary in spec.entries:
  var path:=directory+"/"+str(entry.key)+".png"
  guide.visible=false
  var image:Image
  var row:Dictionary={"key":entry.key,"path":path,"scope":entry.scope}
  if entry.has("copy_path"):
   DirAccess.copy_absolute(ProjectSettings.globalize_path(entry.copy_path),ProjectSettings.globalize_path(path))
   image=Image.load_from_file(ProjectSettings.globalize_path(path))
   row.copied_from=entry.copy_path
   assert(FileAccess.get_sha256(path)==FileAccess.get_sha256(entry.copy_path))
  else:
   var atlas:=AtlasTexture.new()
   atlas.atlas=load(str(entry.source))
   var rect:Array=entry.source_rect
   atlas.region=Rect2(rect[0],rect[1],rect[2],rect[3])
   sprite.texture=atlas
   sprite.scale=Vector2.ONE*float(entry.scale)
   var source_anchor:=Vector2(entry.source_anchor[0],entry.source_anchor[1])
   var target_anchor:=Vector2(entry.target_anchor[0],entry.target_anchor[1])
   sprite.position=target_anchor-source_anchor*float(entry.scale)
   await process_frame
   await RenderingServer.frame_post_draw
   image=read_image(viewport)
   image.save_png(path)
   row.registration=entry
   if entry.has("source_axes"):
    var points:=PackedVector2Array()
    var point_records:Array=[]
    for point:Array in entry.source_axes:
     var native:=sprite.position+Vector2(point[0],point[1])*float(entry.scale)
     points.append(native)
     point_records.append([native.x,native.y])
    row.axis_centers_native=point_records
    row.axis_delta_native=[absf(points[1].x-points[0].x),absf(points[1].y-points[0].y)]
    guide.points=points
    guide.visible=true
    guide.queue_redraw()
    await process_frame
    await RenderingServer.frame_post_draw
    axis_images.append(read_image(viewport))
  row.sha256=FileAccess.get_sha256(path)
  row.bounds=str(image.get_used_rect())
  records.append(row)
 var columns:int=spec.columns
 var rows:int=ceili(float(records.size())/columns)
 for background:String in ["white","black"]:
  var contact:=Image.create(columns*128,rows*128,false,Image.FORMAT_RGBA8)
  contact.fill(Color.WHITE if background=="white" else Color.BLACK)
  for index in range(records.size()):
   var image:=Image.load_from_file(ProjectSettings.globalize_path(records[index].path))
   contact.blend_rect(image,Rect2i(0,0,128,128),Vector2i((index%columns)*128,(index/columns)*128))
  contact.save_png(directory+"/comparison_"+background+"_1x.png")
  contact.resize(columns*512,rows*512,Image.INTERPOLATE_NEAREST)
  contact.save_png(directory+"/comparison_"+background+"_4x.png")
 if not axis_images.is_empty():
  var contact:=Image.create(axis_images.size()*128,128,false,Image.FORMAT_RGBA8)
  contact.fill(Color.WHITE)
  for index in range(axis_images.size()):contact.blend_rect(axis_images[index],Rect2i(0,0,128,128),Vector2i(index*128,0))
  contact.resize(axis_images.size()*1024,1024,Image.INTERPOLATE_NEAREST)
  contact.save_png(directory+"/axis_guides_8x.png")
 FileAccess.open(directory+"/catalog.json",FileAccess.WRITE).store_string(JSON.stringify({"name":spec.name,"status":"PENDING_TA_STATIC_REVIEW","scope":spec.scope,"registration_sha256":FileAccess.get_sha256(spec_path),"columns":columns,"entries":records},"\t"))
 print("EXPORTED_STATIC_SNAPSHOT_",spec.name)
 quit()

func read_image(viewport:SubViewport)->Image:
 var result:=viewport.get_texture().get_image()
 result.convert(Image.FORMAT_RGBA8)
 for y in range(128):
  for x in range(128):
   if result.get_pixel(x,y).a8==0:result.set_pixel(x,y,Color.TRANSPARENT)
 return result
