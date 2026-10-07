shader_type canvas_item;
render_mode unshaded;

// 游戏实体采用硬边覆盖；光效仍应使用独立的连续 Alpha 图层。
// 原PNG不改动，此材质只规定渲染覆盖率，不能代替像素美术精修。
uniform float coverage_cutoff : hint_range(0.0, 1.0) = 0.5;
// 母稿已有的六个传感器像素仅作为断电状态变暗，纹理源不变。
uniform float sensor_power : hint_range(0.0, 1.0) = 1.0;

void fragment() {
	vec4 pixel_sample = texture(TEXTURE, UV);
	vec2 source_pixel = floor(UV / TEXTURE_PIXEL_SIZE);
	if (source_pixel.x >= 64.0 && source_pixel.x < 67.0 && source_pixel.y >= 62.0 && source_pixel.y < 64.0) {
		pixel_sample.rgb *= mix(0.35, 1.0, sensor_power);
		// 明确量化到导出8位色阶，避免透明/不透明Viewport在小数色值上相差1级。
		pixel_sample.rgb = floor(pixel_sample.rgb * 255.0 + 0.5) / 255.0;
	}
	COLOR = vec4(pixel_sample.rgb, step(coverage_cutoff, pixel_sample.a));
}
