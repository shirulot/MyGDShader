# Shader 课程资源计划

2026-10-06 地板继续扩展：[十三材质v006标准](reference-floor-v006-materials.md)与[使用说明](../../assets/ember/environment/reference_floor_v006/README.md)。新增压实沙土、灰色碎石、苔石地坪三份内置imagegen母稿，原十种表面和统一收边保留，扩展干燥作业区／矿区／废弃区域。[实际GPU对比](../../assets/ember/environment/reference_floor_v006/gpu_material_comparison_v006.png)和[独立工程ZIP](../../art-source/ember/deliveries/reference_floor_v006_2026-10-06.zip)提供四场景、来源、完整提示词与铺刷代码。

2026-10-06 地板再扩展：[十材质v005标准](reference-floor-v005-materials.md)与[使用说明](../../assets/ember/environment/reference_floor_v005/README.md)。三份内置imagegen母稿新增旧沥青、砖红工业铺装、灰褐木栈道，原七种材质编号与公共收边不变。砖木按真实母稿接缝裁片注册完整周期，原艺术RGBA保留；附[实际GPU对比](../../assets/ember/environment/reference_floor_v005/gpu_material_comparison_v005.png)、[独立工程ZIP](../../art-source/ember/deliveries/reference_floor_v005_2026-10-06.zip)与全部来源／提示词。

2026-10-06 地板继续扩展：[七材质v004标准](reference-floor-v004-materials.md)与[使用说明](../../assets/ember/environment/reference_floor_v004/README.md)。新增浅砂混凝土、青绿旧涂层、磨损灰白地砖三份实际imagegen母稿，保持原四种编号和公共构造；[实际GPU地图对比](../../assets/ember/environment/reference_floor_v004/gpu_material_comparison_v004.png)展示三张同构地图与七材质混铺。[工程ZIP](../../art-source/ember/deliveries/reference_floor_v004_2026-10-06.zip)含源稿、完整提示词、可铺刷索引、代码和验证记录。

2026-10-06 地板扩展：[多材质v003标准](reference-floor-v003-materials.md)与[使用说明](../../assets/ember/environment/reference_floor_v003/README.md)。三份实际imagegen母稿新增浅灰控制区、深灰防滑检修区、锈褐旧仓区，原蓝灰及公共构造复用v002。四种材质共用47型拓扑和统一尺寸，附三张同构地图及一张混铺示例；[工程ZIP](../../art-source/ember/deliveries/reference_floor_v003_2026-10-06.zip)保留源文件、提示词、代码和验证。12组材质交界、四向桥口、9次增量／完整RGBA一致性以及GPU换材质通过，旧v002默认输出未变。

2026-10-06 本轮：[参考效果地板 v002 生产标准](reference-floor-v002-production.md)、[使用说明](../../assets/ember/environment/reference_floor_v002/README.md)与[独立工程 ZIP](../../art-source/ember/deliveries/reference_floor_v002_2026-10-06.zip)。五份实际生图母稿已整理为两套47型原生Terrain与六个派生context图层，附Godot实际实拼图。27,909格结构复验、局部与完整RGBA一致性及GPU动态刷擦通过；装饰独立摆放，视觉仍待用户评判。

旧 [pixel_floor_v001 地板交付](pixel-floor-v001-delivery.md) 与[历史ZIP](../../art-source/ember/deliveries/pixel_floor_v001_material_v002_2026-10-06.zip) 的Godot结构检查通过，但随后**用户否定视觉差距**，只保留为技术基线。旧10张atlas、7份TileSet、487核心结构＋8装饰、117,851格结构验证均不是当前新包的完成证据。

2026-10-06 新生产规范：[美术 v2](art-style-standard-v002.md)、[自动铺刷瓦片 v2](autotile-production-standard-v002.md)、[可视规范页](art-style-standard-v002.html)。用户认可原生比例板中的角色／设备方向，明确不认可其中地板；新地板重新设计。下方完成数为历史批次记录，不代表本轮视觉认可或已接入主游戏。

2026-10-05 历史 tile 入口：[v007 全项风格统一](autotile-v007-style-unification.md)。旧 67 个手工笔刷 ID 已全部迁移至统一风格资源，另有 236 种自动连接配置；两类数量重叠，不重复计入艺术预算。包含新检修口、贴花、阀门和地板变体，已提供可操作笔刷页。技术检查通过，视觉状态为候选。

2026-10-05 后续铺刷修复：[v006 重绘候选版](autotile-v006-review.md)，110 个配置采用新地板/墙体/栈桥图，另 126 个复用 v005；两版失败池岸稿已排除。已验证实际 Godot 铺刷和端口连通性，尚待用户视觉认可。下方资源交付数为历史快照，不因重绘重复累计。

2026-10-05 当前入口：[裂图修复与新角色交付](seam-repair-and-rivet-2026-10-05.md)。v005 修复透明截面、颜色跳变、内部重复外框与预览跨图块采样；新角色「铆钉」单独交付四向待机/移动 SpriteFrames 和可操作预览。两项均保留旧资源，不改变主游戏入口；新角色 20 个源帧中 19 个进入预览，错误工具换边帧已排除。

当前自动铺设素材另见 [v003 官方模板订正交付](autotile-v003-delivery.md)：保存新的 imagegen 美术母稿及 13 个采样记录，整理为 330 个图块配置和 7 个 Terrain 资源。该批为 T01～T06 的衍生/替换版本，不与下方历史 123 项原始美术预算重复相加。v002 保留；v003 尚待用户视觉确认。完整 47 型面积模板与四邻接 16 型路径规则已写入 [规范](art-generation-standard.md)。

2026-10-04 综合复核：当前生产预算 123 艺术单元与 40 技术输入已交付；当前文件测量和逐章缺项见[素材审核与全课程补充清单](asset-curriculum-review-2026-10-04.md)。后续按布局准备 D13 区域、按需补桥方向及运行时拆层，并在 C14～16 准备 3D 几何；这些建议不自动改写原清单完成数或课程进度。

本文定义课程需要的最小资源集合、获取策略和许可证台账。资源随当前实验需要逐步准备，不批量下载或生成。

2026-10-03：用户要求彻底替换原有美术，按[全新美术与生图标准](art-generation-standard.md)从零生产。新标准覆盖人物、场景、建筑、任务交互、特效输入及 C14～16 的 3D 预留；详细数量与批次见[生产清单](asset-generation-manifest.csv)。首批已实际生成机器人朝下待机、采能站、四种地板，共 **6/123 个艺术单元的候选母稿，正式合格 0/123**；Alpha 修正稿与诊断图不增加艺术计数。生产与差距见[首批生产报告](asset-production-batch-01.md)。下方旧文件与许可记录保留为历史事实，不作为新素材造型、尺寸或兼容约束；本轮没有替换现有场景引用。

2026-10-04：新增的三套可复用 TileMapLayer 瓦片集已交付：3 张原生 atlas 共 12＋26＋24＝62 个地形艺术单元，采用原 T01～T08 预算。已完成 16 色、二值 Alpha、轮廓与接口整理、代理视觉审查以及 Godot 4.7.2 实际导入／保存重载／渲染；正式文件见[通用瓦片集交付](tilemap-reusable-tilesets.md)。制作跨 10 月 3～4 日，11 份母稿、12 次调用保留为历史。原首批四地板已包含在 62 内；机器人朝下待机一帧与采能站也已原生整理通过，合计 **64/123 正式艺术单元，剩余 59 未完成，原首批 6/6 完成**。C01 仅 1/20 帧，不额外制作其余角色帧或预算项。

2026-10-04 后续批次：C01 机器人四向 **20/20 帧及 8 组 SpriteFrames 动画已完成**；本批 19 次实际 imagegen 调用、19 份母稿及原生整理记录见[机器人动画报告](asset-production-batch-02-robot.md)和[生成记录](../../art-source/ember/batch-02-robot/generation-record.json)。来源为 `AI_MATERIAL_AND_POSE_REFERENCE_WITH_NATIVE_PIXEL_FINISH`，不登记为 CC0。原朝下待机 SHA 不变；当前全套 **83/123，剩余 40**。上方 64/123 是瓦片批次完成时的历史快照。

2026-10-04 完整艺术批次：新增建筑道具 18、UI 15、特效／3D 纹理 7，合计全套 **123/123 艺术项完成**；此前 6、64 和 83 的数量是分批历史快照。40 份实际 imagegen 母稿逐项保留提示词、原始输出路径和 SHA256，并经原生整理、交叉视审与 Godot 新工程复用检查。来源使用方式包含材料／结构参考和明确登记的原生重建，不登记为 CC0。目录与来源证明见[完整艺术交付说明](asset-production-full-art.md)。D01～D13 技术输入、可选动作与课程 Shader 仍按实验需要准备。

2026-10-04 技术输入批次：按用户持续授权补齐 **D01～D12 共40/40输入**，由项目程序及已确认底图几何派生，来源为 `GENERATED_IN_PROJECT` / `DERIVED_FROM_REGISTERED_BASE_GEOMETRY`。40 PNG、5资源、1独立检查场景已完成导入逐像素、真实移动灯、跨组审阅及无缓存复用验证；[技术交付说明](asset-production-technical-inputs.md)登记脚本、通道、参数和限制。上方‘D01～D13另行准备’是完整艺术批次快照；当前D13实际0张，仍待真实布局。资源准备不推进课程状态。

## 资源原则

### 后续游戏用料与独立练习分流（2026-10-06）

用户明确后续游戏使用新生成的像素机器人与地板，不要求所有 Shader 练习强制换料；随后允许教师在适合的练习中试用一些新素材。后续游戏搭建/效果接入采用 `assets/ember/` 自制像素美术，不再默认拿旧 Kenney 或 512 测试角色作正式游戏角色；已完成实验和 M0 原引用保留，在下一次独立游戏教学中逐步接入，不现在自动换图、改场景或重构。独立练习按概念选材，当前已启动 C04 的 Test Sprite、D02/D03 起点不为此自动替换。

- 机器人默认入口：`assets/ember/characters/robot/robot_sprite_frames_v003.tres`，图集 `robot_animations_v003.png`，目录 `robot_frames_catalog_v003.json`；40 姿态/12 动画，64×96、脚底 (32,80)，来源复用已确认 idle v001/walk v002 并由原部件制作微动/采集动作，不改标 CC0。说明见 [v003 动作交付](asset-production-robot-actions-v003.md)。预览中的采集锁移动/重播不自动成为游戏规则。「铆钉」是另一份可运行候选，不自动取代当前机器人。
- 地板当前入口：[reference_floor_v006 使用说明](../../assets/ember/environment/reference_floor_v006/README.md)与 [v006 标准](reference-floor-v006-materials.md)。复用已生成表面及 v002 公共构造，保持 128 纹理格／32 世界格／0.25 层缩放和自动铺设契约；材质按任务需要选用，不新增生图。地板方向认可不等于十三种材质/所有细节逐项最终通过，旧失败稿不作为默认基准。
- 游戏接入需核对实际角色动画与锚点、地板层缩放、Alpha、材质参数和自然重开；素材本身的生产验收不能代替可玩应用验收。地板 v006 依赖 v002 公共构造及 v003～v005 表面，按 catalog 和使用说明复用，不仅复制一张 atlas。
- 练习选材由教师决定：角色颜色/局部效果、描边/溶解可试用新机器人的独立 RGBA 帧，避免为了换美术额外引入图集 UV；地面采样/流动/扭曲可按需要用新地板。UV 校准、通道与数值对照继续保留 UV Grid、ColorRect、测试角色、Mask、Noise；不强制换料、不删内容、不为换图打断已开始实验。本轮没有实际替换练习资源。

每个 Section 只引入完成当前视觉实验所需的资源。能程序生成的测试资源不依赖外部素材；需要真实素材时，优先选择 CC0 或明确允许免费商用的许可。

资源按以下优先级准备：

1. 使用 Godot 节点、Shader 或小型生成脚本产生测试图。
2. 复用项目中已经登记许可的资源。
3. 查找 CC0 或免费商用资源，并记录原始页面。
4. 为教学实验生成专用资源，并标记生成方式。

## 建议目录

首次需要资源时再创建对应目录。不要提前填充空目录或大量素材。

```text
assets/shader-learning/
├─ common/          # 跨章节复用的测试图
├─ 2d/              # 2D Sprite、Mask、Noise、Normal Map
├─ screen/          # 屏幕效果测试场景素材
├─ 3d/              # 基础 Mesh、纹理和 3D 测试材质
└─ licenses/        # 外部资源许可副本或说明
```

## 共用基础资源

这些资源服务于多个章节，但仍按首次使用时间准备。

| 资源 | 形式 | 首次使用 | 准备方式 | 用途 |
| --- | --- | --- | --- | --- |
| UV Grid | 512×512 PNG | 01 | 程序生成 | 检查方向、缩放和扭曲 |
| Color Test | 色块与灰阶 PNG | 01 | 程序生成 | 颜色和混合实验；Alpha 验证使用 Test Sprite |
| Checkerboard | 512×512 PNG | 02 | 程序生成 | 观察 UV 重复和边界 |
| Gradient | 灰度与彩色 PNG | 04 | 程序生成 | 阈值、Mask 和 Ramp |
| Circle Mask | 灰度 PNG | 04 | 程序生成 | Mask 组合与柔边 |
| Noise Set | 平滑、颗粒各一张 | 05 | Godot NoiseTexture2D 或程序生成 | 溶解和扭曲 |
| Test Sprite | 带透明轮廓的角色或图标 | 01 | 先生成；必要时找 CC0 | 闪白、描边、溶解和受击反馈 |
| Test Background | 有直线和色块的背景 | 06 | 程序生成 | 水波、热浪和屏幕畸变 |
| 2D Normal Map | 与 Test Sprite 或砖墙匹配 | 13 | 生成或找 CC0 | 2D 灯光实验 |
| Basic 3D Set | Plane、Cube、Sphere、简单角色代理 | 14 | Godot PrimitiveMesh | 3D 材质与空间实验 |

## 各章专用资源

表中“无”表示只使用共用资源和 Godot 内建节点。

| Chapter | 专用资源 | 来源策略 | 当前动作 |
| --- | --- | --- | --- |
| 01 | 透明 Test Sprite | 程序或 AI 生成简单图标 | 开章时生成一张 |
| 02 | 非方形校准图 | UV Grid、Checkerboard；02.3 用派生非方形图检查宽高比 | C02 已复用旧 UV Grid 与 D01 非方格图；不用重复生成 |
| 03 | 无 | 使用 ColorRect、Gradient 和内建 `TIME` | 不准备 |
| 04 | 既有 D02 灰度渐变、D03 圆/星 Mask | 复用已登记的项目生成数据 | 04.1 用渐变/圆，04.3 再用星形；不重复生成 |
| 05 | 既有 D04 低频/高频 Noise；NoiseTexture2D 内建资源 | 优先复用项目生成数据，仍学习内建资源 | 05.1 先观察已有两图，再按小步连接最小 NoiseTexture2D；不重复生成 PNG |
| 06 | 既有直线背景、低频 Noise/圆 Mask、非方形校准/色块 | 复用已登记项目生成输入 | 四实验已实际使用；本章未用机器人或 C05 内建 Noise，无新 PNG |
| 07 | 既有 D05 Alpha 校准 Sprite；可选独立机器人帧 | 复用项目生成与已登记角色 | 07.1 优先 128×128 Alpha 图，孔洞/细线/渐变齐全，不重复生成 |
| 08 | 环形 Gradient、能量纹理 | 程序生成 | 按 Section 分别生成 |
| 09 | 一个统一主题的 Sprite 与背景 | 从已生成资源中组合 | 不新增大素材包 |
| 10 | 最小交互场景 | Godot 节点搭建 | 章节 Chat 创建 |
| 11 | 角色、HP 和攻击触发代理 | 简单几何或自制占位图 | 章节 Chat 创建 |
| 12 | 可滚动的综合测试场景 | 复用前章效果和背景 | 不下载新素材 |
| 13 | 2D Normal Map、Light Occluder 轮廓 | 生成或 CC0 | 使用前核验许可 |
| 14 | 球、立方体和 Plane | PrimitiveMesh | 无外部资源 |
| 15 | 草片 Mesh、低模角色代理 | 自建 PrimitiveMesh；必要时 CC0 | 到章时决定 |
| 16 | 水面 Plane、护盾 Sphere、简单角色 | 复用 14～15 | 不新增大素材包 |

## 可程序生成的资源

以下资源优先由短小、可复现的工具生成。生成脚本不是教学 Shader 答案，可以由 AI 协助完成。

- UV Grid、Checkerboard、颜色测试图和渐变图。
- 圆、环、星形、条带和软边 Mask。
- Value Noise、Cellular 风格测试纹理和蓝噪声替代测试图。
- 扫描线、像素格、CRT 网格和色差对齐标记。
- 环形冲击波 Ramp、溶解边缘 Ramp 和能量条纹。
- 2D 高度图转 Normal Map 的测试资源。

程序生成资源在许可证台账中将来源记为 `GENERATED_IN_PROJECT`，并记录生成脚本路径和参数。

## 需要寻找或生成的资源

只有当占位图不能验证目标时，才引入真实美术资源。

- 带透明细节的 2D 角色：用于检验描边、受击和溶解在真实 Alpha 边缘上的表现。
- 像素风 Sprite：用于检验像素化、采样过滤和像素描边。
- 可平铺环境纹理及 Normal Map：用于 2D 灯光与水面测试。
- 简单低模角色：用于 3D 受击、溶解和全息效果。

查找时必须从资源原始页面确认许可。搜索摘要、转载页或文件名不能作为许可依据。

## 许可证台账

每个外部资源占一行。未知许可的资源不得进入课程主线。

同一许可覆盖的原样整包允许按包登记；包内保留原文件名与目录，便于追溯。

| 资源 ID | 文件路径 | 作者/生成者 | 原始来源 | 许可 | 许可证据 | 修改 | 使用章节 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `kenney-rts-scifi-full` | `assets/vendor/kenney/rts-scifi/` | Kenney | 本地 All-in-1 3.7.0 / 2D assets / RTS Sci-fi，完整来源见下文 | CC0 1.0 | `assets/vendor/kenney/rts-scifi/License.txt` | 无；264 文件逐一 SHA256 校验一致 | 用户指定的完整素材库，按实验需要选用 |
| `uv-grid-512` | `assets/shader-learning/common/uv_grid_512.png` | 项目内生成脚本 | `tools/generate_chapter01_assets.ps1` | `GENERATED_IN_PROJECT` | 生成脚本；首次生成日期 2026-09-19；512×512，无参数 | 无 | 01.1，后续 UV 实验可复用 |
| `color-test-512` | `assets/shader-learning/common/color_test_512.png` | 项目内生成脚本 | `tools/generate_chapter01_assets.ps1` | `GENERATED_IN_PROJECT` | 生成脚本；首次生成日期 2026-09-20；512×512，无参数 | 无 | 01.2 颜色与灰度实验 |
| `test-sprite-robot-512` | `assets/shader-learning/2d/test_sprite_robot_512.png` | 项目内生成脚本 | `tools/generate_test_sprite.ps1` | `GENERATED_IN_PROJECT` | 生成脚本；生成日期 2026-09-25；512×512 RGBA，无参数 | 无 | 01.2 Alpha 验证；01.3 可复用 |
| `kenney-scifi-player` | `assets/shader-learning/2d/kenney-rts-scifi/player_scifi_unit_03.png` | Kenney | 本地 RTS Sci-fi / PNG/Retina/Unit/scifiUnit_03.png，完整来源见下文 | CC0 1.0 | 同目录 License.txt | 仅改文件名，像素未改 | 01.2、01.3；小游戏角色候选 |
| `kenney-scifi-station` | `assets/shader-learning/2d/kenney-rts-scifi/station_scifi_structure_01.png` | Kenney | 本地 RTS Sci-fi / PNG/Retina/Structure/scifiStructure_01.png | CC0 1.0 | 同目录 License.txt | 仅改文件名，像素未改 | 后续 Mask、站点状态实验备用 |
| `kenney-scifi-ground` | `assets/shader-learning/2d/kenney-rts-scifi/ground_scifi_tile_05.png` | Kenney | 本地 RTS Sci-fi / PNG/Retina/Tile/scifiTile_05.png | CC0 1.0 | 同目录 License.txt | 仅改文件名，像素未改 | 后续 UV 和场地实验备用 |

许可证据可以是原始页面链接、随资源附带的许可证文件，或生成工具与生成日期。若许可要求署名，将署名文本同时记录在 `assets/shader-learning/licenses/`。

## 新美术来源台账：首批候选

本批使用内置 `image_gen.imagegen`，生成日期为 2026-10-03（Asia/Irkutsk）。来源登记为 `AI_GENERATED_IN_PROJECT`，不登记为 CC0。完整源文件、工具输出路径、参考版本、调用次数和调整记录见[生成记录](../../art-source/ember/batch-01/generation-record.json)；每次提示词均完整存档。母稿原样归档，母稿阶段没有像素调整；后续正式整理另行登记。

| 资源 ID | 原始生成稿 | 完整提示词 | 新参考版本 | 修改与状态 |
| --- | --- | --- | --- | --- |
| `ember-robot-idle-down-master-v001` | [robot_idle_down_master_v001.png](../../art-source/ember/batch-01/generated/robot_idle_down_master_v001.png) | [机器人 v001 提示词](../../art-source/ember/batch-01/prompts/01_robot_idle_down_v001.txt) | 无外部参考 | 候选；C01 仅 1/20 帧，待像素整理 |
| `ember-robot-idle-down-master-v002` | [robot_idle_down_master_v002.png](../../art-source/ember/batch-01/generated/robot_idle_down_master_v002.png) | [Alpha 修正提示词](../../art-source/ember/batch-01/prompts/02_robot_alpha_cleanup_v002.txt) | 机器人 v001 | 模型修正未达到 0/255 Alpha；备用，不计新增单元 |
| `ember-station-master-v001` | [station_master_v001.png](../../art-source/ember/batch-01/generated/station_master_v001.png) | [采能站提示词](../../art-source/ember/batch-01/prompts/03_station_base_v001.txt) | 机器人 v001 | 候选；B01 1/1，待像素整理 |
| `ember-floor-clean-master-v001` | [floor_clean_master_v001.png](../../art-source/ember/batch-01/generated/floor_clean_master_v001.png) | [干净地板提示词](../../art-source/ember/batch-01/prompts/04_floor_clean_v001.txt) | 机器人 v001、站点 v001 | 候选；待 32×32 调色与接缝整理 |
| `ember-floor-worn-master-v001` | [floor_worn_master_v001.png](../../art-source/ember/batch-01/generated/floor_worn_master_v001.png) | [磨损地板提示词](../../art-source/ember/batch-01/prompts/05_floor_worn_v001.txt) | 干净地板 v001、站点 v001 | 候选；待 32×32 调色与接缝整理 |
| `ember-floor-grate-master-v001` | [floor_grate_master_v001.png](../../art-source/ember/batch-01/generated/floor_grate_master_v001.png) | [格栅地板提示词](../../art-source/ember/batch-01/prompts/06_floor_grate_v001.txt) | 干净地板 v001、站点 v001 | 候选；待 32×32 调色与接缝整理 |
| `ember-floor-wet-master-v001` | [floor_wet_master_v001.png](../../art-source/ember/batch-01/generated/floor_wet_master_v001.png) | [潮湿地板提示词](../../art-source/ember/batch-01/prompts/07_floor_wet_v001.txt) | 干净地板 v001、站点 v001 | 候选；待 32×32 调色与接缝整理 |

T01 四种地板母稿共 4/4 候选。高分辨率母稿、目标网格诊断图和整数预览分开保存；诊断文件由 Nearest 粗采样与组合派生，没有进行调色板量化、Alpha 阈值处理、裁切、重定位或接缝修正。它们留在 `art-source/ember/`，不进入正式目录。

| 派生记录 | 来源 | 路径与用途 | 验收状态 |
| --- | --- | --- | --- |
| 目标网格与整数 2 倍预览 | 六张 v001 母稿 | `art-source/ember/batch-01/diagnostics/native-grid/`、`integer-2x/`；逐项链接见[生产报告](asset-production-batch-01.md#可见成果与诊断文件) | 仅诊断；不计正式艺术单元 |
| 四张 3×3 平铺图、全类型邻接图 | 四块目标网格地板诊断图 | `art-source/ember/batch-01/diagnostics/tiling_*_3x3_4x.png`、`all_floor_adjacencies_v001.png` | 人工初评已记录，角交叉与阴影连接待修；不登记无缝合格 |
| R01 比例与风格诊断图 | 本批机器人、站点、四种地板 | [batch01_style_scale_diagnostic_v001.png](../../art-source/ember/references/batch01_style_scale_diagnostic_v001.png)，1536×1024；未包含门素材 | `DIAGNOSTIC_BOARD_CREATED_NEEDS_REVIEW`；参考不计艺术单元 |
| 自动测量记录 | 母稿与目标网格诊断 PNG | [母稿报告](../../art-source/ember/batch-01/validation-masters.json)、[诊断报告](../../art-source/ember/batch-01/validation-native-probes.json)、[只读脚本](../../art-source/ember/batch-01/tools/validate_assets.py) | 自动检测不能代替造型、像素尺度、锚点与接缝人工验收 |

正式目录状态见 [assets/ember/README.md](../../assets/ember/README.md)。首批母稿阶段没有正式生产 PNG；本轮地板已整理并纳入下面的正式瓦片集。旧素材、现有场景、游戏逻辑和学习者 Shader 没有因新素材交付而替换。

## 新美术来源台账：首批原生对象

2026-10-04 从已有新母稿进行 `AI_SUBJECT_SAMPLING_AND_NATIVE_PIXEL_FINISH`，没有新增 imagegen 调用；原始母稿 SHA256 与生成记录一致，不登记为 CC0。只交付 C01 朝下待机一帧和 B01 静态底图，不代表全部角色动画、建筑分层、Mask 或 Normal 已完成。

| 资源 ID | 正式文件 | 原始新来源 / 整理证据 | 实际状态 |
| --- | --- | --- | --- |
| `ember-robot-idle-down-native-v001` | [robot_idle_down_v001.png](../../assets/ember/characters/robot/robot_idle_down_v001.png)，64×96 | 机器人母稿 v001；高 Alpha 主体取样、原生轮廓／窗口／脚底整理；[整理记录](../../art-source/ember/batch-01/pixel-finish-v001/finishing-record.json) | C01 仅 1/20 帧完成；bbox [12,21,52,80)，锚点 (32,80)，11 标准色，0/255 Alpha |
| `ember-station-base-native-v001` | [station_base_v001.png](../../assets/ember/buildings/station/station_base_v001.png)，128×160 | 站点母稿 v001；高 Alpha 主体取样、原生窗口／轮廓／基座边界整理；同上记录 | B01 1/1 完成；bbox [17,26,111,144)，锚点 (64,144)，11 标准色，四周至少 16 像素留边 |
| R01 部分原生比例验证 | [batch01_native_scale_v002.png](../../art-source/ember/references/batch01_native_scale_v002.png)，1024×832 | 上述两对象与四块已完成地板；同一整数 4 倍比例 | 参考不计艺术单元；只覆盖机器人／站点／地板，缺门与控制台，不登记完整 R01 |

[独立只读对象报告](../../art-source/ember/batch-01/pixel-finish-v001/validation-objects-independent.json)确认两图半透明 0、板外色 0、固定底边界与原母稿未改变；制作与独立代理已查看对象／比例图。原首批报告头部记录当前 6/6，其下保留 2026-10-03 母稿阶段 0/123 的历史，二者不混用。

## 新美术来源台账：可复用瓦片集母稿历史

本轮来源为 `AI_GENERATED_IN_PROJECT`，不登记为 CC0；工具为内置 `image_gen.imagegen`，制作期为 2026-10-03～2026-10-04（Asia/Irkutsk）。[生成记录](../../art-source/ember/tilesets-v001/generation-record.json)保存 12 次调用、11 份成功母稿与一次桥面网络失败后成功重试的事实。完整提示词逐份归档，母稿归档时像素调整为无；下表为母稿阶段状态。后续整理已完成，来源与实际调整见正式图集台账。

| 资源 ID | 原始生成稿 | 完整提示词 | 母稿归档时来源关系与状态 |
| --- | --- | --- | --- |
| `ember-wall-module-master-v001` | [wall_module_master_v001.png](../../art-source/ember/tilesets-v001/generated/wall_module_master_v001.png) | [01 墙体](../../art-source/ember/tilesets-v001/prompts/01_wall_module_master_v001.txt) | T02 材料参考；13 连接片尚未制作 |
| `ember-railing-module-master-v001` | [railing_module_master_v001.png](../../art-source/ember/tilesets-v001/generated/railing_module_master_v001.png) | [02 栏杆](../../art-source/ember/tilesets-v001/prompts/02_railing_module_master_v001.txt) | T03 材料参考；8 连接片尚未制作 |
| `ember-pipe-module-master-v001` | [pipe_module_master_v001.png](../../art-source/ember/tilesets-v001/generated/pipe_module_master_v001.png) | [03 管线](../../art-source/ember/tilesets-v001/prompts/03_pipe_module_master_v001.txt) | T04 材料参考；12 连接片尚未制作 |
| `ember-channel-module-master-v001` | [channel_module_master_v001.png](../../art-source/ember/tilesets-v001/generated/channel_module_master_v001.png) | [04 水岸](../../art-source/ember/tilesets-v001/prompts/04_channel_bank_master_v001.txt) | T05 材料参考；12 岸线片尚未制作，不含水面中心 |
| `ember-bridge-module-master-v001` | [bridge_module_master_v001.png](../../art-source/ember/tilesets-v001/generated/bridge_module_master_v001.png) | [05 桥面](../../art-source/ember/tilesets-v001/prompts/05_bridge_deck_master_v001.txt) | T06 材料参考；网络重试成功；绘制棋盘格背景需清理；5 连接片尚未验收 |
| `ember-hatch-closed-master-v001` | [hatch_closed_module_master_v001.png](../../art-source/ember/tilesets-v001/generated/hatch_closed_module_master_v001.png) | [06 检修口关闭](../../art-source/ember/tilesets-v001/prompts/06_hatch_closed_master_v001.txt) | T07 关闭态候选，未校正固定安装框 |
| `ember-hatch-open-master-v001` | [hatch_open_module_master_v001.png](../../art-source/ember/tilesets-v001/generated/hatch_open_module_master_v001.png) | [07 检修口开启](../../art-source/ember/tilesets-v001/prompts/07_hatch_open_master_v001.txt) | T07 开启态候选，与关闭态共计 2/2 母稿候选 |
| `ember-cable-loop-master-v001` | [cable_loop_module_master_v001.png](../../art-source/ember/tilesets-v001/generated/cable_loop_module_master_v001.png) | [08 电缆圈](../../art-source/ember/tilesets-v001/prompts/08_cable_loop_master_v001.txt) | T08 实际贴花候选之一 |
| `ember-crack-module-master-v001` | [crack_module_master_v001.png](../../art-source/ember/tilesets-v001/generated/crack_module_master_v001.png) | [09 裂痕初稿](../../art-source/ember/tilesets-v001/prompts/09_crack_decal_master_v001.txt) | 生成了整块面板，未选作独立贴花；保留原稿 |
| `ember-debris-master-v001` | [debris_module_master_v001.png](../../art-source/ember/tilesets-v001/generated/debris_module_master_v001.png) | [10 碎屑](../../art-source/ember/tilesets-v001/prompts/10_debris_decal_master_v001.txt) | T08 实际贴花候选之一 |
| `ember-crack-decal-master-v002` | [crack_decal_master_v002.png](../../art-source/ember/tilesets-v001/generated/crack_decal_master_v002.png) | [11 裂痕提取](../../art-source/ember/tilesets-v001/prompts/11_crack_extraction_master_v002.txt) | 使用裂痕 v001 作模型编辑参考；视觉提取已成功，32×32 整理待验收；不增加同一裂痕单元数 |

母稿归档时 T08 只有裂痕 v002、电缆圈、碎屑 3/6 候选。随后按母稿设计语汇重绘锈迹、油迹、螺栓，六种正式贴花已完成；这三种不增加生图调用数。T01 从原四种新地板母稿整理，不增加重复地板单元。母稿和粗采样诊断文件继续保存，诊断图不冒充正式 PNG。

[planned-catalog-v001.json](../../art-source/ember/tilesets-v001/planned-catalog-v001.json)是历史规划；正式 [ember_tiles_catalog_v001.json](../../assets/ember/environment/tilesets/ember_tiles_catalog_v001.json)登记实际 62 个 ID／坐标／变体／接口与水侧。用户在提出脚本像素整理方案后回复“继续”，已按该方案完成原生调色、Alpha／轮廓／接口整理，没有额外的等待审批。

## 新美术来源台账：正式原生瓦片集

正式成果来源为 `AI_MATERIAL_REFERENCE_AND_NATIVE_PIXEL_FINISH`，不登记为 CC0。原始生成稿、11 份完整提示词、参考关系、日期和脚本调整均保留；[pixel-finish-record.json](../../art-source/ember/tilesets-v001/pixel-finish-record.json)区分取样整理与设计参考重绘。裂痕、锈迹、螺栓、油迹和开启态内区不称直接像素提取。

| 资源 ID | 正式文件与数量 | 新来源 / 整理记录 | 实际状态 |
| --- | --- | --- | --- |
| `ember-ground-details-v001` | [ground_details_v001.png](../../assets/ember/environment/tilesets/ground_details_v001.png)，256×64，12 个 32×32 单元 | 原四地板、两态检修口、裂痕／电缆／碎屑新母稿与参考派生贴花；[地面整理脚本](../../art-source/ember/tilesets-v001/tools/finish_ground_details.py) | 4 地板＋2 检修口＋6 贴花；共框与类型平铺审查通过 |
| `ember-structures-v001` | [structures_v001.png](../../assets/ember/environment/tilesets/structures_v001.png)，256×128，26 单元 | 墙／栏杆／桥新母稿；[结构整理脚本](../../art-source/ember/tilesets-v001/tools/finish_structures.py) | 13 墙＋8 栏杆＋5 桥；桥母稿棋盘底未进入正式图，边梁是独立叠层 |
| `ember-utilities-v001` | [utilities_v001.png](../../assets/ember/environment/tilesets/utilities_v001.png)，256×96，24 单元 | 管线／水岸新母稿；[设施整理脚本](../../art-source/ember/tilesets-v001/tools/finish_utilities.py) | 12 管线＋12 水岸；接口包含水侧，不含水面中心 |

[原生自动报告](../../art-source/ember/tilesets-v001/validation-native-atlases.json)记录 62/62、规则失败 0、556 个最终有向接口与未匹配 0。独立验收确认正式 PNG 与原生 atlas 哈希一致；[视觉报告](../../art-source/ember/tilesets-v001/art-review-v001.json)保留旧 628 到新 556 的过滤原因、实际逐页范围与明暗 RGB 差异，不宣称全部 RGBA 相同或完整 Terrain 自动拼接。

已实际生成 3 张生产 PNG、3 份独立 TileSet、1 份共享 TileSet 与 [四层可编辑场景](../../scenes/ember/tileset_layout_sandbox.tscn)。[Godot 4.7.2 验证报告](../../art-source/ember/tilesets/godot_validation_v001.json)记录导入、构建、重载和真实渲染退出 0，Lossless、无 mipmaps、共享资源与 62 画笔正常，场景未因只读核验／截图而改写。29 个旧项目原文件哈希保持一致；碰撞、导航、Terrain 和课程 Shader 尚不由这组资源设置。


## C03 / 03.1 实际使用记录（2026-10-05）

据 [03.1 检查点报告](chapter03-section01-checkpoint-report.md)与最新保存场景登记，仅更新使用事实，不新增素材或改变生产预算：

| 文件 | 本节使用 | 来源边界 |
| --- | --- | --- |
| `assets/shader-learning/common/uv_grid_512.png` | 最终时间移动场景，512×512 | `GENERATED_IN_PROJECT`，`tools/generate_chapter01_assets.ps1` |
| `assets/shader-learning/2d/test_sprite_robot_512.png` | 初始呼吸场景准备，最终已替换；512×512 RGBA | `GENERATED_IN_PROJECT`，`tools/generate_test_sprite.ps1` |
| `assets/shader-learning/2d/kenney-rts-scifi/player_scifi_unit_03.png` | 中途呼吸实验，128×128 RGBA；不是最终引用 | Kenney RTS Sci-fi，CC0，旧许可记录仍有效 |
| `assets/ember/characters/robot/robot_animations_v002.png` | 最终呼吸场景 AnimatedSprite2D，320×384 图集，朝上行 5 个 64×96 裁片 | `AI_MATERIAL_AND_POSE_REFERENCE_WITH_NATIVE_PIXEL_FINISH`，v002 原生 rig/标注修复，不是 CC0；证据见 [v002 修复说明](asset-production-robot-repair-v002.md)、[动画批次](asset-production-batch-02-robot.md)与 `assets/ember/characters/robot/robot_frames_catalog_v002.json` |

采集脉冲已复用 M0 当前 Kenney 站点 PNG 与已有实例材质，不自动换成新美术。实验运行确认来自学习者；素材交付证明不替代课程或游戏应用验收。

## C03 整章使用与 C04 最小资源（2026-10-06）

03.2 使用 ColorRect，不需素材；03.3 已复用下表 D02，256×1 的渐变在场景显示为 512×512，最终形状用程序 UV、纹理仅用于默认采样与 Alpha，不登记为已经学习纹理 Mask。下表资源均已存在，C04 按节使用，不新增下载/生成，不更换主游戏美术；不改变上方艺术/技术生产预算。

| 资源 | 使用节与读取注意 | 来源与证据 |
| --- | --- | --- |
| `assets/shader-learning/2d/test_sprite_robot_512.png`，512×512 RGBA | 04.1 局部闪白底图；保留原 Alpha。使用完整纹理避免额外引入图集 UV | `GENERATED_IN_PROJECT`；`tools/generate_test_sprite.ps1` |
| `assets/ember/data/ramps/grayscale_gradient_v001.png`，256×1 RGB | 04.1 黑/灰/白权重对照；RGB 从左至右 0→1，Alpha 全不透明，数据读取 `.r` | D02、`GENERATED_IN_PROJECT`；`art-source/ember/technical-inputs-v001/basic/generate_basic.py` 与技术输入 catalog |
| `assets/ember/data/masks/circle_mask_v001.png`，256×256 灰度 | 04.1 圆形局部选择；读取灰度/R，不用不透明的 Alpha 充当黑白区域 | D03、`GENERATED_IN_PROJECT`；同上脚本与 `assets/ember/data/technical_inputs_catalog_v001.json` |
| `assets/ember/data/masks/star_mask_v001.png`，256×256 灰度 | 04.3 与圆/条带做交并差；先预测再观察，04.1 不提前展开组合 | D03、`GENERATED_IN_PROJECT`；同上脚本与 catalog |

灰度 Mask 是线性权重数据，不将其 sampler 标为颜色用 `source_color`；教师检查现有导入/采样连接即可。04.2 用 ColorRect 生成圆形范围，不必另做贴图或 GDScript。资源路径已核验；教材与实际教学状态见 [C04 交接](chapter04-chat-prompt.md)和 [progress.md](progress.md)。

2026-10-06 C04 使用核对：04.1 已使用完整 Test Sprite、D02 渐变与 D03 圆图；04.2 用 ColorRect（含蓝色透明参照），没有新纹理；04.3 用既有圆/星 Mask，最终程序距离圆×星形×移动扫描。新增纹理为无，来源仍为项目生成，不变更艺术生产计数或游戏引用；游戏应用仍未验收，见 [C04 完成报告](chapter04-completion-report.md)。

## C05 最小资源与实际使用（启动2026-10-06；结课2026-10-07）

启动时已核对现有D04文件与catalog哈希；2026-10-07依据 [C05报告](chapter05-completion-report.md)、实际Shader/场景订正使用状态：两PNG用于观察，已实际建立Godot内建Noise并使用独立机器人溶解。没有新PNG/下载/生图，不改变123艺术项与40技术输入计数；课程核心通过、实际游戏应用仍待验。

| 资源 | 按节用途与读取 | 来源 / 边界 |
| --- | --- | --- |
| `assets/ember/data/noise/noise_low_v001.png`，256×256 L | 05.1 首个灰度观察；后续对照尺度、05.2/05.3 按效果选择 | D04、`GENERATED_IN_PROJECT`；种子240410、周期频段1～4 |
| `assets/ember/data/noise/noise_high_v001.png`，256×256 L | 05.1 后续细碎变化对照，不与首步同时堆叠概念 | 同上；种子240411、周期频段10～24 |
| Godot 内建 `NoiseTexture2D` / `FastNoiseLite` 资源 | 已用于05.1与05.2/05.3；观察器外部资源与溶解内嵌资源分别保存 | `scenes/chapter05/ch05_01_builtin_noise.tres`及`ch05_02_noise_dissolve.tscn`内嵌；256×256、seed7，frequency分别0.08/0.02，无分形、无mipmap；已有PNG没有替代内建教学 |
| `assets/ember/characters/robot/robot_idle_down_v001.png`，64×96 RGBA | 已用于05.2/05.3合并成品，Sprite2D整数4倍显示，避免图集UV | AI 母稿经原生整理，不是CC0；当前v003组合仍复用此待机帧，见机器人catalog与首批报告 |

两张PNG的生成器为 `art-source/ember/technical-inputs-v001/basic/generate_basic.py`，证据为 `assets/ember/data/technical_inputs_catalog_v001.json`。它们是周期频率叠加灰度测试数据，不冒称FastNoiseLite/Perlin；本章另有真实FastNoiseLite内建资源，来源不要混淆。Noise线性读`.r`，无`source_color`；观察器seamless且Repeat开启，溶解Noise不重复。05.2/05.3最终成品在05.2文件，正边宽为灰度跨度、RGB柔和混色，原Alpha保留；05.3单独文件仅起点。Ramp/双色挑战未做且非核心阻塞，未新增GDScript。课程和真实游戏应用分别登记，不宣称GPU性能测量。

## C06 最小资源与实际使用（2026-10-07）

依据 [C06 报告](chapter06-completion-report.md)及保存的四实验更新实际使用，不再只是启动计划。06.1/06.2 用 `assets/ember/data/calibration/straight_background_v001.png`（512×512 RGB、D01）；06.2 实际用 D04 `assets/ember/data/noise/noise_low_v001.png`（256×256 单通道）与 D03 `assets/ember/data/masks/circle_mask_v001.png`（256×256 单通道），不是 C05 内建 Noise。06.3 像素化用 `assets/ember/data/calibration/non_square_grid_v001.png`（512×256 RGB），RGB 色散用 `assets/shader-learning/common/color_test_512.png`（512×512 RGBA、当前全不透明）。本章未用独立机器人帧/地板、未新增 PNG/下载/生图/课程 GDScript，艺术与技术输入生产计数不变。

技术校准/Noise/Mask 来源 `GENERATED_IN_PROJECT`，沿用 technical-input catalog / 已登记生成脚本；Color Test 来源 `tools/generate_chapter01_assets.ps1`。颜色底图读完整 RGBA，Noise/Mask 读 `.r`；色散保留原点 Alpha 的代码已核对，但全不透明色块不能证明透明机器人视觉。前两节实际 Linear，像素化/色散 Nearest；按当前实验解释，不机械套用 catalog 通用备注。四实验核心完成，真实游戏水渠/热浪/终端应用仍待验收，不以素材交付替代。

## C07 最小资源计划（2026-10-07）

用于 [C07 交接](chapter07-chat-prompt.md)。已核对文件、catalog 尺寸与 D05 哈希；此处登记准备齐全，不冒充课程作品/应用完成。

| 输入 | 本章用途与边界 | 来源 |
| --- | --- | --- |
| `assets/ember/data/calibration/alpha_edge_test_v001.png`，128×128 RGBA | 07.1 首步 Alpha 读数，再邻域/孔洞/细线；有透明椭圆孔洞、孤立单像素线与 Alpha 渐变。先 1 源像素描边；边距不是任意宽光晕保证。读 `.a`，不读通用数据备注的 `.r` | D05，`GENERATED_IN_PROJECT`；`art-source/ember/technical-inputs-v001/basic/generate_basic.py`；technical-input catalog 中 `alpha_edge_test` |
| `assets/ember/characters/robot/robot_idle_down_v001.png`，64×96 RGBA | 适合时验证真实非方形轮廓与假发光；先独立 Sprite2D 帧，不引入 AtlasUV/动画 | AI 母稿经原生整理，不是 CC0；当前 v003 组合仍复用此已登记待机帧 |

D05 1 源纹理像素为每轴 1/128 UV（0.0078125）；Sprite scale=4 且无其他变换时为 4 场景单位，实际屏幕像素另受视口/窗口缩放影响。机器人每轴单位分别 1/64、1/96 UV，不混称显示距离。可用现有节点做背景，首步不用 Noise、地板、额外美术或 GDScript；不重新生成 D05、不改旧实验/M0。07.2 保留两层假柔光与成本观察，07.3 保留三种参数化强调，不因像素风选材删标准。

## 资源验收

### 历史临时素材选型：Kenney RTS Sci-fi

已实际查看 RTS Sci-fi、Robot Pack 的预览，以及 RTS Sci-fi 的 Sample 与选定单图。选择 RTS Sci-fi 的原因是俯视单位、工业装置和地面具备一致的轮廓、阴影与配色；Robot Pack 更偏正面/侧面机器人展示，场地配套不如前者直接。角色选用蓝白色科幻单位作为机器人/维修员临时代理，不宣称素材原设定就是机器人；此选型不改变游戏机制。

原始包路径：`E:\download\game read\Kenney Game Assets All-in-1 3.7.0\2D assets\RTS Sci-fi`。随包 License.txt 标题为 RTS Sci-fi (1.0)，作者 Kenney，明确 CC0，允许个人、教学和商业项目使用，署名非强制。以该随包文件为许可依据。首次精选三张 PNG 与一份许可；随后按用户明确要求将完整 RTS Sci-fi 包原样引入 `assets/vendor/kenney/rts-scifi/`，共264个文件、1,374,913字节（约1.31 MiB），逐文件SHA256与来源一致。

整包包含 `PNG/Default size`、`PNG/Retina`、`Spritesheet`、`Tilesheet`、`Vector`、`Preview.png`、`Sample.png` 和 `License.txt`。日常场景优先从 PNG 子目录取单图；图集和矢量源文件保留备用，不因整包可用而一次添加所有资源到场景。旧精选目录继续有效，避免改变现有引用。

三张图片均为 Retina 版 128×128，复制后已核对 SHA256 一致。角色含 14916 个全透明像素、202 个半透明像素；站点含 10957 个全透明像素、142 个半透明像素。两者适合保留 Alpha 的灰度、闪白和描边实验。地面完全不透明，适合背景/UV 实验，不作为透明轮廓验收素材。

当前 01.2/01.3 优先使用 `player_scifi_unit_03.png`。角色在画布内占比较小，教学中可适度放大 Sprite2D 并观察；不要误以为 128×128 都是角色有效细节，也不要靠放大纹理制造不存在的细节。原 512×512 机器人与 Color Test 保留用于高分辨率透明度和色彩对照。地面是棕色地表加浅色道路，不是最终工业室内地板；后续 Shader 程序地面仍按课程学习。

本次仅准备素材与许可，没有修改学习者 Shader、现有场景、主场景配置或自动替换 Texture。素材可以服务游戏，也可以仅用于独立实验，课程内容不受其风格约束。

### 通用检查

资源加入课程前必须通过以下检查。

- 尺寸、色彩空间、Alpha 和导入设置适合当前实验。
- 图案能清晰暴露 UV、边界、采样或颜色问题。
- 外部资源已有可追溯许可。
- 文件名包含用途，不使用 `test1.png` 之类的模糊名称。
- 资源只解决当前章节需要，没有附带无关素材包。
