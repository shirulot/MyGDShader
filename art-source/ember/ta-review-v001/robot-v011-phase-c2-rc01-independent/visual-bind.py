"""Bind fixed C2 visuals and make original 64x96-canvas diagnostics; no source edits."""
from pathlib import Path, PurePosixPath
from PIL import Image, ImageDraw
import hashlib
import json
import zipfile

base=Path(__file__).resolve().parent
root=base.parents[3]
package=base/'visual-package'
zp=root/'art-source/ember/deliveries/robot_eight_way_v011_phase_c2_rc01_2026-10-07.zip'
expected='e0a5fe91bcd62509d0f342e45334ce34cf374ebea1ac0203162d9b90f79b5643'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(zp)==expected
with zipfile.ZipFile(zp) as z:
    assert z.testzip() is None
    members=[i for i in z.infolist() if not i.is_dir()]
    assert len({i.filename.casefold() for i in members})==len(members)
    for i in members:
        name=PurePosixPath(i.filename)
        assert not name.is_absolute() and '..' not in name.parts and ':' not in i.filename and '\\' not in i.filename
        p=package.joinpath(*name.parts);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(i))
manifest=json.loads((package/'sha256-manifest.json').read_text(encoding='utf-8-sig'))
for item in manifest['files']:
    p=package/item['file']
    assert sha(p)==item['sha256'] and p.stat().st_size==item['bytes']
meta=json.loads((package/'full-action-metadata.json').read_text(encoding='utf-8-sig'))
atlas=Image.open(package/meta['atlas']).convert('RGBA')
dirs=['down','left','up_left','up','up_right','right','down_right']
out={'zip_sha256':expected,'bytes':zp.stat().st_size,'file_members':len(members),'manifest_payload':len(manifest['files']),
     'manifest_pass':True,'metadata_sha256':sha(package/'full-action-metadata.json'),'atlas_sha256':sha(package/meta['atlas']),
     'canvas':meta['canvas'],'root_anchor':meta['root_anchor'],'frames':{},'endpoints':{},'hold_difference':{},
     'diagnostic_sha256':{},'joint_roi_half_open':[12,39,50,82],'bound_author_evidence':{}}
frames={}
for direction in ['down_left']+dirs:
    frames[direction]={}
    for action in ['idle','collect']:
        clip=next(c for c in meta['clips'] if c['direction']==direction and c['action']==action)
        frames[direction][action]=[]
        for item in clip['frames']:
            im=Image.open(package/item['file']).convert('RGBA')
            assert im.size==(64,96) and set(im.getchannel('A').tobytes())=={0,255}
            x,y,w,h=item['region']
            assert atlas.crop((x,y,x+w,y+h)).tobytes()==im.tobytes()
            assert sha(package/item['file'])==item['sha256']
            frames[direction][action].append(im)
            out['frames'][item['file']]={'sha256':item['sha256'],'canvas':[64,96],'atlas_region_rgba_same':True,'scope':'C2_new' if direction in dirs else 'approved_C1_reference'}
    idle=frames[direction]['idle'];collect=frames[direction]['collect']
    out['endpoints'][direction]={'collect_f03_equals_idle_f00':collect[3].tobytes()==idle[0].tobytes()}
    changed=[(x,y) for y in range(96) for x in range(64) if collect[1].getpixel((x,y))!=collect[2].getpixel((x,y))]
    out['hold_difference'][direction]={'rgba_pixels':len(changed),'bbox_half_open':[min(x for x,y in changed),min(y for x,y in changed),max(x for x,y in changed)+1,max(y for x,y in changed)+1] if changed else None}
colors={'light':(232,232,228,255),'dark':(25,42,52,255)}
for direction in dirs:
    six=frames[direction]['idle']+frames[direction]['collect']
    labels=['idle F00','idle F01','collect F00','collect F01','collect F02','collect F03']
    for color,bg in colors.items():
        ink=(20,20,20,255) if color=='light' else (240,240,240,255)
        for kind,roi,scale in [('full',(0,0,64,96),4),('joints',tuple(out['joint_roi_half_open']),8)]:
            w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
            chart=Image.new('RGBA',(w*6,h+24),bg);draw=ImageDraw.Draw(chart)
            for n,(im,label) in enumerate(zip(six,labels)):
                draw.text((n*w+4,4),label,fill=ink)
                chart.alpha_composite(im.crop(roi).resize((w,h),Image.Resampling.NEAREST),(n*w,24))
            p=base/f'visual-{kind}-{direction}-{color}-{scale}x.png';chart.convert('RGB').save(p)
            out['diagnostic_sha256'][p.name]=sha(p)
for color,bg in colors.items():
    ink=(20,20,20,255) if color=='light' else (240,240,240,255)
    chart=Image.new('RGBA',(484,696),bg);draw=ImageDraw.Draw(chart)
    for row,direction in enumerate(dirs):
        draw.text((4,24+row*96),direction,fill=ink)
        for col,im in enumerate(frames[direction]['idle']+frames[direction]['collect']):
            draw.text((104+col*64,4),['I00','I01','C00','C01','C02','C03'][col],fill=ink)
            chart.alpha_composite(im,(100+col*64,24+row*96))
    p=base/f'visual-new42-native-{color}-1x.png';chart.convert('RGB').save(p);out['diagnostic_sha256'][p.name]=sha(p)
    # Approved SW collect is juxtaposed with S/N and two side views on identical full canvases.
    chart=Image.new('RGBA',(1084,2040),bg);draw=ImageDraw.Draw(chart)
    for row,direction in enumerate(['down_left','down','up','left','right']):
        draw.text((4,row*408+4),direction,fill=ink)
        for n,im in enumerate(frames[direction]['collect']):
            draw.text((64+n*256,row*408+4),f'F{n:02}',fill=ink)
            chart.alpha_composite(im.resize((256,384),Image.Resampling.NEAREST),(60+n*256,row*408+24))
    p=base/f'visual-c1-sw-new-collect-comparison-{color}-4x.png';chart.convert('RGB').save(p);out['diagnostic_sha256'][p.name]=sha(p)
for name in ['qa/export_validation_full_actions.json','qa/godot_full_actions_v011.json','qa/visual-review-c2-rc01.json','run-manifest.json','eight_way_action_contract_v011.json']:
    out['bound_author_evidence'][name]=sha(package/name)
(base/'visual-binding.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'bytes':out['bytes'],'members':len(members),'manifest':len(manifest['files']),'new_frames':42,'reference_frames':6,'endpoints':out['endpoints'],'diagnostics':len(out['diagnostic_sha256'])}))
