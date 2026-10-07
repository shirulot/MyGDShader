extends SceneTree
## 直接读取实际rig遮罩，按同源物理实例检查零件归属，记录短轴真实采样色。
const Rig=preload("res://rig.gd")
func _initialize()->void:call_deferred("run")
func run()->void:
 var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://rig.json"))
 var rows:Array=[];var passed:=true
 for direction:String in spec.configs:
  var rig:=Rig.new();rig.direction=direction;root.add_child(rig)
  var cfg:Dictionary=rig.raw.spec if direction=="down_right" else rig.raw.config
  var counts:Dictionary={};var sources:Dictionary={};var owner_counts:Dictionary={}
  var nodes:Dictionary=rig.raw.parts.duplicate();nodes.merge(rig.arms)
  for id:String in nodes:
   var group:="canonical"
   for p:Dictionary in cfg.parts:
    if p.id==id:group=p.get("source_kind","canonical")
   var sprite:Sprite2D=nodes[id].get_child(0)
   var source:Image=sprite.texture.get_image()
   var mask:Image=sprite.material.get_shader_parameter("ownership").get_image()
   if not counts.has(group):
    var array:=PackedInt32Array();array.resize(128*128);counts[group]=array;sources[group]=source
   owner_counts[id]=0
   for y in range(128):
    for x in range(128):
     if source.get_pixel(x,y).a>.5 and mask.get_pixel(x,y).r>.5:
      counts[group][y*128+x]+=1;owner_counts[id]+=1
  var groups:Array=[]
  for group:String in counts:
   var missing:Array=[];var multiple:Array=[]
   for y in range(128):
    for x in range(128):
     if sources[group].get_pixel(x,y).a<.5:continue
     if counts[group][y*128+x]==0:missing.append([x,y])
     if counts[group][y*128+x]>1:multiple.append([x,y,counts[group][y*128+x]])
   var okay:bool=missing.is_empty() and multiple.is_empty();passed=passed and okay
   groups.append({"instance":group,"missing":missing,"multiple":multiple,"passed":okay})
  var sockets:Array=[]
  for arm:Dictionary in rig.config.arms:
   var pixels:Array=[];var uv:Array=arm.socket_uv
   for y in range(uv[1],uv[1]+uv[3]):
    for x in range(uv[0],uv[0]+uv[2]):
     var c:Color=rig.raw.texture.get_image().get_pixel(x,y)
     pixels.append({"source_pixel":[x,y],"rgba":[c.r8,c.g8,c.b8,c.a8]})
   sockets.append({"part":arm.id,"uv_rect":uv,"source_pixels":pixels})
  rows.append({"direction":direction,"instances":groups,"owner_opaque_counts":owner_counts,"socket_uv_samples":sockets})
  rig.queue_free();await process_frame
 var report:Dictionary={"status":"PASS" if passed else "FAIL","catalog_sha256":FileAccess.get_sha256("res://output/catalog.json"),"records":rows,"limits":"Near/far in approved profiles are distinct same-source physical instances; ownership is unique within each instance. UV joint quads intentionally sample fixed pixels separately."}
 FileAccess.open("res://qa/ownership_audit.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("P26_OWNERSHIP_",report.status)
 quit(0 if passed else 1)
