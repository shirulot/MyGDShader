"""Review only frozen v002 increment against this audit's frozen v001."""
from pathlib import Path,PurePosixPath
import hashlib,json,zipfile,copy
from PIL import Image,ImageChops,ImageDraw
base=Path(__file__).resolve().parent
root=base.parents[3]
old=base.parent/'enemy-heavy-v014-move-v001/package'
zpath=root/'art-source/ember/deliveries/enemy_heavy_eight_moves_v014_v002_2026-10-07.zip'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='74ce3153d2389e9d170fbc5ccf0ea92dcf0a14dd671822d3479a5feaa1d00db9'
assert sha(zpath)==expected
pkg=base/'package';pkg.mkdir(exist_ok=True)
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    files=[i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in files})==len(files)
    for info in files:
        p=PurePosixPath(info.filename)
        assert not p.is_absolute() and '..' not in p.parts and ':' not in info.filename and '\\' not in info.filename
        dest=pkg.joinpath(*p.parts);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(info))
manifest=json.loads((pkg/'manifest.json').read_text(encoding='utf-8-sig'))
checks={p:sha(pkg/p)==rec['sha256'] and (pkg/p).stat().st_size==rec['bytes'] for p,rec in manifest['files'].items()}
assert all(checks.values())
directions=['down','down_left','left','up_left','up_right','right','down_right']
same={}
for d in directions:
    for p in sorted((pkg/'output/enemy_tracked_heavy'/('move_'+d)).glob('*.png')):
        rel=p.relative_to(pkg);same[str(rel).replace('\\','/')]=p.read_bytes()==(old/rel).read_bytes()
    rel=Path('output/enemy_tracked_heavy')/f'move_{d}.png'
    same[str(rel).replace('\\','/')]=(pkg/rel).read_bytes()==(old/rel).read_bytes()
assert len(same)==63 and all(same.values())
source_same={f'source/{d}.png':(pkg/'source'/f'{d}.png').read_bytes()==(old/'source'/f'{d}.png').read_bytes() for d in ['up']+directions}
assert all(source_same.values())
logic_same={p:(pkg/p).read_bytes()==(old/p).read_bytes() for p in ['rig.gd','tread_flow.gdshader','masked_part.gdshader']}
assert all(logic_same.values())
rig=json.loads((pkg/'rig.json').read_text(encoding='utf-8-sig'))
oldrig=json.loads((old/'rig.json').read_text(encoding='utf-8-sig'))
normalized=copy.deepcopy(rig);normalized.pop('revision',None)
normalized['configs']['up']['windows'][0]=oldrig['configs']['up']['windows'][0]
assert normalized==oldrig
source=Image.open(pkg/'source/up.png').convert('RGBA')
newwindow_alpha=sorted({source.getpixel((x,y))[3] for y in range(85,101) for x in range(31,42)})
assert newwindow_alpha==[255]
frames=[Image.open(pkg/'output/enemy_tracked_heavy/move_up'/f'f{f:02}.png').convert('RGBA') for f in range(8)]
records=[]
for f,im in enumerate(frames):
    prev=Image.open(old/'output/enemy_tracked_heavy/move_up'/f'f{f:02}.png').convert('RGBA')
    changed=[];outside=[];white=[]
    for y in range(128):
        for x in range(128):
            rgba=im.getpixel((x,y))
            if rgba!=prev.getpixel((x,y)):
                changed.append([x,y])
                if not (28<=x<44 and 85<=y<101):outside.append([x,y])
            if 20<=x<52 and 68<=y<108 and rgba==(255,255,255,255):white.append([x,y])
    alpha_equal=im.getchannel('A').tobytes()==prev.getchannel('A').tobytes()
    fixed_bronze={str(xy):list(im.getpixel(xy))==list(source.getpixel(xy)) for xy in [(28,89),(29,89),(28,90),(29,90)]}
    assert alpha_equal and not outside and not white and all(fixed_bronze.values())
    changed_bbox=[min(p[0] for p in changed),min(p[1] for p in changed),max(p[0] for p in changed)+1,max(p[1] for p in changed)+1] if changed else None
    records.append({'frame':f,'png_sha256':sha(pkg/'output/enemy_tracked_heavy/move_up'/f'f{f:02}.png'),'changed_pixels':len(changed),'changed_bbox':changed_bbox,'outside_old_window':outside,'alpha_equal':alpha_equal,'pure_white_edge_points':white,'fixed_bronze_matches_source':fixed_bronze})
assert (pkg/'output/enemy_tracked_heavy/move_up/f00.png').read_bytes()==(old/'output/enemy_tracked_heavy/move_up/f00.png').read_bytes()
contact_checks={}
for color,bg in [('white',(255,255,255,255)),('black',(0,0,0,255))]:
    contact=Image.new('RGBA',(512,256),bg)
    for f,im in enumerate(frames):contact.alpha_composite(im,((f%4)*128,(f//4)*128))
    for scale in [1,4]:
        a=Image.open(pkg/'qa'/f'move_up_{color}_{scale}x.png').convert('RGB')
        e=contact.resize((512*scale,256*scale),Image.Resampling.NEAREST).convert('RGB')
        contact_checks[f'{color}_{scale}x']=a.size==e.size and ImageChops.difference(a,e).getbbox() is None
assert all(contact_checks.values())
out=Image.new('RGBA',(32*8*4,(40*8+24)*2),(25,42,52,255));draw=ImageDraw.Draw(out)
for f,im in enumerate(frames):
    x,y=(f%4)*256,(f//4)*344
    out.alpha_composite(im.crop((20,68,52,108)).resize((256,320),Image.Resampling.NEAREST),(x,y+24))
    draw.text((x+8,y+6),f'v002 up F{f:02}',fill=(240,240,240,255))
out.convert('RGB').save(base/'rear_left_tread_eight_dark_8x.png')
data={'zip_sha256':expected,'bytes':zpath.stat().st_size,'entries':len(files),'manifest_checks':checks,'seven_directions_63_png_byte_equal':same,'eight_source_png_byte_equal':source_same,'logic_byte_equal':logic_same,'rig_changes_only_up_left_window_and_revision':True,'new_window':rig['configs']['up']['windows'][0],'new_window_source_alpha':newwindow_alpha,'new_window_sample_points':176,'n_frames':records,'contact_pixel_checks':contact_checks,'diagnostic_sha256':sha(base/'rear_left_tread_eight_dark_8x.png')}
(base/'visual-incremental-evidence.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'bytes':data['bytes'],'entries':data['entries'],'manifest':len(checks),'seven_directions_png_same':len(same),'logic_byte_equal':logic_same,'new_window_source_alpha':newwindow_alpha,'n_frame_changed_pixels':[r['changed_pixels'] for r in records],'white_edge_points':[len(r['pure_white_edge_points']) for r in records],'contacts':contact_checks},ensure_ascii=False))
