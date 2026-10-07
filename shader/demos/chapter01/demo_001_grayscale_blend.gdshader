shader_type canvas_item;
uniform float gray_progress : hint_range(0.0, 1.0, 0.05);

void vertex() {
	// Called for every vertex the material is visible on.
}

// Demo 001：纹理采样与灰度混合。
// 学习内容：用 TEXTURE、UV 采样原始颜色；取 RGB 平均值生成灰度；
// 用 uniform 参数 gray_progress 和 mix 控制原色到灰度的过渡；
// 输出处理后的 RGB，同时保留原贴图的 alpha 透明度。
void fragment() {
	vec4 tempColor = texture(TEXTURE, UV);
	float gray =(tempColor.r + tempColor.g + tempColor.b)/3.0;
	vec3 outputColor = mix(tempColor.rgb,vec3(gray),gray_progress);
	COLOR = vec4(outputColor,tempColor.a);
}
