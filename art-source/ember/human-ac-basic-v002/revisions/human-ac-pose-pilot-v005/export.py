"""固定格导出与审阅预览：不逐帧居中、齐底、缩放或修改角色关节。"""
from pathlib import Path
from PIL import Image
import hashlib
import json
import shutil
import numpy as np

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'human-ac-registration-v004'
KEYS = {'A-idle-down_right': (4, 2, 250),
        'A-walk-down_right': (8, 4, 120),
        'C-run-down_left': (8, 4, 80)}
COLORS = ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','ECE9D8',
          '7B4D35','B77C4B','E2B77A','B9947B','D7B59B','EAC5A0','3A3436',
          '635754','9B8170','F2D9B8','AAB7B1']
palette = np.array([list(bytes.fromhex(c)) for c in COLORS], dtype=np.int32)
old_catalog = {c['key']: c for c in json.loads((OLD/'catalog.json').read_text())['clips']}
for folder in ['final','frames','previews','qa','before']:
    (ROOT/folder).mkdir(exist_ok=True)
clips, audit = [], []
for key, (count, cols, ms) in KEYS.items():
    source = ROOT/'source'/f'{key}.png'
    if not source.exists(): continue
    im = Image.open(source).convert('RGBA')
    # 所有帧采用同一固定格。以首格确定一次比例，后续各帧禁止重新拟合。
    cw, ch = im.width/cols, im.height/2
    first = im.crop((0, 0, round(cw), round(ch)))
    first_alpha = np.array(first)[:,:,3] >= 210
    yy, xx = np.nonzero(first_alpha)
    scale = 66 / (int(yy.max()) - int(yy.min()) + 1)
    # 原稿未严格执行引导格，首格注册仅用于诊断。整段共用同一地面位置。
    anchor_x, anchor_y = cw/2, float(yy.max()+1)
    frames, bboxes = [], []
    for i in range(count):
        # 先按固定格隔离，防止输出透明边距采到相邻格。并非按人物包围盒裁切。
        cell = im.crop((round((i % cols)*cw), round((i // cols)*ch),
                        round((i % cols+1)*cw), round((i // cols+1)*ch)))
        frame = cell.transform((64,96), Image.Transform.AFFINE,
            (1/scale,0,anchor_x-32/scale,0,1/scale,anchor_y-80/scale),
            Image.Resampling.NEAREST)
        arr = np.array(frame)
        mask = arr[:,:,3] >= 210
        rgb = arr[:,:,:3][mask].astype(np.int32)
        idx = ((rgb[:,None]-palette[None])**2).sum(axis=2).argmin(axis=1)
        arr[:,:,:3][mask] = palette[idx].astype(np.uint8)
        arr[:,:,3] = mask.astype(np.uint8)*255
        arr[~mask] = 0
        frame = Image.fromarray(arr)
        frames.append(frame)
        bboxes.append(frame.getbbox())
        frame_dir=ROOT/'frames'/key
        frame_dir.mkdir(exist_ok=True)
        frame.save(frame_dir/f'f{i:02}.png')
    atlas = Image.new('RGBA',(64*count,96))
    for i, frame in enumerate(frames): atlas.paste(frame,(64*i,0))
    atlas.save(ROOT/'final'/f'{key}.png')
    atlas.resize((64*count*4,384),Image.Resampling.NEAREST).save(ROOT/'qa'/f'{key}-contact.png')
    seam = Image.new('RGBA',(256,96))
    for i,j in enumerate([count-2,count-1,0,1]): seam.paste(frames[j],(i*64,0))
    seam.resize((1024,384),Image.Resampling.NEAREST).save(ROOT/'qa'/f'{key}-seam.png')
    large = [f.resize((256,384),Image.Resampling.NEAREST) for f in frames]
    large[0].save(ROOT/'previews'/f'{key}.webp',save_all=True,append_images=large[1:],duration=ms,loop=0,lossless=True)
    old = old_catalog[key]
    shutil.copy2(OLD/old['atlas'],ROOT/'before'/f'{key}.png')
    meta = {'key':key,'cell':[64,96],'root':[32,80],'frame_count':count,'duration_ms':ms,
            'loop':True,'atlas':f'final/{key}.png','old':old,'production_ready':False,
            'technical_status':'pass','visual_status':'not_reviewed','runtime_status':'not_reviewed',
            'source':f'source/{key}.png','source_size':im.size,'source_cell':[cw,ch],
            'common_anchor':[anchor_x,anchor_y],'common_scale':scale,
            'method':'imagegen soft pose guidance; fixed-cell diagnostic export',
            'limitations':['Generated source does not exactly follow guide cell coordinates.',
                          'Whole-strip first-frame calibration; no per-frame registration corrections.',
                          'Downsampled diagnostic candidate, not approved native pixel art.']}
    (ROOT/'final'/f'{key}.json').write_text(json.dumps(meta,indent=2))
    clips.append(meta)
    clear_edges = all(b and b[0]>0 and b[1]>0 and b[2]<64 and b[3]<96 for b in bboxes)
    audit.append({'key':key,'bboxes':bboxes,'clear_edges':clear_edges,
                  'unique_frames':len({hashlib.sha256(f.tobytes()).hexdigest() for f in frames}),
                  'no_per_frame_transform':True,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
(ROOT/'catalog.json').write_text(json.dumps({'clips':clips,'production_ready':False},indent=2))
(ROOT/'qa'/'export-check.json').write_text(json.dumps(audit,indent=2))
print(json.dumps({'clips':len(clips),'frames':sum(c['frame_count'] for c in clips),'audit':audit}))
