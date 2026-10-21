shader_type canvas_item;

// 保留已学的瞬时受击接口；旧 main.gdshader 不修改。
uniform float white_flash : hint_range(0.0, 1.0, 0.5);
uniform vec3 hit_color : source_color = vec3(1.0);
uniform vec3 low_hp_color : source_color = vec3(1, 0.35, 0.15);
uniform float danger_progress : hint_range(0.0, 1.0, 0.01) = 0.0;
// TODO：新增独立的 danger_progress（float，0～1，初值0）和 low_hp_color（vec3）。
// 低血输入颜色使用 RGB(1.0, 0.35, 0.15)，持续混色由你实现。
uniform sampler2D noise  ;
uniform float dissolve_progress : hint_range(0.0, 1.0, 0.01) = 1.0;

void fragment() {
	vec4 tempColor = texture(TEXTURE, UV);
	vec4 noiseColor = texture(noise, UV);
	// 先算持续色偏，再把该 RGB 作为下面受击混色的底色。
	vec3 damege_color = mix(tempColor.rgb , low_hp_color,danger_progress);
	vec3 outputColor = mix(damege_color, hit_color, white_flash);
	float noiseAlpha =  tempColor.a * step(noiseColor.r , dissolve_progress);
	if(dissolve_progress == 0.0) noiseAlpha = 0.0;
	COLOR = vec4(outputColor, noiseAlpha );
	
}
