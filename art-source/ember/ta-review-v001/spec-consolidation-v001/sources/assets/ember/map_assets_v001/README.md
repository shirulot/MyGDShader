# 可铺刷地图与独立素材 v001

素材用于重建潮汐物流港、干旱采矿站和废弃生态研究站。地图使用实际 Floor / Bridge 瓦片与独立 Sprite2D 素材，概念参考图用于美术方向。27 个素材注册、地板独立验收及三图 GPU 验收均已技术 PASS；管道母稿确认透明，无需重新生图。艺术效果仍待用户选择，完整验收范围以目录内报告为准。

本轮包括 19 个独立对象、8 个管道部件、9 种新地板 period 和 1 张岩坑背景。已输出 `buildings/`、`props/` 下共 27 张透明 PNG，以及 `scene_library/` 下同名的 27 个可实例化场景。墙段、墙角、管道是静态手摆部件，未包含自动管网/墙体 Terrain、碰撞、动画、导航或完整玩法。

打开以下场景运行并铺刷：

| 场景 | 结构与默认地板笔刷 |
| --- | --- |
| `res://scenes/ember/map_assets_tidal_port_v001.tscn` | 分层指状码头、桥与东侧设备平台；steel，ID 0 |
| `res://scenes/ember/map_assets_dry_mine_v001.tscn` | 围岩坑的工作场与跨坑桥；sand，ID 10 |
| `res://scenes/ember/map_assets_overgrown_lab_v001.tscn` | 实验工作区、水渠、中央庭院与连接桥；moss，ID 12 |

运行操作：1 地板，2 双格桥，3 单格桥；左键刷、右键擦；`[` / `]` 循环材质；Ctrl+Z/Y 撤销/重做，Ctrl+S/L 保存/载入。每张图分别保存到 `user://map_assets_<map_id>_layout_v001.json`。运行时存档不改写包内原始场景。

| ID | 材质 | 快捷键 | 来源 |
| --- | --- | --- | --- |
| 0 | 蓝灰钢板 steel | 4 | 本轮新生图 |
| 1 | 浅灰控制区 control | 5 | 沿用旧材质 |
| 2 | 深灰检修区 service | 6 | 沿用旧材质 |
| 3 | 锈褐钢板 rust | 7 | 本轮新生图 |
| 4 | 浅砂混凝土 concrete | 8 | 本轮新生图 |
| 5 | 青绿旧涂层 teal | 9 | 本轮新生图 |
| 6 | 灰白地砖 ceramic | 0 | 本轮新生图 |
| 7 | 旧沥青 asphalt | F1 | 沿用旧材质 |
| 8 | 砖红铺装 brick | F2 | 沿用旧材质 |
| 9 | 灰褐木栈道 wood | F3 | 本轮新生图 |
| 10 | 压实沙土 sand | F4 | 本轮新生图 |
| 11 | 灰色碎石 gravel | F5 | 本轮新生图 |
| 12 | 苔石地坪 moss | F6 | 本轮新生图 |

世界格 32、纹理格 128、地板图层 scale 0.25、Nearest、Camera zoom 2。`floors/catalog.json` 记录 13 个材质的实际 period 与 SHA。Floor / Bridge 原生 Terrain 各有 47 种邻接形式；helper 根据二者联合占用编译六个可见层：water、facade、floor、rim、bridge、heads。材质交界不会产生外轮廓墙，桥口共享压顶与立面接口。结构采用南向立面、8world 压顶、默认桥体 40world 与 12world 肩部。

编辑器中通过隐藏的 `Floor` / `Bridge` 输入层刷 Terrain，通过 `FloorMaterials` 普通图块层选择材质 ID；后者不参加 Terrain 候选。实际可见 context 图层由 helper 派生。矿站中作为背景绘制的沙土与岩坑不表示 Floor 占用；沙土材质本身也可铺在可走地板上。植物不作为新地板边界。

手摆复用时，将 `scene_library/<id>.tscn` 拖入自己的场景。注册场景已经设置 Nearest、透明画布与 pivot；立起对象以接地底座为锚点，浮叶和管段以规格中的平面锚点为准。纹理层 0.25 的规则针对地板；道具显示大小应保留实际示例场景的比例。管道锚点以注册 metadata 为准；本轮不提供端口坐标或自动接口，不执行自动连管。

实际资源预览位于 `previews/`：

- `sprite_library_v001.png`：27 个注册素材的实渲染陈列。
- `floor_library_v001.png`：9 种新地板；catalog 兼容 13 个材质 ID。
- `gpu_tidal_port_v001.png`、`gpu_dry_mine_v001.png`、`gpu_overgrown_lab_v001.png`：三张实际拼装地图。

检查 `sprite_registration_v001.json`、`sprite_validation_v001.json`、`floors/independent_validation_v001.json`、`floors/gpu_capture_v001.json` 和 `map_placements_v001.json` 的最终状态。技术 PASS 对应报告列出的尺寸、RGBA、铺刷、存档及 GPU 检查；艺术接受另记，不由结构验收推断。

已通过的独立验收包括 156 个材质交界、36 个桥口、21 次增量/全量六层 RGBA 精确比较、9 次撤销与 9 次重做，以及 JSON/场景重载、原生输入采纳和同尺寸 bounds 原点移动。三张 GPU 地图各连续改刷 2 次，每次检查 3 个样点、每图共 6 个样点，最大 RGB8 误差为 0。完整数据、检测尺度和未测试项见报告；ZIP 冷启动另有交付检查。

来源见 `art-source/ember/map-assets-v001/source_specs_v001.json`、`generation_manifest_v001.json`、`masters/` 和 `prompts/`。30 张母稿保留内置 imagegen 原始 provenance；注册仅作裁切、Nearest 缩放、画布和锚点整理，不重新绘画或改色。独立 ZIP 会包含旧基线依赖；原项目旧文件保持原样。
