extends SceneTree
var preview: Node2D
var previous := -1
var loops := 0
var frames_seen: Array = []
var slow_seen: Array = []
var elapsed := 0.0
var recording := false
func _initialize() -> void:
	call_deferred("run")
func _process(delta: float) -> bool:
	if not recording: return false
	elapsed+=delta
	var frame := int(preview.frame_index)
	if not frames_seen.has(frame): frames_seen.append(frame)
	var slow := int(preview.time)%8
	if not slow_seen.has(slow): slow_seen.append(slow)
	if previous==7 and frame==0: loops+=1
	previous=frame
	return false
func run() -> void:
	preview=load("res://preview.tscn").instantiate()
	root.add_child(preview)
	recording=true
	await create_timer(8.4).timeout
	recording=false
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://qa/gpu_playback.png")
	var report := {"status":"PASS" if frames_seen.size()==8 and loops>=2 and slow_seen.size()==8 else "FAIL","scope":"Runtime traversal only, not art acceptance","renderer":RenderingServer.get_video_adapter_name(),"elapsed_seconds":elapsed,"fps":8,"frames_seen":frames_seen,"normal_loops":loops,"slow_fps":1,"slow_frames_seen":slow_seen,"atlas_sha256":FileAccess.get_sha256("res://output/move_down_v003.png")}
	FileAccess.open("res://qa/gpu_playback.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print(JSON.stringify(report))
	quit()
