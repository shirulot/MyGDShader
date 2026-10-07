"""C24 v002 只读两冻结 ZIP，独立定位修改帧并制作固定坐标诊断。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image,ImageDraw
import json,hashlib,re
out=Path(__file__).resolve().parent;root=out.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest()
p1=root/'art-source/ember/deliveries/enemy_cutter_attack_death_v024_v001_2026-10-07.zip'
p2=root/'art-source/ember/deliveries/enemy_cutter_attack_death_v024_v002_2026-10-07.zip'
assert sha(p1.read_bytes())=='c3c1d9fb84d909fb113ee0a9d7ddac6afa98b8132f669ae0f5be5fa0963d572c'
assert sha(p2.read_bytes())=='3fc81f650daf58c949f216c4b9a783b03348d9ba11fcf512f7e6f08f92ff80be'
assert p2.stat().st_size==3807029
old,new=ZipFile(p1),ZipFile(p2);assert new.testzip() is None
cat=json.loads(new.read('output/catalog.json'))
assert sha(new.read('output/catalog.json'))=='fd2bf874e376a4ec7194e975a45c3b47a9cbee471ee6a09591b3fb5534f11a70'
def read(z,n):return Image.open(BytesIO(z.read(n))).convert('RGBA')
report={'zip_sha256':sha(p2.read_bytes()),'baseline_zip_sha256':sha(p1.read_bytes()),'frames':{},'sources':{},'diagnostics':{},'changed_frames':0,'changed_pixel_events':0}
changed_clips=set()
for n in new.namelist():
    if re.fullmatch(r'output/enemy_cutter/[^/]+/f\d\d.png',n):
        a,b=read(old,n),read(new,n)
        count=sum(x!=y for x,y in zip(a.getdata(),b.getdata()))
        report['frames'][n]={'old_sha256':sha(old.read(n)),'new_sha256':sha(new.read(n)),'rgba_changed_pixels':count,'same_bytes':old.read(n)==new.read(n)}
        if count:changed_clips.add(n.split('/')[2]);report['changed_frames']+=1;report['changed_pixel_events']+=count
assert len(report['frames'])==112 and report['changed_frames']==59 and report['changed_pixel_events']==11597
for n in new.namelist():
    if n.startswith('source/') and n.endswith('.png'):
        assert new.read(n)==old.read(n);report['sources'][n]=sha(new.read(n))
frames={}
for clip in cat['clips']:
    act=clip['action']
    if act not in changed_clips:continue
    atlas_path=clip['atlas'].removeprefix('res://');atlas=read(new,atlas_path)
    assert sha(new.read(atlas_path))==clip['atlas_sha256']
    arr=[]
    for n in range(clip['frame_count']):
        path=f'output/enemy_cutter/{act}/f{n:02}.png';a=read(new,path)
        assert sha(new.read(path))==clip['frame_hashes'][n]
        assert atlas.crop((n*128,0,(n+1)*128,128)).tobytes()==a.tobytes()
        arr.append(a)
    frames[act]=arr
def sheet(name,items,cols,roi,scale,bg):
    w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
    img=Image.new('RGBA',(w*cols,((len(items)+cols-1)//cols)*(h+24)),bg);dr=ImageDraw.Draw(img)
    for i,(label,a) in enumerate(items):
        x,y=i%cols*w,i//cols*(h+24);dr.text((x+3,y+3),label,fill='black' if bg[0]>100 else 'white')
        img.alpha_composite(a.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
    img.convert('RGB').save(out/name)
    report['diagnostics'][name]={'sha256':sha((out/name).read_bytes()),'roi_half_open':roi,'scale':scale,'labels':[l for l,a in items]}
dirs=['down_left','up_left','up_right','right','down_right']
for mode,bg in [('light',(238,238,238,255)),('dark',(8,11,16,255))]:
    for act,arr in frames.items():
        sheet(f'visual-{act}-{mode}-4x.png',[(f'{act} F{n:02}',a) for n,a in enumerate(arr)],3 if act.startswith('attack') else 4,(24,50,104,110),4,bg)
    for kind in ['attack','death']:
        subset=[(act,arr) for act,arr in frames.items() if act.startswith(kind)]
        for part,block in enumerate([subset[:3],subset[3:]],1):
            sheet(f'visual-{kind}-native-{mode}-p{part}.png',[(f'{act} F{n:02}',a) for act,arr in block for n,a in enumerate(arr)],6 if kind=='attack' else 8,(0,0,128,128),1,bg)
    sheet(f'visual-source-five-{mode}-4x.png',[(d,read(new,f'source/{d}.png')) for d in dirs],3,(24,50,104,110),4,bg)
rois={'down_left':(29,72,59,106),'up_left':(75,65,102,100),'up_right':(70,65,102,102),'right':(66,72,103,108),'down_right':(44,77,76,108)}
for d,roi in rois.items():
    items=[(d+' source',read(new,f'source/{d}.png')),('v001 attack F03',read(old,f'output/enemy_cutter/attack_{d}/f03.png'))]+[(f'v002 attack F{n:02}',frames['attack_'+d][n]) for n in [1,2,3,4]]+[(f'v002 death F{n:02}',frames['death_'+d][n]) for n in [1,3,7]]
    for mode,bg in [('light',(238,238,238,255)),('dark',(8,11,16,255))]:sheet(f'visual-blade-{d}-{mode}-8x.png',items,3,roi,8,bg)
for mode,bg in [('light',(238,238,238,255)),('dark',(8,11,16,255))]:
    items=[(f'v001 N F{n:02}',read(old,f'output/enemy_cutter/attack_up/f{n:02}.png')) for n in range(6)]+[(f'v002 N F{n:02}',a) for n,a in enumerate(frames['attack_up'])]
    sheet(f'visual-n-before-after-{mode}-4x.png',items,6,(32,65,96,106),4,bg)
    sheet(f'visual-n-joints-{mode}-6x.png',[(f'v002 N F{n:02}',a) for n,a in enumerate(frames['attack_up'])],3,(36,73,92,106),6,bg)
(out/'visual-binding.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'modified':report['changed_frames'],'pixel_events':report['changed_pixel_events'],'clips_viewed_with_endpoints':len(frames),'frames_in_changed_clips':sum(map(len,frames.values())),'diagnostics':len(report['diagnostics'])}))
