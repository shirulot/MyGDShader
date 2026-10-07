shader_type canvas_item;
render_mode unshaded;
uniform vec4 source_rect;
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 vec2 s=UV/TEXTURE_PIXEL_SIZE;
 bool inside=s.x>=source_rect.x&&s.x<source_rect.x+source_rect.z&&s.y>=source_rect.y&&s.y<source_rect.y+source_rect.w;
 COLOR=vec4(p.rgb,inside?step(0.5,p.a):0.0);
}
