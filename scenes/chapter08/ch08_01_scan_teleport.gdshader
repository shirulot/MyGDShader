shader_type canvas_item;
//uniform float progress : hint_range(0.0, 1.0, 0.01) = 0.0;
uniform vec3 edge_color : source_color = vec3(1.0);
uniform float scan_strength : hint_range(0.0, 1.0, 0.1) = 0.3;
uniform float teleport_speed : hint_range(0.0, 1.0, 0.1) = 0.2;
uniform vec3 blue_bar :source_color = vec3(0.25, 0.75, 1.0);
// 灰度数据：只作为边带的局部细节输入，不使用 source_color。
uniform sampler2D noise_texture : filter_linear, repeat_disable;
uniform float noise_strength : hint_range(0.0, 1.0, 0.05) = 0.5;
uniform float edge_width : hint_range(0.01, 1.0, 0.01) = 0.05;
uniform float edge_strength : hint_range(0.0, 1.0, 0.01) = 1.0;

void fragment() {
	float progress = 0.0;
	// 起点：读取原图 RGBA。方向进度和显隐逻辑由你添加。
	vec4 origin = texture(TEXTURE, UV);
	vec4 noise = texture(noise_texture, UV);
	vec3 origin_color = origin.rgb;
	
	progress = (sin(TIME * PI * teleport_speed) + 1.0) / 2.0  ;
	// 从顶部外开始，最终把整条扫描带送出底部
	//float scan_position = mix(-edge_width, 1.0 + edge_width * 2.0, progress);
	float alpha = origin.a;
	float light_end_progress = progress + edge_width;
	
	// 先移动整图坐标，再划分成8格，并回绕到每格内部
	float scan_local_y = fract((UV.y - TIME * 0.1) * 8.0);

	// 每格前25%取1，其余取0，作为蓝色混合权重
	float blue_zone_weight = 1.0 - step(0.25, scan_local_y);

	vec3 result_color = mix(origin_color , blue_bar,blue_zone_weight * scan_strength);
	
	if (UV.y < progress){
		alpha = 0.0;
	}
	float light_weight = smoothstep(progress,light_end_progress,UV.y);
	float lignth_show_weight = step(UV.y,light_end_progress);
	// 第一种效果：你原来的平滑白边
	float plain_edge = light_weight * lignth_show_weight * edge_strength;
	// 第二种效果：在同一条白边内，让噪声调节白色混入多少
	float noisy_edge = plain_edge * noise.r;
	// 在两种效果之间过渡
	float edge_weight = mix(plain_edge, noisy_edge, noise_strength);
	vec3 mix_color = mix(result_color,edge_color, edge_weight);
	
	COLOR = vec4(mix_color,alpha);
	
}
