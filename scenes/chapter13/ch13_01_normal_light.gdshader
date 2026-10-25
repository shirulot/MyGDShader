shader_type canvas_item;
//render_mode unshaded;
uniform float normal_strength :hint_range(0.0, 1.0, 0.1) = 0.0;
uniform bool flip_normal_y  = false;
uniform vec3 light_color :source_color = vec3(1.0, 0.65, 0.30);

void light(){
	float light_weight = max(dot(NORMAL,LIGHT_DIRECTION),0.0);
	vec3 light_rgb = LIGHT_COLOR.rgb * light_color * LIGHT_ENERGY * COLOR.rgb;
	LIGHT = vec4(light_rgb * light_weight ,LIGHT_COLOR.a);
}
void fragment() {
	// 起点只读取底色。法线由 CanvasTexture 暂时接入，后续由你写 Shader 输入。
	vec4 origin = texture(TEXTURE, UV);
	vec4 normal = texture(NORMAL_TEXTURE,UV);
	vec3 flat_normal_rgb = vec3(0.5,0.5,1.0);
	vec3 reverse_g_normal = normal.rgb;
	if (flip_normal_y){
		reverse_g_normal = vec3(normal.r, 1.0 - normal.g ,normal.b);
	}
	NORMAL_MAP = mix(reverse_g_normal,flat_normal_rgb,normal_strength);
	COLOR = origin;
}
