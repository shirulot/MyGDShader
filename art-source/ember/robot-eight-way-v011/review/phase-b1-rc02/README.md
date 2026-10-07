# 机器人 v011 阶段 B1 rc02：三向摆臂返修

2026-10-07。**新增 NW / N / NE / SE 各八帧，共 32 帧，当前候选待独立 TA 审查。** 加上原字节保留的 S / SW，共六向行走 48 帧。另有八张固定造型参考，不计为最终双帧 idle。最终授权范围仍为八向 idle2 / walk8 / collect4，共 24 段、112 帧。

阶段 A rc02 已通过，回执副本 `qa/ta-receipt-phase-a-rc02.md`。B1 rc01 因 NE/SE 同侧手脚同向被撤回，正式回执 `qa/ta-receipt-phase-b1-rc01.md` 为 NEEDS_REVISION。rc02 仅调整 N/NE/SE 共24帧；S/SW/NW的24行走帧与八向身份母版原字节保持。W/E 隐藏部件源图已生成作下一批准备，**没有用于 B1 的 32 张新帧**，两侧行走和全部最终 idle/collect 仍未完成。

## 本次返修

NE/SE 的摆臂角按右向投影反转，使同侧手臂与腿交错。N 使用纵向手腕目标和定长双骨求肘位，避免继续套用横向摆动。身体、腿和靴的变换保持 rc01。仅在旧/新手臂覆盖范围及肩肘连接处重新合成，范围外实际像素差为0；刚性甲片、前臂工具和末端仍受保护。

NE母图坐标(22,59)的一枚原色腕部像素曾被错分到body，反相后会留在原位置成为孤点。本次将其归回 `arm_left_lower`，RGBA原值不变，静态实拼仍零差。局部修订掩膜明确包含该像素的旧身体位置与新前臂位置。此归属修复在生成肩肘补丁后发现；当时实际送入imagegen的三张原始输入单独保存在 `source/arm_edit_inputs_b1_rc02/`，未用后来重建的NE输入图冒充生成参考。

`qa/arm_phase_revision_evidence.md` 给出八帧肩/肘/腕与髋/膝/踝坐标、修前后与骨点示意；相应JSON绑定24帧、掩膜、32个原样保留文件。F00/F04的同侧腕/踝沿方向投影在三向均异号。脚的屏幕Y包含抬脚，不把这种高度变化误当作地面步相。原生像素帧和实际播放仍是美术复审依据。

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

`qa/godot_walk_batch_v011.json`：针对rc02重新执行真实 GPU 112 个样本（56图×1×/4×），六段行走各自然运行两圈，全部通过；`qa/godot_walk_transitions_v011.json`：同一 AnimatedSprite2D 的32次相邻方向同相位切换重新执行通过。二者绑定本批图集 SHA `137196518cba1eabfcb8b58579a33fe493ad6865ed8304426f98414ff6a42f01`。

制作侧查看三向修前后联系图、浏览器正常速度浅底、慢放设置深底的离散画面，并暂停逐向核对 F07→F00。rc02截图保存在 `qa/browser/phase_b1_rc02_*.png`；旧rc01截图仅作历史对照。这不是连续视频，也不自行推导美术 PASS。

已运行 game-character-sprites 的 `audit_sprite_motion.py`。因脚本只支持正方格，用**不缩放原像素的左右各16px透明补边**构成96×96诊断格，文件 `qa/walk_motion_diagnostic_padded96.png` 只供诊断，不是另一尺寸的游戏素材。脚本无几何/边缘/色键错误，但对 SW、N、SE 发出小步幅/近似帧提示；SW是已通过且未改的基准。提示完整保存在 `qa/skill_motion_audit_walk_batch.json`，N/SE的可读性和投影合理性仍交由 TA 结合播放判断，没有为消除提示擅自修改已通过帧。

主工程未接入，阶段 A 和 v010 冻结包未改。其他新方向的动作通过结论、最终双帧 idle、四帧 collect 及完整112帧包均不能从本批技术检查外推。
