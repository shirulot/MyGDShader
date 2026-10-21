shader_type canvas_item;

uniform vec3 background_color : source_color = vec3(0.102745, 0.135686, 0.166667);
uniform vec3 grid_color : source_color = vec3(0.2, 0.611765, 1.0);
uniform vec3 scan_color : source_color = vec3(0.185412, 0.540353, 0.875);
uniform vec3 ring_color : source_color = vec3(0.165961, 0.445137, 0.708333);

uniform float radius : hint_range(0.01, 0.5, 0.01) = 0.4;
uniform float grid_width : hint_range(0.001, 0.1, 0.001) = 0.004;
uniform float ring_width : hint_range(0.01, 0.1, 0.01) = 0.01;
uniform float ring_edge : hint_range(0.0001, 0.0025, 0.0001) = 0.0025;
uniform float scan_width : hint_range(0.01, 0.3, 0.01) = 0.1;
uniform float scan_edge : hint_range(0.0001, 0.1, 0.0001) = 0.05;

uniform float grid_alpha : hint_range(0.01, 1.0, 0.01) = 0.2;
uniform float grid_count: hint_range(0.0, 40.0, 1.0) = 20.0;

uniform float scan_speed : hint_range(0.01, 1.0, 0.01) = 0.4;

// 圆环权重
float get_ring_weight(float uv_length){
	 float ring_inner_start = radius - ring_width;
	 float ring_inner_end = ring_inner_start + ring_edge;
	 float ring_inner_zone = smoothstep(ring_inner_start,ring_inner_end,uv_length);
	
	 float ring_outer_start = radius - ring_edge ;
	 float ring_outer_end = radius;
	 float ring_outer_zone = 1.0 - smoothstep(ring_outer_start,ring_outer_end,uv_length);
	return ring_inner_zone * ring_outer_zone;
}
// 09.1：独立扫描窗口实验。场景已连接本 Shader，效果逻辑由学习者编写。
// 当前只保留默认采样；ColorRect 未绑定外部图片，起点显示为白色方块。
void fragment() {
	float progress = 0.5;
	vec2 center = vec2(0.5,0.5);
	vec4 origin = texture(TEXTURE, UV);
	float uv_length = length(UV - center);
	// 背景
	float backgroup_weight = step(uv_length , radius);
	float grid_weight = step(uv_length + ring_width, radius);
	vec3 backgroup = mix(origin.rbg,background_color,backgroup_weight);
	// 圆环
	float ring_weight = get_ring_weight(uv_length);
	vec3 ring = mix(backgroup,ring_color,ring_weight);
	
	//网格
	vec2 newUV = fract(UV * grid_count);
	float grid_x = step(newUV.x,grid_width * grid_count);
	float grid_y = step(newUV.y,grid_width * grid_count);
	vec3 grid = mix(ring,grid_color,max(grid_x,grid_y) * grid_alpha * grid_weight);
	
	progress = fract(TIME * scan_speed);
	// 扫描线
	float scan_top_start = progress - scan_width;
	float scan_top_end = scan_top_start + scan_edge;
	float scan_top_weight = smoothstep(scan_top_start,scan_top_end,UV.y);
	
	float scan_bottom_start = progress - scan_edge;
	float scan_bottom_end = progress;
	float scan_bottom_weight = 1.0 - smoothstep(scan_bottom_start,scan_bottom_end,UV.y);
	
	float scan_weight = scan_top_weight * scan_bottom_weight;
	
	vec3 scan = mix(grid,scan_color,scan_weight);
	
	
	COLOR = vec4(scan,backgroup_weight);
}
