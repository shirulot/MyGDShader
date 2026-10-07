extends SceneTree
## 真实 GPU 捕获：沿用 06.2 当前代码副本的 TIME 动画，不手工生成效果帧。
## 不使用 --headless；SubViewport 在每一帧持续绘制，然后读取其实际渲染纹理。

const SCENE_PATH := "res://scenes/chapter06/ch06_02_water_compare.tscn"
const OUTPUT_DIR := "res://art-source/ember/chapter06-water-preview"
const VIEW_SIZE := Vector2i(1112, 680)
const FRAME_COUNT := 36
const TARGET_FPS := 12.0

var report: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run")


func _finish(status: String, error_message: String = "") -> void:
	report["status"] = status
	report["error"] = error_message
	var file := FileAccess.open(OUTPUT_DIR + "/capture-report.json", FileAccess.WRITE)
	if file == null:
		push_error("无法写入 GPU 捕获报告：" + str(FileAccess.get_open_error()))
		quit(1)
		return
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	if not error_message.is_empty():
		push_error(error_message)
	print("WATER_COMPARE_CAPTURE ", status, " frames=", report.get("captured_frame_count", 0))
	quit(0 if status == "GPU_CAPTURED" else 1)


func _run() -> void:
	# 文件夹只承载本次预览输出；不会移动或覆盖既有水面素材。
	var output_error := DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR + "/frames"))
	if output_error != OK:
		push_error("无法创建捕获输出目录：" + str(output_error))
		quit(1)
		return
	report = {
		"engine": Engine.get_version_info(),
		"display_server": DisplayServer.get_name(),
		"gpu_adapter": RenderingServer.get_video_adapter_name(),
		"gpu_vendor": RenderingServer.get_video_adapter_vendor(),
		"graphics_api_version": RenderingServer.get_video_adapter_api_version(),
		"configured_renderer": ProjectSettings.get_setting("rendering/renderer/rendering_method"),
		"scene": SCENE_PATH,
		"scene_sha256": FileAccess.get_sha256(SCENE_PATH),
		"shader": "res://scenes/chapter06/ch06_02_water_preview.gdshader",
		"shader_sha256": FileAccess.get_sha256("res://scenes/chapter06/ch06_02_water_preview.gdshader"),
		"image_size": [VIEW_SIZE.x, VIEW_SIZE.y],
		"requested_frame_count": FRAME_COUNT,
		"requested_fps": TARGET_FPS,
		"requested_duration_seconds": FRAME_COUNT / TARGET_FPS,
		"captured_frame_count": 0,
		"animation_clock": "Unchanged Godot shader TIME; measured capture timestamps are relative wall-clock times.",
		"still_image": OUTPUT_DIR + "/water_compare_gpu.png",
		"frames": [],
	}
	if DisplayServer.get_name() == "headless" or str(report["gpu_adapter"]).is_empty():
		_finish("CAPTURE_FAILED", "需要可用的实际 GPU 渲染；请去掉 --headless 后重新运行。")
		return
	var packed := load(SCENE_PATH) as PackedScene
	if packed == null:
		_finish("CAPTURE_FAILED", "无法加载两版水面对比场景。请先确认水图及其场景已导入。")
		return
	var viewport := SubViewport.new()
	viewport.size = VIEW_SIZE
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	viewport.add_child(packed.instantiate())

	# 等待场景、字体和 Shader 至少完成首次绘制。
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var started_usec := Time.get_ticks_usec()
	var frame_records: Array[Dictionary] = []
	for index in range(FRAME_COUNT):
		# 用绝对目标时刻安排读取。PNG 保存耗时不会被额外加进每次等待；
		# 如机器不能达到目标间隔，报告仍保留实际时间，不伪造 12 FPS。
		var target_usec := started_usec + int(index * 1000000.0 / TARGET_FPS)
		var remaining_seconds := (target_usec - Time.get_ticks_usec()) / 1000000.0
		if remaining_seconds > 0.0:
			await create_timer(remaining_seconds).timeout
		await RenderingServer.frame_post_draw
		var captured_usec := Time.get_ticks_usec()
		var image := viewport.get_texture().get_image()
		if image == null or image.is_empty() or image.get_size() != VIEW_SIZE:
			_finish("CAPTURE_FAILED", "GPU 输出图像无效，或尺寸与对比布局不一致。")
			return
		var frame_path := OUTPUT_DIR + "/frames/frame_%03d.png" % index
		if image.save_png(frame_path) != OK:
			_finish("CAPTURE_FAILED", "无法保存动画帧：" + frame_path)
			return
		if index == 0 and image.save_png(str(report["still_image"])) != OK:
			_finish("CAPTURE_FAILED", "无法保存水面对比静态图。")
			return
		frame_records.append({
			"index": index,
			"path": frame_path,
			"target_seconds": index / TARGET_FPS,
			"captured_seconds": (captured_usec - started_usec) / 1000000.0,
			"captured_ticks_usec": captured_usec,
			"image_size": [image.get_width(), image.get_height()],
		})
		report["captured_frame_count"] = frame_records.size()
		report["frames"] = frame_records

	# 36 帧播放时长为 3 秒；实际捕获运行时间也单独测量并写入报告。
	var remaining_duration := FRAME_COUNT / TARGET_FPS - (Time.get_ticks_usec() - started_usec) / 1000000.0
	if remaining_duration > 0.0:
		await create_timer(remaining_duration).timeout
	report["actual_elapsed_seconds"] = (Time.get_ticks_usec() - started_usec) / 1000000.0
	report["captured_span_seconds"] = float(frame_records[-1]["captured_seconds"]) - float(frame_records[0]["captured_seconds"])
	_finish("GPU_CAPTURED")
