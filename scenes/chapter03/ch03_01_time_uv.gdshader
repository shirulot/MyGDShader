shader_type canvas_item;
uniform float horizontal_move :hint_range(0.0, 0.25, 0.01);

void fragment() {
	vec4 originColor = texture(TEXTURE, UV);
	float moveX = TIME * horizontal_move;
	vec2 newUV = vec2(UV.x + moveX,UV.y);
	if(newUV.x > 1.0 || newUV.x<0.0){
		COLOR = vec4(vec3(0.0),1.0);
	}else{
		COLOR = texture(TEXTURE,newUV);
	}
}
