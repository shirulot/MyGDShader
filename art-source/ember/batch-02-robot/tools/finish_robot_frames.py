"""C01 四向原生帧整理器：只读AI母稿及已确认idle，显式原生标注驱动。

idle：主体块采样只提供材质/造型起点，轮廓、窗口、工具及足底由原生标注整理。
walk：不缩放、不扭曲已确认idle；分部件平移后按AI母稿姿态标注重画关节/遮挡。
      实际walk母稿必须存在并进入来源记录；不会凭复制idle伪造新的母稿记录。
本脚本只输出art-source工作帧及测量，不修改已有down PNG或正式assets目录。

使用方式：
  python finish_robot_frames.py --direction up --state idle --annotation annotations/idle_up.json
  python finish_robot_frames.py --direction up --state walk --frame 0 --annotation annotations/walk_up_f00.json

标注中的像素/多边形都是64×96原生坐标；bbox右/下边界排除。所有图像只用Pillow。
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[2]
CANVAS = (64, 96)
ANCHOR = (32, 80)
EMPTY = (0, 0, 0, 0)
HEX = ('101820', '182631', '2B3E4B', '4D6470', '829BA3', 'BECBC4',
       '7B4D35', 'B77C4B', 'E2B77A', '51C5C2', 'E5A44B', 'E65B4A',
       '566B78', '203A4B', '406B78', 'ECE9D8')
PALETTE = tuple(tuple(bytes.fromhex(s))+(255,) for s in HEX)
BASE_INDICES = (0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 15)
SIDES = ('down', 'up', 'left', 'right')


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def color(value: int | str) -> tuple:
    if isinstance(value, int):
        if value not in BASE_INDICES:
            raise ValueError('静态机器人不使用运行状态颜色')
        return PALETTE[value]
    if value == 'transparent': return EMPTY
    rgb = tuple(bytes.fromhex(value.removeprefix('#')))+(255,)
    if rgb not in [PALETTE[i] for i in BASE_INDICES]:
        raise ValueError(f'未登记静态颜色: {value}')
    return rgb


def nearest(rgb: tuple) -> tuple:
    i = min(BASE_INDICES, key=lambda k: sum((rgb[c]-PALETTE[k][c])**2 for c in range(3)))
    return PALETTE[i]


def largest_native_component(im: Image.Image) -> None:
    """仅去原生孤立背景碎片；主体有明确分离部件时不得靠此猜测补部件。"""
    remaining = {(x,y) for y in range(im.height) for x in range(im.width)
                 if im.getpixel((x,y))[3]}
    best = set()
    while remaining:
        seed = remaining.pop()
        component, queue = {seed}, deque([seed])
        while queue:
            x,y = queue.popleft()
            for dx,dy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
                q = (x+dx,y+dy)
                if q in remaining:
                    remaining.remove(q); component.add(q); queue.append(q)
        if len(component) > len(best): best = component
    for y in range(im.height):
        for x in range(im.width):
            if (x,y) not in best: im.putpixel((x,y), EMPTY)


def sample_idle_subject(source: Image.Image, annotation: dict) -> tuple[Image.Image, dict]:
    """从显式/测得主体框抽取材料，绝不把完整模型画布缩小当成成品。"""
    alpha = source.getchannel('A')
    if alpha.getextrema()[0] >= 240:
        raise ValueError('母稿缺少真实透明背景；先审阅并修正母稿，不能静默去绘制棋盘格')
    crop = annotation.get('source_subject_crop') or alpha.point(lambda v:255 if v>=240 else 0).getbbox()
    if crop is None: raise ValueError('母稿没有可辨认主体')
    x0,y0,x1,y1 = crop
    target_h = annotation.get('native_subject_height', 59)
    target_w = annotation.get('native_subject_width', round(target_h*(x1-x0)/(y1-y0)))
    if not (1 <= target_w <= 40 and 1 <= target_h <= 64):
        raise ValueError('主体比例超过40×64；应审阅构图/标注，不能无声压扁')
    native = Image.new('RGBA', (target_w,target_h), EMPTY)
    for y in range(target_h):
        for x in range(target_w):
            samples = [source.getpixel((int(x0+(x+(u+.5)/5)*(x1-x0)/target_w),
                                        int(y0+(y+(v+.5)/5)*(y1-y0)/target_h)))
                       for v in range(5) for u in range(5)]
            opaque = [p for p in samples if p[3]>=240]
            if len(opaque)>=13:
                rgb = tuple(sorted(p[c] for p in opaque)[len(opaque)//2] for c in range(3))
                native.putpixel((x,y), nearest(rgb))
    largest_native_component(native)
    result = Image.new('RGBA', CANVAS, EMPTY)
    origin = annotation.get('native_subject_origin', [(64-target_w)//2, 80-target_h])
    for y in range(target_h):
        for x in range(target_w):
            q = (x+origin[0],y+origin[1])
            if not (0<=q[0]<64 and 0<=q[1]<96): raise ValueError('原生主体越出画布')
            result.putpixel(q,native.getpixel((x,y)))
    return result, {'subject_crop':list(crop),'material_sampling_size':[target_w,target_h],
                    'native_subject_origin':origin,
                    'sampling_role':'材质和造型起点；不是独立验收结果'}


def outline_and_simplify(im: Image.Image) -> None:
    """原生孤立钢灰点简化及1px轮廓；不膨胀主体、不开启抗锯齿。"""
    old = im.copy()
    for y in range(1,95):
        for x in range(1,63):
            p = old.getpixel((x,y))
            if p not in [PALETTE[i] for i in (2,3,12)]: continue
            n = [old.getpixel((x+dx,y+dy)) for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]]
            if p not in n and all(q[3] for q in n):
                q,count = Counter(n).most_common(1)[0]
                if count>=3: im.putpixel((x,y),q)
    old = im.copy()
    for y in range(96):
        for x in range(64):
            if not old.getpixel((x,y))[3]: continue
            border = any(not (0<=x+dx<64 and 0<=y+dy<96) or
                         old.getpixel((x+dx,y+dy))[3]==0
                         for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)])
            if border: im.putpixel((x,y),PALETTE[0])


def native_edits(im: Image.Image, annotation: dict) -> None:
    """艺术标注逐像素/逐线/逐多边形重画，不把ROI误当完整语义部件。"""
    draw = ImageDraw.Draw(im)
    for patch in annotation.get('patches',[]):
        fill = color(patch['color'])
        if patch['type']=='pixel':
            x,y = patch['at']; im.putpixel((x,y),fill)
        elif patch['type']=='line':
            draw.line([tuple(p) for p in patch['points']],fill=fill,width=patch.get('width',1))
        elif patch['type']=='polygon':
            draw.polygon([tuple(p) for p in patch['points']],fill=fill)
        else: raise ValueError('patch类型应为pixel/line/polygon')


def parts_from_idle(idle: Image.Image, annotation: dict) -> dict[str,set]:
    """显式原生蒙版分配像素。交叠/遗漏会报错，防止悄悄丢手或重复装甲。"""
    parts, covered = {}, set()
    opaque = {(x,y) for y in range(96) for x in range(64) if idle.getpixel((x,y))[3]}
    rig_items=annotation.get('parts',[])
    if annotation.get('parts_file'):
        rig_items=json.loads((BASE/annotation['parts_file']).read_text(encoding='utf-8'))['parts']
    for item in rig_items:
        name = item['name']
        if name in parts: raise ValueError(f'重复部件: {name}')
        mask = Image.new('1',CANVAS)
        painter = ImageDraw.Draw(mask)
        for polygon in item.get('polygons',[]): painter.polygon([tuple(p) for p in polygon],fill=1)
        for x,y in item.get('pixels',[]): mask.putpixel((x,y),1)
        pixels = {(x,y) for x,y in opaque if mask.getpixel((x,y))}
        if not pixels: raise ValueError(f'空部件: {name}')
        if pixels & covered: raise ValueError(f'部件蒙版交叠: {name}')
        covered |= pixels; parts[name]=pixels
    if covered != opaque:
        raise ValueError(f'idle蒙版遗漏{len(opaque-covered)}个实体像素，需人工补足')
    return parts


def build_walk(idle: Image.Image, annotation: dict) -> tuple[Image.Image,dict]:
    """分部件的整数位移/遮挡与关节重画。禁止整体变形、缩放或镜像。

    每帧标注必须明确AI母稿观察到的步态/工具手，母稿像素不替代固定idle设计。
    转动膝肘等造型需要patches逐像素重绘，而不是对整件使用仿射变换。
    """
    if not annotation.get('pose_observation'):
        raise ValueError('walk缺少实际AI母稿姿态观察记录')
    parts=parts_from_idle(idle,annotation)
    offsets=annotation.get('offsets',{})
    order=annotation.get('draw_order',list(parts))
    if set(order)!=set(parts) or len(order)!=len(parts): raise ValueError('draw_order必须包含每部件一次')
    if set(offsets)!=set(parts): raise ValueError('必须逐部件声明整数位移，包括不移动的头/躯干')
    result=Image.new('RGBA',CANVAS,EMPTY)
    for name in order:
        dx,dy=offsets[name]
        if not isinstance(dx,int) or not isinstance(dy,int): raise ValueError('部件位移只能为原生整数像素')
        if name in ('head','torso') and max(abs(dx),abs(dy))>1:
            raise ValueError('头/身起伏超过1px，需重新审阅动作设计')
        for x,y in parts[name]:
            q=x+dx,y+dy
            if not (0<=q[0]<64 and 0<=q[1]<96): raise ValueError(f'部件越界:{name}')
            result.putpixel(q,idle.getpixel((x,y)))
    native_edits(result,annotation)
    return result, {'parts_pixel_counts':{name:len(p) for name,p in parts.items()},
                    'offsets':offsets,'draw_order':order,
                    'pose_observation':annotation['pose_observation'],
                    'idle_transform':'NONE_WHOLE_IMAGE','joint_repair':'explicit_native_patches'}


def prepare_down_walk_annotations() -> None:
    """已逐张观看四张down母稿后的原生标注，不直接采用母稿错误的同脚phase。

    部件边界来自已确认down原生PNG的实际39..69行读取：肩部宽，前臂收窄；
    不能把下半身最外侧腿甲误划入手臂。像素枚举确保每个实体像素恰好归属一次。
    AI四张都偏屏幕左脚前，f02比例漂移；本标注明确做动作/比例修正。
    """
    idle_path=ROOT/'assets/ember/characters/robot/robot_idle_down_v001.png'
    idle=Image.open(idle_path).convert('RGBA')
    names=['head','torso','right_arm','left_arm','right_leg','left_leg']
    parts={name:[] for name in names}
    for y in range(96):
        for x in range(64):
            if not idle.getpixel((x,y))[3]: continue
            if y<=39 or (y<=42 and 23<=x<=40): name='head'
            elif 40<=y<=48 and x<=23 or 49<=y<=64 and x<=20: name='right_arm'
            elif 40<=y<=48 and x>=40 or 49<=y<=65 and x>=44: name='left_arm'
            elif y<=61: name='torso'
            elif x<32: name='right_leg'
            else: name='left_leg'
            parts[name].append([x,y])
    rig={'idle_source':relative(idle_path),'idle_sha256':source_hash(idle_path),
         'mask_method':'观看原生实际像素后按头/肩/前臂/髋与两腿分配；每像素唯一归属',
         'anatomical_hands':'left_arm含屏幕右侧黄铜工具；right_arm为空手',
         'parts':[{'name':name,'pixels':pixels} for name,pixels in parts.items()]}
    annotation_dir=BASE/'annotations'
    annotation_dir.mkdir(parents=True,exist_ok=True)
    rig_path=annotation_dir/'rig_down_v001.json'
    rig_path.write_text(json.dumps(rig,ensure_ascii=False,indent=2),encoding='utf-8')
    for frame in range(4):
        bob=-1 if frame in [1,3] else 0
        # 下向：自身左脚在屏幕右；f0左支撑，f2右支撑，f1/f3对侧脚抬起。
        offsets={'head':[0,bob],'torso':[0,bob],
                 'right_arm':[0,1 if frame==0 else -1 if frame==2 else bob],
                 'left_arm':[0,-1 if frame==0 else 1 if frame==2 else bob],
                 'right_leg':[0,-1 if frame==0 else -2 if frame==1 else 0],
                 'left_leg':[0,-1 if frame==2 else -2 if frame==3 else 0]}
        # 原生补髋连接：只填已有接头内部的深灰，不新增长腿或漂浮投影。
        patches=[]
        for x in [26,38]:
            patches.append({'type':'pixel','at':[x,61+bob],'color':2})
            patches.append({'type':'pixel','at':[x,62+bob],'color':1})
        observation=('实际母稿工具保持屏幕右腕，四张均偏屏幕左脚前，未正确交替支撑足。'
                     +'本帧原生重建为'+['自身左脚触地/右脚后','左脚支撑/右脚经过抬起',
                                      '自身右脚触地/左脚后','右脚支撑/左脚经过抬起'][frame]+'. '
                     +('f02母稿头身偏高，已用确认idle头躯干替代以保持比例。' if frame==2 else
                       '头盔与胸甲保留确认idle比例，不能把母稿独立随机变化带入动画。'))
        rect=[30,52+bob,34,54+bob]
        record={'direction':'down','state':'walk','frame_index':frame,
                'idle_source':relative(idle_path),'parts_file':rig_path.relative_to(BASE).as_posix(),
                'design_observation':'圆陶瓷头盔、钢灰visor/关节、浅护甲和短靴；母稿为动作/材料参考而非直接帧提取',
                'tool_hand_observation':'确认idle的解剖左腕工具在屏幕右，与left_arm整件共同移动；没有镜像换手',
                'pose_observation':observation,
                'adjustments':['AI_POSE_INCONSISTENCY: 四母稿同脚前与f02比例漂移如实记录',
                               'NATIVE_CORRECTIVE_COMPOSITING: 确认idle逐像素部件分区、整数位移和髋关节原生修补',
                               'f0/f2交换实际支撑脚；f1/f3对侧脚抬高2原生像素，头身最多1像素起伏',
                               '肩臂与工具同一部件；固定64×96画布和虚拟脚底(32,80)，不自动裁切/整体warp'],
                'offsets':offsets,'draw_order':['right_leg','left_leg','torso','right_arm','left_arm','head'],
                'patches':patches,
                'runtime_windows':[{'id':'chest_status','safe_active_rect':rect,
                                   'center':[32,53+bob],'center_basis':'safe_active_rect_geometric_center',
                                   'normalized_uv':[0.5,(53+bob)/96],'mask_delivery_status':'NOT_PRODUCED'}]}
        record['gait']={'support_leg':'left' if frame in [0,1] else 'right',
                        'lifted_leg':'right' if frame==1 else 'left' if frame==3 else None,
                        'phase':['left_contact','right_passing','right_contact','left_passing'][frame],
                        'camera_depth':'down正面；双脚投影深度基本一致，至少一脚末行79',
                        'virtual_ground_anchor':[32,80]}
        (annotation_dir/f'walk_down_f{frame:02d}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')


def prepare_other_walk_annotations() -> None:
    """已逐张观看up/left/right共12母稿后，按各自idle结构建立非镜像的原生rig。

    三方向的近/远手和腿必须分别标注；侧面足底的屏幕高度差是相机投影，不是腿长。
    经过相可见最低点允许抬到78..79，虚拟地面原点仍是固定(32,80)。
    每部件全部像素唯一归属，头身/工具/装甲来自已确认方向idle。
    """
    observations={
      'up':[
        'f00母稿黄铜工具左侧保持；屏幕左腿最低，画出的前后投影与上向前移符号不稳，原生按上向左脚接触调整。',
        'f01母稿左侧工具保持，右靴抬起且露出底面；可用作右脚经过参考，头盔/背甲外形细节变化不带入原生。',
        'f02母稿右腿最低、左腿抬后，背甲维护槽与idle不同；原生交换支撑脚但保持确认维护口与头身比例。',
        'f03母稿左靴抬起露底，右靴支撑可辨；采用左脚经过语义，丢弃母稿新增装甲色块。'],
      'left':[
        'f00母稿前靴伸向左、另一靴后收，近侧左腕黄铜工具后摆；原生采用左脚接触及小幅反向摆臂。',
        'f01母稿与f00偏同只前靴，经过相不够明确；原生抬起远侧右脚并保持近侧左脚支撑。',
        'f02母稿黄铜近腕向前摆清楚，但头盔高度、身姿和步幅漂移；原生保留idle比例并交换右脚支撑。',
        'f03母稿前靴侧举、远靴落地，是经过相参考；原生让近侧左脚抬2px，不拉长远脚填齐bbox。'],
      'right':[
        'f00母稿两脚分开、右侧远腕黄铜接口保持；接触脚相位不够稳定，原生明确左脚接触。',
        'f01母稿近侧靴最低、远侧靴前伸，实际经过/接触语义混杂；原生让近侧右脚抬2px经过。',
        'f02母稿远侧腕黄铜接口前摆、近侧靴前伸可辨；原生采用右脚接触，保持idle头盔高光。',
        'f03母稿远侧靴抬起近侧支撑可作参考；原生左脚经过，工具部分遮挡保持同一手。']}
    annotation_dir=BASE/'annotations'
    for direction in ['up','left','right']:
        idle_path=BASE/'finished-frames'/f'robot_idle_{direction}_v001.png'
        idle=Image.open(idle_path).convert('RGBA')
        names=['head','torso','right_arm','left_arm','right_leg','left_leg']
        parts={name:[] for name in names}
        for y in range(96):
            for x in range(64):
                if not idle.getpixel((x,y))[3]: continue
                if direction=='up':
                    if y<=40 or (y<=42 and 24<=x<=40): name='head'
                    elif 41<=y<=50 and x<=24 or 51<=y<=64 and x<=22: name='left_arm'
                    elif 41<=y<=50 and x>=40 or 51<=y<=64 and x>=42: name='right_arm'
                    elif y<=61: name='torso'
                    elif x<32: name='left_leg'
                    else: name='right_leg'
                elif direction=='left':
                    if y<=41: name='head'
                    elif 42<=y<=52 and x<=25 or 53<=y<=59 and x<=23: name='right_arm'
                    elif 42<=y<=52 and x>=35 or 53<=y<=59 and x>=38 or 60<=y<=64 and x>=39: name='left_arm'
                    elif y<=55 or (y<=59 and 29<=x<=32): name='torso'
                    elif x<32: name='right_leg'
                    else: name='left_leg'
                else:
                    if y<=41: name='head'
                    elif 42<=y<=51 and x<=27 or 52<=y<=63 and x<=26 or 64<=y<=66 and x<=24: name='right_arm'
                    elif 42<=y<=55 and x>=40: name='left_arm'
                    elif y<=59: name='torso'
                    elif x<35: name='right_leg'
                    else: name='left_leg'
                parts[name].append([x,y])
        rig_path=annotation_dir/f'rig_{direction}_v001.json'
        rig={'idle_source':relative(idle_path),'idle_sha256':source_hash(idle_path),
             'mask_method':'观看实际原生像素后按方向的肩/前臂/髋及近远腿分区，每实体像素唯一归属；没有镜像',
             'parts':[{'name':n,'pixels':p} for n,p in parts.items()]}
        rig_path.write_text(json.dumps(rig,ensure_ascii=False,indent=2),encoding='utf-8')
        idle_annotation=json.loads((annotation_dir/f'idle_{direction}.json').read_text(encoding='utf-8'))
        for frame in range(4):
            bob=-1 if frame in [1,3] else 0
            if direction=='up':
                offsets={'head':[0,bob],'torso':[0,bob],
                         'left_arm':[0,1 if frame==0 else -1 if frame==2 else bob],
                         'right_arm':[0,-1 if frame==0 else 1 if frame==2 else bob],
                         'left_leg':[0,-1 if frame==0 else -2 if frame==3 else 0],
                         'right_leg':[0,-1 if frame==2 else -2 if frame==1 else 0]}
                order=['left_leg','right_leg','torso','left_arm','right_arm','head']
                patch_coords=[(26,61+bob,2),(26,62+bob,1),(38,61+bob,2),(38,62+bob,1)]
                depth='up背视双脚深度近似一致；前步沿屏幕上向，固定地面原点80'
            elif direction=='left':
                offsets={'head':[0,bob],'torso':[0,bob],
                         'left_arm':[1 if frame==0 else -1 if frame==2 else 0,bob],
                         'right_arm':[-1 if frame==0 else 1 if frame==2 else 0,bob],
                         'left_leg':[-2 if frame==0 else 1 if frame==2 else 0,-2 if frame==3 else 0],
                         'right_leg':[1 if frame==0 else -2 if frame==2 else 0,-1 if frame==1 else 0]}
                order=['right_leg','right_arm','torso','left_leg','left_arm','head']
                patch_coords=[(34,46+bob,2),(35,47+bob,1),(30,57+bob,2),(32,59+bob,1)]
                depth='left侧视：left_leg近侧靴最低79，right_leg远侧靴投影较高；f03近侧抬2px，全体最低可见末行78、bbox下边界79（含躯干/接缝），原点不动'
            else:
                offsets={'head':[0,bob],'torso':[0,bob],
                         'left_arm':[-1 if frame==0 else 1 if frame==2 else 0,bob],
                         'right_arm':[1 if frame==0 else -1 if frame==2 else 0,bob],
                         'left_leg':[2 if frame==0 else -1 if frame==2 else 0,-1 if frame==3 else 0],
                         'right_leg':[-1 if frame==0 else 2 if frame==2 else 0,-2 if frame==1 else 0]}
                order=['left_leg','left_arm','torso','right_leg','right_arm','head']
                patch_coords=[(29,46+bob,2),(29,47+bob,1),(34,59+bob,2),(33,61+bob,1)]
                depth='right侧视：right_leg近側靴最低79，left_leg远侧靴投影较高；f01近侧抬2px时bbox末端78，原点不动'
            patches=[{'type':'pixel','at':[x,y],'color':c} for x,y,c in patch_coords]
            windows=[]
            for window in idle_annotation.get('runtime_windows',[]):
                w=dict(window)
                r=w['safe_active_rect']
                w['safe_active_rect']=[r[0],r[1]+bob,r[2],r[3]+bob]
                w['center']=[w['center'][0],w['center'][1]+bob]
                w['normalized_uv']=[w['center'][0]/64,w['center'][1]/96]
                windows.append(w)
            record={'direction':direction,'state':'walk','frame_index':frame,
                'idle_source':relative(idle_path),'parts_file':rig_path.relative_to(BASE).as_posix(),
                'design_observation':'实际4母稿逐项观看；造型材料语汇相同但头身/维护槽/相位有漂移，用确认方向idle保持一致',
                'tool_hand_observation':idle_annotation['tool_hand_observation'],
                'pose_observation':observations[direction][frame],
                'adjustments':['AI_POSE_INCONSISTENCY: 观察到的模型phase/头身/装甲漂移逐帧如实记录',
                               'NATIVE_CORRECTIVE_COMPOSITING: 用确认方向idle的显式像素部件、不同近远zorder和局部关节修补',
                               '四phase明确接触/经过两脚交替；脚1–2px、摆臂1px、头身起伏1px；不整图warp/镜像',
                               '相机侧视的远近足底高度不同；虚拟地面原点固定(32,80)，抬脚可使可见底界78..80'],
                'offsets':offsets,'draw_order':order,'patches':patches,'runtime_windows':windows,
                'gait':{'support_leg':'left' if frame in [0,1] else 'right',
                        'lifted_leg':'right' if frame==1 else 'left' if frame==3 else None,
                        'phase':['left_contact','right_passing','right_contact','left_passing'][frame],
                        'camera_depth':depth,'virtual_ground_anchor':[32,80]}}
            (annotation_dir/f'walk_{direction}_f{frame:02d}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')


def measure(im: Image.Image, state: str = 'idle') -> dict:
    if im.size != CANVAS: raise ValueError('每帧固定64×96')
    pixels=[im.getpixel((x,y)) for y in range(96) for x in range(64)]
    bbox=im.getbbox()
    if bbox is None: raise ValueError('空帧')
    rules={'binary_alpha':{p[3] for p in pixels}<={0,255},
           'palette':{p for p in pixels if p[3]}<={PALETTE[i] for i in BASE_INDICES},
           'subject_max_40x64':bbox[2]-bbox[0]<=40 and bbox[3]-bbox[1]<=64,
           'ground_boundary_80':bbox[3]==80 if state=='idle' else 78<=bbox[3]<=80,
           'subject_centered_in_x12_52':12<=bbox[0] and bbox[2]<=52}
    if not all(rules.values()): raise ValueError(f'原生技术规则失败:{rules}')
    return {'canvas':list(CANVAS),'bbox':list(bbox),'anchor':list(ANCHOR),
            'anchor_convention':'idle足底边界80；末行79' if state=='idle' else
                                'walk虚拟地面原点固定(32,80)；可见底界78..80依近远投影/抬腳，不自动裁切',
            'visible_bottom_boundary':bbox[3],
            'rgb_count':len({p[:3] for p in pixels if p[3]}),'rules':rules}


def write_idle_review() -> None:
    """四方向共画布/共基线审阅；down正式PNG只读，审阅底色不进入成品。"""
    paths={'down':ROOT/'assets/ember/characters/robot/robot_idle_down_v001.png'}
    paths.update({d:BASE/'finished-frames'/f'robot_idle_{d}_v001.png' for d in ['up','left','right']})
    if any(not p.exists() for p in paths.values()): return
    board=Image.new('RGBA',(320,128),'#4D6470')
    draw=ImageDraw.Draw(board)
    for index,(direction,path) in enumerate(paths.items()):
        sprite=Image.open(path).convert('RGBA')
        board.alpha_composite(sprite,(index*80+8,8))
        draw.text((index*80+10,106),direction,fill='#ECE9D8')
        draw.line([(index*80+37,88),(index*80+43,88)],fill='#E2B77A')
    for scale in [1,2,4]:
        board.resize((320*scale,128*scale),Image.Resampling.NEAREST).save(
            BASE/'pixel-review'/f'idle_directions_review_{scale}x.png')


def write_walk_review(direction: str) -> None:
    """原生帧接触表与整数2倍8fps循环；脚底标记和底色不进入生产帧。"""
    paths=[BASE/'finished-frames'/f'robot_walk_{direction}_f{f:02d}_v001.png' for f in range(4)]
    if any(not p.exists() for p in paths): return
    idle_path=ROOT/'assets/ember/characters/robot/robot_idle_down_v001.png' if direction=='down' else \
        BASE/'finished-frames'/f'robot_idle_{direction}_v001.png'
    row=Image.new('RGBA',(400,128),'#4D6470')
    draw=ImageDraw.Draw(row)
    frames=[]
    for index,path in enumerate([idle_path]+paths):
        im=Image.open(path).convert('RGBA')
        row.alpha_composite(im,(index*80+8,8))
        draw.text((index*80+10,106),'idle' if index==0 else f'f{index-1:02d}',fill='#ECE9D8')
        draw.line([(index*80+37,88),(index*80+43,88)],fill='#E2B77A')
        if index:
            matte=Image.new('RGBA',CANVAS,'#4D6470'); matte.alpha_composite(im)
            ImageDraw.Draw(matte).line([(29,80),(35,80)],fill='#E2B77A')
            frames.append(matte.resize((128,192),Image.Resampling.NEAREST))
    review=BASE/'pixel-review'
    row.save(review/f'walk_{direction}_contact_1x.png')
    row.resize((800,256),Image.Resampling.NEAREST).save(review/f'walk_{direction}_contact_2x.png')
    frames[0].save(review/f'walk_{direction}_8fps_2x.apng',save_all=True,
                   append_images=frames[1:],duration=125,loop=0,disposal=1,blend=0)
    pal=Image.new('P',(1,1))
    pal.putpalette([v for rgba in PALETTE for v in rgba[:3]]+[0]*(768-48))
    gif=[im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE) for im in frames]
    # GIF延时单位是10ms，不能精确存125ms；120/130交替保持500ms循环、平均8fps。
    gif[0].save(review/f'walk_{direction}_8fps_2x.gif',save_all=True,
                append_images=gif[1:],duration=[120,130,120,130],loop=0,disposal=2,optimize=False)
    (review/f'walk_{direction}_preview_timing.json').write_text(json.dumps({
        'direction':direction,'frames':4,'production_preview_fps':8,
        'apng_durations_ms':[125,125,125,125],
        'gif_durations_ms':[120,130,120,130],
        'gif_cycle_ms':500,'gif_note':'10ms量化；平均8fps，APNG每帧精确125ms'},
        ensure_ascii=False,indent=2),encoding='utf-8')


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--direction',choices=SIDES,required=True)
    parser.add_argument('--state',choices=['idle','walk'],required=True)
    parser.add_argument('--frame',type=int,choices=range(4),default=0)
    parser.add_argument('--annotation',type=Path,required=True)
    args=parser.parse_args()
    annotation_path=args.annotation if args.annotation.is_absolute() else BASE/args.annotation
    annotation=json.loads(annotation_path.read_text(encoding='utf-8'))
    if annotation.get('direction') != args.direction or annotation.get('state')!=args.state:
        raise ValueError('标注方向/状态与CLI不一致')
    required=['design_observation','adjustments','tool_hand_observation','patches']
    if any(k not in annotation for k in required): raise ValueError('必须显式记录母稿观察/原生修改/工具手/像素修补')
    stem=f'robot_idle_{args.direction}' if args.state=='idle' else f'robot_walk_{args.direction}_f{args.frame:02d}'
    source=BASE/'generated'/(stem+'_master_v001.png')
    if not source.exists(): raise FileNotFoundError(f'实际AI母稿未到位，拒绝生成成品:{source}')
    before=source_hash(source)
    reference=Image.open(source).convert('RGBA')
    if args.state=='idle':
        result,process=sample_idle_subject(reference,annotation)
        outline_and_simplify(result)
        native_edits(result,annotation)
        dependencies=[]
    else:
        idle_path=ROOT/annotation['idle_source']
        idle=Image.open(idle_path).convert('RGBA')
        if idle.size!=CANVAS: raise ValueError('idle不是64×96原生帧')
        result,process=build_walk(idle,annotation)
        dependencies=[{'path':relative(idle_path),'sha256':source_hash(idle_path)}]
        if annotation.get('parts_file'):
            rig_path=BASE/annotation['parts_file']
            dependencies.append({'path':relative(rig_path),'sha256':source_hash(rig_path)})
    metrics=measure(result,args.state)
    if source_hash(source)!=before: raise RuntimeError('母稿被意外修改')
    out=BASE/'finished-frames'/(stem+'_v001.png')
    out.parent.mkdir(parents=True,exist_ok=True)
    result.save(out)
    record={'id':stem,'source':relative(source),'source_sha256':before,'output':relative(out),
            'output_sha256':source_hash(out),
            'annotation':relative(annotation_path),'annotation_sha256':source_hash(annotation_path),
            'dependencies':dependencies,'source_use':'AI_MATERIAL_AND_POSE_REFERENCE_WITH_NATIVE_PIXEL_FINISH',
            'observations':{k:annotation[k] for k in ['design_observation','tool_hand_observation']},
            'adjustments':annotation['adjustments'],'process':process,'measurement':metrics,
            'runtime_windows':annotation.get('runtime_windows',[]),
            'gait':annotation.get('gait'),
            'emitter_points':[],'emission_baked':False,'review_status':'ROOT_VISUAL_REVIEW_REQUIRED'}
    out.with_suffix('.finish.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    review=BASE/'pixel-review'
    review.mkdir(parents=True,exist_ok=True)
    for scale in [1,2,4]:
        matte=Image.new('RGBA',CANVAS,'#4D6470'); matte.alpha_composite(result)
        matte.resize((64*scale,96*scale),Image.Resampling.NEAREST).save(review/(stem+f'_{scale}x.png'))
    if args.state=='idle': write_idle_review()
    else: write_walk_review(args.direction)
    print(json.dumps({'output':relative(out),'measurement':metrics,'visual_status':'PENDING_ROOT_REVIEW'}))


if __name__=='__main__': main()
