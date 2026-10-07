"""C24 视觉审查只读冻结 ZIP，固定画布诊断并绑定所有实际观看帧。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image,ImageDraw
import json,hashlib
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
zp=ROOT/'art-source/ember/deliveries/enemy_cutter_attack_death_v024_v001_2026-10-07.zip'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(zp.read_bytes())=='c3c1d9fb84d909fb113ee0a9d7ddac6afa98b8132f669ae0f5be5fa0963d572c'
assert zp.stat().st_size==3802515
z=ZipFile(zp);assert z.testzip() is None
cat=json.loads(z.read('output/catalog.json'));spec=json.loads(z.read('rig.json'))
assert sha(z.read('output/catalog.json'))=='444e71fa6255dc25e5eb824a882c58bb07f94ba444364df20eac1039b1e99a7c'
im=lambda n:Image.open(BytesIO(z.read(n))).convert('RGBA')
dirs=['down_left','left','up_left','up','up_right','right','down_right']
report={'zip_sha256':sha(zp.read_bytes()),'catalog_sha256':sha(z.read('output/catalog.json')),'new_frames':{},'sources':{},'boundaries':{},'diagnostics':{},'scope':'All98 new frames static native/light-dark4x; focused ROI and source comparison; root owns actual browser playback'}
frames={}
roi=(24,50,104,110)
for d in dirs:
    src=im('source/'+d+'.png');report['sources'][d]=sha(z.read('source/'+d+'.png'));frames[d]={}
    for act in ['attack','death']:
        clip=next(c for c in cat['clips'] if c['direction']==d and c['action']==act+'_'+d)
        atlas_path=clip['atlas'].removeprefix('res://')
        atlas=im(atlas_path);assert sha(z.read(atlas_path))==clip['atlas_sha256']
        collection=[]
        for n in range(clip['frame_count']):
            path=f'output/enemy_cutter/{act}_{d}/f{n:02}.png';a=im(path)
            assert a.size==(128,128) and sha(z.read(path))==clip['frame_hashes'][n]
            assert atlas.crop((128*n,0,128*(n+1),128)).tobytes()==a.tobytes()
            bbox=a.getbbox();assert bbox[0]>=roi[0] and bbox[1]>=roi[1] and bbox[2]<=roi[2] and bbox[3]<=roi[3]
            collection.append(a);report['new_frames'][path]={'sha256':sha(z.read(path)),'bbox_half_open':bbox,'atlas_rgba_same':True}
        frames[d][act]=collection
    report['boundaries'][d]={'attack00_source':frames[d]['attack'][0].tobytes()==src.tobytes(),'attack05_source':frames[d]['attack'][5].tobytes()==src.tobytes(),'death00_source':frames[d]['death'][0].tobytes()==src.tobytes(),'death05_06_07_same':len({a.tobytes() for a in frames[d]['death'][5:]})==1}
def sheet(name,items,cols,roi,scale,bg):
    w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale;rows=(len(items)+cols-1)//cols
    a=Image.new('RGBA',(cols*w,rows*(h+24)),bg);dr=ImageDraw.Draw(a)
    for i,(label,frame) in enumerate(items):
        x,y=i%cols*w,i//cols*(h+24);dr.text((x+3,y+3),label,fill=(20,20,20,255) if bg[0]>100 else (240,240,240,255))
        a.alpha_composite(frame.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
    a.convert('RGB').save(OUT/name);report['diagnostics'][name]={'sha256':sha((OUT/name).read_bytes()),'roi_half_open':roi,'scale':scale,'labels':[x[0] for x in items]}
for bgname,bg in [('light',(238,238,238,255)),('dark',(8,11,16,255))]:
    for act,count in [('attack',6),('death',8)]:
        for group,subset in enumerate([dirs[:4],dirs[4:]],1):
            sheet(f'visual-{act}-all-native-{bgname}-p{group}.png',[(f'{d} F{n:02}',a) for d in subset for n,a in enumerate(frames[d][act])],count,(0,0,128,128),1,bg)
        for d in dirs:
            sheet(f'visual-{act}-{d}-{bgname}-4x.png',[(f'{d} F{n:02}',a) for n,a in enumerate(frames[d][act])],3 if act=='attack' else 4,roi,4,bg)
    sheet(f'visual-sources-{bgname}-4x.png',[(d,im('source/'+d+'.png')) for d in dirs],4,roi,4,bg)
assert len(report['new_frames'])==98
(OUT/'visual-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'new_frames':len(report['new_frames']),'diagnostics':len(report['diagnostics']),'boundaries':report['boundaries']}))
