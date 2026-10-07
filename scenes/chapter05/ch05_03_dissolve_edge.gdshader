shader_type canvas_item;

// 复用你在 05.2 完成的输入与显隐逻辑；05.3 的边带由你继续编写。
// noise_texture 提供灰度数据，TEXTURE 仍提供机器人原图。
uniform sampler2D noise_texture : filter_linear, repeat_disable;
uniform float dissolve_progress : hint_range(0.0, 1.0, 0.01) = 0.0;

void fragment() {
	vec4 origin = texture(TEXTURE, UV);
	vec4 noise = texture(noise_texture, UV);
	float weight = step(dissolve_progress, noise.r);

	// 保留全隐端点，避免灰度恰好为 1 时仍留下像素。
	if (dissolve_progress >= 1.0) {
		weight = 0.0;
	}
	if (weight == 0.0) {
		discard;
	}

	// 当前仍显示留下来的机器人；下一步只改变这些片元的 RGB。
	COLOR = origin;
}
