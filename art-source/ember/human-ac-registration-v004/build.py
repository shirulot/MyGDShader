"""修正动画绘制坐标。源图集字节不变，不重画、缩放或形变角色。"""
from pathlib import Path
from PIL import Image, ImageDraw
import json, shutil, hashlib, statistics

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'human-ac-expanded-v003'
landmarks=json.loads((ROOT/'waist-landmarks.json').read_text(encoding='utf-8'))
catalog=json.loads((BASE/'catalog.json').read_text(encoding='utf-8'))
for folder in ['final','qa','previews']:(ROOT/folder).mkdir(exist_ok=True)
audit=[]
for clip in catalog['clips']:
    key=clip['key'];n=clip['frame_count'];source=BASE/clip['atlas'];dest=ROOT/clip['atlas']
    shutil.copy2(source,dest)
    assert source.read_bytes()==dest.read_bytes()
    offsets=[[0,0] for _ in range(n)]
    if key in landmarks:
        xs,ys=landmarks[key]
        # 腰部的平均高度保持原动作登记；两个半步共用周期起伏，移除排版换行跳变。
        center=round(statistics.median(ys))
        if clip['action']=='idle':target_y=[center]*n
        else:
            half=[(ys[i]+ys[i+4])/2 for i in range(4)]
            cap=1 if clip['action']=='walk' else 2
            mean=statistics.mean(half)
            half=[center+max(-cap,min(cap,round(v-mean))) for v in half]
            target_y=half*2
        offsets=[[32-xs[i],target_y[i]-ys[i]] for i in range(n)]
        clip['waist_landmarks']=[[xs[i],ys[i]] for i in range(n)]
        clip['waist_targets']=[[32,target_y[i]] for i in range(n)]
        audit.append({'key':key,'before_waist_x_range':max(xs)-min(xs),'after_waist_x_range':0,'before_waist_y_range':max(ys)-min(ys),'after_waist_y_range':max(target_y)-min(target_y),'max_translation':max(max(abs(x),abs(y)) for x,y in offsets)})
    else:assert clip['direction']=='left'
    clip['draw_offsets']=offsets
    clip['registration']='manual waist/pelvis landmarks; integer translation only' if key in landmarks else 'v003 left unchanged'
    clip['production_ready']=False
    atlas=Image.open(dest).convert('RGBA');frames=[];before=[]
    for i,(dx,dy) in enumerate(offsets):
        frame=atlas.crop((64*i,0,64*(i+1),96));box=frame.getbbox()
        assert box[0]+dx>=-16 and box[1]+dy>=0 and box[2]+dx<=80 and box[3]+dy<=96,(key,i,box,dx,dy)
        original=Image.new('RGBA',(96,96));original.paste(frame,(16,0));before.append(original)
        # 此处仅模拟运行时绘制位置，用于联系图和动图；生产PNG维持原样。
        rendered=Image.new('RGBA',(96,96));rendered.paste(frame,(16+dx,dy));frames.append(rendered)
    for label,fs in [('before',before),('registered',frames)]:
        strip=Image.new('RGBA',(96*n,96))
        for i,im in enumerate(fs):strip.paste(im,(96*i,0))
        strip.resize((96*n*3,288),Image.Resampling.NEAREST).save(ROOT/'qa'/f'{key}-{label}.png')
    # 一张动图并列展示同相位前后，不改变帧时长。
    animation=[]
    for i in range(n):
        b=Image.new('RGB',(768,408),(24,38,49));d=ImageDraw.Draw(b)
        d.text((8,6),'v003',fill='white');d.text((392,6),'v004 registration',fill='white')
        for column,im in enumerate([before[i],frames[i]]):
            up=im.resize((384,384),Image.Resampling.NEAREST);b.paste(up,(column*384,24),up)
            d.line((column*384+192,24,column*384+192,407),fill=(79,97,103))
        animation.append(b)
    animation[0].save(ROOT/'previews'/f'{key}-compare.webp',save_all=True,append_images=animation[1:],duration=clip['duration_ms'],loop=0,lossless=True)
    (ROOT/'final'/f'{key}.json').write_text(json.dumps(clip,ensure_ascii=False,indent=2),encoding='utf-8')

catalog['registration_version']='v004';catalog['production_ready']=False
(ROOT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
report={'status':'registration_corrected_visual_review_pending','changed_clips':len(audit),'unchanged_left_clips':len(catalog['clips'])-len(audit),'png_bytes_unchanged':True,'frame_order_and_timing_unchanged':True,'clipping_checks':'pass','source_art_revision':False,'limits':['手工腰部标记存在约1-2像素读数误差。','登记点消除全身平移；源图中的转身、体态和比例变化仍存在。','不得只用PNG而忽略draw_offsets；此版本不宣称动作整体通过验收。'],'clips':audit}
(ROOT/'qa'/'registration-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'changed_clips':len(audit),'max_shift':max(c['max_translation'] for c in audit),'atlas_bytes_unchanged':True}))
