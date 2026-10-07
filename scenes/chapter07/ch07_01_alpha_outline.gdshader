shader_type canvas_item;

// 07.1 起点：只读取原图，Alpha 观察和描边逻辑由学习者逐步添加。
void fragment() {
	// 沿用原始 UV，读回完整 RGBA；当前没有邻域偏移。
	vec4 tex_color = texture(TEXTURE, UV);
	COLOR = vec4(vec3(tex_color.a),1.0);
	//COLOR = tex_color;
}
