"""Reuse reviewed v002 sampler; independently model only the two new controls.

Only SW/E 28 frames are reconstructed. Other directions retain byte bindings.
"""
from pathlib import Path
import types,json

B=Path(__file__).resolve().parent
old=B.parent/'enemy-heavy-v019-attack-death-v002/technical-audit.py'
text=old.read_text(encoding='utf-8')
text=text[:text.index("for clip in cat['clips']:")]
text=text.replace("if inside(x+.5,y+.5,cfg['gun']['polygon']): part='gun'",
                  "if [x,y] in cfg['gun'].get('fixed_receiver_pixels',[]): part='fixed'\n                if inside(x+.5,y+.5,cfg['gun']['polygon']): part='gun'")
text=text.replace("if poly and own[(x,y)]=='gun' and src.getpixel((x,y))[3]>=128:",
                  "clip=cfg['gun'].get('socket_clip_rect',[0,0,128,128])\n    if poly and own[(x,y)]=='gun' and src.getpixel((x,y))[3]>=128 and clip[0]<=q[0]<clip[0]+clip[2] and clip[1]<=q[1]<clip[1]+clip[3]:")
m=types.ModuleType('independent_delta');m.__file__=__file__
exec(compile(text,str(old),'exec'),m.__dict__)
out={'scope':'Only SW/E 28 incremental frames; rest bind reviewed v002 unchanged bytes','frames':[],'points':[]}
for c in m.cat['clips']:
    if c['direction'] not in ['down_left','right']:continue
    kind=c['action'].removesuffix('_'+c['direction']);model=m.models[c['direction']]
    for i in range(c['frame_count']):
        im=m.rgba(m.P/f'output/enemy_tracked_heavy/{c["action"]}/f{i:02d}.png');residual=[];hidden=socket=0;outside_socket=[]
        for y in range(128):
            for x in range(128):
                expected,owner=m.pixel_layer(model,kind,i,x,y);actual=im.getpixel((x,y))
                if expected!=actual:residual.append({'xy':[x,y],'cpu_rgba':expected,'actual_rgba':actual,'owner':owner})
                if owner and owner['part']=='hidden_mount':hidden+=1
                if owner and owner['part']=='socket':
                    socket+=1
                    if c['direction']=='right' and not (92<=x<=94 and 73<=y<=86):outside_socket.append([x,y])
        out['frames'].append({'action':c['action'],'frame':i,'cpu_residual_count':len(residual),'cpu_residual':residual,'cpu_alpha_residual':sum(r['cpu_rgba'][3]!=r['actual_rgba'][3] for r in residual),
                              'hidden_mount_visible_pixels':hidden,'socket_visible_pixels':socket,'outside_e_socket_root':outside_socket})
        points=[(46,76),(46,77),(46,89),(46,90)] if c['direction']=='down_left' else [(96,83),(96,84),(98,83),(98,84)]
        for xy in points:
            expected,owner=m.pixel_layer(model,kind,i,*xy);out['points'].append({'action':c['action'],'frame':i,'xy':xy,'actual_rgba':im.getpixel(xy),'cpu_rgba':expected,'owner':owner})
out['cpu_residual_total']=sum(r['cpu_residual_count'] for r in out['frames'])
out['cpu_alpha_residual_total']=sum(r['cpu_alpha_residual'] for r in out['frames'])
out['hidden_mount_visible_total']=sum(r['hidden_mount_visible_pixels'] for r in out['frames'])
out['e_socket_outside_root_total']=sum(len(r['outside_e_socket_root']) for r in out['frames'])
(B/'technical-two-direction-reconstruction.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ['frames','points']},indent=2))
