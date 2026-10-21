shader_type canvas_item;

// 08.2：正方形 ColorRect 上的柔边圆环，滚动能量纹理只调节环内颜色。
// 护盾独立于机器人纹理；当前未接入游戏保护判定。
uniform vec3 shield_color : source_color = vec3(0.25, 0.75, 1.0);
// 半径为 UV 单位；当前 512×512 画布上，0.4 对应 204.8 个画布像素。
// 使用未经宽高比校正的 UV 距离；非正方形画布会将圆拉伸成椭圆。
uniform float outer_radius : hint_range(0.15, 0.48, 0.01) = 0.4;
// 内半径 = 外半径 - 环宽，单位同样是 UV。
uniform float ring_width : hint_range(0.03, 0.12, 0.005) = 0.06;
// 内、外边缘各自的渐变宽度；当前参数范围下，两段渐变之间仍有平台区。
uniform float edge_softness : hint_range(0.001, 0.02, 0.001) = 0.01;
// 圆环 Alpha 的上限，不是外半径；场景材质可以覆盖此处默认值。
uniform float outer_radius_alpha : hint_range(0.0, 1.0, 0.01) = 0.5;
// 竖直灰度能量条纹：读取.r作为颜色混合权重，越界后循环采样。
uniform sampler2D energy_texture : filter_linear, repeat_enable;
uniform vec3 energy_color : source_color = vec3(0.65, 0.95, 1.0);
// 每秒滚动的 UV 距离；当前采样坐标减去时间，可见纹理向右移动。
uniform float flow_speed : hint_range(0.0, 0.5, 0.01) = 0.1;
// 纹理 R 通道乘以此值，作为两种颜色的混合权重，不控制 Alpha。
uniform float energy_strength : hint_range(0.0, 1.0, 0.05) = 0.6;
// 受击预览输入：位置使用 ShieldCanvas 的本地UV，不是场景坐标。
uniform vec2 hit_uv = vec2(0.87, 0.5);
uniform float hit_radius : hint_range(0.01, 0.3, 0.005) = 0.12;
uniform vec3 hit_color : source_color = vec3(1.0, 0.85, 0.55);
uniform float hit_strength : hint_range(0.0, 1.0, 0.05) = 1.0;



void fragment() {
	// 保留的原图采样目前没有参与输出；护盾颜色和 Alpha 均由下方逻辑生成。
	vec4 origin = texture(TEXTURE, UV);
	
	// 只滚动能量纹理坐标，repeat_enable 使越界采样重复；圆环仍使用原始 UV。
	vec2 newUV = vec2(UV.x - TIME * flow_speed,UV.y);
	vec4 energy = texture(energy_texture, newUV);
	// 把 UV 中心移到原点，再用 length 计算当前片元到圆心的距离。
	vec2 center_point = vec2(0.5,0.5);
	vec2 UV_center = UV - center_point;
	float UV_lenght = length(UV_center);
	
	// 外圆边界及其外部直接输出透明；内部再计算空心环。
	if(UV_lenght < outer_radius){
		float inner_radius = outer_radius - ring_width;
		// 小于内半径时为 0，从内半径开始为 1，用于挖空中心。
		float is_outer = step(inner_radius,UV_lenght);
		// 内缘由透明渐入；外缘在到达外半径前渐出到透明。
		float inner_weight = smoothstep(inner_radius,inner_radius+edge_softness ,UV_lenght);
		float outer_weight = 1.0 - smoothstep(outer_radius - edge_softness,outer_radius ,UV_lenght);
		// 相乘表示同时满足内外边界，再乘整体 Alpha 上限。
		float aplha_weight = outer_radius_alpha * is_outer * inner_weight * outer_weight;
		// 灰度越亮，颜色越接近 energy_color；不会扩大圆环或改变其透明度。
		vec3 mix_color = mix(shield_color,energy_color,energy.r * energy_strength);
		
		float uv_hit_lenght = length(UV - hit_uv);
		
		float hit_weight = 1.0 - smoothstep(0.0,hit_radius,uv_hit_lenght);
		
		vec3 result_color = mix(mix_color,hit_color,hit_weight * hit_strength);
		
		COLOR = vec4(result_color, aplha_weight );
	} else {
		COLOR = vec4(0.0);
	}
}
