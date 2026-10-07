"""Common-canvas 1x montage, not a new asset or aligned silhouette."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
base=Path(__file__).resolve().parent;pkg=base/'package'
directions=['down_left','left','up_left','up','up_right','right','down_right']
for color,bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
    out=Image.new('RGBA',(100+128*8,24+128*7),bg)
    draw=ImageDraw.Draw(out);ink=(20,20,20,255) if color=='light' else (240,240,240,255)
    for c in range(8):draw.text((106+c*128,6),('idle' if c<4 else 'hit')+f' F{c%4:02}',fill=ink)
    for row,d in enumerate(directions):
        draw.text((8,24+row*128+54),d,fill=ink)
        for c in range(8):
            key=('idle_' if c<4 else 'hit_')+d
            im=Image.open(pkg/'output/enemy_tracked_heavy'/key/f'f{c%4:02}.png').convert('RGBA')
            out.alpha_composite(im,(100+c*128,24+row*128))
    out.convert('RGB').save(base/f'all_new_frames_{color}_1x.png')
binding=json.loads((base/'visual-binding.json').read_text(encoding='utf-8'))
binding['diagnostic_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in base.glob('all_new_frames_*_1x.png')}
(base/'visual-binding.json').write_text(json.dumps(binding,indent=2,ensure_ascii=False),encoding='utf-8')
print('56 frames, two 1x common-canvas montages saved')
