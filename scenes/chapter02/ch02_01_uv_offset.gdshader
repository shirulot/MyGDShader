shader_type canvas_item;
uniform float offset_x : hint_range(-0.25, 0.25, 0.01) = 0;
uniform float offset_y : hint_range(-0.25, 0.25, 0.01) = 0;

void vertex() {
	// Called for every vertex the material is visible on.
}

void fragment() {
	vec4 originColor = texture(TEXTURE,UV);
	vec2 newUV = vec2(UV.x+offset_x,UV.y+offset_y);
	if(newUV.x > 1.0 ||newUV.x<0.0 || newUV.y>1.0 ||newUV.y<0.0){
		COLOR = vec4(vec3(0),originColor.a);		
	}else{
		COLOR = texture(TEXTURE,newUV);
	}
	
}

//void light() {
//	// Called for every pixel for every light affecting the CanvasItem.
//	// Uncomment to replace the default light processing function with this one.
//}
