shader_type canvas_item;
// 完整母图始终只有一个几何载体。仅在已登记的活动区域内改变像素取样，
// 屋顶、檐口、柱、墙与所有转角不受门状态影响，避免拆件形成第二圈倒角。
uniform vec4 personnel_rect = vec4(0.0);
uniform vec4 cargo_rect = vec4(0.0);
uniform float personnel_progress = 0.0;
uniform float cargo_progress = 0.0;
uniform float personnel_chamfer = 0.0;
uniform vec4 service_rect = vec4(0.0);
uniform vec4 hatch_rect = vec4(0.0);
uniform bool service_open = false;
uniform bool hatch_open = false;
uniform vec4 lens_rects[6];
uniform int lens_count = 0;
uniform vec4 glass_rects[6];
uniform int glass_count = 0;
uniform bool powered = true;
uniform bool faulted = false;
uniform bool locked = false;
uniform bool moving = false;
uniform bool device_enabled = true;
uniform bool glass_lit = false;
uniform float state_clock = 0.0;
varying vec4 node_tint;

void vertex() {
	// fragment 的内置 COLOR 已含纹理；单独传递节点调色，避免重复乘纹理。
	node_tint = COLOR;
}

bool in_rect(vec2 p, vec4 r) {
	return r.z > 0.0 && r.w > 0.0 && p.x >= r.x && p.y >= r.y && p.x < r.x + r.z && p.y < r.y + r.w;
}

bool in_aperture(vec2 p, vec4 r, float bevel) {
	vec2 q = p - r.xy;
	return in_rect(p, r) && q.x + q.y >= bevel && r.z - q.x + q.y >= bevel;
}

vec4 move_leaf(sampler2D source_texture, vec4 original, vec2 p, vec4 r, float bevel, float progress, vec2 texel) {
	// 完全关闭时直接返回母图，绝不二次叠加Alpha或给门框描边。
	if (progress <= 0.0 || !in_aperture(p, r, bevel)) { return original; }
	float lift = floor(progress * r.w + 0.5);
	vec2 source = p + vec2(0.0, lift);
	if (source.y < r.y + r.w) { return texture(source_texture, source * texel); }
	// 看不到内部的深暗门洞。没有把暗色洞口伪称为完整室内资产。
	return vec4(0.055, 0.089, 0.109, original.a);
}

void fragment() {
	vec4 tint = node_tint;
	vec2 p = UV / TEXTURE_PIXEL_SIZE;
	vec4 value = texture(TEXTURE, UV);
	value = move_leaf(TEXTURE, value, p, personnel_rect, personnel_chamfer, personnel_progress, TEXTURE_PIXEL_SIZE);
	value = move_leaf(TEXTURE, value, p, cargo_rect, 0.0, cargo_progress, TEXTURE_PIXEL_SIZE);
	if ((service_open && in_rect(p, service_rect)) || (hatch_open && in_rect(p, hatch_rect))) {
		value.rgb = vec3(0.055, 0.089, 0.109);
	}
	for (int i = 0; i < 6; i++) {
		if (i < glass_count && glass_lit && powered && in_rect(p, glass_rects[i])) {
			value.rgb = min(value.rgb * vec3(1.22, 1.24, 1.20), vec3(1.0));
		}
		if (i < lens_count && in_rect(p, lens_rects[i])) {
			// 默认状态仍保留原稿灯色。状态只改变灯面，不影响外壳和转角。
			if (!powered) { value.rgb *= 0.2; }
			else if (faulted) {
				value.rgb = mod(state_clock, 0.7) < 0.35 ? vec3(0.76, 0.28, 0.14) : value.rgb * 0.12;
			} else if (locked || !device_enabled) { value.rgb *= vec3(0.88, 0.57, 0.23); }
			else if (moving && mod(state_clock, 0.32) >= 0.24) { value.rgb *= 0.25; }
		}
	}
	COLOR = value * tint;
}
