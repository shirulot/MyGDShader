shader_type canvas_item;

// 引擎将此前已绘制的屏幕内容提供给此输入；本步不需要额外图片。
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform float zoom : hint_range(1.0, 4.0, 0.1) = 2.0;
void fragment() {
	// 起点：普通默认采样。ColorRect 没有底图，因此现在是白色窗口。
	// 练习：替换这里的读取来源与坐标，再处理读到的 RGB。
	vec4 origin = texture(TEXTURE, UV);
	vec2 zoom_uv = (SCREEN_UV - vec2(0.5)) / zoom + vec2(0.5);
	vec4 mirro = texture(screen_texture, zoom_uv);
	float gray = (mirro.r + mirro.g + mirro.b) / 3.0;
	COLOR = vec4(vec3(gray),1.0);
}
