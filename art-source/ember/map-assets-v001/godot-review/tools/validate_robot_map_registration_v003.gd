extends SceneTree
## 只验证三张地图中的机器人注册点；不改素材、铺刷器或地图数据。
## 放到已有地图独立审查工程运行，--output 指定本次报告目录。

const MAPS := ["tidal_port", "dry_mine", "overgrown_lab"]
const FOOT := Vector2(32, 80)
var output_dir := ""
var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):
			output_dir = argument.trim_prefix("--output=").replace("\\", "/")
	if output_dir.is_empty():
		push_error("需要 --output=<绝对输出目录>")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_dir)
	var records: Array[Dictionary] = []
	for map_id: String in MAPS:
		var scene_path := "res://scenes/ember/map_assets_" + map_id + "_v001.tscn"
		var scene := load(scene_path) as PackedScene
		if scene == null:
			failures.append("地图无法加载：" + scene_path)
			continue
		var view := SubViewport.new()
		view.size = Vector2i(1536, 1024)
		view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		view.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
		root.add_child(view)
		var map := scene.instantiate() as Node2D
		view.add_child(map)
		await process_frame
		await process_frame
		var robot := map.get_node("Props/ExistingRobot") as Sprite2D
		# Sprite2D 的 offset 先于节点缩放。虚拟足底变换后应正好是节点原点。
		var canvas_origin := -robot.texture.get_size() * 0.5 if robot.centered else Vector2.ZERO
		var local_foot := FOOT + canvas_origin + robot.offset
		var foot_world := robot.to_global(local_foot)
		var error := foot_world.distance_to(robot.global_position)
		var valid := error < 0.0001 and not robot.centered and robot.offset == Vector2(-32, -80)
		if not valid:
			failures.append("地图机器人足底未对齐：" + map_id)
		var record := {"map_id": map_id, "scene": scene_path,
			"scene_sha256": FileAccess.get_sha256(scene_path), "centered": robot.centered,
			"offset": [robot.offset.x, robot.offset.y], "scale": [robot.scale.x, robot.scale.y],
			"node_world": [robot.global_position.x, robot.global_position.y],
			"foot_world": [foot_world.x, foot_world.y], "foot_error_world": error,
			"registration_matches": valid}
		if DisplayServer.get_name() != "headless":
			map.set_process(false)
			if map.get("_help_label") != null:
				map.get("_help_label").get_parent().hide()
			await process_frame
			await RenderingServer.frame_post_draw
			var screenshot := output_dir.path_join("map_" + map_id + "_anchor_v003.png")
			var saved := view.get_texture().get_image().save_png(screenshot)
			if saved != OK:
				failures.append("截图写入失败：" + map_id)
			record["screenshot"] = screenshot
			record["screenshot_sha256"] = FileAccess.get_sha256(screenshot)
		records.append(record)
		view.queue_free()
		await process_frame
	var report := {"status": "PASS" if failures.is_empty() else "FAIL",
		"engine": Engine.get_version_info().string,
		"tool_sha256": FileAccess.get_sha256(get_script().resource_path),
		"foot_pivot": [32, 80], "map_count": records.size(), "maps": records,
		"scope": "Only robot registration; map scale/proportions retained, new action preview uses integer display scale",
		"failures": failures}
	var file := FileAccess.open(output_dir.path_join("map_registration_v003.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	print("ROBOT_MAP_REGISTRATION_", report.status, " maps=", records.size())
	quit(0 if failures.is_empty() else 1)
