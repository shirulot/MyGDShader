"""Independent source-mask, projected-pose and CPU sampling audit for P20.

Original RGB is never changed. Singular projected connectors are recorded and
not inverted: their polygons collapse and produce no area in the renderer.
"""
from pathlib import Path
from PIL import Image
import hashlib,json,math,zipfile

B=Path(__file__).resolve().parent;P=B/'technical-package';ROOT=B.parents[3]
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rgba=lambda p:Image.open(p).convert('RGBA')
def inside(x,y,poly):
    state=False
    for i,(ax,ay) in enumerate(poly):
        bx,by=poly[(i+1)%len(poly)];cross=(x-ax)*(by-ay)-(y-ay)*(bx-ax)
        if abs(cross)<1e-10 and min(ax,bx)<=x<=max(ax,bx) and min(ay,by)<=y<=max(ay,by):return True
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:state=not state
    return state
def round_godot(x):return math.floor(x+.5) if x>=0 else math.ceil(x-.5)
def add(a,b):return [a[0]+b[0],a[1]+b[1]]
def sub(a,b):return [a[0]-b[0],a[1]-b[1]]
def project(v,c):return [round_godot(v[1]*c['heading'][0]*.7),round_godot(-v[0]*.75+v[1]*.35*c['heading'][1])]
def world_knee(bob,depth,lift):
    hip=[32-bob/.75,0];ankle=[8+lift,depth];axis=sub(ankle,hip);length=math.hypot(*axis);unit=[a/length for a in axis];bend=math.sqrt(max(0,169-length*length/4))
    return [hip[0]+unit[0]*length/2+unit[1]*bend,hip[1]+unit[1]*length/2-unit[0]*bend]
def segment(part,start,end):
    rest=sub(part['end'],part['pivot']);cur=sub(end,start);rl=math.hypot(*rest);cl=math.hypot(*cur);ra=[a/rl for a in rest];rn=[-ra[1],ra[0]];ta=[a/rl for a in cur];tn=[-cur[1]/cl,cur[0]/cl] if cl else [0,0]
    return {'position':start,'basis_x':[ta[j]*ra[0]+tn[j]*rn[0] for j in [0,1]],'basis_y':[ta[j]*ra[1]+tn[j]*rn[1] for j in [0,1]]}
def pose(c,phase):
    transforms={'body':{'position':[0,phase['body_y']],'basis_x':[1,0],'basis_y':[0,1]}};supports={}
    for s in ['right','left']:
        leg=c['legs'][s];foot=phase[s];hip=add(leg['hip'],[0,phase['body_y']]);knee=add(leg['knee'],project(sub(world_knee(phase['body_y'],foot['depth'],foot['lift']),world_knee(0,0,0)),c));ankle=add(leg['ankle'],project([foot['lift'],foot['depth']],c))
        supports[s]={'hip':hip,'knee':knee,'ankle':ankle,'sole':add(ankle,leg['sole_offset']),'ground':add(add(leg['ankle'],leg['sole_offset']),project([0,foot['depth']],c)),'support':foot['support'],'depth':foot['depth'],'lift':foot['lift']}
        for part in c['parts']:
            if part['id']==s+'_thigh':transforms[part['id']]=segment(part,hip,add(knee,sub(part['end'],leg['knee'])))
            elif part['id']==s+'_shin':transforms[part['id']]=segment(part,add(knee,sub(part['pivot'],leg['knee'])),add(ankle,sub(part['end'],leg['ankle'])))
        for suffix,position in [('cap',knee),('foot',ankle)]:transforms[s+'_'+suffix]={'position':position,'basis_x':[1,0],'basis_y':[0,1]}
    return transforms,supports
def equal(a,b,tol=2e-5):
    if isinstance(a,dict):return set(a)==set(b) and all(equal(a[k],b[k],tol) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(equal(x,y,tol) for x,y in zip(a,b))
    if isinstance(a,(float,int)) and not isinstance(a,bool):return abs(a-b)<tol
    return a==b

manifest=load(P/'manifest.json');listed=manifest['files'];actual={f.relative_to(P).as_posix() for f in P.rglob('*') if f.is_file()};rig=load(P/'rig.json');cat=load(P/'output/catalog.json');receipt=load(P/'SOURCE_RECEIPT.json')
out={'manifest':{'sha256':sha(P/'manifest.json'),'listed':len(listed),'missing':sorted(set(listed)-actual),'extra':sorted(actual-set(listed)-{'manifest.json'}),'bad':[f for f,r in listed.items() if not (P/f).exists() or sha(P/f)!=r['sha256'] or (P/f).stat().st_size!=r['bytes']]},
     'catalog':{'sha256':sha(P/'output/catalog.json'),'rig_sha256':sha(P/'rig.json'),'tres_sha256':sha(P/cat['tres'].removeprefix('res://')),'rig_sha_exact':sha(P/'rig.json')==cat['rig_sha256'],'tres_sha_exact':sha(P/cat['tres'].removeprefix('res://'))==cat['tres_sha256'],'clip_names':[c['action'] for c in cat['clips']],'not_made':rig['not_made'],'root':cat['root'],'canvas':cat['canvas']},
     'sources':[],'binds':[],'clips':[],'preserved':[],'singular_connectors':[]}
staticzip=ROOT/'art-source/ember/deliveries/enemy_patrol_seven_directions_v013_s002_2026-10-06.zip';downzip=ROOT/'art-source/ember/deliveries/enemy_sequences_v012_2026-10-06.zip';sezip=ROOT/'art-source/ember/deliveries/enemy_eight_directions_v013_pilot_patrol_v001_2026-10-06.zip'
out['source_zips']=[{'file':z.name,'sha256':sha(z),'receipt_exact':sha(z)==receipt[k]} for z,k in [(staticzip,'static_zip_sha256'),(downzip,'down_zip_sha256'),(sezip,'down_right_zip_sha256')]]
with zipfile.ZipFile(staticzip) as z:
    for d in receipt['source_png_hashes']:
        path=P/'source'/d;direction=d[:-4];out['sources'].append({'direction':direction,'sha256':sha(path),'receipt_sha_exact':sha(path)==receipt['source_png_hashes'][d],
                        's002_static_byte_exact':path.read_bytes()==z.read('neutral_'+d),'preview_neutral_byte_exact':path.read_bytes()==(P/'output/enemy_patrol'/('neutral_'+d)).read_bytes()})
models={}
for d,c in rig['configs'].items():
    src=rgba(P/c['source'].removeprefix('res://'));parts=[{'id':'body','pivot':[0,0],'polygon':[],'exclude':[p['polygon'] for p in c['parts']],'z':5}]+c['parts'];masks={};opaque_counts={}
    for part in parts:
        points=set()
        for y in range(128):
            for x in range(128):
                owned=not part['polygon'] or inside(x+.5,y+.5,part['polygon'])
                if any(inside(x+.5,y+.5,s) for s in part['exclude']):owned=False
                if any(inside(x+.5,y+.5,s) for s in c['protected_body_polygons']):owned=part['id']=='body'
                if owned:points.add((x,y))
        masks[part['id']]=points;opaque_counts[part['id']]=sum(src.getpixel(xy)[3]>=128 for xy in points)
        mask=Image.new('L',(128,128));
        for xy in points:mask.putpixel(xy,255)
        mask.save(B/f'technical-mask-{d}-{part["id"]}.png')
    opaque={(x,y) for y in range(128) for x in range(128) if src.getpixel((x,y))[3]>=128};protected={xy for xy in opaque if any(inside(xy[0]+.5,xy[1]+.5,s) for s in c['protected_body_polygons'])}
    models[d]=(src,c,parts,masks,protected)
    out['binds'].append({'direction':d,'source_sha_config_exact':sha(P/c['source'].removeprefix('res://'))==c['source_sha256'],'actual_bind_rgba_difference':sum(a!=b for a,b in zip(src.getdata(),rgba(P/f'qa/bind_{d}.png').getdata())),
                        'unowned_original_opaque':len(opaque-set.union(*masks.values())),'multiple_owners_original_opaque':sum(sum(xy in ms for ms in masks.values())>1 for xy in opaque),'part_opaque_counts':opaque_counts,
                        'protected_body_opaque':len(protected),'protected_stolen_by_leg_parts':sum(xy in ms for k,ms in masks.items() if k!='body' for xy in protected)})

def reconstruct(model,tr):
    src,c,parts,masks,protected=model;image=Image.new('RGBA',(128,128),(255,255,255,0));owners={}
    for n,part in sorted(enumerate(parts),key=lambda a:(a[1]['z'],a[0])):
        t=tr[part['id']];a,b=t['basis_x'];cc,dd=t['basis_y'];det=a*dd-b*cc
        if abs(det)<1e-12:continue
        for y in range(128):
            for x in range(128):
                qx=x+.5-t['position'][0];qy=y+.5-t['position'][1];uv=((dd*qx-cc*qy)/det+part['pivot'][0],(-b*qx+a*qy)/det+part['pivot'][1]);xy=(math.floor(uv[0]),math.floor(uv[1]))
                if xy not in masks[part['id']] or not (0<=xy[0]<128 and 0<=xy[1]<128):continue
                color=src.getpixel(xy)
                if color[3]>=128:image.putpixel((x,y),(*color[:3],255));owners[(x,y)]={'part':part['id'],'source_xy':xy,'source_uv':uv}
    return image,owners

for c in cat['clips']:
    path=P/c['atlas'].removeprefix('res://');atlas=rgba(path);d=c['direction'];cr={'action':c['action'],'direction':d,'atlas_sha_exact':sha(path)==c['atlas_sha256'],'configuration_exact':c['frame_count']==8 and c['fps']==8 and c['loop'] is True,'atlas_size':list(atlas.size),'frames':[]}
    for i in range(8):
        fp=path.with_suffix('')/f'f{i:02d}.png';im=rgba(fp);fr={'frame':i,'file':fp.relative_to(P).as_posix(),'sha_exact':sha(fp)==c['frame_hashes'][i],'atlas_difference':sum(a!=b for a,b in zip(im.getdata(),atlas.crop((i*128,0,(i+1)*128,128)).getdata())),
                                'nonbinary_alpha':sum(a[3] not in [0,255] for a in im.getdata()),'size':list(im.size),'alpha_bbox':im.getchannel('A').getbbox()}
        if d in models:
            tr,supports=pose(rig['configs'][d],rig['phases'][i]);expected,owners=reconstruct(models[d],tr);res=[]
            for y in range(128):
                for x in range(128):
                    a=expected.getpixel((x,y));z=im.getpixel((x,y))
                    if a!=z:res.append({'xy':[x,y],'cpu_rgba':a,'actual_rgba':z,'owner':owners.get((x,y))})
            src,cfg,parts,masks,prot=models[d];bob=rig['phases'][i]['body_y'];tool_diffs=[]
            for x,y in prot:
                target=(x,y+bob)
                if im.getpixel(target)!=src.getpixel((x,y)):tool_diffs.append({'source_xy':[x,y],'target_xy':target,'original_rgba':src.getpixel((x,y)),'actual_rgba':im.getpixel(target)})
            singular=[];endpoint_errors=[]
            for part in cfg['parts']:
                if part['end'] is None:continue
                t=tr[part['id']];a,b=t['basis_x'];cc,dd=t['basis_y'];det=a*dd-b*cc
                rest=sub(part['end'],part['pivot']);mapped=add(t['position'],[a*rest[0]+cc*rest[1],b*rest[0]+dd*rest[1]])
                side=part['id'].split('_')[0];leg=cfg['legs'][side];expected_end=add(supports[side]['knee'],sub(part['end'],leg['knee'])) if part['id'].endswith('thigh') else add(supports[side]['ankle'],sub(part['end'],leg['ankle']))
                endpoint_errors.append(math.hypot(*sub(mapped,expected_end)))
                if abs(det)<1e-12:
                    singular.append(part['id']);out['singular_connectors'].append({'direction':d,'frame':i,'part':part['id'],'source_pivot':part['pivot'],'source_end':part['end'],'target_start':t['position'],'target_end':mapped,'basis_x':t['basis_x'],'basis_y':t['basis_y']})
            fr.update({'pose_transforms_exact':equal(tr,c['poses'][i]['part_transforms']),'supports_exact':equal(supports,c['poses'][i]['supports']),
                       'caps_boots_rigid_identity':all(t['basis_x']==[1,0] and t['basis_y']==[0,1] for key,t in tr.items() if key.endswith('cap') or key.endswith('foot')),
                       'connector_endpoint_max_error':max(endpoint_errors),'singular_connectors':singular,'protected_tool_differences':tool_diffs,
                       'cpu_residual_count':len(res),'cpu_residual':res,'cpu_alpha_residual':sum(r['cpu_rgba'][3]!=r['actual_rgba'][3] for r in res),'independent_transforms':tr,'independent_supports':supports})
        cr['frames'].append(fr)
    out['clips'].append(cr)
for direction,zpath in [('down',downzip),('down_right',sezip)]:
    with zipfile.ZipFile(zpath) as z:
        c=next(c for c in cat['clips'] if c['direction']==direction);rel=c['atlas'].removeprefix('res://');files=[rel]+[rel[:-4]+f'/f{i:02d}.png' for i in range(8)]
        for f in files:
            candidates=[n for n in z.namelist() if n==f or n.endswith('/'+f.removeprefix('output/'))]
            assert len(candidates)==1,(f,candidates)
            out['preserved'].append({'file':f,'source_zip':zpath.name,'byte_exact':(P/f).read_bytes()==z.read(candidates[0])})
(B/'technical-pixel-integrity.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
nf=[f for c in out['clips'] for f in c['frames'] if 'cpu_residual_count' in f];af=[f for c in out['clips'] for f in c['frames']]
summary={'manifest':out['manifest'],'catalog':out['catalog'],'all_8_s002_source_and_static_preview_bytes_exact':all(x['s002_static_byte_exact'] and x['preview_neutral_byte_exact'] and x['receipt_sha_exact'] for x in out['sources']),
         'all_16_old_frames_2_atlas_bytes_exact':all(r['byte_exact'] for r in out['preserved']),'frames':len(af),'new_frames':len(nf),'all_hashes_configuration_exact':all(c['atlas_sha_exact'] and c['configuration_exact'] for c in out['clips']) and all(f['sha_exact'] for f in af),
         'atlas_difference':sum(f['atlas_difference'] for f in af),'nonbinary_alpha':sum(f['nonbinary_alpha'] for f in af),'all_32_pose_supports_exact':all(f['pose_transforms_exact'] and f['supports_exact'] for f in nf),
         'all_caps_boots_rigid':all(f['caps_boots_rigid_identity'] for f in nf),'protected_tool_difference_total':sum(len(f['protected_tool_differences']) for f in nf),
         'bind_rgba_difference':sum(x['actual_bind_rgba_difference'] for x in out['binds']),'connector_endpoint_max_error':max(f['connector_endpoint_max_error'] for f in nf),'singular_connectors':out['singular_connectors'],
         'cpu_residual_total':sum(f['cpu_residual_count'] for f in nf),'cpu_alpha_residual_total':sum(f['cpu_alpha_residual'] for f in nf),'per_direction_cpu':{c['direction']:[f['cpu_residual_count'] for f in c['frames']] for c in out['clips'] if c['direction'] in models}}
(B/'technical-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
