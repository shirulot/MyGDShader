# 机器人 v011 阶段 B1：四个新增方向行走

2026-10-06。**新增 NW / N / NE / SE 各八帧，共 32 帧，当前候选待独立 TA 审查。** 加上原字节保留的 S / SW，共六向行走 48 帧。另有八张固定造型参考，不计为最终双帧 idle。最终授权范围仍为八向 idle2 / walk8 / collect4，共 24 段、112 帧。

阶段 A rc02 已通过，回执副本 `qa/ta-receipt-phase-a-rc02.md`。本次保留 S/SW 和八向身份母版原字节。W/E 隐藏部件源图已生成作下一批准备，**没有用于 B1 的 32 张新帧**，两侧行走和全部最终 idle/collect 仍未完成。

## 直接查看

- `walk-review.html`：方向切换、8 FPS / 2 FPS、1× / 4×、深浅底、逐帧与自动换向。W/E 选择行走时明确回落到静态身份参考。
- `previews/walk_<direction>_light_4x_v011.png`：每方向 4×2 八帧联系图；另有 dark / transparent 和 1× 版本。
- `previews/walk_<direction>_<normal|slow>_<1x|4x>_v011.webp` 与 `.gif`：透明无损动画；normal 每圈 1000ms，slow 每圈 4000ms。
- `godot-walk-review/project.godot`：本批独立 Godot 工程。WASD 选向，Tab 切换 pose/walk，空格暂停，暂停后方向键逐帧，B 换底。
- `gpu-walk-playback/transitions/`：实际引擎同一步相换向图。当前支持 S→SW、NW→N、N→NE、SE→S 四组相邻45°切换，每组八步相。缺失 W/E 的两侧组合尚不能验收。

## 固定部件与连接保护

四个新方向分别登记自己的分区和骨点，位于 `build_remaining_walk_v011.cjs`。每方向 11 个固定源片，静态实拼与其已通过身份母版 RGBA 零差；动作源和所有排姿保存在 `source/fixed-rig-pilot/<direction>/`，部件在 `source/fixed-parts/<direction>/`。没有方向镜像，也没有逐帧包围盒缩放或齐底。

膝/踝等局部连接经过对应方向的 imagegen 编辑，原始图和完整 prompt 均保留。`composite_remaining_joints_v011.cjs` 按该方向的骨点变换保护身体、上段甲片、胫部甲片、前臂壳、手/工具、刚性靴和透明轮廓边；补丁只在连接区域生效。原本不透明的关节内芯不会被透明编辑像素擦掉。对比记录和保护图在 `qa/<direction>_joint_patch_v011.json`、`qa/<direction>_rigid_protection_4x.png`。

骨骼来自同一母版，图案来自 imagegen，代码负责裁片、刚性变换、调色板归一化与局部合成。并非直接将整条 AI 动画作为最终源帧。64×96、root(32,80)、11 色、二值 alpha、固定左上光源和解剖学左腕工具保持一致。

## 制作侧验证与边界

`qa/export_validation_walk_batch.json`：56 张审阅 PNG（48 walk + 8 pose）、48 个动图导出通过；S/SW及八向母版与阶段 A 已通过快照字节相同；新帧没有独立 alpha 碎点。透明 GIF/WebP 解码与源 RGBA 完全相同。连通性与掩膜保护只证明资产结构与修改范围。

`qa/godot_walk_batch_v011.json`：真实 GPU 112 个样本（56图×1×/4×）通过，六段行走各自然运行两圈；`qa/godot_walk_transitions_v011.json`：同一 AnimatedSprite2D 的32次相邻方向同相位切换通过。二者绑定本批图集 SHA `6d1bfe2cc93cfd17dfe404ba18db0ae87e8e33db3665b1d5df716a291991e9cc`。

制作侧查看四组八帧联系图、浏览器正常速度浅底、慢放设置深底的离散画面，并暂停逐向核对 F07→F00。截图保存在 `qa/browser/phase_b1_*.png`；这不是连续视频，也不自行推导美术 PASS。

已运行 game-character-sprites 的 `audit_sprite_motion.py`。因脚本只支持正方格，用**不缩放原像素的左右各16px透明补边**构成96×96诊断格，文件 `qa/walk_motion_diagnostic_padded96.png` 只供诊断，不是另一尺寸的游戏素材。脚本无几何/边缘/色键错误，但对 SW、N、SE 发出小步幅/近似帧提示；SW是已通过且未改的基准。提示完整保存在 `qa/skill_motion_audit_walk_batch.json`，N/SE的可读性和投影合理性仍交由 TA 结合播放判断，没有为消除提示擅自修改已通过帧。

主工程未接入，阶段 A 和 v010 冻结包未改。其他新方向的动作通过结论、最终双帧 idle、四帧 collect 及完整112帧包均不能从本批技术检查外推。
