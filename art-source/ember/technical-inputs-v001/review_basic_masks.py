"""独立只读审计其它制作方的 D08 和 basic 输入；不修改源图、目录或生成器。

重建明确几何期望值并比较真实 PNG，核验来源和语义，不调用制作方验收函数。
完整报告只在 basic20 与 D08十项都实际核验后写入。
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

PROOF = Path(__file__).resolve().parent
ROOT = PROOF.parents[2]
CHECKS = []
ASSETS = []


def read(path): return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve(file): return ROOT / file.removeprefix("res://")


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, passed, **details):
    CHECKS.append({"name":name,"pass":bool(passed),**details})


def bbox(data):
    y,x=np.where(data!=0)
    return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)] if len(x) else None


def pointer(value, pointer):
    for component in pointer.strip("/").split("/"):
        value=value[int(component)] if isinstance(value,list) else value[component]
    return value


def mask_audit():
    catalog=read(PROOF/"object-masks/catalog.json")
    check("D08:ten",len(catalog["assets"])==10)
    check("D08:unique",len({a['id'] for a in catalog['assets']})==10)
    for a in catalog['assets']:
        id="D08:"+a['id']; output=resolve(a['file']); base_path=resolve(a['source_file'])
        im=Image.open(output); m=np.array(im); base=np.array(Image.open(base_path).convert('RGBA'))
        check(id+":png_sha",sha(output)==a['sha256'])
        check(id+":base_sha",sha(base_path)==a['source_sha256'])
        check(id+":mode",im.mode=='RGBA')
        check(id+":canvas",list(im.size)==a['canvas']==[base.shape[1],base.shape[0]])
        check(id+":alpha_byte_exact",np.array_equal(m[:,:,3],base[:,:,3]))
        check(id+":binary_channels",set(np.unique(m))<={0,255})
        check(id+":rgb_outside_alpha_zero",np.all(m[base[:,:,3]==0,:3]==0))
        check(id+":B_unused_zero",np.all(m[:,:,2]==0))
        source_geom=resolve(a['source_geometry_file']); geom_json=read(source_geom)
        check(id+":source_geometry_sha",sha(source_geom)==a['source_geometry_sha256'])
        windows=pointer(geom_json,a['source_geometry_json_pointer'])
        g=a['registered_geometry']
        check(id+":windows_match_source_pointer",windows==g['windows'])
        source_entry=geom_json[int(a['source_geometry_json_pointer'].split('/')[1])] if a['id']=='station' else geom_json['assets'][int(a['source_geometry_json_pointer'].split('/')[2])]
        source_metadata=source_entry['measurements'] if a['id']=='station' else source_entry
        check(id+":canvas_anchor_match_source",g['canvas']==a['canvas']==source_metadata['canvas'] and g['anchor']==a['anchor']==source_metadata['anchor'])
        canonical=json.dumps(g,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
        check(id+":registered_geometry_sha",hashlib.sha256(canonical).hexdigest()==a['registered_geometry_sha256'])
        active=np.zeros(m.shape[:2],bool)
        for w in windows:
            x0,y0,x1,y1=w['safe_active_rect']; active[y0:y1,x0:x1]=True
            check(id+":window_in_bounds:"+w['id'],0<=x0<x1<=im.width and 0<=y0<y1<=im.height)
            check(id+":window_center:"+w['id'],w['center']==[(x0+x1)/2,(y0+y1)/2])
        for s in a['selection_sources']:
            selected_im=Image.open(resolve(s['file'])); selected=np.array(selected_im)
            component=np.array(Image.open(resolve(s['component_file'])).convert('RGBA'))
            check(id+":selection_sha",sha(resolve(s['file']))==s['sha256'])
            check(id+":component_sha",sha(resolve(s['component_file']))==s['component_sha256'])
            check(id+":selection_L_native",selected_im.mode=='L' and selected.shape==m.shape[:2])
            check(id+":selection_component_alpha_exact",np.array_equal(selected,component[:,:,3]))
            check(id+":component_selected_RGB_base_exact",np.array_equal(component[selected>0,:3],base[selected>0,:3]))
            check(id+":selection_binary",set(np.unique(selected))<={0,255})
            if a['id']=='ventilator': active=selected>0
            else:
                check(id+":selection_equals_safe_geometry",np.array_equal(selected>0,active))
                active &= selected>0
            layers=[l for l in source_entry['layers'] if l['name']==s['layer_name']]
            check(id+":component_registered_layer",len(layers)==1 and layers[0]['file']==s['component_file'] and layers[0]['sha256']==s['component_sha256'])
        active &= base[:,:,3]>0
        expected=active.astype(np.uint8)*255
        check(id+":R_geometry_exact",np.array_equal(m[:,:,0],expected),selected_pixels=int(active.sum()))
        check(id+":G_semantic_exact",np.array_equal(m[:,:,1],np.zeros_like(expected) if a['id']=='ventilator' else expected))
        if a['id']=='ventilator':
            check(id+":only_actual_rotor_no_glow",g['selected_layer']=='fan_rotor' and not windows and np.all(m[:,:,1:3]==0))
        for index,c in enumerate('RGBA'):
            data=m[:,:,index]; measured=a['channels'][c]
            check(id+":channel_numeric_metadata:"+c,int((data>0).sum())==measured['nonzero_count'] and bbox(data)==measured['bbox'] and np.unique(data).tolist()==measured['values'])
        one=PROOF/'object-masks/review'/f"{a['id']}_mask_review_1x.png"
        two=resolve(a['preview_2x'])
        expected_review=np.array(Image.open(one).resize((Image.open(one).width*2,Image.open(one).height*2),Image.Resampling.NEAREST))
        check(id+":preview_exact_nearest2x",np.array_equal(expected_review,np.array(Image.open(two))))
        ASSETS.append({'id':a['id'],'manifest_id':'D08','file':a['file'],'sha256':sha(output),'source_sha256':sha(base_path),'geometry_sha256':sha(source_geom),'preview_1x':one.relative_to(ROOT).as_posix(),'preview_2x':a['preview_2x']})


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mask-only',action='store_true');args=parser.parse_args()
    mask_audit()
    failed=[c for c in CHECKS if not c['pass']]
    report={'status':'D08_INDEPENDENT_10_PASS_BASIC20_PENDING' if not failed else 'FAILED',
            'actual_reviewed_assets':len(ASSETS),'failed_checks':len(failed),'checks':len(CHECKS),'assets':ASSETS,'details':CHECKS,'failures':failed,
            'excluded_scope':'D09/D11/D12 self-produced surfaces10 excluded from independent review'}
    target=PROOF/'independent-mask-stage-review.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','actual_reviewed_assets','failed_checks','checks']},ensure_ascii=False))
    raise SystemExit(bool(failed))


if __name__=='__main__': main()
