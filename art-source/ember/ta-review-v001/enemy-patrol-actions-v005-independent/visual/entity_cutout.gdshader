shader_type canvas_item;
render_mode unshaded;

// 游戏实体采用硬边覆盖；光效仍应使用独立的连续 Alpha 图层。
// 原PNG不改动，此材质只规定渲染覆盖率，不能代替像素美术精修。
uniform float coverage_cutoff : hint_range(0.0, 1.0) = 0.5;

void fragment() {
	vec4 pixel_sample = texture(TEXTURE, UV);
	COLOR = vec4(pixel_sample.rgb, step(coverage_cutoff, pixel_sample.a));
}
