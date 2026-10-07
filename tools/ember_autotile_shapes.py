"""v002 原生像素结构模板。

这是可编辑的像素结构源，不依赖旋转成品或给同一张图片换连接编号。
所有坐标都在 32px 网格中，结构与表面细节分开；光照始终来自左上。
"""
from functools import lru_cache
from PIL import Image, ImageDraw

HEX = ['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','7B4D35','B77C4B','E2B77A','51C5C2','E5A44B','E65B4A','566B78','203A4B','406B78','ECE9D8']
C = [tuple(bytes.fromhex(s)) + (255,) for s in HEX]
EMPTY = (0,0,0,0)
NEIGHBORS = [(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]

@lru_cache(maxsize=None)
def boundary(mask):
    """距空邻格的像素距离与朝向。跨格计算，避免把图块边框当成轮廓。

对角空格用 Chebyshev 距离产生工厂式直角凹口。连接处距离来自共同
的占用区域，因此图块两侧的包边不会随机错位。
"""
    result = []
    for y in range(32):
        row=[]
        for x in range(32):
            candidates=[]
            for bit,(ox,oy) in enumerate(NEIGHBORS):
                if mask & (1<<bit): continue
                dx = ox*32-x if ox>0 else x+1 if ox<0 else 0
                dy = oy*32-y if oy>0 else y+1 if oy<0 else 0
                candidates.append((max(dx,dy), ox if dx>=dy else 0, oy if dy>=dx else 0))
            row.append(min(candidates) if candidates else (99,0,0))
        result.append(row)
    return result

def bolt(draw,x,y):
    draw.rectangle((x,y,x+2,y+2),fill=C[0])
    draw.point((x,y),fill=C[4]); draw.point((x+1,y+1),fill=C[7])

def floor(mask,variant=0):
    """连续钢板内区 + 宽包边。变化只落在内区，不改变连接接口。"""
    im=Image.new('RGBA',(32,32)); field=boundary(mask)
    for y in range(32):
        for x in range(32):
            distance,dx,dy=field[y][x]
            if distance<=2: continue
            color=C[3]
            if distance==3: color=C[0]
            elif distance==4: color=C[5 if dx+dy<0 else 1]
            elif distance<=6: color=C[4 if dx+dy<0 else 2]
            # 薄板拼缝只画一条，内部没有每格一个厚黑框。
            elif y==16: color=C[2]
            elif y==17: color=C[12]
            elif x==16 and y<16: color=C[12]
            im.putpixel((x,y),color)
    d=ImageDraw.Draw(im)
    for x,y in [(8,8),(24,24)]:
        if field[y][x][0]>8: d.point((x,y),fill=C[4])
    if variant==1:
        for x,y in [(10,11),(11,11),(12,10),(23,21)]:
            if field[y][x][0]>8: d.point((x,y),fill=C[2])
    elif variant==2:
        for x,y in [(9,23),(10,23),(11,23),(10,24)]:
            if field[y][x][0]>8: d.point((x,y),fill=C[6 if x==10 else 7])
    return im

def wall(mask):
    """墙顶连续；只在外露南面画立面，在东侧画深侧面。

中心不再带一块完整的正面窗/面板。端墙会同时出现多个外露面，
内角依邻域自动收口，外角的亮暗交界构成角柱。
"""
    field=boundary(mask); im=Image.new('RGBA',(32,32))
    for y in range(32):
        for x in range(32):
            distance,dx,dy=field[y][x]
            if distance<=2: continue
            color=C[12]
            if distance==3: color=C[0]
            elif dy>0 and distance<=11:
                color=C[1 if distance<=5 else 2 if distance<=9 else 4]
                if distance in (6,7) and x%16 in (7,8): color=C[7 if distance==7 else 0]
            elif dx>0 and distance<=7: color=C[1 if distance<=4 else 2]
            elif dx+dy<0 and distance<=5: color=C[5 if distance==4 else 4]
            elif distance==6 and dx+dy<0: color=C[3]
            elif y in (11,12) and x%16 not in (0,15): color=C[3 if y==11 else 4]
            elif x==16: color=C[3]
            im.putpixel((x,y),color)
    return im

def water(mask):
    """8px 铆接渠岸与独立水底。全内区岸沿必须透明。"""
    field=boundary(mask)
    surface=Image.new('RGBA',(32,32)); bank=Image.new('RGBA',(32,32))
    for y in range(32):
        for x in range(32):
            distance,dx,dy=field[y][x]
            if distance<=2: continue
            surface.putpixel((x,y),C[13])
            if distance>11: continue
            light=dx+dy<0
            if distance==3: color=C[0]
            elif distance==4: color=C[4 if light else 1]
            elif distance<=8: color=C[3 if light else 2]
            elif distance==9: color=C[4]
            elif distance==10: color=C[0]
            else: color=C[14]
            # 铆钉属于岸带，按方向布置，不会跨进水域。
            along=x if dy else y
            if distance in (6,7) and along%16 in (7,8): color=C[7 if distance==7 and along%16==7 else 0]
            bank.putpixel((x,y),color)
    return surface,bank

def rail(mask):
    """直段无中心柱；端柱、转角柱和分流节点有各自结构。"""
    im=Image.new('RGBA',(32,32)); d=ImageDraw.Draw(im)
    # 各方向固定相同边界截面，端柱不能污染开放端口。
    for bit in range(4):
        if not mask & (1<<bit): continue
        if bit in (1,3):
            a,b=(16,31) if bit==1 else (0,16)
            for y,c in [(10,0),(11,4),(12,3),(13,2),(19,0),(20,4),(21,2)]: d.line((a,y,b,y),fill=C[c])
        else:
            a,b=(0,16) if bit==0 else (16,31)
            for x,c in [(10,0),(11,4),(12,3),(13,2),(19,0),(20,4),(21,2)]: d.line((x,a,x,b),fill=C[c])
    if mask in (5,10):
        # 直段只有薄接套；柱子留给端头/角/节点和可选的独立支撑道具。
        if mask==10:
            for y in (10,19): d.rectangle((14,y,17,y+2),fill=C[12]); d.point((14,y),fill=C[4])
        else:
            for x in (10,19): d.rectangle((x,14,x+2,17),fill=C[12]); d.point((x,14),fill=C[4])
    else:
        degree=mask.bit_count()
        radius=5 if degree>=3 else 4
        d.rectangle((16-radius,16-radius,16+radius,16+radius),fill=C[0])
        d.rectangle((17-radius,17-radius,15+radius,15+radius),fill=C[3])
        d.line((17-radius,17-radius,15+radius,17-radius),fill=C[4])
        bolt(d,15,15)
        if degree==1:
            # 端柱黄铜帽；与多向节点视觉区分。
            d.rectangle((14,12,18,13),fill=C[7]); d.line((14,12,18,12),fill=C[8])
    return im

def bridge(mask):
    """四向栈桥：各臂按行进方向铺踏板，节点为独立铆接平台。"""
    shape=Image.new('1',(32,32)); d=ImageDraw.Draw(shape)
    d.rectangle((4,4,27,27),fill=1)
    for bit,box in [(0,(4,0,27,15)),(1,(16,4,31,27)),(2,(4,16,27,31)),(3,(0,4,15,27))]:
        if mask & (1<<bit): d.rectangle(box,fill=1)
    im=Image.new('RGBA',(32,32)); degree=mask.bit_count()
    for y in range(32):
        for x in range(32):
            if not shape.getpixel((x,y)): continue
            # 臂的方向取决于位置，避免弯桥还沿用整张横向桥板。
            vertical=(mask in (1,4,5)) or (mask not in (2,8,10) and (y<10 or y>21))
            along=y if vertical else x
            color=C[2 if along%6==0 else 4 if along%6==1 else 3]
            if 10<=x<=21 and 10<=y<=21 and mask not in (5,10): color=C[12]
            for distance in (3,2,1):
                for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]:
                    xx,yy=x+dx*distance,y+dy*distance
                    if 0<=xx<32 and 0<=yy<32 and not shape.getpixel((xx,yy)):
                        color=C[0 if distance==1 else (4 if dx+dy<0 else 1) if distance==2 else 2]
            im.putpixel((x,y),color)
    d=ImageDraw.Draw(im)
    if mask not in (5,10):
        for x,y in [(11,11),(19,11),(11,19),(19,19)]: bolt(d,x,y)
        # 独立平台与端头有检修盖；多向节点保留通畅中心。
        if degree<=1:
            d.rectangle((14,14,18,18),outline=C[2]); d.line((15,15,17,15),fill=C[4])
    return im
