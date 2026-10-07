shader_type canvas_item;
render_mode unshaded;
uniform sampler2D canonical_mask : filter_nearest;
varying vec2 native_point;
void vertex(){ native_point=VERTEX; }
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 float mask=texture(canonical_mask,native_point/vec2(128.0)).a;
 COLOR=vec4(p.rgb,step(0.5,p.a)*step(0.5,mask));
}
