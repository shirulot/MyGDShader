extends Node2D


var point :float = 0.0
# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass


func _add_point(p: float) -> void:
	point+= p
	print("现有能量：%.2f" % point)
	Game.update_energy_point(point)
	
