shader_type canvas_item;

// 第二张纹理由 ShaderMaterial 连接；它提供区域数据，不作为底图显示。
uniform sampler2D mask_texture : filter_linear, repeat_disable;

void fragment() {
	// 起点只显示底图，并保留它的 RGB 与 Alpha。
	vec4 origin = texture(TEXTURE, UV);
	vec4 mixResroce = texture(mask_texture,UV);
	//vec3 mixRgb = mix(origin.rgb,vec3(0.5),mixResroce.r);
	vec3 mixRgb = mix(origin.rgb,vec3(1.0),mixResroce.r);
	COLOR = vec4(mixRgb,origin.a);
}
