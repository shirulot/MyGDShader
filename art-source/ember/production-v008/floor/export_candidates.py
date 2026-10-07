"""Export complete v008 floor samples without replacing their drawn geometry.

All candidates preserve complete component geometry. The north straight piece
uses one square registration crop, trimming continuous open material endpoints
and its page padding without modifying the drawn beam. Passage side space is
retained. This script cannot pass artwork or manufacture matching interfaces.
"""
from pathlib import Path
import hashlib,json
from PIL import Image
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'art-source/ember/production-v008/floor'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def measure(im):
    a=np.asarray(im.convert('RGBA'))[:,:,3]
    ys,xs=np.where(a>0)
    bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None
    sy,sx=np.where(a>127)
    solid=[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)] if len(sx) else None
    return {'size':list(im.size),'mode':im.mode,'alpha_nonzero_bbox_xyxy':bbox,
            'alpha_gt127_bbox_xyxy_diagnostic_only':solid,
            'alpha_gt127_median':int(np.median(a[a>127])) if len(sx) else None,
            'alpha_range':[int(a.min()),int(a.max())],
            'nonzero_alpha_count':int((a>0).sum()),
            'partial_alpha_count':int(((a>0)&(a<255)).sum()),
            'edge_nonzero_alpha_count':{'N':int((a[0]>0).sum()),'E':int((a[:,-1]>0).sum()),'S':int((a[-1]>0).sum()),'W':int((a[:,0]>0).sum())}}
seed=json.loads((BASE/'generation-record.seed.json').read_text(encoding='utf-8'))
selected={'floor_edge_N':'v003','floor_outer_NW':'v001','floor_inner_NW':'v002','floor_narrow_NS':'v002'}
tool_files={'floor_edge_N_v001':'exec-7359ca8b-9059-4b4a-8694-c392139b630f.png',
 'floor_edge_N_v002':'exec-0ea98cc6-4764-4e95-bf41-dddc21b3149e.png',
 'floor_outer_NW_v001':'exec-e6c80fb2-49ec-4d8a-bae9-ff94d5cbf731.png',
 'floor_inner_NW_v001':'exec-0f4f2862-7805-4ebc-9bf7-a462f74354c0.png',
 'floor_inner_NW_v002':'exec-fe64b143-c17c-48d6-8054-e6924a169583.png',
 'floor_narrow_NS_v001':'exec-3c03836d-ac9c-45ea-a6d8-1bf18483c837.png',
 'floor_narrow_NS_v002':'exec-bdd328b5-3fc5-4163-ae17-602e2f47bb41.png'}
semantics={
 'floor_edge_N':{'open_sides':['E','S','W'],'closed_sides':['N'],'corner':'no external corner; N horizontal boundary'},
 'floor_outer_NW':{'open_sides':['E','S'],'closed_sides':['N','W'],'corner':'convex northwest external corner'},
 'floor_inner_NW':{'open_sides':['N','E','S','W'],'closed_sides':[],'corner':'northwest diagonal off; localized concave outer pocket'},
 'floor_narrow_NS':{'open_sides':['N','S'],'closed_sides':['E','W'],'corner':'none; continuous longitudinal walkway'}}
candidates=[]
for rec in seed['records']:
    path=ROOT/rec['raw_file']
    im=Image.open(path)
    rec['raw_sha256']=sha(path)
    # 根代理续修的原稿来自其自身工具目录，优先使用逐次记录的实际路径。
    original=(Path(rec['original_tool_path']) if rec.get('original_tool_path') else
              Path('C:/Users/shiru/.codex/generated_images/01a10ba5-b837-7a63-b1af-cdcd6f2564cb')/tool_files[rec['id']+'_'+rec['version']])
    rec['original_tool_path']=original.as_posix()
    rec['original_tool_sha256']=sha(original)
    if rec['original_tool_sha256']!=rec['raw_sha256']:
        raise ValueError('Raw copy differs from original tool output: '+str(path))
    rec['raw_measurement']=measure(im)
    rec['reference_sha256']={p:sha(ROOT/p) for p in rec['references']}
    rec['source_crop_xyxy']=[0,0,*im.size]
    rec['transparent_padding_added']=[0,0,0,0]
    rec['normalization']='NONE; original raw preserved byte-for-byte'
    rec['prompt_file']=f"art-source/ember/production-v008/floor/prompts/{rec['id']}_{rec['version']}.txt"
    rec['prompt_sha256']=sha(ROOT/rec['prompt_file'])
    if selected[rec['id']]!=rec['version']:
        if rec['id']=='floor_edge_N' and rec['version']=='v002':
            # Full-canvas diagnostics preserve the failed south fade. They are
            # deliberately excluded from active candidate selection.
            rejected=im.convert('RGBA').resize((128,128),Image.Resampling.LANCZOS)
            diagnostic=BASE/'review'/'floor_edge_N_v002_rejected_128.png'
            rejected.save(diagnostic)
            enlarged=BASE/'review'/'floor_edge_N_v002_rejected_4x.png'
            rejected.resize((512,512),Image.Resampling.NEAREST).save(enlarged)
            rec['rejected_diagnostic_file']=diagnostic.relative_to(ROOT).as_posix()
            rec['rejected_diagnostic_sha256']=sha(diagnostic)
            rec['rejected_preview']=enlarged.relative_to(ROOT).as_posix()
            rec['south_alpha_qualification']='FAILED; actual floor fades out into transparent south edge'
        continue
    if rec['id']=='floor_edge_N' and rec['version']=='v001':
        # Root-approved whole-component square registration. y84 contains the
        # first anti-aliased beam contour, opaque core begins at y85. Only open
        # beam continuations are trimmed by42px at E/W, leaving its full body.
        rec['source_crop_xyxy']=[42,84,1212,1254]
        rec['notes']='Square registered north-only beam by crop[42,84,1212,1254]. Original top page padding remains in preserved raw. Crop cuts end-brass fasteners partially; beam width mismatch, material seam discontinuity and partial interior Alpha remain unqualified.'
    crop=im.crop(tuple(rec['source_crop_xyxy']))
    if crop.width!=crop.height:
        raise ValueError('No nonuniform stretching permitted: '+str(path))
    out=BASE/'candidates'/f"{rec['id']}_{rec['version']}_128.png"
    # One whole tile is reduced once. No atlas or patch is resized, no trim
    # fragments are moved, and neither colour nor alpha is manufactured.
    candidate=crop.convert('RGBA').resize((128,128),Image.Resampling.LANCZOS)
    candidate.save(out)
    rec['candidate_file']=out.relative_to(ROOT).as_posix()
    rec['candidate_sha256']=sha(out)
    enlarged=BASE/'review'/f"{rec['id']}_{rec['version']}_4x.png"
    candidate.resize((512,512),Image.Resampling.NEAREST).save(enlarged)
    candidates.append({'id':rec['id'],'mask':rec['mask'],'version':rec['version'],
                       'raw_file':rec['raw_file'],'raw_sha256':rec['raw_sha256'],
                       'source_crop_xyxy':rec['source_crop_xyxy'],
                       'raw_measurement':rec['raw_measurement'],
                       'transparent_padding_added':[0,0,0,0],
                       'transform':'one square whole-component registration crop then uniform reduction; no rotation, alpha repair, recolour or endpoint matching',
                       'candidate_file':rec['candidate_file'],'candidate_sha256':rec['candidate_sha256'],
                       'texture_size':[128,128],'world_grid_units':32,'layer_scale':0.25,
                       'candidate_measurement':measure(candidate),
                       **semantics[rec['id']],
                       'source_refs':rec['references'],'reference_sha256':rec['reference_sha256'],
                       'review_preview':enlarged.relative_to(ROOT).as_posix(),
                       'registration_status':'NOT_PASSED',
                       'interface_status':'NOT_PASSED',
                       'visual_status':'CANDIDATE_NOT_USER_APPROVED','issues':[rec['notes']]})
(BASE/'generation-record.json').write_text(json.dumps(seed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE/'prompts.json').write_text(json.dumps([{'id':r['id'],'version':r['version'],'prompt':r['prompt'],'prompt_file':r['prompt_file'],'references':r['references']} for r in seed['records']],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
catalog={'status':'FOUR_COMPLETE_SAMPLE_CANDIDATES_INTERFACES_NOT_PASSED',
         'not_a_final_tileset':True,'native_raw_count':len(seed['records']),'candidate_count':len(candidates),
         'official_template_role':'neighbour on/off semantics only; drawn 1/3 corridor width is a composition choice',
         'candidates':candidates}
(BASE/'candidate-catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'raw_count':len(seed['records']),'candidate_count':len(candidates),'measurements':[{k:c[k] for k in ['id','version','raw_measurement','candidate_file','candidate_measurement']} for c in candidates]},indent=2))

