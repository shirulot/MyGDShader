@tool
extends EditorPlugin
## 仅在 tools/test.ps1 建立的临时项目启用，绝不编辑课程脚本。

var _failures := 0
var _checks := 0


func _enter_tree() -> void:
	_run.call_deferred()


func _run() -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var script := load("res://fixture.gd") as Script
	EditorInterface.edit_script(script)
	EditorInterface.set_main_screen_editor("Script")
	for index in range(5):
		await get_tree().process_frame
	var editor := EditorInterface.get_script_editor().get_current_editor().get_base_editor() as CodeEdit
	_check(editor != null, "Native script editor supplies CodeEdit")
	if editor == null:
		get_tree().quit(1)
		return
	_check(_connections(editor) == 1, "Plugin connected exactly once")
	_set_code(editor, "extends Node\nfunc test(event: InputEvent):\n\tif event is InputEventMouseButton:\n\t\tevent.but")
	_check(_has(editor, "button_index"), "Mouse member appears in native dropdown")
	_set_code(editor, "extends Node\nfunc test():\n\tMOUSE_BU")
	_check(_has(editor, "MOUSE_BUTTON_LEFT"), "Global constant appears in native dropdown")
	_select(editor, "MOUSE_BUTTON_LEFT")
	_check(editor.get_line(editor.get_caret_line()).ends_with("MOUSE_BUTTON_LEFT"), "Accepting candidate inserts correct constant")
	_set_code(editor, "extends Node\nfunc test():\n\tVector2.ZE")
	_check(_has(editor, "ZERO"), "Builtin constant appears in native dropdown")
	_select(editor, "ZERO")
	_check(editor.get_line(editor.get_caret_line()).ends_with("Vector2.ZERO"), "Qualified constant inserts without duplicate prefix")
	# 让原生引擎先补全，再单独调用补充回调，验证合并不丢失已有候选。
	EditorInterface.set_plugin_enabled("learning_completion", false)
	_check(_connections(editor) == 0, "Disable disconnects callback")
	_set_code(editor, "extends Node\nfunc test():\n\tvar MOUSE_CUSTOM_NATIVE = 1\n\tMOUSE_")
	var native_options := editor.get_code_completion_options()
	_check(_has(editor, "MOUSE_CUSTOM_NATIVE"), "Native local variable baseline exists")
	EditorInterface.set_plugin_enabled("learning_completion", true)
	for index in range(3):
		await get_tree().process_frame
	_check(_connections(editor) == 1, "Reenable attaches exactly once")
	for connection in editor.code_completion_requested.get_connections():
		var callback: Callable = connection.callable
		if _is_plugin_callback(callback):
			callback.call()
	for option in native_options:
		_check(_has(editor, option.display_text), "Preserved native option: " + str(option.display_text))
	_check(_has(editor, "MOUSE_BUTTON_LEFT"), "Merged global constant exists")
	# 不留下不完整的临时文本，也不保存这些测试片段。
	editor.text = "extends Node\n"
	EditorInterface.set_plugin_enabled("learning_completion", false)
	_check(_connections(editor) == 0, "Final disable cleans up")
	print("EDITOR INTEGRATION: %d checks, %d failures" % [_checks, _failures])
	get_tree().quit(1 if _failures else 0)


func _set_code(editor: CodeEdit, source: String) -> void:
	editor.cancel_code_completion()
	editor.text = source
	editor.set_caret_line(editor.get_line_count() - 1)
	editor.set_caret_column(editor.get_line(editor.get_caret_line()).length())
	editor.request_code_completion(true)


func _has(editor: CodeEdit, name: String) -> bool:
	for option in editor.get_code_completion_options():
		if option.display_text == name:
			return true
	return false


func _select(editor: CodeEdit, name: String) -> void:
	var options := editor.get_code_completion_options()
	for index in range(options.size()):
		if options[index].display_text == name:
			editor.set_code_completion_selected_index(index)
			editor.confirm_code_completion()
			return


func _is_plugin_callback(callback: Callable) -> bool:
	var object := callback.get_object()
	return is_instance_valid(object) and object.get_script() != null and object.get_script().resource_path == "res://addons/learning_completion/plugin.gd"


func _connections(editor: CodeEdit) -> int:
	var count := 0
	for connection in editor.code_completion_requested.get_connections():
		if _is_plugin_callback(connection.callable):
			count += 1
	return count


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		push_error(message)
