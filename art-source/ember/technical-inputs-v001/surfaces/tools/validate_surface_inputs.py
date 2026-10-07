"""只读复算技术 PNG 并产生测量和审阅板，不重建输入图。

CPU 定向照明仅验证编码方向/注册，实际 Godot Light2D/PBR 另由根代理核验。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SURFACES = Path(__file__).resolve().parents[1]
ROOT = SURFACES.parents[3]
REVIEW = SURFACES / "review"
CHECKS = []


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def path(file): return ROOT / file.removeprefix("res://")


def check(name, passed, **details):
    CHECKS.append({"name": name, "passed": bool(passed), **details})


def normal(height, strength, periodic):
    # 独立差分实现：不导入构建器函数。
    if periodic:
        dy = np.empty_like(height); dx = np.empty_like(height)
        h,w = height.shape
        for y in range(h): dy[y] = (height[(y+1)%h] - height[(y-1)%h])*.5
        for x in range(w): dx[:,x] = (height[:,(x+1)%w] - height[:,(x-1)%w])*.5
    else:
        dx = np.empty_like(height); dy = np.empty_like(height)
        dx[:,1:-1] = (height[:,2:] - height[:,:-2])*.5
        dx[:,0] = height[:,1]-height[:,0]; dx[:,-1] = height[:,-1]-height[:,-2]
        dy[1:-1] = (height[2:]-height[:-2])*.5
        dy[0] = height[1]-height[0]; dy[-1] = height[-1]-height[-2]
    n = np.stack((-dx*strength,dy*strength,np.ones_like(height)),axis=-1)
    n /= np.sqrt((n*n).sum(axis=-1,keepdims=True))
    return n,dx,dy


def format_png(entry):
    im=Image.open(path(entry["file"])); data=np.array(im)
    check(entry["id"]+":SHA",sha(path(entry["file"]))==entry["sha256"])
    check(entry["id"]+":canvas",list(im.size)==entry["canvas"])
    check(entry["id"]+":mode",im.mode==entry["mode"])
    for s in entry["sources"]:
        check(entry["id"]+":sourceSHA",sha(path(s["file"]))==s["sha256"],source=s["file"])
    if entry["repeat_axes"]:
        check(entry["id"]+":X_exact",np.array_equal(data[:,0],data[:,-1]))
        check(entry["id"]+":Y_exact",np.array_equal(data[0],data[-1]))
    return im,data


def validate_normal(entry,data):
    id=entry["id"]; field=entry["heightfield"]
    height=np.load(path(field["file"]),allow_pickle=False)
    check(id+":heightSHA",sha(path(field["file"]))==field["sha256"])
    check(id+":geometrySHA",sha(path(field["geometry_file"]))==field["geometry_sha256"])
    check(id+":height_finite",np.isfinite(height).all())
    check(id+":height_native",height.dtype==np.float32 and height.shape==data.shape[:2])
    check(id+":height_range",[float(height.min()),float(height.max())]==field["range"])
    n,dx,dy=normal(height,entry["strength"],bool(entry["repeat_axes"]))
    base=Image.open(path(entry["sources"][0]["file"])).convert("RGBA")
    if entry.get("base_region"): base=base.crop(tuple(entry["base_region"]))
    support=np.array(base.getchannel("A"))==255
    if "transparent exterior" in entry["support"]:
        check(id+":outside_height_zero",np.all(height[~support]==0))
        check(id+":height_alpha_registration",np.array_equal(height>0,support))
        n[~support]=(0,0,1)
        check(id+":outside_normal_neutral",np.all(data[~support]==[128,128,255]))
    expected=np.clip(np.floor((n*.5+.5)*255+.5),0,255).astype(np.uint8)
    mismatch=int(np.any(data!=expected,axis=-1).sum())
    check(id+":independent_height_to_normal_exact",mismatch==0,mismatched_pixels=mismatch)
    decoded=data.astype(np.float64)/255*2-1
    length=np.linalg.norm(decoded,axis=-1)
    check(id+":decoded_unit_length",np.max(np.abs(length-1))<.009,max_error=float(np.max(np.abs(length-1))))
    check(id+":positive_Z",np.all(data[:,:,2]>=128),min_byte=int(data[:,:,2].min()))
    if entry.get("neutral_window"):
        x0,y0,x1,y1=entry["neutral_window"]
        check(id+":safe_window_full_plane",np.all(data[y0:y1,x0:x1]==[128,128,255]),rect=entry["neutral_window"])
    if entry["repeat_axes"]:
        for name,array in [("height",height),("dx",dx),("dy",dy)]:
            check(id+":"+name+"_X_exact",np.array_equal(array[:,0],array[:,-1]))
            check(id+":"+name+"_Y_exact",np.array_equal(array[0],array[-1]))
    if id=="metal_normal":
        check(id+":shallow_nonflat",np.any(data!=[128,128,255]) and height.max()<=.060001,
              nonflat_pixels=int(np.any(data!=[128,128,255],axis=-1).sum()))
        geometry=json.loads(path(field["geometry_file"]).read_text(encoding="utf-8"))
        label=np.array(Image.open(path(geometry["coating_mask"])))
        rgb=np.array(base)[:,:,:3]
        check(id+":categorical_mask_exact",np.array_equal(label==255,np.all(rgb==geometry["coating_label_rgb"],axis=-1)))
    if id=="concrete_normal": check(id+":intentional_flat",np.all(height==0) and np.all(data==[128,128,255]))
    return base,height,n,support


def font(size=13): return ImageFont.truetype("C:/Windows/Fonts/consola.ttf",size)


def norm_shade(n,support,light):
    v=np.array(light,dtype=np.float32);v/=np.linalg.norm(v)
    diffuse=np.clip((n*v).sum(axis=-1),0,1)
    intensity=np.rint((.18+.82*diffuse)*255).astype(np.uint8)
    result=np.zeros((*support.shape,4),np.uint8)
    result[:,:,:3]=intensity[:,:,None];result[:,:,3]=support.astype(np.uint8)*255
    return Image.fromarray(result)


def normal_review(entry,base,height,n,support):
    columns=[base,Image.open(REVIEW/f"{entry['id']}_height_display_v001.png").convert("RGBA"),
             Image.open(path(entry["file"])).convert("RGBA"),
             norm_shade(n,support,(-.65,.3,1)),norm_shade(n,support,(.65,.3,1)),
             norm_shade(n,support,(0,.8,1)),norm_shade(n,support,(0,-.8,1))]
    scale=2 if base.width<=128 else 1
    cell=max(160,base.width*scale+16); board=Image.new("RGBA",(cell*7,base.height*scale+100),"#182631")
    d=ImageDraw.Draw(board); labels=["BASE native","HEIGHT display","NORMAL RGB","LIGHT -X","LIGHT +X","LIGHT +Y(up)","LIGHT -Y(down)"]
    d.text((10,8),entry["id"]+" | CPU isolated normal-light proof; not Godot capture",font=font(),fill="white")
    for i,(im,label) in enumerate(zip(columns,labels)):
        im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
        board.alpha_composite(im,(i*cell+(cell-im.width)//2,48))
        d.text((i*cell+8,board.height-32),label,font=font(),fill="white")
    board.save(REVIEW/f"{entry['id']}_registration_light_v001.png")
    if entry["repeat_axes"]:
        # 3x3 真实周期法线和隔离光照：每格都是同一张输入，非新增素材。
        tile=norm_shade(n,support,(-.65,.3,1)).convert("RGB")
        grid=Image.new("RGB",(tile.width*3,tile.height*3))
        for y in range(3):
            for x in range(3): grid.paste(tile,(x*tile.width,y*tile.height))
        grid.save(REVIEW/f"{entry['id']}_3x3_light_v001.png")


def main():
    catalog=json.loads((SURFACES/"catalog.json").read_text(encoding="utf-8")); assets=catalog["assets"]
    check("asset_count_10",len(assets)==10)
    check("ids_unique",len({a['id'] for a in assets})==10)
    check("budget_D09_D11_D12",[sum(a['manifest_id']==m for a in assets) for m in ['D09','D11','D12']]==[3,6,1])
    # 合成斜坡做方向辨识，不复用任何生产高度。
    y,x=np.indices((5,5),dtype=np.float32)
    test,_,_=normal(x+2*y,1,False)
    check("OpenGL_direction_synthetic",np.all(test[:,:,0]<0) and np.all(test[:,:,1]>0) and np.all(test[:,:,2]>0),
          expectation="height increases to image right/down => N.x<0,N.y>0")
    scalar=[]
    for a in assets:
        im,data=format_png(a)
        if "heightfield" in a:
            base,height,n,support=validate_normal(a,data)
            normal_review(a,base,height,n,support)
        elif "nominal_parameter" in a:
            check(a['id']+":constant_parameter",np.all(data==a['byte_value']),byte=a['byte_value'],nominal=a['nominal_parameter'])
            check(a['id']+":quantization",abs(a['quantized_parameter']-a['nominal_parameter'])<=.5/255)
            scalar.append((a['id'],im))
        else:
            base=Image.open(path(a['sources'][0]['file'])).convert('RGBA');alpha=np.array(base.getchannel('A'))==255
            yy=np.indices(alpha.shape)[0];expected=np.rint(np.clip((119-yy)/109,0,1)*255).astype(np.uint8);expected[~alpha]=0
            check("grass:formula_exact",np.array_equal(data,expected))
            check("grass:root_zero",np.any(alpha[119]) and np.all(data[119,alpha[119]]==0))
            check("grass:top_one",np.any(alpha[10]) and np.all(data[10,alpha[10]]==255))
            check("grass:outside_zero",np.all(data[~alpha]==0))
            check("grass:actual_visible_height",np.where(alpha)[0].min()==10 and np.where(alpha)[0].max()==119)
            check("grass:anchor_boundary120",a['anchor']==[32,120] and a['root_boundary']==120)
            check("grass:geometrySHA",sha(path(a['geometry_file']))==a['geometry_sha256'])
            board=Image.new('RGBA',(480,360),'#182631');d=ImageDraw.Draw(board)
            base2=base.resize((128,256),Image.Resampling.NEAREST);board.alpha_composite(base2,(32,48))
            preview=Image.merge('RGBA',(im,im,im,base.getchannel('A'))).resize((128,256),Image.Resampling.NEAREST)
            board.alpha_composite(preview,(200,48));d.text((12,12),'GRASS native alpha / weight x2',font=font(),fill='white')
            d.text((12,322),'top y10=1 | root pixel y119=0 | boundary120',font=font(),fill='white')
            board.save(REVIEW/'grass_height_weight_registration_v001.png')
    # 顶层基线由根代理在技术输入任务开始前冻结；这里只核验受保护旧文件，不检查并发新文件。
    baseline=ROOT/'art-source/ember/technical-inputs-v001/protected-before.json'
    protected=0
    for file,original in json.loads(baseline.read_text(encoding='utf-8'))['sha256'].items():
        if file.startswith('assets/') or file.endswith(('.gd','.tscn','.gdshader')) or file=='project.godot':
            check('protected:'+file,sha(ROOT/file)==original);protected+=1
    if scalar:
        board=Image.new('RGB',(640,360),'#182631');d=ImageDraw.Draw(board)
        for i,(label,im) in enumerate(scalar):
            x=(i%2)*320;y=(i//2)*180;board.paste(im.resize((140,140)),(x+8,y+30));d.text((x+8,y+6),label,font=font(),fill='white')
            d.text((x+158,y+50),str(im.getpixel((0,0)))+'/255',font=font(),fill='white')
        board.save(REVIEW/'pbr_uniform_parameters_v001.png')
    failures=[c for c in CHECKS if not c['passed']]
    report={'status':'PASS' if not failures else 'FAIL','scope':'PNG native numeric checks, independent derivatives, CPU light registration; Godot runtime reviewed separately',
            'catalog_sha256':sha(SURFACES/'catalog.json'),'asset_count':len(assets),'check_count':len(CHECKS),'failure_count':len(failures),
            'protected_old_files_checked':protected,'checks':CHECKS,'failures':failures}
    (SURFACES/'validation-v001.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','asset_count','check_count','failure_count','protected_old_files_checked']},ensure_ascii=False))
    raise SystemExit(bool(failures))


if __name__=='__main__': main()
