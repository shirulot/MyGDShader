@tool
extends EditorPlugin
## 在原生补全回调之后合并候选，不替换 CodeEdit、不保存或修改用户文本。

const Provider = preload("completion_provider.gd")
var _provider := Provider.new()
var _script_editor: ScriptEditor
var _editors: Dictionary = {}


func _enter_tree() -> void:
	_script_editor = EditorInterface.get_script_editor()
	_script_editor.editor_script_changed.connect(_on_script_changed)
	_script_editor.script_close.connect(_on_script_closed)
	_attach_current.call_deferred()


func _exit_tree() -> void:
	if is_instance_valid(_script_editor):
		_script_editor.editor_script_changed.disconnect(_on_script_changed)
		_script_editor.script_close.disconnect(_on_script_closed)
	for editor in _editors:
		_disconnect_editor(editor)
	_editors.clear()


func _on_script_changed(_script: Script) -> void:
	_attach_current.call_deferred()


func _on_script_closed(_script: Script) -> void:
	_prune_editors.call_deferred()


func _prune_editors() -> void:
	for editor in _editors.keys():
		if not is_instance_valid(editor):
			_editors.erase(editor)


func _attach_current() -> void:
	if not is_inside_tree():
		return
	_prune_editors()
	var script := _script_editor.get_current_script()
	if script == null or not script is GDScript:
		return
	var current := _script_editor.get_current_editor()
	if current == null:
		return
	var editor := current.get_base_editor() as CodeEdit
	if editor == null or _editors.has(editor):
		return
	var callback := _complete.bind(editor)
	# 编辑器自带的监听先执行；这里随后取得原生候选并保留它们。
	editor.code_completion_requested.connect(callback)
	_editors[editor] = callback


func _disconnect_editor(editor: Variant) -> void:
	if is_instance_valid(editor):
		var callback: Callable = _editors[editor]
		if editor.code_completion_requested.is_connected(callback):
			editor.code_completion_requested.disconnect(callback)


func _complete(editor: CodeEdit) -> void:
	if not is_instance_valid(editor) or editor.get_caret_count() != 1:
		return
	var extras := _provider.get_candidates(editor.text, editor.get_caret_line(), editor.get_caret_column())
	if extras.is_empty():
		return
	var existing := editor.get_code_completion_options()
	var seen := {}
	for option in existing:
		seen[option.insert_text] = true
	var additions: Array[Dictionary] = []
	for option in extras:
		if not seen.has(option.insert_text):
			seen[option.insert_text] = true
			additions.append(option)
	if additions.is_empty():
		return
	# update_code_completion_options 会替换整份列表，所以先重新提交原生项。
	for option in existing:
		editor.add_code_completion_option(option.kind, option.display_text, option.insert_text,
			option.font_color, option.icon, option.default_value, option.get("location", 1024))
	for option in additions:
		var icon_name := "MemberConstant" if option.kind == CodeEdit.KIND_CONSTANT else "MemberProperty"
		if option.kind == CodeEdit.KIND_FUNCTION:
			icon_name = "MemberMethod"
		editor.add_code_completion_option(option.kind, option.display_text, option.insert_text,
			editor.get_theme_color("font_color"), EditorInterface.get_base_control().get_theme_icon(icon_name, "EditorIcons"),
			option.default_value)
	editor.update_code_completion_options(false)
