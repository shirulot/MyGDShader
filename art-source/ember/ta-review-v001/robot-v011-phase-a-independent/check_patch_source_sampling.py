"""补丁母板整体采样诊断，独立Pillow Nearest/色板量化，避免逐帧裁盒校准。"""
from pathlib import Path
from PIL import Image
import json
OUT=Path(__file__).resolve().parent
P=OUT/"package"
palette=[tuple(bytes.fromhex(c)) for c in ["101820","182631","2B3E4B","4D6470","829BA3","BECBC4","566B78","ECE9D8","7B4D35","B77C4B","E2B77A"]]
source=Image.open(P/"source/walk_down_left_joint_edit_raw_v011.png").convert("RGBA")
sample=source.resize((256,192),Image.Resampling.NEAREST)
expected=bytearray()
for pixel in sample.get_flattened_data():
    if pixel[3]<160: expected.extend((0,0,0,0))
    else:
        rgb=min(palette,key=lambda color:sum((color[i]-pixel[i])**2 for i in range(3)))
        expected.extend((*rgb,255))
actual=Image.open(P/"source/walk_down_left_joint_edit_quantized_v011.png").convert("RGBA").tobytes()
different=sum(expected[i:i+4]!=actual[i:i+4] for i in range(0,len(actual),4))
result={"scope":"independent source sheet one-time whole transform; no per-frame bbox fit",
    "source_size":list(source.size),"target_size":[256,192],"method":"Pillow Nearest, Alpha160 threshold, declared 11-color RGB squared-distance",
    "quantized_sheet_full_rgba_different_pixels":different,
    "status":"SOURCE_SHEET_SAMPLING_ZERO_DIFF" if different==0 else "DIAGNOSTIC_LIBRARY_SAMPLING_DIFFERENCE_NOT_AUTOMATIC_ART_BUG"}
(OUT/"patch-source-sampling.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(result,ensure_ascii=False))
