shader_type canvas_item;
render_mode unshaded;
varying vec2 local_position;
void vertex(){local_position=VERTEX;}
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 COLOR=vec4(p.rgb,step(0.5,p.a)*step(length(local_position),6.5));
}
