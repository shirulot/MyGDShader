shader_type canvas_item;

// 复用既有圆 Mask；区域组合逻辑由学习者编写。
uniform sampler2D circle_mask : filter_linear, repeat_disable;
// 星形灰度图已接入材质；采样和组合逻辑由学习者编写。
uniform sampler2D star_mask : filter_linear, repeat_disable;
uniform float start : hint_range(0.0, 1.0, 0.01) = 0.4;
uniform float end : hint_range(0.0, 1.0, 0.01) = 0.6;

uniform float feather : hint_range(0.0, 1.0, 0.01) =  0.22;
uniform float radius : hint_range(0.0, 1.0, 0.01) =  0.25;

uniform float repeat_count : hint_range(1.0, 16.0, 1.0) = 4.0;
uniform float move_weight : hint_range(0.0, 1.0, 0.01) = 0.1;

void fragment() {
	// ColorRect 的默认采样起点显示白色矩形。
	vec2 center = vec2(0.5);
	vec4 origin = texture(TEXTURE, UV);
	float localX = mod((UV.x + TIME * move_weight) * repeat_count,1.0);
	vec2 newUV = vec2(localX,UV.y);
	float leftWeight = smoothstep(start - 0.1,start,localX);
	float rightWeight = 1.0 - smoothstep(end,end + 0.1,localX);
	vec4 newTexture = texture(circle_mask,UV);
	vec4 star = texture(star_mask,UV);
	//float weight = leftWeight * rightWeight * newTexture.r ;
	float scanWeight = leftWeight * rightWeight;
	float weight = clamp(scanWeight + newTexture.r ,0.0,1.0 );
	float weightF = 1.0 - smoothstep(feather,radius,distance(UV,center));
	//float maxWeight = max(weight, newTexture.r);
	//float maxWeight = min(weight, newTexture.r);
	//vec3 a = mix(vec3(weight),vec3(1.0),newTexture.r); 
	COLOR = vec4(vec3(star.r * weightF * scanWeight),origin.a);
}
