extends SceneTree
## 诊断范围固定；局部联系图不是单帧自动 bbox 归一化。
func _initialize() -> void:
	var records: Array = []
	var comparison := Image.create(48*8,64,false,Image.FORMAT_RGBA8)
	comparison.fill(Color.TRANSPARENT)
	var bind := Image.load_from_file(ProjectSettings.globalize_path("res://output/bind_pose.png"))
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://output/catalog_v004.json"))
	for index in range(8):
		var frame := Image.load_from_file(ProjectSettings.globalize_path("res://output/f%02d.png"%index))
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
		records.append({"frame":index,"head_chest_roi_rgba_differences":core_differences,"alpha_partial_pixels":alpha_partial,"visible_pixels":visible,"components":components(frame),"sha256":FileAccess.get_sha256("res://output/f%02d.png"%index)})
	comparison.save_png("res://qa/move_detail_1x.png")
	comparison.resize(1536,256,Image.INTERPOLATE_NEAREST)
	comparison.save_png("res://qa/move_detail_4x.png")
	FileAccess.open("res://qa/pixel_audit.json",FileAccess.WRITE).store_string(JSON.stringify({"scope":"diagnostic only, no visual acceptance","fixed_roi":[54,52,20,25],"frame_records":records},"\t"))
	print(JSON.stringify(records))
	quit()

func components(frame: Image) -> Array:
	var visited := PackedByteArray()
	visited.resize(128*128)
	var result: Array = []
	for y in range(128):
		for x in range(128):
			if visited[y*128+x] or frame.get_pixel(x,y).a<0.5: continue
			var queue: Array[Vector2i] = [Vector2i(x,y)]
			visited[y*128+x]=1
			var cursor:=0
			var minimum:=Vector2i(x,y)
			var maximum:=Vector2i(x,y)
			while cursor<queue.size():
				var point:=queue[cursor]
				cursor+=1
				minimum=minimum.min(point)
				maximum=maximum.max(point)
				for dy in range(-1,2):
					for dx in range(-1,2):
						var next:=point+Vector2i(dx,dy)
						if next.x<0 or next.y<0 or next.x>=128 or next.y>=128: continue
						if visited[next.y*128+next.x] or frame.get_pixelv(next).a<0.5: continue
						visited[next.y*128+next.x]=1
						queue.append(next)
			result.append({"pixels":queue.size(),"bbox":[minimum.x,minimum.y,maximum.x-minimum.x+1,maximum.y-minimum.y+1]})
	return result
