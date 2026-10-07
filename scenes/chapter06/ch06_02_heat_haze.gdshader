shader_type canvas_item;

// 06.2 的灰度输入已由场景材质绑定；它提供 0～1 数据，读取 .r。
// filter_linear 是纹理插值；这里不使用 source_color，避免把数据当颜色转换。
// Noise 读取坐标随 TIME 移动，repeat_enable 让周期 Noise 越界后循环读取。
uniform sampler2D noise_texture : filter_linear, repeat_enable;
// 已连接固定圆形范围图；由你在原 UV 读取 .r，控制已有位移的作用范围。
uniform sampler2D region_mask : filter_linear, repeat_disable;
uniform float noise_speed : hint_range(0.0, 0.2, 0.01) = 0.05;

void fragment() {
	// 保留已完成的动画 Noise 偏移；下一步将固定范围权重作用于位移量。
	// TEXTURE 提供完整底图 RGBA，Noise 和 Mask 提供控制位移的数据。
	//vec4 origin = texture(TEXTURE, UV);
	vec2 noiseUV = vec2(UV.x,UV.y + noise_speed * TIME );
	vec4 noise = texture(noise_texture, noiseUV);
	vec4 mask = texture(region_mask,UV);
	float noise_r = (noise.r - 0.5) * 2.0;
	float noise_uv_x = UV.x + noise_r * 0.01;
	//float mask_uv_x = UV.x + noise_r * mask.r * 0.01;
	COLOR = texture(TEXTURE,vec2(noise_uv_x,UV.y));
}
