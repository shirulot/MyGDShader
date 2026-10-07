"""Fixed native source ownership for six cutter walking directions."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parent
UNIT='enemy_cutter'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rect(x,y,w,h):return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
def part(name,polygon,pivot,sole,overlap=None):
    return dict(id=name,polygon=polygon,pivot=pivot,sole=sole,overlap_polygons=overlap or [],phase_offset=0 if name in ['front_left','rear_right'] else 4,z=-2)
# 所有坐标来自各方向的固定原图，不镜像生成非对称工具。
definitions={
 'down_left':[
  part('rear_right',[[0,0],[56,0],[56,67],[54,67],[54,71],[51,71],[51,77],[0,77]],[50,72],[48,77]),
  part('rear_left',[[80,0],[128,0],[128,84],[85,84],[85,82],[80,82]],[82,77],[87,84]),
  part('front_right',[[50,85],[56,85],[56,89],[57,89],[57,92],[55,94],[49,94],[49,89]],[54,87],[54,94]),
  part('front_left',[[83,84],[88,84],[88,87],[91,87],[91,96],[82,96],[82,91],[83,91]],[85,85],[86,96])],
 'left':[
  part('front_left',rect(52,89,15,15),[62,90],[57,104]),
  part('rear_left',rect(74,88,15,16),[76,89],[82,102])],
 'up_left':[
  part('rear_left',rect(44,89,15,15),[54,91],[50,104]),
  part('rear_right',rect(76,87,15,17),[79,90],[84,102]),
  part('front_right',[[73,67],[82,67],[86,71],[86,75],[82,75],[82,77],[78,77],[78,72],[73,72]],[79,72],None)],
 'up':[
  part('front_left',[[0,0],[52,0],[52,80],[51,80],[51,86],[46,86],[46,89],[43,89],[43,95],[0,95]],[49,80],[42,94]),
  part('front_right',[[76,0],[128,0],[128,95],[86,95],[86,89],[82,89],[82,86],[78,86],[78,80],[76,80]],[79,80],[87,94]),
  part('rear_left',[[43,89],[55,89],[55,97],[50,97],[50,104],[39,104],[39,96],[43,96]],[52,92],[44,104]),
  part('rear_right',[[78,89],[86,89],[86,96],[89,96],[89,104],[78,104],[78,98],[74,96],[74,91]],[77,92],[83,104])],
 'up_right':[
  part('front_left',[[0,0],[47,0],[47,70],[45,70],[45,80],[42,80],[42,83],[0,83]],[45,74],[40,83]),
  part('rear_left',rect(36,83,14,15),[45,87],[41,97]),
  part('rear_right',rect(62,87,16,17),[65,90],[70,104])],
 'right':[
  part('rear_right',rect(34,87,16,17),[45,90],[40,102]),
  part('front_right',rect(56,90,15,14),[60,91],[64,104])]
}
tools={
 'down_left':[[[34,81],[41,81],[41,78],[48,78],[48,77],[50,77],[50,80],[53,80],[53,85],[50,85],[50,88],[48,88],[48,98],[34,98]],[[72,85],[75,85],[75,82],[81,82],[81,86],[83,86],[83,90],[81,90],[81,94],[78,94],[78,104],[68,104],[68,97],[70,97],[70,91],[72,91]],rect(56,84,10,6)],
 'left':[[[32,84],[53,84],[53,83],[56,83],[56,91],[52,91],[52,93],[49,93],[49,99],[32,99]]],
 'up_left':[rect(32,75,24,14),[[83,73],[96,73],[96,90],[87,90],[87,88],[83,88],[83,86],[81,86],[81,76]]],
 'up':[],
 'up_right':[[[71,79],[81,79],[81,80],[97,80],[97,97],[80,97],[80,90],[75,90],[75,88],[71,88]],rect(71,63,14,16)],
 'right':[[[64,82],[78,82],[78,81],[95,81],[95,100],[74,100],[74,93],[69,93],[69,91],[64,91]]]
}
heading={'down_left':[-.7071,.7071],'left':[-1,0],'up_left':[-.7071,-.7071],'up':[0,-1],'up_right':[.7071,-.7071],'right':[1,0]}
configs={}
sockets={
 'down_left':{'rear_right':([53,69],[50,70]),'rear_left':([80,76],[84,76]),'front_right':([55,86],[53,90]),'front_left':([82,85],[85,88])},
 'left':{'front_left':([64,88],[62,92]),'rear_left':([76,87],[78,91])},
 'up_left':{'rear_left':([55,89],[52,93]),'rear_right':([79,86],[82,92]),'front_right':([77,72],[81,71])},
 'up':{'rear_left':([53,89],[49,93]),'rear_right':([76,89],[80,93]),'front_left':([51,81],[46,81]),'front_right':([77,81],[82,81])},
 'up_right':{'rear_left':([47,83],[44,87]),'rear_right':([64,87],[67,92]),'front_left':([46,74],[43,75])},
 'right':{'rear_right':([47,87],[44,92]),'front_right':([60,88],[62,92])}
}
def inside(p,poly):
    hit=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
for d,parts in definitions.items():
    image=Image.open(ROOT/'source'/f'{d}.png').convert('RGBA')
    for p in parts:
        owned=[(x,y) for y in range(128) for x in range(128) if image.getpixel((x,y))[3] and inside((x+.5,y+.5),p['polygon']) and not any(inside((x+.5,y+.5),q) for q in tools[d])]
        assert owned,p['id']
        p['opaque_source_pixels']=len(owned)
        start,end=sockets[d][p['id']]
        patches=[]
        for py in range(76,95):
            for px in range(42,84):
                pixels=[image.getpixel((px+dx,py+dy)) for dx in range(2) for dy in range(2)]
                if all(a==255 and b>=r and max(r,g,b)<120 and sum((r,g,b))>55 for r,g,b,a in pixels):patches.append(((px-start[0])**2+(py-start[1])**2,[px,py,2,2]))
        assert patches
        p['socket']=dict(start=start,end=end,width=2 if d=='up_right' and p['id']=='front_left' else 3,source_rect=min(patches)[1])
        # 只读取脚底边缘来注册接地点，不重采样或修改源图。
        if p['sole'] is not None:
            bottom=max(y for x,y in owned);xs=sorted(x for x,y in owned if y==bottom)
            p['sole']=[xs[len(xs)//2],bottom+1]
    configs[d]=dict(source=f'res://source/{d}.png',source_sha256=sha(ROOT/'source'/f'{d}.png'),parts=parts,heading=heading[d],protected_body_polygons=tools[d],hidden_legs=[k for k in ['front_left','front_right','rear_left','rear_right'] if k not in [p['id'] for p in parts]],occlusion_note='The far pair in W/E and far front leg in diagonals remain behind the chassis/tools. Hidden sole positions are not claimed as measured contact pixels.')
preserved=[]
for d,folder in [('down','enemy-sequences-v012'),('down_right','enemy-eight-directions-v013-pilot-hc-v001')]:
    name='move_'+d;src=ROOT.parent/folder/'output'/UNIT/name;dst=ROOT/'output'/UNIT/name
    shutil.copytree(src,dst,dirs_exist_ok=True);shutil.copy2(src.with_suffix('.png'),dst.with_suffix('.png'))
    preserved.append(dict(action=name,atlas_sha256=sha(dst.with_suffix('.png')),frame_hashes=[sha(dst/f'f{i:02}.png') for i in range(8)]))
directions=['down','down_left','left','up_left','up','up_right','right','down_right']
for d in directions:shutil.copy2(ROOT/'source'/f'{d}.png',ROOT/'output'/UNIT/f'neutral_{d}.png')
for name in ['move_down.png','neutral_down.png']:shutil.copy2(ROOT/'output'/UNIT/name,ROOT/'reference'/UNIT/name)
spec=dict(version='v022-cutter-six-moves',unit=UNIT,canvas=[128,128],root=[64,104],directions=directions,configs=configs,preserved=preserved,depth=[2,1,0,-1,-2,-1,0,1],lift=[0,0,0,0,0,1,2,1],body_y=[0,0,-1,0,0,0,-1,0])
(ROOT/'rig.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('CUTTER_SIX_DIRECTIONS_REGISTERED')
