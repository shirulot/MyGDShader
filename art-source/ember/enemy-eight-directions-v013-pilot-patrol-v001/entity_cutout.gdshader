shader_type canvas_item;
render_mode unshaded;
// 与已通过实体一致的显式覆盖规则，原始生成PNG另存不修改。
void fragment(){vec4 p=texture(TEXTURE,UV);COLOR=vec4(p.rgb,step(0.5,p.a));}
