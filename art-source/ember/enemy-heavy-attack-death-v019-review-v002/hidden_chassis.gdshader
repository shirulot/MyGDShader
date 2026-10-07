shader_type canvas_item;
render_mode unshaded;
uniform sampler2D canonical_mask : filter_nearest, repeat_disable;
uniform float y_min=72.0;
varying vec2 source_position;
void vertex(){source_position=VERTEX;}
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 float allowed=step(y_min,source_position.y)*step(0.5,texture(canonical_mask,source_position/128.0).a);
 COLOR=vec4(p.rgb,step(0.5,p.a)*allowed);
}
