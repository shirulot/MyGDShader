"""独立 CPU 最近邻逆取样；检验固定源区可重组，不借用作者GPU PASS。"""
from pathlib import Path
from PIL import Image
import json, math, hashlib
OUT=Path(__file__).resolve().parent
P=OUT/"package"
rig=json.loads((P/"pilot_rigs.json").read_text())
def img(path): return Image.open(P/path.removeprefix("res://")).convert("RGBA")
def round_away(value): return math.floor(value+.5) if value>=0 else math.ceil(value-.5)
def inside(px,py,poly):
    # 每个源格按中心点登记。此包多边形轴线均为整数，射线可直接复算。
    value=False
    for i,(ax,ay) in enumerate(poly):
        bx,by=poly[i-1]
        if abs((px-ax)*(by-ay)-(py-ay)*(bx-ax))<1e-9 and min(ax,bx)<=px<=max(ax,bx) and min(ay,by)<=py<=max(ay,by): return True
        if (ay>py)!=(by>py) and px < (bx-ax)*(py-ay)/(by-ay)+ax: value=not value
    return value
def ownership(includes,excludes):
    return {(x,y) for y in range(128) for x in range(128)
        if (not includes or any(inside(x+.5,y+.5,p) for p in includes)) and not any(inside(x+.5,y+.5,p) for p in excludes)}
records=[]
for unit in rig["enabled_pilot_units"]:
    spec=next(u for u in rig["units"] if u["unit"]==unit)
    master=img(spec["source"])
    excluded=spec.get("remove_polygons",[])+[p["polygon"] for p in spec["parts"]]
    layers=[{"id":"body","mask":ownership([],excluded),"z":5}]
    for part in spec["parts"]:
        layers.append({"id":part["id"],"mask":ownership([part["polygon"]]+part.get("overlap_polygons",[]),part["exclude"]),"z":part["z"]})
    owners={p:[l["id"] for l in layers if p in l["mask"]] for y in range(128) for x in range(128) if master.getpixel((x,y))[3]>=128 for p in [(x,y)]}
    unowned=[list(p) for p,names in owners.items() if not names]
    expected_removed={p for p in owners if any(inside(p[0]+.5,p[1]+.5,poly) for poly in spec.get("remove_polygons",[]))}
    assert {tuple(p) for p in unowned}==expected_removed
    duplicate=[{"point":list(p),"parts":names} for p,names in owners.items() if len(names)>1]
    expected_overlaps=spec.get("parts",[])
    for item in duplicate:
        x,y=item["point"]
        assert any(any(inside(x+.5,y+.5,poly) for poly in part.get("overlap_polygons",[])) for part in expected_overlaps)
    leg_image=img(spec["leg_source"]) if "leg_source" in spec else None
    outputs=[]
    for index in [-1]+list(range(8)):
        bob=0 if index==-1 else ([0,0,1,0,0,0,1,0][index] if unit=="enemy_tracked_heavy" else [0,0,-1,0,0,0,-1,0][index])
        moves={}
        if unit=="enemy_cutter":
            for leg in spec["legs"]:
                phase=0 if index==-1 else (index+leg["phase_offset"])%8
                if index==-1: travel=(0,0)
                else:
                    depth=[2,1,0,-1,-2,-1,0,1][phase]
                    lift=[0,0,0,0,0,1,2,1][phase]
                    # Godot roundf 的半整数向外取整；Python round 的银行家取整不等价。
                    travel=(round_away(depth*.7),round_away(depth*.25-lift))
                moves[leg["id"]]=travel
        # 实际导出用 Godot Color.TRANSPARENT 清空，PNG空格为白RGB/Alpha0；
        # 比较全RGBA必须遵守这个已有空格契约，不把隐藏RGB当轮廓差异。
        output=Image.new("RGBA",(128,128),(255,255,255,0))
        render_layers=[dict(layer) for layer in layers]
        if unit=="enemy_cutter":
            for leg in spec["legs"]:
                if not leg.get("registered",False): render_layers.append({"id":leg["id"],"z":leg["z"],"leg":leg})
        for layer in sorted(render_layers,key=lambda l:l["z"]):
            dx,dy=moves.get(layer["id"],(0,0))
            if layer["id"]=="body":dy=bob
            for y in range(128):
                for x in range(128):
                    if "leg" in layer:
                        leg=layer["leg"]; sx,sy,sw,sh=leg["source_rect"]
                        ox,oy=leg["target_origin"]; scale=leg["scale"]
                        lx=(x+.5-ox-dx)/scale;ly=(y+.5-oy-dy)/scale
                        if not (0<=lx<sw and 0<=ly<sh):continue
                        color=leg_image.getpixel((sx+math.floor(lx),sy+math.floor(ly)))
                    else:
                        px,py=x-dx,y-dy
                        if (px,py) not in layer["mask"]:continue
                        color=master.getpixel((px,py))
                        if unit=="enemy_tracked_heavy" and layer["id"]!="body" and index!=-1:
                            start=43 if 43<=px<55 else (90 if 90<=px<102 else None)
                            if start is not None:
                                top=(84 if start==43 else 72)-math.floor((px-start)*.25)
                                if top<=py<top+16:
                                    rgb=master.getpixel((px,top+(py-top-index*2)%16))[:3]
                                    color=(*rgb,color[3])
                    if color[3]>=128:output.putpixel((x,y),(*color[:3],255))
        suffix="rig_neutral_down_right.png" if index==-1 else f"move_down_right/f{index:02}.png"
        actual=img(f"output/{unit}/{suffix}")
        changes=[(x,y) for y in range(128) for x in range(128) if output.getpixel((x,y))!=actual.getpixel((x,y))]
        visible=[p for p in changes if output.getpixel(p)[3] or actual.getpixel(p)[3]]
        outputs.append({"frame":"bind" if index==-1 else index,"full_rgba_diff_pixels":len(changes),"visible_rgba_diff_pixels":len(visible),"sample_differences":[{"point":p,"cpu":output.getpixel(p),"actual":actual.getpixel(p)} for p in changes[:12]]})
    records.append({"unit":unit,"source_part_visible_points":{l["id"]:sum(master.getpixel(p)[3]>=128 for p in l["mask"]) for l in layers},"original_visible_removed_points":unowned,"declared_overlap_points":duplicate,"frames":outputs,"fixed_front_source_sha256":hashlib.sha256((P/spec["leg_source"].removeprefix("res://")).read_bytes()).hexdigest() if leg_image else None})
(OUT/"fixed-parts-reconstruction.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({r["unit"]:{"removed":len(r["original_visible_removed_points"]),"overlap":len(r["declared_overlap_points"]),"differences":[f["full_rgba_diff_pixels"] for f in r["frames"]]} for r in records}))
