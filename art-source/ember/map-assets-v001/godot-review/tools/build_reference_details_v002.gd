extends SceneTree
## 实际生图细节的生产切片器：只取 ROI、按几何足迹去掉母稿背景、nearest 缩放。
## 不重新绘制材质或改变颜色。板缝保留窄蓝灰肩边，适合铺在同套钢板上。

const SOURCE := "res://art-source/ember/reference-floor-v002/details_modules_master_v001.png"
const OUT := "res://assets/ember/environment/reference_floor_v002/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var source := Image.load_from_file(ProjectSettings.globalize_path(SOURCE))
	assert(source != null and source.get_size() == Vector2i(1536,1024))
	var entries: Array[Dictionary] = []
	# 去掉宽矩形底漆板；只保留细缝两侧的窄肩与真实端头扣件。
	entries.append(_save(source,"seam_horizontal",Rect2i(16,219,485,64),Vector2i(512,68),[
		Rect2i(16,244,485,17),Rect2i(18,236,38,35),Rect2i(465,236,35,35)]))
	entries.append(_save(source,"seam_vertical",Rect2i(738,9,60,484),Vector2i(68,512),[
		Rect2i(758,9,20,484),Rect2i(749,199,38,36),Rect2i(749,451,38,38)]))
	# 内拐角只保留钢板肩边的实际 L 足迹；不把母稿灰色背景也铺上地板。
	entries.append(_save(source,"seam_elbow",Rect2i(1069,178,286,315),Vector2i(320,352),[
		Rect2i(1069,204,277,17),Rect2i(1328,207,19,284),
		Rect2i(1312,196,42,51),Rect2i(1312,452,42,39)]))
	entries.append(_save(source,"grate_hatch",Rect2i(49,623,418,264),Vector2i(256,192)))
	var rail_h_mask: Array[Rect2i] = [Rect2i(568,724,407,29),Rect2i(582,753,387,34)]
	for post_x: int in [553,754,957]:
		rail_h_mask.append(Rect2i(post_x,710,36,81))
		rail_h_mask.append(Rect2i(post_x-16,763,64,52))
	entries.append(_save(source,"rail_horizontal",Rect2i(536,709,471,108),Vector2i(384,88),rail_h_mask))
	var rail_l_mask: Array[Rect2i] = [Rect2i(1090,794,339,29),Rect2i(1106,825,307,34),
		Rect2i(1410,568,26,238),Rect2i(1399,588,47,209)]
	for post: Vector2i in [Vector2i(1079,781),Vector2i(1243,781),Vector2i(1405,781),Vector2i(1405,724),Vector2i(1405,549)]:
		rail_l_mask.append(Rect2i(post,Vector2i(35,75)))
		rail_l_mask.append(Rect2i(post+Vector2i(-14,37),Vector2i(62,61)))
	entries.append(_save(source,"rail_elbow",Rect2i(1065,549,393,332),Vector2i(284,240),rail_l_mask))
	var report := {"source":SOURCE,"source_sha256":FileAccess.get_sha256(SOURCE),
		"processing":"Original artist RGBA crops, explicit outside-footprint alpha, nearest resize; no art repaint or palette quantization.",
		"placement":"Optional Sprite2D overlays, scale 0.25 in the 32 world/128 texture pipeline. Not terrain connectivity input.","entries":entries}
	var file := FileAccess.open(OUT+"details_catalog_v002.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t")+"\n")
	print("REFERENCE_DETAILS_V002_PASS: ",entries.size()," artist overlays saved")
	quit()

func _save(source: Image,label: String,roi: Rect2i,size: Vector2i,footprint: Array[Rect2i]=[]) -> Dictionary:
	assert(Rect2i(Vector2i.ZERO,source.get_size()).encloses(roi))
	var img := source.get_region(roi)
	img.convert(Image.FORMAT_RGBA8)
	if not footprint.is_empty():
		for y in range(img.get_height()):
			for x in range(img.get_width()):
				var retained := false
				for rect: Rect2i in footprint:
					if rect.has_point(roi.position+Vector2i(x,y)):
						retained = true
						break
				if not retained: img.set_pixel(x,y,Color(0,0,0,0))
	img.resize(size.x,size.y,Image.INTERPOLATE_NEAREST)
	var path := OUT+label+"_artist_v002.png"
	assert(img.save_png(path) == OK)
	return {"name":label,"path":path,"source_roi":[roi.position.x,roi.position.y,roi.size.x,roi.size.y],
		"native_dimensions":[size.x,size.y],"world_dimensions":[size.x/4.0,size.y/4.0],"uses_explicit_alpha_mask":not footprint.is_empty()}
