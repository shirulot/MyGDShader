shader_type canvas_item;
uniform float white_flash : hint_range(0.0, 1.0, 0.5);
// 受击颜色：默认白色，可在材质 Inspector 中选择。
uniform vec3 hit_color : source_color = vec3(1.0);

void vertex() {
	// Called for every vertex the material is visible on.
}

// Demo 002：可调颜色的受击变色效果。
// 学习内容：用 TEXTURE、UV 采样原始颜色，用 source_color 暴露颜色参数；
// 通过 white_flash 和 mix 控制原色向 hit_color 的混合强度，保留原始透明度。
// white_flash 为 0 时显示原色，为 1 时完全显示受击色；本脚本不包含自动闪烁计时。
void fragment() {
	vec4 tempColor = texture(TEXTURE, UV);
	vec3 outputColor = mix(tempColor.rgb,hit_color,white_flash);
	COLOR = vec4(outputColor,tempColor.a);
}
