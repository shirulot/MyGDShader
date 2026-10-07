"""将生图切片、按固定比例缩放和注册，导出动作预览；不绘制肢体或补画关节。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
import json,hashlib,zipfile
from inspect_sources import regions
ROOT=Path(__file__).resolve().parent
for d in ('frames','final','previews','qa'):(ROOT/d).mkdir(exist_ok=True)
# 每个动作只使用一个缩放比例；跑动保留源稿中的离地高度。
SCALES={'A-idle':66/789,'C-idle':66/786,'A-walk':66/577,'C-walk':66/578,'A-run':.135,'C-run':.135}
DUR={'idle':180,'walk':120,'run':80}
COLORS=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','ECE9D8','7B4D35','B77C4B','E2B77A','B9947B','D7B59B','EAC5A0','3A3436','635754','9B8170','F2D9B8','AAB7B1']
PAL=np.array([list(bytes.fromhex(c)) for c in COLORS],dtype=np.int32)
allframes={};reports=[]
for key,scale in SCALES.items():
    src=np.array(Image.open(ROOT/'source'/f'{key}.png').convert('RGBA'))
    groups=regions(src[:,:,3]>=210);expected=4 if key.endswith('idle') else 8
    assert len(groups)==expected,(key,len(groups))
    baseline=max(g['bbox'][3] for g in groups);frames=[];records=[]
    folder=ROOT/'frames'/key;folder.mkdir(exist_ok=True)
    for i,g in enumerate(groups):
        x0,y0,x1,y1=g['bbox'];pts=g['points']
        # 以源稿连通区域切片，不按均分列切断伸出的手脚。
        tile=np.zeros((y1-y0,x1-x0,4),dtype=np.uint8)
        tile[pts[:,1]-y0,pts[:,0]-x0]=src[pts[:,1],pts[:,0]]
        tile[:,:,3]=np.where(tile[:,:,3]>=210,255,0)
        # 髋部附近实体像素的横向中位数作根定位；保留源稿步幅和上下运动。
        band=pts[(pts[:,1]>=y0+(y1-y0)*.46)&(pts[:,1]<y0+(y1-y0)*.51)]
        anchor=float(np.median(band[:,0]))
        im=Image.fromarray(tile).transform((64,96),Image.Transform.AFFINE,(1/scale,0,anchor-x0-32/scale,0,1/scale,baseline-y0-80/scale),Image.Resampling.NEAREST)
        arr=np.array(im);on=arr[:,:,3]>0;rgb=arr[:,:,:3][on].astype(np.int32)
        nearest=((rgb[:,None,:]-PAL[None,:,:])**2).sum(axis=2).argmin(axis=1)
        arr[:,:,:3][on]=PAL[nearest].astype(np.uint8);arr[:,:,3]=on.astype(np.uint8)*255
        # 小画布直接统计所有四邻域连通分量，不把连通性等同于解剖正确。
        remaining=set(zip(*np.where(on)));counts=[];removed=0
        while remaining:
            todo=[remaining.pop()];n=0;component=[]
            while todo:
                y,x=todo.pop();n+=1;component.append((y,x))
                for pt in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if pt in remaining:remaining.remove(pt);todo.append(pt)
            if n==1:
                # 只清理缩采样产生的单像素浮点；不补画或改变主体。
                y,x=component[0];arr[y,x]=(0,0,0,0);removed+=1
            else: counts.append(n)
        im=Image.fromarray(arr);im.save(folder/f'f{i:02d}.png');frames.append(im)
        box=im.getbbox();assert box and box[0]>0 and box[2]<64 and box[1]>0 and box[3]<96,(key,i,box)
        records.append({'frame':i,'source_bbox':g['bbox'],'source_anchor_x':anchor,'bbox':box,'components_4':sorted(counts,reverse=True),'isolated_pixels_removed':removed,'duration_ms':DUR[key.split('-')[1]]})
    allframes[key]=frames
    sheet=Image.new('RGBA',(64*expected,96))
    for i,im in enumerate(frames):sheet.paste(im,(64*i,0))
    sheet.save(ROOT/'final'/f'{key}.png')
    sheet.resize((64*expected*3,288),Image.Resampling.NEAREST).save(ROOT/'qa'/f'{key}-contact.png')
    large=[im.resize((256,384),Image.Resampling.NEAREST) for im in frames]
    for speed,mult in [('normal',1),('slow',3)]:
        ms=DUR[key.split('-')[1]]*mult
        large[0].save(ROOT/'previews'/f'{key}-{speed}.webp',save_all=True,append_images=large[1:],duration=ms,loop=0,lossless=True)
        # GIF 的透明索引独立保留；不向生产 PNG 添加背景。
        gifframes=[];dark=[]
        for im in large:
            pi=im.convert('RGB').quantize(colors=254);mask=im.getchannel('A').point(lambda a:255 if a==0 else 0);pi.paste(255,mask=mask);pi.info['transparency']=255;gifframes.append(pi)
            bg=Image.new('RGBA',im.size,'#182631');bg.alpha_composite(im);dark.append(bg.convert('RGB'))
        gifframes[0].save(ROOT/'previews'/f'{key}-{speed}-transparent.gif',save_all=True,append_images=gifframes[1:],duration=ms,loop=0,transparency=255,disposal=2)
        dark[0].save(ROOT/'previews'/f'{key}-{speed}.gif',save_all=True,append_images=dark[1:],duration=ms,loop=0,disposal=2)
    metadata={'character':key[0],'action':key.split('-')[1],'direction':'left','cell':[64,96],'root':[32,80],'frame_count':expected,'duration_ms':DUR[key.split('-')[1]],'loop':True,'frames':records}
    (ROOT/'final'/f'{key}.json').write_text(json.dumps(metadata,indent=2))
    reports.append({'key':key,'scale':scale,'baseline_source':baseline,**metadata})
qa={'status':'VISUAL_TRIAL_NOT_PRODUCTION_APPROVED','total_frames':sum(len(v) for v in allframes.values()),'palette':COLORS,'source_method':'imagegen; connected-component slicing, fixed-scale nearest resampling, shared palette and registration only','actions':reports,'limitations':['Generated gait is an approximation, not exact Dead Revolver pose matching.','Connectivity is not proof of correct knee or foot motion.','High-resolution source resized to 64x96; not native-authored sprite art.']}
(ROOT/'qa/validation.json').write_text(json.dumps(qa,indent=2))
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
overview=[]
for tick in range(72):
    board=Image.new('RGB',(960,740),'#101820');d=ImageDraw.Draw(board)
    for row,ch in enumerate(('A','C')):
        for col,(act,name) in enumerate((('idle','待机'),('walk','行走'),('run','跑动'))):
            x=col*320;y=row*370;frames=allframes[f'{ch}-{act}'];idx=(tick*40//DUR[act])%len(frames)
            d.rectangle((x+8,y+8,x+312,y+362),fill='#182631');d.text((x+24,y+18),f'{ch} · {name}',font=font,fill='#ece9d8')
            im=frames[idx].resize((192,288),Image.Resampling.NEAREST);board.paste(im,(x+64,y+58),im)
    overview.append(board)
overview[0].save(ROOT/'previews/overview.gif',save_all=True,append_images=overview[1:],duration=40,loop=0)
overview[0].save(ROOT/'previews/overview.png')
print(json.dumps({'total_frames':qa['total_frames'],'components':{r['key']:[f['components_4'] for f in r['frames']] for r in reports}}))
