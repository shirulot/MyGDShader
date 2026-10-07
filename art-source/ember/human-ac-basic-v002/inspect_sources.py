"""只检查透明源稿的连通区域，确定切片边界；不绘制或修补角色。"""
from pathlib import Path
from PIL import Image
import numpy as np
import json
ROOT=Path(__file__).resolve().parent
def regions(mask):
    mask=mask.copy(); h,w=mask.shape; result=[]
    for y,x in zip(*np.where(mask)):
        if not mask[y,x]: continue
        todo=[(int(x),int(y))]; mask[y,x]=False; pts=[]
        while todo:
            px,py=todo.pop();pts.append((px,py))
            for nx,ny in ((px-1,py),(px+1,py),(px,py-1),(px,py+1)):
                if 0<=nx<w and 0<=ny<h and mask[ny,nx]:
                    mask[ny,nx]=False;todo.append((nx,ny))
        if len(pts)>400:
            ar=np.array(pts);result.append({'count':len(pts),'bbox':[int(ar[:,0].min()),int(ar[:,1].min()),int(ar[:,0].max()+1),int(ar[:,1].max()+1)],'points':ar})
    return sorted(result,key=lambda r:r['bbox'][0])
if __name__=='__main__':
    out={}
    for p in (ROOT/'source').glob('*.png'):
        im=np.array(Image.open(p).convert('RGBA'));rs=regions(im[:,:,3]>=210)
        out[p.stem]={'size':[im.shape[1],im.shape[0]],'regions':[{k:v for k,v in r.items() if k!='points'} for r in rs]}
    (ROOT/'source-regions.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out))
