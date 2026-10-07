extends SceneTree
## 直接截取真实Godot UI和地图。没有烘焙文字，也没有把概念图当作游戏截图。
const PREVIEW = preload("res://scenes/ember/ui_edge_interactive_v004.tscn")
const STYLE = preload("res://scripts/ember/ui_edge_v001/edge_ui_style.gd")
const OUT := "res://assets/ember/ui_final/previews/"
## 图片统一进入 assets；验证元数据留在审查资料目录。
const EVIDENCE := "res://art-source/ember/ui-interactions-v004/"
var captures: Array[Dictionary] = []

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	root.position = Vector2i(-10000,-10000)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(EVIDENCE))
	var preview_ignore := FileAccess.open(OUT + ".gdignore", FileAccess.WRITE)
	preview_ignore.close()
	var board := SubViewport.new()
	board.size = Vector2i(1600,960)
	board.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(board)
	var layout := Control.new()
	layout.size = Vector2(board.size)
	board.add_child(layout)
	var background := ColorRect.new()
	background.size = layout.size
	background.color = Color("101820")
	layout.add_child(background)
	var title := STYLE.label(layout,"边缘标记 · 横向生命与窗口交互",36)
	title.position = Vector2(48,24)
	var caption := STYLE.label(layout,"现场 HUD",24)
	caption.position = Vector2(48,108)
	caption = STYLE.label(layout,"设备详情窗口",24)
	caption.position = Vector2(832,108)
	var left := _add_view(layout,Vector2(48,156))
	var right := _add_view(layout,Vector2(832,156))
	var demo: Node2D = right.get_child(0)
	demo.ui.open_details()
	await _draw()
	_save(board,"overview.png")
	_save(left,"hud.png")
	_save(right,"details.png")
	for page in ["pause","settings","help","confirm_restart","confirm_title","title","success","failure"]:
		demo.ui._open(page,false,true)
		if page == "failure":
			demo.ui.set_game_state({"life":0})
			demo.ui._build_page()
		elif page == "success":
			demo.ui.set_game_state({"energy":380})
			demo.ui._build_page()
		await _draw()
		_save(right,String(page)+".png")
		if page == "settings":
			var slider: HSlider = demo.ui.window.body.get_node("SafeMargin")
			slider.grab_focus()
			await _draw()
			_save(right,"settings_slider_focused_720.png")
			var focused := right.get_texture().get_image()
			var focused_has_focus := slider.has_focus()
			var slider_rect := Rect2i(slider.get_global_rect())
			demo.ui.window.body.get_node("Markers").grab_focus()
			await _draw()
			_save(right,"settings_slider_unfocused_720.png")
			var unfocused := right.get_texture().get_image()
			var changed := 0
			for y in range(slider_rect.position.y,slider_rect.end.y):
				for x in range(slider_rect.position.x,slider_rect.end.x):
					if focused.get_pixel(x,y) != unfocused.get_pixel(x,y):
						changed += 1
			var focus_report := {"status":"PASS" if focused_has_focus and not slider.has_focus() and changed > 0 else "FAIL","focused_has_focus":focused_has_focus,"unfocused_has_focus":slider.has_focus(),"same_value":slider.value,"roi":[slider_rect.position.x,slider_rect.position.y,slider_rect.size.x,slider_rect.size.y],"changed_pixels":changed}
			var evidence := FileAccess.open(EVIDENCE+"slider-focus-validation.json",FileAccess.WRITE)
			evidence.store_string(JSON.stringify(focus_report,"\t"))
			evidence.close()
	demo.ui.close_all()
	demo.apply_example(0,true,2,145,78,true)
	await _draw()
	_save(right,"terminal.png")
	demo.ui.hud.set_drawer_open(false)
	demo.ui.toast.notify("界面设置已保存",20)
	await _draw()
	_save(right,"toast.png")
	demo.ui.toast.hide()
	right.size = Vector2i(320,480)
	demo.ui._open("settings",false,true)
	await _draw()
	_save(right,"compact_settings_320x480.png")
	var report := {"status":"PASS","render":"Godot Compatibility GPU, native screen pixels","captures":captures,"logical_base":[720,720],"overview_scale":1}
	var output := FileAccess.open(EVIDENCE + "gpu-validation.json",FileAccess.WRITE)
	output.store_string(JSON.stringify(report,"\t"))
	output.close()
	print("UI_INTERACTION_CAPTURES ",captures.size())
	quit()

func _add_view(parent: Control, point: Vector2) -> SubViewport:
	var container := SubViewportContainer.new()
	container.position = point
	container.size = Vector2(720,720)
	parent.add_child(container)
	var view := SubViewport.new()
	view.size = Vector2i(720,720)
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	view.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	container.add_child(view)
	var demo := PREVIEW.instantiate()
	demo.use_saved_preferences = false
	view.add_child(demo)
	return view

func _draw() -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	await process_frame
	await RenderingServer.frame_post_draw

func _save(view: SubViewport, filename: String) -> void:
	var pixels := view.get_texture().get_image()
	var path := OUT + filename
	var result := pixels.save_png(ProjectSettings.globalize_path(path))
	if result != OK:
		push_error("Capture failed: " + path)
		quit(1)
		return
	captures.append({"path":path,"width":pixels.get_width(),"height":pixels.get_height(),"sha256":FileAccess.get_sha256(path)})
