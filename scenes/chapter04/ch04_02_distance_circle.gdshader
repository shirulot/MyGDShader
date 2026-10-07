shader_type canvas_item;
uniform float radius : hint_range(0.0, 1.0, 0.01) = 0.25;
uniform float feather : hint_range(0.0, 1.0, 0.01) = 0.3;

void fragment() {
	vec2 center = vec2(0.5);
	// ColorRect 没有指定图片；默认采样起点显示白色矩形。
	// 当前位置到中心的距离、圆形范围由学习者编写。
	vec4 origin = texture(TEXTURE, UV);
	//float lenght = distance(UV,center);
	float lenght = length(UV - center);
	float q = 1.0 - smoothstep(feather,radius,lenght);
	COLOR = vec4(vec3(q),q);
}
