"""Read frozen frames; preserve a common full-body ROI, no recentering."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib

base = Path(__file__).resolve().parent
package = base / 'package'
directions = ['down','down_left','left','up_left','up','up_right','right','down_right']
roi = (24,44,104,106)
result = {'roi': list(roi), 'outside_visible_pixels': {}, 'diagnostic_sha256': {}}
for direction in directions:
    for action, count in [('attack',6),('death',8)]:
        name = action + '_' + direction
        frames = [Image.open(package/f'output/enemy_scout_drone/{name}/f{f:02}.png').convert('RGBA') for f in range(count)]
        counts = []
        for im in frames:
            a = im.getchannel('A')
            outside = a.copy()
            outside.paste(0, roi)
            counts.append(sum(v != 0 for v in outside.tobytes()))
        result['outside_visible_pixels'][name] = counts
        assert not any(counts), (name, counts)
        for color, bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
            # Each 80x62 crop includes every visible pixel on the original canvas.
            sheet = Image.new('RGBA',(1280,544),bg)
            draw = ImageDraw.Draw(sheet)
            ink = (20,20,20,255) if color == 'light' else (240,240,240,255)
            for f, im in enumerate(frames):
                x = (f%4)*320
                y = (f//4)*272
                draw.text((x+5,y+5),f'{name} F{f:02}',fill=ink)
                crop = im.crop(roi).resize((320,248),Image.Resampling.NEAREST)
                sheet.alpha_composite(crop,(x,y+24))
            path = base/f'full_body_{name}_{color}_4x.png'
            sheet.convert('RGB').save(path)
            result['diagnostic_sha256'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
for direction in ['down_left','down_right']:
    probe_roi = (48,68,82,88)
    for color, bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
        sheet = Image.new('RGBA',(1088,368),bg)
        draw = ImageDraw.Draw(sheet)
        ink = (20,20,20,255) if color == 'light' else (240,240,240,255)
        for f in range(6):
            im = Image.open(package/f'output/enemy_scout_drone/attack_{direction}/f{f:02}.png').convert('RGBA')
            x, y = (f%4)*272, (f//4)*184
            draw.text((x+4,y+4),f'attack {direction} F{f:02}',fill=ink)
            sheet.alpha_composite(im.crop(probe_roi).resize((272,160),Image.Resampling.NEAREST),(x,y+24))
        path = base/f'probe_attack_{direction}_{color}_8x.png'
        sheet.convert('RGB').save(path)
        result['diagnostic_sha256'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
result['probe_roi'] = list(probe_roi)
(base/'roi-diagnostics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'charts':len(result['diagnostic_sha256']),'outside_visible_pixels':sum(sum(v) for v in result['outside_visible_pixels'].values())}))
