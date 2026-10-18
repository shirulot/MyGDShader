shader_type canvas_item;

uniform float sample_radius : hint_range(1.0, 3.0, 1.0) = 1.0; 
uniform float core_radius : hint_range(1.0, 3.0, 1.0) = 1.0; 
uniform float outer_strength : hint_range(0.0, 1.0, 0.01) = 0.3;

uniform	vec3 border_color  : source_color = vec3(1.0, 0.5, 0.0);
// 07.3 起点：复用学习者完成的双层描边，颜色参数与强调方案由学习者配置。
void fragment() {
	float max_a = 0.0;
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
	
	// 合并核心与外圈的 Alpha，外圈强度由参数控制。
	float outline_alpha = clamp(max(core_mask, output_a * outer_strength),0.0,1.0);
	float total_alhpa = clamp(outline_alpha + origin.a,0.0,1.0);
	vec3 mix_origin = mix(origin.rgb,border_color,outline_alpha / max(total_alhpa,0.0001));
	// 输出原图与双层轮廓的混合颜色及真实总 Alpha。
	COLOR = vec4(mix_origin,total_alhpa);
}
