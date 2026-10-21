shader_type canvas_item;
// 08.1：滚动蓝条、扫描显隐与噪声调制边带。UV.y 默认从上向下增大。
// 下方手动 progress 接口已停用，当前由 fragment 内的 TIME 生成进度。
//uniform float progress : hint_range(0.0, 1.0, 0.01) = 0.0;
// 边带的目标颜色：通过 mix 混入原图，并不是独立的发光层。
uniform vec3 edge_color : source_color = vec3(1.0);
// 蓝色条纹的颜色混合比例；不影响透明度。
uniform float scan_strength : hint_range(0.0, 1.0, 0.1) = 0.3;
// 相位为 TIME * PI * teleport_speed；非零时完整往返周期为 2 / teleport_speed 秒。
// 速度为 0 时，sin(0) 使进度固定在 0.5，而不是固定在 0。
uniform float teleport_speed : hint_range(0.0, 1.0, 0.1) = 0.2;
uniform vec3 blue_bar :source_color = vec3(0.25, 0.75, 1.0);
// 灰度数据：只作为边带的局部细节输入，不使用 source_color。
uniform sampler2D noise_texture : filter_linear, repeat_disable;
// 0 使用基础边带，1 完全使用噪声 R 调制的边带；不改变扫描边界。
uniform float noise_strength : hint_range(0.0, 1.0, 0.05) = 0.5;
// 边带沿 Y 的宽度，以 UV 高度比例计量，不是屏幕像素。
uniform float edge_width : hint_range(0.01, 1.0, 0.01) = 0.05;
// 基础边带的颜色混合强度，不控制原图 Alpha。
uniform float edge_strength : hint_range(0.0, 1.0, 0.01) = 1.0;

void fragment() {
	float progress = 0.0;
	// 原图提供 RGB 和 Alpha；噪声按原始 UV 采样，不随蓝色条纹滚动。
	vec4 origin = texture(TEXTURE, UV);
	vec4 noise = texture(noise_texture, UV);
	vec3 origin_color = origin.rgb;
	
	// sin 的 [-1,1] 映射为 [0,1]：TIME=0 从中间开始，随后往返，非单次传送。
	progress = (sin(TIME * PI * teleport_speed) + 1.0) / 2.0  ;
	// 以下为未启用的替代位置映射；当前实际边界仍直接使用 progress。
	//float scan_position = mix(-edge_width, 1.0 + edge_width * 2.0, progress);
	float alpha = origin.a;
	float light_end_progress = progress + edge_width;
	
	// 沿高度划分 8 个周期，fract 得到各周期内的 [0,1) 坐标。
	// 减去 TIME * 0.1，使可见条纹向下移动，速度为 0.1 UV/秒。
	float scan_local_y = fract((UV.y - TIME * 0.1) * 8.0);

	// 每格前25%取1，其余取0，作为蓝色混合权重
	float blue_zone_weight = 1.0 - step(0.25, scan_local_y);

	vec3 result_color = mix(origin_color , blue_bar,blue_zone_weight * scan_strength);
	
	// 扫描位置上方隐藏，下方保留原 Alpha；进度增大时向下消失，减小时反向显现。
	if (UV.y < progress){
		alpha = 0.0;
	}
	// smoothstep 在边带内由 0 升至 1，step 在末端之后归零。
	// 因而当前边带是起点柔和、末端硬切，不是两侧柔化。
	float light_weight = smoothstep(progress,light_end_progress,UV.y);
	float lignth_show_weight = step(UV.y,light_end_progress);
	// 基础边带权重；实际颜色由 edge_color 决定，不限定为白色。
	float plain_edge = light_weight * lignth_show_weight * edge_strength;
	// 噪声只调制边带混色强度，不扰动扫描位置，也不挖除 Alpha。
	float noisy_edge = plain_edge * noise.r;
	// 在两种效果之间过渡
	float edge_weight = mix(plain_edge, noisy_edge, noise_strength);
	vec3 mix_color = mix(result_color,edge_color, edge_weight);
	
	// RGB 为条纹和边带混色；Alpha 只来自原图与扫描显隐，透明背景不会被边带填满。
	COLOR = vec4(mix_color,alpha);
	
}
