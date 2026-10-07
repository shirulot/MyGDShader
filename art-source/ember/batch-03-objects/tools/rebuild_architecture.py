"""原生门框/门板与可拉伸屏幕框的结构修正，不对整图做缩放或镜像。

闭门AI稿偏方：直接等比采样66px高不足人物59px通行视觉。以实际母稿的
lintel/基脚像素、柱截面材料为来源，重新安排94px原生结构。门板与连接细节
在目标网格逐线绘制；两态使用同一个实际frame PNG，孔洞是真透明。
screen母稿边条长度/厚度有漂移：保留4个不同光照角的8px实际材料角块，
以固定色截面重画恒厚8px边条；九宫格中心48x48完全透明。
"""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
import finish_objects as f
BASE=Path(__file__).resolve().parents[1]
def native_doors():
    source=Image.open(BASE/'pixel-review/drafts/door_closed_draft.png').convert('RGBA')
    # 保留生成设计的陶瓷过梁、螺栓与铜角件；移到原生y18，没有缩放。
    frame=Image.new('RGBA',(96,128),f.EMPTY)
    frame.alpha_composite(source.crop((16,46,80,66)),(16,18))
    # 柱截面取自已观察的平直中部86行，每行材料/外轮廓一致。
    # 柱的长度重新设计，嵌入接缝、铜件、按钮；不是整个门体拉伸。
    for y in range(38,101):
        for x in list(range(16,26))+list(range(70,80)):
            frame.putpixel((x,y),source.getpixel((x,86)))
    frame.alpha_composite(source.crop((16,100,80,112)),(16,100))
    d=ImageDraw.Draw(frame)
    # 共安装结构：左上亮、右面暗；斜面接缝与铜连接口来自母稿语汇。
    for y in (58,88):
        d.line([(22,y),(25,y)],fill=f.COLORS[4]);d.line([(70,y),(73,y)],fill=f.COLORS[3])
        d.line([(21,y+1),(25,y+1)],fill=f.COLORS[2]);d.line([(70,y+1),(74,y+1)],fill=f.COLORS[1])
    for x in (18,76):
        d.rectangle([x,75,x+1,79],fill=f.COLORS[7]);d.line([(x,75),(x+1,75)],fill=f.COLORS[8])
    d.rectangle([70,62,75,70],fill=f.COLORS[0])
    d.rectangle([71,63,74,69],fill=f.COLORS[5])
    d.rectangle([72,64,73,68],fill=f.COLORS[2])
    # 根比例实审：机器人最大宽40，32px通路会夹臂。原生内柱收薄到44px通道。
    # 从过梁下38一直通到画布下112；阈值/地板不会填进通路。
    d.rectangle([26,38,69,111],fill=f.EMPTY)
    shared=BASE/'layers/door_shared';shared.mkdir(exist_ok=True)
    frame.save(shared/'frame_native.png')
    opened=frame.copy()
    closed=frame.copy();p=ImageDraw.Draw(closed)
    # 两块原生钢板。语汇来自母稿的折角轮廓、竖向嵌板、中心黄铜把手。
    p.rectangle([26,38,69,109],fill=f.COLORS[0])
    p.polygon([(27,39),(46,39),(46,107),(30,107),(27,104)],fill=f.COLORS[3])
    p.polygon([(49,39),(68,39),(68,104),(65,107),(49,107)],fill=f.COLORS[3])
    p.line([(27,41),(29,39),(44,39)],fill=f.COLORS[4])
    p.line([(29,43),(29,101),(32,104),(44,104)],fill=f.COLORS[4])
    p.line([(50,41),(65,41),(67,43),(67,101),(64,104),(51,104)],fill=f.COLORS[12])
    p.line([(47,39),(47,107)],fill=f.COLORS[1]);p.line([(48,39),(48,107)],fill=f.COLORS[1])
    p.rectangle([45,70,46,77],fill=f.COLORS[7]);p.rectangle([49,70,50,77],fill=f.COLORS[7])
    p.line([(45,70),(46,70)],fill=f.COLORS[8]);p.line([(49,70),(50,70)],fill=f.COLORS[8])
    p.line([(28,108),(67,108)],fill=f.COLORS[2])
    for ident,im in [('door_closed',closed),('door_open',opened)]:
        im.save(BASE/'layers/door_shared'/f'{ident}_native.png')
    return {'method':'NATIVE_STRUCTURAL_REBUILD',
      'sampled_parts':['closed draft 64x20 lintel cluster, moved y46->18 without scaling',
                       'closed draft feet rows100..111 copied unchanged',
                       'closed draft plain post cross-section row86 used as native material strip'],
      'native_redrawn':['94px tall posts, two seam joints and brass couplers',
                        '2 panel leaves with bevel seams/handles, no whole-image warp'],
      'shared_frame_file':f.rel(shared/'frame_native.png'),
      'shared_frame_sha256':f.sha(shared/'frame_native.png'),
      'opening_rect':[26,38,70,112],'opening_convention':'[x0,y0,x1,y1), genuine transparent aperture',
      'native_proportion_correction':'root actual review: widen aperture32->44px for existing40px robot, thin inner posts, preserve64x94 outer silhouette',
      'source_design_masters':[f.rel(BASE/'generated/door_closed_master_v001.png'),
                               f.rel(BASE/'generated/door_open_master_v001.png')],
      'exact_same_frame_and_anchor':True}

def native_screen():
    source=Image.open(BASE/'pixel-review/drafts/screen_frame_draft.png').convert('RGBA')
    screen=Image.new('RGBA',(96,96),f.EMPTY)
    for src,dst in [((16,19,24,27),(16,16)),((72,19,80,27),(72,16)),
                    ((16,72,24,80),(16,72)),((72,72,80,80),(72,72))]:
        screen.alpha_composite(source.crop(src),dst)
    # 8px钢灰截面与每角原生材料相配。光照始终世界左上，底/右不会镜像高光。
    top=[0,4,3,3,2,2,1,0];bottom=[0,2,3,3,3,1,1,0]
    left=[0,4,3,3,2,2,1,0];right=[0,2,3,3,2,1,1,0]
    for x in range(24,72):
        for k in range(8):screen.putpixel((x,16+k),f.COLORS[top[k]]);screen.putpixel((x,72+k),f.COLORS[bottom[k]])
    for y in range(24,72):
        for k in range(8):screen.putpixel((16+k,y),f.COLORS[left[k]]);screen.putpixel((72+k,y),f.COLORS[right[k]])
    # 保留source角的铜栓同时去稀碎点、补1px角连接。不是按文字凭空猜母稿Mask。
    f.native_cleanup(screen)
    screen.save(BASE/'layers'/'screen_frame_native.png')
    return {'method':'NATIVE_NINE_SLICE_REBUILD','sampled_parts':'four actual 8x8 corner clusters, no mirroring',
     'native_redrawn':'constant 8px material strips and 1px inner/outer outline; 48x48 alpha hole',
     'source_design_master':f.rel(BASE/'generated/screen_frame_master_v001.png'),
     'slice_region':[16,16,64,64],'slice_region_convention':'[x,y,width,height]',
     'slice_margins':{'left':8,'top':8,'right':8,'bottom':8},'center_rect':[24,24,72,72],
     'draw_center':False,'repeat':False}

def main():
    data={'door':native_doors(),'screen_frame':native_screen()}
    for item in data.values():
        refs=item.get('source_design_masters') or [item['source_design_master']]
        item['source_master_sha256']={r:f.sha(f.ROOT/r) for r in refs}
    f.save_json(BASE/'annotations'/'architectural-rebuild-record.json',data)
    print(json.dumps({'rebuilt':['door_closed','door_open','screen_frame'],'whole_image_warp':False}))
if __name__=='__main__':main()
