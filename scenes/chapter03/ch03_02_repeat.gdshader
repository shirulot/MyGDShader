shader_type canvas_item;
uniform float repeat_count : hint_range(1.0, 16.0, 1.0) = 4.0;
uniform float move_weight : hint_range(0.0, 1.0, 0.01) = 0.1;

void fragment() {
	// 默认采样起点，重复图案由学习者编写。
	vec4 origin = texture(TEXTURE, UV);
	//float localX = fract(UV.x * repeat_count);
	float localX = mod((UV.x + move_weight * TIME) * repeat_count,1.0);
	if(localX >0.9){
		COLOR = vec4(vec3(1.0),origin.a); 
	}else{
		COLOR = vec4(vec3(0.0),origin.a); 	
	}
}
