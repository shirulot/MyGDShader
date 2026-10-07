shader_type canvas_item;
uniform float split_weight : hint_range(0.0, 1.0, 0.1) = 0.5; 
uniform float split_start : hint_range(0.0, 1.0, 0.01) = 0.45; 
uniform float split_end : hint_range(0.0, 1.0, 0.01) = 0.55; 
void fragment() {
	// 默认显示灰度渐变，边缘控制由学习者编写。
	vec4 origin = texture(TEXTURE, UV);
	float light = (sin(TIME) + 1.0) / 2.0 *0.7 + 0.3;
	vec2 newUV = mod(UV * 4.0 , 1.0);
	float smooth_weight1 = smoothstep(0.2,split_start,newUV.x);
	float smooth_weight2 = 1.0 - smoothstep(split_end,0.8,newUV.x);
	
	COLOR = vec4(vec3(smooth_weight1 * smooth_weight2 * light),origin.a);
	
	
}
