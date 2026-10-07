shader_type canvas_item;
uniform float wave_speed :hint_range(0.0, 6.3, 0.00001) = 3.14159;
uniform float wave_amplitude :hint_range(0.0, 0.02, 0.002) = 0.01;
uniform float wave_frequency :hint_range(1.0, 4.00, 0.1) = 2.00;

// 06.1 起点：TEXTURE 来自场景中 Sprite2D 绑定的 512×512 直线背景。
// 当前只做默认采样；静态单轴波纹由你在这个 fragment 中编写。
void fragment() {
	// 一次读取完整 RGBA，保留底图颜色与原 Alpha。
	vec4 origin = texture(TEXTURE, UV);
	vec2 newUV = UV;
	newUV.x = sin(newUV.y * wave_frequency * 2.0  * PI + wave_speed * TIME) * wave_amplitude + newUV.x;
	COLOR = texture(TEXTURE,newUV);
}
