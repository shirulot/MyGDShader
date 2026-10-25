@tool
extends RefCounted
## 补充候选生成器：只读取文本和引擎元数据，不加载或运行用户脚本。
## 这是保守的局部类型分析，不尝试替代 GDScript 编译器。

var _api: Dictionary = {}
var _globals: Dictionary = {}
var _member_cache: Dictionary = {}
var _regex_cache: Dictionary = {}


func _init() -> void:
	var path := (get_script() as Script).resource_path.get_base_dir().path_join("api_index.json")
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if parsed is Dictionary:
		_api = parsed
	for enumeration in _api.get("global_enums", []):
		for item in enumeration.values:
			_globals[item.name] = item.value
	for item in _api.get("global_constants", []):
		_globals[item.name] = item.value
	# GDScript 的数学常量不在 GDExtension 的全局枚举里。
	_globals.merge({"PI": PI, "TAU": TAU, "INF": INF, "NAN": NAN})


func get_candidates(source: String, line: int, column: int) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var lines := source.split("\n")
	if line < 0 or line >= lines.size():
		return result
	# 注释和字符串用等长空白替换，既保留列号，也不从字符串中推断类型。
	var cleaned := _mask_non_code(source)
	var clean_lines: PackedStringArray = cleaned.lines
	column = clampi(column, 0, lines[line].length())
	if _caret_in_non_code(source, line, column):
		return result
	var before := clean_lines[line].left(column)
	var member := _match("([A-Za-z_][A-Za-z_0-9]*(?:\\(\\))?(?:\\.[A-Za-z_][A-Za-z_0-9]*(?:\\(\\))?)*)\\.([A-Za-z_0-9]*)$", before)
	var scope := _scope_at(clean_lines, line, column)
	if member:
		var receiver := member.get_string(1)
		var prefix := member.get_string(2)
		# NativeClass.CONSTANT / Vector2.ZERO / MouseButton.MOUSE_BUTTON_LEFT。
		if _known_type(receiver):
			return _members(receiver, true, prefix)
		for enumeration in _api.get("global_enums", []):
			if enumeration.name == receiver:
				for item in enumeration.values:
					_add_constant(result, item.name, item.value, prefix)
				return result
		var class_enum := receiver.split(".")
		if class_enum.size() == 2 and ClassDB.class_exists(class_enum[0]):
			if ClassDB.class_has_enum(class_enum[0], class_enum[1]):
				for name in ClassDB.class_get_enum_constants(class_enum[0], class_enum[1]):
					_add_constant(result, name, ClassDB.class_get_integer_constant(class_enum[0], name), prefix)
				return result
		var type := _resolve_type(receiver, scope.types)
		if not type.is_empty():
			return _members(type, false, prefix)
		return result
	var word := _match("([A-Za-z_][A-Za-z_0-9]*)$", before)
	if word == null:
		return result
	var prefix := word.get_string(1)
	# 两个字符后才补全全局常量，避免刚开始输入就出现大量无关项。
	if prefix.length() < 2:
		return result
	for name in _globals:
		_add_constant(result, name, _globals[name], prefix)
	for name in scope.constants:
		_add_constant(result, name, null, prefix)
	var base_type: String = scope.types.get("self", "")
	if ClassDB.class_exists(base_type):
		for name in ClassDB.class_get_integer_constant_list(base_type):
			_add_constant(result, name, ClassDB.class_get_integer_constant(base_type, name), prefix)
	return result


func _scope_at(lines: PackedStringArray, caret_line: int, column: int) -> Dictionary:
	var globals := {"types": {}, "constants": {}}
	# 类成员可以在当前函数之后声明，先收集顶层声明。
	for raw in lines:
		if _indent(raw) != 0:
			continue
		var base := _match("^extends\\s+(\\w+)", raw)
		if base:
			globals.types["self"] = base.get_string(1)
		_declare(raw, globals)
	var frames: Array[Dictionary] = [{"indent": -1, "scope": globals.duplicate(true)}]
	for index in range(caret_line + 1):
		var raw := lines[index]
		if index == caret_line:
			raw = raw.left(column)
		if raw.strip_edges().is_empty():
			continue
		var indent := _indent(raw)
		while frames.size() > 1 and indent <= int(frames.back().indent):
			frames.pop_back()
		var scope: Dictionary = frames.back().scope
		if index == caret_line:
			return scope
		var statement := raw.strip_edges()
		var function := _match("^(?:static\\s+)?func\\s+\\w+\\s*\\((.*)\\)", statement)
		if function:
			var local: Dictionary = globals.duplicate(true)
			for parameter_text in function.get_string(1).split(","):
				var parameter := _match("^\\s*(\\w+)(?:\\s*:\\s*(\\w+))?", parameter_text)
				if parameter:
					# 未标注类型的参数也会遮蔽同名类成员，不能沿用外层类型。
					local.types[parameter.get_string(1)] = parameter.get_string(2)
			frames.append({"indent": indent, "scope": local})
			continue
		_declare(statement, scope)
		# 一旦重新赋值，撤销对旧值的推断，宁可交回原生补全也不误报。
		var assignment := _match("^(\\w+)\\s*=(?!=)\\s*(.*)$", statement)
		if assignment:
			scope.types[assignment.get_string(1)] = _expression_type(assignment.get_string(2), scope.types)
		if statement.ends_with(":"):
			var child: Dictionary = scope.duplicate(true)
			var loop_variable := _match("^for\\s+(\\w+)\\s+in\\s", statement)
			if loop_variable:
				child.types[loop_variable.get_string(1)] = ""
			# 只处理明确的正向类型判断；or / not 不保证变量属于该类型。
			if statement.begins_with("if ") or statement.begins_with("elif "):
				var condition := statement.substr(statement.find(" ") + 1).trim_suffix(":").strip_edges()
				var guard := _match("^(\\w+)\\s+is\\s+(\\w+)$", condition)
				if guard:
					child.types[guard.get_string(1)] = guard.get_string(2)
			frames.append({"indent": indent, "scope": child})
	return frames.back().scope


func _declare(statement: String, scope: Dictionary) -> void:
	var declaration := _match("(?:^|\\s)(var|const)\\s+(\\w+)\\s*(?::\\s*([A-Za-z_]\\w*))?\\s*(?::?=\\s*(.*))?$", statement.strip_edges())
	if declaration == null:
		return
	var name := declaration.get_string(2)
	var type := declaration.get_string(3)
	if type.is_empty():
		type = _expression_type(declaration.get_string(4), scope.types)
	scope.types[name] = type
	if declaration.get_string(1) == "const":
		scope.constants[name] = true


func _expression_type(expression: String, types: Dictionary) -> String:
	var cast := _match("\\bas\\s+(\\w+)\\s*$", expression)
	if cast:
		return cast.get_string(1)
	var construction := _match("^(\\w+)\\.new\\(", expression)
	if construction:
		return construction.get_string(1)
	var builtin := _match("^(\\w+)\\(", expression)
	if builtin and _api.get("builtins", {}).has(builtin.get_string(1)):
		return builtin.get_string(1)
	return _resolve_type(expression.strip_edges(), types)


func _resolve_type(expression: String, types: Dictionary) -> String:
	var parts := expression.split(".")
	var type: String = types.get(parts[0], "")
	if type.is_empty() and parts[0].ends_with("()"):
		type = _property_type(types.get("self", ""), parts[0])
	for index in range(1, parts.size()):
		type = _property_type(type, parts[index])
	return type


func _property_type(type: String, member: String) -> String:
	var method := member.ends_with("()")
	var name := member.trim_suffix("()")
	if ClassDB.class_exists(type):
		if method:
			for info in ClassDB.class_get_method_list(type):
				if info.name == name:
					return _info_type(info["return"])
		else:
			for info in ClassDB.class_get_property_list(type):
				if info.name == name:
					return _info_type(info)
	elif _api.get("builtins", {}).has(type):
		var data: Dictionary = _api.builtins[type]
		for info in data.get("methods" if method else "members", []):
			if info.name == name:
				return str(info.get("return_type" if method else "type", ""))
	return ""


func _info_type(info: Dictionary) -> String:
	if int(info.get("type", TYPE_NIL)) == TYPE_OBJECT:
		return str(info.get("class_name", ""))
	return type_string(int(info.get("type", TYPE_NIL)))


func _members(type: String, static_only: bool, prefix: String) -> Array[Dictionary]:
	var key := type + (":static" if static_only else ":instance")
	if not _member_cache.has(key):
		var options: Array[Dictionary] = []
		if ClassDB.class_exists(type):
			for name in ClassDB.class_get_integer_constant_list(type):
				_add_constant(options, name, ClassDB.class_get_integer_constant(type, name), "")
			if not static_only:
				for info in ClassDB.class_get_property_list(type):
					# 分组/分类标题不是可访问属性。
					if int(info.usage) & (PROPERTY_USAGE_CATEGORY | PROPERTY_USAGE_GROUP | PROPERTY_USAGE_SUBGROUP):
						continue
					options.append(_option(info.name, CodeEdit.KIND_MEMBER))
			for info in ClassDB.class_get_method_list(type):
				if not static_only or int(info.flags) & METHOD_FLAG_STATIC:
					_add_method(options, info.name, info.args)
		elif _api.get("builtins", {}).has(type):
			var data: Dictionary = _api.builtins[type]
			for info in data.constants:
				_add_constant(options, info.name, info.value, "")
			if not static_only:
				for info in data.members:
					options.append(_option(info.name, CodeEdit.KIND_MEMBER))
			for info in data.methods:
				if not static_only or info.is_static:
					_add_method(options, info.name, info.arguments)
		_member_cache[key] = options
	var filtered: Array[Dictionary] = []
	for option in _member_cache[key]:
		if String(option.display_text).to_lower().begins_with(prefix.to_lower()):
			filtered.append(option)
	return filtered


func _add_method(options: Array[Dictionary], name: String, arguments: Array) -> void:
	# 不补充引擎内部名称或虚方法，原生编辑器仍负责其专用提示。
	if name.begins_with("_"):
		return
	var option := _option(name + "()", CodeEdit.KIND_FUNCTION)
	option.insert_text = name + ("()" if arguments.is_empty() else "(")
	options.append(option)


func _add_constant(options: Array[Dictionary], name: String, value: Variant, prefix: String) -> void:
	if name.to_lower().begins_with(prefix.to_lower()):
		var option := _option(name, CodeEdit.KIND_CONSTANT)
		option.default_value = value
		options.append(option)


func _option(name: String, kind: int) -> Dictionary:
	return {"kind": kind, "display_text": name, "insert_text": name, "default_value": null}


func _known_type(name: String) -> bool:
	return ClassDB.class_exists(name) or _api.get("builtins", {}).has(name)


func _indent(line: String) -> int:
	var width := 0
	for character in line:
		if character == "\t":
			width += 4
		elif character == " ":
			width += 1
		else:
			break
	return width


func _regex(pattern: String) -> RegEx:
	if not _regex_cache.has(pattern):
		var regex := RegEx.new()
		regex.compile(pattern)
		_regex_cache[pattern] = regex
	return _regex_cache[pattern]


func _match(pattern: String, text: String) -> RegExMatch:
	return _regex(pattern).search(text)


func _caret_in_non_code(source: String, line: int, column: int) -> bool:
	var lines := source.split("\n")
	var prefix := "\n".join(lines.slice(0, line))
	if line > 0:
		prefix += "\n"
	prefix += lines[line].left(column)
	return _mask_non_code(prefix).inside


func _mask_non_code(source: String) -> Dictionary:
	var output := ""
	var quote := ""
	var comment := false
	var escaped := false
	var index := 0
	while index < source.length():
		var character := source[index]
		if character == "\n":
			output += "\n"
			comment = false
			escaped = false
			index += 1
			continue
		if comment:
			output += " "
		elif not quote.is_empty():
			if not escaped and source.substr(index, quote.length()) == quote:
				output += " ".repeat(quote.length())
				index += quote.length()
				quote = ""
				continue
			output += " "
			escaped = not escaped and character == "\\"
		elif character == "#":
			comment = true
			output += " "
		elif character == "\"" or character == "'":
			quote = character.repeat(3) if source.substr(index, 3) == character.repeat(3) else character
			output += " ".repeat(quote.length())
			index += quote.length()
			continue
		else:
			output += character
		index += 1
	return {"lines": output.split("\n"), "inside": comment or not quote.is_empty()}
