"""候选审阅图和9slice实际像素测量；不修改finished PNG。"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]


def font(size):
    path = Path("C:/Windows/Fonts/msyh.ttc")
    return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default()


def label(canvas,position,text,size=12,color="#BECBC4"):
    ImageDraw.Draw(canvas).text(position,text,font=font(size),fill=color)


def nine_slice(source,width,height):
    """用原始8px角块，四条边只沿长度缩放，中心单独拉伸。"""
    if min(width,height) < 16:
        raise ValueError("尺寸至少16，以容纳两侧固定8px边框")
    out = Image.new("RGBA",(width,height),(0,0,0,0))
    original = [0,8,88,96]
    target_x,target_y = [0,8,width-8,width],[0,8,height-8,height]
    for row in range(3):
        for column in range(3):
            fragment = source.crop((original[column],original[row],original[column+1],original[row+1]))
            size = (target_x[column+1]-target_x[column],target_y[row+1]-target_y[row])
            fragment = fragment.resize(size,Image.Resampling.NEAREST)
            out.paste(fragment,(target_x[column],target_y[row]))
    return out


def measure_slice(source,output):
    width,height = output.size
    corner_pairs = [((0,0,8,8),(0,0,8,8)),((88,0,96,8),(width-8,0,width,8)),
                    ((0,88,8,96),(0,height-8,8,height)),((88,88,96,96),(width-8,height-8,width,height))]
    corners = all(source.crop(a).tobytes()==output.crop(b).tobytes() for a,b in corner_pairs)
    rails = all(output.getpixel((x,y))==source.getpixel((8,y)) for x in range(8,width-8) for y in range(8))
    rails &= all(output.getpixel((x,height-8+y))==source.getpixel((8,88+y)) for x in range(8,width-8) for y in range(8))
    rails &= all(output.getpixel((x,y))==source.getpixel((x,8)) for x in range(8) for y in range(8,height-8))
    rails &= all(output.getpixel((width-8+x,y))==source.getpixel((88+x,8)) for x in range(8) for y in range(8,height-8))
    center = all(output.getpixel((x,y))==source.getpixel((8,8)) for x in range(8,width-8) for y in range(8,height-8))
    return {"size":[width,height],"slice_margins":[8,8,8,8],"four_corners_byte_identical":corners,
            "all_four_rail_cross_sections_constant":bool(rails),"center_uniform":center,"pass":bool(corners and rails and center)}


def main():
    catalog = json.loads((BATCH/"ui-catalog-v001.json").read_text(encoding="utf-8"))
    review = BATCH/"review"
    review.mkdir(exist_ok=True)
    for theme,bg,fg in (("dark","#101820","#BECBC4"),("light","#D6D3C7","#182631")):
        contact = Image.new("RGB",(720,484),bg)
        label(contact,(12,6),"UI15 原生候选 · 14图标32×32 / 面板96×96",14,fg)
        for index,entry in enumerate(catalog["assets"]):
            x,y = (index%5)*144,32+(index//5)*144
            image = Image.open(ROOT/entry["file"]).convert("RGBA")
            px,py = x+(144-image.width)//2,y+28+(96-image.height)//2
            contact.paste(image,(px,py),image)
            label(contact,(x+8,y+6),entry["id"],11,fg)
            label(contact,(x+8,y+124),entry["name"],11,fg)
        native = review/f"all_ui_native_{theme}_v001.png"
        contact.save(native)
        contact.resize((1440,968),Image.Resampling.NEAREST).save(review/f"all_ui_2x_{theme}_v001.png")
    # 源与原生对照：原图主体裁切仅用于审阅缩略图，原始PNG字节不改。
    comparison = Image.new("RGB",(960,660),"#182631")
    label(comparison,(12,4),"母稿轮廓/材料参考 → 原生语义整理（母稿缩略图不作为生产）",14)
    for index,entry in enumerate(catalog["assets"]):
        x,y = (index%5)*192,30+(index//5)*208
        raw = Image.open(ROOT/entry["source_use"]["mother"]).convert("RGBA")
        bbox = raw.getchannel("A").point(lambda a:255 if a>=128 else 0).getbbox()
        thumb = raw.crop(bbox)
        thumb.thumbnail((88,112),Image.Resampling.NEAREST)
        comparison.paste(thumb,(x+4,y+26),thumb)
        native = Image.open(ROOT/entry["file"]).convert("RGBA")
        display = native.resize((64,64),Image.Resampling.NEAREST) if native.width==32 else native
        comparison.paste(display,(x+94,y+36),display)
        label(comparison,(x+4,y+3),entry["id"],11)
        label(comparison,(x+4,y+148),"真实母稿       原生候选",11)
        label(comparison,(x+4,y+173),"语义重画/边界修正" if entry["id"]!="panel_9slice" else "8px结构重建",11)
    comparison.save(review/"source_to_native_review_v001.png")
    source = Image.open(BATCH/"finished/panel_9slice_v001.png").convert("RGBA")
    cases = [(96,96,20,48),(256,64,160,48),(96,160,448,48),(160,96,568,48),(320,120,20,248),(256,128,376,248)]
    measurements = []
    for theme,bg,fg in (("dark","#101820","#BECBC4"),("light","#D6D3C7","#182631")):
        canvas = Image.new("RGB",(768,408),bg)
        label(canvas,(12,4),"九宫格多尺寸预览 · 四角及边框保持8px · 中部平静",14,fg)
        for width,height,x,y in cases:
            output = nine_slice(source,width,height)
            canvas.paste(output,(x,y),output)
            label(canvas,(x,y-20),f"{width}×{height}",12,fg)
            if theme=="dark":
                measurements.append(measure_slice(source,output))
        canvas.save(review/f"panel_9slice_multisize_{theme}_v001.png")
    (review/"panel_9slice_measurement_v001.json").write_text(json.dumps({"method":"actual native 8px nine-slice reconstruction","cases":measurements,
         "all_pass":all(item["pass"] for item in measurements),"scope":"像素切片测量与审阅图；Godot StyleBoxTexture 实际加载由根代理后续执行。"},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"candidate_count":len(catalog["assets"]),"nine_slice_cases":len(measurements),"nine_slice_all_pass":all(item["pass"] for item in measurements)},ensure_ascii=False))


if __name__=="__main__":
    main()
