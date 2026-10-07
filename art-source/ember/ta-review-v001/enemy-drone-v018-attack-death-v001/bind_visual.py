"""Bind frozen D18 input and prepare readable fixed-canvas review charts."""
from pathlib import Path, PurePosixPath
import json, hashlib, zipfile
from PIL import Image, ImageChops, ImageDraw

base=Path(__file__).resolve().parent
root=base.parents[3]
zpath=root/'art-source/ember/deliveries/enemy_drone_attack_death_v018_v001_2026-10-07.zip'
expected='3da0700799bbc002601a77887912a64d67c7582c10ed86a1ccb64b1cd4661e7d'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(zpath)==expected
package=base/'package';package.mkdir(exist_ok=True)
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    members=[i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in members})==len(members)
    for i in members:
        p=PurePosixPath(i.filename)
        assert not p.is_absolute() and '..' not in p.parts and ':' not in i.filename and '\\' not in i.filename
        dest=package.joinpath(*p.parts);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(i))
manifest=json.loads((package/'manifest.json').read_text(encoding='utf-8-sig'))
checks={name:sha(package/name)==item['sha256'] and (package/name).stat().st_size==item['bytes'] for name,item in manifest['files'].items()}
assert len(checks)==262 and all(checks.values())
data={'zip_sha256':expected,'bytes':zpath.stat().st_size,'entries':len(members),'manifest_checks':checks,
      'catalog_sha256':sha(package/'output/catalog.json'),'rig_sha256':sha(package/'rig.json'),
      'frames':{},'contact_checks':{},'identity_checks':{},'endpoint_checks':{},'diagnostics_sha256':{},'bound_author_evidence':{}}
directions=['down','down_left','left','up_left','up','up_right','right','down_right']
new=directions[1:]
previous=base.parent/'enemy-drone-v017-idle-hit-v001/package'
all_frames={}
for direction in directions:
    all_frames[direction]={}
    for action,count in [('attack',6),('death',8)]:
        name=action+'_'+direction
        frames=[Image.open(package/f'output/enemy_scout_drone/{name}/f{f:02}.png').convert('RGBA') for f in range(count)]
        all_frames[direction][action]=frames
        data['frames'][name]=[{'frame':f,'sha256':sha(package/f'output/enemy_scout_drone/{name}/f{f:02}.png'),'size':list(im.size),'alpha':sorted(set(im.getchannel('A').tobytes()))} for f,im in enumerate(frames)]
        assert all(im.size==(128,128) and set(im.getchannel('A').tobytes())=={0,255} for im in frames)
        for color,bg in [('white',(255,255,255,255)),('black',(0,0,0,255))]:
            contact=Image.new('RGBA',(count*128,128),bg)
            for f,im in enumerate(frames):contact.alpha_composite(im,(f*128,0))
            for scale in [1,4]:
                wanted=contact.resize((count*128*scale,128*scale),Image.Resampling.NEAREST).convert('RGB')
                actual=Image.open(package/f'qa/{name}_{color}_{scale}x.png').convert('RGB')
                data['contact_checks'][f'{name}_{color}_{scale}x']=actual.size==wanted.size and ImageChops.difference(actual,wanted).getbbox() is None
        detail=Image.new('RGBA',(count*80,62),(255,255,255,255))
        for f,im in enumerate(frames):detail.alpha_composite(im.crop((24,44,104,106)),(f*80,0))
        wanted=detail.resize((count*320,248),Image.Resampling.NEAREST).convert('RGB')
        actual=Image.open(package/f'qa/detail_{name}_4x.png').convert('RGB')
        data['contact_checks'][f'detail_{name}_4x']=actual.size==wanted.size and ImageChops.difference(actual,wanted).getbbox() is None
        if action=='attack':data['endpoint_checks'][name]={'f05_rgba_equals_f00':frames[-1].tobytes()==frames[0].tobytes()}
        else:data['endpoint_checks'][name]={'f05_f06_f07_rgba_equal':frames[5].tobytes()==frames[6].tobytes()==frames[7].tobytes()}
    if direction in new:
        old=Image.open(previous/f'output/enemy_scout_drone/idle_{direction}/f00.png').convert('RGBA')
        data['identity_checks'][direction]={'source_png_same_v017':(package/f'source/{direction}.png').read_bytes()==(previous/f'source/{direction}.png').read_bytes(),
            'attack_f00_rgba_same_v017_idle_f00':all_frames[direction]['attack'][0].tobytes()==old.tobytes(),
            'death_f00_rgba_same_v017_idle_f00':all_frames[direction]['death'][0].tobytes()==old.tobytes()}
assert all(data['contact_checks'].values())
assert all(all(v.values()) for v in data['identity_checks'].values())
assert all(all(v.values()) for v in data['endpoint_checks'].values())
for action,count in [('attack',6),('death',8)]:
    for color,bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
        # Include the submitted old down reference, on identical 128x128 canvases.
        montage=Image.new('RGBA',(1124,1048),bg);draw=ImageDraw.Draw(montage)
        ink=(20,20,20,255) if color=='light' else (240,240,240,255)
        for f in range(count):draw.text((104+f*128,6),f'F{f:02}',fill=ink)
        for row,direction in enumerate(directions):
            draw.text((4,32+row*128),direction+(' (old)' if direction=='down' else ''),fill=ink)
            for f,im in enumerate(all_frames[direction][action]):montage.alpha_composite(im,(100+f*128,24+row*128))
        path=base/f'all_{action}_with_down_{color}_1x.png';montage.convert('RGB').save(path);data['diagnostics_sha256'][path.name]=sha(path)
        # Actual 4x full canvases in at most four columns prevent automatic shrinking
        # of the package's 3072/4096px-wide horizontal contacts during review.
        for direction in directions:
            for start in [0,4]:
                sheet=Image.new('RGBA',(2048,536),bg);draw=ImageDraw.Draw(sheet)
                for column,f in enumerate(range(start,min(start+4,count))):
                    draw.text((column*512+8,6),f'{action} {direction} F{f:02}',fill=ink)
                    sheet.alpha_composite(all_frames[direction][action][f].resize((512,512),Image.Resampling.NEAREST),(column*512,24))
                path=base/f'{action}_{direction}_f{start:02}_{color}_4x.png';sheet.convert('RGB').save(path);data['diagnostics_sha256'][path.name]=sha(path)
for name in ['gpu_roundtrip.json','runtime.json','pose_audit.json','pixel_audit.json']:data['bound_author_evidence'][name]=sha(package/'qa'/name)
(base/'visual-binding.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'bytes':data['bytes'],'entries':len(members),'manifest':len(checks),'new_frames':98,'old_reference_frames':14,'contacts':len(data['contact_checks']),'identity_checks':21},ensure_ascii=False))
