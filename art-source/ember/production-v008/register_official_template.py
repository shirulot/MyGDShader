"""从官方模板读取连接位；只保存语义参照，不程序化制作美术轮廓。"""
from pathlib import Path
import hashlib
import json
from PIL import Image

P = Path(__file__).resolve().parent / 'inputs'
source = P / 'official_autotile_template_3x3_minimal.png'
image = Image.open(source).convert('RGB')
samples = [(32, 10), (54, 10), (54, 32), (54, 54),
           (32, 54), (10, 54), (10, 32), (10, 10)]

def on(x, y):
    r, g, b = image.getpixel((x, y))
    return r > 200 and g < 150

rows, coords = [], {}
for y in range(4):
    row = []
    for x in range(12):
        mask = sum(1 << i for i, (dx, dy) in enumerate(samples)
                   if on(x * 64 + dx, y * 64 + dy))
        occupied = on(x * 64 + 32, y * 64 + 32)
        row.append(mask if occupied else None)
        if occupied:
            coords[str(mask)] = [x, y]
            if mask in [255, 124, 28, 127, 17]:
                image.crop((x*64, y*64, (x+1)*64, (y+1)*64)).save(
                    P / f'official_mask{mask}.png')
    rows.append(row)
data = {'source_url': 'https://docs.godotengine.org/en/3.5/_images/autotile_template_3x3_minimal.png',
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'size': list(image.size), 'tile_size': 64,
        'bit_order': 'N NE E SE S SW W NW',
        'layout_rows': rows, 'unique_masks': len(coords), 'coords': coords,
        'purpose': 'Official topology reference only; no generated game artwork.'}
(P / 'official-template-layout.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
print(json.dumps(data))
