"""Create fixed-position source/NE-frame evidence for the newly identified local risk."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib
import json

base=Path(__file__).resolve().parent
package=base/'visual-package'
source=Image.open(package/'source/up_right.png').convert('RGBA')
frames={n:Image.open(package/f'output/enemy_patrol/move_up_right/f{n:02}.png').convert('RGBA') for n in [2,3,4]}
roi=(50,76,81,105)
scale=12
w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
out={'roi_half_open':list(roi),'scale':scale,'diagnostic_sha256':{},'actual_pixel_reads':{},
     'source_points':{str(p):list(source.getpixel(p)) for p in [(62,89),(62,96),(62,82),(61,83)]},
     'coordinate_trace_scope':'Output pixels independently read; source ownership/transform trace provided by animation_skills.'}
for color,bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
    chart=Image.new('RGBA',(w*4,h+24),bg);draw=ImageDraw.Draw(chart)
    ink=(20,20,20,255) if color=='light' else (240,240,240,255)
    for col,(label,im) in enumerate([('SOURCE neutral',source)]+[(f'NE F{n:02}',frames[n]) for n in [2,3,4]]):
        draw.text((col*w+4,4),label,fill=ink)
        chart.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(col*w,24))
    p=base/f'visual-ne-local-source-f02-f03-f04-{color}-12x.png';chart.convert('RGB').save(p)
    out['diagnostic_sha256'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
for n,points in {2:[(62,89),(64,86),(62,96),(62,92)],3:[(61,83),(61,84),(59,85)],4:[(60,91),(63,88),(59,97),(65,95),(61,84),(61,85),(59,86)]}.items():
    out['actual_pixel_reads'][f'F{n:02}']=[{'xy':list(p),'rgba':list(frames[n].getpixel(p))} for p in points]
(base/'visual-ne-local.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Bound NE F02/03/04 pixel readings and fixed-position source comparison.')
