shader_type canvas_item;

uniform float split_pixels :hint_range(0.0, 8.0, 1.0) = 2.0;
// 06.3 色散首步：同一画面位置的 R、G、B 分别从不同位置读取。
// 已连接 512×512 色块图；横向偏移目标为 2 个源纹理像素。
// 由你完成三处采样及 RGB 重组，Alpha 使用原 UV 读取的值。
void fragment() {
	// 起点先显示完整原图；通道错位采样由你实现。
	vec4 origin = texture(TEXTURE, UV);
	float sizeUv2 = TEXTURE_PIXEL_SIZE.x * split_pixels;
	vec4 right_texture = texture(TEXTURE,vec2(UV.r - sizeUv2,UV.y));
	vec4 left_texture = texture(TEXTURE,vec2(UV.r + sizeUv2,UV.y));
	COLOR = vec4(vec3(right_texture.r,origin.g,left_texture.b),origin.a);
	//COLOR = origin;
	
}
