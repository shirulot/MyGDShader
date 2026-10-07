"""Bind frozen H19 frames and prepare fixed-canvas visual diagnostics only."""
from pathlib import Path, PurePosixPath
from PIL import Image, ImageDraw, ImageChops
import hashlib, json, zipfile

base=Path(__file__).resolve().parent
root=base.parents[3]
zp=root/'art-source/ember/deliveries/enemy_heavy_attack_death_v019_v002_2026-10-07.zip'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='c16edaeb70592d03cd8426a584399d815bb00fd7791e3242a606abdf9ff8d192'
assert sha(zp)==expected
package=base/'visual-package';package.mkdir(exist_ok=True)
with zipfile.ZipFile(zp) as z:
    assert z.testzip() is None
    members=[i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in members})==len(members)
    for i in members:
        p=PurePosixPath(i.filename)
        assert not p.is_absolute() and '..' not in p.parts and ':' not in i.filename and '\\' not in i.filename
        dest=package.joinpath(*p.parts);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(i))
manifest=json.loads((package/'manifest.json').read_text(encoding='utf-8-sig'))
bad=[name for name,item in manifest['files'].items() if sha(package/name)!=item['sha256'] or (package/name).stat().st_size!=item['bytes']]
assert not bad and len(manifest['files'])==272
out={'zip_sha256':expected,'bytes':zp.stat().st_size,'file_members':len(members),'payload':len(manifest['files']),'manifest_bad':bad,'catalog_sha256':sha(package/'output/catalog.json'),'rig_sha256':sha(package/'rig.json'),'frames':{},'contact_binding':{},'endpoint_checks':{},'full_body_roi':[16,24,112,108],'roi_outside_visible':{},'diagnostic_sha256':{},'bound_author_evidence':{}}
dirs=['down','down_left','left','up_left','up','up_right','right','down_right']
loaded={}
for direction in dirs:
    loaded[direction]={}
    for action,count in [('attack',6),('death',8)]:
        key=action+'_'+direction
        frames=[]
        for f in range(count):
            p=package/f'output/enemy_tracked_heavy/{key}/f{f:02}.png'
            im=Image.open(p).convert('RGBA');frames.append(im)
            assert im.size==(128,128) and set(im.getchannel('A').tobytes())=={0,255}
            out['frames'][p.relative_to(package).as_posix()]={'sha256':sha(p),'size':list(im.size),'alpha_values':sorted(set(im.getchannel('A').tobytes()))}
        loaded[direction][action]=frames
        for color,bg in [('white',(255,255,255,255)),('black',(0,0,0,255))]:
            sheet=Image.new('RGBA',(128*count,128),bg)
            for f,im in enumerate(frames):sheet.alpha_composite(im,(f*128,0))
            for scale in [1,4]:
                actual=Image.open(package/f'qa/{key}_{color}_{scale}x.png').convert('RGB')
                wanted=sheet.resize((128*count*scale,128*scale),Image.Resampling.NEAREST).convert('RGB')
                same=actual.size==wanted.size and actual.tobytes()==wanted.tobytes()
                out['contact_binding'][f'{key}_{color}_{scale}x']=same
                assert same
        sheet=Image.new('RGBA',(88*count,66),(255,255,255,255))
        for f,im in enumerate(frames):sheet.alpha_composite(im.crop((20,40,108,106)),(f*88,0))
        wanted=sheet.resize((88*count*4,264),Image.Resampling.NEAREST).convert('RGB')
        actual=Image.open(package/f'qa/detail_{key}_4x.png').convert('RGB')
        same=actual.size==wanted.size and actual.tobytes()==wanted.tobytes()
        out['contact_binding'][f'detail_{key}_4x']=same;assert same
        if action=='attack':out['endpoint_checks'][key]={'f05_rgba_equals_f00':frames[5].tobytes()==frames[0].tobytes()}
        else:out['endpoint_checks'][key]={'f06_rgba_equals_f07':frames[6].tobytes()==frames[7].tobytes(),'f04_rgba_equals_f06':frames[4].tobytes()==frames[6].tobytes()}
        roi=tuple(out['full_body_roi'])
        outside=[]
        for im in frames:
            a=im.getchannel('A');a.paste(0,roi);outside.append(sum(v!=0 for v in a.tobytes()))
        out['roi_outside_visible'][key]=outside
        assert not any(outside),(key,outside)
        for color,bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
            chart=Image.new('RGBA',(1536,720),bg);draw=ImageDraw.Draw(chart)
            ink=(20,20,20,255) if color=='light' else (240,240,240,255)
            for f,im in enumerate(frames):
                x,y=(f%4)*384,(f//4)*360
                draw.text((x+4,y+4),f'{key} F{f:02}',fill=ink)
                chart.alpha_composite(im.crop(roi).resize((384,336),Image.Resampling.NEAREST),(x,y+24))
            p=base/f'visual-full_body-{key}-{color}-4x.png';chart.convert('RGB').save(p);out['diagnostic_sha256'][p.name]=sha(p)
for action,count in [('attack',6),('death',8)]:
    for color,bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
        chart=Image.new('RGBA',(1124,1048),bg);draw=ImageDraw.Draw(chart)
        ink=(20,20,20,255) if color=='light' else (240,240,240,255)
        for f in range(count):draw.text((100+f*128+4,4),f'F{f:02}',fill=ink)
        for row,direction in enumerate(dirs):
            draw.text((4,24+row*128),direction+(' OLD' if direction=='down' else ''),fill=ink)
            for f,im in enumerate(loaded[direction][action]):chart.alpha_composite(im,(100+f*128,24+row*128))
        p=base/f'visual-all_{action}_with_down-{color}-1x.png';chart.convert('RGB').save(p);out['diagnostic_sha256'][p.name]=sha(p)
for n in ['gpu_roundtrip.json','runtime.json','pixel_audit.json','pose_audit.json']:out['bound_author_evidence']['qa/'+n]=sha(package/'qa'/n)
for n in ['source/hidden_chassis_eight_views_v001.png','source/hidden_chassis_prompt.txt','source/hidden_registration.json','SOURCE_RECEIPT.json']:out['bound_author_evidence'][n]=sha(package/n)
(base/'visual-binding.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'bytes':out['bytes'],'members':len(members),'manifest':out['payload'],'frames':len(out['frames']),'contacts':len(out['contact_binding']),'outside_visible_pixels':sum(sum(v) for v in out['roi_outside_visible'].values())}))
