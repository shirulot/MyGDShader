"""从固定包取证：逐帧绑定、时序/事件、可見安装与残骸联系图；不运行 Godot。"""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import hashlib
import json
import math
from collections import Counter
from PIL import Image, ImageDraw

ROOT=Path('E:/dev/shader/godot-shader/godot-shader-simple')
OUT=Path(__file__).resolve().parent
ZIP=ROOT/'art-source/ember/deliveries/enemy_heavy_actions_v009_2026-10-06.zip'
EXPECTED='329e2fb60b0e7930a5178e92b4fe014e526bc5aa771f1a8b53e69eee8b15bf18'
def sha(data): return hashlib.sha256(data).hexdigest()
def pixels(img): return list(img.get_flattened_data())
def diff(a,b):
    assert a.size==b.size
    return sum(x!=y for x,y in zip(pixels(a),pixels(b)))
def visible_diff(a,b):
    return sum((x[3]>=128)!=(y[3]>=128) or (x[:3]!=y[:3] and (x[3]>=128 or y[3]>=128)) for x,y in zip(pixels(a),pixels(b)))
def inside(point,poly):
    x,y=point;result=False
    for index,a in enumerate(poly):
        b=poly[(index+1)%len(poly)]
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: result=not result
    return result
assert sha(ZIP.read_bytes())==EXPECTED
with ZipFile(ZIP) as package:
    files=[e for e in package.infolist() if not e.is_dir()]
    assert len(files)==len({e.filename for e in files})
    folder=OUT/'package'
    for entry in files:
        target=(folder/entry.filename).resolve()
        assert target.is_relative_to(folder.resolve())
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(package.read(entry))
    catalog=json.loads(package.read('output/catalog_v009.json'))
    rig=json.loads(package.read('rig.json'))
    canonical=Image.open(BytesIO(package.read('source/canonical.png'))).convert('RGBA')
    hidden=Image.open(BytesIO(package.read('source/hidden_chassis_master.png'))).convert('RGBA')
    report={'zip_sha256':EXPECTED,'zip_bytes':ZIP.stat().st_size,'entries':len(files),'catalog_sha256':sha(package.read('output/catalog_v009.json')),'rig_sha256':sha(package.read('rig.json')),'root':rig['root'],'actions':{},'frames':[]}
    report['canonical_comparison_contract']={
        'source_path':'package/source/canonical.png',
        'source_sha256':sha(package.read('source/canonical.png')),
        'source_read_method':'Raw PNG RGBA via Pillow convert(RGBA); alpha was not quantized or changed in memory.',
        'source_alpha_histogram':dict(sorted(Counter(p[3] for p in pixels(canonical)).items())),
        'raw_rgba_difference':'Compare all four original bytes; no coverage conversion.',
        'effective_visible_difference':'Compare RGB only where alpha >= 128 and compare this binary coverage, matching the declared shader cutoff=0.5; this is not raw RGBA equality.',
        'output_alpha_contract':'Output frames independently verified binary alpha {0,255}.'
    }
    for action,definition in catalog['actions'].items():
        frames=[]
        atlas=Image.open(BytesIO(package.read(definition['atlas'].removeprefix('res://')))).convert('RGBA')
        assert sha(package.read(definition['atlas'].removeprefix('res://')))==definition['atlas_sha256']
        assert definition['fps']==10 and definition['loop'] is False
        report['actions'][action]={'fps':definition['fps'],'loop':definition['loop'],'frame_count':definition['frame_count'],'poses':definition['poses'],'visual_events':definition.get('visual_events',definition.get('events',[]))}
        for index in range(definition['frame_count']):
            raw=package.read(f'output/{action}/f{index:02d}.png')
            assert sha(raw)==definition['frame_hashes'][index]
            img=Image.open(BytesIO(raw)).convert('RGBA')
            assert img.size==(128,128)
            assert set(img.getchannel('A').get_flattened_data())=={0,255}
            assert diff(img,atlas.crop((index*128,0,(index+1)*128,128)))==0
            track_changed=0
            outer_track_changed=0
            for y in range(128):
                for x in range(128):
                    if (y<66 and (x<46 or x>=82)) or (y>=66 and (x<49 or x>=79)):
                        a=img.getpixel((x,y));b=canonical.getpixel((x,y))
                        track_changed+=int((a[3]>=128)!=(b[3]>=128) or (a[:3]!=b[:3] and (a[3]>=128 or b[3]>=128)))
                    if x<46 or x>=82:
                        a=img.getpixel((x,y));b=canonical.getpixel((x,y))
                        outer_track_changed+=int((a[3]>=128)!=(b[3]>=128) or (a[:3]!=b[:3] and (a[3]>=128 or b[3]>=128)))
            assert outer_track_changed==0
            pose=definition['poses'][index]
            hidden_points=[]
            for y in range(78,98):
                for x in range(48,80):
                    if canonical.getpixel((x,y))[3]<128: continue
                    covered=False
                    for part in rig['parts']:
                        transform=pose['part_transforms'][part['id']]
                        dx=x+0.5-transform['position'][0];dy=y+0.5-transform['position'][1]
                        # 旋转正交基的转置就是逆；映回同一原生源像素中心。
                        sx=dx*transform['basis_x'][0]+dy*transform['basis_x'][1]+part['pivot'][0]
                        sy=dx*transform['basis_y'][0]+dy*transform['basis_y'][1]+part['pivot'][1]
                        if inside((sx,sy),part['polygon']) and 0<=sx<128 and 0<=sy<128 and canonical.getpixel((int(sx),int(sy)))[3]>=128:
                            covered=True;break
                    if not covered and img.getpixel((x,y))[3]>=128:
                        # 这里只定位新增底座实际显露区域；独立技术审计负责完整栅格源重建。
                        hidden_points.append([x,y])
            hidden_bbox=[min(p[0] for p in hidden_points),min(p[1] for p in hidden_points),max(p[0] for p in hidden_points)+1,max(p[1] for p in hidden_points)+1] if hidden_points else None
            report['frames'].append({'action':action,'frame':index,'sha256':sha(raw),'bounds':img.getbbox(),'visible_pixels':sum(p[3]>0 for p in pixels(img)),'bottom_y102_103_visible_changed_vs_canonical':visible_diff(img.crop((0,102,128,104)),canonical.crop((0,102,128,104))),'track_source_region_visible_changed_vs_canonical':track_changed,'track_source_region_difference_meaning':'Includes dynamic tower covering the inner 3px mounting seam; not by itself track deformation.','outer_track_region_visible_changed_vs_canonical':outer_track_changed,'hidden_chassis_exposed_points':hidden_points,'hidden_chassis_exposed_bbox':hidden_bbox})
            frames.append(img)
        report['actions'][action]['f00_changed_vs_canonical']=diff(frames[0],canonical)
        report['actions'][action]['f00_visible_changed_vs_canonical']=visible_diff(frames[0],canonical)
        report['actions'][action]['last_frame_changed_vs_canonical']=diff(frames[-1],canonical)
        report['actions'][action]['last_frame_visible_changed_vs_canonical']=visible_diff(frames[-1],canonical)
        report['actions'][action]['last_two_equal']=diff(frames[-1],frames[-2])==0
        report['actions'][action]['first_last_rgba_difference']=diff(frames[0],frames[-1])
        report['actions'][action]['neutral_only_alpha0_hidden_rgb_difference']=sum(a!=b and a[3]==b[3]==0 for a,b in zip(pixels(frames[0]),pixels(canonical)))
        report['actions'][action]['neutral_raw_alpha_difference']=sum(a[3]!=b[3] for a,b in zip(pixels(frames[0]),pixels(canonical)))
        report['actions'][action]['neutral_effective_coverage_difference']=sum((a[3]>=128)!=(b[3]>=128) for a,b in zip(pixels(frames[0]),pixels(canonical)))
        report['actions'][action]['neutral_effective_rgb_difference']=sum(a[:3]!=b[:3] and (a[3]>=128 or b[3]>=128) for a,b in zip(pixels(frames[0]),pixels(canonical)))
        assert report['actions'][action]['f00_changed_vs_canonical']==report['actions'][action]['neutral_raw_alpha_difference']+report['actions'][action]['neutral_only_alpha0_hidden_rgb_difference']
        assert report['actions'][action]['neutral_raw_alpha_difference']==3200
        assert report['actions'][action]['neutral_only_alpha0_hidden_rgb_difference']==1195
        assert report['actions'][action]['neutral_effective_coverage_difference']==report['actions'][action]['neutral_effective_rgb_difference']==0
        for background,color in [('light',(248,247,244,255)),('dark',(32,41,48,255))]:
            for zoom in [1,4]:
                # 完整原生画布不按各帧bbox居中；所有帧保持同一坐标。
                cols=4
                rows=(len(frames)+cols-1)//cols
                step=128*zoom
                sheet=Image.new('RGB',(step*cols,rows*(step+22)),color[:3])
                draw=ImageDraw.Draw(sheet)
                for index,img in enumerate(frames):
                    mat=Image.new('RGBA',(128,128),color)
                    mat.alpha_composite(img)
                    mat=mat.convert('RGB').resize((step,step),Image.Resampling.NEAREST)
                    x=(index%cols)*step;y=(index//cols)*(step+22)
                    sheet.paste(mat,(x,y+22))
                    draw.text((x+4,y+5),f'{action} f{index:02d}',fill=(30,38,44) if background=='light' else (245,243,233))
                sheet.save(OUT/f'{action}_{background}_{zoom}x.png')
            roi=(43,68,85,106)
            cols=4;rows=(len(frames)+3)//4;stepx=(roi[2]-roi[0])*8;stepy=(roi[3]-roi[1])*8
            sheet=Image.new('RGB',(stepx*cols,rows*(stepy+22)),color[:3])
            draw=ImageDraw.Draw(sheet)
            for index,img in enumerate(frames):
                cut=img.crop(roi);mat=Image.new('RGBA',cut.size,color);mat.alpha_composite(cut)
                mat=mat.convert('RGB').resize((stepx,stepy),Image.Resampling.NEAREST)
                x=(index%cols)*stepx;y=(index//cols)*(stepy+22)
                sheet.paste(mat,(x,y+22));draw.text((x+4,y+5),f'f{index:02d}',fill=(30,38,44) if background=='light' else (245,243,233))
            sheet.save(OUT/f'{action}_mounts_{background}_8x.png')
    assert len(report['frames'])==14
(OUT/'action-binding-evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'zip_bytes':report['zip_bytes'],'entries':report['entries'],'frames':len(report['frames']),'catalog_sha256':report['catalog_sha256'],'neutral_and_end':{k:{x:v[x] for x in ['f00_changed_vs_canonical','f00_visible_changed_vs_canonical','last_frame_changed_vs_canonical','last_frame_visible_changed_vs_canonical','last_two_equal']} for k,v in report['actions'].items()},'hidden_visible':[{k:f[k] for k in ['action','frame','hidden_chassis_exposed_bbox','track_source_region_visible_changed_vs_canonical']} for f in report['frames']]},ensure_ascii=False))
