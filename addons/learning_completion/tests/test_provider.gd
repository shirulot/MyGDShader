extends SceneTree

const Provider = preload("../completion_provider.gd")
var provider := Provider.new()
var failures := 0
var checks := 0


func _initialize() -> void:
	# 光标用 | 表示；输入片段不必能编译，模拟正在打字的真实情况。
	_expect("extends Node\nfunc input(event: InputEvent):\n\tif event is InputEventMouseButton:\n\t\tevent.|", "button_index")
	_expect("func input(event: InputEvent):\n\tif event is InputEventMouseButton:\n\t\tevent.|", "position")
	_expect("func input(event: InputEvent):\n\tif event is InputEventMouseButton:\n\t\tpass\n\tevent.|", "button_index", false)
	_expect("func input(event: InputEvent):\n\tif event is InputEventMouseButton:\n\t\tpass\n\telse:\n\t\tevent.|", "button_index", false)
	_expect("func input(event: InputEvent):\n\tif event is InputEventMouseButton or true:\n\t\tevent.|", "button_index", false)
	_expect("func first(event: InputEventMouseButton):\n\tpass\nfunc second(event: InputEvent):\n\tevent.|", "button_index", false)
	_expect("func input(event: InputEvent):\n\tvar mouse := event as InputEventMouseButton\n\tmouse.|", "button_index")
	_expect("var mouse: InputEventMouseButton\nfunc input():\n\tmouse.|", "pressed")
	_expect("func input():\n\tvar mouse := InputEventMouseButton.new()\n\tmouse.|", "button_index")
	_expect("func input():\n\tvar mouse := InputEventMouseButton.new()\n\tmouse = InputEventKey.new()\n\tmouse.|", "button_index", false)
	_expect("func input(event: InputEventMouseButton):\n\tevent.position.|", "x")
	_expect("extends Node\nfunc input():\n\tget_viewport().|", "get_visible_rect()")
	_expect("func input():\n\tMOUSE_BU|", "MOUSE_BUTTON_LEFT")
	_expect("func input():\n\tKEY_SP|", "KEY_SPACE")
	_expect("func input():\n\tNode.PROCESS_MODE_|", "PROCESS_MODE_ALWAYS")
	_expect("func input():\n\tVector2.|", "ZERO")
	_expect("func input():\n\tMouseButton.MOUSE_BUTTON_|", "MOUSE_BUTTON_LEFT")
	_expect("func input():\n\tNode.ProcessMode.PROCESS_MODE_|", "PROCESS_MODE_ALWAYS")
	_expect("const CUSTOM_LIMIT = 8\nfunc input():\n\tCUSTOM_|", "CUSTOM_LIMIT")
	_expect("func input():\n\tconst LOCAL_LIMIT = 8\n\tLOCAL_|", "LOCAL_LIMIT")
	_expect("func input():\n\tif true:\n\t\tconst LOCAL_LIMIT = 8\n\tLOCAL_|", "LOCAL_LIMIT", false)
	_expect("func input():\n\t# MOUSE_BU|", "MOUSE_BUTTON_LEFT", false)
	_expect('func input():\n\tprint("MOUSE_BU|', "MOUSE_BUTTON_LEFT", false)
	_expect('func input():\n\tvar text = """example\nMOUSE_BU|', "MOUSE_BUTTON_LEFT", false)
	_expect('func input():\n\tvar text = "if event is InputEventMouseButton:"\n\tevent.|', "button_index", false)
	_expect("func input(event: InputEventKey):\n\tevent.|", "physical_keycode")
	_expect("func input():\n\tunknown.|", "button_index", false)
	_expect("func input():\n\tVector2.|", "length()", false)
	_expect("var event: InputEventMouseButton\nfunc input(event):\n\tevent.|", "button_index", false)
	_expect("var event: InputEventMouseButton\nfunc input():\n\tfor event in []:\n\t\tevent.|", "button_index", false)
	print("PROVIDER TESTS: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)


func _expect(source: String, name: String, expected := true) -> void:
	checks += 1
	var caret := source.find("|")
	var before := source.left(caret).split("\n")
	var options := provider.get_candidates(source.replace("|", ""), before.size() - 1, before[-1].length())
	var found := false
	for option in options:
		if option.display_text == name:
			found = true
	if found != expected:
		failures += 1
		push_error("Expected %s present=%s in %s" % [name, expected, source])
