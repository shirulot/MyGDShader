shader_type canvas_item;
render_mode unshaded;

// 游戏实体采用硬边覆盖；光效仍应使用独立的连续 Alpha 图层。
// 原PNG不改动，此材质只规定渲染覆盖率，不能代替像素美术精修。
uniform float coverage_cutoff : hint_range(0.0, 1.0) = 0.5;
uniform float tread_phase_px = 0.0;
uniform float sensor_power = 1.0;

void fragment() {
	vec4 pixel_sample = texture(TEXTURE, UV);
	vec2 source_pixel = floor(UV / TEXTURE_PIXEL_SIZE);
	bool in_left = source_pixel.x >= 30.0 && source_pixel.x < 42.0;
	bool in_right = source_pixel.x >= 86.0 && source_pixel.x < 98.0;
	if ((in_left || in_right) && source_pixel.y >= 86.0 && source_pixel.y < 102.0) {
		// 同一16px原履带窗口循环，外侧胶边与白色护板均保持原采样。
		vec2 tread_pixel = vec2(source_pixel.x, 86.0 + mod(source_pixel.y - 86.0 - tread_phase_px, 16.0));
		pixel_sample.rgb = texture(TEXTURE, (tread_pixel + vec2(0.5)) * TEXTURE_PIXEL_SIZE).rgb;
	}
	if (source_pixel.x >= 60.0 && source_pixel.x < 69.0 && source_pixel.y >= 69.0 && source_pixel.y < 72.0) { pixel_sample.rgb = floor(pixel_sample.rgb * mix(0.30, 1.0, sensor_power) * 255.0 + 0.5) / 255.0; }
	COLOR = vec4(pixel_sample.rgb, step(coverage_cutoff, pixel_sample.a));
}


