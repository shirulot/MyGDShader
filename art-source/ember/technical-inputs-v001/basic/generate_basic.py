"""从零生成20张技术测试输入。固定参数；不读取、替换或重画游戏美术。"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ASSETS = []

def save(identifier, group, folder, data, semantics, repeat=()):
    image = data if isinstance(data, Image.Image) else Image.fromarray(data)
    path = ROOT/f"assets/ember/{folder}/{identifier}_v001.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): raise RuntimeError(f"Refusing overwrite: {path}")
    image.save(path)
    ASSETS.append(dict(id=identifier, manifest_id=group, file="res://"+path.relative_to(ROOT).as_posix(),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), canvas=list(image.size), mode=image.mode,
        repeat_axes=list(repeat), data_semantics=semantics, generator=HERE.relative_to(ROOT).as_posix()+"/generate_basic.py"))

def grid(size):
    w,h=size; x,y=np.meshgrid(np.arange(w), np.arange(h))
    a=np.stack((np.rint(x/(w-1)*255),np.rint(y/(h-1)*255),np.full_like(x,128)),axis=-1).astype('uint8')
    image=Image.fromarray(a); d=ImageDraw.Draw(image); font=ImageFont.load_default(size=18)
    for px in range(0,w,64): d.line((px,0,px,h-1),fill='white',width=2)
    for py in range(0,h,64): d.line((0,py,w-1,py),fill='white',width=2)
    for py in range(0,h,64):
        for px in range(0,w,64): d.text((px+6,py+6),f"{px//64},{py//64}",fill='black',font=font)
    d.text((w-132,h-26),'U -> / V down',fill='white',font=font)
    return image

def normal(height):
    # PNG行y朝下；OpenGL的+Y朝上，因此编码绿色使用+dh/dy。
    dy,dx=np.gradient(height.astype('float64')/255.0*8.0)
    n=np.stack((-dx,dy,np.ones_like(dx)),axis=-1)
    n/=np.linalg.norm(n,axis=-1,keepdims=True)
    return np.rint((n*.5+.5)*255).astype('uint8')

def noise(seed, lo, hi):
    rng=np.random.default_rng(seed)
    s=np.linspace(0,1,256); q=s-np.sin(2*np.pi*s)/(2*np.pi)
    x,y=np.meshgrid(q,q); value=np.zeros((256,256)); modes=[]
    for _ in range(24):
        fx=int(rng.integers(lo,hi+1))*int(rng.choice([-1,1])); fy=int(rng.integers(lo,hi+1))*int(rng.choice([-1,1]))
        phase=float(rng.uniform(0,2*np.pi)); amplitude=float(rng.uniform(.3,1))
        value+=amplitude*np.cos(2*np.pi*(fx*x+fy*y)+phase)
        modes.append([fx,fy,phase,amplitude])
    result=np.rint((value-value.min())/(value.max()-value.min())*255).astype('uint8')
    # 周期参数在边界一阶导数为0；量化后明确共享端点及相邻像素，避免1字节误差。
    result[-1]=result[0]; result[:, -1]=result[:,0]
    result[1]=result[0]; result[-2]=result[-1]
    result[:,1]=result[:,0]; result[:,-2]=result[:,-1]
    return result,dict(seed=seed,phase_frequency_band=[lo,hi],modes=modes,
        coordinates="q(s)=s-sin(2*pi*s)/(2*pi); endpoint derivative zero; nonuniform phase speed",seam="XY endpoints and finite first differences exact")

def main():
    save('uv_grid','D01','data/calibration',grid((512,512)),"R=U G=V background, labelled64px cells; origin top-left")
    save('non_square_grid','D01','data/calibration',grid((512,256)),"512x256 native grid, 64px square cells expose aspect ratio")
    x,y=np.meshgrid(np.arange(512),np.arange(512))
    checker=np.where(((x//32+y//32)%2)==0,32,224).astype('uint8')
    save('checkerboard','D01','data/calibration',np.repeat(checker[...,None],3,axis=2),"32px binary checker tiles; RGB32/224",('X','Y'))
    test=np.zeros((512,512,3),dtype='uint8')
    colors=[(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),(255,0,255),(0,0,0),(255,255,255)]
    for i,c in enumerate(colors): test[(i//4)*128:(i//4+1)*128,(i%4)*128:(i%4+1)*128]=c
    test[256:384]=np.repeat(np.rint(np.arange(512)/511*255).astype('uint8')[None,:,None],3,axis=2)
    test[384:]=np.repeat((np.arange(512)//32*17).astype('uint8')[None,:,None],3,axis=2)
    save('color_test','D01','data/calibration',test,{"patches":colors,"gray_ramp_endpoints":[0,255],"gray_steps":list(range(0,256,17))})
    background=np.full((512,512,3),210,dtype='uint8')
    background[(y%64)<2]=(15,30,45); background[(x%64)<2]=(20,110,150)
    background[(x-y)%128<2]=(180,50,40)
    save('straight_background','D01','data/calibration',background,"Horizontal/vertical64px and diagonal128px straight lines for distortion")
    gray=np.repeat(np.arange(256,dtype='uint8')[None,:,None],3,axis=2)
    save('grayscale_gradient','D02','data/ramps',gray,{"linear_values":"x/255","endpoints":[0,255],"steps":256})
    stops=[(0,(16,24,32)),(64,(30,190,200)),(128,(255,180,40)),(192,(240,70,60)),(255,(255,255,255))]
    ramp=np.stack([np.interp(np.arange(256),[s[0] for s in stops],[s[1][c] for s in stops]) for c in range(3)],axis=-1)
    save('color_ramp','D02','data/ramps',np.rint(ramp)[None].astype('uint8'),{"stops":stops,"interpolation":"linear in encoded RGB; mark source_color when used as color", "addressing":"clamp X; one-pixel Y"})
    xx,yy=np.meshgrid(np.arange(256)+.5,np.arange(256)+.5); radius=np.hypot(xx-128,yy-128)
    save('circle_mask','D03','data/masks',np.clip((92-radius)/2+.5,0,1).__mul__(255).round().astype('uint8'),"center128/128 radius92; 2px soft boundary; black0 white1")
    star=Image.new('L',(256,256)); d=ImageDraw.Draw(star)
    points=[(128+np.cos(-np.pi/2+i*np.pi/5)*(94 if i%2==0 else 42),128+np.sin(-np.pi/2+i*np.pi/5)*(94 if i%2==0 else 42)) for i in range(10)]
    d.polygon(points,fill=255)
    save('star_mask','D03','data/masks',star,{"vertices":points,"binary_values":[0,255],"origin":"center128/128"})
    for name,seed,lo,hi in [('noise_low',240410,1,4),('noise_high',240411,10,24)]:
        a,meta=noise(seed,lo,hi); save(name,'D04','data/noise',a,meta,('X','Y'))
    edge=Image.new('RGBA',(128,128)); d=ImageDraw.Draw(edge)
    d.rectangle((12,12,90,94),fill=(210,220,235,255)); d.ellipse((30,30,65,65),fill=(0,0,0,0))
    d.line((92,52,112,52),fill=(210,220,235,255),width=1); d.line((104,16,104,50),fill=(210,220,235,255),width=1)
    d.rectangle((102,70,116,94),fill=(210,220,235,255))
    for i in range(64):
        d.line((12+i,108,12+i,119),fill=(210,220,235,round(i/63*255)))
    save('alpha_edge_test','D05','data/calibration',edge,{"opaque_body":[12,12,91,95],"transparent_hole":[30,30,66,66],"thin_lines":"isolated 1px horizontal and vertical lines", "alpha_gradient":"x12..75 y108..119 alpha0..255"})
    save('radial_ramp','D06','data/energy',np.clip(1-radius/128,0,1).__mul__(255).round().astype('uint8'),"center1 to radius128=0; .r weight")
    stripe=np.rint((.5+.5*np.cos(2*np.pi*xx/32))*255).astype('uint8')
    save('energy_stripe','D06','data/energy',stripe,"eight32px sinusoidal stripes; X/Y periodic center sampling",('X','Y'))
    xx,yy=np.meshgrid(np.arange(128),np.arange(128)); height=128+50*np.exp(-((xx-35)**2+(yy-46)**2)/240)-50*np.exp(-((xx-91)**2+(yy-46)**2)/240)
    height[88:112,16:48]=128+np.arange(32)[None,:]*2
    height[88:112,80:112]=128+np.arange(24)[:,None]*2
    height=np.rint(height).astype('uint8')
    save('test_height','D07','data/calibration',height,{"convex_center":[35,46],"concave_center":[91,46],"neutral":128,"ramp_x":[16,88,48,112],"ramp_y":[80,88,112,112],"height_scale":8.0})
    save('test_normal','D07','data/calibration',normal(height),{"height_id":"test_height","convention":"OpenGL +X,+Y,+Z; n=(-dh/dx,+dh/dy,1)","height_scale":8.0,"difference":"numpy gradient on actual quantized L PNG"})
    for name in ('rain_line','water_drop','spark','dust_dot'):
        image=Image.new('RGBA',(16,16)); d=ImageDraw.Draw(image)
        if name=='rain_line': d.line((9,2,6,13),fill=(175,210,235,255),width=1)
        elif name=='water_drop': d.polygon([(8,2),(5,7),(4,10),(6,13),(10,13),(12,10),(11,7)],fill=(100,180,220,255))
        elif name=='spark': d.line((3,12,11,4),fill=(255,190,70,255),width=1); d.point((12,3),fill=(255,240,200,255))
        else: d.ellipse((6,6,9,9),fill=(190,180,160,255))
        save(name,'D10','vfx/particles',image,"16px native binary Alpha particle input; no baked effect")
    assert len(ASSETS)==20
    HERE.mkdir(parents=True,exist_ok=True)
    (HERE/'catalog.json').write_text(json.dumps({"status":"BASIC_20_GENERATED","assets":ASSETS},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # 审阅板仅展示实际文件；不计入交付PNG数量。
    board=Image.new('RGB',(1380,920),(18,26,35)); draw=ImageDraw.Draw(board)
    for i,a in enumerate(ASSETS):
        image=Image.open(ROOT/a['file'].removeprefix('res://')).convert('RGBA'); image.thumbnail((250,174),Image.Resampling.NEAREST)
        ox=10+(i%5)*276; oy=10+(i//5)*230
        board.paste(image,(ox,oy),image); draw.text((ox,oy+182),a['id'],fill='white')
    board.save(HERE/'preview.png')
    print('BASIC_20_GENERATED: 20 PNG')

if __name__=='__main__': main()
