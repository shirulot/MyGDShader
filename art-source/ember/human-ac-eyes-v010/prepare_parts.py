"""仅切分生成的静态分件图。角色运动由浏览器骨架驱动，不生成或修补像素。"""
from pathlib import Path
from PIL import Image
import numpy as np
import json
import importlib.util
ROOT=Path(__file__).resolve().parent
image=Image.open(ROOT/'source'/'A-parts.png').convert('RGBA')
spec=importlib.util.spec_from_file_location('inspect_parts',ROOT.parent/'human-ac-expanded-v003'/'inspect_sources.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
groups=module.regions(np.array(image)[:,:,3]>=210)
assert len(groups)==12, len(groups)
groups.sort(key=lambda g:(g['bbox'][1]+g['bbox'][3])/2)
groups=sum([sorted(groups[i:i+4],key=lambda g:g['bbox'][0]) for i in range(0,12,4)],[])
names=['head','torso','near_upper_arm','near_forearm','far_upper_arm','far_forearm',
       'near_thigh','far_thigh','near_shin','far_shin','near_boot','far_boot']
data=[]
for i,name in enumerate(names):
    # 静态零件独立裁片，不是逐帧角色居中；每件裁一次后所有帧共用同一纹理。
    box=groups[i]['bbox']
    cell=image.crop(box)
    arr=np.array(cell);mask=arr[:,:,3]>=210
    arr[:,:,3]=mask.astype(np.uint8)*255;arr[~mask]=0
    cell=Image.fromarray(arr);bounds=cell.getbbox()
    assert bounds,name
    cell.crop(bounds).save(ROOT/'parts'/f'{name}.png')
    data.append({'name':name,'source_cell':box,'bounds':bounds,'file':f'parts/{name}.png'})
(ROOT/'parts.json').write_text(json.dumps({'parts':data,'source_size':image.size},indent=2))

# 眼部局部编辑源覆盖旧头片，防止重新裁切时恢复旧表情。
import shutil
replacement=ROOT/'source/head-eyes-edit.png'
if replacement.exists():
    shutil.copy2(replacement,ROOT/'parts/head.png')
    dims=Image.open(replacement).size
    data[0].update(replacement_source='source/head-eyes-edit.png',source_cell=[0,0,*dims],bounds=[0,0,*dims])
    (ROOT/'parts.json').write_text(json.dumps({'parts':data,'source_size':image.size},indent=2))
