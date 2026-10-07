"""Freeze this review's input without altering production."""
from pathlib import Path, PurePosixPath
import hashlib, json, zipfile
from PIL import Image, ImageChops, ImageDraw
base = Path(__file__).resolve().parent
root = base.parents[3]
zip_path = root / 'art-source/ember/deliveries/enemy_drone_seven_directions_v013_s004_2026-10-06.zip'
expected = '3a6dc8a5ab9c16dc5e71d083568768ff3cabefae2675d5385e552149acb79342'
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(zip_path.read_bytes()) == expected
pkg = base / 'package'
pkg.mkdir(exist_ok=True)
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    members = [i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in members}) == len(members)
    for i in members:
        p = PurePosixPath(i.filename)
        assert not p.is_absolute() and '..' not in p.parts and ':' not in i.filename and '\\' not in i.filename
        dest = pkg.joinpath(*p.parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(z.read(i))
manifest_path = next(pkg.rglob('manifest.json'))
input_dir = manifest_path.parent
manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
data = {'zip_sha256': expected, 'bytes': zip_path.stat().st_size, 'entries': len(members), 'input_root': str(input_dir.relative_to(base)), 'zip_file_sha256': {i.filename: sha((pkg / i.filename).read_bytes()) for i in members}, 'manifest': manifest, 'native_images': {}}
for p in input_dir.glob('*.png'):
    im = Image.open(p).convert('RGBA')
    if im.size == (128,128):
        data['native_images'][p.name] = {'sha256': sha(p.read_bytes()), 'size': list(im.size), 'alpha': sorted(set(im.getchannel('A').tobytes())), 'bbox': im.getchannel('A').getbbox()}
data['manifest_checks'] = {}
for name, item in manifest['files'].items():
    p = input_dir / name
    data['manifest_checks'][name] = p.is_file() and sha(p.read_bytes()) == item['sha256'] and p.stat().st_size == item['bytes']
assert all(data['manifest_checks'].values()) and len(data['manifest_checks']) == 39
catalog = json.loads((input_dir / 'catalog.json').read_text(encoding='utf-8-sig'))
data['catalog_checks'] = {e['key']: sha((input_dir / (e['key'] + '.png')).read_bytes()) == e['sha256'] for e in catalog['entries']}
assert all(data['catalog_checks'].values())
old_dir = base.parent / 'enemy-drone-v013-c003' / 'package'
data['preserved_c003_checks'] = {}
for name, old_name in [('neutral_down.png', 'neutral_down.png'), ('generated_front.png', 'generated_front_c002.png'), ('neutral_down_left.png', 'neutral_down_left.png'), ('neutral_down_right.png', 'neutral_down_right.png')]:
    data['preserved_c003_checks'][name] = (input_dir / name).read_bytes() == (old_dir / old_name).read_bytes()
assert all(data['preserved_c003_checks'].values())
data['contact_pixel_checks'] = {}
for color, bg in [('white', (255,255,255,255)), ('black', (0,0,0,255))]:
    contact = Image.new('RGBA', (128*3,128*3), bg)
    for idx, entry in enumerate(catalog['entries']):
        contact.alpha_composite(Image.open(input_dir / (entry['key'] + '.png')).convert('RGBA'), ((idx%3)*128,(idx//3)*128))
    for scale in [1,4]:
        expected_contact = contact.resize((128*3*scale,128*3*scale), Image.Resampling.NEAREST).convert('RGB')
        actual = Image.open(input_dir / f'comparison_{color}_{scale}x.png').convert('RGB')
        data['contact_pixel_checks'][f'{color}_{scale}x'] = actual.size == expected_contact.size and ImageChops.difference(actual,expected_contact).getbbox() is None
assert all(data['contact_pixel_checks'].values())
# Native preassembly and submitted profile on a shared ROI, with only the
# declared whole-object registration added to the preassembly side.
for color, bg in [('light',(232,232,228,255)), ('dark',(25,42,52,255))]:
    out = Image.new('RGBA', (34*16*4,(45*16)+32), bg)
    draw = ImageDraw.Draw(out)
    for idx, (direction,offset) in enumerate([('left',(2,2)),('right',(-1,2))]):
        pre = Image.new('RGBA',(128,128),(0,0,0,0))
        pre.alpha_composite(Image.open(input_dir / 'provenance/source/registered/drone_profile_preassembly_v001' / (direction + '.png')).convert('RGBA'), offset)
        final = Image.open(input_dir / ('neutral_' + direction + '.png')).convert('RGBA')
        for k, (im,label) in enumerate([(pre, 'source + registration'),(final,'submitted')]):
            col = idx*2+k
            im = im.crop((48,45,82,90)).resize((34*16,45*16),Image.Resampling.NEAREST)
            out.alpha_composite(im,(col*34*16,32))
            draw.text((col*34*16+8,8),direction+' '+label,fill=(20,20,20,255) if color=='light' else (240,240,240,255))
    p = base / ('profile_preassembly_final_' + color + '_16x.png')
    out.convert('RGB').save(p)
data['independent_diagnostics_sha256'] = {p.name:sha(p.read_bytes()) for p in base.glob('profile_preassembly_final_*_16x.png')}
(base / 'visual-binding.json').write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({'input_root': str(input_dir), 'bytes': data['bytes'], 'entries': data['entries'], 'manifest_checked':len(data['manifest_checks']), 'catalog':data['catalog_checks'], 'preserved_c003':data['preserved_c003_checks'], 'contact_pixels':data['contact_pixel_checks']}, ensure_ascii=False))
