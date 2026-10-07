extends SceneTree
## 同帧rig与普通PNG按正常混合显示在黑白底，核查导出表示。
const Rig=preload("res://fixed_rig.gd")
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var viewport:=SubViewport.new()
	viewport.size=Vector2i(128,128)
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var backdrop:=ColorRect.new()
	backdrop.size=Vector2(128,128)
	viewport.add_child(backdrop)
	var rig:=Rig.new()
	viewport.add_child(rig)
	var png:=Sprite2D.new()
	png.centered=false
	png.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	viewport.add_child(png)
	var records:Array=[]
	var failed:=false
	for background: String in ["black","white"]:
		backdrop.color=Color.BLACK if background=="black" else Color.WHITE
		for index in range(8):
			rig.pose(index)
			rig.visible=true
			png.visible=false
			await process_frame
			await RenderingServer.frame_post_draw
			var rig_image:=viewport.get_texture().get_image()
			rig_image.convert(Image.FORMAT_RGBA8)
			rig.visible=false
			var raw:=Image.load_from_file(ProjectSettings.globalize_path("res://output/f%02d.png"%index))
			png.texture=ImageTexture.create_from_image(raw)
			png.visible=true
			await process_frame
			await RenderingServer.frame_post_draw
			var png_image:=viewport.get_texture().get_image()
			png_image.convert(Image.FORMAT_RGBA8)
			var difference:=0
			var maximum:=0
			var a:=rig_image.get_data()
			var b:=png_image.get_data()
			for p in range(a.size()):
				if a[p]!=b[p]: difference+=1
				maximum=maxi(maximum,absi(int(a[p])-int(b[p])))
			if difference>0: failed=true
			records.append({"frame":index,"background":background,"differing_channels":difference,"max_channel_error":maximum})
			if index in [1,2,5,6]:
				var pair:=Image.create(96,64,false,Image.FORMAT_RGBA8)
				pair.blit_rect(rig_image,Rect2i(40,48,48,64),Vector2i.ZERO)
				pair.blit_rect(png_image,Rect2i(40,48,48,64),Vector2i(48,0))
				pair.resize(384,256,Image.INTERPOLATE_NEAREST)
				pair.save_png("res://qa/roundtrip_f%02d_%s_4x.png"%[index,background])
				# 修前采用冻结v002实际PNG的普通显示，与新PNG同一底色、同一ROI。
				var old:=Image.load_from_file(ProjectSettings.globalize_path("res://comparison/v002_f%02d.png"%index))
				png.texture=ImageTexture.create_from_image(old)
				await process_frame
				await RenderingServer.frame_post_draw
				var before:=viewport.get_texture().get_image()
				before.convert(Image.FORMAT_RGBA8)
				var change:=Image.create(96,64,false,Image.FORMAT_RGBA8)
				change.blit_rect(before,Rect2i(40,48,48,64),Vector2i.ZERO)
				change.blit_rect(png_image,Rect2i(40,48,48,64),Vector2i(48,0))
				change.save_png("res://qa/before_after_f%02d_%s_1x.png"%[index,background])
				change.resize(384,256,Image.INTERPOLATE_NEAREST)
				change.save_png("res://qa/before_after_f%02d_%s_4x.png"%[index,background])
	var result:Dictionary={"status":"FAIL" if failed else "PASS","scope":"16 actual GPU rig versus straight-alpha PNG comparisons, opaque black/white backgrounds","atlas_sha256":FileAccess.get_sha256("res://output/move_down_v004.png"),"records":records}
	FileAccess.open("res://qa/render_roundtrip.json",FileAccess.WRITE).store_string(JSON.stringify(result,"\t"))
	print(JSON.stringify(result))
	quit(1 if failed else 0)
