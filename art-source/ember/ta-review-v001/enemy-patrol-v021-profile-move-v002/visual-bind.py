"""Independent fixed-package diagnostics for P21 v002 W/E move frames."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from PIL import Image, ImageDraw
import hashlib,json

base=Path(__file__).resolve().parent;root=base.parents[3]
package=base/'visual-package'
archive=root/'art-source/ember/deliveries/enemy_patrol_profile_moves_v021_v002_2026-10-07.zip'
expected='c5e82a238abaf9c0d258370322c02503cc320364cacca7f17d7b59547925481b'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(archive)==expected
with ZipFile(archive) as z:
    assert z.testzip() is None
    entries=[i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in entries})==len(entries)
    for entry in entries:
        rel=PurePosixPath(entry.filename)
        assert not rel.is_absolute() and '..' not in rel.parts and ':' not in entry.filename and '\\' not in entry.filename
        p=package.joinpath(*rel.parts);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(entry))
manifest=json.loads((package/'manifest.json').read_text(encoding='utf-8-sig'))
assert {entry.filename for entry in entries}==set(manifest['files'])|{'manifest.json'}
fixed=root/'art-source/ember/enemy-patrol-profile-move-v021-review-v002'
for n,v in manifest['files'].items():
    assert sha(package/n)==v['sha256'] and (package/n).stat().st_size==v['bytes']
    assert (package/n).read_bytes()==(fixed/n).read_bytes()
catalog=json.loads((package/'output/catalog.json').read_text(encoding='utf-8-sig'))
assert sha(package/'output/catalog.json')=='bd3f70e183fad3c713c59c2e5336c7915903810f57896528426c09b330f24b10'
c002=root/'art-source/ember/ta-review-v001/enemy-patrol-v021-calibration-c002-v003/visual-package'
report={'zip_sha256':expected,'bytes':archive.stat().st_size,'members':len(entries),'payload':len(manifest['files']),
        'manifest_sha256':sha(package/'manifest.json'),'catalog_sha256':sha(package/'output/catalog.json'),
        'manifest_and_fixed_directory_binding':True,'c002_binding':{},'frames':{},'diagnostics':{},
        'full_roi_half_open':[40,44,87,108],'joint_roi_half_open':[48,76,79,107]}
im=lambda p:Image.open(p).convert('RGBA')
frames={};neutral={};source={}
old_archive=root/'art-source/ember/deliveries/enemy_patrol_profile_moves_v021_v001_2026-10-07.zip'
assert sha(old_archive)=='4c907f50f6851787d84e7212a0cd7c64215566baf482a520fde937212db10b61'
with ZipFile(old_archive) as old:
    for d in ['down','down_right','left','right']:
        frames[d]=[];source[d]=im(package/f'source/{d}.png')
        neutral[d]=im(package/f'output/enemy_patrol/neutral_{d}.png')
        clip=next(c for c in catalog['clips'] if c['direction']==d)
        for i in range(8):
            n=f'output/enemy_patrol/move_{d}/f{i:02}.png';pic=im(package/n)
            assert pic.size==(128,128) and set(pic.getchannel('A').tobytes())=={0,255}
            assert sha(package/n)==clip['frame_hashes'][i]
            alpha=pic.getchannel('A');alpha.paste(0,tuple(report['full_roi_half_open']));assert not any(alpha.tobytes())
            if d in ['down','down_right']:assert (package/n).read_bytes()==old.read(n)
            frames[d].append(pic);report['frames'][n]={'sha256':sha(package/n),'scope':'new' if d in ['left','right'] else 'preserved_reference'}
for d in ['left','right']:
    sources={}
    for part in ['body','near','far']:
        n=f'source/c002_{d}_{part}.png'
        assert (package/n).read_bytes()==(c002/f'output/{d}_{part}.png').read_bytes()
        sources[part]=sha(package/n)
    reference=im(c002/f'output/neutral_{d}.png')
    assert reference.tobytes()==neutral[d].tobytes()==im(package/f'qa/bind_{d}.png').tobytes()
    assert source[d].tobytes()==im(c002/f'source/{d}.png').tobytes()
    report['c002_binding'][d]={'actual_three_part_bytes_same':sources,'neutral_and_bind_full_rgba_same':True,'original_source_rgba_same':True}

def chart(name,items,cols,roi,scale,bg):
    w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
    pic=Image.new('RGBA',(cols*w,((len(items)+cols-1)//cols)*(h+24)),bg);draw=ImageDraw.Draw(pic)
    ink=(16,16,16,255) if bg[0]>100 else (240,240,240,255)
    for i,(label,frame) in enumerate(items):
        x,y=(i%cols)*w,(i//cols)*(h+24);draw.text((x+3,y+4),label,fill=ink)
        pic.alpha_composite(frame.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
    pic.convert('RGB').save(base/name)
    report['diagnostics'][name]={'sha256':sha(base/name),'roi_half_open':roi,'scale':scale,'labels':[label for label,_ in items]}

for color,bg in {'light':(236,233,216,255),'dark':(25,42,52,255)}.items():
    chart(f'visual-new16-native-{color}-1x.png',[(f'{d} F{i:02}',f) for d in ['left','right'] for i,f in enumerate(frames[d])],8,[0,0,128,128],1,bg)
    for d in ['left','right']:
        for kind,scale in [('full',4),('joint',8)]:
            chart(f'visual-{kind}-{d}-{color}-{scale}x.png',[(f'{d} F{i:02}',f) for i,f in enumerate(frames[d])],4,report[f'{kind}_roi_half_open'],scale,bg)
    chart(f'visual-loop-{color}-8x.png',[(f'{d} F{i:02}',frames[d][i]) for d in ['left','right'] for i in [6,7,0,1]],4,report['joint_roi_half_open'],8,bg)
    chart(f'visual-c002-source-phase-{color}-4x.png',[(f'{d} {label}',frame) for d in ['left','right'] for label,frame in [('S002',source[d]),('C002',neutral[d])]+[(f'F{i:02}',frames[d][i]) for i in [0,2,4,6]]],6,report['full_roi_half_open'],4,bg)
    chart(f'visual-s-se-reference-{color}-4x.png',[(f'{d} F{i:02}',frames[d][i]) for d in ['down','down_right','left','right'] for i in [0,2,4,6]],4,report['full_roi_half_open'],4,bg)
(base/'visual-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'bytes':report['bytes'],'members':report['members'],'payload':report['payload'],'frames':len(report['frames']),'diagnostics':len(report['diagnostics'])}))
