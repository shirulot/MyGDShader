extends SceneTree
## 迁移增量探针：只加载新入口及18张皮肤，不实例化UI、不修改生产资源。
const REPORT := "res://art-source/ember/ta-review-v001/ui-folder-migration-independent/load-entry-minimal.json"

func _initialize() -> void:
	call_deferred("_audit")

func _audit() -> void:
	var records: Array[Dictionary] = []
	var failed := false
	var inventory: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ember/ui_final/skins/inventory.json"))
	for item: Dictionary in inventory.assets:
		var path := str(item.file)
		var texture := ResourceLoader.load(path) as Texture2D
		var valid := texture != null
		var size := Vector2i.ZERO if texture == null else Vector2i(texture.get_width(), texture.get_height())
		valid = valid and size == Vector2i(int(item.canvas[0]), int(item.canvas[1]))
		failed = failed or not valid
		records.append({"path": path, "loaded": texture != null, "size": [size.x, size.y], "expected_canvas": item.canvas, "uid": ResourceUID.id_to_text(ResourceLoader.get_resource_uid(path)), "pass": valid})
	for path: String in ["res://assets/ember/ui_final/ui.tscn", "res://assets/ember/ui_final/demo.tscn"]:
		var scene := ResourceLoader.load(path) as PackedScene
		failed = failed or scene == null
		records.append({"path": path, "loaded_as_packed_scene": scene != null, "pass": scene != null})
	var report := {"status": "FAIL" if failed else "PASS", "scope": "18 skin textures and two new PackedScene entries only; no UI instantiation or interaction replay", "engine": Engine.get_version_info(), "records": records}
	var file := FileAccess.open(REPORT, FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print("UI_MIGRATION_MINIMAL ", report.status, " loads=", records.size())
	quit(1 if failed else 0)
