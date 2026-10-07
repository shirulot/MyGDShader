extends SceneTree
## 新动作仅写 v003 文件：旧待机、修复版行走与新原生动作按原字节拼成图集。
## 构建：godot --headless --path <独立工程> --script res://tools/build_robot_animation_v003.gd
## 之后导入该独立工程，再用 -- --verify-only 核验；加 --gpu 进行真实透明读回。
## 所有源素材检查都只读。图集组合不重画、缩放、量化或修补任何原生帧。

const BASE := "res://assets/ember/characters/robot/"
const SOURCE_MANIFEST := "res://art-source/ember/robot-actions-v003/frame_manifest_v003.json"
const OLD_CATALOG := BASE + "robot_frames_catalog_v002.json"
const CATALOG := BASE + "robot_frames_catalog_v003.json"
const ATLAS := BASE + "robot_animations_v003.png"
const FRAMES := BASE + "robot_sprite_frames_v003.tres"
const PREVIEW := "res://scenes/ember/robot_animation_sandbox_v003.tscn"
const PREVIEW_SCRIPT := "res://scripts/ember/robot_action_preview_v003.gd"
const DIRECTIONS := ["down", "left", "right", "up"]
const FRAME_SIZE := Vector2i(64, 96)
const ANCHOR := Vector2i(32, 80)
const ATLAS_SIZE := Vector2i(640, 384)
const DISPLAY_SIZE := Vector2i(1536, 1024)

var verify_only := false
var gpu := false
var snapshot := false
var animation_frames_dir := ""
var report_path := ""
var errors: Array = []
var records: Array = []
var clips: Array = []
var observed: Dictionary = {}

func _initialize() -> void: call_deferred("_run")

func _run() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument == "--verify-only": verify_only = true
		elif argument == "--gpu": gpu = true
		elif argument == "--snapshot": snapshot = true
		elif argument.begins_with("--animation-frames="): animation_frames_dir = argument.trim_prefix("--animation-frames=")
		elif argument.begins_with("--report="): report_path = argument.trim_prefix("--report=")
		else: errors.append("未知参数: " + argument)
	if report_path.is_empty():
		report_path = "res://art-source/ember/robot-actions-v003/runtime_verify_v003.json" if verify_only else "res://art-source/ember/robot-actions-v003/runtime_build_v003.json"
	if (gpu or snapshot or not animation_frames_dir.is_empty()) and DisplayServer.get_name() == "headless": errors.append("真实 GPU 或窗口截图需要非 headless 渲染器。")
	if not errors.is_empty(): _finish(); return
	_assemble_records()
	_validate_sources()
	if not errors.is_empty(): _finish(); return
	if not verify_only:
		_build_atlas()
		_build_resource_text()
		_build_preview_text()
		_write_json(CATALOG, {"schema_version": 2, "status": "ROBOT_ACTIONS_V003_BUILT", "canvas": [64,96], "anchor": [32,80], "directions": DIRECTIONS,
			"frames": records, "animations": clips, "sheet": {"texture": ATLAS, "size": [640,384], "columns":10, "rows":4, "sha256": FileAccess.get_sha256(ATLAS)},
			"source_manifest": SOURCE_MANIFEST, "source_manifest_sha256": FileAccess.get_sha256(SOURCE_MANIFEST), "legacy_catalog": OLD_CATALOG, "legacy_catalog_sha256": FileAccess.get_sha256(OLD_CATALOG)})
	else:
		_validate_atlas_and_resource()
		if errors.is_empty(): await _validate_playback_and_controls()
		if errors.is_empty() and gpu: await _validate_gpu_frames()
		if errors.is_empty() and not animation_frames_dir.is_empty(): await _capture_animation_boards()
	_finish()

func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path): errors.append("输入不存在: " + path); return {}
	var value: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not value is Dictionary: errors.append("JSON 必须为对象: " + path); return {}
	return value

func _raw(path: String) -> Image:
	var output := Image.new()
	if output.load(ProjectSettings.globalize_path(path)) != OK: errors.append("无法读取原始 PNG: " + path); return null
	output.convert(Image.FORMAT_RGBA8)
	return output

func _assemble_records() -> void:
	var actions := _read_json(SOURCE_MANIFEST)
	var legacy := _read_json(OLD_CATALOG)
	if actions.is_empty() or legacy.is_empty(): return
	if actions.get("status","") != "PASS": errors.append("新动作manifest尚未通过原生验证。"); return
	if not _pair_matches(actions.get("canvas"),FRAME_SIZE) or not _pair_matches(actions.get("anchor"),ANCHOR): errors.append("新动作必须保留 64×96 / (32,80)。"); return
	var action_lookup := {}
	for entry: Dictionary in actions.get("frames", []):
		if action_lookup.has(str(entry["id"])): errors.append("新动作 manifest 重复 ID: " + str(entry["id"]))
		action_lookup[str(entry["id"])] = entry
	var legacy_lookup := {}
	for entry: Dictionary in legacy.get("frames", []): legacy_lookup[str(entry["id"])] = entry
	for row in DIRECTIONS.size():
		var direction: String = DIRECTIONS[row]
		var column := 0
		for state: String in ["idle", "walk", "collect"]:
			var frame_ids: Array = []
			var count := 2 if state == "idle" else 4
			for index in count:
				var id := "robot_%s_%s_f%02d" % [state,direction,index]
				var entry: Dictionary = {}
				if state == "walk": entry = legacy_lookup.get(id, {}).duplicate(true)
				else: entry = action_lookup.get(id, {}).duplicate(true)
				if entry.is_empty(): errors.append("缺少正式原生帧: " + id); continue
				entry["id"] = id; entry["state"] = state; entry["direction"] = direction; entry["frame_index"] = index
				entry["coord"] = [column,row]; entry["anchor"] = [32,80]
				entry["reused_original"] = state == "walk" or (state == "idle" and index == 0)
				records.append(entry); frame_ids.append(id); column += 1
			clips.append({"id": state + "_" + direction, "direction":direction, "state":state,
				"frame_ids":frame_ids, "fps":2.0 if state == "idle" else (8.0 if state == "walk" else 6.0), "loop":state != "collect"})
	if records.size() != 40 or clips.size() != 12: errors.append("必须具有完整40姿态与12动画。")
	observed["new_pose_count"] = 20
	observed["reused_pose_count"] = 20

func _validate_sources() -> void:
	var inputs: Array = []
	for record: Dictionary in records:
		var path := str(record["file"])
		if not FileAccess.file_exists(path): errors.append("原生帧不存在: " + path); continue
		var hash := FileAccess.get_sha256(path)
		if hash != str(record.get("sha256", "")): errors.append("原生帧 SHA 不符: " + path)
		var frame := _raw(path)
		if frame == null: continue
		if frame.get_size() != FRAME_SIZE: errors.append("原生帧尺寸不符: " + path)
		var alpha_ok := true
		for y in frame.get_height():
			for x in frame.get_width():
				var alpha := frame.get_pixel(x,y).a8
				if alpha != 0 and alpha != 255: alpha_ok = false
		if not alpha_ok: errors.append("原生帧 Alpha 不是0/255: " + path)
		inputs.append({"id":record["id"],"file":path,"sha256":hash,"size":[frame.get_width(),frame.get_height()],"binary_alpha":alpha_ok,"reused_original":record["reused_original"]})
	observed["source_frames"] = inputs

func _build_atlas() -> void:
	var atlas := Image.create(ATLAS_SIZE.x, ATLAS_SIZE.y, false, Image.FORMAT_RGBA8)
	atlas.fill(Color(0,0,0,0))
	for record: Dictionary in records:
		var frame := _raw(str(record["file"]))
		atlas.blit_rect(frame, Rect2i(Vector2i.ZERO,FRAME_SIZE), Vector2i(int(record["coord"][0]),int(record["coord"][1])) * FRAME_SIZE)
	if atlas.save_png(ProjectSettings.globalize_path(ATLAS)) != OK: errors.append("图集保存失败。")

func _build_resource_text() -> void:
	# 直接写外部 PNG 引用，第一次构建不依赖尚未导入的新图集缓存。
	var output := "[gd_resource type=\"SpriteFrames\" format=3]\n\n[ext_resource type=\"Texture2D\" path=\"%s\" id=\"1_atlas\"]\n\n" % ATLAS
	for index in records.size():
		var record: Dictionary = records[index]
		output += "[sub_resource type=\"AtlasTexture\" id=\"Frame_%02d\"]\nresource_name = \"%s\"\natlas = ExtResource(\"1_atlas\")\nregion = Rect2(%d, %d, 64, 96)\nfilter_clip = true\n\n" % [index,record["id"],int(record["coord"][0])*64,int(record["coord"][1])*96]
	output += "[resource]\nresource_name = \"EmberRobotActionsV003\"\nanimations = ["
	for clip_index in clips.size():
		var clip: Dictionary = clips[clip_index]
		output += "{\n\"frames\": ["
		for frame_index in clip["frame_ids"].size():
			var id := str(clip["frame_ids"][frame_index])
			var record_index := _find_record(id)
			output += "{\"duration\": 1.0, \"texture\": SubResource(\"Frame_%02d\")}" % record_index
			if frame_index < clip["frame_ids"].size()-1: output += ", "
		output += "],\n\"loop\": %d,\n\"name\": &\"%s\",\n\"speed\": %.1f\n}" % [1 if clip["loop"] else 0,clip["id"],clip["fps"]]
		if clip_index < clips.size()-1: output += ", "
	output += "]\n"
	_write_text(FRAMES,output)

func _find_record(id: String) -> int:
	for index in records.size():
		if str(records[index]["id"]) == id: return index
	return -1

func _pair_matches(value: Variant, expected: Vector2i) -> bool:
	# JSON数字按float读入，不能用整型Array直接相等判断相同尺寸。
	return value is Array and value.size()==2 and float(value[0])==expected.x and float(value[1])==expected.y

func _label(name: String, parent_path: String, point: Vector2, value: String, size: int) -> String:
	return "[node name=\"%s\" type=\"Label\" parent=\"%s\"]\noffset_left = %.1f\noffset_top = %.1f\ntheme_override_colors/font_color = Color(0.78, 0.83, 0.80, 1)\ntheme_override_font_sizes/font_size = %d\ntext = %s\n\n" % [name,parent_path,point.x,point.y,size,JSON.stringify(value)]

func _sprite_text(name: String, parent_path: String, point: Vector2, animation: String) -> String:
	return "[node name=\"%s\" type=\"AnimatedSprite2D\" parent=\"%s\"]\ntexture_filter = 1\nposition = Vector2(%.1f, %.1f)\nscale = Vector2(4, 4)\nsprite_frames = ExtResource(\"1_frames\")\nanimation = &\"%s\"\nautoplay = \"%s\"\ncentered = false\noffset = Vector2(-32, -80)\n\n" % [name,parent_path,point.x,point.y,animation,animation]

func _build_preview_text() -> void:
	var output := "[gd_scene format=3]\n\n[ext_resource type=\"SpriteFrames\" path=\"%s\" id=\"1_frames\"]\n[ext_resource type=\"Script\" path=\"%s\" id=\"2_script\"]\n\n[node name=\"RobotActionPreviewV003\" type=\"Node2D\"]\ntexture_filter = 1\nscript = ExtResource(\"2_script\")\n\n" % [FRAMES,PREVIEW_SCRIPT]
	output += "[node name=\"Background\" type=\"ColorRect\" parent=\".\"]\noffset_right = 1536.0\noffset_bottom = 1024.0\nmouse_filter = 2\ncolor = Color(0.07, 0.105, 0.13, 1)\n\n"
	output += _label("Title",".",Vector2(28,18),"机器人动作 v003 · 原生 64×96 · 固定脚底 (32,80) · 整数 4×",24)
	output += _label("Hint",".",Vector2(28,52),"待机 2 帧 / 2 FPS   |   行走 4 帧 / 8 FPS   |   采集 4 帧 / 6 FPS，动作不循环，小样停顿重播",18)
	output += "[node name=\"Grid\" type=\"Node2D\" parent=\".\"]\n\n"
	for direction_index in DIRECTIONS.size():
		var direction: String = DIRECTIONS[direction_index]
		var x := 166.0 + direction_index * 276.0
		output += _label("Direction"+direction.capitalize(),"Grid",Vector2(x-60,88),["朝下 / down","朝左 / left","朝右 / right","朝上 / up"][direction_index],18)
		for state_index in 3:
			var state: String = ["idle","walk","collect"][state_index]
			var foot := Vector2(x,374+state_index*282)
			output += _sprite_text(state.capitalize()+direction.capitalize(),"Grid",foot,state+"_"+direction)
			output += _label("Caption"+state.capitalize()+direction.capitalize(),"Grid",Vector2(x-82,foot.y+10),["待机 · 循环","行走 · 循环","采集 · 单次后重播"][state_index],16)
			output += "[node name=\"Anchor%s%s\" type=\"Line2D\" parent=\"Grid\"]\nposition = Vector2(%.1f, %.1f)\npoints = PackedVector2Array(-16, 0, 16, 0)\nwidth = 1.0\ndefault_color = Color(0.32, 0.46, 0.49, 1)\n\n" % [state.capitalize(),direction.capitalize(),foot.x,foot.y]
	output += "[node name=\"Interactive\" type=\"Node2D\" parent=\".\"]\n\n"
	output += _label("Title","Interactive",Vector2(1186,100),"键盘交互小样",22)
	output += _label("Keys","Interactive",Vector2(1186,143),"WASD / 方向键移动\n空格 / E：采集\n松开移动键：待机\n采集结束自动回待机",17)
	output += _label("Status","Interactive",Vector2(1186,245),"",18)
	output += _sprite_text("Actor","Interactive",Vector2(1316,676),"idle_down")
	output += _label("Scope",".",Vector2(28,994),"独立素材预览：不改变主游戏、碰撞、导航和课程 Shader。",15)
	_write_text(PREVIEW,output)

func _validate_atlas_and_resource() -> void:
	var catalog := _read_json(CATALOG)
	# 经JSON往返统一数值类型，同时保留浮点UV全精度，避免整数/浮点数组误报。
	if catalog.get("frames") != JSON.parse_string(JSON.stringify(records,"",false,true)) or catalog.get("animations") != JSON.parse_string(JSON.stringify(clips,"",false,true)): errors.append("组合目录与实际源 manifest 不一致。")
	if catalog.get("source_manifest_sha256") != FileAccess.get_sha256(SOURCE_MANIFEST): errors.append("来源 manifest SHA 不符。")
	var atlas := _raw(ATLAS)
	if atlas == null: return
	if atlas.get_size() != ATLAS_SIZE: errors.append("图集不是640×384。")
	if catalog.get("sheet",{}).get("sha256") != FileAccess.get_sha256(ATLAS): errors.append("图集 SHA 不符。")
	var sprite_frames := load(FRAMES) as SpriteFrames
	if sprite_frames == null: errors.append("SpriteFrames 无法导入读取。"); return
	if sprite_frames.get_animation_names().size() != 12: errors.append("SpriteFrames 动画数量不是12。")
	var resource_checks: Array = []
	for clip: Dictionary in clips:
		var id := StringName(clip["id"])
		if not sprite_frames.has_animation(id): errors.append("资源缺动画: " + str(id)); continue
		var count := sprite_frames.get_frame_count(id)
		if count != clip["frame_ids"].size(): errors.append("资源帧数不符: " + str(id)); continue
		if sprite_frames.get_animation_speed(id) != float(clip["fps"]) or sprite_frames.get_animation_loop_mode(id) != (SpriteFrames.LOOP_LINEAR if clip["loop"] else SpriteFrames.LOOP_NONE): errors.append("资源FPS/循环模式不符: " + str(id))
		for index in count:
			var record: Dictionary = records[_find_record(str(clip["frame_ids"][index]))]
			var expected := Rect2i(Vector2i(int(record["coord"][0]),int(record["coord"][1]))*FRAME_SIZE,FRAME_SIZE)
			var texture := sprite_frames.get_frame_texture(id,index) as AtlasTexture
			if texture == null or texture.region != Rect2(expected) or texture.margin != Rect2() or not texture.filter_clip or texture.atlas.resource_path != ATLAS or sprite_frames.get_frame_duration(id,index) != 1.0:
				errors.append("资源裁片/顺序/边距/时长不符: " + str(record["id"])); continue
			var source := _raw(str(record["file"]))
			if atlas.get_region(expected).get_data() != source.get_data(): errors.append("图集与原帧 RGBA 不符: " + str(record["id"]))
			var imported := texture.get_image()
			if imported == null: errors.append("无法读回导入纹理: " + str(record["id"])); continue
			var metrics := _compare(source,imported,1)
			if metrics["alpha_changed"] != 0 or metrics["visible_rgb_changed"] != 0: errors.append("导入纹理改变可见像素: " + str(record["id"]))
			resource_checks.append({"id":record["id"],"clip":str(id),"index":index,"region":[expected.position.x,expected.position.y,64,96],"import_readback":metrics})
	observed["resource_frames"] = resource_checks
	observed["atlas_regions_rgba_equal"] = resource_checks.size()
	observed["clip_dependencies"] = clips

func _validate_playback_and_controls() -> void:
	var packed := load(PREVIEW) as PackedScene
	if packed == null: errors.append("预览场景无法载入。"); return
	var preview := packed.instantiate()
	var playback := {}
	for direction: String in DIRECTIONS:
		for state: String in ["idle","walk","collect"]:
			var node_path := "Grid/" + state.capitalize() + direction.capitalize()
			var sprite := preview.get_node(node_path) as AnimatedSprite2D
			if sprite == null: errors.append("预览缺节点: " + node_path); continue
			if sprite.scale != Vector2(4,4) or sprite.centered or sprite.offset != -Vector2(ANCHOR) or sprite.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST or sprite.sprite_frames.resource_path != FRAMES or sprite.animation != state + "_" + direction or sprite.flip_h or sprite.flip_v: errors.append("预览锚点/像素倍率/资源不符: " + node_path)
			playback[node_path] = {"animation": str(sprite.animation),"visited":{0:true},"previous":0,"wraps":0,"finished":0,"transitions":[]}
			sprite.frame_changed.connect(_record_transition.bind(sprite,playback[node_path]))
			sprite.animation_finished.connect(_record_finished.bind(playback[node_path]))
	root.add_child(preview)
	await process_frame
	var started := Time.get_ticks_msec()
	await create_timer(2.35).timeout
	var playback_report := {}
	for node_path: String in playback:
		# 信号仍在后续交互检查期间发出，报告要复制快照，不能删除活记录的字段。
		var record: Dictionary = playback[node_path].duplicate(true)
		var visited: Array = record["visited"].keys(); visited.sort()
		record["visited_frames"] = visited; record.erase("visited"); record.erase("previous")
		var state := str(record["animation"]).split("_")[0]
		if visited != ([0,1] if state=="idle" else [0,1,2,3]): errors.append("真实播放未访问完整帧: " + node_path)
		if state != "collect" and int(record["wraps"]) < 1: errors.append("循环动画未出现完整回环: " + node_path)
		if state == "collect" and int(record["finished"]) < 2: errors.append("采集没有真实结束/停顿重播: " + node_path)
		playback_report[node_path] = record
	observed["runtime_playback"] = playback_report
	observed["runtime_observation_ms"] = Time.get_ticks_msec()-started
	observed["collect_preview_restarts"] = preview.get("collect_restart_count").duplicate(true)
	# 交互控制复用与键盘相同的公开入口，逐方向确认 walk→collect→idle 的真实播放。
	preview.set_physics_process(false)
	var controls: Array = []
	for index in DIRECTIONS.size():
		var direction: String = DIRECTIONS[index]
		var move: Vector2 = [Vector2.DOWN,Vector2.LEFT,Vector2.RIGHT,Vector2.UP][index]
		var actor := preview.get_node("Interactive/Actor") as AnimatedSprite2D
		var before := actor.position
		preview.call("preview_step",move,0.1)
		var walk_ok := str(actor.animation) == "walk_"+direction and actor.position != before
		preview.call("start_collect")
		var collect_ok := str(actor.animation) == "collect_"+direction and bool(preview.get("collecting"))
		var stopped := actor.position
		preview.call("preview_step",move,0.1)
		var locked := actor.position == stopped
		await create_timer(0.78).timeout
		var return_ok := str(actor.animation) == "idle_"+direction and not bool(preview.get("collecting"))
		if not walk_ok or not collect_ok or not locked or not return_ok: errors.append("交互状态切换失败: " + direction)
		controls.append({"direction":direction,"move_selects_walk":walk_ok,"collect_starts":collect_ok,"collect_locks_movement":locked,"complete_returns_idle":return_ok})
	observed["control_state_cases"] = controls
	observed["keyboard_input_scope"] = "公开控制入口与实际键盘处理共用；未模拟原生操作系统按键。"
	if snapshot:
		await process_frame
		await RenderingServer.frame_post_draw
		var file := BASE+"robot_preview_v003.png"
		if root.get_texture().get_image().save_png(ProjectSettings.globalize_path(file)) != OK: errors.append("实际预览截图保存失败。")
		else: observed["preview_screenshot"] = {"file":file,"sha256":FileAccess.get_sha256(file),"size":[1536,1024]}
	root.remove_child(preview); preview.queue_free()
	await process_frame

func _record_transition(sprite: AnimatedSprite2D, record: Dictionary) -> void:
	var previous := int(record["previous"])
	var current := sprite.frame
	record["visited"][current] = true
	if previous != current:
		record["transitions"].append([previous,current])
		if current == 0 and previous > 0: record["wraps"] = int(record["wraps"])+1
	record["previous"] = current

func _record_finished(record: Dictionary) -> void: record["finished"] = int(record["finished"])+1

func _compare(source: Image, actual: Image, factor: int) -> Dictionary:
	actual.convert(Image.FORMAT_RGBA8)
	var alpha_changed := 0
	var visible_changed := 0
	var max_error := 0
	if actual.get_size() != source.get_size()*factor: return {"alpha_changed":-1,"visible_rgb_changed":-1,"size_mismatch":true}
	for y in actual.get_height():
		for x in actual.get_width():
			var expected := source.get_pixel(x/factor,y/factor)
			var readback := actual.get_pixel(x,y)
			if expected.a8 != readback.a8: alpha_changed += 1
			if expected.a8 > 0 or readback.a8 > 0:
				var rgb_error := maxi(maxi(absi(expected.r8-readback.r8),absi(expected.g8-readback.g8)),absi(expected.b8-readback.b8))
				if rgb_error > 0: visible_changed += 1
				max_error = maxi(max_error,rgb_error)
	return {"alpha_changed":alpha_changed,"visible_rgb_changed":visible_changed,"max_rgb_channel_error":max_error,"transparent_rgb_ignored":true}

func _validate_gpu_frames() -> void:
	var sprite_frames := load(FRAMES) as SpriteFrames
	var gpu_cases: Array = []
	var collected := {1:Image.create(640,384,false,Image.FORMAT_RGBA8),4:Image.create(2560,1536,false,Image.FORMAT_RGBA8)}
	for factor in [1,4]: collected[factor].fill(Color(0,0,0,0))
	for record: Dictionary in records:
		var source := _raw(str(record["file"]))
		for factor in [1,4]:
			var viewport := SubViewport.new()
			viewport.size = FRAME_SIZE*factor; viewport.transparent_bg = true
			viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
			viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
			var sprite := AnimatedSprite2D.new()
			sprite.sprite_frames = sprite_frames; sprite.animation = str(record["state"])+"_"+str(record["direction"])
			sprite.frame = int(record["frame_index"]); sprite.centered = false; sprite.offset = -Vector2(ANCHOR)
			sprite.position = Vector2(ANCHOR)*factor; sprite.scale = Vector2(factor,factor)
			sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			var material := CanvasItemMaterial.new(); material.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED; sprite.material = material
			viewport.add_child(sprite); root.add_child(viewport)
			await process_frame; await process_frame; await RenderingServer.frame_post_draw
			var actual := viewport.get_texture().get_image()
			var metrics := _compare(source,actual,factor)
			metrics["id"] = record["id"]; metrics["factor"] = factor; metrics["animation"] = str(sprite.animation); metrics["frame"] = sprite.frame
			metrics["source_sha256"] = FileAccess.get_sha256(str(record["file"])); metrics["size"] = [actual.get_width(),actual.get_height()]
			if metrics["alpha_changed"] != 0 or metrics["visible_rgb_changed"] != 0: errors.append("透明 GPU 读回改变原生像素: %s / %dx" % [record["id"],factor])
			collected[factor].blit_rect(actual,Rect2i(Vector2i.ZERO,FRAME_SIZE*factor),Vector2i(int(record["coord"][0]),int(record["coord"][1]))*FRAME_SIZE*factor)
			gpu_cases.append(metrics)
			root.remove_child(viewport); viewport.free()
	observed["gpu_cases"] = gpu_cases
	observed["gpu_case_count"] = gpu_cases.size()
	observed["gpu_renderer"] = RenderingServer.get_video_adapter_name()
	observed["gpu_artifacts"] = []
	for factor in [1,4]:
		var path := BASE+"robot_gpu_%dx_v003.png" % factor
		if collected[factor].save_png(ProjectSettings.globalize_path(path)) != OK: errors.append("GPU帧联系图保存失败。")
		else: observed["gpu_artifacts"].append({"factor":factor,"file":path,"sha256":FileAccess.get_sha256(path)})
	if gpu_cases.size() != 80: errors.append("必须完成40帧×原生/4倍，共80项GPU读回。")

func _write_text(path: String, value: String) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
	var file := FileAccess.open(path,FileAccess.WRITE)
	if file == null: errors.append("输出无法写入: " + path); return
	file.store_string(value)

func _write_json(path: String, value: Dictionary) -> void: _write_text(path,JSON.stringify(value,"\t",false,true)+"\n")

func _capture_animation_boards() -> void:
	# 按一秒时轴以12FPS采样实际SpriteFrames：idle2FPS、walk8FPS、collect6FPS。
	# 采集四帧结束后回待机，补足一秒；这只生成编码板，不改非循环资源。
	var directory := ProjectSettings.globalize_path(animation_frames_dir)
	if DirAccess.make_dir_recursive_absolute(directory) != OK: errors.append("动画板输出目录不可写。"); return
	var packed := load(PREVIEW) as PackedScene
	var preview := packed.instantiate()
	root.add_child(preview)
	await process_frame
	preview.set_physics_process(false)
	var boards: Array = []
	for phase in 12:
		var seconds := float(phase)/12.0
		var idle_index := int(floor(seconds*2.0))%2
		var walk_index := int(floor(seconds*8.0))%4
		var collecting_phase := seconds < 4.0/6.0
		var collect_index := int(floor(seconds*6.0)) if collecting_phase else idle_index
		for direction: String in DIRECTIONS:
			for state: String in ["idle","walk","collect"]:
				var sprite := preview.get_node("Grid/"+state.capitalize()+direction.capitalize()) as AnimatedSprite2D
				sprite.stop()
				sprite.animation = "idle_"+direction if state=="collect" and not collecting_phase else state+"_"+direction
				sprite.set_frame_and_progress(idle_index if state=="idle" else (walk_index if state=="walk" else collect_index),0.0)
		var actor := preview.get_node("Interactive/Actor") as AnimatedSprite2D
		actor.stop(); actor.animation = "collect_down" if collecting_phase else "idle_down"; actor.set_frame_and_progress(collect_index,0.0)
		preview.get_node("Interactive/Status").text = "人工时轴采样 / %.3f s\n动作: %s / frame %d" % [seconds,str(actor.animation),collect_index]
		await process_frame
		await RenderingServer.frame_post_draw
		var file := directory.path_join("robot_actions_phase_%02d_v003.png" % phase)
		var output := root.get_texture().get_image()
		if output.save_png(file) != OK: errors.append("动作帧序板保存失败: " + file)
		boards.append({"phase":phase,"seconds":seconds,"file":file,"sha256":FileAccess.get_sha256(file),"size":[output.get_width(),output.get_height()],"collect_state":"collect" if collecting_phase else "idle","collect_frame":collect_index,"walk_frame":walk_index,"idle_frame":idle_index})
	observed["animation_boards"] = {"files":boards,"encoding_fps":12,"duration_seconds":1.0,
		"scope":"实际SpriteFrames由AnimatedSprite2D以4倍GPU显示；一秒时轴按12FPS采样原idle2/walk8/collect6，采集结束回待机。供人工循环GIF审阅，非资源内collect循环，也不是原生按键事件实测。"}
	root.remove_child(preview); preview.queue_free()
	await process_frame

func _finish() -> void:
	var dependencies := {}
	for path: String in [SOURCE_MANIFEST,OLD_CATALOG,CATALOG,ATLAS,FRAMES,PREVIEW,PREVIEW_SCRIPT,"res://tools/build_robot_animation_v003.gd"]:
		if FileAccess.file_exists(path): dependencies[path] = FileAccess.get_sha256(path)
	_write_json(report_path,{"status":"ROBOT_ACTIONS_V003_PASS" if errors.is_empty() else "ROBOT_ACTIONS_V003_FAIL","phase":"verify" if verify_only else "build",
		"errors":errors,"engine":Engine.get_version_info(),"timestamp_utc":Time.get_datetime_string_from_system(true),"gpu_requested":gpu,"snapshot_requested":snapshot,"animation_frames_dir":animation_frames_dir,
		"dependencies_sha256":dependencies,"observed":observed,"scope":"40个姿态源SHA/二值Alpha、逐RGBA图集、40个导入裁片、12剪辑时序、固定脚底/Nearest/4倍预览、真实计时播放、公开控制入口；可选80项透明GPU读回。关节与动作美术由独立逐帧审查负责。"})
	print("ROBOT_ACTIONS_V003 ","PASS" if errors.is_empty() else "FAIL", " / ",report_path)
	for error: String in errors: push_error(error)
	quit(0 if errors.is_empty() else 1)
