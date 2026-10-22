shader_type canvas_item;

// 复用12.1已经学过的原样读屏；本场景不叠加12.2的CRT/Glitch。
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

// 当前只准备输入：点击传参、定位标记及后续折射环由你逐步实现。
uniform vec2 center_uv = vec2(0.5);
uniform vec4 marker_color : source_color = vec4(0.25, 0.75, 1.0, 1.0);

void fragment() {
	vec4 screen_color = texture(screen_texture, SCREEN_UV);
	COLOR = screen_color;
}
