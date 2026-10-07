extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var viewport:=SubViewport.new()
 viewport.size=Vector2i(640,720)
 viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
 root.add_child(viewport)
 var bg:=ColorRect.new()
 bg.size=Vector2(640,720)
 bg.color=Color("eeeeee")
 viewport.add_child(bg)
 for direction in ["down_left","left","up_left","up","up_right","right","down_right"]:
  var sprite:=Sprite2D.new()
  sprite.texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://source/"+direction+".png")))
  sprite.centered=false
  sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
  sprite.scale=Vector2(10,10)
  sprite.position=Vector2(-32*10,-36*10)
  viewport.add_child(sprite)
  var labels:Array=[]
  for y in range(40,109,4):
   var label:=Label.new()
   label.text=str(y)
   label.position=Vector2(0,(y-36)*10)
   label.add_theme_color_override("font_color",Color.RED)
   viewport.add_child(label)
   labels.append(label)
  for x in range(36,96,4):
   var label:=Label.new()
   label.text=str(x)
   label.position=Vector2((x-32)*10,0)
   label.add_theme_color_override("font_color",Color.RED)
   viewport.add_child(label)
   labels.append(label)
  await process_frame
  await RenderingServer.frame_post_draw
  viewport.get_texture().get_image().save_png("res://qa/source_"+direction+"_10x.png")
  sprite.queue_free()
  for label in labels:label.queue_free()
  await process_frame
 quit()
