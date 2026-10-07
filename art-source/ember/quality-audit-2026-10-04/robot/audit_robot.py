"""Read-only native-pixel diagnostics; all output stays in this audit directory.

Eight-connected components avoid mistaking valid diagonal outlines for breaks.
Component/transparent-hole candidates require visual and rig-based judgement.
"""
from pathlib import Path
import hashlib, json
from collections import deque
from PIL import Image, ImageDraw, ImageFont
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
FRAMES = ROOT / 'assets/ember/characters/robot'
SOURCE = ROOT / 'art-source/ember/batch-02-robot'
DIRECTIONS = ('down', 'left', 'right', 'up')

def components(mask, connectivity=8):
    pending = {(int(x),int(y)) for y,x in np.argwhere(mask)}
    found=[]
    neighbors = [(-1,0),(1,0),(0,-1),(0,1)]
    if connectivity==8:
        neighbors += [(-1,-1),(-1,1),(1,-1),(1,1)]
    while pending:
        seed=min(pending, key=lambda p:(p[1],p[0])); pending.remove(seed)
        group={seed}; todo=deque([seed])
        while todo:
            x,y=todo.popleft()
            for dx,dy in neighbors:
                pt=(x+dx,y+dy)
                if pt in pending:
                    pending.remove(pt); group.add(pt); todo.append(pt)
        found.append(group)
    return sorted(found,key=lambda g:-len(g))

def describe(group):
    xs=[p[0] for p in group]; ys=[p[1] for p in group]
    return {'area':len(group), 'bbox_xyxy_inclusive':[min(xs),min(ys),max(xs),max(ys)],
            'pixels_xy':sorted(map(list,group),key=lambda p:(p[1],p[0]))}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def composite(raw, bg=(78,96,107,255)):
    result=Image.new('RGBA',raw.size,bg); result.alpha_composite(raw); return result.convert('RGB')

report={'method':'Source PNG alpha; 8-connectivity silhouette, 4-connectivity enclosed transparency; no pass/fail inferred from count alone.', 'frames':[], 'input_sha256':{}}
board=Image.new('RGB',(5*256,4*416),(30,38,45)); draw=ImageDraw.Draw(board)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',18)
for row,direction in enumerate(DIRECTIONS):
    for col in range(5):
        name=f'robot_idle_{direction}_v001.png' if col==0 else f'robot_walk_{direction}_f{col-1:02d}_v001.png'
        path=FRAMES/name; raw=Image.open(path).convert('RGBA'); a=np.array(raw)
        alpha=a[:,:,3]>0
        cs=components(alpha,8)
        holes=[g for g in components(~alpha,4) if not any(x in (0,63) or y in (0,95) for x,y in g)]
        record={'file':path.relative_to(ROOT).as_posix(), 'sha256':sha(path),
                'opaque_count':int(alpha.sum()),'alpha_values':np.unique(a[:,:,3]).tolist(),
                'components8':[describe(g) for g in cs],
                'enclosed_transparency4':[describe(g) for g in holes]}
        report['frames'].append(record); report['input_sha256'][record['file']]=record['sha256']
        tile=composite(raw).resize((256,384),Image.Resampling.NEAREST)
        board.paste(tile,(col*256,row*416)); draw.text((col*256+8,row*416+388),direction+(' idle' if col==0 else f' f{col-1:02d}')+f' / C8={len(cs)}',(232,236,230),font=font)
        annotated=tile.copy(); painter=ImageDraw.Draw(annotated)
        for g in cs[1:]:
            x0,y0,x1,y1=describe(g)['bbox_xyxy_inclusive']; painter.rectangle((x0*4-2,y0*4-2,(x1+1)*4+1,(y1+1)*4+1),outline=(255,60,100),width=2)
        for g in holes:
            for x,y in g:
                painter.rectangle((x*4,y*4,x*4+3,y*4+3),fill=(238,46,181))
        annotated.save(OUT/(name.replace('.png','_diagnostic_4x.png')))
board.save(OUT/'robot_all20_4x.png')
(OUT/'native-pixel-statistics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for record in report['frames']:
    print(Path(record['file']).name,'C8',[(g['area'],g['bbox_xyxy_inclusive']) for g in record['components8']], 'holes',[(g['area'],g['bbox_xyxy_inclusive']) for g in record['enclosed_transparency4']])
