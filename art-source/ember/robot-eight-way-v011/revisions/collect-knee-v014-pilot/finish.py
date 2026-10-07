"""整理生图结果：统一尺度、以鞋底标记对齐、限色和导出；不绘制角色像素。"""
from pathlib import Path
from PIL import Image
import json, hashlib

ROOT = Path(__file__).resolve().parent
PALETTE = [tuple(bytes.fromhex(c)) for c in ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A']]
src = Image.open(ROOT/'source/generated-v1.png').convert('RGBA')
assert src.width == src.height, src.size
# 人工标记相同的鞋底支撑位置；所有帧使用同一个缩放，不按轮廓大小逐帧拟合。
display_marks = [(200, 581), (620, 581), (1055, 581), (258, 1183), (625, 1181), (1044, 1179)]
sole_marks = [(x*src.width/1280,y*src.height/1280) for x,y in display_marks]
scale = .123*1280/src.width
# 首次导出逐帧核对鞋底后，修正人工标记至实际接地像素（只平移）。
sole_marks = [(x,y+dy/scale) for (x,y),dy in zip(sole_marks,[1,1,1,3,3,1])]
frames, records = [], []
cache = {}
for i, (sx, sy) in enumerate(sole_marks):
    # 仅固定网格切片内取样，防止其他格的像素进入本帧。
    x0, y0 = round((i%3)*src.width/3), (i//3)*(src.height//2)
    x1 = round((i%3+1)*src.width/3)
    cell = src.crop((x0,y0,x1,y0+src.height//2))
    result = cell.transform((64,96), Image.Transform.AFFINE,
        (1/scale,0,sx-x0-30/scale,0,1/scale,sy-y0-79/scale), Image.Resampling.NEAREST)
    values=[]
    for r,g,b,a in result.get_flattened_data():
        if a < 210: values.append((0,0,0,0)); continue
        key=(r,g,b)
        if key not in cache: cache[key]=min(PALETTE,key=lambda c:sum((c[j]-key[j])**2 for j in range(3)))
        values.append((*cache[key],255))
    result.putdata(values)
    frames.append(result)
# 首尾复用同一张生成的站立姿势；不把重画的站立帧冒充原始资产。
frames[-1] = frames[0].copy()
for i, result in enumerate(frames):
    filename=f'frames/left_collect_f{i:02d}.png'
    result.save(ROOT/filename)
    pts={(x,y) for y in range(96) for x in range(64) if result.getpixel((x,y))[3]}
    groups=[]
    while pts:
        stack=[pts.pop()]; count=0
        while stack:
            x,y=stack.pop();count+=1
            for n in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if n in pts: pts.remove(n);stack.append(n)
        groups.append(count)
    records.append({'frame':i,'file':filename,'components_4_connected':sorted(groups,reverse=True),'bbox':result.getbbox(),'sha256':hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()})

previews=ROOT/'previews';previews.mkdir(exist_ok=True)
strip=Image.new('RGBA',(64*6,96))
for i,im in enumerate(frames):strip.paste(im,(i*64,0))
strip.save(previews/'left_collect_strip.png')
strip.resize((1536,384),Image.Resampling.NEAREST).save(previews/'left_collect_strip_4x.png')
bg=(24,38,49,255)
animated=[]
for im in frames:
    back=Image.new('RGBA',im.size,bg);back.alpha_composite(im)
    animated.append(back.convert('RGB').resize((256,384),Image.Resampling.NEAREST))
for speed, durations in [('normal',[320,140,180,440,180,280]),('slow',[640,400,500,900,500,640])]:
    animated[0].save(previews/f'left_collect_{speed}.gif',save_all=True,append_images=animated[1:],duration=durations,loop=0,disposal=2)

qa={'status':'POSE_PILOT_AWAITING_VISUAL_FEEDBACK','frame_count':6,'canvas':[64,96],
    'single_scale_all_frames':scale,'registration':'manual sole landmarks, translation only; no per-frame bbox fit',
    'sole_landmarks_source':sole_marks,'target_sole':[30,79],'endpoints_identical':frames[0].tobytes()==frames[-1].tobytes(),
    'palette_max':11,'records':records,
    'limitations':['Whole character redrawn by imagegen; identity is approximate, not byte-preserved.',
      'Four-connected alpha components do not establish anatomical or animation quality.',
      'Pilot is left-facing only; no replacement of runtime clips.']}
(ROOT/'qa/validation.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(qa,ensure_ascii=False,indent=2))
