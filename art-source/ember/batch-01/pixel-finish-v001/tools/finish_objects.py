"""仅整理首批维修机器人朝下待机及采能站，保持新母稿只读。

步骤明确分开：
1. 母稿采样：在高 Alpha 的主体 bbox 内，以规则块采样得到材质/造型候选。
2. 原生像素整理：固定16色、二值轮廓、单像素外描边、局部材质简化。
3. 手工网格修改：足底、胸部中性窗口、站点窗口和安装点按精确原生坐标校正。
不是把整张像素风母稿粗缩后直接冒充合格资源；报告仅声明可自动测量的规则。
"""
from pathlib import Path
from collections import Counter, deque
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

FINISH = Path(__file__).resolve().parents[1]
BATCH = FINISH.parent
ROOT = BATCH.parents[2]
FINISH.mkdir(parents=True, exist_ok=True)
HEX = ['101820', '182631', '2B3E4B', '4D6470', '829BA3', 'BECBC4',
       '7B4D35', 'B77C4B', 'E2B77A', '51C5C2', 'E5A44B', 'E65B4A',
       '566B78', '203A4B', '406B78', 'ECE9D8']
PALETTE = [tuple(bytes.fromhex(s))+(255,) for s in HEX]
ALLOWED = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 15]
EMPTY = (0, 0, 0, 0)


def nearest(rgb):
    # 底图不保留运行状态色；只保留中性钢板、陶瓷和黄铜。
    return min(ALLOWED, key=lambda n: sum((rgb[k]-PALETTE[n][k])**2 for k in range(3)))


def set_pixel(im, x, y, n):
    im.putpixel((x, y), PALETTE[n] if n is not None else EMPTY)


def largest_component(im):
    """二值前景只保留最大的八连通主体，去母稿边缘小碎片；不填充真实孔洞。"""
    foreground = {(x,y) for y in range(im.height) for x in range(im.width)
                  if im.getpixel((x,y))[3]}
    best = set()
    while foreground:
        seed = foreground.pop()
        component = {seed}
        queue = deque([seed])
        while queue:
            x,y = queue.popleft()
            for dy in [-1,0,1]:
                for dx in [-1,0,1]:
                    p = (x+dx, y+dy)
                    if p in foreground:
                        foreground.remove(p)
                        component.add(p)
                        queue.append(p)
        if len(component) > len(best): best = component
    for y in range(im.height):
        for x in range(im.width):
            if (x,y) not in best: im.putpixel((x,y), EMPTY)


def sampled_subject(source, crop_box, size):
    """仅采样主体，而非大画布整体缩放；各块使用中位色去随机碎色。"""
    x0,y0,x1,y1 = crop_box
    out = Image.new('RGBA', size, EMPTY)
    for y in range(size[1]):
        for x in range(size[0]):
            sx0 = x0+x*(x1-x0)/size[0]
            sy0 = y0+y*(y1-y0)/size[1]
            block = [source.getpixel((int(sx0+(u+.5)*(x1-x0)/size[0]/5),
                                      int(sy0+(v+.5)*(y1-y0)/size[1]/5)))
                     for v in range(5) for u in range(5)]
            opaque = [p for p in block if p[3] >= 240]
            # 二值轮廓以多数主体像素判定，Alpha halo 和软边不会保留。
            if len(opaque) >= 13:
                rgb = tuple(sorted(p[k] for p in opaque)[len(opaque)//2] for k in range(3))
                out.putpixel((x,y), PALETTE[nearest(rgb)])
    largest_component(out)
    return out


def simplify_and_outline(im):
    """在原生网格去无结构孤立材质点，然后补连续1px外轮廓。

    只对钢板阴影色处理单点；眼、螺栓、黄铜工具和最高亮点保留。
    轮廓只改已有实体像素，不膨胀 bbox，也不把投影补回去。
    """
    original = im.copy()
    for y in range(1, im.height-1):
        for x in range(1, im.width-1):
            p = original.getpixel((x,y))
            if p not in [PALETTE[2], PALETTE[3], PALETTE[12]]: continue
            neighbors = [original.getpixel((x+dx,y+dy)) for dx,dy in
                         [(-1,0),(1,0),(0,-1),(0,1)]]
            if p not in neighbors and all(v[3] for v in neighbors):
                replacement,count = Counter(neighbors).most_common(1)[0]
                if count >= 3: im.putpixel((x,y), replacement)
    original = im.copy()
    for y in range(im.height):
        for x in range(im.width):
            if not original.getpixel((x,y))[3]: continue
            outside = any(not (0 <= x+dx < im.width and 0 <= y+dy < im.height) or
                          original.getpixel((x+dx,y+dy))[3] == 0
                          for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)])
            if outside: im.putpixel((x,y), PALETTE[0])


def robot_native(source):
    # 已读母稿：头盔、两手、腿和右侧黄铜维修工具均保留原来造型及非对称位置。
    crop = (201,239,832,1167)
    body = sampled_subject(source, crop, (40,59))
    simplify_and_outline(body)
    result = Image.new('RGBA',(64,96),EMPTY)
    result.paste(body,(12,21))
    # 原生重绘：胸部窗口为暗蓝灰中性凹面，避免母稿压缩产生散乱高亮点。
    for y in [52,53]:
        for x in range(30,34): set_pixel(result,x,y,2)
    for x in range(29,35): set_pixel(result,x,51,0)
    # 原生重绘：两个脚底边界明确落在 y=80；末行 y=79，不把锚点当像素中心。
    # 只重画母稿足底已有区域，不改变腿长或新添阴影。
    for left,right in [(19,26),(38,45)]:
        for x in range(left,right):
            if result.getpixel((x,78))[3]: set_pixel(result,x,79,0)
    # 头盔前窗保留采样轮廓；以连续两档钢灰清理最大暗面的小散点。
    for y in range(36,40):
        for x in range(27,37):
            if result.getpixel((x,y))[:3] in [PALETTE[n][:3] for n in [0,1,2,3]]:
                set_pixel(result,x,y,2 if y <= 38 else 1)
    return result,crop


def station_native(source):
    crop=(89,97,1033,1271)
    body=sampled_subject(source,crop,(94,118))
    simplify_and_outline(body)
    result=Image.new('RGBA',(128,160),EMPTY)
    result.paste(body,(17,26))
    # 原生重绘：窗口是未运行的静止灰蓝面，两档明暗，严禁能量状态色/发光。
    for y in range(66,95):
        for x in range(54,74):
            if result.getpixel((x,y))[:3] in [PALETTE[n][:3] for n in [0,1,2,3,12]]:
                set_pixel(result,x,y,2 if y < 89 else 1)
    # 安装点：左右地脚底的末行统一为143，脚底/基座边界为(64,144)。
    for left,right in [(35,48),(80,93)]:
        for x in range(left,right):
            if result.getpixel((x,142))[3]: set_pixel(result,x,143,0)
    return result,crop


def metrics(im, anchor, limits):
    rgba=[im.getpixel((x,y)) for y in range(im.height) for x in range(im.width)]
    bbox=im.getbbox()
    colors=sorted({p[:3] for p in rgba if p[3]})
    margins=[bbox[0],bbox[1],im.width-bbox[2],im.height-bbox[3]]
    rules={'binary_alpha':set(p[3] for p in rgba)<={0,255},
           'fixed_palette':set(p for p in rgba if p[3])<=set(PALETTE),
           'bbox_limit':bbox[2]-bbox[0]<=limits[0] and bbox[3]-bbox[1]<=limits[1],
           'foot_boundary_y':bbox[3]==anchor[1],
           'no_runtime_status_colors':all(PALETTE[n][:3] not in colors for n in [9,10,11])}
    if im.width==128: rules['minimum_margins_16']=min(margins)>=16
    assert all(rules.values()),rules
    return {'canvas':list(im.size),'bbox':list(bbox),'subject_size':[bbox[2]-bbox[0],bbox[3]-bbox[1]],
            'margins_l_t_r_b':margins,'anchor':anchor,'anchor_convention':'底边界；末行像素在anchor_y-1',
            'visible_rgb_count':len(colors),'rgb_hex':['#'+''.join(f'{v:02X}' for v in rgb) for rgb in colors],
            'alpha_values':sorted({p[3] for p in rgba}),'rules':rules}


def main():
    records=[]
    items=[('C01','robot_idle_down_master_v001.png','assets/ember/characters/robot/robot_idle_down_v001.png',
            robot_native,[32,80],[40,64]),
           ('B01','station_master_v001.png','assets/ember/buildings/station/station_base_v001.png',
            station_native,[64,144],[96,128])]
    finished={}
    for asset_id,name,target,procedure,anchor,limits in items:
        source_path=BATCH/'generated'/name
        before=hashlib.sha256(source_path.read_bytes()).hexdigest()
        source=Image.open(source_path).convert('RGBA')
        im,crop=procedure(source)
        destination=ROOT/target
        destination.parent.mkdir(parents=True,exist_ok=True)
        im.save(destination)
        assert hashlib.sha256(source_path.read_bytes()).hexdigest()==before
        measurement=metrics(im,anchor,limits)
        finished[asset_id]=im
        records.append({'id':asset_id,'source':str(source_path.relative_to(ROOT)).replace('\\','/'),
                        'source_sha256':before,'output':target,'source_size':list(source.size),
                        'source_subject_crop':list(crop),'method':'AI_SUBJECT_SAMPLING_AND_NATIVE_PIXEL_FINISH',
                        'adjustments':['高Alpha主体分块中位色采样；透明halo及边缘碎片剔除，母稿保持不变',
                                       '固定16色中的中性钢灰、陶瓷及黄铜；移除母稿碎色和渐变',
                                       '在原生网格整理1像素外轮廓与孤立材质点，不向透明区扩张主体',
                                       '原生重画中性窗口/安装点；脚底边界对齐固定锚点，保存二值Alpha'],
                        'details': '胸部窗口与头盔前窗清理；两脚最后一行对齐79' if asset_id=='C01' else
                                   '核心中性窗口两档暗面；左右地脚最后一行对齐143',
                        'measurements':measurement,'visual_status':'ROOT_REVIEW_REQUIRED_NOT_SELF_APPROVED'})
    (FINISH/'finishing-record.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    (FINISH/'measurements.json').write_text(json.dumps({'assets':[{'id':r['id'],**r['measurements']} for r in records],
       'scope':'自动技术规则通过，造型、比例和实际运行表现由root另行审阅'},ensure_ascii=False,indent=2),encoding='utf-8')
    # 两个实际画布以共同脚底基线显示；标签与锚点线只存在于审阅板。
    board=Image.new('RGBA',(320,224),'#4D6470')
    board.alpha_composite(finished['C01'],(48,96))
    board.alpha_composite(finished['B01'],(160,32))
    draw=ImageDraw.Draw(board)
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',10)
    draw.line([(16,176),(303,176)],fill='#829BA3')
    for x in [80,224]:
        draw.line([(x-3,176),(x+3,176)],fill='#E2B77A')
        draw.line([(x,173),(x,179)],fill='#E2B77A')
    draw.text((16,8),'NATIVE 1x / shared ground line',font=font,fill='#ECE9D8')
    draw.text((34,191),'C01 1/20',font=font,fill='#ECE9D8')
    draw.text((177,191),'B01 neutral',font=font,fill='#ECE9D8')
    board.save(FINISH/'objects_native_review.png')
    for scale in [2,4]:
        board.resize((320*scale,224*scale),Image.Resampling.NEAREST).save(FINISH/f'objects_{scale}x_review.png')
    print(json.dumps({'outputs':[r['output'] for r in records],'measurements':[r['measurements'] for r in records]},ensure_ascii=False))


if __name__=='__main__': main()
