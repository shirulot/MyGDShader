shader_type canvas_item;

void fragment() {
	vec4 origin = texture(TEXTURE, UV);
	float wave = sin(TIME);

	COLOR = vec4(origin.rgb * ((wave + 1.0) / 2.0 * 0.7 +0.3),origin.a);
	
}
