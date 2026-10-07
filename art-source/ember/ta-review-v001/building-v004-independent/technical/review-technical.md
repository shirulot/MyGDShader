# 建筑 v004 独立功能与封包审查

结论：**NEEDS_REVISION，2 项局部 P2；无已确认 P1。** 整体造型由根级与视觉审查另行通过。新净口、存档安全和整壳淡出行为通过；正式格式与展示反馈仍需修订，不需要重画建筑。

固定包：building_assets_v004_2026-10-06.zip，SHA256 7d0b44613858a073ecb2696f88e4c4188dc7a58b38aa3d7a6f20279ae6d70ff5，27,605,384 bytes，66 files / 65 manifest payload。

## 已确认问题

### P2-1：v004 演示继续使用旧界面坐标，操作提示和反馈均在窗口外

- 文件：[building_demo_v004.gd](E:/dev/shader/godot-shader/godot-shader-simple/scripts/ember/building_demo_v004.gd:26) 调用继承的 _build_ui；[building_demo_v001.gd](E:/dev/shader/godot-shader/godot-shader-simple/scripts/ember/building_demo_v001.gd:163) 第163–167行。v004独立项目固定窗口1408×800，godot-review/project.godot 第8行。
- 实测 help (28,946,648,55)、toast (28,896,1,27) 与视口没有交集。建筑名称继续按旧位置公式登记在 y945，同样位于窗口外。toast 的初始宽度尚未布局不影响结论：其 y896 已完全超界。
- 复现：打开包内 demo，锁定人门后尝试开门，或保存/恢复。拒绝、故障、防夹与存档反馈由 _show_toast 正常写入，但界面不可见；底部按键说明也不可见。
- 影响：演示接入者无法知道操作为何被拒绝或是否保存成功。这是反馈布局问题，未发现状态机失效。
- 最小建议：在 v004 独立覆盖 _build_ui 或布局函数，以新视口与 PLACEMENTS 登记说明、toast、名称；避免改动旧版本共用坐标。重新截图验证真实拒绝/保存反馈。
- 独立证据：[完整 GPU 画面](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004-independent/technical/cold-project/ta-demo-feedback-layout.png)、[定点结果](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004-independent/technical/cold-project/ta-v004-probe-result.json) 两条 feedback_visible 失败。

### P2-2：正式完整 PNG 仍保留连续实体 Alpha，运行 shader 也未实施二值覆盖

- 标准依据：[art-style-standard-v002.md](E:/dev/shader/godot-shader/godot-shader-simple/docs/shader-learning/art-style-standard-v002.md:76) 规定静态色彩图实体 alpha255、透空 alpha0。v004 整体造型/比例优先规则没有豁免此项；未经整理的母稿可以保留。
- 文件：assets/ember/building_assets_v004/complete 三张正式PNG；其 SHA 与 masters 原稿完全相同。generation_manifest_v004.json 第10/19/28行说明 preserved generated alpha。[building_intact_v004.gdshader](E:/dev/shader/godot-shader/godot-shader-simple/shaders/ember/building_intact_v004.gdshader:53) 第53行采样原纹理，第72行 COLOR = value * tint，没有 hard coverage。

| 正式图 | 0 < Alpha < 255 | Alpha250–254 | 其占连续像素比例 | Alpha1–249 |
|---|---:|---:|---:|---:|
| control_tower | 650939 | 626141 | 96.19% | 24798 |
| repair_workshop | 744442 | 717739 | 96.41% | 26703 |
| logistics_warehouse | 649050 | 621763 | 95.80% | 27287 |

- 此问题是正式实体覆盖格式缺口；没有把低 Alpha 纯彩边计作肉眼可见霓虹，也没有因连续像素数量推断 GPU 出现裂缝。当前 GPU 定点截图未确认新的可见外壳缺陷。
- 最小建议：保留现有 masters 原样，在正式完整图与功能层使用同一已登记覆盖 mask 输出二值 Alpha，保持有效 RGB、结构和单次统一缩放；按新正式图更新组合/闭合 GPU 证据。整壳 modulate.a=0.14 是允许的运行遮挡效果，应与底图覆盖区分。单改 shader 不能修好提供给普通 Sprite2D 的正式 PNG 格式。
- 独立证据：[Alpha 分布与哈希](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004-independent/technical/alpha-format-evidence.json)、[分析脚本](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004-independent/technical/inspect_alpha.py)、[同母稿分层核验](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004-independent/technical/static-integrity-evidence.json)。

## 本轮独立验证

没有运行用户编辑器，没有修改生产脚本或 M0。冷副本仅改变用户存档目录，并新增 TA 探针；固定 ZIP 及生产路径只读。

| 检查 | 独立结果及范围 |
|---|---|
| 固定包完整性 | 65载荷路径/字节数/SHA在ZIP与当前生产源两侧一致；ZIP哈希正确；无额外遗漏载荷。 |
| 同母稿导出 | 3 masters与完整图字节一致；15功能层逐源像素复算，可见RGBA零差、无遗漏/重复可见归属。固定层清空区域的双方Alpha0隐藏RGB差异单独记录，不当作造型差异。 |
| 新登记/预制体 | 3脚印256×128 / 384×128 / 608×224；统一scale/pivot/门净口源坐标与运行登记一致；3静态入口直接载完整图，3交互入口载v004组装器。 |
| 独立冷导入 | Godot4.7.2 Steam，headless editor import exit0、stderr0，日志在本目录。 |
| 四个实际门口 | 24项通过：闭门阻挡、请求开门、完全开门后角色中心及净口两侧通行、相邻墙阻挡。使用实际18×12 CharacterBody2D碰撞，未仅用数据宽度推断。 |
| 锁电/读档/占用 | 16案例×3检查共48通过：存档近/远、读档前相反位置、有电/断电，覆盖全部4门。角色/电源/锁/半开进度正确恢复；真实存档占用安全重开，远处继续关闭；断电保持半开。 |
| 整壳进出 | 三栋分别y18→6→−6→−24→18，共15淡出状态+15 GPU可见性检查通过。门口外侧与同背景强制前景角色基准逐像素零差；内部整壳alpha0.14后角色仍可读；退出恢复1。未复现不透明深暗门洞把角色盖住。 |
| 展示反馈 | 2条失败，为上述同一P2-1。 |

独立运行汇总 **102/104**。Alpha格式问题属于独立静态检查，不计入运行104项。此前使用“无建筑背景”比率作诊断时发现背景对比度差，已以“同背景前景”对照排除假阳性；最终结果只保留准确判定，原比率明确标为 diagnostic_only。

运行证据：[TA probe](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004-independent/technical/cold-project/tools/ta_v004_probe.gd)、[最终 JSON](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004-independent/technical/cold-project/ta-v004-probe-result.json)、probe-independent.log、probe-independent.stderr.log（0 bytes）。15张局部GPU图 cold-project/ta-entry-building-index.png 可逐步核对角色进出。

## 作者证据与范围边界

作者60/60冷工程结果、报告SHA 33e5010917ddcb1b8b267a8feb22c9c54ada459ee2d2043686ac206b3817016f、7张截图哈希已与固定包绑定；其闭合完整图/功能图/固定区域、门状态、服务/灯光/舱盖测试按源码检查过。此处标为“已复核作者证据”，**不冒充本轮独立重跑60项**。作者采集时主动隐藏反馈UI，因此未覆盖P2-1。

本版支持新脚印、4个门口、锁电/故障/防夹/存档、维护与灯光，以及进入建筑整壳统一淡出。深暗门洞没有完整室内资产；未声明楼层/房间高度分区或旧屋顶/前墙独立遮挡，不能继承旧版全部交互范围PASS。本轮没有要求生产者补回未承诺玩法，也没有复跑历史500项。
