shader_type canvas_item;
render_mode unshaded;
uniform bool canonical_source = true;
uniform float sensor_power=1.0;
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 vec2 s=floor(UV/TEXTURE_PIXEL_SIZE);
 if(canonical_source){
  bool old_front_foot=((s.x>=51.0&&s.x<55.0)||(s.x>=73.0&&s.x<77.0))&&s.y>=89.0&&s.y<95.0;
  if(old_front_foot){p.a=0.0;}
  if(s.x>=60.0&&s.x<68.0&&s.y>=82.0&&s.y<85.0){p.rgb=floor(p.rgb*mix(0.3,1.0,sensor_power)*255.0+0.5)/255.0;}
 }
 COLOR=vec4(p.rgb,step(0.5,p.a));
}
