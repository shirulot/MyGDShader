"""C22 髋座/遮挡专项诊断；仅读冻结 ZIP，不修改或重导生产帧。"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image,ImageDraw
import json,hashlib,numpy as np

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
ZP=ROOT/'art-source/ember/deliveries/enemy_cutter_six_moves_v022_v002_2026-10-07.zip'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(ZP.read_bytes())=='3b1619b3cc5a32f11dbe699716b88a9b4a1b8874da55526d6d8c61f6e7d3377e'
z=ZipFile(ZP);js=lambda n:json.loads(z.read(n));im=lambda n:Image.open(BytesIO(z.read(n))).convert('RGBA')
spec=js('rig.json');audit=js('qa/pose_audit.json');catalog=js('output/catalog.json')
colors={'rear_right':(35,184,228,255),'rear_left':(246,149,50,255),'front_right':(78,225,134,255),'front_left':(218,87,238,255)}
def inside(points,shape):
    X,Y=points;mask=np.zeros(X.shape,bool)
    for (x1,y1),(x2,y2) in zip(shape,shape[1:]+shape[:1]):
        if y1!=y2:mask^=((y1>Y)!=(y2>Y))&(X<(x2-x1)*(Y-y1)/(y2-y1)+x1)
    return mask
yy,xx=np.indices((128,128));centers=(xx+.5,yy+.5)
report={'zip_sha256':sha(ZP.read_bytes()),'scope':'Targeted static hip-seat/hidden-limb visual evidence, author exposure coordinates are pointers until independent integrity verification','sources':{},'directions':{},'diagnostics':{}}
def save(name,can):
    can.convert('RGB').save(OUT/name);report['diagnostics'][name]=sha((OUT/name).read_bytes())
for d,cfg in spec['configs'].items():
    source=im('source/'+d+'.png');array=np.array(source)
    report['sources']['source/'+d+'.png']=sha(z.read('source/'+d+'.png'))
    rows=[r for r in audit['records'] if r['action']=='move_'+d]
    clip=next(c for c in catalog['clips'] if c['direction']==d)
    diagnostic=array.copy();diagnostic[diagnostic[:,:,3]>0,:3]=[132,132,132]
    protected=np.zeros((128,128),bool)
    for poly in cfg['protected_body_polygons']:protected|=inside(centers,poly)
    masks={}
    for p in cfg['parts']:
        mask=inside(centers,p['polygon'])
        for poly in p['overlap_polygons']:mask|=inside(centers,poly)
        mask&=(~protected)&(array[:,:,3]>0);masks[p['id']]=mask
        diagnostic[mask]=colors[p['id']]
    report['directions'][d]={'hidden_legs':cfg['hidden_legs'],'parts':[]}
    for bgname,bg in [('light',(238,238,238,255)),('dark',(8,11,16,255))]:
        # 同坐标原图与归属图；彩色只作为归属辅助，不作为真实外观。
        can=Image.new('RGBA',(640,248),bg);dr=ImageDraw.Draw(can);ink=(20,20,20,255) if bgname=='light' else (240,240,240,255)
        for idx,(label,frame) in enumerate([('original '+d,source),('ownership diagnostic',Image.fromarray(diagnostic))]):
            dr.text((idx*320+4,4),label,fill=ink);can.alpha_composite(frame.crop((24,52,104,108)).resize((320,224),Image.Resampling.NEAREST),(idx*320,24))
        save('hip-source-owner-'+d+'-'+bgname+'-4x.png',can)
        # 每个髋座独立选作者记录中其暴露最多的一帧，连同前后帧和中性作同ROI比较。
        can=Image.new('RGBA',(640,len(cfg['parts'])*200),bg);dr=ImageDraw.Draw(can)
        for j,p in enumerate(cfg['parts']):
            counts=[sum(p['id'] in v[2] for v in row['visible_dark_connector_pixels']) for row in rows]
            frame=max(range(8),key=lambda n:counts[n]);mx,my=map(int,p['socket']['start']);roi=(mx-10,my-10,mx+10,my+12)
            frames=[('bind',source)]+[(f'F{n:02}',im(f'output/enemy_cutter/move_{d}/f{n:02}.png')) for n in [(frame-1)%8,frame,(frame+1)%8]]
            for n in [(frame-1)%8,frame,(frame+1)%8]:
                path=f'output/enemy_cutter/move_{d}/f{n:02}.png';report['sources'][path]=sha(z.read(path))
            for i,(name,a) in enumerate(frames):
                dr.text((i*160+2,j*200+3),f'{p["id"]} {name}',fill=ink)
                can.alpha_composite(a.crop(roi).resize((160,176),Image.Resampling.NEAREST),(i*160,j*200+24))
            if bgname=='light':
                report['directions'][d]['parts'].append({'id':p['id'],'socket':p['socket'],'sole':p['sole'],'opaque_mask_pixels':int(masks[p['id']].sum()),'selected_frame':frame,'author_exposure_counts':counts,'roi_half_open':roi,'selected_exposure_coordinates':[v[:2] for v in rows[frame]['visible_dark_connector_pixels'] if p['id'] in v[2]]})
        save('hip-seat-'+d+'-'+bgname+'-8x.png',can)
    # 部件来源与2x2取样矩形绑定，颜色是否足够暗及落点语义由实际图像判。
    for p in report['directions'][d]['parts']:
        x,y,w,h=p['socket']['source_rect'];p['sample_RGBA_rows']=array[y:y+h,x:x+w].tolist()
        p['original_endpoint_pixel_owners']={}
        for k in ['start','end']:
            x,y=map(int,p['socket'][k]);p['original_endpoint_pixel_owners'][k]=[name for name,mask in masks.items() if mask[y,x]] or ['body_or_transparent']
# 每方向重点暴露帧的原生与4倍整体环境，用于确认安装座没有读成新增支脚。
selected=[('down_left',4),('left',2),('up_left',2),('up',2),('up_right',4),('right',6)]
for bgname,bg in [('light',(238,238,238,255)),('dark',(8,11,16,255))]:
    for scale,roi in [(1,(0,0,128,128)),(4,(24,52,104,108))]:
        w,h=(roi[2]-roi[0])*scale,(roi[3]-roi[1])*scale
        can=Image.new('RGBA',(w*3,(h+24)*2),bg);dr=ImageDraw.Draw(can)
        for i,(d,n) in enumerate(selected):
            x,y=i%3*w,i//3*(h+24)
            dr.text((x+3,y+4),f'{d} F{n:02}',fill=(20,20,20,255) if bgname=='light' else (240,240,240,255))
            path=f'output/enemy_cutter/move_{d}/f{n:02}.png'
            can.alpha_composite(im(path).crop(roi).resize((w,h),Image.Resampling.NEAREST),(x,y+24))
            report['sources'][path]=sha(z.read(path))
        save(f'hip-selected-full-{bgname}-{scale}x.png',can)
    # 技术邻接特例：SW后右F5-7连接四边形全部藏在自身腿内，单独复看原实体。
    can=Image.new('RGBA',(768,200),bg);dr=ImageDraw.Draw(can)
    for i,n in enumerate([4,5,6,7]):
        path=f'output/enemy_cutter/move_down_left/f{n:02}.png'
        dr.text((i*192+3,3),f'SW rear_right F{n:02}',fill=(20,20,20,255) if bgname=='light' else (240,240,240,255))
        can.alpha_composite(im(path).crop((40,60,64,82)).resize((192,176),Image.Resampling.NEAREST),(i*192,24))
        report['sources'][path]=sha(z.read(path))
    save(f'hip-sw-rear-right-f04-f07-{bgname}-8x.png',can)
(OUT/'hip-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'directions':len(report['directions']),'sockets':sum(len(x['parts']) for x in report['directions'].values()),'diagnostic_files':len(report['diagnostics'])}))
