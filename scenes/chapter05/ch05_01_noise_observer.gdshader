shader_type canvas_item;
uniform float noise_scale :hint_range(0.5, 1.0, 0.01) ;
uniform float scale :hint_range(0.01, 2.0, 0.01) = 1.0;
uniform float contrast: hint_range(0.0, 2.0, 0.1) = 1.0;

void fragment() {
	// 当前只按原始 UV 显示 Sprite2D 的纹理，作为后续观察实验的起点。
	// 保留采样得到的 RGB 与 Alpha，不额外改变灰度或显隐。
	vec2 center = vec2(0.5);
	vec2 scaleUv = (UV - center) / scale + center;
	vec4 origin = texture(TEXTURE, scaleUv);
	float r = clamp((origin.r - 0.5) * contrast + 0.5,0.0,1.0);
	COLOR = vec4(vec3(r),origin.a);
	
}
