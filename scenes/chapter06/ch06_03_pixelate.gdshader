shader_type canvas_item;

uniform float cell : hint_range(8.0, 64.0, 2.0) = 16.0;
// 06.3 首步：512×256 的底图按 16 列、8 行分格，每格为 32×32 源纹理像素。
// 同一格内的像素应统一读取该格中心；分格与采样坐标由你实现。
// 本步先做静态像素化，输出底图的完整 RGBA。
void fragment() {
	vec2 image_size = vec2(1.0) / TEXTURE_PIXEL_SIZE;
	float row = cell * image_size.y / image_size.x ;
	vec2 sell_count = vec2(cell, row);
	vec2 sell_uv = floor(sell_count * UV);
	vec2 sell_center_uv = sell_uv + vec2(0.5);
	vec2 base_sell_uv = sell_center_uv / sell_count;
	// 起点仍显示原图，下一步将 UV 替换为自己算出的分格采样坐标。
	COLOR = texture(TEXTURE, base_sell_uv);
}
