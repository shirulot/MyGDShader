shader_type canvas_item;

void fragment() {
	// 默认起点：两个独立材质共用这个 Shader，各自采样相同的底图。
	// 全局参数声明与危险染色逻辑由你在本节逐步添加。
	COLOR = texture(TEXTURE, UV);
}
