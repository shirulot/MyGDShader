shader_type canvas_item;
render_mode unshaded;
uniform sampler2D ownership : filter_nearest, repeat_disable;
uniform vec4 sensor_rect;
uniform float sensor_power=1.0;
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 vec2 s=UV/TEXTURE_PIXEL_SIZE;
 if(s.x>=sensor_rect.x&&s.x<sensor_rect.x+sensor_rect.z&&s.y>=sensor_rect.y&&s.y<sensor_rect.y+sensor_rect.w){
  p.rgb=floor(p.rgb*mix(0.3,1.0,sensor_power)*255.0+0.5)/255.0;
 }
 COLOR=vec4(p.rgb,step(0.5,p.a)*step(0.5,texture(ownership,UV).r));
}
