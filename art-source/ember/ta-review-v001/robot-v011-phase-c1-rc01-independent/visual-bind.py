"""Freeze C1 visual inputs and make fixed-canvas nearest-neighbor diagnostics."""
from pathlib import Path, PurePosixPath
from PIL import Image, ImageDraw, ImageChops
import hashlib, json, zipfile

base = Path(__file__).resolve().parent
root = base.parents[3]
zp = root/'art-source/ember/deliveries/robot_eight_way_v011_phase_c1_rc01_2026-10-07.zip'
sha = lambda data: hashlib.sha256(data).hexdigest()
expected = '0c62177198973b24bb3fbfcc306ba4617af3ad754eb5a0696bdfddb4f19f51df'
assert sha(zp.read_bytes()) == expected
dest = base/'visual-package'; dest.mkdir(exist_ok=True)
with zipfile.ZipFile(zp) as z:
    members = [i for i in z.infolist() if not i.is_dir()]
    assert z.testzip() is None
    assert len({i.filename.casefold() for i in members}) == len(members)
    for item in members:
        name = PurePosixPath(item.filename)
        assert not name.is_absolute() and '..' not in name.parts and ':' not in item.filename and '\\' not in item.filename
        path = dest.joinpath(*name.parts)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(z.read(item))
manifest = json.loads((dest/'sha256-manifest.json').read_text(encoding='utf-8-sig'))
manifest_bad = [item['file'] for item in manifest['files'] if sha((dest/item['file']).read_bytes()) != item['sha256'] or (dest/item['file']).stat().st_size != item['bytes']]
assert not manifest_bad
meta = json.loads((dest/'action-pilot-metadata.json').read_text(encoding='utf-8-sig'))
atlas = Image.open(dest/meta['atlas']).convert('RGBA')
out = {'zip_sha256':expected,'bytes':zp.stat().st_size,'file_members':len(members),'manifest_count':len(manifest['files']),'manifest_bad':manifest_bad,'metadata_sha256':sha((dest/'action-pilot-metadata.json').read_bytes()),'frames':{},'chart_binding':{},'diagnostic_sha256':{},'bound_author_evidence':{}}
loaded = {}
for clip in meta['clips'][:2]:
    name = clip['name']; loaded[name] = []
    for item in clip['frames']:
        path = dest/item['file']
        assert sha(path.read_bytes()) == item['sha256']
        im = Image.open(path).convert('RGBA')
        assert im.size == (64,96)
        x,y,w,h = item['region']
        region_same = im.tobytes() == atlas.crop((x,y,x+w,y+h)).tobytes()
        assert region_same
        out['frames'][item['file']] = {'sha256':item['sha256'],'size':list(im.size),'alpha_values':sorted(set(im.getchannel('A').tobytes())),'atlas_region_rgba_same':region_same}
        loaded[name].append(im)
    for color in ['light','dark']:
        for scale in [1,4]:
            p = dest/f'previews/{name}_{color}_{scale}x_v011.png'
            actual = Image.open(p).convert('RGBA')
            bg = actual.getpixel((0,0))
            contact = Image.new('RGBA',(128,96*((len(loaded[name])+1)//2)),bg)
            for f,im in enumerate(loaded[name]): contact.alpha_composite(im,((f%2)*64,(f//2)*96))
            wanted = contact.resize((contact.width*scale,contact.height*scale),Image.Resampling.NEAREST)
            same = actual.size == wanted.size and actual.tobytes() == wanted.tobytes()
            out['chart_binding'][p.relative_to(dest).as_posix()] = same
            assert same
            # New neutral background charts have labels outside the full frame.
            ink = (20,20,20,255) if color == 'light' else (240,240,240,255)
            review_bg = (232,232,228,255) if color == 'light' else (25,42,52,255)
            chart = Image.new('RGBA',(len(loaded[name])*64*scale,96*scale+24),review_bg)
            draw = ImageDraw.Draw(chart)
            for f,im in enumerate(loaded[name]):
                draw.text((f*64*scale+2,3),f'F{f:02}',fill=ink)
                chart.alpha_composite(im.resize((64*scale,96*scale),Image.Resampling.NEAREST),(f*64*scale,24))
            rp = base/f'visual-{name}-{color}-{scale}x.png';chart.convert('RGB').save(rp)
            out['diagnostic_sha256'][rp.name] = sha(rp.read_bytes())
idle = loaded['idle_down_left']; collect = loaded['collect_down_left']
out['return_collect_f03_to_idle_f00_rgba_same'] = collect[3].tobytes() == idle[0].tobytes()
mother = Image.open(dest/'source/candidate-masters/robot_idle_down_left_v011.png').convert('RGBA')
out['idle_f00_same_current_sw_identity_rgba'] = idle[0].tobytes() == mother.tobytes()
changed = [(x,y) for y in range(96) for x in range(64) if collect[1].getpixel((x,y)) != collect[2].getpixel((x,y))]
out['collect_f01_to_f02_difference'] = {'points':len(changed),'bbox_half_open':[min(x for x,y in changed),min(y for x,y in changed),max(x for x,y in changed)+1,max(y for x,y in changed)+1] if changed else None}
out['idle_lower_body_y64_to95_rgba_same'] = idle[0].crop((0,64,64,96)).tobytes() == idle[1].crop((0,64,64,96)).tobytes()
out['collect_shoe_bottom_y77_to95_rgba_same'] = all(im.crop((0,77,64,96)).tobytes() == collect[3].crop((0,77,64,96)).tobytes() for im in collect)
joint_roi = (14,40,46,81)
out['joint_roi'] = list(joint_roi)
for name in ['idle_down_left','collect_down_left']:
    for color,bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
        chart = Image.new('RGBA',(len(loaded[name])*256,352),bg);draw=ImageDraw.Draw(chart)
        ink=(20,20,20,255) if color=='light' else (240,240,240,255)
        for f,im in enumerate(loaded[name]):
            draw.text((f*256+4,4),f'{name} F{f:02}',fill=ink)
            chart.alpha_composite(im.crop(joint_roi).resize((256,328),Image.Resampling.NEAREST),(f*256,24))
        rp=base/f'visual-joints-{name}-{color}-8x.png';chart.convert('RGB').save(rp)
        out['diagnostic_sha256'][rp.name]=sha(rp.read_bytes())
for color,bg in [('light',(232,232,228,255)),('dark',(25,42,52,255))]:
    # All six complete characters on original 64x96 canvases, at true 8x.
    # Two rows are deliberate: no cropping or bounding-box alignment.
    chart = Image.new('RGBA',(2048,1584),bg);draw=ImageDraw.Draw(chart)
    ink=(20,20,20,255) if color=='light' else (240,240,240,255)
    for f,im in enumerate(collect):
        draw.text((f*512+5,4),f'collect F{f:02}',fill=ink)
        chart.alpha_composite(im.resize((512,768),Image.Resampling.NEAREST),(f*512,24))
    for f,im in enumerate(idle):
        draw.text((f*512+5,796),f'idle F{f:02}',fill=ink)
        chart.alpha_composite(im.resize((512,768),Image.Resampling.NEAREST),(f*512,816))
    rp=base/f'visual-all-six-{color}-8x.png';chart.convert('RGB').save(rp)
    out['diagnostic_sha256'][rp.name]=sha(rp.read_bytes())
for name in ['qa/export_validation_action_pilot.json','qa/godot_action_pilot_v011.json','qa/collect_down_left_joint_patch_v011.json','qa/idle_down_left_joint_patch_v011.json','qa/action_pilot_provenance.json']:
    out['bound_author_evidence'][name] = sha((dest/name).read_bytes())
(base/'visual-binding.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'manifest':out['manifest_count'],'frames':len(out['frames']),'chart_binding':sum(out['chart_binding'].values()),'return_same':out['return_collect_f03_to_idle_f00_rgba_same']}))
