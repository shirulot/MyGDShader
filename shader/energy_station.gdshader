shader_type canvas_item;
uniform int state : hint_range(0, 3, 1);
uniform float stateProgress : hint_range(0.0, 1.0, 0.01);
uniform bool collecting = false;

const vec3 stateSafe = vec3(0.2, 0.9, 0.8);
const vec3 stateWarning = vec3(1.0, 0.6, 0.15);
const vec3 stateBurst = vec3(1.0, 0.2, 0.15);
const vec3 stateCooldown = vec3(0.4, 0.4, 0.4);

void vertex() {
	// Called for every vertex the material is visible on.
}

void fragment() {
	vec4 originColor = texture(TEXTURE,UV);
	vec3 mixColor = vec3(0);
	if(state == 0){
		mixColor = stateSafe;
	}else if(state == 1){
		mixColor = stateWarning;
	}else if(state == 2){
		mixColor = stateBurst;
	}else if(state == 3){
		mixColor = stateCooldown;
	}
	
	float progress = stateProgress;
	if(stateProgress > 0.5){
		progress = 1.0 - clamp(stateProgress,0.0,1.0);
	}
	
	float timeColorWeight = 1.0;
	if(collecting){
		timeColorWeight = (sin(TIME) + 1.0) / 2.0 * 0.2 + 0.8;
	}
	vec3 resultColor = mix(originColor.rgb,mixColor,progress);
	COLOR = vec4(resultColor * timeColorWeight,originColor.a);
	// Called for every pixel the material is visible on.
}

//void light() {
//	// Called for every pixel for every light affecting the CanvasItem.
//	// Uncomment to replace the default light processing function with this one.
//}
