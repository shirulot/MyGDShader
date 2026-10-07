shader_type canvas_item;
render_mode unshaded;
uniform sampler2D ownership : filter_nearest, repeat_disable;
uniform int window_count=0;
// xy=origin; z=cross-axis span; w=period. Parameters: shear, sign, horizontal, thickness.
uniform vec4 windows[4];
uniform vec4 parameters[4];
uniform float phase=0.0;
void fragment(){
 vec4 source=texture(TEXTURE,UV);
 vec2 q=floor(UV/TEXTURE_PIXEL_SIZE);
 for(int index=0;index<4;index++){
  if(index>=window_count)break;
  vec4 w=windows[index];vec4 p=parameters[index];
  vec2 sample_point=q;bool inside=false;
  if(p.z>0.5){
   inside=q.x>=w.x&&q.x<w.x+w.w&&q.y>=w.y&&q.y<w.y+p.w;
   sample_point.x=w.x+mod(q.x-w.x-phase*p.y,w.w);
  }else{
   float top=w.y+floor((q.x-w.x)*p.x);
   inside=q.x>=w.x&&q.x<w.x+w.z&&q.y>=top&&q.y<top+w.w;
   sample_point.y=top+mod(q.y-top-phase*p.y,w.w);
  }
  if(inside)source.rgb=texture(TEXTURE,(sample_point+vec2(0.5))*TEXTURE_PIXEL_SIZE).rgb;
 }
 COLOR=vec4(source.rgb,step(0.5,source.a)*step(0.5,texture(ownership,UV).r));
}
