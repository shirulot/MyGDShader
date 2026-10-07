"""Read-only frozen C22 source binding and fixed-coordinate visual diagnostics."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from PIL import Image, ImageDraw
import hashlib,json

base=Path(__file__).resolve().parent
root=base.parents[3]
package=base/'visual-package'
archive=root/'art-source/ember/deliveries/enemy_cutter_six_moves_v022_v002_2026-10-07.zip'
expected='3b1619b3cc5a32f11dbe699716b88a9b4a1b8874da55526d6d8c61f6e7d3377e'
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
spec=json.loads((package/'rig.json').read_text())
directions=['down_left','left','up_left','up','up_right','right']
all_dirs=['down']+directions+['down_right']
frames={};sources={}
report={'zip_sha256':expected,'bytes':archive.stat().st_size,'members':len(entries),'payload':len(manifest['files']),
        'manifest_pass':True,'catalog_sha256':sha(package/'output/catalog.json'),'frames':{},'sources':{},'diagnostics':{},
        'full_roi_half_open':[24,52,104,108],'joint_roi_half_open':[32,63,96,108]}
for d in all_dirs:
    sources[d]=Image.open(package/f'source/{d}.png').convert('RGBA')
    frames[d]=[]
    for i in range(8):
        n=f'output/enemy_cutter/move_{d}/f{i:02d}.png';pic=Image.open(package/n).convert('RGBA')
        assert pic.size==(128,128) and set(pic.getchannel('A').tobytes())=={0,255}
        frames[d].append(pic);report['frames'][n]={'sha256':sha(package/n),'scope':'new' if d in directions else 'approved_reference'}
        alpha=pic.getchannel('A');alpha.paste(0,tuple(report['full_roi_half_open']))
        assert not any(alpha.tobytes())
    if d in directions:
        bind=Image.open(package/f'qa/bind_{d}.png').convert('RGBA')
        assert sources[d].tobytes()==bind.tobytes()
        cfg=spec['configs'][d]
        report['sources'][d]={'sha256':sha(package/f'source/{d}.png'),'neutral_bind_exact':True,
                              'parts':[{'id':p['id'],'sole':p.get('sole'),'opaque_source_pixels':p.get('opaque_source_pixels')} for p in cfg['parts']]}

def save(name,pic):
    p=base/name;pic.convert('RGB').save(p);report['diagnostics'][name]=sha(p)

for color,bg in {'light':(236,233,216,255),'dark':(25,42,52,255)}.items():
    ink=(20,20,20,255) if color=='light' else (240,240,240,255)
    for d in directions:
        for kind,scale in [('full',4),('joint',8)]:
            roi=tuple(report[f'{kind}_roi_half_open']);w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
            pic=Image.new('RGBA',(w*4,(h+24)*2),bg);draw=ImageDraw.Draw(pic)
            for i,im in enumerate(frames[d]):
                x,y=(i%4)*w,(i//4)*(h+24)
                draw.text((x+3,y+4),f'{d} F{i:02d}',fill=ink)
                pic.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
            save(f'visual-{kind}-{d}-{color}-{scale}x.png',pic)
    pic=Image.new('RGBA',(1124,792),bg);draw=ImageDraw.Draw(pic)
    for row,d in enumerate(directions):
        draw.text((3,24+row*128),d,fill=ink)
        for i,im in enumerate(frames[d]):
            draw.text((104+i*128,4),f'F{i:02d}',fill=ink);pic.alpha_composite(im,(100+i*128,24+row*128))
    save(f'visual-new48-native-{color}-1x.png',pic)
    # Native source/motion juxtaposition preserves the whole original canvas.
    pic=Image.new('RGBA',(740,792),bg);draw=ImageDraw.Draw(pic)
    for row,d in enumerate(directions):
        draw.text((3,24+row*128),d,fill=ink)
        for col,(label,im) in enumerate([('SOURCE',sources[d])]+[(f'F{i:02d}',frames[d][i]) for i in [0,2,4,6]]):
            draw.text((104+col*128,4),label,fill=ink);pic.alpha_composite(im,(100+col*128,24+row*128))
    save(f'visual-source-and-phases-{color}-1x.png',pic)
    roi=(24,52,104,108);w,h=80*3,56*3
    pic=Image.new('RGBA',(100+4*w,8*(h+24)),bg);draw=ImageDraw.Draw(pic)
    for row,d in enumerate(all_dirs):
        draw.text((3,row*(h+24)+4),d,fill=ink)
        for col,i in enumerate([0,2,4,6]):
            draw.text((104+col*w,row*(h+24)+4),f'F{i:02d}',fill=ink)
            pic.alpha_composite(frames[d][i].crop(roi).resize((w,h),Image.Resampling.NEAREST),(100+col*w,row*(h+24)+24))
    save(f'visual-eight-dir-same-phases-{color}-3x.png',pic)
(base/'visual-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'bytes':report['bytes'],'members':report['members'],'payload':report['payload'],'frames':len(report['frames']),'diagnostics':len(report['diagnostics']),'sources':report['sources']}))
