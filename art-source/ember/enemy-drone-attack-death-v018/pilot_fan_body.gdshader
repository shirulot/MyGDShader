shader_type canvas_item;
render_mode unshaded;
uniform vec2 fan_a_center;
uniform vec2 fan_a_radius;
uniform vec2 fan_b_center;
uniform vec2 fan_b_radius;
uniform vec4 sensor_rect;
uniform float sensor_power=1.0;
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 vec2 s=UV/TEXTURE_PIXEL_SIZE;
 if(length((s-fan_a_center)/fan_a_radius)<1.0||length((s-fan_b_center)/fan_b_radius)<1.0){p.a=0.0;}
 // Only the registered visible red sensor dims; brass hubs and rear vents remain unchanged.
 if(s.x>=sensor_rect.x&&s.x<sensor_rect.x+sensor_rect.z&&s.y>=sensor_rect.y&&s.y<sensor_rect.y+sensor_rect.w){
  p.rgb=floor(p.rgb*mix(0.3,1.0,sensor_power)*255.0+0.5)/255.0;
 }
 COLOR=vec4(p.rgb,step(0.5,p.a));
}
