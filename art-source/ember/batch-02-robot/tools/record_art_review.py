"""登记已完成的root逐帧审查，绑定20帧哈希；不把测量代替视觉审查。"""
import json
from pathlib import Path

BATCH = Path(__file__).resolve().parents[1]
catalog = json.loads((BATCH / "frames-catalog-v001.json").read_text(encoding="utf-8"))
validation = json.loads((BATCH / "validation-frames-v001.json").read_text(encoding="utf-8"))
report = {
    "date": "2026-10-04", "status": "ROBOT_20_FRAME_VISUAL_REVIEW_PASS",
    "reviewer": "root agent; user final style approval not claimed",
    "scope": "20帧原生/整数2x，4方向contact表，浅/深底轮廓，以及逐帧f03到f00循环端点",
    "frame_sha256": {f["id"]: f["sha256"] for f in catalog["frames"]},
    "viewed": ["pixel-review/all20_neutral_2x.png", "pixel-review/all20_light_1x.png",
               "pixel-review/all20_dark_1x.png"] +
              [f"pixel-review/walk_{d}_contact_2x.png" for d in catalog["directions"]],
    "findings": [
        "同一浅陶瓷装甲/钢灰关节/黄铜左腕工具，四方向轮廓与明暗可读；侧向未镜像换手。",
        "逐部件步态交替，头/胸起伏最多1原生像素；手臂、工具与靴保持连接。",
        "侧视近远靴投影高度不同；抬脚帧最低可见底边78或79，虚拟地面锚点始终(32,80)。",
        "所有方向末帧接首帧回到接触相，头部1px起伏复位；无突然换头、改胸甲或新增肢体。",
        "浅/深底可见轮廓连贯；运行能量/危险状态及投影未烘焙，背视没有伪造前胸窗口。"
    ],
    "source_limits": "19份实际AI母稿只作造型/材料/姿态参考；模型phase和比例漂移按原生rig整理纠正，不称直接逐像素提取。",
    "playback_evidence": "此记录是逐帧和端点视觉审查；实际8FPS播放、帧访问与循环时序另由Godot报告确认。",
    "independent_review": "完整20帧独立审查见validation-frames-v001.json；审查状态以该报告为准。",
    "independent_visual_status": validation.get("independent_visual_review", {}).get("status", "NOT_RECORDED"),
    "automatic_report": "validation-frames-v001.json"
}
(BATCH / "art-review-v001.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print("root 20帧视觉审查及版本绑定已登记")
