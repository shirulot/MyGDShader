shader_type canvas_item;
render_mode unshaded;
// 固定炮座内壁：来源为新安装座母图的实心蓝灰面，仅在原炮管覆盖区内显示。
uniform sampler2D ownership : filter_nearest, repeat_disable;
uniform sampler2D socket_source : filter_nearest, repeat_disable;
uniform vec4 source_rect;
uniform vec4 target_rect;
void fragment(){
 vec2 local=UV/TEXTURE_PIXEL_SIZE;
 vec2 relative=clamp((local-target_rect.xy)/target_rect.zw,vec2(0.0),vec2(1.0));
 vec2 uv=(source_rect.xy+relative*source_rect.zw)/vec2(textureSize(socket_source,0));
 vec4 p=texture(socket_source,uv);
 float allowed=step(0.5,texture(TEXTURE,UV).a)*step(0.5,texture(ownership,UV).r);
 COLOR=vec4(p.rgb,step(0.5,p.a)*allowed);
}
