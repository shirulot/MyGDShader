shader_type canvas_item;
render_mode unshaded;
void fragment(){vec4 p=texture(TEXTURE,UV);COLOR=vec4(p.rgb,step(0.5,p.a));}
