"""Read only frozen heavy movement input; write this review's binding."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile
from PIL import Image,ImageChops
base=Path(__file__).resolve().parent
root=base.parents[3]
zpath=root/'art-source/ember/deliveries/enemy_heavy_eight_moves_v014_v001_2026-10-06.zip'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='dbad34a8845cce2a648d904790f5abd34fd64abbb5762f50d458f595e648c9ae'
assert sha(zpath)==expected
pkg=base/'package';pkg.mkdir(exist_ok=True)
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    files=[i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in files})==len(files)
    for i in files:
        p=PurePosixPath(i.filename)
        assert not p.is_absolute() and '..' not in p.parts and ':' not in i.filename and '\\' not in i.filename
        target=pkg.joinpath(*p.parts);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(i))
manifest=json.loads((pkg/'manifest.json').read_text(encoding='utf-8-sig'))
checks={name:sha(pkg/name)==rec['sha256'] and (pkg/name).stat().st_size==rec['bytes'] for name,rec in manifest['files'].items()}
assert len(checks)==159 and all(checks.values())
cat=json.loads((pkg/'output/catalog.json').read_text(encoding='utf-8-sig'))
newdirs=['down_left','left','up_left','up','up_right','right']
data={'zip_sha256':expected,'bytes':zpath.stat().st_size,'entries':len(files),'manifest_checks':checks,'catalog_sha256':sha(pkg/'output/catalog.json'),'rig_sha256':sha(pkg/'rig.json'),'reviewed_frames':{},'contact_checks':{}}
for direction in newdirs:
    frames=[Image.open(pkg/'output/enemy_tracked_heavy'/('move_'+direction)/f'f{f:02}.png').convert('RGBA') for f in range(8)]
    data['reviewed_frames'][direction]=[{'frame':f,'sha256':sha(pkg/'output/enemy_tracked_heavy'/('move_'+direction)/f'f{f:02}.png'),'size':list(im.size),'alpha':sorted(set(im.getchannel('A').tobytes()))} for f,im in enumerate(frames)]
    for color,bg in [('white',(255,255,255,255)),('black',(0,0,0,255))]:
        sheet=Image.new('RGBA',(512,256),bg)
        for f,im in enumerate(frames):sheet.alpha_composite(im,((f%4)*128,(f//4)*128))
        for scale in [1,4]:
            expected_img=sheet.resize((512*scale,256*scale),Image.Resampling.NEAREST).convert('RGB')
            actual=Image.open(pkg/'qa'/f'move_{direction}_{color}_{scale}x.png').convert('RGB')
            key=f'{direction}_{color}_{scale}x'
            data['contact_checks'][key]=expected_img.size==actual.size and ImageChops.difference(expected_img,actual).getbbox() is None
    roi=Image.new('RGBA',(352,96),(255,255,255,255))
    for f,im in enumerate(frames):roi.alpha_composite(im.crop((20,58,108,106)),((f%4)*88,(f//4)*48))
    expected_roi=roi.resize((1408,384),Image.Resampling.NEAREST).convert('RGB')
    actual_roi=Image.open(pkg/'qa'/f'treads_{direction}_4x.png').convert('RGB')
    data['contact_checks'][direction+'_tread_roi_4x']=actual_roi.size==expected_roi.size and ImageChops.difference(actual_roi,expected_roi).getbbox() is None
data['contact_failures']=[k for k,v in data['contact_checks'].items() if not v]
assert not data['contact_failures']
(base/'visual-binding.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'zip_sha256':expected,'bytes':data['bytes'],'entries':len(files),'manifest':len(checks),'contact_pixel_equal':sum(data['contact_checks'].values()),'contact_failures':data['contact_failures'],'catalog_keys':list(cat)},ensure_ascii=False))
