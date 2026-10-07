# 《余烬采能站》正式素材目录

2026-10-06 建筑最终包：[buildings_final](buildings_final/README.md)。控制塔、维修工坊、物流仓库的完整图、功能层、交互预制体、独立示例、母图与规范已集中在同一目录。

2026-10-06 最新：[十三材质地板v006](environment/reference_floor_v006/README.md)。新增压实沙土、灰色碎石、苔石地坪，原十种编号、砖木周期与共同47型构造保留；附[三种新地图与十三材质混铺对比](environment/reference_floor_v006/gpu_material_comparison_v006.png)及[独立工程ZIP](../../art-source/ember/deliveries/reference_floor_v006_2026-10-06.zip)。F4～F6或方括号选择新表面，新增美术仍待用户评判。

2026-10-06 前一批：[十材质地板v005](environment/reference_floor_v005/README.md)。新增旧沥青、砖红工业铺装、灰褐木栈道，原七种编号与共同47型构造保留。砖块和木板按原稿接缝裁片校准统一周期，支持混铺；附[实际地图对比](environment/reference_floor_v005/gpu_material_comparison_v005.png)及[独立工程ZIP](../../art-source/ember/deliveries/reference_floor_v005_2026-10-06.zip)。新三种用F1～F3或方括号选择，新增视觉仍待用户评判。

2026-10-06 前一批：[七材质地板v004](environment/reference_floor_v004/README.md)。新增浅砂混凝土、青绿旧涂层、磨损灰白地砖，保留原四种表面和共同47型构造；附[三种新地图与七材质混铺对比](environment/reference_floor_v004/gpu_material_comparison_v004.png)及[独立工程ZIP](../../art-source/ember/deliveries/reference_floor_v004_2026-10-06.zip)。编号与旧存档保持兼容，表面变化沿用统一桥头、压顶和立面标准，新增美术仍待用户评判。

2026-10-06 前一批：[多材质地板v003](environment/reference_floor_v003/README.md)。沿用v002构造，新增浅灰控制区、深灰防滑检修区、锈褐旧仓区，四种表面可混铺；附[实际地图对比](environment/reference_floor_v003/gpu_material_comparison_v003.png)及[独立工程ZIP](../../art-source/ember/deliveries/reference_floor_v003_2026-10-06.zip)。材质交界、四向桥口、纯材质增量更新和存档通过独立复验；新表面视觉仍待用户评判。

2026-10-06 本轮新入口：[参考效果地板 v002](environment/reference_floor_v002/README.md) 与[生产标准](../../docs/shader-learning/reference-floor-v002-production.md)。实际生图材质、厚压顶、深立面和二格宽格栅桥已完成可铺刷实拼；27,909格结构复验与GPU动态刷擦通过。打开[独立工程 ZIP](../../art-source/ember/deliveries/reference_floor_v002_2026-10-06.zip)试铺；视觉仍待用户评判。

旧 [pixel_floor_v001](environment/pixel_floor_v001/README.md) 的结构测试通过，但**用户已明确否定其视觉**，保留为技术基线，不再推荐为当前美术成品。487核心结构＋8装饰配置、旧交付文件均属于该历史批次。

以下为历史交付目录与数量；用户本轮重新选择原生像素角色／设备基准，并明确要求重设计地板。后续生产遵循[美术规范 v2](../../docs/shader-learning/art-style-standard-v002.md)与[自动铺刷瓦片规范 v2](../../docs/shader-learning/autotile-production-standard-v002.md)。旧批次“正式／完成”标签不代表新版风格认可。

当前已正式交付 **123/123 个艺术单元，剩余艺术项 0**：瓦片 62、机器人 20 帧、建筑道具 19、UI 15、2D 特效纹理 4、3D 底色／草片 3。另有40个技术输入。机器人行走已完成 **v002 断裂修复**，请使用下方新资源入口。目录含保留的旧版本，共 **122 张生产 PNG、17 份 .tres、5 个独立示例场景**；当前推荐版本对应105 PNG、16份资源、4个示例。图集、版本副本、组件源层和审阅图不增加艺术计数。新修正版已通过 Godot 4.7.2 导入、保存重载、逐帧实际渲染、完整循环及无原缓存新工程复用验证。

| PNG | 内容 | 单元 / 尺寸 |
| --- | --- | --- |
| [ground_details_v001.png](environment/tilesets/ground_details_v001.png) | 地板、两态检修口、六种贴花 | 12 / 256×64 |
| [structures_v001.png](environment/tilesets/structures_v001.png) | 墙体、栏杆、桥面与独立边梁 | 26 / 256×128 |
| [utilities_v001.png](environment/tilesets/utilities_v001.png) | 管线与水渠岸线，不含水面中心 | 24 / 256×96 |

打开 [tileset_layout_sandbox.tscn](../../scenes/ember/tileset_layout_sandbox.tscn)，选择 `LayoutWorkspace` 下的 Ground、Structures、Utilities 或 Details，在 TileMap 面板手动刷块。也可把 [ember_common_tileset_v001.tres](environment/tilesets/ember_common_tileset_v001.tres)指定给自己的 TileMapLayer；三份单包 TileSet 与[坐标／接口目录](environment/tilesets/ember_tiles_catalog_v001.json)位于同目录。

水岸后缀表示水侧；桥边梁要与桥面同格放在独立覆盖层。当前支持手动布局，未配置完整 Terrain 自动连接、碰撞、导航或课程 Shader；具体摆法与方向限制见[交付文档](../../docs/shader-learning/tilemap-reusable-tilesets.md)。

原首批 **6/6 已完成**：四地板包含在上述 62 内，另有 [robot_idle_down_v001.png](characters/robot/robot_idle_down_v001.png)（64×96、脚底 32/80）和 [station_base_v001.png](buildings/station/station_base_v001.png)（128×160、基座 64/144）。C01 **20/20 帧完成**，最新见[断裂修复与复用说明](../../docs/shader-learning/asset-production-robot-repair-v002.md)。将[robot_sprite_frames_v002.tres](characters/robot/robot_sprite_frames_v002.tres)指定给自己的 AnimatedSprite2D，或打开[修正版机器人预览场景](../../scenes/ember/robot_animation_sandbox_v002.tscn)。walk 8 FPS；centered=false、offset=(-32,-80)、Nearest。v002复用4张原待机，替换16张行走与1张图集；v001行走、旧资源和[历史批次报告](../../docs/shader-learning/asset-production-batch-02-robot.md)保留供对照，v001包含已确认的断裂问题，不再推荐使用。R01 的统一2×[比例验收板](../../art-source/ember/references/full_native_scale_v003.png)是旧批次快照；修正版逐帧对照与源标注位于 `art-source/ember/robot-repair-v002/`。原始母稿、完整提示词和整理源保留于 `art-source/ember/`。

来源为项目内 AI 母稿与原生像素整理，不登记为 CC0。记录见[来源台账](../../docs/shader-learning/resources.md)、[独立验收](../../art-source/ember/tilesets-v001/art-review-v001.json)与[Godot 实际验证](../../art-source/ember/tilesets/godot_validation_v001.json)。对象的原生验收见[首批最新结果](../../docs/shader-learning/asset-production-batch-01.md)。新示例与素材未替换现有游戏、旧资源或学习者 Shader。

打开[新素材库场景](../../scenes/ember/asset_library_sandbox.tscn)查看建筑道具、UI 九宫格、特效纹理和 3D 材质。门的两态 SpriteFrames、面板／屏幕 StyleBoxTexture，以及三种 StandardMaterial3D 可直接复用；每项尺寸、锚点、灯窗、发射点和可拆源层见[40项目录](ember_additional_catalog_v001.json)及[完整艺术交付说明](../../docs/shader-learning/asset-production-full-art.md)。

当前合并包：[ember_assets_v005_2026-10-04.zip](../../art-source/ember/deliveries/ember_assets_v005_2026-10-04.zip)，含123艺术单元、40技术输入、机器人v002与来源／验证记录，打开包内工程默认进入修正版机器人示例。v001～v004历史包保持原样。

D01～D12 的 **40/40 技术输入已完成**，含40 PNG、3 CanvasTexture、2带法线的3D材质及[技术输入检查场景](../../scenes/ember/technical_inputs_sandbox.tscn)，本次修复未更改这些输入。v004快照为105生产PNG、16份.tres、4示例；修复后目录总量见本文开头。[使用方法／数据采样／完成范围](../../docs/shader-learning/asset-production-technical-inputs.md)。D13区域Mask实际0张，等你布置实际水面、露天和热区后派生；课程Shader和可选collect动画另行完成。
