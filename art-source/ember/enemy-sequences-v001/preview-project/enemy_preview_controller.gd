extends Node2D
## 仅用于审阅序列，五列独立播放同一单位的五个动作，不含 AI 或伤害逻辑。
## 单次动画的资源仍是 loop=false；这里在结束后停留再重新播放。
## 空格暂停/继续，R 从第 0 帧重放，Esc 关闭本预览窗口。

const CATALOG := "res://assets/ember/characters/enemies_v001/sequence_catalog_v001.json"
const ACTIONS := ["idle", "move", "attack", "hit", "death"]
const TITLES := {"idle": "IDLE / 4 FPS", "move": "MOVE / 8 FPS", "attack": "ATTACK / 10 FPS", "hit": "HIT / 12 FPS", "death": "DEATH / 10 FPS"}
const SHORT_NAMES := {"enemy_patrol": "01  PATROL", "enemy_cutter": "02  CUTTER", "enemy_tracked_heavy": "03  TRACKED", "enemy_scout_drone": "04  DRONE"}
var sprites: Array[AnimatedSprite2D] = []
var playback_records: Dictionary = {}
var paused := false
var background_mode := "industrial"
var status_label: Label
var unit_count := 0


func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
	_label("EMBER  |  ENEMY ANIMATION REVIEW  |  DOWN", Vector2(24, 20), 27, Color(0.87, 0.89, 0.84))
	status_label = _label("Space: pause / resume    R: restart    B: background    Esc: close", Vector2(24, 58), 17, Color(0.58, 0.66, 0.67))
	for column in range(ACTIONS.size()):
		_label(TITLES[ACTIONS[column]], Vector2(195 + column * 270, 98), 17, Color(0.78, 0.80, 0.72))
	for unit: Dictionary in catalog.unit_resources:
		var row := unit_count
		unit_count += 1
		var unit_id := str(unit.unit_id)
		_label(SHORT_NAMES.get(unit_id, unit_id), Vector2(20, 207 + row * 216), 18, Color(0.74, 0.79, 0.77))
		var packed := load(str(unit.scene)) as PackedScene
		for column in range(ACTIONS.size()):
			var sprite := packed.instantiate() as AnimatedSprite2D
			var animation := str(ACTIONS[column]) + "_down"
			if not sprite.sprite_frames.has_animation(animation):
				sprite.free()
				_label("PENDING", Vector2(261 + column * 270, 230 + row * 216), 17, Color(0.37, 0.47, 0.49))
				continue
			sprite.name = unit_id + "_" + animation
			sprite.position = Vector2(318 + column * 270, 317 + row * 216)
			sprite.scale = Vector2(2, 2)
			sprite.centered = false
			sprite.offset = Vector2(-64, -104)
			sprite.set_meta("replay_delay", 0.0)
			var record_id := str(sprite.name)
			playback_records[record_id] = {"unit_id": unit_id, "animation": animation, "frames_seen": [0], "finished_count": 0, "looped_count": 0, "events_seen": []}
			sprite.frame_changed.connect(_on_frame_changed.bind(sprite))
			sprite.animation_finished.connect(_on_finished.bind(sprite))
			sprite.animation_looped.connect(_on_looped.bind(sprite))
			add_child(sprite)
			sprites.append(sprite)
			_restart(sprite, animation)
	queue_redraw()


func _process(delta: float) -> void:
	if paused:
		return
	for sprite: AnimatedSprite2D in sprites:
		var remaining := float(sprite.get_meta("replay_delay", 0.0))
		if remaining <= 0.0:
			continue
		remaining -= delta
		sprite.set_meta("replay_delay", remaining)
		if remaining <= 0.0:
			_restart(sprite, str(sprite.animation))


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.keycode == KEY_ESCAPE:
		get_tree().quit()
	elif event.keycode == KEY_R:
		paused = false
		for sprite: AnimatedSprite2D in sprites:
			_restart(sprite, str(sprite.animation))
	elif event.keycode == KEY_SPACE:
		paused = not paused
		for sprite: AnimatedSprite2D in sprites:
			if paused:
				sprite.pause()
			elif float(sprite.get_meta("replay_delay", 0.0)) <= 0.0:
				sprite.play()
	elif event.keycode == KEY_B:
		var modes := ["industrial", "black", "white"]
		background_mode = modes[(modes.find(background_mode) + 1) % modes.size()]
		queue_redraw()
	status_label.text = ("PAUSED  |  " if paused else "PLAYING  |  ") + "Space: pause / resume    R: restart    B: background    Esc: close"


func _restart(sprite: AnimatedSprite2D, animation: String) -> void:
	sprite.set_meta("replay_delay", 0.0)
	sprite.play(animation)
	# AnimatedSprite2D 没有 AnimationPlayer.advance()；明确设为 f00 保证预览重播姿态。
	sprite.set_frame_and_progress(0, 0.0)


func _on_frame_changed(sprite: AnimatedSprite2D) -> void:
	var record: Dictionary = playback_records[str(sprite.name)]
	if not sprite.frame in record.frames_seen:
		record.frames_seen.append(sprite.frame)
	# 只是审阅事件标记，不调用攻击或生成残骸的游戏逻辑。
	if str(sprite.animation).begins_with("attack") and sprite.frame == 3 and not "attack_release_visual" in record.events_seen:
		record.events_seen.append("attack_release_visual")
	if str(sprite.animation).begins_with("death") and sprite.frame == 7 and not "corpse_hold_visual" in record.events_seen:
		record.events_seen.append("corpse_hold_visual")


func _on_finished(sprite: AnimatedSprite2D) -> void:
	playback_records[str(sprite.name)].finished_count += 1
	# death f07 留更久便于观察，重播只属于展示控制器。
	sprite.set_meta("replay_delay", 1.25 if str(sprite.animation).begins_with("death") else 0.55)


func _on_looped(sprite: AnimatedSprite2D) -> void:
	playback_records[str(sprite.name)].looped_count += 1


func _draw() -> void:
	for row in range(unit_count):
		for column in range(ACTIONS.size()):
			var cell := Rect2(187 + column * 270, 128 + row * 216, 259, 209)
			var background := Color.BLACK if background_mode == "black" else (Color.WHITE if background_mode == "white" else Color(0.10, 0.17, 0.19))
			draw_rect(cell, background)
			draw_rect(cell, Color(0.20, 0.28, 0.29), false, 1)
			# 接地点标记只画在预览 UI 中，原始透明帧不含基线或阴影。
			var anchor := Vector2(318 + column * 270, 317 + row * 216)
			draw_line(anchor - Vector2(7, 0), anchor + Vector2(7, 0), Color(0.37, 0.45, 0.42), 1)
			draw_line(anchor - Vector2(0, 4), anchor + Vector2(0, 4), Color(0.37, 0.45, 0.42), 1)


func _label(text: String, position_px: Vector2, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.position = position_px
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	add_child(label)
	return label
