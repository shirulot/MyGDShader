shader_type canvas_item;
uniform float angle_deg :hint_range(-180.0, 180.0, 1.0) = 0.0;
uniform float aspect_ratio  = 1.0;
uniform float zoom : hint_range(0.5, 2.0, 0.01) = 1.0;

void vertex() {
	// Called for every vertex the material is visible on.
}

void fragment() {
	vec2 center = vec2(0.5);
	vec4 originColor = texture(TEXTURE,UV);
	vec2 center_uv = UV - center;
	float angle_rad = radians(float(angle_deg));
	float c = cos(angle_rad);
	float s = sin(angle_rad);
	
	mat2 rotaion_mat = mat2(
		vec2(c,-s),
		vec2(s,c)
	);
	
	vec2 scalelUv = vec2(center_uv.x * aspect_ratio , center_uv.y);
	vec2 rotationUV = rotaion_mat * scalelUv ;
	  // 3. 旋转相对坐标，再移回纹理坐标系。
    vec2 newUV = vec2 (rotationUV.x /aspect_ratio,rotationUV.y) / zoom + center;
	if(newUV.x <0.0 || newUV.x > 1.0 || newUV.y > 1.0 || newUV.y<0.0){
		COLOR = vec4(vec3(0.0),originColor.a);
	}else{
		COLOR = texture(TEXTURE,newUV);
	}
	// Called for every pixel the material is visible on.
}

//void light() {
//	// Called for every pixel for every light affecting the CanvasItem.
//	// Uncomment to replace the default light processing function with this one.
//}
