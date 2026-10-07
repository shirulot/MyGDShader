"""Inspect the delivered E boot rim; do not alter or regenerate candidate pixels."""
from pathlib import Path
from PIL import Image, ImageDraw
import json,hashlib

base=Path(__file__).resolve().parent;p=base/'visual-package'
im=lambda path:Image.open(path).convert('RGBA')
catalog=json.loads((p/'output/catalog.json').read_text())
poses=next(c['poses'] for c in catalog['clips'] if c['direction']=='right')
neutral=im(p/'qa/bind_right.png');near=im(p/'source/c002_right_near.png')
frames=[im(p/f'output/enemy_patrol/move_right/f{i:02}.png') for i in range(8)]
report={'scope':'source classification and actual PNG follow-up only; no production rerender',
        'near_source_points':{f'{x},{y}':list(near.getpixel((x,y))) for x,y in [(61,94),(61,95)]},
        'actual_pixels':{'f04':{f'{x},{y}':list(frames[4].getpixel((x,y))) for x,y in [(66,93),(67,94)]},
                         'f07':{'59,92':list(frames[7].getpixel((59,92)))}},
        'foot_alignment_translation':{},'diagnostics':{}}

def chart(name,items,cols,roi,scale,bg):
    w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
    c=Image.new('RGBA',(cols*w,((len(items)+cols-1)//cols)*(h+24)),bg);d=ImageDraw.Draw(c)
    for i,(label,pic) in enumerate(items):
        x,y=i%cols*w,i//cols*(h+24)
        d.text((x+3,y+4),label,fill=(15,15,15,255) if bg[0]>100 else (245,245,245,255))
        c.alpha_composite(pic.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
    c.convert('RGB').save(base/name)
    report['diagnostics'][name]={'sha256':hashlib.sha256((base/name).read_bytes()).hexdigest(),'roi_half_open':roi,'scale':scale}

# Whole delivered frames are translated only for an explicitly labelled local
# comparison. The boot anchor stays fixed so its upper-rim drift is visible.
aligned=[]
for f,pose in enumerate(poses):
    ankle=pose['part_transforms']['right_foot']['position'];delta=(int(58-ankle[0]),int(94-ankle[1]))
    report['foot_alignment_translation'][str(f)]=delta
    pic=Image.new('RGBA',(128,128));pic.alpha_composite(frames[f],delta)
    aligned.append((f'F{f:02} aligned to foot',pic))
for color,bg in {'light':(236,233,216,255),'dark':(25,42,52,255)}.items():
    chart(f'visual-e-foot-aligned-{color}-12x.png',[('C002 neutral',neutral)]+aligned,3,[51,85,70,105],12,bg)
    chart(f'visual-e-ankle-unmarked-{color}-4x.png',[(f'E F{i:02}',frames[i]) for i in [4,5,6,7]],4,[40,44,87,108],4,bg)
    chart(f'visual-e-ankle-unmarked-{color}-1x.png',[(f'E F{i:02}',frames[i]) for i in [4,5,6,7]],4,[0,0,128,128],1,bg)
(base/'visual-e-ankle-followup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'source':report['near_source_points'],'actual':report['actual_pixels'],'diagnostics':len(report['diagnostics'])}))
