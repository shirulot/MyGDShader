"""Produce fixed gun/mount crops, only within this review directory."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json
base=Path(__file__).resolve().parent
package=base/'visual-package'
rois={'down_left':(40,66,70,103),'left':(20,54,86,104),'up_left':(38,60,85,104),'up':(36,54,92,104),'up_right':(42,60,89,104),'right':(42,54,108,104),'down_right':(58,66,88,103)}
out={'rois_half_open':{k:list(v) for k,v in rois.items()},'diagnostic_sha256':{}}
for direction,roi in rois.items():
    for action,count in [('attack',6),('death',8)]:
        scale=8 if direction in ['down_left','down_right'] else 6
        w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
        for color,bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
            chart=Image.new('RGBA',(w*4,(h+24)*2),bg);draw=ImageDraw.Draw(chart)
            ink=(20,20,20,255) if color=='light' else (240,240,240,255)
            for f in range(count):
                im=Image.open(package/f'output/enemy_tracked_heavy/{action}_{direction}/f{f:02}.png').convert('RGBA')
                x,y=(f%4)*w,(f//4)*(h+24)
                draw.text((x+4,y+4),f'{action}_{direction} F{f:02}',fill=ink)
                chart.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
            p=base/f'visual-detail-{action}_{direction}-{color}-{scale}x.png';chart.convert('RGB').save(p)
            out['diagnostic_sha256'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(base/'visual-detail-binding.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
