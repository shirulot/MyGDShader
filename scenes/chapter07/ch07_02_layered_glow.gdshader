shader_type canvas_item;

uniform float sample_radius : hint_range(1.0, 3.0, 1.0) = 1.0; 
uniform float core_radius : hint_range(1.0, 3.0, 1.0) = 1.0; 
uniform float outer_strength : hint_range(0.0, 1.0, 0.01) = 0.3;
// 07.2 起点：保留学习者完成的单层描边，接下来由学习者添加分层。
void fragment() {
	float max_a = 0.0;
	vec3 output_color = vec3(1.0, 0.5, 0.0);
	// 读取原点 RGBA，供轮廓差值与原图合成使用。
	vec4 origin = texture(TEXTURE, UV);
	float core_max_a = 0.0;
	for(float d = 1.0; sample_radius >= d;d++){
		vec4 right_color = texture(TEXTURE, vec2(UV.x - TEXTURE_PIXEL_SIZE.x * d, UV.y));
		vec4 left_color = texture(TEXTURE, vec2(UV.x + TEXTURE_PIXEL_SIZE.x * d , UV.y));
		vec4 bottom_color = texture(TEXTURE, vec2(UV.x , UV.y - TEXTURE_PIXEL_SIZE.y * d));
		vec4 top_color = texture(TEXTURE, vec2(UV.x , UV.y + TEXTURE_PIXEL_SIZE.y * d));
		float max_last = max(max(left_color.a , right_color.a) , max(top_color.a , bottom_color.a)) ;
		max_a = max(max_a,max_last);
		if (d <= core_radius){
			core_max_a = max(max_last,core_max_a);
		}
	}
	
	float output_a = clamp(max_a - origin.a,0.0,1.0);
	float core_mask = clamp(core_max_a - origin.a,0.0,1.0);
	
	// 窄轮廓保持原亮度，宽轮廓降低到三成，取较亮的一份。
	float outline_alpha = clamp(max(core_mask, output_a * outer_strength),0.0,1.0);
	float total_alhpa = clamp(outline_alpha + origin.a,0.0,1.0);
	vec3 mix_origin = mix(origin.rgb,output_color,outline_alpha / max(total_alhpa,0.0001));
	// 暂时显示灰度读数，Alpha 固定为 1，让黑色区域也能看见。
	COLOR = vec4(mix_origin,total_alhpa);
	//COLOR = tex_color;
}
