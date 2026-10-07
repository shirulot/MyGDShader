"""Bind H19 v003's fixed delivery and create fixed-canvas SW/E review images only."""
from pathlib import Path, PurePosixPath
from PIL import Image, ImageDraw
import hashlib
import json
import zipfile

base = Path(__file__).resolve().parent
root = base.parents[3]
old = base.parent / 'enemy-heavy-v019-attack-death-v002/visual-package'
package = base / 'visual-package'
zip_path = root / 'art-source/ember/deliveries/enemy_heavy_attack_death_v019_v003_2026-10-07.zip'
expected = '18666a8a60b03a5d90ca96d0ae9e49db05f2384d4cf5e05b43fc27895c1935a4'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(zip_path) == expected
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    members = [i for i in z.infolist() if not i.is_dir()]
    assert len(set(i.filename.casefold() for i in members)) == len(members)
    for i in members:
        p = PurePosixPath(i.filename)
        assert not p.is_absolute() and '..' not in p.parts and ':' not in i.filename and '\\' not in i.filename
        target = package.joinpath(*p.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(z.read(i))
manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8-sig'))
for name, item in manifest['files'].items():
    p = package / name
    assert sha(p) == item['sha256'] and p.stat().st_size == item['bytes']
out = {'zip_sha256': expected, 'zip_bytes': zip_path.stat().st_size, 'file_members': len(members),
       'manifest_payload': len(manifest['files']), 'manifest_pass': True, 'reviewed_directions': ['down_left', 'right'],
       'frame_binding': {}, 'changed_frames_against_v002': {}, 'contact_binding': {},
       'full_body_roi': [16, 24, 112, 108], 'outside_roi_visible_count': {},
       'diagnostic_sha256': {}, 'source_binding': {}, 'bound_author_evidence': {}}
colors = {'light': (232,232,228,255), 'dark': (25,42,52,255)}
details = {'down_left': (40,66,70,103), 'right': (84,65,103,94)}
frames = {}
for direction in ['down_left', 'right']:
    source_name = f'source/{direction}.png'
    out['source_binding'][source_name] = {'sha256': sha(package/source_name), 'bytes_equal_v002': (package/source_name).read_bytes() == (old/source_name).read_bytes()}
    for action, count in [('attack',6), ('death',8)]:
        key = f'{action}_{direction}'
        frames[key] = []
        for n in range(count):
            rel = f'output/enemy_tracked_heavy/{key}/f{n:02}.png'
            p = package/rel
            im = Image.open(p).convert('RGBA')
            prev = Image.open(old/rel).convert('RGBA')
            assert im.size == (128,128) and set(im.getchannel('A').tobytes()) == {0,255}
            frames[key].append(im)
            out['frame_binding'][rel] = {'sha256':sha(p),'rgba_equals_v002':im.tobytes()==prev.tobytes(),'file_equals_v002':p.read_bytes()==(old/rel).read_bytes()}
            changes = []
            visible_changes = []
            for y in range(128):
                for x in range(128):
                    a,b = prev.getpixel((x,y)),im.getpixel((x,y))
                    if a != b:
                        changes.append((x,y))
                        if a[3] or b[3]: visible_changes.append((x,y))
            if changes:
                box = lambda pts: [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts)+1,max(y for x,y in pts)+1] if pts else None
                out['changed_frames_against_v002'][rel] = {'rgba_changed_pixels':len(changes),'visible_changed_pixels':len(visible_changes),'bbox_half_open':box(visible_changes)}
            a = im.getchannel('A')
            a.paste(0, tuple(out['full_body_roi']))
            out['outside_roi_visible_count'][rel] = sum(v != 0 for v in a.tobytes())
            assert out['outside_roi_visible_count'][rel] == 0
        for color, bg in [('white',(255,255,255,255)),('black',(0,0,0,255))]:
            chart = Image.new('RGBA',(count*128,128),bg)
            for n, im in enumerate(frames[key]): chart.alpha_composite(im,(n*128,0))
            for scale in [1,4]:
                wanted = chart.resize((count*128*scale,128*scale),Image.Resampling.NEAREST).convert('RGB')
                actual = Image.open(package/f'qa/{key}_{color}_{scale}x.png').convert('RGB')
                ok = wanted.size == actual.size and wanted.tobytes() == actual.tobytes()
                assert ok
                out['contact_binding'][f'{key}_{color}_{scale}x'] = ok
        for color,bg in colors.items():
            ink = (20,20,20,255) if color=='light' else (240,240,240,255)
            for kind,roi,scale in [('full',tuple(out['full_body_roi']),4),('detail',details[direction],8)]:
                w,h = (roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
                chart = Image.new('RGBA',(w*4,(h+24)*2),bg)
                draw = ImageDraw.Draw(chart)
                for n,im in enumerate(frames[key]):
                    x,y = (n%4)*w,(n//4)*(h+24)
                    draw.text((x+4,y+4),f'{key} F{n:02}',fill=ink)
                    chart.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
                p=base/f'visual-{kind}-{key}-{color}-{scale}x.png'
                chart.convert('RGB').save(p)
                out['diagnostic_sha256'][p.name]=sha(p)
for action,count in [('attack',6),('death',8)]:
    for color,bg in colors.items():
        chart=Image.new('RGBA',(1124,280),bg);draw=ImageDraw.Draw(chart)
        ink=(20,20,20,255) if color=='light' else (240,240,240,255)
        for row,direction in enumerate(['down_left','right']):
            draw.text((4,24+row*128),direction,fill=ink)
            for n,im in enumerate(frames[f'{action}_{direction}']):
                draw.text((104+n*128,4),f'F{n:02}',fill=ink)
                chart.alpha_composite(im,(100+n*128,24+row*128))
        p=base/f'visual-native-{action}-{color}-1x.png'
        chart.convert('RGB').save(p);out['diagnostic_sha256'][p.name]=sha(p)
# Fixed coordinate old/new comparison for the two actual P2s, not bbox alignment.
for key,indices,roi in [('death_down_left',[3,4,5,6,7],(42,82,57,97)),('attack_right',[0,1,3,4,5],(90,74,102,89)),('death_right',[2,3,4,5,6,7],(89,76,103,96))]:
    w,h=(roi[2]-roi[0])*8,(roi[3]-roi[1])*8
    for color,bg in colors.items():
        chart=Image.new('RGBA',(len(indices)*w,2*(h+24)),bg);draw=ImageDraw.Draw(chart)
        ink=(20,20,20,255) if color=='light' else (240,240,240,255)
        for row,version in enumerate(['v002','v003']):
            for col,n in enumerate(indices):
                im=Image.open((old if row==0 else package)/f'output/enemy_tracked_heavy/{key}/f{n:02}.png').convert('RGBA')
                draw.text((col*w+4,row*(h+24)+4),f'{version} F{n:02}',fill=ink)
                chart.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(col*w,row*(h+24)+24))
        p=base/f'visual-compare-{key}-{color}-8x.png';chart.convert('RGB').save(p);out['diagnostic_sha256'][p.name]=sha(p)
for name in ['qa/revision_audit_v003.json','qa/gpu_roundtrip.json','qa/runtime.json','source/hidden_chassis_eight_views_v001.png','source/hidden_registration.json','rig.json','rig.gd','socket.gdshader']:
    out['bound_author_evidence'][name]=sha(package/name)
(base/'visual-binding.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'zip_bytes':out['zip_bytes'],'file_members':len(members),'payload':len(manifest['files']),'scoped_frames':len(out['frame_binding']),'changed_frames':len(out['changed_frames_against_v002']),'contacts':len(out['contact_binding']),'diagnostics':len(out['diagnostic_sha256'])}))
