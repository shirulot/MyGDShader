shader_type canvas_item;

// 颜色与参数是练习输入；圆形权重、环形组合和输出由你实现。
uniform vec3 shield_color : source_color = vec3(0.25, 0.75, 1.0);
uniform float outer_radius : hint_range(0.15, 0.48, 0.01) = 0.4;
uniform float ring_width : hint_range(0.03, 0.12, 0.005) = 0.06;
uniform float edge_softness : hint_range(0.001, 0.02, 0.001) = 0.01;

void fragment() {
	// ColorRect 默认采样显示白色方块，后续用环形权重控制其透明度。
	COLOR = texture(TEXTURE, UV);
}
