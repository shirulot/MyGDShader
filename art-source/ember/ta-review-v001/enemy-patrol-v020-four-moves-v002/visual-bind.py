"""Bind frozen P20 v002 and diagnose the revised NE frames at fixed coordinates."""
from pathlib import Path, PurePosixPath
from PIL import Image, ImageDraw
import hashlib
import json
import zipfile

base = Path(__file__).resolve().parent
root = base.parents[3]
package = base / 'visual-package'
old = base.parent / 'enemy-patrol-v020-four-moves-v001/visual-package'
zp = root / 'art-source/ember/deliveries/enemy_patrol_four_moves_v020_v002_2026-10-07.zip'
expected = '7bc4982abe5fdcfb7a205ddae599cffade57961b347fcd6200bb2f59a1f244a7'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(zp) == expected
with zipfile.ZipFile(zp) as z:
    assert z.testzip() is None
    members = [i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in members}) == len(members)
    for i in members:
        name = PurePosixPath(i.filename)
        assert not name.is_absolute() and '..' not in name.parts and ':' not in i.filename and '\\' not in i.filename
        p = package.joinpath(*name.parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(z.read(i))
manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8-sig'))
for name, row in manifest['files'].items():
    assert sha(package / name) == row['sha256']
    assert (package / name).stat().st_size == row['bytes']
source_path = package / 'source/up_right.png'
source = Image.open(source_path).convert('RGBA')
old_manifest = json.loads((old / 'manifest.json').read_text(encoding='utf-8-sig'))
for name in ['source/up_right.png'] + [f'output/enemy_patrol/move_up_right/f{i:02d}.png' for i in range(8)]:
    assert sha(old/name) == old_manifest['files'][name]['sha256']
assert sha(source_path) == sha(old / 'source/up_right.png')
frames, prior = [], []
result = {'zip_sha256': expected, 'bytes': zp.stat().st_size, 'members': len(members),
          'payload': len(manifest['files']), 'manifest_pass': True,
          'catalog_sha256': sha(package/'output/catalog.json'), 'source_sha256': sha(source_path),
          'source_same_v001': True, 'frames': {}, 'diagnostics': {}}
for i in range(8):
    name = f'output/enemy_patrol/move_up_right/f{i:02d}.png'
    a = Image.open(package / name).convert('RGBA')
    b = Image.open(old / name).convert('RGBA')
    assert a.size == b.size == (128, 128)
    assert set(a.getchannel('A').tobytes()) == {0, 255}
    frames.append(a); prior.append(b)
    changed = [(x, y) for y in range(128) for x in range(128) if a.getpixel((x, y)) != b.getpixel((x, y))]
    result['frames'][name] = {'sha256': sha(package/name), 'old_sha256': sha(old/name),
                            'changed_rgba_pixels': len(changed),
                            'bbox_half_open': [min(x for x,y in changed), min(y for x,y in changed), max(x for x,y in changed)+1, max(y for x,y in changed)+1]}
assert sum(r['changed_rgba_pixels'] for r in result['frames'].values()) == 334

def save(name, im):
    p = base/name
    im.convert('RGB').save(p)
    result['diagnostics'][name] = sha(p)

for color, bg in {'light': (232,232,228,255), 'dark': (25,42,52,255)}.items():
    ink = (20,20,20,255) if color == 'light' else (240,240,240,255)
    for kind, roi, scale in [('full', (16,20,112,112), 4), ('joints',(36,56,94,108),6), ('legs',(40,77,94,109),8)]:
        w,h = (roi[2]-roi[0])*scale, (roi[3]-roi[1])*scale
        chart = Image.new('RGBA',(w*4,(h+24)*2),bg); draw=ImageDraw.Draw(chart)
        for i,im in enumerate(frames):
            x,y=(i%4)*w,(i//4)*(h+24)
            draw.text((x+4,y+4),f'NE v002 F{i:02d}',fill=ink)
            chart.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
        save(f'visual-{kind}-ne-{color}-{scale}x.png',chart)
    chart = Image.new('RGBA',(1124,280),bg); draw=ImageDraw.Draw(chart)
    for row,(label,imgs) in enumerate([('v001',prior),('v002',frames)]):
        draw.text((4,24+row*128),label,fill=ink)
        for i,im in enumerate(imgs):
            draw.text((104+i*128,4),f'F{i:02d}',fill=ink)
            chart.alpha_composite(im,(100+i*128,24+row*128))
    save(f'visual-ne-eight-native-{color}-1x.png',chart)
    roi=(44,76,86,109);w,h=42*8,33*8
    for start in (0,4):
        chart=Image.new('RGBA',(w*3,(h+24)*4),bg);draw=ImageDraw.Draw(chart)
        for row,i in enumerate(range(start,start+4)):
            for col,(label,im) in enumerate([('SOURCE',source),(f'v001 F{i:02d}',prior[i]),(f'v002 F{i:02d}',frames[i])]):
                x,y=col*w,row*(h+24)
                draw.text((x+4,y+4),label,fill=ink)
                chart.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
        save(f'visual-ne-source-v001-v002-f{start:02d}-f{start+3:02d}-{color}-8x.png',chart)
(base/'visual-binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['frames','diagnostics']}))
print(json.dumps({'frame_changes':[v['changed_rgba_pixels'] for v in result['frames'].values()], 'diagnostics':len(result['diagnostics'])}))
