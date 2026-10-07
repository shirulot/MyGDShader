extends SceneTree
## 只测继承合并交接风险；旧对照来自冻结r1 ZIP，不运行完整94/GPU。
const NEW_DEMO = preload("res://scripts/ember/building_demo.gd")
const OLD_ASSET = preload("res://scripts/ember/building_asset_v004r1.gd")
var checks: Array[Dictionary] = []
var scene
func _initialize() -> void: call_deferred("_run")
func record(name: String, passed: bool) -> void:
	checks.append({"name":name,"pass":passed})
	if not passed: print("TA_FAIL ",name)
func contacts() -> void:
	for b in scene.buildings: b.set_actor_rects([scene.actor.ground_rect()])
func _run() -> void:
	root.size=Vector2i(1408,800)
	scene=NEW_DEMO.new()
	root.add_child(scene)
	scene.set_process(false)
	scene.actor.set_physics_process(false)
	for b in scene.buildings: b.set_process(false)
	var b=scene.buildings[0]
	var old=OLD_ASSET.new()
	old.building_id=b.building_id
	old.position=Vector2(-4000,-4000)
	root.add_child(old)
	old.set_process(false)
	b.set_actor_rects([])
	old.set_actor_rects([])
	var defaults: Dictionary=b.snapshot()
	record("new_old_default_registration_and_snapshot",b.initialized and old.initialized and b.snapshot()==old.snapshot() and b.footprint_rect()==old.footprint_rect() and b.doors.personnel.safety_rect==old.doors.personnel.safety_rect)
	for x in [old,b]: x.set_locked("personnel",true)
	record("new_old_locked_denial",not old.request_door("personnel",true,Vector2.INF,true) and not b.request_door("personnel",true,Vector2.INF,true) and old.snapshot()==b.snapshot())
	for x in [old,b]:
		x.set_locked("personnel",false)
		x.request_door("personnel",true,Vector2.INF,true)
		x.advance_state(0.32)
	record("new_old_partial_motion",old.snapshot()==b.snapshot() and is_equal_approx(float(b.doors.personnel.progress),0.4))
	for x in [old,b]:
		x.set_power(false)
		x.advance_state(1.0)
	record("new_old_power_freeze",old.snapshot()==b.snapshot() and is_equal_approx(float(b.doors.personnel.progress),0.4))
	for x in [old,b]:
		x.set_power(true)
		x.doors.personnel.progress=0.5
		x.doors.personnel.target=0.0
		var center: float=x.doors.personnel.center_x
		x.set_actor_rects([Rect2(x.position+Vector2(center-9,-12),Vector2(18,12))])
		x.advance_state(0.08)
	record("new_old_occupied_reverse",old.snapshot()==b.snapshot() and b.doors.personnel.obstructed and is_equal_approx(float(b.doors.personnel.target),1.0))
	b.set_actor_rects([])
	b.restore(defaults)
	await physics_frame
	await physics_frame
	var outside: Vector2=b.position+Vector2(float(b.doors.personnel.center_x),27)
	record("new_actual_closed_collision",scene.actor.test_move(Transform2D(0,outside),Vector2(0,-42)))
	b.request_door("personnel",true,Vector2.INF,true)
	b.advance_state(1)
	await physics_frame
	await physics_frame
	record("new_actual_open_clearance",not scene.actor.test_move(Transform2D(0,outside),Vector2(0,-42)))
	for saved_near: bool in [false,true]:
		b.set_actor_rects([])
		b.restore(defaults)
		var near_point: Vector2=b.position+Vector2(float(b.doors.personnel.center_x),6)
		var far_point: Vector2=b.position+Vector2(0,70)
		scene.actor.position=near_point if saved_near else far_point
		contacts()
		b.set_power(false)
		b.set_locked("personnel",true)
		b.doors.personnel.progress=0.5
		b.doors.personnel.target=0.0
		scene.save_state("user://ta_final_order.json")
		var saved_point: Vector2=scene.actor.position
		scene.actor.position=far_point if saved_near else near_point
		contacts()
		b.doors.personnel.target=1.0
		b.doors.personnel.progress=1.0
		scene.load_state("user://ta_final_order.json")
		record("restore_player_first_"+str(saved_near),scene.actor.position==saved_point)
		record("restore_uses_saved_occupancy_"+str(saved_near),is_equal_approx(float(b.doors.personnel.target),1.0 if saved_near else 0.0))
		record("restore_lock_and_power_freeze_"+str(saved_near),b.doors.personnel.locked and not b.powered and is_equal_approx(float(b.doors.personnel.progress),0.5))
	var floor: TileMapLayer=scene.world.get_node("ExistingContinuousFloor")
	record("flattened_floor_final_1100_cells",floor.get_used_cells().size()==1100 and floor.scale==Vector2(0.25,0.25) and floor.tile_set.tile_size==Vector2i(128,128))
	var view:=Rect2(Vector2.ZERO,Vector2(root.size))
	record("retained_help_toast_layout",view.encloses(scene.help_label.get_global_rect()) and view.encloses(scene.toast_label.get_global_rect()) and scene.building_labels.size()==3)
	for name: String in ["control_tower","repair_workshop","logistics_warehouse","control_tower_static","repair_workshop_static","logistics_warehouse_static","demo"]:
		var resource: PackedScene=load("res://scenes/ember/building_assets_v004r1/"+name+".tscn")
		record("load_prefab_"+name,resource!=null and resource.can_instantiate())
	b.set_actor_rects([])
	b.restore(defaults)
	b.set_locked("personnel",true)
	scene.actor.position=outside
	scene.set_process(true)
	var event:=InputEventKey.new()
	event.keycode=KEY_E
	event.physical_keycode=KEY_E
	event.pressed=true
	Input.parse_input_event(event)
	await process_frame
	await process_frame
	record("actual_E_routes_after_merge",scene.toast_label.visible and scene.toast_label.text=="门已锁定" and is_zero_approx(float(b.doors.personnel.target)))
	var failed: Array[Dictionary]=[]
	for item: Dictionary in checks:
		if not item["pass"]: failed.append(item)
	var file:=FileAccess.open("res://ta-runtime-incremental.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"scope":"limited inheritance-flattening handoff: one gate pair, saved near/far, scene/input/load","checks":checks,"total":checks.size(),"passed":checks.size()-failed.size(),"failures":failed,"engine":Engine.get_version_info()},"\t"))
	print("TA_RUNTIME ",checks.size()-failed.size(),"/",checks.size())
	old.queue_free()
	scene.queue_free()
	await process_frame
	quit(0 if failed.is_empty() else 1)
