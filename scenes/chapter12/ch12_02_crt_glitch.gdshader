shader_type canvas_item;

// 复用12.1的屏幕输入；CRT各层由你逐步实现。
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform float scan_strength : hint_range(0.0, 1.0, 0.01) = 0.25;
uniform float curvature : hint_range(0.0, 0.5, 0.01) = 0.15;
uniform float glitch_offset : hint_range(0.0, 0.03, 0.01) = 0.01;
uniform float rgb_offset_px : hint_range(0.0, 3.0, 1.0) = 1.0;
uniform float pixel_size_px : hint_range(1.0, 16.0, 1.0) = 4.0;

vec2 get_new_scale_uv (vec2 scale_uv,vec2 screen_uv, float translation_time,bool is_translation){
	vec2 new_scale_uv = scale_uv;
	if(is_translation){
		if(translation_time == 0.0){
			new_scale_uv = vec2(scale_uv.x + glitch_offset,scale_uv.y);
		}else if (translation_time == 1.0){
			new_scale_uv = vec2(scale_uv.x - glitch_offset,scale_uv.y);
		}	
	}
	return new_scale_uv;
}

vec3 get_mirro_rgb(vec4 mirro,vec2 scale_uv,vec2 pix ,bool is_translation){
	vec3 mirro_rgb = mirro.rgb;
	if(is_translation){
		vec4 mirro_left = texture(screen_texture, vec2(scale_uv.x - pix.x,scale_uv.y));
		vec4 mirro_right = texture(screen_texture, vec2(scale_uv.x + pix.x,scale_uv.y));
		mirro_rgb = vec3(mirro_left.r,mirro_rgb.g,mirro_right.b);
	}
	return mirro_rgb;
}

vec4 get_result_color (vec2 newScreenUV, vec2 scale_uv,vec3 mirro_rgb,float mirro_alpha){
	
	float light = 1.0;
	if(newScreenUV.y <= 0.25){
		light  = 1.0 - scan_strength;
	}
	
	float black_weight = 1.0 - step(0.0,scale_uv.x) * step(scale_uv.x,1.0) * step(0.0,scale_uv.y) * step(scale_uv.y,1.0);
	vec3 result_color = mirro_rgb * light;
	float alpha = mirro_alpha;
	if(black_weight >= 1.0 ){
		alpha = 1.0;
		result_color = vec3(0.0);
	} 
	return vec4(result_color,alpha);
}
void fragment() {
	// 默认起点：改为屏幕对应位置的彩色采样，再添加扫描线亮度层。
	vec2 newScreenUV = vec2(SCREEN_UV.x,fract(SCREEN_UV.y * 180.0));
	
	vec2 p = SCREEN_UV - vec2(0.5);
	vec2 scale_uv = vec2(0.5) + p * (1.0 + curvature * dot(p,p));
	
	float time_floor = floor(TIME * 5.0);
	float translation_time = mod(time_floor,2.0);
	float translation_type = mod(time_floor,5.0);
	bool is_translation = SCREEN_UV.y > 0.4 && SCREEN_UV.y < 0.6 && (translation_type == 1.0 || translation_type == 0.0);
	scale_uv = get_new_scale_uv(scale_uv,SCREEN_UV,translation_time,is_translation);
	vec2 pixel_uv = scale_uv;
	if(is_translation && pixel_size_px > 1.0){
		vec2 cell_size_uv = SCREEN_PIXEL_SIZE * pixel_size_px;
		pixel_uv = (floor(scale_uv / cell_size_uv) + vec2(0.5)) * cell_size_uv ; 
	}
	vec4 mirro = texture(screen_texture, pixel_uv);
	vec2 pix = SCREEN_PIXEL_SIZE * rgb_offset_px;
	vec3 mirro_rgb = get_mirro_rgb(mirro,pixel_uv,pix,is_translation);
	vec4 result_color = get_result_color(newScreenUV,pixel_uv,mirro_rgb,mirro.a);
	COLOR = result_color;
}
