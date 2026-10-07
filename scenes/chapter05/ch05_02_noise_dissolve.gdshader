shader_type canvas_item;

// 第二张纹理提供灰度数据；机器人底图仍由 Sprite2D 的 TEXTURE 提供。
// 当前只建立输入连接，阈值与显隐逻辑由你在下一步编写。
uniform sampler2D noise_texture : filter_linear, repeat_disable;
uniform float dissolve_progress : hint_range(0.0, 1.0, 0.01) = 0.0;
uniform float edge_width : hint_range(0.01, 0.2, 0.01) = 0.05;
uniform vec3 line_color = vec3(1.0, 0.55, 0.1);
void fragment() {
	// 起点显示完整机器人，并保留底图的 RGB 和 Alpha。
	vec4 origin = texture(TEXTURE, UV);
	vec4 noise = texture(noise_texture,UV);
	float weight = step(dissolve_progress,noise.r);
	float smoothWeight = smoothstep(dissolve_progress,dissolve_progress+edge_width,noise.r);
	if(dissolve_progress >= 1.0){
		weight = 0.0;
	}
	if(weight == 0.0){
		discard;
	}
	if(weight - smoothWeight > 0.0 && dissolve_progress > 0.0){
		vec3 last_line_color = mix(line_color,origin.rgb,smoothWeight);
		COLOR = vec4(last_line_color,origin.a);
	}else{
		COLOR = origin;
	}
}
