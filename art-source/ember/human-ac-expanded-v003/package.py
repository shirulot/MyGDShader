"""仅切片、共同注册和导出 AI 动作；不绘制角色或修补关节。"""
from pathlib import Path
from PIL import Image
import numpy as np
import json, shutil, hashlib
from inspect_sources import regions

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'human-ac-basic-v002'
COLORS=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','ECE9D8','7B4D35','B77C4B','E2B77A','B9947B','D7B59B','EAC5A0','3A3436','635754','9B8170','F2D9B8','AAB7B1']
PAL=np.array([list(bytes.fromhex(c)) for c in COLORS],dtype=np.int32)
DUR={'idle':125,'walk':120,'run':80,'crouch':150,'jump':110,'collect':160,'push':140,'pull':140}
for folder in ['frames','final','previews','qa']:(ROOT/folder).mkdir(exist_ok=True)
catalog=[]
previous={c['key']:c for c in json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))['clips']} if (ROOT/'catalog.json').exists() else {}

def export(key,frames,ms,record):
    ch,action,direction=key.split('-',2)
    folder=ROOT/'frames'/key;folder.mkdir(exist_ok=True)
    atlas=Image.new('RGBA',(64*len(frames),96))
    for i,im in enumerate(frames):
        im.save(folder/f'f{i:02d}.png');atlas.paste(im,(64*i,0))
    atlas.save(ROOT/'final'/f'{key}.png')
    atlas.resize((atlas.width*3,288),Image.Resampling.NEAREST).save(ROOT/'qa'/f'{key}-contact.png')
    seam=Image.new('RGBA',(256,96))
    for i,j in enumerate([len(frames)-2,len(frames)-1,0,1]):seam.paste(frames[j],(64*i,0))
    seam.resize((768,288),Image.Resampling.NEAREST).save(ROOT/'qa'/f'{key}-seam.png')
    large=[im.resize((256,384),Image.Resampling.NEAREST) for im in frames]
    for speed,mult in [('normal',1),('slow',3)]:
        large[0].save(ROOT/'previews'/f'{key}-{speed}.webp',save_all=True,append_images=large[1:],duration=ms*mult,loop=0,lossless=True)
    data={'key':key,'character':ch,'action':action,'direction':direction,'cell':[64,96],'root':[32,80],'frame_count':len(frames),'duration_ms':ms,'loop':True,'atlas':f'final/{key}.png','review':'candidate','production_ready':False,**record}
    (ROOT/'final'/f'{key}.json').write_text(json.dumps(data,indent=2),encoding='utf-8');catalog.append(data)

# 左向已改善的原图逐字节沿用，不把新增动作覆盖到 v002。
for ch in ['A','C']:
    for action in ['idle','walk','run']:
        key=f'{ch}-{action}';md=json.loads((BASE/'final'/f'{key}.json').read_text())
        frames=[Image.open(BASE/'frames'/key/f'f{i:02d}.png').convert('RGBA') for i in range(md['frame_count'])]
        export(key+'-left',frames,md['duration_ms'],{'source_version':'v002 unchanged'})

for file in sorted((ROOT/'source').glob('*.png')):
    if 'rejected' in file.stem or file.stem.endswith('-r2'):continue
    key=file.stem;ch,action,direction=key.split('-',2)
    # 原稿未变时保留上次导出，避免重复处理百万像素连通域。
    digest=hashlib.sha256(file.read_bytes()).hexdigest()
    if previous.get(key,{}).get('source_sha256')==digest and (ROOT/'final'/f'{key}.png').exists():
        catalog.append(previous[key]);continue
    arr=np.array(Image.open(file).convert('RGBA'));h,w=arr.shape[:2]
    groups=regions(arr[:,:,3]>=210)
    if len(groups)!=8:
        print('REJECT_COMPONENT_COUNT',key,len(groups));continue
    groups.sort(key=lambda g:((g['bbox'][1]+g['bbox'][3])/2))
    groups=sorted(groups[:4],key=lambda g:g['bbox'][0])+sorted(groups[4:],key=lambda g:g['bbox'][0])
    # 一整段共用一个比例。按行登记印刷版面的地面线，不逐帧贴齐脚底。
    # 最大身高用于屈膝动作，保留角色降低高度；跳跃保留源稿的足底离地差。
    heights=[g['bbox'][3]-g['bbox'][1] for g in groups]
    scale=66/max(heights)
    row_baselines=[max(g['bbox'][3] for g in groups[r*4:r*4+4]) for r in range(2)]
    frames=[];records=[]
    for i,g in enumerate(groups):
        x0,y0,x1,y1=g['bbox'];pts=g['points'];row=i//4;col=i%4
        tile=np.zeros((y1-y0,x1-x0,4),dtype=np.uint8)
        tile[pts[:,1]-y0,pts[:,0]-x0]=arr[pts[:,1],pts[:,0]]
        tile[:,:,3]=np.where(tile[:,:,3]>=210,255,0)
        # 列中心来自固定网格；身体重心和脚的相对位移保留在输出中。
        anchor=(col+.5)*w/4
        im=Image.fromarray(tile).transform((64,96),Image.Transform.AFFINE,(1/scale,0,anchor-x0-32/scale,0,1/scale,row_baselines[row]-y0-80/scale),Image.Resampling.NEAREST)
        out=np.array(im);on=out[:,:,3]>0;rgb=out[:,:,:3][on].astype(np.int32)
        idx=((rgb[:,None]-PAL[None])**2).sum(axis=2).argmin(axis=1)
        out[:,:,:3][on]=PAL[idx].astype(np.uint8);out[:,:,3]=on.astype(np.uint8)*255;out[~on]=0
        im=Image.fromarray(out);box=im.getbbox()
        assert box and box[0]>0 and box[1]>0 and box[2]<64 and box[3]<96,(key,i,box)
        frames.append(im);records.append({'frame':i,'source_bbox':g['bbox'],'bbox':box,'source_grid_x':anchor,'source_row_baseline':row_baselines[row]})
    export(key,frames,DUR[action],{'source':str(file.relative_to(ROOT)),'source_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'uniform_scale':scale,'source_row_baselines':row_baselines,'frames':records})

(ROOT/'catalog.json').write_text(json.dumps({'clips':catalog,'total_frames':sum(c['frame_count'] for c in catalog),'production_ready':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'clips':len(catalog),'frames':sum(c['frame_count'] for c in catalog)}))
