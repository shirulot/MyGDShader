"""绑定作者运行记录；不把作者结果描述成TA重跑。"""
from pathlib import Path
from PIL import Image
import hashlib,json,re
HERE=Path(__file__).resolve().parent
PACK=HERE/'package';OLD=HERE.parent/'robot-v011-phase-b1-rc01-independent/package'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def difference(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):return sum((difference(a.get(k),b.get(k),path+'/'+k) for k in a.keys()|b.keys()),[])
    if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):return sum((difference(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
    return [] if a==b else [{'path':path,'before':a,'after':b}]
rig=[]
for d in ['up','up_right','down_right']:
    n=load(PACK/f'source/fixed-rig-pilot/{d}/rig_and_poses.json');o=load(OLD/f'source/fixed-rig-pilot/{d}/rig_and_poses.json')
    rig.append({'direction':d,'rig_config_diff':difference(o['rig'],n['rig']),'part_raw_hashes_exact':all(sha(Image.open(PACK/q['file']).convert('RGBA').tobytes())==q['raw_sha256'] for q in n['parts']),'rightward_arm_angle_reflection_max_error':max(abs(ns['transforms'][k]['radians']+os['transforms'][k]['radians']) for ns,os in zip(n['states'],o['states']) for k in ns['transforms'] if k.startswith('arm_')) if d!='up' else None,'notes':[s.get('notes',[]) for s in n['states']]})
manifest={q['file']:q for q in load(PACK/'sha256-manifest.json')['files']}
gpu=load(PACK/'qa/godot_walk_batch_v011.json');trans=load(PACK/'qa/godot_walk_transitions_v011.json');bindings=[]
for q in gpu['cases']:
    f=q['file'];b=(PACK/f).read_bytes();bindings.append({'file':f,'sha256':sha(b),'in_manifest_exact':sha(b)==manifest[f]['sha256'],'author_rgba_exact':q['rgba_exact']})
warn=load(PACK/'qa/skill_motion_audit_walk_batch.json')['warnings']
html=(PACK/'walk-review.html').read_text(encoding='utf-8');links=re.findall(r'(?:href|src)=[\"\']([^\"\']+)[\"\']',html)
links=[l for l in links if not l.startswith(('http','#','data:')) and '${' not in l]
result={'scope':'Author GPU/natural loop/transition results are package-bound only; TA did not independently rerun those matrices.','gpu_report_sha256':sha((PACK/'qa/godot_walk_batch_v011.json').read_bytes()),'gpu_report_atlas_sha256':gpu['atlas_sha256'],'gpu_cases':bindings,'natural_playback':[{'clip':q['clip'],'actual_loops':q['actual_loops'],'sequence_entries':len(q['sequence'])} for q in gpu['natural_playback']],'transition_report_sha256':sha((PACK/'qa/godot_walk_transitions_v011.json').read_bytes()),'transition_report_atlas_sha256':trans['atlas_sha256'],'transition_cases':len(trans['cases']),'warnings':warn,'rig_increment':rig,'entry_links':[{'href':l,'exists':(PACK/l).exists()} for l in links],'dynamic_pose_links_all_eight_exist':all((PACK/f'source/candidate-masters/robot_idle_{d}_v011.png').exists() for d in load(PACK/'walk-batch-metadata.json')['direction_order']),'historical_cold_qa_note':'qa/cold_delivery_validation_rc02.json explicitly binds phase-A rc02 ZIP df9884..., not this B1 rc02. TA minimum B1 cold load is a separate independent result.'}
(HERE/'author-evidence-binding.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('RIG config differences',[(q['direction'],q['rig_config_diff']) for q in rig]);print('GPU',len(bindings),all(q['in_manifest_exact'] for q in bindings),'TRANS',len(trans['cases']),'WARN',warn)
print('Original package unchanged',all(sha((PACK/f).read_bytes())==q['sha256'] for f,q in manifest.items()))
