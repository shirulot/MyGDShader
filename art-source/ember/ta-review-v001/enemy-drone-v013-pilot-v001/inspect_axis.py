"""Document the visible rotor-center sampling question without altering frames."""
from pathlib import Path
import json, hashlib
from PIL import Image,ImageDraw
base=Path(__file__).resolve().parent
pkg=base/'package'
bobs=[0,-1,-1,0,1,1,0,0]
out=Image.new('RGB',(240*8,16*16+42),(232,232,228))
draw=ImageDraw.Draw(out)
data={}
for f,bob in enumerate(bobs):
    im=Image.open(pkg/'output/enemy_scout_drone/move_down_right'/f'f{f:02}.png').convert('RGBA')
    # Common original-canvas ROI; bob is retained in the displayed crop.
    crop=im.crop((72,51,87,67)).resize((240,256),Image.Resampling.NEAREST)
    tile=Image.new('RGBA',crop.size,(232,232,228,255));tile.alpha_composite(crop)
    out.paste(tile.convert('RGB'),(f*240,24))
    draw.text((f*240+8,6),f'far F{f:02} / bob {bob}',fill=(20,20,20))
    data[f'f{f:02}']={'body_y':bob,'axis_canvas':[79.5,58.5+bob],
      'center_pixel_79_58_plus_bob':list(im.getpixel((79,58+bob))),
      'center_3x3':[[list(im.getpixel((x,y+bob))) for x in range(78,81)] for y in range(57,60)]}
out.save(base/'far_axis_eight_16x.png')
(base/'axis-sampling-observation.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
binding=json.loads((base/'visual-binding.json').read_text(encoding='utf-8'))
binding['axis_observation_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [base/'axis-sampling-observation.json',base/'far_axis_eight_16x.png']}
(base/'visual-binding.json').write_text(json.dumps(binding,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(data))
