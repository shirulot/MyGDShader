"""裁出方向母图，保留源像素；不创建或重画角色。"""
from pathlib import Path
from PIL import Image
import numpy as np
from inspect_sources import regions
root=Path(__file__).resolve().parent
dirs=['down','down_left','left','up_left','up','up_right','right','down_right']
for ch in ['A','C']:
    im=Image.open(root/'references'/f'master-{ch}.png').convert('RGBA')
    groups=regions(np.array(im)[:,:,3]>=210)
    groups.sort(key=lambda g:(g['bbox'][1]+g['bbox'][3])/2)
    groups=sorted(groups[:4],key=lambda g:g['bbox'][0])+sorted(groups[4:],key=lambda g:g['bbox'][0])
    assert len(groups)==8
    for direction,g in zip(dirs,groups):
        x0,y0,x1,y1=g['bbox'];im.crop((max(0,x0-12),max(0,y0-12),min(im.width,x1+12),min(im.height,y1+12))).save(root/'references'/f'{ch}-{direction}.png')
