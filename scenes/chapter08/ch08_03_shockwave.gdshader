shader_type canvas_item;

// 手动进度先用于观察传播过程，后续再加入衰减和自动播放。
uniform float progress : hint_range(0.0, 1.0, 0.01) = 0.0;
// 单次播放的持续时间，单位为秒；自动进度由你接入。
uniform float duration : hint_range(0.2, 5.0, 0.1) = 1.5;
uniform vec3 wave_color : source_color = vec3(0.35, 0.85, 1.0);
// 半径和环宽均以本场景正方形画布的 UV 为单位。
uniform float start_radius : hint_range(0.08, 0.15, 0.01) = 0.08;
uniform float end_radius : hint_range(0.2, 0.48, 0.01) = 0.42;
uniform float wave_width : hint_range(0.03, 0.05, 0.005) = 0.04;
uniform float edge_softness : hint_range(0.001, 0.01, 0.001) = 0.008;

void fragment() {
	float timing = clamp( TIME / duration,0.0,1.0);
	
	// 起点仍是默认采样；由你接入动态半径与环形 Alpha。
	vec4 origin = texture(TEXTURE, UV);
	vec2 center_point = vec2(0.5);
	float uv_center_lenght = length(UV - center_point);
	float diff_lenght = (end_radius - start_radius) * timing;
	float ring_start_radius = start_radius - wave_width;
	float start = clamp(ring_start_radius,ring_start_radius + diff_lenght,end_radius);
	float end = start + wave_width;
	float wave_start_weight = smoothstep(start ,start + edge_softness,uv_center_lenght);
	float wave_end_weight = 1.0 - smoothstep(end - edge_softness , end , uv_center_lenght);
	
	vec3 v1_color = mix(origin.rgb , wave_color,  wave_start_weight * wave_end_weight );
	//float end_weight = 1.0 - step(end_radius,uv_center_lenght);
	
	COLOR = vec4(v1_color,origin.a * wave_start_weight * wave_end_weight * (1.0 - timing));
	
}
