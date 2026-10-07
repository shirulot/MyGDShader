shader_type canvas_item;
render_mode unshaded;
uniform sampler2D ownership : filter_nearest, repeat_disable;
uniform float phase=0.0;
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 vec2 q=floor(UV/TEXTURE_PIXEL_SIZE);
 // 固定源面的投影斜率；采样只在胎面内部，轮廓/护罩/轮轴不动。
 bool near_belt=q.x>=43.0&&q.x<55.0;
 bool far_belt=q.x>=90.0&&q.x<102.0;
 float top=near_belt?84.0-floor((q.x-43.0)*0.25):72.0-floor((q.x-90.0)*0.25);
 if((near_belt||far_belt)&&q.y>=top&&q.y<top+16.0){
  vec2 sample_point=vec2(q.x,top+mod(q.y-top-phase,16.0));
  p.rgb=texture(TEXTURE,(sample_point+vec2(0.5))*TEXTURE_PIXEL_SIZE).rgb;
 }
 COLOR=vec4(p.rgb,step(0.5,p.a)*step(0.5,texture(ownership,UV).r));
}
