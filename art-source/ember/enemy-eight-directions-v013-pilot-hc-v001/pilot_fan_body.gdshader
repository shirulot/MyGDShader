shader_type canvas_item;
render_mode unshaded;
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 vec2 q=UV/TEXTURE_PIXEL_SIZE;
 bool near_fan=length((q-vec2(44.0,67.5))/vec2(6.0,4.0))<1.0;
 bool far_fan=length((q-vec2(76.0,60.5))/vec2(5.75,4.0))<1.0;
 COLOR=vec4(p.rgb,step(0.5,p.a)*float(!(near_fan||far_fan)));
}
