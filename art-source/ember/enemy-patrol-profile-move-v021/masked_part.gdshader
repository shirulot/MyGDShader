shader_type canvas_item;
render_mode unshaded;
// ownership 只登记固定源像素属于哪个刚体，RGB 仍来自原母图。
uniform sampler2D ownership : filter_nearest, repeat_disable;
void fragment(){
 vec4 p=texture(TEXTURE,UV);
 COLOR=vec4(p.rgb,step(0.5,p.a)*step(0.5,texture(ownership,UV).r));
}
