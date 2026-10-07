"""独立重算SW源分区、刚性逆映射与局部补丁保护，不运行制作方CJS。"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
from PIL import Image
OUT = Path(__file__).resolve().parent
P = OUT/"package"
W,H = 64,96
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(path): return json.loads(path.read_text(encoding="utf-8-sig"))
def img(path): return Image.open(path).convert("RGBA")
def raw(path): return img(path).tobytes()
def path(value): return P/value.replace("\\","/")
def inside(x,y,poly):
    hit = False
    j = len(poly)-1
    for i,a in enumerate(poly):
        b = poly[j]
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            hit = not hit
        j = i
    return hit
ledger = load(P/"source/fixed-rig-pilot/down_left/rig_and_poses.json")
rig = ledger["rig"]
source = raw(path(ledger["source_file"]))
assert sha(path(ledger["source_file"]).read_bytes()) == ledger["source_sha256"]
parts = {"body":bytearray(source)}
owners = ["body"]*(W*H)
owned = Counter()
for y in range(H):
    for x in range(W):
        at = (y*W+x)*4
        if not source[at+3]: continue
        hits = [key for key,limb in rig["limbs"].items() if inside(x+.5,y+.5,limb["polygon"])]
        assert len(hits) <= 1
        owner = hits[0] if hits else "body"
        owned[owner] += 1
        owners[y*W+x] = owner
        if hits: parts["body"][at:at+4] = b"\0"*4
for key,limb in rig["limbs"].items():
    segments = ["upper","lower"]+(["end"] if limb["end_part"] else [])
    for segment in segments: parts[key+"_"+segment] = bytearray(W*H*4)
    for y in range(H):
        for x in range(W):
            if owners[y*W+x] != key: continue
            at = (y*W+x)*4
            if y < limb["split"][0]+2: parts[key+"_upper"][at:at+4] = source[at:at+4]
            if y >= limb["split"][0]-2 and (not limb["end_part"] or y < limb["split"][1]+.5):
                parts[key+"_lower"][at:at+4] = source[at:at+4]
            if limb["end_part"] and y >= limb["split"][1]-.5: parts[key+"_end"][at:at+4] = source[at:at+4]
assert len(parts) == 11
part_records = []
for entry in ledger["parts"]:
    data = bytes(parts[entry["id"]])
    actual = raw(path(entry["file"]))
    assert actual == data and sha(actual) == entry["raw_sha256"]
    part_records.append({"id":entry["id"],"rgba_source_partition_zero_difference":True,
        "raw_sha256":sha(actual),"actual_opaque_pixels":sum(actual[i+3]>0 for i in range(0,len(actual),4))})

def stamp(out,part,t):
    c,s = math.cos(t["radians"]),math.sin(t["radians"])
    sp,tp = t["sourcePivot"],t["targetPivot"]
    for y in range(H):
        for x in range(W):
            dx,dy = x+.5-tp[0],y+.5-tp[1]
            sx,sy = math.floor(dx*c+dy*s+sp[0]),math.floor(-dx*s+dy*c+sp[1])
            if sx<0 or sy<0 or sx>=W or sy>=H: continue
            at,dest = (sy*W+sx)*4,(y*W+x)*4
            if part[at+3]: out[dest:dest+4] = part[at:at+4]
def render(pieces,state):
    out = bytearray(W*H*4)
    for limb in rig["limb_order"]:
        if limb == "body": stamp(out,pieces["body"],state["transforms"]["body"])
        else:
            for segment in ["end","lower","upper"]:
                name = limb+"_"+segment
                if name in pieces: stamp(out,pieces[name],state["transforms"][name])
    return bytes(out)
identity = {"transforms":{}}
for key in parts:
    if key=="body": pivot=[32,56]
    else:
        limb,segment = key.rsplit("_",1)
        pivot = rig["limbs"][limb][{"upper":"root","lower":"joint","end":"end"}[segment]]
    identity["transforms"][key]={"sourcePivot":pivot,"targetPivot":pivot,"radians":0}
assert render(parts,identity) == source
protected_parts = {}
for key,part in parts.items():
    keep = bytearray(len(part))
    for y in range(H):
        for x in range(W):
            at=(y*W+x)*4
            if key=="body" or key.endswith("_end") or (key.startswith("arm_") and y>=57):
                keep[at:at+4]=part[at:at+4]
    coords=[(x,y) for y in range(H) for x in range(W) if keep[(y*W+x)*4+3]]
    if coords and (key.endswith("_end") or key.startswith("arm_")):
        minx,maxx=min(x for x,y in coords),max(x for x,y in coords)
        miny,maxy=min(y for x,y in coords),max(y for x,y in coords)
        for y in range(miny,min(H-1,maxy+2)+1):
            for x in range(max(0,minx-2),min(W-1,maxx+2)+1):
                at=(y*W+x)*4
                keep[at:at+4]=b"\xff"*4
    protected_parts[key]=keep
patch_record = load(P/"qa/down_left_joint_patch_v011.json")
quantized = img(P/"source/walk_down_left_joint_edit_quantized_v011.png")
assert quantized.size == (256,192)
quant = quantized.tobytes()
source_patch_path=path(patch_record["source_file"])
assert sha(source_patch_path.read_bytes())==patch_record["source_sha256"]
source_patch=img(source_patch_path)
assert list(source_patch.size)==patch_record["source_size"]
assert patch_record["common_sheet_transform"]==[256/source_patch.width,192/source_patch.height]
records = []
for i,state in enumerate(ledger["states"]):
    assert set(state["transforms"])==set(parts)
    assert all(set(t)=={"sourcePivot","targetPivot","radians"} for t in state["transforms"].values())
    original=raw(P/("source/fixed-rig-pilot/down_left/robot_walk_down_left_f%02d_v011.png"%i))
    assert render(parts,state)==original
    assert sha(original)==ledger["frames"][i]["raw_sha256"]
    protection=render(protected_parts,state)
    regions=[]
    for key,j in state["joints"].items():
        specs=[("hip","root",3.4,3.4),("knee","joint",4.8,5.6),("ankle","ankle",4,3.5)] if key.startswith("leg") else [("shoulder","root",3.4,3.4),("elbow","joint",3.5,4)]
        for name,center,rx,ry in specs: regions.append({"id":key+"_"+name,"center":j[center],"rx":rx,"ry":ry})
    claimed=patch_record["records"][i]
    assert claimed["regions"]==regions
    expected=bytearray(original)
    mask=bytearray(W*H*4)
    changes=[]
    for y in range(H):
        for x in range(W):
            at=(y*W+x)*4
            selected=[r["id"] for r in regions if ((x+.5-r["center"][0])/r["rx"])**2+((y+.5-r["center"][1])/r["ry"])**2<=1]
            if not selected or protection[at+3] or y<=46: continue
            mask[at:at+4]=b"\xff"*4
            src=(((i//4)*H+y)*256+(i%4)*W+x)*4
            expected[at:at+4]=quant[src:src+4]
            if original[at:at+4]!=expected[at:at+4]:
                changes.append({"xy":[x,y],"regions":selected,"before":list(original[at:at+4]),"after":list(expected[at:at+4])})
    output_path=P/("frames/walk/down_left/robot_walk_down_left_f%02d_v011.png"%i)
    actual=raw(output_path)
    assert actual==bytes(expected)
    assert raw(P/("qa/down_left_joint_patch_mask_f%02d.png"%i))==bytes(mask)
    assert claimed["changes"]==changes and claimed["changed_pixels"]==len(changes)
    assert sha(output_path.read_bytes())==claimed["output_sha256"]
    protected_diff=sum(actual[at:at+4]!=original[at:at+4] and protection[at+3]>0 for at in range(0,len(actual),4))
    outside_diff=sum(actual[at:at+4]!=original[at:at+4] and mask[at+3]==0 for at in range(0,len(actual),4))
    assert protected_diff==outside_diff==0
    records.append({"frame":i,"pilot_11_part_rgba_reconstruction_difference":0,"patch_reconstruction_difference":0,
        "computed_mask_difference":0,"changed_pixels":len(changes),"complete_changes_ledger_exact":True,
        "protected_body_hands_tool_boots_and_outline_rgba_changed":protected_diff,"outside_mask_full_rgba_changed":outside_diff})
result={"status":"SW_FIXED_SOURCE_AND_PATCH_LEDGER_PASS","source_opaque_partition":dict(owned),"parts":part_records,
    "source_partition_ambiguity":0,"neutral_full_rgba_difference":0,"records":records,
    "raw_edit_source_sha256":patch_record["source_sha256"],"quantized_patch_sha256":sha((P/"source/walk_down_left_joint_edit_quantized_v011.png").read_bytes()),
    "raw_edit_resampling_scope":"raw edit hash/dimensions + single sheet transform bound; compositor independently reconstructed from supplied quantized sheet"}
(OUT/"sw-pixel-reconstruction.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"status":result["status"],"parts":11,"source_opaque_partition":dict(owned),"records":records},ensure_ascii=False,indent=2))
