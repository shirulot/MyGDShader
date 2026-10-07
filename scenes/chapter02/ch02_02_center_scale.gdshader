shader_type canvas_item;
uniform float zoom : hint_range(0.5, 2.0, 0.1) = 1.0;

void vertex() {
	// Called for every vertex the material is visible on.
}

void fragment() {
	vec4 originColor = texture(TEXTURE,UV );
	vec2 newUV = (UV - vec2(0.5)) /zoom+ vec2(0.5);
	if(newUV.x >1.0 || newUV.x < 0.0 || newUV.y<0.0 || newUV.y>1.0){
		COLOR = vec4(vec3(0.0),originColor.a);
	}else{
		COLOR = texture(TEXTURE,newUV );
	}
	// Called for every pixel the material is visible on.
}

//void light() {
//	// Called for every pixel for every light affecting the CanvasItem.
//	// Uncomment to replace the default light processing function with this one.
//}
