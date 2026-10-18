shader_type canvas_item;

uniform float sample_radius : hint_range(1.0, 3.0, 1.0) = 1.0; 
// 07.1 起点：只读取原图，Alpha 观察和描边逻辑由学习者逐步添加。
void fragment() {
	float max_a = 0.0;
	vec3 output_color = vec3(1.0, 0.5, 0.0);
	// 沿用原始 UV，读回完整 RGBA；当前没有邻域偏移。
	vec4 origin = texture(TEXTURE, UV);
	for(float d = 1.0; sample_radius >= d;d++){
		vec4 right_color = texture(TEXTURE, vec2(UV.x + TEXTURE_PIXEL_SIZE.x * d, UV.y));
		vec4 left_color = texture(TEXTURE, vec2(UV.x - TEXTURE_PIXEL_SIZE.x * d , UV.y));
		vec4 bottom_color = texture(TEXTURE, vec2(UV.x , UV.y + TEXTURE_PIXEL_SIZE.y * d));
		vec4 top_color = texture(TEXTURE, vec2(UV.x , UV.y - TEXTURE_PIXEL_SIZE.y * d));
		float max_last = max(max(left_color.a , right_color.a) , max(top_color.a , bottom_color.a)) ;
		max_a = max(max_a,max_last);
	}
	
	float output_a = clamp(max_a - origin.a,0.0,1.0);
	
	float total_alpha = clamp(origin.a + output_a,0.0,1.0);
	float out_weight = output_a / max(total_alpha,0.00001);
	vec3 mix_rgb = mix(origin.rgb,output_color,out_weight);
	COLOR = vec4(mix_rgb,total_alpha);
	//COLOR = tex_color;
}
