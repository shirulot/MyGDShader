"""c003静态绑定：不运行导出器/Godot，不机械判造型。"""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from PIL import Image
import json, hashlib, math
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
SRC=ROOT/"art-source/ember/enemy-eight-directions-v013/calibration_check_c003_drone"
P=OUT/"package"
Z=ROOT/"art-source/ember/deliveries/enemy_drone_diagonal_calibration_v013_c003_2026-10-06.zip"
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def img(path):return Image.open(path).convert("RGBA")
assert sha(Z.read_bytes())=="10ba6bfa175c1327869292252345b36410a36741b75b59d280781a4e8a9e3e3c"
with ZipFile(Z) as archive:
    names=archive.namelist()
    assert len(names)==len(set(names))==20 and archive.testzip() is None
    for n in names:
        q=PurePosixPath(n)
        assert not q.is_absolute() and ".." not in q.parts and ":" not in n and "\\" not in n
        assert ((archive.getinfo(n).external_attr>>16)&0o170000)!=0o120000
    declared=json.loads(archive.read("manifest.json"))
    manifest=[{"path":name,**item} for name,item in declared["files"].items()]
    assert len(manifest)==19 and {i["path"] for i in manifest}|{"manifest.json"}==set(names)
    for item in manifest:
        data=archive.read(item["path"])
        assert len(data)==item["bytes"] and sha(data)==item["sha256"]
        assert (SRC/item["path"]).read_bytes()==data
    assert (SRC/"manifest.json").read_bytes()==archive.read("manifest.json")
    for n in names:
        dest=P/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(archive.read(n))
report={"status":"STATIC_BINDING_PASS","archive":{"sha256":sha(Z.read_bytes()),"bytes":Z.stat().st_size,"files":20,"payload":19,"crc_safe_path_no_duplicates":True,"manifest":manifest}}
catalog=read(P/"catalog.json");registration=read(P/"registration.json")
assert catalog["registration_sha256"]==sha((P/"registration.json").read_bytes())
assert catalog["columns"]==registration["columns"]==4
assert [e["key"] for e in catalog["entries"]]==[e["key"] for e in registration["entries"]]==["neutral_down","generated_front_c002","neutral_down_left","neutral_down_right"]
images=[];report["pngs"]=[]
qa=read(P/"native_static_qa.json")
for entry in catalog["entries"]:
    key=entry["key"];path=P/(key+".png");image=img(path)
    assert image.size==(128,128) and sha(path.read_bytes())==entry["sha256"]==qa[key]["sha256"]
    assert entry["path"]=="res://calibration_check_c003_drone/"+key+".png"
    alpha=image.getchannel("A");hist=alpha.histogram()
    assert set(alpha.get_flattened_data())<={0,255}
    assert hist[0]==qa[key]["alpha_counts"]["0"] and hist[255]==qa[key]["alpha_counts"]["255"]
    assert list(alpha.getbbox())==qa[key]["bounds"]
    images.append(image)
    report["pngs"].append({"key":key,"sha256":sha(path.read_bytes()),"size":[128,128],"alpha_counts":{"0":hist[0],"255":hist[255]},"bbox_diagnostic_only":alpha.getbbox(),"catalog_and_current_output_match":True})
c002=ROOT/"art-source/ember/ta-review-v001/enemy-calibration-v013-c002/package/enemy_scout_drone"
assert (P/"neutral_down.png").read_bytes()==(c002/"approved_down.png").read_bytes()
assert (P/"generated_front_c002.png").read_bytes()==(c002/"generated_front.png").read_bytes()
v012=ROOT/"art-source/ember/deliveries/enemy_sequences_v012_2026-10-06.zip"
assert sha(v012.read_bytes())=="42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe"
with ZipFile(v012) as archive:
    old=next(n for n in archive.namelist() if n.endswith("/enemy_scout_drone/idle_down/f00.png"))
    assert (P/"neutral_down.png").read_bytes()==archive.read(old)
report["old_two"]={"approved_down_byte_equal_c002_and_v012":True,"c002_front_byte_equal_prior_fixed_c002":True,"approved_down_sha256":sha((P/"neutral_down.png").read_bytes()),"c002_front_sha256":sha((P/"generated_front_c002.png").read_bytes())}
report["contacts"]=[]
for bg,color in [("white",(255,255,255,255)),("black",(0,0,0,255))]:
    expected=Image.new("RGBA",(512,128),color)
    for i,image in enumerate(images):expected.alpha_composite(image,(i*128,0))
    assert expected.tobytes()==img(P/f"comparison_{bg}_1x.png").tobytes()
    assert expected.resize((2048,512),Image.Resampling.NEAREST).tobytes()==img(P/f"comparison_{bg}_4x.png").tobytes()
    report["contacts"].append({"background":bg,"native_and_nearest_4x_zero_rgba_diff":True})
guide=img(P/"axis_guides_8x.png")
assert guide.size==(2048,1024)
assert guide.resize((256,128),Image.Resampling.NEAREST).resize((2048,1024),Image.Resampling.NEAREST).tobytes()==guide.tobytes()
report["axis_guide"]={"sha256":sha((P/"axis_guides_8x.png").read_bytes()),"size":[2048,1024],"nearest_8x_blocks_exact":True,"hash_and_scale_bound_only_no_gpu_overlay_rerun":True}
report["registration"]=[]
for entry in registration["entries"][2:]:
    record=next(e for e in catalog["entries"] if e["key"]==entry["key"])
    assert math.isclose(entry["scale"],26/244*724/887,rel_tol=1e-14)
    source=P/"source"/Path(entry["source"]).name
    assert sha(source.read_bytes())==entry["source_sha256"]
    width,height=Image.open(source).size
    x,y,w,h=entry["source_rect"]
    assert x>=0 and y>=0 and x+w<=width and y+h<=height
    sx,sy=entry["source_anchor"];tx,ty=entry["target_anchor"];scale=entry["scale"]
    assert [tx,ty]==[64,80] and math.isclose(sx,sum(p[0] for p in entry["source_axes"])/2,abs_tol=1e-10)
    centers=[[tx+(a-sx)*scale,ty+(b-sy)*scale] for a,b in entry["source_axes"]]
    error=max(abs(a-b) for actual,declared in zip(centers,record["axis_centers_native"]) for a,b in zip(actual,declared))
    assert error<0.0001
    delta=[abs(centers[1][i]-centers[0][i]) for i in [0,1]]
    assert max(abs(a-b) for a,b in zip(delta,record["axis_delta_native"]))<0.0001
    for field in ["source","source_sha256","source_rect","target_anchor"]:assert record["registration"][field]==entry[field]
    assert math.isclose(record["registration"]["scale"],scale,rel_tol=1e-14)
    report["registration"].append({"key":entry["key"],"source_sha256":entry["source_sha256"],"single_uniform_scale":scale,"scale_formula":"26/244 * 724/887","target_probe_anchor":[64,80],"ground_root_contract":[64,104],"axis_centers_recomputed":centers,"axis_delta_recomputed":delta,"catalog_float32_error_max":error,"arithmetic_binding_only_not_shape_threshold":True})
provenance=read(P/"source_provenance.json")
report["source_provenance"]=[]
for name,item in provenance.items():
    assert sha((P/"source"/name).read_bytes())==item["sha256"]
    assert sha(Path(item["original"]).read_bytes())==item["sha256"]
    report["source_provenance"].append({"path":name,"sha256":item["sha256"],"fixed_and_original_source_match":True})
report["scope"]="static pack and provenance binding; no Godot, GPU regeneration or visual verdict"
(OUT/"integrity.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("C003_STATIC_BINDING_PASS: manifest19; old2bytes preserved; native4 and contacts exact; registration/source/guide bound")
