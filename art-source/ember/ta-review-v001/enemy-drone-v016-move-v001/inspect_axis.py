"""Read actual central pixels and create fixed-ROI last/first diagnostics."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw

base = Path(__file__).resolve().parent
package = base / "package"
spec = json.loads((package / "rig.json").read_text(encoding="utf-8-sig"))
data = {"axis_samples": [], "diagnostics_sha256": {}}
for direction, config in spec["configs"].items():
    frames = [Image.open(package / f"output/enemy_scout_drone/move_{direction}/f{index:02}.png").convert("RGBA") for index in range(8)]
    for fan in config["fans"]:
        x, y = map(int, fan["center"])
        colors = [list(frame.getpixel((x,y+spec["body_y"][index]))) for index,frame in enumerate(frames)]
        data["axis_samples"].append({"direction":direction,"fan":fan["id"],"center":fan["center"],"central_pixel":[x,y],"colors_f00_f07":colors,"constant":len({tuple(color) for color in colors})==1})
assert len(data["axis_samples"]) == 12 and all(item["constant"] for item in data["axis_samples"])
for name, bg in [("light",(232,232,228,255)),("dark",(25,42,52,255))]:
    # Side/back axes are the new view configurations. Keep all three common ROIs.
    sheet = Image.new("RGBA",(1440,936),bg)
    draw = ImageDraw.Draw(sheet)
    ink = (20,20,20,255) if name == "light" else (240,240,240,255)
    for row,direction in enumerate(["left","up","right"]):
        for column,index in enumerate([7,0,1]):
            frame = Image.open(package / f"output/enemy_scout_drone/move_{direction}/f{index:02}.png").convert("RGBA")
            x,y=column*480,row*312
            draw.text((x+6,y+6),f"{direction} F{index:02}",fill=ink)
            sheet.alpha_composite(frame.crop((24,44,104,92)).resize((480,288),Image.Resampling.NEAREST),(x,y+24))
    path = base / f"side_rear_loop_f07_f00_f01_{name}_6x.png"
    sheet.convert("RGB").save(path)
    data["diagnostics_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
(base / "axis-sampling-observation.json").write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps({"constant_axes":12,"colors":{item['direction']+'/'+item['fan']:item['colors_f00_f07'][0] for item in data['axis_samples']}},ensure_ascii=False))
