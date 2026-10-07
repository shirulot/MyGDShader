"""独立反采样原部件/保护区/固定支撑组装，逐点复核八源腰髋采纳与112PNG边界。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,json,math,numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];P=OUT/'technical-package';R=P/'runtime';BASE=ROOT/'art-source/ember/robot-eight-way-v011';OLD=BASE/'delivery/robot-v011'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();js=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));arr=lambda p:np.array(Image.open(p).convert('RGBA'))
meta=js(R/'full-action-metadata.json');oldmeta=js(OLD/'full-action-metadata.json');run=js(P/'run-manifest.json');mapping=js(P/'source/fixed-source-mapping.json');generation=js(P/'source/imagegen-ledger.json')
assert len(meta['clips'])==24 and meta['canvas']==[64,96] and meta['root_anchor']==[32,80]
assert sha(R/meta['atlas'])==meta['atlas_sha256']=='4c964f4d4d633b98c743d496354bce6e1d91f3c1cbefa741cf5055c6f5db7aac'
atlas=arr(R/meta['atlas']);assert atlas.shape==(2304,512,4)
palette=np.array([[int(h[i:i+2],16) for i in [0,2,4]] for h in ['101820','182631','2b3e4b','4d6470','829ba3','becbc4','566b78','ece9d8','7b4d35','b77c4b','e2b77a']],dtype=np.int32)
allowed={tuple(c) for c in palette};frames=[];changes=[]
for clip in meta['clips']:
    oldclip=next(c for c in oldmeta['clips'] if c['name']==clip['name']);expected_n={'idle':2,'walk':8,'collect':4}[clip['action']]
    assert len(clip['frames'])==expected_n and clip['fps']=={'idle':2,'walk':8,'collect':6}[clip['action']] and clip['loop']==(clip['action']!='collect')
    for f in clip['frames']:
        fp=R/f['file'];im=arr(fp);oldf=oldclip['frames'][f['frame']];old=arr(OLD/oldf['file']);x,y,w,h=f['region']
        assert sha(fp)==f['sha256'] and im.shape==(96,64,4) and [w,h]==[64,96] and np.array_equal(im,atlas[y:y+h,x:x+w]) and set(np.unique(im[:,:,3])).issubset({0,255}) and all(tuple(rgb) in allowed for rgb in im[im[:,:,3]>0,:3])
        same=fp.read_bytes()==(OLD/oldf['file']).read_bytes()
        if not same:
            assert clip['action']=='collect' and f['frame'] in [1,2] and np.array_equal(im[:53],old[:53]);changes.append({'clip':clip['name'],'frame':f['frame'],'old_file':oldf['file'],'before_sha256':sha(OLD/oldf['file']),'after_sha256':sha(fp)})
        if clip['action']=='collect':
            assert fp.read_bytes()==(P/f['file']).read_bytes() and np.array_equal(im[70:],arr(P/f'source/{clip["direction"]}/baseline_f3.png')[70:])
        frames.append({'clip':clip['name'],'frame':f['frame'],'file':f['file'],'same_v011_bytes':same,'rgba_atlas_exact':True,'upper_before_y53_equal':bool(np.array_equal(im[:53],old[:53]))})
assert len(frames)==112 and len(changes)==16 and sum(f['same_v011_bytes'] for f in frames)==96
assert [(c['clip'],c['frame'],c['before_sha256'],c['after_sha256']) for c in changes]==[(c['clip'],c['frame'],c['before_sha256'],c['after_sha256']) for c in run['changes']]
mapped=[]
for m in mapping:
    assert sha(P/m['copy'])==m['sha256']==sha(BASE/m['original']);mapped.append({'copy':m['copy'],'original':m['original'],'sha256':m['sha256']})
assert len(mapping)==96
yy,xx=np.indices((96,64));X,Y=xx+.5,yy+.5
def stamp(part,t):
    a=t['radians'];c,s=math.cos(a),math.sin(a);dx=X-t['targetPivot'][0];dy=Y-t['targetPivot'][1];sx=np.floor(dx*c+dy*s+t['sourcePivot'][0]).astype(int);sy=np.floor(-dx*s+dy*c+t['sourcePivot'][1]).astype(int);cx,cy=np.clip(sx,0,63),np.clip(sy,0,95)
    use=(sx>=0)&(sx<64)&(sy>=0)&(sy<96)&(part[cy,cx,3]>0);out=np.zeros((96,64,4),np.uint8);out[use]=part[cy[use],cx[use]];return out
def render(parts,rig,state):
    out=np.zeros((96,64,4),np.uint8)
    for name in rig['limb_order']:
        names=['pelvis','body'] if name=='body' else [name+'_'+suffix for suffix in ['end','lower','upper'] if name+'_'+suffix in parts]
        for key in names:
            image=stamp(parts[key],state['transforms'][key]);use=image[:,:,3]>0;out[use]=image[use]
    return out
def dilate(mask,radius):
    padded=np.pad(mask,radius);out=np.zeros(mask.shape,bool)
    for dy in range(radius*2+1):
        for dx in range(radius*2+1):out|=padded[dy:dy+96,dx:dx+64]
    return out
generation_rows=[];assembly_rows=[];patch_rows=[]
for e in generation:
    d=e['direction'];folder=P/'source'/d;ledger=js(P/f'source/fixed-source-record/{d}/original_rig_and_poses.json');poses=js(folder/'poses.json');parts={}
    original_ledger=BASE/f'source/{"action-rig-pilot" if d=="down_left" else "action-rig-batch"}/collect/{d}/rig_and_poses.json'
    assert (P/f'source/fixed-source-record/{d}/original_rig_and_poses.json').read_bytes()==original_ledger.read_bytes()
    for q in ledger['parts']:
        im=arr(P/f'source/fixed-source-record/{d}/{q["id"]}.png');assert hashlib.sha256(im.tobytes()).hexdigest()==q['raw_sha256'];parts[q['id']]=im
    for key,file in [('source_sha256','source'),('input_sha256','actual_input'),('prompt_sha256','prompt')]:assert sha(P/e[file])==e[key]
    assert e in run['generation']
    original_output=Path(e['original_output']);original_file_present=original_output.exists()
    if original_file_present:assert sha(original_output)==e['source_sha256']
    prompt=(P/e['prompt']).read_text(encoding='utf-8');assert '2-column by 2-row' in prompt and '21' in prompt and '62' in prompt
    inp=arr(P/e['actual_input']);assert inp.shape==(768,512,4)
    input_small=np.array(Image.fromarray(inp).resize((128,192),Image.Resampling.NEAREST))
    edit=arr(OUT/f'technical-resampled-{d}.png');assert edit.shape==(192,128,4)
    lower={k:v if k=='pelvis' or k.startswith('leg_') else np.zeros_like(v) for k,v in parts.items()}
    upper={k:np.zeros_like(v) if k=='pelvis' or k.startswith('leg_') else v for k,v in parts.items()}
    arms={k:v if k.startswith('arm_') else np.zeros_like(v) for k,v in parts.items()}
    guardparts={k:v if k=='body' or k.startswith('arm_') else np.zeros_like(v) for k,v in parts.items()}
    input_diffs=[];common_patch=[]
    for f in range(4):
        state=poses['frames'][f]['state'];oldstate=ledger['states'][f];original=arr(folder/f'baseline_f{f}.png');raw=arr(folder/f'fixed_support_raw_f{f}.png');actual=arr(P/f'frames/collect/{d}/robot_collect_{d}_f{f:02d}_v012.png')
        prior=next(c for c in oldmeta['clips'] if c['name']=='collect_'+d)['frames'][f]
        assert (folder/f'baseline_f{f}.png').read_bytes()==(OLD/prior['file']).read_bytes()
        expected_state=json.loads(json.dumps(oldstate))
        if f in [1,2]:
            expected_state['transforms']['pelvis']={'sourcePivot':[32,56],'targetPivot':[32,56],'radians':0};expected_state['pelvis_shift']=[0,0]
            for name,limb in ledger['rig']['limbs'].items():
                if limb['kind']!='leg':continue
                for suffix,pivot in [('upper',limb['root']),('lower',limb['joint']),('end',limb['end'])]:expected_state['transforms'][name+'_'+suffix]={'sourcePivot':pivot,'targetPivot':pivot,'radians':0}
                expected_state['joints'][name]={'root':limb['root'],'joint':limb['joint'],'ankle':limb['end'],'lift':0,'contact':True}
        assert state==expected_state
        for name,limb in ledger['rig']['limbs'].items():
            if limb['kind']=='leg':assert state['joints'][name]['root']==limb['root'] and state['joints'][name]['joint']==limb['joint'] and state['joints'][name]['ankle']==limb['end']
        predicted_raw=original.copy()
        if f in [1,2]:
            assembled=render(parts,ledger['rig'],state);oldlower=render(lower,ledger['rig'],oldstate);newlower=render(lower,ledger['rig'],state);upperimage=render(upper,ledger['rig'],state);armimage=render(arms,ledger['rig'],state)
            replace=(Y>=53)&(upperimage[:,:,3]==0)&~dilate(armimage[:,:,3]>0,1)&(dilate(oldlower[:,:,3]>0,3)|dilate(newlower[:,:,3]>0,3));predicted_raw[replace]=assembled[replace]
        raw_res=np.any(predicted_raw!=raw,axis=2)
        sheetcell=input_small[(f//2)*96:(f//2+1)*96,(f%2)*64:(f%2+1)*64]
        input_res=(sheetcell[:,:,3]!=raw[:,:,3])|(np.any(sheetcell[:,:,:3]!=raw[:,:,:3],axis=2)&(raw[:,:,3]>0))
        input_diffs.append(int(input_res.sum()))
        guard=render(guardparts,ledger['rig'],state);predicted=raw.copy();used=[]
        if f in [1,2]:
            for y in range(58 if d=='down' else 54,63):
                for x in range(21,43):
                    color=edit[y,64+x]
                    if not raw[y,x,3] or guard[y,x,3] or color[3]<160:continue
                    rgb=palette[np.argmin(np.sum((palette-color[:3].astype(np.int32))**2,axis=1))].astype(np.uint8)
                    if not np.array_equal(rgb,raw[y,x,:3]):
                        predicted[y,x,:3]=rgb;used.append({'xy':[x,y],'sample_xy':[64+x,y],'source_resampled_rgba':color.tolist(),'adopted_rgba':predicted[y,x].tolist()})
        assert np.array_equal(predicted,actual) and np.array_equal(actual[:,:,3],raw[:,:,3]) and np.array_equal(actual[63:],raw[63:])
        mask=np.zeros((96,64),np.uint8)
        for p in used:mask[p['xy'][1],p['xy'][0]]=255
        Image.fromarray(mask).save(OUT/f'technical-adopt-mask-{d}-f{f:02d}.png')
        assembly_rows.append({'direction':d,'frame':f,'actual_state_matches_original_upper_and_fixed_lower':True,'fixed_support_raw_cpu_residual':[{'xy':[int(x),int(y)],'cpu':predicted_raw[y,x].tolist(),'actual':raw[y,x].tolist()} for y,x in np.argwhere(raw_res)],'input_cell_vs_raw_visible_or_alpha_diffs':int(input_res.sum())})
        patch_rows.append({'direction':d,'frame':f,'rgba_composite_diff':0,'alpha_preserved':True,'below_y63_preserved':True,'guarded_upper_pixels_preserved':True,'adopted_pixels':used})
        common_patch.append({tuple(p['xy']):p['adopted_rgba'] for p in used})
    common=set(common_patch[1])&set(common_patch[2]);assert all(common_patch[1][xy]==common_patch[2][xy] for xy in common)
    generation_rows.append({'direction':d,'source':e['source'],'source_sha256':e['source_sha256'],'actual_input':e['actual_input'],'input_sha256':e['input_sha256'],'prompt_sha256':e['prompt_sha256'],'original_generation_output_present_and_sha_equal':original_file_present,'input_cell_diffs':input_diffs,'F1_F2_common_adopted_coordinates':len(common),'common_color_equal':True,'all_frames_sample_same_source_F01_cell':True})
gpu=js(R/'evidence/collect-gpu-validation.json');assert gpu['technical_checks']=='PASS' and len(gpu['samples'])==64 and len(gpu['recoveries'])==8 and all(s['mismatched_pixels']==0 for s in gpu['samples'])
result={'status':'SOURCE_PIXEL_SCOPE_COMPOSITE_PASS_PENDING_VISUAL_AND_RESIDUAL_REVIEW','manifest_payloads':698,'frames112':frames,'changed16':changes,'preserved96':96,'fixed_source_mapping96':mapped,'generation8':generation_rows,'assembly32':assembly_rows,'waist_patch32':patch_rows,'raw_assembly_cpu_residual_total':sum(len(r['fixed_support_raw_cpu_residual']) for r in assembly_rows),'imagegen_input_cell_diff_total':sum(r['input_cell_vs_raw_visible_or_alpha_diffs'] for r in assembly_rows),'waist_adopted_pixel_events':sum(len(r['adopted_pixels']) for r in patch_rows),'author_gpu64_bound_only':{'sha256':sha(R/'evidence/collect-gpu-validation.json'),'samples':64,'recoveries':8,'independent_full_replay':False},'boundary':'Numerical hip/knee/ankle stability is registration proof only; new pose naturalness remains independent visual review. Generation provenance binds supplied exact inputs/prompts/raw files and local original output SHA; it does not claim a fresh imagegen request was made in this review.'}
(OUT/'technical-integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'assembly_residual':result['raw_assembly_cpu_residual_total'],'input_cell_diff':result['imagegen_input_cell_diff_total'],'waist_events':result['waist_adopted_pixel_events'],'sources':generation_rows},ensure_ascii=False))
