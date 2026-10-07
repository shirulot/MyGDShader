shader_type canvas_item;
uniform float progress : hint_range(0.0, 1.0, 0.01);

void vertex() {
	// Called for every vertex the material is visible on.
}

void fragment() {
	vec4 originColor = texture(TEXTURE,UV);
	vec3 mixColor = mix(originColor.rgb, vec3(0) ,progress);
	COLOR = vec4(mixColor,originColor.a);
}

//void light() {
//	// Called for every pixel for every light affecting the CanvasItem.
//	// Uncomment to replace the default light processing function with this one.
//}
