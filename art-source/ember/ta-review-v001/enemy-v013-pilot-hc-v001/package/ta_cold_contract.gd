extends SceneTree
## 独立冷加载合同；不运行作者capture/export，不覆盖原PNG或TRES。
const Preview = preload("res://preview.gd")
const UNITS = ["enemy_tracked_heavy", "enemy_cutter"]
var checks: Array[Dictionary] = []
func record(name: String, passed: bool) -> void:
	checks.append({"name":name,"pass":passed})
	if not passed: print("TA_FAIL ",name)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://output/pilot_catalog_v013.json"))
	record("canvas_root_registration",Vector2(catalog.canvas[0],catalog.canvas[1])==Vector2(128,128) and Vector2(catalog.root[0],catalog.root[1])==Vector2(64,104))
	for unit: String in UNITS:
		var frames: SpriteFrames = load("res://output/"+unit+"_pilot_v013.tres")
		record(unit+"_single_clip_contract",frames!=null and frames.get_animation_names()==PackedStringArray(["move_down_right"]) and frames.get_frame_count("move_down_right")==8 and is_equal_approx(frames.get_animation_speed("move_down_right"),8) and frames.get_animation_loop("move_down_right"))
		var saved: AtlasTexture = frames.get_frame_texture("move_down_right",0)
		var atlas := Image.load_from_file(ProjectSettings.globalize_path("res://output/"+unit+"/move_down_right.png"))
		atlas.convert(Image.FORMAT_RGBA8)
		var embedded := saved.atlas.get_image()
		embedded.convert(Image.FORMAT_RGBA8)
		record(unit+"_embedded_atlas_full_rgba",embedded.get_size()==Vector2i(1024,128) and embedded.get_data()==atlas.get_data())
		for index in range(8):
			var frame: AtlasTexture = frames.get_frame_texture("move_down_right",index)
			record(unit+"_region_"+str(index),frame.region==Rect2(index*128,0,128,128) and frame.get_size()==Vector2(128,128) and is_equal_approx(frames.get_frame_duration("move_down_right",index),1))
			var raw := Image.load_from_file(ProjectSettings.globalize_path("res://output/"+unit+"/move_down_right/f%02d.png"%index))
			raw.convert(Image.FORMAT_RGBA8)
			var crop := frame.atlas.get_image().get_region(Rect2i(frame.region))
			crop.convert(Image.FORMAT_RGBA8)
			record(unit+"_saved_frame_rgba_"+str(index),crop.get_data()==raw.get_data())
	var preview := Preview.new()
	root.add_child(preview)
	preview.playing=false
	preview.set_process(false)
	record("preview_picker_only_two_enabled_units",preview.unit_picker.item_count==2 and preview.unit_picker.get_item_id(0)==1 and preview.unit_picker.get_item_id(1)==2)
	for index in [1,2]:
		preview.select_unit(index)
		preview.target.pause()
		preview.approved.pause()
		record("preview_route_"+str(index),preview.target.animation=="move_down_right" and preview.target.sprite_frames.get_frame_count("move_down_right")==8 and preview.approved.animation=="move_down" and preview.target.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST and not preview.target.centered)
	var failed: Array = checks.filter(func(item: Dictionary):return not item["pass"])
	FileAccess.open("res://ta-cold-contract.json",FileAccess.WRITE).store_string(JSON.stringify({"checks":checks,"total":checks.size(),"passed":checks.size()-failed.size(),"failures":failed,"scope":"minimum independent cold load; no author GPU or loops rerun"},"\t"))
	print("TA_COLD_CONTRACT ",checks.size()-failed.size(),"/",checks.size())
	preview.queue_free()
	await process_frame
	quit(0 if failed.is_empty() else 1)
