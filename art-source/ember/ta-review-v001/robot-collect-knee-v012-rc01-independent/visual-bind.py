"""只从冻结 ZIP 绑定并组合视觉证据，固定坐标最近邻展示。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image,ImageDraw
import hashlib,json
out=Path(__file__).resolve().parent;root=out.parents[3]
zp=root/'art-source/ember/deliveries/robot_collect_knee_v012_rc01_2026-10-07.zip'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(zp.read_bytes())=='4dc7298a4b1f3782635bd461eca6dc2be1179e79b35dc4ecfa7ac04a6030f209'
assert zp.stat().st_size==14181428
z=ZipFile(zp);assert z.testzip() is None
meta=json.loads(z.read('comparison-metadata.json'));ledger=json.loads(z.read('source/imagegen-ledger.json'))
read=lambda n:Image.open(BytesIO(z.read(n))).convert('RGBA')
report={'zip_sha256':sha(zp.read_bytes()),'frames':{},'diagnostics':{},'source_ledger':[]}
frames={}
def sheet(name,items,cols,roi,scale,bg):
    w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
    img=Image.new('RGBA',(cols*w,((len(items)+cols-1)//cols)*(h+22)),bg);dr=ImageDraw.Draw(img)
    for i,(label,a) in enumerate(items):
        x,y=i%cols*w,i//cols*(h+22)
        dr.text((x+2,y+2),label,fill='black' if bg[0]>100 else 'white')
        img.alpha_composite(a.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+22))
    img.convert('RGB').save(out/name)
    report['diagnostics'][name]={'sha256':sha((out/name).read_bytes()),'roi_half_open':roi,'scale':scale,'labels':[l for l,a in items]}
for m in meta:
    d=m['direction'];frames[d]={'old':[],'new':[]}
    for kind,paths in [('old',m['before']),('new',m['after'])]:
        for n,p in enumerate(paths):
            a=read(p);assert a.size==(64,96)
            if kind=='new':assert z.read(p)==z.read('runtime/'+p)
            frames[d][kind].append(a)
            report['frames'][p]={'sha256':sha(z.read(p)),'bbox_half_open':a.getbbox(),'runtime_same_bytes':True if kind=='new' else None}
for mode,bg in [('light',(236,233,216,255)),('dark',(24,38,49,255))]:
    for d,f in frames.items():
        items=[(f'{d} {kind} F{n}',a) for kind in ['old','new'] for n,a in enumerate(f[kind])]
        sheet(f'visual-{d}-before-after-{mode}-4x.png',items,4,(0,0,64,96),4,bg)
        sheet(f'visual-{d}-hip-knee-ankle-{mode}-6x.png',items,4,(12,48,53,84),6,bg)
    dirs=list(frames)
    for group,subset in enumerate([dirs[:4],dirs[4:]],1):
        items=[(f'{d} {kind} F{n}',a) for d in subset for kind in ['old','new'] for n,a in enumerate(frames[d][kind])]
        sheet(f'visual-native-before-after-{mode}-p{group}.png',items,4,(0,0,64,96),1,bg)
for rec in ledger:
    d=rec['direction'];src=read(rec['source']);inp=read(rec['actual_input'])
    assert sha(z.read(rec['source']))==rec['source_sha256'] and sha(z.read(rec['actual_input']))==rec['input_sha256']
    assert sha(z.read(rec['prompt']))==rec['prompt_sha256']
    report['source_ledger'].append({'direction':d,'source_sha256':rec['source_sha256'],'input_sha256':rec['input_sha256'],'source_size':src.size,'input_size':inp.size})
    src=src.resize((128,192),Image.Resampling.NEAREST).crop((64,0,128,96))
    inp=inp.resize((128,192),Image.Resampling.NEAREST).crop((64,0,128,96))
    raw=read(f'source/{d}/fixed_support_raw_f1.png')
    items=[(d+' input F1',inp),(d+' generated F1',src),(d+' fixed raw F1',raw),(d+' final F1',frames[d]['new'][1])]
    for mode,bg in [('light',(236,233,216,255)),('dark',(24,38,49,255))]:sheet(f'visual-source-{d}-{mode}-6x.png',items,4,(12,43,53,81),6,bg)
legacy_path=root/'art-source/ember/deliveries/robot_eight_way_v011_final_2026-10-07.zip'
assert sha(legacy_path.read_bytes())=='8dc65a715b41b2c61a09eb6e2afbcd31134db60228f4b3081a0a39e4d153f4bb'
legacy=ZipFile(legacy_path);report['legacy_baseline_binding']={}
for d in frames:
    checks=[]
    for n in range(4):
        oldpath=f'frames/collect/{d}/robot_collect_{d}_f{n:02}_v011.png'
        baseline=f'source/{d}/baseline_f{n}.png'
        assert z.read(baseline)==legacy.read(oldpath)
        checks.append({'frame':n,'legacy_path':oldpath,'baseline_same_bytes':True,'endpoints_same_bytes':z.read(f'frames/collect/{d}/robot_collect_{d}_f{n:02}_v012.png')==legacy.read(oldpath) if n in [0,3] else None})
    report['legacy_baseline_binding'][d]=checks
for d in ['down','up','up_left','down_right']:
    raw=read(f'source/{d}/fixed_support_raw_f1.png')
    items=[(d+' neutral F0',frames[d]['new'][0]),(d+' fixed raw F1',raw),(d+' final F1',frames[d]['new'][1]),(d+' final F2',frames[d]['new'][2])]
    for mode,bg in [('light',(236,233,216,255)),('dark',(24,38,49,255))]:sheet(f'visual-waist-{d}-{mode}-8x.png',items,4,(17,48,47,70),8,bg)
(out/'visual-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'bound_old_new_frames':len(report['frames']),'diagnostics':len(report['diagnostics']),'sources':len(report['source_ledger'])}))
