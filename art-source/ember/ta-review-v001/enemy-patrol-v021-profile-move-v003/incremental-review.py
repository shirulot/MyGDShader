"""TA v003 delta and view-only diagnostics. Frozen candidates are read only."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib, json
import numpy as np

OUT = Path(__file__).resolve().parent
OLD = OUT.with_name('enemy-patrol-v021-profile-move-v002')
P = OUT/'technical-package'
Q = OLD/'technical-package'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
im = lambda p: Image.open(p).convert('RGBA')
arr = lambda p: np.array(im(p))
rig, oldrig = load(P/'rig.json'), load(Q/'rig.json')
cat = load(P/'output/catalog.json')
report = {'scope':'independent v002 to v003 delta; diagnostics are exact PNG crops with nearest scaling', 'frames':[], 'ownership_changes':[], 'point_motion':[], 'sole_probes':[], 'diagnostics':{}}

# Check actual engine-read masks against the old engine-read masks on source pixels.
expected = {('near',61,94),('near',61,95),('far',64,91),('far',64,92)}
for direction, config in rig['configs'].items():
    for kind in ['near','far']:
        texture=arr(P/config[kind+'_source'].removeprefix('res://'))
        parts=[p for p in config['parts'] if p['source_kind']==kind]
        masks={p['id']:np.array(Image.open(OUT/f'technical-runtime-mask-{direction}-{p["id"]}.png').convert('L'))>0 for p in parts}
        oldmasks={p['id']:np.array(Image.open(OLD/f'technical-runtime-mask-{direction}-{p["id"]}.png').convert('L'))>0 for p in parts}
        for y,x in np.argwhere(texture[:,:,3]>0):
            owners=[p['id'] for p in parts if masks[p['id']][y,x]]
            previous=[p['id'] for p in parts if oldmasks[p['id']][y,x]]
            assert len(owners)==1 and len(previous)==1
            if owners!=previous:
                assert direction=='right' and (kind,int(x),int(y)) in expected
                assert previous[0].endswith('_shin') and owners[0].endswith('_foot')
                report['ownership_changes'].append({'direction':direction,'instance':kind,'xy':[int(x),int(y)],'rgba':texture[y,x].tolist(),'old':previous[0],'new':owners[0]})
assert len(report['ownership_changes'])==4

for clip in cat['clips']:
    d=clip['direction']; atlas=clip['atlas'].removeprefix('res://')
    if d!='right': assert (P/atlas).read_bytes()==(Q/atlas).read_bytes()
    for f in range(8):
        rel=f'output/enemy_patrol/move_{d}/f{f:02}.png'
        old,new=arr(Q/rel),arr(P/rel)
        ys,xs=np.where(np.any(old!=new,axis=2))
        row={'direction':d,'frame':f,'byte_equal':(P/rel).read_bytes()==(Q/rel).read_bytes(),'rgba_changes':len(xs),'pixels':[{'xy':[int(x),int(y)],'before':old[y,x].tolist(),'after':new[y,x].tolist()} for y,x in zip(ys,xs)]}
        report['frames'].append(row)
        if d!='right' or f in [5,6]:assert row['byte_equal']
assert sum(r['rgba_changes'] for r in report['frames'])==19
assert sum(r['rgba_changes']>0 for r in report['frames'])==6

# New metadata gives an opaque source center; it remains distinct from the nominal edge coordinate.
integrity=load(OUT/'technical-integrity.json')
for direction,config in rig['configs'].items():
    clip=next(c for c in cat['clips'] if c['direction']==direction)
    for side,leg in config['legs'].items():
        part=next(p for p in config['parts'] if p['id']==side+'_foot')
        tex=arr(P/config[part['source_kind']+'_source'].removeprefix('res://'))
        mask=np.array(Image.open(OUT/f'technical-runtime-mask-{direction}-{part["id"]}.png').convert('L'))>0
        sx,sy=[int(v) for v in leg['visible_sole_source_pixel_center']]
        ys,xs=np.where(mask&(tex[:,:,3]>0));assert sy==int(ys.max()) and mask[sy,sx] and tex[sy,sx,3]==255
        for f,pose in enumerate(clip['poses']):
            t=pose['part_transforms'][part['id']];assert t['basis_x']==[1,0] and t['basis_y']==[0,1]
            dx,dy=[int(t['position'][j]-part['pivot'][j]) for j in [0,1]]
            sample=next(s for s in integrity['actual_sole_samples'] if s['direction']==direction and s['frame']==f and s['side']==side)
            measured=next(s for s in sample['actual_bottom_row_samples'] if s['source_xy']==[sx,sy])
            assert measured['output_xy']==[sx+dx,sy+dy]
            report['sole_probes'].append({'direction':direction,'frame':f,'side':side,'source_xy':[sx,sy],'output_xy':measured['output_xy'],'top_owner':measured['top_owner'],'self_visible':measured['self_visible'],'actual_rgba_equal':measured['actual_rgba_equal'],'nominal_sole':sample['sole'],'nominal_source_probe_on_foot':sample['nominal_source_probe_on_foot']})
            if direction=='right':
                points=[(61,94),(61,95)] if side=='right' else [(64,91),(64,92)]
                final=arr(P/f'output/enemy_patrol/move_right/f{f:02}.png')
                for x,y in points:
                    report['point_motion'].append({'frame':f,'side':side,'source_xy':[x,y],'rigid_output_xy':[x+dx,y+dy],'source_rgba':tex[y,x].tolist(),'actual_rgba':final[y+dy,x+dx].tolist(),'equals_source':bool(np.array_equal(final[y+dy,x+dx],tex[y,x]))})
report['sources_byte_unchanged']={f.name:sha(f)==sha(Q/'source'/f.name) for f in (P/'source').glob('*.png')}
assert all(report['sources_byte_unchanged'].values())
report['bind_rgba_unchanged']={d:bool(np.array_equal(arr(P/f'qa/bind_{d}.png'),arr(Q/f'qa/bind_{d}.png'))) for d in ['left','right']}
assert all(report['bind_rgba_unchanged'].values())

def chart(name,items,cols,roi,scale,bg):
    w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
    canvas=Image.new('RGBA',(cols*w,((len(items)+cols-1)//cols)*(h+24)),bg);draw=ImageDraw.Draw(canvas)
    for i,(label,picture) in enumerate(items):
        x,y=i%cols*w,i//cols*(h+24)
        draw.text((x+3,y+4),label,fill=(15,15,15,255) if bg[0]>100 else (245,245,245,255))
        canvas.alpha_composite(picture.crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
    canvas.convert('RGB').save(OUT/name)
    report['diagnostics'][name]={'sha256':sha(OUT/name),'roi_half_open':roi,'scale':scale,'labels':[x[0] for x in items]}

frames=[im(P/f'output/enemy_patrol/move_right/f{i:02}.png') for i in range(8)]
previous=[im(Q/f'output/enemy_patrol/move_right/f{i:02}.png') for i in range(8)]
poses=next(c['poses'] for c in cat['clips'] if c['direction']=='right')
aligned=[]
for f,pose in enumerate(poses):
    # Local foot anchoring only: do not use these shifted diagnostic views to judge global gait.
    ankle=pose['part_transforms']['right_foot']['position'];delta=(int(58-ankle[0]),int(94-ankle[1]))
    for label,picture in [('v002',previous[f]),('v003',frames[f])]:
        pic=Image.new('RGBA',(128,128));pic.alpha_composite(picture,delta);aligned.append((f'{label} F{f:02}',pic))
sources=[('C002 near',im(P/'source/c002_right_near.png')),('C002 far',im(P/'source/c002_right_far.png')),('C002 neutral',im(P/'qa/bind_right.png'))]
for color,bg in {'light':(236,233,216,255),'dark':(25,42,52,255)}.items():
    chart(f'visual-e-native-{color}-1x.png',[(f'v003 E F{i:02}',pic) for i,pic in enumerate(frames)],4,[0,0,128,128],1,bg)
    chart(f'visual-e-full-{color}-4x.png',[(f'v003 E F{i:02}',pic) for i,pic in enumerate(frames)],4,[40,44,87,108],4,bg)
    chart(f'visual-e-joints-{color}-8x.png',[(f'v003 E F{i:02}',pic) for i,pic in enumerate(frames)],4,[48,76,79,107],8,bg)
    chart(f'visual-e-aligned-before-after-{color}-12x.png',aligned,4,[51,85,70,105],12,bg)
    chart(f'visual-e-source-{color}-12x.png',sources,3,[51,85,73,106],12,bg)
    chart(f'visual-e-loop-{color}-8x.png',[(f'v003 E F{i:02}',frames[i]) for i in [6,7,0,1]],4,[48,76,79,107],8,bg)

report['status']='PASS_INCREMENTAL_SOURCE_OWNERSHIP_DELTA_AND_SOLE_BINDING'
(OUT/'incremental-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'ownership_changed':len(report['ownership_changes']),'changed_frames':sum(r['rgba_changes']>0 for r in report['frames']),'rgba_changes':sum(r['rgba_changes'] for r in report['frames']),'by_frame':[(r['frame'],r['rgba_changes']) for r in report['frames'] if r['direction']=='right'],'sole_probes':len(report['sole_probes']),'self_visible_sole_probes':sum(r['self_visible'] for r in report['sole_probes']),'diagnostics':len(report['diagnostics'])}))
