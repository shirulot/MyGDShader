"""Bind frozen heavy idle/hit input; validate charts against actual frames."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile
from PIL import Image,ImageChops
base=Path(__file__).resolve().parent;root=base.parents[3]
zpath=root/'art-source/ember/deliveries/enemy_heavy_idle_hit_v015_v001_2026-10-07.zip'
expected='3ebf1f1fdb7bb820cdb09258b76df2e087c29f0f8dea1b4bbc0e76adce4bd29f'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(zpath)==expected
pkg=base/'package';pkg.mkdir(exist_ok=True)
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    members=[i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in members})==len(members)
    for i in members:
        p=PurePosixPath(i.filename)
        assert not p.is_absolute() and '..' not in p.parts and ':' not in i.filename and '\\' not in i.filename
        dest=pkg.joinpath(*p.parts);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(i))
manifest=json.loads((pkg/'manifest.json').read_text(encoding='utf-8-sig'))
checks={p:sha(pkg/p)==rec['sha256'] and (pkg/p).stat().st_size==rec['bytes'] for p,rec in manifest['files'].items()}
assert all(checks.values())
directions=['down_left','left','up_left','up','up_right','right','down_right']
data={'zip_sha256':expected,'bytes':zpath.stat().st_size,'entries':len(members),'manifest_checks':checks,'catalog_sha256':sha(pkg/'output/catalog.json'),'rig_sha256':sha(pkg/'rig.json'),'frames':{},'contact_checks':{}}
for d in directions:
    for action in ['idle','hit']:
        key=action+'_'+d
        frames=[Image.open(pkg/'output/enemy_tracked_heavy'/key/f'f{f:02}.png').convert('RGBA') for f in range(4)]
        data['frames'][key]=[{'frame':f,'sha256':sha(pkg/'output/enemy_tracked_heavy'/key/f'f{f:02}.png'),'size':list(im.size),'alpha':sorted(set(im.getchannel('A').tobytes()))} for f,im in enumerate(frames)]
        for color,bg in [('white',(255,255,255,255)),('black',(0,0,0,255))]:
            sheet=Image.new('RGBA',(512,128),bg)
            for f,im in enumerate(frames):sheet.alpha_composite(im,(f*128,0))
            for scale in [1,4]:
                e=sheet.resize((512*scale,128*scale),Image.Resampling.NEAREST).convert('RGB')
                a=Image.open(pkg/'qa'/f'{key}_{color}_{scale}x.png').convert('RGB')
                data['contact_checks'][f'{key}_{color}_{scale}x']=a.size==e.size and ImageChops.difference(a,e).getbbox() is None
        roi=Image.new('RGBA',(288,50),(255,255,255,255))
        for f,im in enumerate(frames):roi.alpha_composite(im.crop((28,50,100,100)),(f*72,0))
        e=roi.resize((1728,300),Image.Resampling.NEAREST).convert('RGB')
        a=Image.open(pkg/'qa'/f'mount_{key}_6x.png').convert('RGB')
        data['contact_checks'][f'mount_{key}_6x']=a.size==e.size and ImageChops.difference(a,e).getbbox() is None
assert all(data['contact_checks'].values())
(base/'visual-binding.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'bytes':data['bytes'],'entries':len(members),'manifest':len(checks),'new_frames':sum(len(a) for a in data['frames'].values()),'contact_checks':sum(data['contact_checks'].values())},ensure_ascii=False))
