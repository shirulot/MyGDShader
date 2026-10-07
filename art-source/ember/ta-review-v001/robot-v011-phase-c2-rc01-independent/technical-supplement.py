"""补齐固定目录、源输入排版与作者证据绑定；不重复 GPU 矩阵。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import json, hashlib
import numpy as np

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];P=OUT/'technical-package'
F=ROOT/'art-source/ember/robot-eight-way-v011/review/phase-c2-rc01'
sha=lambda b:hashlib.sha256(b).hexdigest()
js=lambda f:json.loads((P/f).read_text(encoding='utf-8'))
arr=lambda f:np.array(Image.open(P/f).convert('RGBA'))
manifest=js('sha256-manifest.json')['files']
assert all(sha((F/r['file']).read_bytes())==r['sha256'] for r in manifest)
meta=js('full-action-metadata.json');atlas=arr(meta['atlas']);used=np.zeros(atlas.shape[:2],bool)
for c in meta['clips']:
    for f in c['frames']:
        x,y,w,h=f['region'];used[y:y+h,x:x+w]=True
assert not np.any(atlas[~used])
inputs=[]
for g in js('run-manifest.json')['generation']:
    if not g.get('scope','').startswith('C2 '):continue
    source=Path(g['original_output'])
    source_exact=sha(source.read_bytes())==g['sha256'] if source.exists() else None
    assert source_exact is not False
    prompt=(P/g['prompt']).read_text(encoding='utf-8')
    assert 'Direction:' in prompt and 'Fixed upper-left light.' in prompt
    ledger=js(f'source/action-rig-batch/{g["action"]}/{g["direction"]}/rig_and_poses.json')
    h=96 if g['action']=='idle' else 192
    expected=np.zeros((h,128,4),np.uint8)
    for i,f in enumerate(ledger['frames']):expected[(i//2)*96:(i//2+1)*96,(i%2)*64:(i%2+1)*64]=arr(f['file'])
    actual=arr(g['actual_input'])
    assert np.array_equal(actual,np.repeat(np.repeat(expected,4,axis=0),4,axis=1))
    inputs.append({'action':g['action'],'direction':g['direction'],'actual_input_rgba_rig_sheet_4x_diff':0,'original_generated_file_exists':source.exists(),'original_generated_file_sha_exact':source_exact})
gpu=js('qa/godot_full_actions_v011.json')
assert len(gpu['cases'])==224 and len(gpu['transitions'])==136 and len(gpu['natural_playback'])==16 and len(gpu['collect_to_idle'])==8 and not gpu['errors']
assert all(c['rgba_exact'] and c['root_unchanged'] for c in gpu['transitions'])
assert all(c['loops']==2 for c in gpu['natural_playback'])
assert all(c['sequence']==[0,1,2,3] and len(c['finished_events'])==1 and c['result_frame']==0 and c['result_animation']=='idle_'+c['direction'] and c['idle0_rgba_exact'] for c in gpu['collect_to_idle'])
result={'status':'PASS','fixed_directory_payload_sha_exact':1702,'unused_atlas_cells_rgba_zero':True,'input_and_original_source_checks':inputs,'author_evidence_bound_only':{'qa_file':'qa/godot_full_actions_v011.json','sha256':sha((P/'qa/godot_full_actions_v011.json').read_bytes()),'gpu_records':224,'switches':136,'loop_clips':16,'loops_per_clip':2,'collect_recovery':8,'independent_replay':False},'note':'These are technical checks only; SE elbow outline visual P2 remains.'}
(OUT/'technical-supplement.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'inputs':len(inputs),'gpu_replayed':False}))
