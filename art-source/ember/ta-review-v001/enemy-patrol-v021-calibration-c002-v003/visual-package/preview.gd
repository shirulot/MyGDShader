extends Node2D
## 静态造型闸门：共同画布、整数倍缩放，不包含动作通过状态。
func _ready()->void:
 texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 for row in range(2):
  var direction:String=["left","right"][row]
  for column in range(2):
   var where:=Vector2(24+column*408,50+row*414)
   var label:=Label.new()
   label.text=direction+(" / ORIGINAL S002" if column==0 else " / C002 CANDIDATE")
   label.position=where-Vector2(0,26)
   add_child(label)
   var back:=ColorRect.new()
   back.color=Color("d2d6dc")
   back.position=where
   back.size=Vector2(384,384)
   add_child(back)
   show_image(("res://source/"+direction+".png") if column==0 else ("res://output/neutral_"+direction+".png"),where,3)
  for index in range(3):
   var kind:String=["body","near","far"][index]
   show_image("res://output/"+direction+"_"+kind+".png",Vector2(864+index*132,110+row*414),1)
func show_image(path:String,where:Vector2,factor:int)->void:
 var sprite:=Sprite2D.new()
 sprite.texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(path)))
 sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
 sprite.centered=false
 sprite.position=where
 sprite.scale=Vector2.ONE*factor
 add_child(sprite)
