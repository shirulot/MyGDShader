extends SceneTree
## 诊断范围固定；局部联系图不是单帧自动 bbox 归一化。
func _initialize() -> void:
	var records: Array = []
	var comparison := Image.create(48*8,64,false,Image.FORMAT_RGBA8)
	comparison.fill(Color.TRANSPARENT)
	var bind := Image.load_from_file("res://output/bind_pose.png")
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog_v002.json"))
	for index in range(8):
		var frame := Image.load_from_file("res://output/f%02d.png"%index)
		var body_y := int(catalog.poses[index].body_translation_px[1])
		var core_differences := 0
		var alpha_partial := 0
		var visible := 0
		for y in range(128):
			for x in range(128):
				var alpha := frame.get_pixel(x,y).a8
				if alpha>0: visible+=1
				if alpha>0 and alpha<255: alpha_partial+=1
		# 固定上躯干 ROI，仅撤销已登记的 y 方向刚性移动。
		for y in range(52,77):
			for x in range(54,74):
				if frame.get_pixel(x,y+body_y)!=bind.get_pixel(x,y): core_differences+=1
		comparison.blit_rect(frame,Rect2i(40,48,48,64),Vector2i(index*48,0))
		records.append({"frame":index,"head_chest_roi_rgba_differences":core_differences,"alpha_partial_pixels":alpha_partial,"visible_pixels":visible,"sha256":FileAccess.get_sha256("res://output/f%02d.png"%index)})
	comparison.save_png("res://qa/move_detail_1x.png")
	comparison.resize(1536,256,Image.INTERPOLATE_NEAREST)
	comparison.save_png("res://qa/move_detail_4x.png")
	FileAccess.open("res://qa/pixel_audit.json",FileAccess.WRITE).store_string(JSON.stringify({"scope":"diagnostic only, no visual acceptance","fixed_roi":[54,52,20,25],"frame_records":records},"\t"))
	print(JSON.stringify(records))
	quit()
