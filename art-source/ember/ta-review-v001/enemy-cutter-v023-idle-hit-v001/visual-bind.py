"""Bind C23 independently and render diagnostics without changing the candidate."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from PIL import Image, ImageDraw
import hashlib,json

base=Path(__file__).resolve().parent;root=base.parents[3];package=base/'visual-package'
archive=root/'art-source/ember/deliveries/enemy_cutter_idle_hit_v023_v001_2026-10-07.zip'
expected='ec2c8806c16271f55ee584749abe0166ac80e00985816150feb2b2369e934973'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(archive)==expected
with ZipFile(archive) as z:
    assert z.testzip() is None
    entries=[i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in entries})==len(entries)
    for i in entries:
        rel=PurePosixPath(i.filename)
        assert not rel.is_absolute() and '..' not in rel.parts and ':' not in i.filename and '\\' not in i.filename
        p=package.joinpath(*rel.parts);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(i))
manifest=json.loads((package/'manifest.json').read_text(encoding='utf-8-sig'))
for n,r in manifest['files'].items():
    assert sha(package/n)==r['sha256'] and (package/n).stat().st_size==r['bytes']
directions=['down_left','left','up_left','up','up_right','right','down_right']
all_dirs=['down']+directions;frames={};sources={}
report={'zip_sha256':expected,'bytes':archive.stat().st_size,'members':len(entries),'payload':len(manifest['files']),
        'manifest_pass':True,'catalog_sha256':sha(package/'output/catalog.json'),'frames':{},'sources':{},'endpoints':{},'diagnostics':{},
        'full_roi_half_open':[24,52,104,108],'joint_roi_half_open':[32,63,96,108]}
assert report['catalog_sha256']=='940b855cafd4c427e98ab2e0e3080ded092c4dd0cdd03c36e01a06aa224662ad'
for d in all_dirs:
    sources[d]=Image.open(package/f'source/{d}.png').convert('RGBA');frames[d]={}
    for action in ['idle','hit']:
        frames[d][action]=[]
        for i in range(4):
            n=f'output/enemy_cutter/{action}_{d}/f{i:02d}.png';pic=Image.open(package/n).convert('RGBA')
            assert pic.size==(128,128) and set(pic.getchannel('A').tobytes())=={0,255}
            frames[d][action].append(pic);report['frames'][n]={'sha256':sha(package/n),'scope':'new' if d in directions else 'approved_reference'}
            alpha=pic.getchannel('A');alpha.paste(0,tuple(report['full_roi_half_open']))
            assert not any(alpha.tobytes())
    if d in directions:
        bind=Image.open(package/f'qa/bind_{d}.png').convert('RGBA')
        neutral=Image.open(package/f'output/enemy_cutter/neutral_{d}.png').convert('RGBA')
        assert sources[d].tobytes()==bind.tobytes()==neutral.tobytes()
        assert all(frames[d][a][f].tobytes()==neutral.tobytes() for a,f in [('idle',0),('idle',2),('hit',0),('hit',3)])
        report['sources'][d]={'sha256':sha(package/f'source/{d}.png'),'bind_and_neutral_rgba_exact':True}
        report['endpoints'][d]={'idle_f00_f02_hit_f00_f03_equals_neutral':True}
oldhc=root/'art-source/ember/deliveries/enemy_eight_directions_pilot_hc_v013_v001_2026-10-06.zip'
# Bind the already-reviewed actual HC neutral from its preserved review package.
hc=root/'art-source/ember/ta-review-v001/enemy-v013-pilot-hc-v001/package/output/enemy_cutter/rig_neutral_down_right.png'
assert sha(hc)=='79e56cd5438f5b78d4dad555e9a364c359635b8cb8b58c6b1790cc166679b462'
assert hc.read_bytes()==(package/'source/down_right.png').read_bytes()
report['se_hc_neutral_byte_exact']=True
report['c22_six_source_byte_exact']={}
for d in directions[:-1]:
    previous=root/f'art-source/ember/ta-review-v001/enemy-cutter-v022-six-moves-v002/visual-package/source/{d}.png'
    assert previous.read_bytes()==(package/f'source/{d}.png').read_bytes()
    report['c22_six_source_byte_exact'][d]=True

def save(name,pic):
    p=base/name;pic.convert('RGB').save(p);report['diagnostics'][name]=sha(p)

for color,bg in {'light':(236,233,216,255),'dark':(25,42,52,255)}.items():
    ink=(20,20,20,255) if color=='light' else (240,240,240,255)
    for d in directions:
        eight=frames[d]['idle']+frames[d]['hit']
        for kind,scale in [('full',4),('joint',8)]:
            roi=tuple(report[f'{kind}_roi_half_open']);w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
            pic=Image.new('RGBA',(w*4,(h+24)*2),bg);draw=ImageDraw.Draw(pic)
            for i,im in enumerate(eight):
                x,y=(i%4)*w,(i//4)*(h+24);label=f"{d} {'idle' if i<4 else 'hit'} F{i%4:02d}"
                draw.text((x+3,y+4),label,fill=ink);pic.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
            save(f'visual-{kind}-{d}-{color}-{scale}x.png',pic)
    pic=Image.new('RGBA',(1124,920),bg);draw=ImageDraw.Draw(pic)
    for row,d in enumerate(directions):
        draw.text((3,24+row*128),d,fill=ink)
        for i,im in enumerate(frames[d]['idle']+frames[d]['hit']):
            draw.text((104+i*128,4),f"{'I' if i<4 else 'H'}{i%4:02d}",fill=ink);pic.alpha_composite(im,(100+i*128,24+row*128))
    save(f'visual-new56-native-{color}-1x.png',pic)
    roi=(24,52,104,108);w,h=80*3,56*3
    pic=Image.new('RGBA',(100+5*w,8*(h+24)),bg);draw=ImageDraw.Draw(pic)
    for row,d in enumerate(all_dirs):
        draw.text((3,row*(h+24)+4),d,fill=ink)
        choices=[('SOURCE',sources[d]),('IDLE01',frames[d]['idle'][1]),('IDLE03',frames[d]['idle'][3]),('HIT01',frames[d]['hit'][1]),('HIT02',frames[d]['hit'][2])]
        for col,(label,im) in enumerate(choices):
            draw.text((104+col*w,row*(h+24)+4),label,fill=ink);pic.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(100+col*w,row*(h+24)+24))
    save(f'visual-source-extreme-pose-reference-{color}-3x.png',pic)
# Include separately rendered, actually inspected coordinate crops in this receipt.
for p in sorted(base.glob('visual-check-seam-*.png')):
    report['diagnostics'][p.name]=sha(p)
(base/'visual-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'bytes':report['bytes'],'members':report['members'],'payload':report['payload'],'frames':len(report['frames']),'diagnostics':len(report['diagnostics']),'se_hc_neutral_byte_exact':report['se_hc_neutral_byte_exact']}))
