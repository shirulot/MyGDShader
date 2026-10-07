"""P21 W/E 双腿候选造型专项。仅读固定 ZIP，输出独立诊断，不执行生产器。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image, ImageDraw
import hashlib, json
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
PACK = ROOT/'art-source/ember/enemy-patrol-profile-move-v021-review-v001'
DEL = ROOT/'art-source/ember/deliveries'
zp = DEL/'enemy_patrol_profile_moves_v021_v001_2026-10-07.zip'
oldp = DEL/'enemy_patrol_seven_directions_v013_s002_2026-10-06.zip'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(zp.read_bytes())=='4c907f50f6851787d84e7212a0cd7c64215566baf482a520fde937212db10b61'
assert sha(oldp.read_bytes())=='28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1'
z, old=ZipFile(zp), ZipFile(oldp)
js=lambda n:json.loads(z.read(n))
im=lambda n:Image.open(BytesIO(z.read(n))).convert('RGBA')
ar=lambda n:np.array(im(n))
dirs=['down','down_left','left','up_left','up','up_right','right','down_right']
report={'scope':'W/E identity source and static candidate only; not full manifest, runtime or animation acceptance',
        'zip_sha256':sha(zp.read_bytes()),'zip_bytes':zp.stat().st_size,'s002_zip_sha256':sha(oldp.read_bytes()),'bindings':{},'directions':{},'diagnostics':{}}
names=['README.md','SOURCE_RECEIPT.json','source/far_legs_v002.png','source/far_legs_prompt_v002.txt','source/far_registration.json','register_far.gd','rig.gd','rig.json','qa/bind_original_candidate_2x.png']
names += [f'source/{d}.png' for d in dirs]
names += [f'qa/bind_{d}.png' for d in ['left','right']]
names += [f'source/far_registered_{d}.png' for d in ['left','right','near_left','near_right']]
for n in names:
    assert z.read(n)==(PACK/n).read_bytes()
    report['bindings'][n]=sha(z.read(n))
for d in dirs:
    assert z.read(f'source/{d}.png')==old.read(f'neutral_{d}.png')
report['all_eight_original_sources_same_as_S002_bytes']=True
reg=js('source/far_registration.json')
raw=ar('source/far_legs_v002.png')
assert reg['source_sha256']==sha(z.read('source/far_legs_v002.png'))
report['registration']=reg
report['raw_source_size']=[raw.shape[1],raw.shape[0]]
report['raw_source_alpha_values']=len(np.unique(raw[:,:,3]))
for d,entry in reg['directions'].items():
    assert entry['sha256']==sha(z.read(f'source/far_registered_{d}.png'))
    a=ar(f'source/far_registered_{d}.png');y,x=np.nonzero(a[:,:,3]);report['directions'][d]={'registered_bounds_inclusive':[int(x.min()),int(y.min()),int(x.max()),int(y.max())],'alpha_values':np.unique(a[:,:,3]).tolist()}
yy,xx=np.indices((128,128))
for d in ['left','right']:
    src,bind=ar(f'source/{d}.png'),ar(f'qa/bind_{d}.png')
    diff=np.any(src!=bind,axis=2)
    assert not (diff&~((xx>=50)&(xx<77)&(yy>=78)&(yy<105))).any()
    y,x=np.nonzero(diff)
    report['directions'][d]['bind_changed_RGBA_pixels']=int(diff.sum())
    report['directions'][d]['bind_changed_bounds_inclusive']=[int(x.min()),int(y.min()),int(x.max()),int(y.max())]
    report['directions'][d]['outside_leg_rect_RGBA_diff']=0
    report['directions'][d]['candidate_bind_sha256']=sha(z.read(f'qa/bind_{d}.png'))
    report['directions'][d]['bottom_row_y103_original_opaque_x']=np.flatnonzero(src[103,:,3]>0).tolist()
    report['directions'][d]['bottom_row_y103_candidate_opaque_x']=np.flatnonzero(bind[103,:,3]>0).tolist()
    sample=(66,94) if d=='left' else (59,94)
    x,y=sample
    report['directions'][d]['blue_shin_color_sample']={'xy':sample,'original_RGBA':src[y,x].tolist(),'candidate_RGBA':bind[y,x].tolist(),'interpretation':'Diagnostic examples supporting observed material shift, not a pixel identity acceptance threshold'}

colors={'light':(221,221,221,255),'dark':(8,11,16,255)}
def chart(name,items,cols,roi,scale,bg):
    w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
    rows=(len(items)+cols-1)//cols
    canvas=Image.new('RGBA',(cols*w,rows*(h+24)),bg);draw=ImageDraw.Draw(canvas)
    ink=(20,20,20,255) if bg[0]>100 else (240,240,240,255)
    for i,(label,frame) in enumerate(items):
        x,y=i%cols*w,i//cols*(h+24)
        draw.text((x+4,y+4),label,fill=ink)
        canvas.alpha_composite(frame.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
    canvas.convert('RGB').save(OUT/name)
    report['diagnostics'][name]={'sha256':sha((OUT/name).read_bytes()),'source_roi_half_open':roi,'scale':scale,'labels':[label for label,im in items]}
for color,bg in colors.items():
    chart(f'identity-profile-full-{color}-1x.png',[(f'{d} {typ}',im(f'source/{d}.png' if typ=='old' else f'qa/bind_{d}.png')) for d in ['left','right'] for typ in ['old','candidate']],4,[0,0,128,128],1,bg)
    chart(f'identity-original8-{color}-4x.png',[(d,im(f'source/{d}.png')) for d in dirs],4,[34,45,94,109],4,bg)
    chart(f'identity-profile-old-new-{color}-8x.png',[(f'{d} {typ}',im(f'source/{d}.png' if typ=='old' else f'qa/bind_{d}.png')) for d in ['left','right'] for typ in ['old','candidate']],4,[47,75,79,107],8,bg)
    chart(f'identity-profile-full-{color}-8x.png',[(f'{d} {typ}',im(f'source/{d}.png' if typ=='old' else f'qa/bind_{d}.png')) for d in ['left','right'] for typ in ['old','candidate']],4,[47,48,79,107],8,bg)
    chart(f'identity-registered-near-far-{color}-8x.png',[(d,im(f'source/far_registered_{d}.png')) for d in ['left','near_left','right','near_right']],4,[47,75,79,107],8,bg)
(OUT/'identity-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'old_sources_byte_same':True,'source_dimensions':report['raw_source_size'],'profiles':report['directions'],'diagnostics':len(report['diagnostics'])}))
