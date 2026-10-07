shader_type canvas_item;

// 06.1 起点：TEXTURE 来自场景中 Sprite2D 绑定的 512×512 直线背景。
// 当前只做默认采样；静态单轴波纹由你在这个 fragment 中编写。
void fragment() {
	// 一次读取完整 RGBA，保留底图颜色与原 Alpha。
	COLOR = texture(TEXTURE, UV);
}
