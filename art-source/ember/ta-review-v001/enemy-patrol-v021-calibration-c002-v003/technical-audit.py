"""静态 C002：从 S002 ZIP 原图独立复现归属、整数实例平移、UV 及层叠。"""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import ast, hashlib, json
import numpy as np

OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[3]; P=OUT/'technical-cold-load'
sha=lambda b:hashlib.sha256(b).hexdigest()
js=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
arr=lambda p:np.array(Image.open(p).convert('RGBA'))
spec=js(P/'calibration.json'); author=js(P/'qa/calibration_audit.json')
assert spec['canvas']==[128,128] and spec['root']==[64,104]
assert js(OUT/'technical-cold-receipt.json')['status']=='PASS'
original=ROOT/'art-source/ember/deliveries/enemy_patrol_seven_directions_v013_s002_2026-10-06.zip'
assert sha(original.read_bytes())=='28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1'
yy,xx=np.indices((128,128));X,Y=xx+.5,yy+.5
# Reuse only independently written math helpers, not earlier review result assertions.
helper=ROOT/'art-source/ember/ta-review-v001/enemy-cutter-v022-six-moves-v002/technical-audit.py'
tree=ast.parse(helper.read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['poly','socket_geometry','uv_sample']],type_ignores=[]),str(helper),'exec'))
def blank():
    im=np.full((128,128,4),255,np.uint8); im[:,:,3]=0; return im
def shift(im,offset):
    result=blank();ys,xs=np.where(im[:,:,3]>0);tx,ty=xs+offset[0],ys+offset[1]
    assert np.all((tx>=0)&(tx<128)&(ty>=0)&(ty<128))
    result[ty,tx]=im[ys,xs];return result
def compose(images):
    result=blank()
    for im in images: use=im[:,:,3]>0;result[use]=im[use]
    return result
def coords(mask):return [[int(x),int(y)] for y,x in np.argwhere(mask)]
records=[]
with ZipFile(original) as z:
  for direction,cfg in spec['configs'].items():
    source_path=P/f'source/{direction}.png';src=arr(source_path);opaque=src[:,:,3]>0
    assert source_path.read_bytes()==z.read(f'neutral_{direction}.png')
    assert cfg['offset']==([-3,-3] if direction=='left' else [3,-3])
    candidate=arr(P/f'output/neutral_{direction}.png')
    parts={name:arr(P/f'output/{direction}_{name}.png') for name in ['far','near','body']}
    assert all(im.shape==(128,128,4) and set(np.unique(im[:,:,3])).issubset({0,255}) for im in [src,candidate,*parts.values()])
    protected=np.zeros((128,128),bool)
    for shape in cfg['protected']:protected|=poly(shape)
    body=~((X>=50)&(X<77)&(Y>=84)&(Y<128))|protected
    leg=(poly(cfg['cap'])|poly(cfg['shin'])|poly(cfg['foot']))&~protected
    for name,mask in [('body',body),('leg',leg)]:Image.fromarray((mask*255).astype(np.uint8)).save(OUT/f'technical-mask-{direction}-{name}.png')
    expect_body=blank();use=body&opaque;expect_body[use]=src[use]
    assert np.array_equal(expect_body,parts['body'])
    assert np.array_equal(shift(parts['near'],cfg['offset']),parts['far'])
    assembled=compose([parts['far'],parts['near'],parts['body']])
    assert np.array_equal(assembled,candidate)
    rigid_near=blank();use=leg&opaque;rigid_near[use]=src[use]
    assert np.array_equal(parts['near'][use],src[use])
    # Socket UV has a fixed original 2x2 footprint. It is the sole added geometry.
    p={'socket':{'start':cfg['socket_start'],'end':cfg['socket_end'],'width':4}}
    quad=socket_geometry(p,np.zeros(2),np.zeros(2));rect=cfg['socket_uv'];assert rect[2:]==[2,2]
    coverage,sx,sy=uv_sample(quad,rect);u,v,w,h=rect;palette=src[v:v+h,u:u+w].reshape(-1,4)
    assert np.all(palette[:,3]==255)
    bridge=blank();cx,cy=np.clip(sx,0,127),np.clip(sy,0,127);bridge[coverage]=src[cy[coverage],cx[coverage]]
    predicted_near=compose([bridge,rigid_near])
    cpu_residual=np.any(predicted_near!=parts['near'],axis=2)
    predicted_final=compose([shift(predicted_near,cfg['offset']),predicted_near,expect_body])
    final_cpu_residual=np.any(predicted_final!=candidate,axis=2)
    extra=(parts['near'][:,:,3]>0)&~(leg&opaque)
    extra_records=[]
    for y,x in np.argwhere(extra):
        rgba=parts['near'][y,x]
        assert poly(quad.tolist())[y,x] and np.any(np.all(palette==rgba,axis=1))
        extra_records.append({'xy':[int(x),int(y)],'rgba':rgba.tolist(),'source_xy':[int(sx[y,x]),int(sy[y,x])],'cpu_uv_rgba':bridge[y,x].tolist(),'uv_exact':bool(np.array_equal(rgba,bridge[y,x]))})
    difference=np.any(src!=candidate,axis=2);row=next(r for r in author['records'] if r['direction']==direction)
    assert int(difference.sum())==(49 if direction=='left' else 50)
    assert coords(difference)==row['coordinates']
    assert np.array_equal(src[103],candidate[103])
    assert int(np.where(candidate[:,:,3]>0)[0].max())==103
    px,py=([66,94] if direction=='left' else [59,94])
    assert np.array_equal(src[py,px],candidate[py,px]) and leg[py,px]
    protected_opaque=protected&opaque
    assert np.array_equal(src[protected_opaque],candidate[protected_opaque])
    assert np.array_equal(src[:83],candidate[:83])
    # Trace each final difference to actual top layer, with its original sampling coordinate.
    routes=[]
    for y,x in np.argwhere(difference):
        owner=None;source_xy=None;source_matches=[];route_kind=None;cpu_source_exact=None
        for name in ['body','near','far']:
            if parts[name][y,x,3]>0:
                owner=name;off=cfg['offset'] if name=='far' else [0,0];ox,oy=x-off[0],y-off[1]
                rigid=name=='body' or (0<=ox<128 and 0<=oy<128 and leg[oy,ox] and opaque[oy,ox])
                route_kind='rigid' if rigid else 'socket'
                source_xy=[int(ox),int(oy)] if rigid else [int(sx[oy,ox]),int(sy[oy,ox])]
                cpu_source_exact=bool(np.array_equal(candidate[y,x],src[source_xy[1],source_xy[0]]))
                if rigid:assert cpu_source_exact
                else:
                    source_matches=[[u+int(qx),v+int(qy)] for qy,qx in np.argwhere(np.all(src[v:v+h,u:u+w]==candidate[y,x],axis=2))]
                    assert source_matches
                break
        routes.append({'xy':[int(x),int(y)],'original':src[y,x].tolist(),'candidate':candidate[y,x].tolist(),'top_owner':owner,'route_kind':route_kind,'cpu_source_xy':source_xy,'cpu_source_exact':cpu_source_exact,'socket_source_matching_xy':source_matches})
    records.append({'direction':direction,'source_s002_byte_exact':True,'source_sha256':sha(source_path.read_bytes()),
      'candidate_sha256':sha((P/f'output/neutral_{direction}.png').read_bytes()),'changed_rgba_pixels':int(difference.sum()),
      'changed_alpha_pixels':int(np.sum(src[:,:,3]!=candidate[:,:,3])),'new_alpha_pixels':int(np.sum(~opaque&(candidate[:,:,3]>0))),
      'lost_alpha_pixels':int(np.sum(opaque&(candidate[:,:,3]==0))),'changed_opaque_rgb_pixels':int(np.sum(difference&opaque&(candidate[:,:,3]>0))),
      'actual_parts_opaque':{name:int(np.sum(im[:,:,3]>0)) for name,im in parts.items()},'body_rgba_source_exact':True,
      'near_original_leg_pixels':int(np.sum(leg&opaque)),'near_rigid_source_rgb_exact':True,'far_exact_translated_near':cfg['offset'],
      'far_near_body_composite_rgba_diff':0,'protected_opaque_pixels':int(np.sum(protected_opaque)),'protected_rgb_diff':0,
      'source_unowned_opaque':coords(opaque&~(body|leg)),'source_body_leg_overlap':coords(opaque&body&leg),
      'bottom_row_103_rgba_equal':True,'bottom_opaque_y':103,'shin_probe_xy':[px,py],'shin_rgba':candidate[py,px].tolist(),
      'socket':{'source_rect':rect,'source_rgba4':palette.tolist(),'quad':quad.tolist(),'width':4,'z_within_leg':-1,'added_near_socket_pixels':extra_records},
      'transparent_rgb_unique':{name:np.unique(im[im[:,:,3]==0,:3],axis=0).tolist() for name,im in {'source':src,'neutral':candidate,**parts}.items()},
      'cpu_near_residual':[{'xy':[int(x),int(y)],'cpu':predicted_near[y,x].tolist(),'gpu':parts['near'][y,x].tolist()} for y,x in np.argwhere(cpu_residual)],
      'cpu_final_residual':[{'xy':[int(x),int(y)],'cpu':predicted_final[y,x].tolist(),'gpu':candidate[y,x].tolist()} for y,x in np.argwhere(final_cpu_residual)],
      'final_difference_routes':routes})
result={'status':'PASS_STATIC_TECHNICAL','new_clips':0,'canvas':[128,128],'root':[64,104],
        'original_s002_zip_sha256':sha(original.read_bytes()),'source_receipt_sha256':sha((P/'SOURCE_RECEIPT.json').read_bytes()),
        'records':records,'boundary':'Static technical reproduction only. Two physical leg instances reuse the same-direction original visible leg; not two separately drawn sources. Original-palette socket geometry can add output alpha. Does not approve any animations.'}
(OUT/'technical-integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'records':[{k:r[k] for k in ['direction','changed_rgba_pixels','new_alpha_pixels','lost_alpha_pixels','changed_opaque_rgb_pixels','actual_parts_opaque','near_original_leg_pixels','source_unowned_opaque','source_body_leg_overlap','cpu_near_residual']} for r in records]},ensure_ascii=False))
