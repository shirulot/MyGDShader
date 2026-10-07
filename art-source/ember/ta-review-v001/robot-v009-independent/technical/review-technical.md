# 机器人 v009 独立技术增量审查

结论：**技术 PASS；v008 全 RGBA 冷导入 P2 已关闭，无新增技术阻塞。** 仅验朝下行走八帧、64×96、8 FPS、root `(32,80)` 与资源/引擎保真；脚部可见形态、承重与步态由主审另行评价，不以 IK/owner/hash 代替美术通过。

固定 ZIP SHA256 `1abc164e76abc5e7f59978ae0d3062d07b37bd6edfe55c69335ec3f61318c60f`，157 文件、778425 bytes。Rig SHA `2a08e84f86bd3611afad19b1573ff12a844615e2d987aa8053c5a1e3cbb343f3`；atlas SHA `50669508acd565455c8b0834a4f90c1d93ec5a1ff2a2721da3e4f5ca1d9c51e3`。仅向此 technical 目录解包/输出；未编辑生产、原提交或主工程，未操作用户已有 Godot。

## 来源、复用与实质修改

`package-source-report.json` 共 **373 项全部通过**：157 个 ZIP payload 与生产提交目录逐文件一致；12 个 run-manifest evidence 哈希绑定；rig/八份 pose/渲染与播放报告引用的实际源绑定；八 PNG 64×96 二值 Alpha；512×96 atlas 八整格与各 PNG 全 RGBA 相同。

直接从冻结 v008 ZIP 比较：23 部件 PNG 逐字节相同；17 个 cap 定义、关键点、实际骨长定义、相机投影完全相同；source masks 与37像素重归属账本仅版本/路径标识变化；固定 canonical PNG 与 v008 逐字节相同。Rig JSON 对版本标识规范化后无结构差异。23中性源层独立读像素，无重叠、重组完整 1492 原始实体像素和母稿 RGBA；不是只接受生产方的复用布尔字段。

`renderer-version-normalized.diff` 已人工读审：实质变化为独立脚跟/脚尖 pivot 和 pitch → 从鞋求 ankle → 两骨腿 IK；body/lift 曲线读取 `source/foot_motion_v009.json`，新增 heel/toe/contact 诊断。既有上身/手臂驱动、源绘制/固定套嵌、UV采样和投影方式未改。Foot曲线范围 -4°..3°、最大 lift0.8、body lower0.8；可见足形是否合适不据这些参数判定。

## v008 导入 P2 关闭

本包确实携带 `godot-review/assets/robot_walk_down_atlas_v009.png.import`，参数为 lossless、mipmap=false、fix_alpha_border=false、premult_alpha=false。独立冷解包后首次 `--headless --editor --import` 退出0、stderr空，首次导入后的参数仍为false。

在 RTX4070 Laptop、Godot4.7.2 Steam 的真实 Compatibility GPU 中运行包内原 `verify_fixed_rig_playback_v009.gd`，退出0、stderr空：**8个实际导入区域全 RGBA 一致；16个1×/4×GPU全像素一致；自然 AnimatedSprite2D 顺序连续、遍历0..7、完成两轮。** 包内 verifier 与冻结 v008 原 verifier 仅版本/路径替换，未放宽比较契约或跳过全透明RGB。

自然信号序列 `0…7,0…7,0,1`，首次事件91ms、其余间隔均125ms。循环未用 stop() 重置伪造；root/整格注册保持 `(32,80)`。源帧、图集、SpriteFrames与rig在复验后哈希绑定仍有效。

## 保护与边界

87个正式文件直接对原冻结baseline再次核验无改变；本版生产保护表的expected集合也与原87项相同，未替换baseline掩盖变化。v008八张源帧仍与其固定包逐字节相同，v008 ZIP SHA仍 `ac74a58d6ac1751556751046571d5d983a9dcc4f9f85a146b4494706b055ff1b`。

1492 原RGBA的完全忠实仍指中性源层原坐标重组；fixed canonical 是沿用v008的rig派生候选，不能声称与原母稿逐像素相同。脚跟/脚尖物理pivot、鞋底中心和登记实体取样是不同概念；README已注明，当前技术 PASS 不声称脚底与地图碰撞或主玩法速度同步，也不扩大到其它朝向。

## 直接证据

- `technical-summary.json`：冻结哈希、范围、复验数量、完成后保护结果。
- `package-source-report.json` / `verify_package_source.py`：373项独立包/原RGBA/复用核验。
- `renderer-version-normalized.diff`：对冻结v008渲染器的实质差异。
- `cold-playback-report.json`：实际导入八格、16GPU与自然播放事件；原运行报告也在 `cold-workspace/art-source/ember/robot-fixed-rig-v009/fixed_rig_playback_v009.json`。
- `cold-import.*.log`、`playback-rerun.*.log`：独立进程日志，stderr均空。
- 真实复截 PNG 在 `cold-workspace/art-source/ember/robot-fixed-rig-v009/gpu-playback/`，只读生产源、未重新渲染候选源帧。
