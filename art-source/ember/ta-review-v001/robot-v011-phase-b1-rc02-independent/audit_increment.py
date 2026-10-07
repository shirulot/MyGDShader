"""TA只读增量审计：独立验源片、修订范围、骨点反相；不调用作者生成脚本。"""
from pathlib import Path
from PIL import Image
import ast, collections, hashlib, json, math, re

HERE = Path(__file__).resolve().parent
PACK = HERE / 'package'
OLD = HERE.parent / 'robot-v011-phase-b1-rc01-independent/package'
W, H = 64, 96
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def rgba(p): return Image.open(p).convert('RGBA')
def mismatch(a, b): return sum(x != y for x, y in zip(a.getdata(), b.getdata()))

# 复用上一轮TA独立像素中心逆映射函数，不执行上一轮全量审计。
old_audit = ast.parse((OLD.parent / 'audit_integrity.py').read_text(encoding='utf-8'))
functions = [n for n in old_audit.body if isinstance(n, ast.FunctionDef) and n.name in ['stamp', 'render', 'protection']]
exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])), '<TA independent renderer>', 'exec'))

manifest = load(PACK / 'sha256-manifest.json')
listed = {q['file']: q for q in manifest['files']}
actual = {p.relative_to(PACK).as_posix() for p in PACK.rglob('*') if p.is_file()}
bad = [f for f,q in listed.items() if not (PACK/f).is_file() or sha((PACK/f).read_bytes()) != q['sha256'] or len((PACK/f).read_bytes()) != q['bytes']]
result = {'manifest': {'sha256':sha((PACK/'sha256-manifest.json').read_bytes()), 'listed':len(manifest['files']), 'unique':len(listed), 'bad':bad, 'extra':sorted(actual-set(listed)-{'sha256-manifest.json'}), 'missing':sorted(set(listed)-actual)}}
meta = load(PACK/'walk-batch-metadata.json')
atlas = rgba(PACK/meta['atlas'])
result['metadata_atlas'] = {'metadata_sha256':sha((PACK/'walk-batch-metadata.json').read_bytes()), 'atlas_sha256':sha((PACK/meta['atlas']).read_bytes()), 'atlas_size':list(atlas.size), 'godot_metadata_byte_exact':(PACK/'walk-batch-metadata.json').read_bytes()==(PACK/'godot-walk-review/walk-batch-metadata.json').read_bytes(), 'godot_atlas_byte_exact':(PACK/meta['atlas']).read_bytes()==(PACK/'godot-walk-review/assets'/meta['atlas']).read_bytes(), 'frames':[]}
palette = {tuple(bytes.fromhex(h)) for h in ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A']}
changed_files, same_files = [], []
for q in meta['source_files']:
    f=q['file'];im=rgba(PACK/f);x,y,w,h=q['region'];colors=collections.Counter(im.getdata())
    same=(PACK/f).read_bytes()==(OLD/f).read_bytes()
    (same_files if same else changed_files).append(f)
    result['metadata_atlas']['frames'].append({'file':f,'metadata_sha_exact':sha((PACK/f).read_bytes())==q['sha256'],'atlas_rgba_mismatch':mismatch(im,atlas.crop((x,y,x+w,y+h))),'unchanged_from_rc01':same,'nonbinary_alpha':sum(n for p,n in colors.items() if p[3] not in [0,255]),'off_palette':sum(n for p,n in colors.items() if p[3] and p[:3] not in palette)})
result['revision_files']={'changed':changed_files,'unchanged':same_files}

scope=load(PACK/'qa/arm_phase_revision_scope.json')
directions=scope['directions'];source_results=[];phase_results=[]
evidence=load(PACK/'qa/arm_phase_revision_evidence.json')
result['declared_unchanged']=[{'file':q['file'],'actual_sha256':sha((PACK/q['file']).read_bytes()),'sha_exact':sha((PACK/q['file']).read_bytes())==q['sha256'],'old_bytes_exact':(PACK/q['file']).read_bytes()==(OLD/q['file']).read_bytes()} for q in evidence['unchanged_files']]
for d in directions:
    ledger=load(PACK/f'source/fixed-rig-pilot/{d}/rig_and_poses.json');previous=load(OLD/f'source/fixed-rig-pilot/{d}/rig_and_poses.json');rig=ledger['rig'];parts={q['id']:rgba(PACK/q['file']) for q in ledger['parts']};old_parts={q['id']:rgba(OLD/q['file']) for q in previous['parts']}
    references=[]
    for p in (PACK/scope['reference_root']/d).rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(PACK/scope['reference_root']/d).as_posix()
        if rel.startswith('parts/'):
            old_path=OLD/next(q['file'] for q in previous['parts'] if q['id']==Path(rel).stem)
        else:old_path=OLD/(f'frames/walk/{d}/{rel}' if rel.startswith('robot_walk_') else f'source/fixed-rig-pilot/{d}/{rel}')
        references.append({'file':p.relative_to(PACK).as_posix(),'old_path':old_path.relative_to(OLD).as_posix(),'old_bytes_exact':p.read_bytes()==old_path.read_bytes()})
    part_deltas=[]
    for key,part in parts.items():
        for y in range(H):
            for x in range(W):
                a,b=old_parts[key].getpixel((x,y)),part.getpixel((x,y))
                if a!=b:part_deltas.append({'part':key,'xy':[x,y],'before':list(a),'after':list(b)})
    neutral=Image.new('RGBA',(W,H))
    for lid in rig['limb_order']:
        ids=['body'] if lid=='body' else [lid+'_'+s for s in ['end','lower','upper'] if lid+'_'+s in parts]
        for key in ids:
            for y in range(H):
                for x in range(W):
                    if parts[key].getpixel((x,y))[3]:neutral.putpixel((x,y),parts[key].getpixel((x,y)))
    guards={};arm_masks={};old_arm_masks={};ownership_old={};ownership_new={}
    for key,part in parts.items():
        arm_masks[key]=protection(part,0,H-1) if key.startswith('arm_') else Image.new('RGBA',(W,H))
        old_arm_masks[key]=protection(old_parts[key],0,H-1) if key.startswith('arm_') else Image.new('RGBA',(W,H))
        ownership_old[key]=Image.new('RGBA',(W,H));ownership_new[key]=Image.new('RGBA',(W,H))
        if key=='body':guards[key]=part.copy();continue
        lid=re.sub(r'_(upper|lower|end)$','',key);limb=rig['limbs'][lid]
        if key.endswith('_end'):lo,hi=0,H-1
        elif limb['kind']=='leg':lo,hi=(0,math.floor(limb['joint'][1]-2.5)) if key.endswith('_upper') else (math.ceil(limb['joint'][1]+2),math.floor(limb['end'][1]-2))
        else:lo,hi=(0,math.floor(limb['joint'][1]-1.5)) if key.endswith('_upper') else (math.ceil(limb['joint'][1]+2),H-1)
        guards[key]=protection(part,lo,hi)
    for q in part_deltas:
        if q['before'][3]:ownership_old[q['part']].putpixel(tuple(q['xy']),(255,255,255,255))
        if q['after'][3]:ownership_new[q['part']].putpixel(tuple(q['xy']),(255,255,255,255))
    quant=rgba(PACK/f'source/walk_{d}_joint_edit_quantized_v011.png');patch=load(PACK/f'qa/{d}_joint_patch_v011.json');frames=[]
    for i,state in enumerate(ledger['states']):
        prev=previous['states'][i];stem=f'robot_walk_{d}_f{i:02d}_v011.png';before=rgba(OLD/f'frames/walk/{d}/{stem}');final=rgba(PACK/f'frames/walk/{d}/{stem}');raw=render(parts,rig,state);guard=render(guards,rig,state)
        oldarm=render(old_arm_masks,previous['rig'],prev);newarm=render(arm_masks,rig,state);oldown=render(ownership_old,previous['rig'],prev);newown=render(ownership_new,rig,state)
        regions=[];armregions=[]
        for lid,j in state['joints'].items():
            if lid.startswith('leg'):regions.extend([(j['root'],3.2,3.2),(j['joint'],4.8,4.8),(j['ankle'],4,3.5)])
            else:regions.extend([(j['root'],3.4,3.4),(j['joint'],3.5,3.5)])
        for s in [prev,state]:
            for lid,j in s['joints'].items():
                if lid.startswith('arm_'):armregions.extend([(j['root'],3.4,3.4),(j['joint'],3.5,3.5)])
        jointmask=Image.new('RGBA',(W,H));revisionmask=Image.new('RGBA',(W,H));expected=raw.copy()
        for y in range(H):
            for x in range(W):
                xy=(x,y)
                if y>=45 and not guard.getpixel(xy)[3] and any(((x+.5-c[0])/rx)**2+((y+.5-c[1])/ry)**2<=1 for c,rx,ry in regions):
                    jointmask.putpixel(xy,(255,255,255,255));q=quant.getpixel(((i%4)*W+x,(i//4)*H+y))
                    if q[3] or not raw.getpixel(xy)[3]:expected.putpixel(xy,q)
                inside=y>=45 and (any(m.getpixel(xy)[3] for m in [oldarm,newarm,oldown,newown]) or any(((x+.5-c[0])/rx)**2+((y+.5-c[1])/ry)**2<=1 for c,rx,ry in armregions))
                if inside:revisionmask.putpixel(xy,(255,255,255,255))
                else:expected.putpixel(xy,before.getpixel(xy))
        rawdiff=[(x,y) for y in range(H) for x in range(W) if raw.getpixel((x,y))!=final.getpixel((x,y))]
        olddiff=[(x,y) for y in range(H) for x in range(W) if before.getpixel((x,y))!=final.getpixel((x,y))]
        ownership_positions={'old':[(x,y) for y in range(H) for x in range(W) if oldown.getpixel((x,y))[3]],'new':[(x,y) for y in range(H) for x in range(W) if newown.getpixel((x,y))[3]]}
        frames.append({'frame':i,'raw_rigid_mismatch':mismatch(raw,rgba(PACK/f'source/fixed-rig-pilot/{d}/{stem}')),'composite_mismatch':mismatch(expected,final),'joint_mask_mismatch':mismatch(jointmask,rgba(PACK/f'qa/{d}_joint_mask_f{i:02d}.png')),'revision_mask_mismatch':mismatch(revisionmask,rgba(PACK/f'qa/{d}_arm_revision_mask_f{i:02d}.png')),'old_final_changed_pixels':len(olddiff),'outside_revision_changed':sum(not revisionmask.getpixel(xy)[3] for xy in olddiff),'protected_pixels_changed_vs_new_raw':sum(bool(guard.getpixel(xy)[3]) for xy in rawdiff),'outside_joint_mask_changed_vs_new_raw':sum(not jointmask.getpixel(xy)[3] for xy in rawdiff),'body_leg_transforms_equal':all(t==prev['transforms'][key] for key,t in state['transforms'].items() if key=='body' or key.startswith('leg_')),'leg_joints_equal':all(j==prev['joints'][key] for key,j in state['joints'].items() if key.startswith('leg_')),'body_bob_equal':state['bob']==prev['bob'],'ownership_positions':ownership_positions,'ownership_position_mask_covered':all(revisionmask.getpixel(xy)[3] for positions in ownership_positions.values() for xy in positions)})
    phase=[];bone_errors=[]
    for side in ['left','right']:
        lid='arm_'+side;leg='leg_'+side;f=rig['forward'];a,b=ledger['states'][0]['joints'],ledger['states'][4]['joints'];ad=[b[lid]['wrist'][k]-a[lid]['wrist'][k] for k in [0,1]];ld=[b[leg]['ankle'][k]-a[leg]['ankle'][k] for k in [0,1]];ap=sum(ad[k]*f[k] for k in [0,1]);lp=sum(ld[k]*f[k] for k in [0,1]);norm=math.hypot(*f)
        phase.append({'side':side,'frames':[0,4],'wrist_delta':ad,'ankle_delta':ld,'forward':f,'arm_dot_forward':ap,'leg_dot_forward':lp,'arm_unit_axis_delta':ap/norm,'leg_unit_axis_delta':lp/norm,'opposed':ap*lp<0})
        l=rig['limbs'][lid];l1=math.dist(l['root'],l['joint']);l2=math.dist(l['joint'],l['end'])
        for i,s in enumerate(ledger['states']):
            j=s['joints'][lid];bone_errors.append({'side':side,'frame':i,'upper_length_error':abs(math.dist(j['root'],j['joint'])-l1),'lower_length_error':abs(math.dist(j['joint'],j['wrist'])-l2),'arm_root_equal_previous':j['root']==previous['states'][i]['joints'][lid]['root'],'wrist_target_y_error':abs(j['wrist'][1]-(l['end'][1]+.60*[1,.6,0,-.6,-1,-.6,0,.6][(i+(0 if side=='left' else 4))%8])) if d=='up' else None})
    source_results.append({'direction':d,'rig_same_as_rc01':rig==previous['rig'],'master_bytes_same_as_rc01':(PACK/ledger['source_file']).read_bytes()==(OLD/previous['source_file']).read_bytes(),'reference_copy_checks':references,'part_deltas':part_deltas,'neutral_reassembly_mismatch':mismatch(neutral,rgba(PACK/ledger['source_file'])),'frames':frames,'fixed_bone_errors':bone_errors,'qa_fixed_ledger_byte_exact':(PACK/f'qa/{d}_fixed_rig_v011.json').read_bytes()==(PACK/f'source/fixed-rig-pilot/{d}/rig_and_poses.json').read_bytes(),'source_image_sha256':sha((PACK/patch['source_file']).read_bytes()),'declared_source_hash_exact':sha((PACK/patch['source_file']).read_bytes())==patch['source_sha256']})
    phase_results.append({'direction':d,'projection_note':'dot_forward uses the stored non-unit ground axis, so absolute values are weighted pixels; unit-axis values are also recorded. Ankles are rig endpoints, not pixel foot-contact proof.','pairs':phase})
result['sources']=source_results;result['phase']=phase_results
(HERE/'incremental-integrity.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('MANIFEST', result['manifest'])
print('REVISION changed/same',len(changed_files),len(same_files),'atlas',atlas.size)
for d in source_results:
    print('SOURCE',d['direction'],'parts deltas',d['part_deltas'],'neutral',d['neutral_reassembly_mismatch'],'references exact',all(q['old_bytes_exact'] for q in d['reference_copy_checks']))
    print('FRAME',[(q['frame'],q['raw_rigid_mismatch'],q['composite_mismatch'],q['joint_mask_mismatch'],q['revision_mask_mismatch'],q['outside_revision_changed'],q['protected_pixels_changed_vs_new_raw'],q['outside_joint_mask_changed_vs_new_raw']) for q in d['frames']])
for d in phase_results:print('PHASE',d['direction'],[(q['side'],q['arm_dot_forward'],q['leg_dot_forward'],q['opposed']) for q in d['pairs']])
