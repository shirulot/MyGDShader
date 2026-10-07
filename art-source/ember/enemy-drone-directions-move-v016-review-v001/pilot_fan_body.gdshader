shader_type canvas_item;
render_mode unshaded;
// Fan openings follow the reviewed direction registration, not the obsolete draft.
uniform vec2 fan_a_center;
uniform vec2 fan_a_radius;
uniform vec2 fan_b_center;
uniform vec2 fan_b_radius;
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 vec2 q=UV/TEXTURE_PIXEL_SIZE;
 bool near_fan=length((q-fan_a_center)/fan_a_radius)<1.0;
 bool far_fan=length((q-fan_b_center)/fan_b_radius)<1.0;
 COLOR=vec4(p.rgb,step(0.5,p.a)*float(!(near_fan||far_fan)));
}
