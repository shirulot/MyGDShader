"""Small visible-color/source diagnostic for an observed rear tread edge."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
base=Path(__file__).resolve().parent
pkg=base/'package'
rig=json.loads((pkg/'rig.json').read_text(encoding='utf-8-sig'))
data={}
for direction in ['up','up_left','up_right','down_left','left','right']:
    source=Image.open(pkg/'source'/f'{direction}.png').convert('RGBA')
    frames=[Image.open(pkg/'output/enemy_tracked_heavy'/f'move_{direction}'/f'f{f:02}.png').convert('RGBA') for f in range(8)]
    records=[]
    for f,im in enumerate(frames):
        bright=[]
        for y in range(70,106):
            for x in range(20,108):
                rgba=im.getpixel((x,y))
                if rgba[3]==255 and min(rgba[:3])>=245:
                    bright.append({'xy':[x,y],'rgba':rgba,'source_same_point':source.getpixel((x,y))})
        records.append({'frame':f,'bright_points':bright})
    data[direction]=records
    if direction=='up':
        # Whole original coordinates retained, shared crop for all eight frames.
        out=Image.new('RGBA',(32*8*4,(40*8+24)*2),(25,42,52,255))
        draw=ImageDraw.Draw(out)
        for f,im in enumerate(frames):
            x,y=(f%4)*32*8,(f//4)*(40*8+24)
            out.alpha_composite(im.crop((20,68,52,108)).resize((256,320),Image.Resampling.NEAREST),(x,y+24))
            draw.text((x+8,y+6),f'up F{f:02}',fill=(240,240,240,255))
        out.convert('RGB').save(base/'rear_left_tread_eight_dark_8x.png')
up_source=Image.open(pkg/'source/up.png').convert('RGBA')
data['up_transparent_source_points']=[{'xy':list(xy),'rgba':up_source.getpixel(xy)} for xy in [(28,98),(28,99),(29,99),(29,100)]]
(base/'bright-tread-edge-observation.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
binding=json.loads((base/'visual-binding.json').read_text(encoding='utf-8'))
binding['edge_observation_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [base/'bright-tread-edge-observation.json',base/'rear_left_tread_eight_dark_8x.png']}
binding['visual_status']='NEEDS_REVISION'
(base/'visual-binding.json').write_text(json.dumps(binding,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'up_visible_white_point_counts':[len(rec['bright_points']) for rec in data['up']],'up_transparent_source_points':data['up_transparent_source_points']}))
