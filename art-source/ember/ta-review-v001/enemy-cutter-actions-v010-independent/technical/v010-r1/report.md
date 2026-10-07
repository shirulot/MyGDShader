# 切割工蜂 v010-r1 辅助裁切增量复审

结论：**PASS，关闭原 v010 审阅 ROI 的唯一技术 P2。** 本轮独立比较两个固定 ZIP 并复算所有新联系图，未以制作方 claims 代替核验；没有运行 Godot 或生产重建脚本。原动作与来源技术结论及表示限制继承 `../report.md`，原包的裁切事实保留，不回改历史报告。

新 ZIP `enemy_cutter_actions_v010_r1_2026-10-06.zip` SHA `c154a145e56aa10cd6394507350a47dc21ead655915c73e7f74131e146f9f948`，1,448,992 B、142 entries / 141 payload，CRC、重名路径、全部清单字节数 / SHA / 独立解包 SHA 通过。只有清单自身不自列入 manifest。

对旧 ZIP 全条目逐字节比较：无删除，新增 `REVISION_R1.md`、`rebuild_contacts.gd` 与 3 个 QA 登记文件；原条目改动仅 manifest、preview.html、export.gd 及 20 张深浅底 1× / 4× 联系图。正式 30 帧、五 atlas、SpriteFrames、catalog、raw source / import 及 rig、shader、verify、capture、Godot runtime 等 50 个冻结源 / 资源文件逐字节完全相同。旧 60 GPU 双栏图片及 verification / playback 记录也没有改变。

独立读 HTML、export.gd 和 rebuild_contacts.gd：全部观察区域统一为 `Rect(24,32,80,80)`，网页 canvas 为 80×80 / 320×320、禁用图像平滑。全 30 帧逐点检查 ROI 外有效像素 **0**，正式 atlas 对 PNG 全 RGBA 0 差。独立从冻结帧按对应黑 / 白底合成、同 ROI、Nearest 放大，20 张新联系图与独立结果尺寸和全 RGBA 都相同。death f03–f07 的 x30..31 圆锯边缘现在完整纳入。

冷证据明确继承旧 v010，`gpu_rerun=false` 的登记与实际证据边界一致。旧冷回执 SHA 仍为 `cea902fda1ed8037db58852c8d7a47ac3bd62a6d33adf191b73e461d5dad54b9`，与 r1 的继承绑定匹配。旧 51 核心中 49 与 r1 仍同 SHA，差异两项是 export.gd 的联系图 ROI 和 preview.html 的辅助播放器 ROI / 标题；二者的文本 diff 已保存，正式渲染、资源、rig 与 Godot preview runtime 不变。不将旧冷记录表述为 r1 重新冷导入，不为该纯辅助改动重复 GPU。

本轮确认新服务入口为 `6106/cutter-actions-v010-r1/index.html`，保留旧 `cutter-actions-v010` 历史页。新 HTML、catalog、五 atlas 及实际 HTML 引用的十张 4× 联系图，共 17 个 served 文件与新包同 SHA。1× 联系图是固定包载荷，网页只引用 4×，未强求网页服务提供无引用的 1× 文件。

逐条证据见 `evidence.json`，独立脚本为 `verify.py`，两项文本修改为 `text-diff.txt`。本次关闭项限辅助裁切；动作受力、身份、造型和运行表现仍由原独立视觉 / 动作意图及根 TA 决定，未将像素绑定通过当作完整游戏接入通过。
