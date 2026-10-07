"""只读 rc01 独立像素追溯；不调用生产构建器、不修改素材。"""
from pathlib import Path
import json, math, hashlib
import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parent
P=OUT/'technical-package'
js=lambda f:json.loads((P/f).read_text(encoding='utf-8'))
arr=lambda f:np.array(Image.open(P/f).convert('RGBA'))
reg=js('source/action-source-registration/down_right/registration.json')
ledger=js('source/action-rig-batch/collect/down_right/rig_and_poses.json')
patch=js('qa/collect_down_right_joint_patch_v011.json')
parts={r['id']:arr(r['file']) for r in reg['parts']}
palette=np.array([[16,24,32],[24,38,49],[43,62,75],[77,100,112],[130,155,163],[190,203,196],[86,107,120],[236,233,216],[123,77,53],[183,124,75],[226,183,122]])
# 原始 imagegen sheet 经过公共 nearest 8:1 缩小后的既有独立重采样；保存原采样值及量化值。
sheet=np.frombuffer((OUT/'technical-resampled-collect-down_right.raw').read_bytes(),np.uint8).reshape(192,128,4)
order=[]
for limb in reg['rig']['limb_order']:
    order += ['pelvis','body'] if limb=='body' else [limb+'_'+suffix for suffix in ['end','lower','upper'] if limb+'_'+suffix in parts]
records=[]
for i in range(4):
    state=ledger['states'][i]
    final=arr(patch['records'][i]['file'])
    raw=arr(ledger['frames'][i]['file'])
    mask=arr(f'qa/collect_down_right_joint_mask_f{i:02d}.png')
    rows=[]
    for x,y in [(14,j) for j in range(50,56)]:
        layers=[]
        for k in order:
            t=state['transforms'][k]; c=math.cos(t['radians']);s=math.sin(t['radians'])
            dx=x+.5-t['targetPivot'][0];dy=y+.5-t['targetPivot'][1]
            sx=math.floor(dx*c+dy*s+t['sourcePivot'][0]);sy=math.floor(-dx*s+dy*c+t['sourcePivot'][1])
            if 0<=sx<64 and 0<=sy<96 and parts[k][sy,sx,3]:
                layers.append({'part':k,'source_xy':[sx,sy],'rgba':parts[k][sy,sx].tolist()})
        expected=layers[-1]['rgba'] if layers else [0,0,0,0]
        assert expected==raw[y,x].tolist()
        sample=sheet[(i//2)*96+y,(i%2)*64+x]
        quantized=palette[np.argmin(np.sum((palette-sample[:3].astype(int))**2,axis=1))].tolist()+[255 if sample[3]>=160 else 0]
        rows.append({'xy':[x,y],'rig_rgba':raw[y,x].tolist(),'final_rgba':final[y,x].tolist(),'changed':bool(np.any(raw[y,x]!=final[y,x])),'mask_alpha':int(mask[y,x,3]),'source_layers_back_to_front':layers,'imagegen_nearest_raw':sample.tolist(),'imagegen_palette_quantized':quantized,'effective_patch_origin':'F01 shared-pose pixel' if i==2 else f'F{i:02d} source cell'})
    records.append({'frame':i,'file':patch['records'][i]['file'],'sha256':hashlib.sha256((P/patch['records'][i]['file']).read_bytes()).hexdigest(),'pixels':rows})
for i in [1,2]:
    lookup={tuple(r['xy']):r for r in records[i]['pixels']}
    assert lookup[(14,51)]['rig_rgba']==lookup[(14,51)]['final_rgba']==[16,24,32,255]
    for y in [52,53,54]:
        r=lookup[(14,y)]
        assert r['rig_rgba']==[16,24,32,255] and r['final_rgba']==[236,233,216,255] and r['mask_alpha']==255
result={'status':'CONFIRMED_LOCAL_OUTLINE_REPLACEMENT','scope':'SE collect screen-left/anatomical-right elbow; technical causal evidence, visual severity decided by TA','source_imagegen':patch['source_file'],'source_sha256':patch['source_sha256'],'conclusion':'F01 AI joint patch replaces original transformed black outer contour at (14,52..54) with opaque #ece9d8. F02 inherits the same far-arm seam from F01. (14,51) remains the original black rig pixel. Alpha is 255 throughout; the apparent floating dark dot on #ece9d8 arises from color/contour loss, not a transparent hole.','records':records}
(OUT/'technical-se-elbow.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'replaced_pixels_per_frame':3,'frames':[1,2],'file':'technical-se-elbow.json'}))
