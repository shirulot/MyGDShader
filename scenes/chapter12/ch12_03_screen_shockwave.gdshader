shader_type canvas_item;

// 复用12.1已经学过的原样读屏；本场景不叠加12.2的CRT/Glitch。
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

// 当前只准备输入：点击传参、定位标记及后续折射环由你逐步实现。
uniform vec2 center_uv = vec2(0.5);
uniform float ring_radius :hint_range(0.0, 0.8, 0.01) = 0.18;
uniform float ring_half_width : hint_range(0.0, 0.1, 0.001) = 0.015;
uniform float refraction_px : hint_range(0.0, 24.0, 1.0) = 8.0;
uniform vec4 marker_color : source_color = vec4(0.25, 0.75, 1.0, 1.0);

void fragment() {
	vec4 screen_color = texture(screen_texture, SCREEN_UV);
	vec2 screen_zone = SCREEN_UV - center_uv;
	float zone_ratio = SCREEN_PIXEL_SIZE.y / max(SCREEN_PIXEL_SIZE.x,0.0001);
	vec2 abs_zone = vec2(zone_ratio * screen_zone.x , screen_zone.y);
	float click_length = length(abs_zone);
	//float click_weight = 1.0 -  smoothstep(0.01,click_center_lenght,click_length) ;
	float out_ring_weight = 1.0 - step(ring_radius + ring_half_width, click_length);
	float inner_ring_weight = 1.0 - step(ring_radius - ring_half_width , click_length);
	float ring_weight = out_ring_weight - inner_ring_weight;
	vec2 offset = SCREEN_PIXEL_SIZE * refraction_px;
	vec4 screen = texture(screen_texture,SCREEN_UV);
	
	vec4 result_color = mix(screen_color,screen,ring_weight);
	if( ring_weight > 0.0 ){
		vec2 direction = abs_zone / max(click_length, 0.00001);
		offset = offset * direction;
		//offset = offset * screen_zone / abs (screen_zone);
		screen = texture(screen_texture,SCREEN_UV +  offset);
		result_color = mix(screen_color,screen,ring_weight);
	}
	
	COLOR = result_color;
}
