shader_type canvas_item;
uniform float gray_progress : hint_range(0.0, 1.0, 0.05);
uniform float white_flash : hint_range(0.0, 1.0, 0.5);
// 受击颜色：默认白色，可在材质 Inspector 中选择。
uniform vec3 hit_color : source_color = vec3(1.0);

void vertex() {
	// Called for every vertex the material is visible on.
}

void fragment() {
	vec4 tempColor = texture(TEXTURE, UV);
	vec3 outputColor = mix(tempColor.rgb,hit_color,white_flash);
	COLOR = vec4(outputColor,tempColor.a);
}

//void light() {
//	// Called for every pixel for every light affecting the CanvasItem.
//	// Uncomment to replace the default light processing function with this one.
//}
