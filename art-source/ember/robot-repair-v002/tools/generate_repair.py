"""Reproduce robot v002 from frozen v001 idle pixels and editable native JSON.

Only this new source directory is written by default. --publish creates the
allowed new 16 frame PNGs and one atlas, never overwrites any existing unequal
official PNG. The old producer module is read-only; its BASE is rebound only in
this process so explicit new parts_file paths resolve to the v002 rig directory.
"""
from pathlib import Path
from collections import deque
import argparse, hashlib, importlib.util, json
from PIL import Image, ImageDraw, ImageFont
import numpy as np

SOURCE=Path(__file__).resolve().parents[1]
ROOT=SOURCE.parents[2]
OLD=ROOT/'art-source/ember/batch-02-robot'
ASSETS=ROOT/'assets/ember/characters/robot'
FINISHED=SOURCE/'finished-frames'
PREVIEWS=SOURCE/'previews'
DIRECTIONS=('down','left','right','up')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return path.resolve().relative_to(ROOT).as_posix()
def write_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def read_json(path):return json.loads(path.read_text(encoding='utf-8'))
def components(alpha):
    pending={(int(x),int(y)) for y,x in np.argwhere(alpha)}; groups=[]
    neighbors=[(dx,dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy]
    while pending:
        seed=min(pending,key=lambda xy:(xy[1],xy[0])); pending.remove(seed)
        group={seed}; todo=deque([seed])
        while todo:
            x,y=todo.popleft()
            for dx,dy in neighbors:
                q=x+dx,y+dy
                if q in pending:pending.remove(q);group.add(q);todo.append(q)
        groups.append(group)
    return sorted(groups,key=lambda g:-len(g))
def summary(group):
    xs=[p[0] for p in group];ys=[p[1] for p in group]
    return {'pixels':len(group),'bbox_xyxy_inclusive':[min(xs),min(ys),max(xs),max(ys)]}
def visible(raw,bg=(81,101,112,255)):
    im=Image.new('RGBA',raw.size,bg);im.alpha_composite(raw);return im.convert('RGB')
def publish_exact(source,dest):
    if dest.exists():
        if sha(dest)!=sha(source):raise FileExistsError(f'Unequal official target already exists: {dest}')
    else:dest.write_bytes(source.read_bytes())

parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true');args=parser.parse_args()
FINISHED.mkdir(parents=True,exist_ok=True);PREVIEWS.mkdir(parents=True,exist_ok=True)
baseline=read_json(SOURCE/'protected-inputs-before.json')
assert all(sha(ROOT/p)==h for p,h in baseline.items()),'A protected v001 input changed.'
spec=importlib.util.spec_from_file_location('frozen_v001_robot_builder',OLD/'tools/finish_robot_frames.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
builder.BASE=SOURCE.resolve();builder.ROOT=ROOT.resolve()
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',17)
rows=[];working={};old_images={};rig_checks=[]
atlas=Image.new('RGBA',(5*64,4*96),(0,0,0,0))
before_after=Image.new('RGB',(10*256,4*414),(30,38,46));draw=ImageDraw.Draw(before_after)
new_board=Image.new('RGB',(5*256,4*414),(30,38,46));new_draw=ImageDraw.Draw(new_board)
for row,direction in enumerate(DIRECTIONS):
    idle_path=ASSETS/f'robot_idle_{direction}_v001.png';idle=Image.open(idle_path).convert('RGBA')
    atlas.paste(idle,(0,row*96))
    rig_path=SOURCE/'annotations'/f'rig_{direction}_v002.json';rig=read_json(rig_path)
    parts=builder.parts_from_idle(idle,{'parts_file':str(rig_path.relative_to(SOURCE).as_posix())})
    pcs={name:[summary(g) for g in components(np.array([[((x,y) in coords) for x in range(64)] for y in range(96)],dtype=bool))] for name,coords in parts.items()}
    rig_checks.append({'direction':direction,'rig':rel(rig_path),'sha256':sha(rig_path),
        'unique_complete_idle_partition':True,'parts_pixel_counts':{n:len(p) for n,p in parts.items()},
        'components8_by_part':pcs,'semantic_repairs':rig['semantic_repairs']})
    frames=[]
    for frame in range(4):
        ident=f'robot_walk_{direction}_f{frame:02d}';ann_path=SOURCE/'annotations'/f'walk_{direction}_f{frame:02d}.json'
        annotation=read_json(ann_path)
        old_ann_path=OLD/'annotations'/f'walk_{direction}_f{frame:02d}.json';old_ann=read_json(old_ann_path)
        assert annotation['offsets']==old_ann['offsets'] and annotation['draw_order']==old_ann['draw_order']
        fixed,info=builder.build_walk(idle,annotation)
        measurement=builder.measure(fixed,'walk')
        path=FINISHED/(ident+'_v002.png');fixed.save(path)
        old_path=ASSETS/(ident+'_v001.png');old=Image.open(old_path).convert('RGBA')
        first=np.array(old);second=np.array(fixed);changed=np.any(first!=second,axis=2)
        cs=components(second[:,:,3]>0)
        assert len(cs)==1,f'{ident} still has detached parts: {[summary(g) for g in cs]}'
        working[ident]=fixed;old_images[ident]=old;frames.append(visible(fixed))
        atlas.paste(fixed,((frame+1)*64,row*96))
        edits=[*rig['semantic_repairs'],*annotation['repair_edits']]
        closed=[]
        if direction=='left' and frame==2:closed.append('ROBOT_LEFT_02_DETACHED')
        if direction=='down' and frame==1:closed.append('ROBOT_DOWN_01_DETACHED')
        if direction=='down' and frame==3:closed.append('ROBOT_DOWN_03_DETACHED')
        seam_ids={('left',0):'ROBOT_LEFT_00_SHOULDER_VERTICAL_CUT',('right',2):'ROBOT_RIGHT_02_SHOULDER_VERTICAL_CUT',
            ('left',1):'ROBOT_LEFT_01_HIP_HORIZONTAL_CUT',('left',3):'ROBOT_LEFT_03_HIP_HORIZONTAL_CUT',
            ('right',3):'ROBOT_RIGHT_03_HIP_HORIZONTAL_CUT'}
        if (direction,frame) in seam_ids:closed.append(seam_ids[(direction,frame)])
        rows.append({'id':ident,'direction':direction,'frame_index':frame,
            'old_file':rel(old_path),'old_sha256':sha(old_path),'new_file':rel(ASSETS/path.name),
            'new_sha256':sha(path),'finished_file':rel(path),'old_annotation':rel(old_ann_path),
            'old_annotation_sha256':sha(old_ann_path),'new_annotation':rel(ann_path),
            'new_annotation_sha256':sha(ann_path),'rig':rel(rig_path),'rig_sha256':sha(rig_path),
            'changed_pixel_count':int(changed.sum()),'alpha_changed_pixel_count':int((first[:,:,3]!=second[:,:,3]).sum()),
            'pixel_diff_xy':[[int(x),int(y)] for y,x in np.argwhere(changed)],
            'opaque_pixel_count':int((second[:,:,3]>0).sum()),
            'transparent_pixels_added':int(((first[:,:,3]>0)&(second[:,:,3]==0)).sum()),
            'transparent_pixels_closed':int(((first[:,:,3]==0)&(second[:,:,3]>0)).sum()),
            'components8':[summary(g) for g in cs],'measurement':measurement,
            'edits':edits,'closed_issue_ids':closed,'old_gait':old_ann['gait'],'new_gait':annotation['gait'],
            'formal_output_written':args.publish})
    # Both APNG timing and actual playback frames use unchanged 125 ms / 8 fps.
    sized=[im.resize((256,384),Image.Resampling.NEAREST) for im in frames]
    sized[0].save(PREVIEWS/f'walk_{direction}_v002_8fps_4x.apng',save_all=True,append_images=sized[1:],duration=125,loop=0,disposal=0,blend=0)
    # Fixed explicit palette, independent of per-frame quantization, prevents GIF
    # palette flicker and preserves every opaque production color exactly.
    palette=[*builder.PALETTE,(81,101,112,255)]
    gif_frames=[]
    for image in sized:
        indexed=Image.new('P',image.size)
        flat_palette=[value for color in palette for value in color[:3]]+[0]*(768-3*len(palette))
        indexed.putpalette(flat_palette)
        index={color[:3]:n for n,color in enumerate(palette)}
        indexed.putdata([index[pixel] for pixel in image.getdata()]);gif_frames.append(indexed)
    # GIF supports 10ms ticks: alternate 120/130 to preserve the total 500ms loop.
    gif_frames[0].save(PREVIEWS/f'walk_{direction}_v002_fixed_palette_4x.gif',save_all=True,append_images=gif_frames[1:],duration=[120,130,120,130],loop=0,disposal=1,optimize=False)
    for col in range(5):
        old=idle if col==0 else old_images[f'robot_walk_{direction}_f{col-1:02d}']
        new=idle if col==0 else working[f'robot_walk_{direction}_f{col-1:02d}']
        new_board.paste(visible(new).resize((256,384),Image.Resampling.NEAREST),(col*256,row*414))
        new_draw.text((col*256+8,row*414+389),f'{direction} '+('idle v001' if col==0 else f'f{col-1:02d} v002'),font=font,fill=(235,237,227))
        for half,im in enumerate([old,new]):
            x=(col*2+half)*256;y=row*414
            before_after.paste(visible(im).resize((256,384),Image.Resampling.NEAREST),(x,y))
            draw.text((x+8,y+389),f'{direction} '+('idle' if col==0 else f'f{col-1:02d}')+(' old' if half==0 else ' v002'),font=font,fill=(235,237,227))
    native_row=Image.new('RGB',(5*64*2,96),(34,44,51))
    for col in range(5):
        old=idle if col==0 else old_images[f'robot_walk_{direction}_f{col-1:02d}']
        new=idle if col==0 else working[f'robot_walk_{direction}_f{col-1:02d}']
        native_row.paste(visible(old),((col*2)*64,0));native_row.paste(visible(new),((col*2+1)*64,0))
    native_row.save(PREVIEWS/f'{direction}_before_after_native.png')
    native_row.resize((2560,384),Image.Resampling.NEAREST).save(PREVIEWS/f'{direction}_before_after_4x.png')
atlas_path=FINISHED/'robot_animations_v002.png';atlas.save(atlas_path)
before_after.save(PREVIEWS/'all20_before_after_4x.png')
new_board.save(PREVIEWS/'all20_repaired_neutral_4x.png')
atlas.resize((1280,1536),Image.Resampling.NEAREST).save(PREVIEWS/'robot_atlas_v002_4x.png')
for ident,im in working.items():
    im.resize((256,384),Image.Resampling.NEAREST).save(PREVIEWS/(ident+'_v002_4x.png'))
    visible(im).resize((256,384),Image.Resampling.NEAREST).save(PREVIEWS/(ident+'_v002_neutral_4x.png'))
if args.publish:
    for p in sorted(FINISHED.glob('*.png')):publish_exact(p,ASSETS/p.name)
assert all(sha(ROOT/p)==h for p,h in baseline.items()),'Protected old input changed after generation.'
source_script=OLD/'tools/finish_robot_frames.py'
record={'status':'CANDIDATE_READY' if not args.publish else 'V002_PUBLISHED_NEW_FILES_ONLY',
    'version':'v002','frames':rows,'atlas':{'old_file':rel(ASSETS/'robot_animations_v001.png'),
    'old_sha256':sha(ASSETS/'robot_animations_v001.png'),'new_file':rel(ASSETS/atlas_path.name),
    'new_sha256':sha(atlas_path),'finished_file':rel(atlas_path),'size':[320,384],
    'layout':'rows down,left,right,up; columns idle,f00,f01,f02,f03'},
    'rig_checks':rig_checks,'preserved_idle':[{'file':rel(ASSETS/f'robot_idle_{d}_v001.png'),
    'sha256':sha(ASSETS/f'robot_idle_{d}_v001.png')} for d in DIRECTIONS],
    'source_builder':{'file':rel(source_script),'sha256':sha(source_script),'module_BASE':rel(SOURCE),
    'reuse':'Read-only build_walk/measure and explicit part masks. Module BASE rebound only within this process.'},
    'animation':{'frames_per_direction':4,'fps':8,'apng_frame_duration_ms':125,
    'gif_frame_duration_ms':[120,130,120,130],'gif_loop_duration_ms':500,'loop':True},
    'protected_input_count':len(baseline),'protected_inputs_changed':[],
    'image_operations':'Explicit native JSON part attribution, unchanged integer part offsets/draw order, individually drawn joint pixels. No global filtering/closing/dilation, fragment deletion, affine warp or image generation.'}
write_json(SOURCE/'repair-record-v002.json',record)
print(json.dumps({'status':record['status'],'frames':len(rows),'components8':[len(r['components8']) for r in rows],
    'changed_pixels':{r['id']:r['changed_pixel_count'] for r in rows},'protected_inputs_changed':[]},indent=2))
