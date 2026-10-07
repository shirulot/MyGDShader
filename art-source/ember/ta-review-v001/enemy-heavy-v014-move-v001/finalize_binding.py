"""收口已有差点与冷证据；不运行引擎、不重新扫测试范围。"""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import json,hashlib
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
p=OUT/'binding.json';result=json.loads(p.read_text(encoding='utf-8'))
with ZipFile(ROOT/'art-source/ember/deliveries/enemy_heavy_eight_moves_v014_v001_2026-10-06.zip') as z:
    records=[]
    for direction in result['new_6']:
        d=direction['direction']
        source=np.array(Image.open(BytesIO(z.read('source/'+d+'.png'))).convert('RGBA'))
        owned=np.array(Image.open(OUT/('godot_ownership_'+d+'.png')).convert('L'))>127
        for frame in direction['cpu_native_reconstruction']:
            for diff in frame['diffs']:
                x,y=diff['output'];i=frame['frame'];bob=1 if i in [2,6] else 0
                # 这些26点全部在窗口外，仅取原track或升降后的原body像素。
                selected=None;layer=None
                if owned[y,x] and source[y,x,3]:selected=[x,y];layer='track'
                if 0<=y-bob<128 and not owned[y-bob,x] and source[y-bob,x,3]:selected=[x,y-bob];layer='body'
                assert selected is not None
                rgba=source[selected[1],selected[0]].tolist()
                headless_expected_same=rgba==diff['png_rgba']
                candidates=[q for q in [[x,y],[x,y-bob]] if source[q[1],q[0]].tolist()==diff['png_rgba']]
                assert candidates
                selected=candidates[0];rgba=source[selected[1],selected[0]].tolist()
                config=json.loads(z.read('rig.json'))['configs'][d]
                edge=[]
                point=np.array([x+.5,y-bob+.5])
                for polygon in config['track_polygons']:
                    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
                        a=np.array(a);b=np.array(b);v=b-a
                        if np.dot(v,v)==0:continue
                        t=float(np.dot(point-a,v)/np.dot(v,v))
                        if 0<=t<=1 and np.linalg.norm(point-(a+t*v))<1e-8:edge.append({'source_pixel_center':point.tolist(),'segment':[a.tolist(),b.tolist()]})
                assert edge
                records.append({'direction':d,'frame':i,'output':[x,y],'png_matching_source_texel':selected,'source_rgba':rgba,'png_rgba':diff['png_rgba'],'source_match_rgba_difference':0,'alpha_coverage_difference':0,'polygon_edge':edge,'headless_Geometry2D_ideal_CPU_result_equals_PNG':headless_expected_same,'reason':'All points are body/track overlap at an exact polygon edge. PNG chooses an unchanged original row or 1px translated row. No off-source RGB or alpha loss. Headless masks alone do not reproduce the original GPU ownership boundary; no claim of CPU fullRGBA zero.'})
    up=next(r for r in result['new_6'] if r['direction']=='up')
    source=np.array(Image.open(BytesIO(z.read('source/up.png'))).convert('RGBA'))
    defects=[]
    for r in up['unsafe_source_samples']:
        sx,sy=r['sample'];x,y=r['dest'];frame=r['frame']
        actual=np.array(Image.open(BytesIO(z.read(f'output/enemy_tracked_heavy/move_up/f{frame:02d}.png'))).convert('RGBA'))
        assert source[sy,sx].tolist()==[255,255,255,0] and actual[y,x].tolist()==[255,255,255,255]
        defects.append(r|{'source_rgba':[255,255,255,0],'output_rgba':[255,255,255,255]})
    assert len(records)==26 and len(defects)==33
    result['cpu_26_polygon_edge_classification']=records
    result['P2_up_tread_white_sampling']={'count':33,'unique_source_transparent_texels':sorted({tuple(r['sample']) for r in defects}),'observed_output_source_bindings':defects,'diagnostic':'up_left_tread_sampling_8x.png','minimum_repair':'Exclude N left-window edge columns x28/x29 or freeze a wholly valid opaque source sampling domain; keep period16/phase2px, frames/identity/supports of other directions unchanged'}
    cold=json.loads((OUT/'cold-receipt.json').read_text(encoding='utf-8'))
    assert cold['status']=='PASS' and cold['independent_checks_passed']==95
    result['independent_cold']={'receipt_sha256':hashlib.sha256((OUT/'cold-receipt.json').read_bytes()).hexdigest(),'passed':95,'total':95,'original159_payloads_hash_same':True,'gpu_framebuffer_rerun':False,'geometry_6_masks_cpu_only':True}
    result['status']='NEEDS_REVISION_P2_UP_TREAD_TRANSPARENT_RGB_SAMPLING'
    # 网页本地文件绑定，仅三个本次审阅入口，非网络请求。
    served=ROOT/'art-source/ember/enemy-sequences-v001/previews/heavy-eight-moves-v014-v001'
    mappings=[('index.html','previews/index.html'),('catalog.json','output/catalog.json'),('output/enemy_tracked_heavy/move_up.png','output/enemy_tracked_heavy/move_up.png')]
    result['served_local_bindings']=[{'served_relative':n,'package':member,'exists':(served/n).is_file(),'byte_same':(served/n).is_file() and (served/n).read_bytes()==z.read(member)} for n,member in mappings]
p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('NEEDS_REVISION: 33 white copied-to-opaque points; unrelated26 exact polygon-border differences all unchanged source; cold95 PASS')
