"""Bind frozen input and generate same-canvas review diagnostics only."""
from pathlib import Path, PurePosixPath
import hashlib, json, zipfile
from PIL import Image, ImageChops, ImageDraw
base = Path(__file__).resolve().parent
root = base.parents[3]
zpath = root / 'art-source/ember/deliveries/enemy_eight_directions_v013_pilot_drone_v001_2026-10-06.zip'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
expected_sha = '2ef84aaa45b2970bf4db9c5abdf4f845f4d65be9878c97d929701d090d4e37f1'
assert sha(zpath) == expected_sha
pkg = base / 'package'
pkg.mkdir(exist_ok=True)
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    files = [i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in files}) == len(files)
    for info in files:
        p = PurePosixPath(info.filename)
        assert not p.is_absolute() and '..' not in p.parts and ':' not in info.filename and '\\' not in info.filename
        target = pkg.joinpath(*p.parts)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(z.read(info))
manifest = json.loads((pkg / 'manifest.json').read_text(encoding='utf-8-sig'))
checks = {name: sha(pkg / name) == entry['sha256'] and (pkg / name).stat().st_size == entry['bytes'] for name,entry in manifest['files'].items()}
assert all(checks.values()) and len(checks) == 55
catalog = json.loads((pkg / 'output/pilot_catalog_v013.json').read_text(encoding='utf-8-sig'))
frames = [Image.open(pkg / 'output/enemy_scout_drone/move_down_right' / f'f{f:02}.png').convert('RGBA') for f in range(8)]
data = {'zip_sha256':expected_sha,'bytes':zpath.stat().st_size,'entries':len(files),'manifest_checks':checks,'catalog_sha256':sha(pkg / 'output/pilot_catalog_v013.json'),'frame_sha256':{},'frame_alpha':{},'diagnostics_sha256':{}}
for f,im in enumerate(frames):
    data['frame_sha256'][f'f{f:02}'] = sha(pkg / 'output/enemy_scout_drone/move_down_right' / f'f{f:02}.png')
    data['frame_alpha'][f'f{f:02}'] = {'size':list(im.size),'alpha':sorted(set(im.getchannel('A').tobytes())),'bbox':im.getchannel('A').getbbox()}
roi=Image.new('RGBA',(256,84),(255,255,255,255))
for f,im in enumerate(frames):
    roi.alpha_composite(im.crop((32,46,96,88)),((f%4)*64,(f//4)*42))
roi=roi.resize((2048,672),Image.Resampling.NEAREST).convert('RGB')
qa_roi=Image.open(pkg/'qa/drone_se_eight_rotors_8x.png').convert('RGB')
data['qa_rotor_roi_actual_frame_pixel_equal'] = qa_roi.size == roi.size and ImageChops.difference(roi,qa_roi).getbbox() is None
assert data['qa_rotor_roi_actual_frame_pixel_equal']
data['qa_rotor_roi_sha256']=sha(pkg/'qa/drone_se_eight_rotors_8x.png')
# Full original 128 canvas and anchor are retained, never bbox aligned.
for color,bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
    out = Image.new('RGBA',(128*4*4,(128*4+24)*2),bg)
    draw=ImageDraw.Draw(out)
    for f,im in enumerate(frames):
        x,y=(f%4)*128*4,(f//4)*(128*4+24)
        out.alpha_composite(im.resize((512,512),Image.Resampling.NEAREST),(x,y+24))
        draw.text((x+8,y+6),f'F{f:02}',fill=(20,20,20,255) if color=='light' else (240,240,240,255))
    p=base / f'frames_{color}_4x.png'
    out.convert('RGB').save(p)
    data['diagnostics_sha256'][p.name]=sha(p)
    # Compare old down and SE with their shared ground anchor, same frame index.
    atlas=Image.open(pkg / 'reference/enemy_scout_drone/move_down.png').convert('RGBA')
    assert atlas.size == (1024,128)
    phase=Image.new('RGBA',(128*4*4,(128*4+24)*4),bg)
    dr=ImageDraw.Draw(phase)
    for f,im in enumerate(frames):
        col=f%4
        row=f//4*2
        old=atlas.crop((f*128,0,(f+1)*128,128))
        for idx,(img,label) in enumerate([(old,'down'),(im,'SE')]):
            x,y=col*512,(row+idx)*(512+24)
            phase.alpha_composite(img.resize((512,512),Image.Resampling.NEAREST),(x,y+24))
            dr.text((x+8,y+6),f'{label} F{f:02}',fill=(20,20,20,255) if color=='light' else (240,240,240,255))
    p=base / f'down_se_same_frame_{color}_4x.png'
    phase.convert('RGB').save(p)
    data['diagnostics_sha256'][p.name]=sha(p)
(base / 'visual-binding.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'zip_sha256':expected_sha,'bytes':data['bytes'],'entries':len(files),'manifest':len(checks),'catalog_sha256':data['catalog_sha256'],'qa_rotor_roi_pixel_equal':data['qa_rotor_roi_actual_frame_pixel_equal']},ensure_ascii=False))
