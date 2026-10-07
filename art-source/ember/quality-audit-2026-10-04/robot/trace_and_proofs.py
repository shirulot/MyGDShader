"""Trace confirmed geometry defects to explicit rig labels without editing inputs."""
import importlib.util, json, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
SOURCE=ROOT/'art-source/ember/batch-02-robot'
FRAMES=ROOT/'assets/ember/characters/robot'
spec=importlib.util.spec_from_file_location('finish_robot_frames_readonly',SOURCE/'tools/finish_robot_frames.py')
finish=importlib.util.module_from_spec(spec); spec.loader.exec_module(finish)
stats=json.loads((OUT/'native-pixel-statistics.json').read_text(encoding='utf-8'))
records={Path(r['file']).stem:r for r in stats['frames']}
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',19)
small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def points_rect(x0,y0,x1,y1):return [[x,y] for y in range(y0,y1+1) for x in range(x0,x1+1)]
def path_name(direction,frame):return f'robot_walk_{direction}_f{frame:02d}_v001'
def fixture(direction,frame):return records[path_name(direction,frame)]

issues=[]
for d,f in [('down',1),('down',3),('left',2)]:
    record=fixture(d,f)
    for group in record['components8'][1:]:
        issues.append({'id':f'ROBOT_{d.upper()}_{f:02d}_DETACHED', 'severity':'confirmed',
            'type':'detached_body_fragment', 'frame':path_name(d,f), 'pixels_xy':group['pixels_xy'],
            'bbox_xyxy_inclusive':group['bbox_xyxy_inclusive'], 'pixel_count':group['area'],
            'reason':'Opaque robot part completely detached from the body even with eight-neighbor connectivity.'})
for d,f,boxes,label in [
    ('left',0,[(25,42,25,52),(35,42,35,46),(35,48,35,52)],'shoulder_vertical_cut'),
    ('right',2,[(27,42,27,51),(40,42,40,55)],'shoulder_vertical_cut'),
    ('left',1,[(33,55,37,55)],'hip_horizontal_cut'),
    ('left',3,[(29,59,31,59)],'hip_horizontal_cut'),
    ('right',3,[(27,59,34,59)],'hip_horizontal_cut'),
]:
    raw=np.asarray(Image.open(FRAMES/(path_name(d,f)+'.png')).convert('RGBA'))
    pts=[pt for box in boxes for pt in points_rect(*box)]
    assert all(raw[y,x,3]==0 for x,y in pts)
    issues.append({'id':f'ROBOT_{d.upper()}_{f:02d}_{label.upper()}', 'severity':'joint_seam_review_required',
        'type':label,'frame':path_name(d,f), 'pixels_xy':pts,
        'bboxes_xyxy_inclusive':[list(b) for b in boxes], 'pixel_count':len(pts),
        'reason':'New straight transparent seam coincides with the hard rig split and independent part movement. A moved arm can legitimately expose background; visible continuity and joint drawing need artist review. This is not classified as complete limb detachment or a mandate to fill all negative space.'})

# Rebuild all 16 walk frames using the existing read-only function and compare
# against official pixels. No prepare/write function from the producer is used.
rebuild=[]
dependencies={}
for d in ('down','left','right','up'):
    idle_path=FRAMES/f'robot_idle_{d}_v001.png'
    idle=Image.open(idle_path).convert('RGBA')
    for f in range(4):
        annotation_path=SOURCE/'annotations'/f'walk_{d}_f{f:02d}.json'
        annotation=json.loads(annotation_path.read_text(encoding='utf-8'))
        remade,info=finish.build_walk(idle,annotation)
        official=Image.open(FRAMES/(path_name(d,f)+'.png')).convert('RGBA')
        different=int(np.any(np.asarray(remade)!=np.asarray(official),axis=2).sum())
        rebuild.append({'frame':path_name(d,f),'differing_pixels':different,'offsets':annotation['offsets'],'patches':annotation['patches']})
        dependencies[annotation_path.relative_to(ROOT).as_posix()]=sha(annotation_path)
        rig_path=SOURCE/annotation['parts_file']
        dependencies[rig_path.relative_to(ROOT).as_posix()]=sha(rig_path)
assert all(row['differing_pixels']==0 for row in rebuild)
dependencies[(SOURCE/'tools/finish_robot_frames.py').relative_to(ROOT).as_posix()]=sha(SOURCE/'tools/finish_robot_frames.py')

for issue in issues:
    name=issue['frame']; d=name.split('_')[2]; f=int(name.split('_')[3][1:])
    annotation=json.loads((SOURCE/'annotations'/f'walk_{d}_f{f:02d}.json').read_text(encoding='utf-8'))
    rig=json.loads((SOURCE/annotation['parts_file']).read_text(encoding='utf-8'))
    if issue['type']=='detached_body_fragment':
        trace=[]
        for x,y in issue['pixels_xy']:
            for part in rig['parts']:
                dx,dy=annotation['offsets'][part['name']]
                if [x-dx,y-dy] in part['pixels']:
                    trace.append({'output_xy':[x,y],'rig_part':part['name'],'idle_xy':[x-dx,y-dy],'offset_xy':[dx,dy]})
        issue['rig_trace']=trace
    else:
        idle=np.asarray(Image.open(FRAMES/f'robot_idle_{d}_v001.png').convert('RGBA'))
        issue['idle_alpha_at_same_coordinates']=[int(idle[y,x,3]) for x,y in issue['pixels_xy']]
        # The straight seam is entirely absent from the static reference.
        assert all(value==255 for value in issue['idle_alpha_at_same_coordinates'])
        issue['rig_offsets']=annotation['offsets']

# The left rig incorrectly labels a 14px portion of the same near-side boot as
# the other leg. Highlight this on the static design using explicit source IDs.
rig=json.loads((SOURCE/'annotations/rig_left_v001.json').read_text(encoding='utf-8'))
colors={'head':(150,178,236),'torso':(225,193,108),'left_arm':(160,213,149),'right_arm':(122,192,190),'left_leg':(224,158,203),'right_leg':(185,118,222)}
raw=Image.open(FRAMES/'robot_idle_left_v001.png').convert('RGBA')
semantic=Image.new('RGB',raw.size,(55,67,77))
for part in rig['parts']:
    for x,y in part['pixels']:semantic.putpixel((x,y),colors[part['name']])
rig_board=Image.new('RGB',(768,580),(26,33,39)); painter=ImageDraw.Draw(rig_board)
for col,img in enumerate([raw,semantic]):
    display=Image.new('RGBA',raw.size,(100,117,129,255)); display.alpha_composite(img.convert('RGBA'))
    display=display.crop((16,18,48,82)).resize((256,512),Image.Resampling.NEAREST)
    rig_board.paste(display,(col*300+16,20))
    painter.rectangle((col*300+16+(29-16)*8-2,20+(73-18)*8-2,col*300+16+(32-16)*8+1,20+(79-18)*8+1),outline=(255,65,93),width=3)
    painter.text((col*300+16,544),['idle left native','rig part assignment'][col],font=small,fill=(240,240,231))
for n,(part,color) in enumerate(colors.items()):
    painter.rectangle((608,22+n*45,624,38+n*45),fill=color)
    painter.text((630,20+n*45),part,font=small,fill=(240,240,231))
rig_board.save(OUT/'left_boot_rig_split_proof_8x.png')

# A compact annotated review includes original pixels (no interpolation), their
# alpha, the static reference, and boxes. Seam candidates remain distinct from
# confirmed detached fragments; outlining a candidate is not a repair mandate.
choices=[('left',2,[(26,72,31,79)]),('left',0,[(24,41,26,53),(34,41,36,53)]),
         ('right',2,[(26,41,28,52),(39,41,41,56)]),('right',3,[(26,58,35,60)]),
         ('down',1,[(31,61,33,63)]),('down',3,[(29,61,32,63)])]
overview=Image.new('RGB',(3*392,2*500),(25,33,40)); p=ImageDraw.Draw(overview)
for index,(d,f,boxes) in enumerate(choices):
    ox=(index%3)*392; oy=(index//3)*500
    name=path_name(d,f); official=Image.open(FRAMES/(name+'.png')).convert('RGBA')
    idle=Image.open(FRAMES/f'robot_idle_{d}_v001.png').convert('RGBA')
    crop=(16,38,48,81) if d in ('left','right') else (12,38,52,81)
    x0,y0,x1,y1=crop; scale=4
    for slot,image0 in enumerate([idle,official]):
        display=Image.new('RGBA',image0.size,((210,215,207,255) if slot==0 else (84,100,110,255)))
        display.alpha_composite(image0)
        display=display.crop(crop).resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST).convert('RGB')
        px=ox+12+slot*188; py=oy+44; overview.paste(display,(px,py))
        if slot==1:
            for a,b,c,e in boxes:
                p.rectangle((px+(a-x0)*scale-2,py+(b-y0)*scale-2,px+(c-x0+1)*scale+1,py+(e-y0+1)*scale+1),outline=(255,77,112),width=2)
        p.text((px,oy+22),'idle source' if slot==0 else f'walk {d} f{f:02d}',font=small,fill=(241,242,234))
    alpha=official.getchannel('A').convert('RGB').crop(crop)
    alpha=alpha.resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST)
    overview.paste(alpha,(ox+12,oy+270))
    for a,b,c,e in boxes:
        p.rectangle((ox+12+(a-x0)*scale-2,oy+270+(b-y0)*scale-2,ox+12+(c-x0+1)*scale+1,oy+270+(e-y0+1)*scale+1),outline=(255,77,112),width=2)
    p.text((ox+204,oy+280),'Alpha: white = solid',font=small,fill=(225,228,218))
    p.text((ox+204,oy+310),'black = transparent',font=small,fill=(225,228,218))
    p.text((ox+12,oy+454),f'{d} f{f:02d}: '+('CONFIRMED detached pixels' if d=='down' or (d=='left' and f==2) else 'joint seam: REVIEW REQUIRED'),font=small,fill=(241,242,234))
overview.save(OUT/'joint_seams_and_fragments_6_examples_4x.png')

# User-facing proof of only the three unambiguous detached-body defects.
strict=Image.new('RGB',(1152,850),(26,33,39)); p=ImageDraw.Draw(strict)
for col,(d,f,box) in enumerate([('left',2,(25,71,33,80)),('down',1,(29,59,35,65)),('down',3,(28,59,34,65))]):
    ox=col*384; raw=Image.open(FRAMES/(path_name(d,f)+'.png')).convert('RGBA')
    idle=Image.open(FRAMES/f'robot_idle_{d}_v001.png').convert('RGBA')
    p.text((ox+12,10),f'CONFIRMED: {d} f{f:02d}',font=font,fill=(243,237,231))
    bg=Image.new('RGBA',raw.size,(103,118,129,255)); bg.alpha_composite(raw)
    full=bg.resize((256,384),Image.Resampling.NEAREST).convert('RGB'); strict.paste(full,(ox+20,44))
    x0,y0,x1,y1=box
    p.rectangle((ox+20+x0*4-2,44+y0*4-2,ox+20+x1*4+1,44+y1*4+1),outline=(255,75,107),width=3)
    # Shared native crop coordinates make a static/walk comparison reviewable.
    crop=(24,56,44,81) if d=='left' else (22,56,42,69)
    cx,cy,ex,ey=crop; scale=7
    for slot,img in enumerate([idle,raw]):
        matte=Image.new('RGBA',img.size,(172,187,196,255)); matte.alpha_composite(img)
        close=matte.crop(crop).resize(((ex-cx)*scale,(ey-cy)*scale),Image.Resampling.NEAREST).convert('RGB')
        px=ox+12+slot*182; py=475; strict.paste(close,(px,py))
        p.text((px,447),'idle pixels' if slot==0 else 'walk pixels',font=small,fill=(236,238,231))
        if slot==1:
            p.rectangle((px+(x0-cx)*scale-2,py+(y0-cy)*scale-2,px+(x1-cx)*scale+1,py+(y1-cy)*scale+1),outline=(255,75,107),width=3)
    area=fixture(d,f)['components8'][1]['area']
    p.text((ox+12,675),f'{area} pixels detached in 8-connectivity',font=small,fill=(238,234,231))
    p.text((ox+12,704),f'ROI: x{x0}..{x1-1}, y{y0}..{y1-1}',font=small,fill=(238,234,231))
    p.text((ox+12,740),'Only source PNGs; nearest scaling.',font=small,fill=(212,220,215))
    p.text((ox+12,768),'Coordinates: native 64 x 96 frame.',font=small,fill=(212,220,215))
strict.save(OUT/'confirmed_detached_3_examples.png')

temporal=[]
for d in ('down','left','right','up'):
    for frame in range(4):
        next_frame=(frame+1)%4
        first=np.array(Image.open(FRAMES/(path_name(d,frame)+'.png')).convert('RGBA'))
        second=np.array(Image.open(FRAMES/(path_name(d,next_frame)+'.png')).convert('RGBA'))
        temporal.append({'direction':d,'from_frame':frame,'to_frame':next_frame,
            'loop_boundary':frame==3,'changed_rgba_pixels':int(np.any(first!=second,axis=2).sum()),
            'changed_alpha_pixels':int((first[:,:,3]!=second[:,:,3]).sum()),
            'from_components8':len(fixture(d,frame)['components8']),
            'to_components8':len(fixture(d,next_frame)['components8']),
            'interpretation':'Motion legitimately changes pixels; these counts are not by themselves defects. Component disappearance identifies confirmed fragment flicker in down/left.'})

report={'status':'CONFIRMED_SOURCE_PIXEL_DEFECTS','reviewed_png_frames':20,'reviewed_walk_frames':16,
        'confirmed_defect_frame_count':len({i['frame'] for i in issues if i['severity']=='confirmed'}),
        'confirmed_defect_frames':sorted({i['frame'] for i in issues if i['severity']=='confirmed'}),
        'joint_seam_review_frame_count':len({i['frame'] for i in issues if i['severity']=='joint_seam_review_required'}),
        'joint_seam_review_frames':sorted({i['frame'] for i in issues if i['severity']=='joint_seam_review_required'}),
        'issues':issues, 'source_reconstruction':rebuild,
        'temporal_transitions_including_f03_to_f00':temporal,
        'input_sha256':stats['input_sha256'], 'rig_and_script_sha256':dependencies,
        'not_automatically_flagged':'Internal alpha holes can represent legal negative space, arm/body separation or armor vents. Diagnostic hole counts are candidates; only traced straight joint seams and eight-connected detached fragments are confirmed here.',
        'unconfirmed_minor_candidates':[{'frame':'robot_walk_down_f00_v001','coordinate_ranges':['19..23,50..63','41,39','23,43'],'reason':'Arm/body negative space and isolated alpha holes need a deliberate art judgement; not included in confirmed frame count.'},{'frame':'robot_walk_down_f02_v001','coordinate_ranges':['40,43'],'reason':'Small alpha hole; not independently confirmed as a tear.'},{'frame':'robot_walk_up_f00_v001','coordinate_ranges':['40..41,50'],'reason':'2px opening between arm and body after vertical swing; may be valid negative space, not a complete limb break.'},{'frame':'robot_walk_up_f02_v001','coordinate_ranges':['23..24,50'],'reason':'2px opening between arm and body after vertical swing; may be valid negative space, not a complete limb break.'}],
        'outputs':['robot_all20_4x.png','confirmed_detached_3_examples.png','joint_seams_and_fragments_6_examples_4x.png','left_boot_rig_split_proof_8x.png','native-pixel-statistics.json'],
        'formal_input_files_changed':False}
(OUT/'robot-quality-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'confirmed_defect_frame_count':report['confirmed_defect_frame_count'],'confirmed_defect_frames':report['confirmed_defect_frames'],'source_reconstruction_different_pixels':[r['differing_pixels'] for r in rebuild]},indent=2))
