shader_type canvas_item;
render_mode unshaded;
uniform float sensor_power=1.0;
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 vec2 s=UV/TEXTURE_PIXEL_SIZE;
 bool left=length((s-vec2(41.5,64.5))/vec2(6.5,4.5))<1.0;
 bool right=length((s-vec2(85.5,64.5))/vec2(6.5,4.5))<1.0;
 if(left||right){p.a=0.0;}
 if(s.x>=62.0&&s.x<66.0&&s.y>=66.0&&s.y<73.0){p.rgb=floor(p.rgb*mix(0.3,1.0,sensor_power)*255.0+0.5)/255.0;}
 COLOR=vec4(p.rgb,step(0.5,p.a));
}
