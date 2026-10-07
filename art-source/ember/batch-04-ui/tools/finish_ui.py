"""UI原生候选：母稿材料/轮廓采样后清边，逐图重绘关键语义；面板独立重建8px切片。

这不是把缩小母稿当成验收结果。采样仅提供起点，下面明确的32px坐标修正
删除母稿噪点/运行颜色，恢复小尺寸可读符号。JSON像素矩阵保留可编辑原生源。
所有输出只写本批 finished/review，不覆盖正式 assets、资源、旧场景或母稿。
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]
HEX = ["101820", "182631", "2B3E4B", "4D6470", "829BA3", "BECBC4", "7B4D35", "B77C4B", "E2B77A", "51C5C2", "E5A44B", "E65B4A", "566B78", "203A4B", "406B78", "ECE9D8"]
RGB = [tuple(bytes.fromhex(value)) for value in HEX]
O, S, D, M, H, L, BD, B, BT, CY, OR, RD, C, WD, WM, W = [(*color, 255) for color in RGB]
TRANSPARENT = (0, 0, 0, 0)
# 青/橙/红是运行状态，不烘焙到本批中性UI底图。黄铜与低对比水色仍可使用。
NEUTRAL = [color for index, color in enumerate(RGB) if index not in (9, 10, 11)]


def pixels(image):
    return image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_start(path):
    """只取真实主体Alpha>=128，避免母稿透明区中的极低Alpha碎粒扩大包围盒。"""
    raw = Image.open(path).convert("RGBA")
    bbox = raw.getchannel("A").point(lambda alpha: 255 if alpha >= 128 else 0).getbbox()
    crop = raw.crop(bbox)
    factor = 24 / max(crop.size)
    size = tuple(max(1, round(side * factor)) for side in crop.size)
    sample = crop.resize(size, Image.Resampling.NEAREST)
    out = Image.new("RGBA", (32, 32), TRANSPARENT)
    origin = ((32-size[0])//2, (32-size[1])//2)
    for y in range(size[1]):
        for x in range(size[0]):
            r, g, b, a = sample.getpixel((x, y))
            if a >= 128:
                nearest = min(NEUTRAL, key=lambda color: sum((color[i]-(r, g, b)[i])**2 for i in range(3)))
                out.putpixel((x+origin[0], y+origin[1]), (*nearest, 255))
    # 母稿取样的孤立单像素不作为材质；保留通信波瓣等较大的分离结构。
    seen = set()
    for y in range(4, 28):
        for x in range(4, 28):
            if (x, y) in seen or not out.getpixel((x, y))[3]:
                continue
            pending, component = [(x, y)], []
            while pending:
                point = pending.pop()
                if point in seen or not (4 <= point[0] < 28 and 4 <= point[1] < 28) or not out.getpixel(point)[3]:
                    continue
                seen.add(point)
                component.append(point)
                pending.extend((point[0]+dx, point[1]+dy) for dx, dy in ((0,1),(0,-1),(1,0),(-1,0)))
            if len(component) == 1:
                out.putpixel(component[0], TRANSPARENT)
    before_edge = out.copy()
    # 统一暴露边界为一个原生暗像素，修正缩图导致的亮边/半透明轮廓。
    for y in range(4, 28):
        for x in range(4, 28):
            if before_edge.getpixel((x, y))[3] and any(not before_edge.getpixel((x+dx, y+dy))[3] for dx, dy in ((0,1),(0,-1),(1,0),(-1,0))):
                out.putpixel((x, y), O)
    return out, {"source_alpha_threshold": 128, "source_body_bbox": list(bbox), "material_grid_size": list(size), "material_grid_origin": list(origin)}


def refine(asset_id, image):
    """以下是逐图原生坐标，不是把不同意义自动旋转/镜像得到新图标。"""
    d = ImageDraw.Draw(image)
    notes = []
    if asset_id == "hp":
        d.ellipse((11,12,21,23), fill=D, outline=O)
        d.rectangle((15,14,17,21), fill=L)
        d.rectangle((12,17,20,19), fill=L)
        d.line((15,14,16,14), fill=W)
        notes = ["保留母稿机械心形轮廓与陶瓷片；移除青色运行状态", "在(11,12)-(21,23)重建暗凹槽，逐像素画中性十字，最窄笔画3px"]
    elif asset_id == "energy":
        d.rectangle((13,11,19,23), fill=D, outline=O)
        d.line((14,12,14,21), fill=H)
        d.line((15,12,18,12), fill=M)
        notes = ["保留电芯顶触点和外壳，合并过细壳体色粒", "重建7×13中性深色窗口与1px左上亮边，避免灯亮状态"]
    elif asset_id == "time":
        d.ellipse((9,12,23,26), fill=L, outline=D)
        d.line((16,19,12,15), fill=D, width=2)
        d.line((16,19,21,15), fill=D, width=1)
        d.rectangle((15,18,17,20), fill=M)
        notes = ["保留母稿表冠/表壳，简化表盘碎点与小刻度", "重绘共用(16,19)轴的长短指针，保持无数字表盘"]
    elif asset_id == "interact":
        d.rectangle((20,5,27,12), fill=M, outline=O)
        d.line((21,6,26,6), fill=H)
        d.rectangle((22,7,25,10), fill=L)
        d.line((15,16,22,9), fill=D, width=4)
        d.line((15,16,22,9), fill=L, width=2)
        d.rectangle((16,14,17,15), fill=B)
        notes = ["保留机械手掌/拇指与关节材料，不替换为文字或emoji手", "将开关重建到右上8×8，指尖以2px陶瓷线连至开关，留下深关节"]
    elif asset_id == "log":
        d.rectangle((13,10,22,14), fill=D, outline=O)
        d.rectangle((14,11,21,13), fill=L)
        d.rectangle((8,10,9,11), fill=B)
        d.rectangle((8,19,9,20), fill=B)
        notes = ["保留书脊、装订件、下方页层，不新增模拟文字", "把标签简化为8×3空白板，修正两处黄铜扣为2×2固定像素"]
    elif asset_id == "pause":
        for x in (10,18):
            d.rectangle((x-1,8,x+4,24), fill=D, outline=O)
            d.rectangle((x,9,x+3,23), fill=L)
            d.line((x,9,x+2,9), fill=W)
            d.line((x+3,10,x+3,23), fill=H)
        notes = ["保留母稿钢板底座；去掉暂停条中的渐变碎粒", "重建等宽4px暂停条，条间4px暗间隙，顶端1px亮边"]
    elif asset_id == "lighting":
        d.line((12,8,12,18), fill=M)
        d.line((20,8,20,18), fill=D)
        d.line((14,8,14,12), fill=W)
        d.line((12,23,19,23), fill=M)
        d.line((13,25,18,25), fill=M)
        notes = ["保留灯泡玻璃和螺口轮廓；不加光线或亮灯颜色", "重绘两条1px护笼、玻璃反光和螺口横线，以形状区分能量电芯"]
    elif asset_id == "drainage":
        d.rectangle((14,9,18,17), fill=D)
        d.polygon([(11,15),(21,15),(16,21)], fill=D)
        d.rectangle((15,10,17,16), fill=L)
        d.polygon([(13,16),(19,16),(16,19)], fill=L)
        notes = ["保留接水盆及底部排出口，母稿下排语义保持", "在盆中央重建3px箭杆与三级箭尖；向下排出无需用颜色说明"]
    elif asset_id == "water_supply":
        d.polygon([(24,21),(21,25),(22,27),(26,27),(27,25)], fill=WM, outline=O)
        d.polygon([(24,22),(22,25),(23,26),(25,26),(26,25)], fill=L)
        d.point((23,24), fill=W)
        notes = ["保留阀柄、水平进管和向下弯嘴，与排水盆保持不同轮廓", "重绘右下7×7水滴及单像素反光，修复缩图水滴形状"]
    elif asset_id == "ventilation":
        d.ellipse((14,14,18,18), fill=M, outline=O)
        d.rectangle((15,15,17,17), fill=B)
        d.point((15,15), fill=BT)
        notes = ["保留四叶风扇及方形安装板，各叶间暗空隙不填平", "中心轮毂固定5×5，黄铜帽3×3；不使用雪花或烟雾"]
    elif asset_id == "cooling":
        d.ellipse((10,10,22,22), fill=D, outline=O)
        d.line((16,12,16,20), fill=L)
        d.line((12,13,20,19), fill=L)
        d.line((20,13,12,19), fill=L)
        for point in ((15,12),(17,12),(15,20),(17,20),(12,14),(12,18),(20,14),(20,18)):
            d.point(point, fill=L)
        notes = ["保留三组换热鳍片，避免与风扇相同轮廓", "中央重建6枝中性雪花与13×13暗底牌，细枝均1px而非运行光效"]
    elif asset_id == "communication":
        for points in ([(7,6),(5,9),(5,12),(5,16),(6,19),(8,21)], [(11,9),(9,11),(8,13),(8,15),(10,18)], [(24,6),(26,9),(26,12),(26,16),(25,19),(23,21)], [(20,9),(22,11),(23,13),(23,15),(21,18)]):
            d.line(points, fill=O, width=3)
            d.line(points, fill=H, width=1)
        d.rectangle((15,5,17,21), fill=M)
        d.rectangle((14,4,18,7), fill=L, outline=O)
        notes = ["保留天线柱与底座，四片波瓣是通信结构标记，不画光晕", "重建两对波瓣为1px亮线加暗衬，并固定柱与顶部陶瓷帽"]
    elif asset_id == "teleport":
        d.polygon([(16,11),(11,16),(14,16),(14,21),(18,21),(18,16),(21,16)], fill=O)
        d.polygon([(16,12),(13,15),(15,15),(15,20),(17,20),(17,15),(19,15)], fill=H)
        d.point((16,13), fill=L)
        notes = ["保留空心拱门与椭圆底座；透明开口不填色，无魔法特效", "中央箭头原生重画，2px杆与阶梯尖表达传送"]
    elif asset_id == "protection":
        d.ellipse((11,11,21,21), fill=M, outline=O)
        d.ellipse((14,14,18,18), fill=L)
        d.line((13,12,17,12), fill=H)
        notes = ["保留盾形陶瓷外壳，与心形HP独立区分", "把母稿圆芯重建为闭合环，5×5内孔用壳体浅色，表示稳定保护"]
    return notes


def panel():
    """8px四角/四边严格原生重建；没有沿可拉伸边条放螺栓或烘焙渐变。"""
    out = Image.new("RGBA", (96,96), S)
    d = ImageDraw.Draw(out)
    top = [O,H,L,M,D,S,H,O]
    bottom = [O,S,D,M,D,S,M,O]
    for inset in range(8):
        end = 95-inset
        d.line((inset,inset,end,inset), fill=top[inset])
        d.line((inset,inset,inset,end), fill=top[inset])
        d.line((inset,end,end,end), fill=bottom[inset])
        d.line((end,inset,end,end), fill=bottom[inset])
    # 只有8×8角块中有螺栓；边条的横截面恒定，任意横纵拉伸不会重复零件。
    for x,y in ((3,3),(89,3),(3,89),(89,89)):
        d.rectangle((x,y,x+3,y+3), fill=D, outline=O)
        d.rectangle((x+1,y+1,x+2,y+2), fill=B)
        d.point((x+1,y+1), fill=BT)
    for y in range(3):
        for x in range(3-y):
            for px,py in ((x,y),(95-x,y),(x,95-y),(95-x,95-y)):
                out.putpixel((px,py), TRANSPARENT)
    return out


def measure(image):
    data = list(pixels(image))
    alpha = Counter(pixel[3] for pixel in data)
    colors = sorted({pixel[:3] for pixel in data if pixel[3]})
    return {"canvas": list(image.size), "bbox": list(image.getchannel("A").getbbox()), "opaque_pixels": alpha[255],
            "transparent_pixels": alpha[0], "partial_alpha_pixels": sum(n for a,n in alpha.items() if a not in (0,255)),
            "color_count": len(colors), "palette_rgb": ["#%02X%02X%02X" % color for color in colors],
            "all_opaque_colors_in_standard16": all(color in RGB for color in colors)}


def save_editable_pixels(asset_id, image):
    alphabet = ".0123456789ABCDEF"
    rows = ["".join("." if not image.getpixel((x,y))[3] else alphabet[RGB.index(image.getpixel((x,y))[:3])+1] for x in range(image.width)) for y in range(image.height)]
    path = BATCH/"annotations"/f"{asset_id}_native_pixel_source_v001.json"
    path.write_text(json.dumps({"canvas": list(image.size), "transparent_symbol": ".", "palette_symbols": dict(zip(alphabet[1:],HEX)),
                                "notes": "每个字符对应一个原生像素，可直接编辑；Alpha只有0/255。", "rows": rows}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return path.relative_to(ROOT).as_posix()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", nargs="*", help="分组整理；省略则全部15项")
    args = parser.parse_args()
    plan = json.loads((BATCH/"planned-catalog-v001.json").read_text(encoding="utf-8"))
    ledger = json.loads((BATCH/"generation-record.json").read_text(encoding="utf-8"))
    catalog_path = BATCH/"ui-catalog-v001.json"
    existing = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {"status":"WORK_NATIVE_CANDIDATE_PENDING_CROSS_REVIEW", "assets":[]}
    selected = set(args.ids) if args.ids else {entry["id"] for entry in plan["assets"]}
    for spec in plan["assets"]:
        asset_id = spec["id"]
        if asset_id not in selected:
            continue
        source = BATCH/"generated"/f"{asset_id}_master_v001.png"
        generation = next(item for item in ledger["records"] if item["id"] == asset_id and item["version"] == 1)
        if sha(source) != generation["sha256"]:
            raise ValueError("原始母稿SHA改变："+asset_id)
        if asset_id == "panel_9slice":
            image, sampling = panel(), None
            modifications = ["参考母稿角部螺栓、钢板倒角与暗中部语汇，96×96逐像素重建", "四边8px恒厚横截面，螺栓限制在8×8角块，中央80×80统一色避免拉伸纹理", "母稿不规则边缘/透视/半透明渐变全部舍弃；四角仅切去3阶透明角"]
            method = "AI_STRUCTURE_MATERIAL_REFERENCE_NATIVE_9SLICE_REBUILD"
        else:
            image, sampling = source_start(source)
            sampled = image.copy()
            modifications = refine(asset_id, image)
            sampling["native_semantic_changed_pixels"] = sum(a != b for a,b in zip(pixels(sampled),pixels(image)))
            method = "AI_BODY_MATERIAL_SAMPLING_NATIVE_SEMANTIC_PIXEL_FINISH"
        # 留边与颜色先实测；候选状态不提前宣称视觉或正式生产通过。
        measurement = measure(image)
        if measurement["partial_alpha_pixels"] or not measurement["all_opaque_colors_in_standard16"]:
            raise ValueError("原生Alpha/调色板失败："+asset_id)
        if asset_id != "panel_9slice" and not (measurement["bbox"][0]>=4 and measurement["bbox"][1]>=4 and measurement["bbox"][2]<=28 and measurement["bbox"][3]<=28):
            raise ValueError("图标越过4px留白："+asset_id+str(measurement["bbox"]))
        output = BATCH/"finished"/f"{asset_id}_v001.png"
        image.save(output)
        pixel_source = save_editable_pixels(asset_id,image)
        finish = {"id":asset_id,"method":method,"source_use":{"mother":source.relative_to(ROOT).as_posix(),"mother_sha256":generation["sha256"],"source_unchanged":True,
                  "direct_original_rgba_byte_reuse":False,"meaning":"母稿仅作轮廓/量化材料起点并明确重画语义；面板只引用结构/材料，不冒称原图像素保留。", "sampling":sampling},
                  "adjustments":modifications,"native_pixel_source":pixel_source,"measurement":measurement,"output_sha256":sha(output)}
        finish_path = BATCH/"finished"/f"{asset_id}_v001.finish.json"
        finish_path.write_text(json.dumps(finish,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        entry = {**spec,"file":output.relative_to(ROOT).as_posix(),"sha256":sha(output),"bbox":measurement["bbox"],"size":list(image.size),
                 "source_use":finish["source_use"],"finishing_record":finish_path.relative_to(ROOT).as_posix(),"measurement":measurement,
                 "status":"NATIVE_CANDIDATE_PENDING_CROSS_REVIEW"}
        existing["assets"] = [old for old in existing["assets"] if old["id"] != asset_id]+[entry]
        print(json.dumps({"id":asset_id,"bbox":entry["bbox"],"file":entry["file"]},ensure_ascii=False))
    order = {entry["id"]:index for index,entry in enumerate(plan["assets"])}
    existing["assets"].sort(key=lambda entry:order[entry["id"]])
    existing["native_candidate_count"] = len(existing["assets"])
    catalog_path.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
