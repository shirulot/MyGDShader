"""Read the fixed P20 package and create original-coordinate visual diagnostics."""
from pathlib import Path, PurePosixPath
from PIL import Image, ImageDraw
import hashlib
import json
import zipfile

base=Path(__file__).resolve().parent
root=base.parents[3]
package=base/'visual-package'
zp=root/'art-source/ember/deliveries/enemy_patrol_four_moves_v020_v001_2026-10-07.zip'
expected='6a22203fde428f0820e3019ad5ae859159b4b39c35bcfe111190fc96c75c1e52'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(zp)==expected
with zipfile.ZipFile(zp) as z:
    assert z.testzip() is None
    members=[i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in members})==len(members)
    for i in members:
        p=PurePosixPath(i.filename)
        assert not p.is_absolute() and '..' not in p.parts and ':' not in i.filename and '\\' not in i.filename
        dest=package.joinpath(*p.parts);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(i))
manifest=json.loads((package/'manifest.json').read_text(encoding='utf-8-sig'))
for name,item in manifest['files'].items():
    p=package/name
    assert sha(p)==item['sha256'] and p.stat().st_size==item['bytes']
spec=json.loads((package/'rig.json').read_text())
dirs=['down_left','up_left','up','up_right']
colors={'light':(232,232,228,255),'dark':(25,42,52,255)}
out={'zip_sha256':expected,'bytes':zp.stat().st_size,'file_members':len(members),'manifest_payload':len(manifest['files']),
     'manifest_pass':True,'catalog_sha256':sha(package/'output/catalog.json'),'review_scope':dirs,'frames':{},'source_binding':{},
     'contact_binding':{},'roi_half_open':{'full':[16,20,112,112],'joints':[36,56,94,108],'legs':[40,77,94,109]},
     'outside_full_roi_visible_count':{},'diagnostic_sha256':{},'bound_author_evidence':{}}
frames={}
sources={}
for direction in ['down','down_right']+dirs:
    key='move_'+direction
    frames[direction]=[]
    for n in range(8):
        rel=f'output/enemy_patrol/{key}/f{n:02}.png'
        im=Image.open(package/rel).convert('RGBA')
        assert im.size==(128,128) and set(im.getchannel('A').tobytes())=={0,255}
        frames[direction].append(im)
        out['frames'][rel]={'sha256':sha(package/rel),'size':[128,128],'alpha_values':[0,255],'scope':'new' if direction in dirs else 'approved_reference'}
    if direction not in dirs:continue
    source_path=package/spec['configs'][direction]['source'].removeprefix('res://')
    sources[direction]=Image.open(source_path).convert('RGBA')
    bind=Image.open(package/f'qa/bind_{direction}.png').convert('RGBA')
    assert bind.tobytes()==sources[direction].tobytes()
    out['source_binding'][direction]={'source_sha256':sha(source_path),'bind_sha256':sha(package/f'qa/bind_{direction}.png'),'bind_rgba_equals_source':True,'f00_equals_neutral_rgba':frames[direction][0].tobytes()==sources[direction].tobytes()}
    for color,bg in [('white',(255,255,255,255)),('black',(0,0,0,255))]:
        sheet=Image.new('RGBA',(512,256),bg)
        for n,im in enumerate(frames[direction]):sheet.alpha_composite(im,((n%4)*128,(n//4)*128))
        for scale in [1,4]:
            actual=Image.open(package/f'qa/{key}_{color}_{scale}x.png').convert('RGB')
            wanted=sheet.resize((512*scale,256*scale),Image.Resampling.NEAREST).convert('RGB')
            ok=actual.size==wanted.size and actual.tobytes()==wanted.tobytes()
            assert ok
            out['contact_binding'][f'{key}_{color}_{scale}x']=ok
    for n,im in enumerate(frames[direction]):
        a=im.getchannel('A');a.paste(0,tuple(out['roi_half_open']['full']))
        out['outside_full_roi_visible_count'][f'{key}/f{n:02}']=sum(v!=0 for v in a.tobytes())
        assert out['outside_full_roi_visible_count'][f'{key}/f{n:02}']==0
    for color,bg in colors.items():
        ink=(20,20,20,255) if color=='light' else (240,240,240,255)
        for kind,scale in [('full',4),('joints',6),('legs',8)]:
            roi=tuple(out['roi_half_open'][kind]);w=(roi[2]-roi[0])*scale;h=(roi[3]-roi[1])*scale
            sheet=Image.new('RGBA',(w*4,(h+24)*2),bg);draw=ImageDraw.Draw(sheet)
            for n,im in enumerate(frames[direction]):
                x,y=(n%4)*w,(n//4)*(h+24)
                draw.text((x+4,y+4),f'{direction} F{n:02}',fill=ink)
                sheet.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
            path=base/f'visual-{kind}-{direction}-{color}-{scale}x.png'
            sheet.convert('RGB').save(path);out['diagnostic_sha256'][path.name]=sha(path)
for color,bg in colors.items():
    ink=(20,20,20,255) if color=='light' else (240,240,240,255)
    sheet=Image.new('RGBA',(1124,536),bg);draw=ImageDraw.Draw(sheet)
    for row,direction in enumerate(dirs):
        draw.text((4,24+row*128),direction,fill=ink)
        for n,im in enumerate(frames[direction]):
            draw.text((104+n*128,4),f'F{n:02}',fill=ink)
            sheet.alpha_composite(im,(100+n*128,24+row*128))
    path=base/f'visual-new32-native-{color}-1x.png';sheet.convert('RGB').save(path);out['diagnostic_sha256'][path.name]=sha(path)
    # Six original-coordinate leg rows show the same F00/02/04/06 phase as approved S and SE.
    roi=(36,73,94,109);w,h=58*4,36*4
    sheet=Image.new('RGBA',(100+4*w,6*(h+24)),bg);draw=ImageDraw.Draw(sheet)
    for row,direction in enumerate(['down','down_right']+dirs):
        draw.text((4,row*(h+24)+4),direction,fill=ink)
        for col,n in enumerate([0,2,4,6]):
            draw.text((104+col*w,row*(h+24)+4),f'F{n:02}',fill=ink)
            sheet.alpha_composite(frames[direction][n].crop(roi).resize((w,h),Image.Resampling.NEAREST),(100+col*w,row*(h+24)+24))
    path=base/f'visual-s-se-new-same-phase-legs-{color}-4x.png';sheet.convert('RGB').save(path);out['diagnostic_sha256'][path.name]=sha(path)
    # Whole canvas neutral source beside F00/02/04/06; F00 is deliberately not called neutral.
    sheet=Image.new('RGBA',(740,536),bg);draw=ImageDraw.Draw(sheet)
    for row,direction in enumerate(dirs):
        draw.text((4,24+row*128),direction,fill=ink)
        for col,(label,im) in enumerate([('BIND',sources[direction])]+[(f'F{n:02}',frames[direction][n]) for n in [0,2,4,6]]):
            draw.text((104+col*128,4),label,fill=ink);sheet.alpha_composite(im,(100+col*128,24+row*128))
    path=base/f'visual-neutral-new-phases-{color}-1x.png';sheet.convert('RGB').save(path);out['diagnostic_sha256'][path.name]=sha(path)
for name in ['qa/gpu_roundtrip.json','qa/runtime.json','qa/pixel_audit.json','qa/pose_audit.json','rig.json','rig.gd','SOURCE_RECEIPT.json']:
    out['bound_author_evidence'][name]=sha(package/name)
(base/'visual-binding.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'bytes':out['bytes'],'members':len(members),'payload':len(manifest['files']),'new_frames':32,'reference_frames':16,'binds':len(sources),'contacts':len(out['contact_binding']),'diagnostics':len(out['diagnostic_sha256'])}))
