# 建筑 v002 独立来源、封包与交付结构增量审核

结论：**SOURCE / ARCHIVE / COMPOSITION / DELIVERY STRUCTURE PASS（本报告范围）**。v001 缺完整整栋主资源的交付问题在本次已关闭：三栋都有透明完整 PNG、固定壳、单 Sprite 静态预制体及功能合层交互预制体。没有发现原造型来源替换、额外缩放、未登记 RGB 修改或组合损失。最终美术、GPU 实际显示、交互和 load_state 结论由另外两位独立审查完成。

## 固定包和来源继承

只从 `art-source/ember/deliveries/building_assets_v002_2026-10-06.zip` 解压至本报告旁 `package/` 审查，生产素材及脚本只读。ZIP SHA256 为 `18fe88a25dc19aaaf7cdae43505ff3eb04c060b5358daf8171fcc300c4832f35`，72303483 bytes；279 文件条目、278 manifest 载荷，唯一不列载荷的是清单自身 `portable_file_manifest_v002.json`。无重复路径，CRC、278 项大小/SHA、解压后 SHA 全通过；无 `.import` 或 `.godot` 缓存载荷。

catalog SHA256 `9a89de864acdcccaf98e3ed6cefab71a89d1edbb9145ae3ebc1cb32b587ed8c1` 与送审值相同。catalog→旧 source catalog、旧 runtime、组合工具三个内容绑定均与实际文件匹配。

与 v001 固定 ZIP 精确比较，131 个共有文件字节相同；仅 portable README、portable 根 project.godot 和 TA 规范快照变化，分别对应新版入口/说明及后续验收要求。28 个接受母稿、2 个明确拒收母稿、30 份提示词、47 个生产拆件、来源规格/注册/生成清单和 3 张用户参考均继承旧包内容。旧 runtime 亦字节相同；没有新一轮 imagegen 来源。v001 已独立通过的源到拆件注册范围可继承，v002 的组合像素另行独立复算。

旧 v001 ZIP 仍存在且 SHA256 为 `5870774d53e2010158523021661cf30a560386fe2826c39a66845d8e7e45dbc1`，没有覆写。

## 从原注册独立复算

没有调用生产 composer 或 validator。独立 Python 从 v001 catalog 的画布、pivot、安装点、门净口读取几何，按实际 v001 runtime 的 group 顺序、局部 rank 稳定排序、门 region 和旋转轴规则重新构建源成员，再合并相邻同功能绘制，得到与 v002 完全相同的 41 层 recipe。不是仅按 v002 自报 source_members 重贴后宣布通过。

| 建筑 | 共同 canvas / pivot | 功能层 | complete_closed RGBA差 | fixed_shell RGBA差 |
|---|---|---:|---:|---:|
| 控制塔 | 192×352 / (96,328) | 11 | 0 | 0 |
| 维修工坊 | 256×256 / (128,232) | 15 | 0 | 0 |
| 物流仓库 | 320×288 / (160,264) | 15 | 0 | 0 |

全部 41 层源成员 ID、源 SHA、源 ROI、整数目标位置、顺序、group/kind、可见裁框、共同 canvas/pivot 与独立重建一致，逐像素 RGBA 差总数 0；实际文件 SHA 与 catalog 绑定均通过。全部可见源像素都在目标画布内，没有依 bbox 重裁整体或轴向伸缩。叶轮真实中心、门 ID、灯设备 ID 等额外登记也匹配原安装。

三栋 complete_closed 和 fixed_shell 共 6 图、41 层均为 Alpha0/255，部分 Alpha 总数0。固定壳只含静态构件；闭合整图还含默认门片、盖板、玻璃、叶轮及默认状态灯面。完整图的状态灯色来自已登记白色数据 Mask 的默认调制（ready / active），不是重新涂改美术 RGB；功能层保留原 RGBA。独立复算明确包含该默认灯色规则，因此完整图差0的结论不是遗漏了灯层。

## 完整图与 prefab 定义一致性

三份 `*_static.tscn` 均只有一个 Sprite2D 节点，绑定对应 complete_closed.png，nearest、centered=false，offset 恰为本栋负 pivot，没有缩放或旋转。三份交互 `.tscn` 均绑定 `building_asset_v002.gd` 和正确 building_id；v002 runtime 使用新 catalog/render_layers，继承原 `_sprite` 的共同 pivot，门片按净口 region、叶轮按原安装中心处理。

运行时使用上述 11/15/15 功能层，与整图闭合配方一致，不继续逐柱梁加载旧 47 件。静态、玻璃与活动部件的合层边界有实际功能/绘制顺序依据：遮挡 group 不跨合，门、检修盖、叶轮、状态灯保留独立。多个静态 batch 是被活动/玻璃绘制隔开的排序需要。

完整 PNG、fixed_shell 和功能合层均明确登记为不同使用入口。README 指明 fixed_shell 不得与已含同像素的静态功能层重复显示；旧 47 拆件和 28 母稿只作辅助来源，未被误称为整栋主交付。文件数量本身不作完成度依据。

此处核的是 prefab 定义、来源几何和像素一致性，没有启动 Godot，也不把静态定义核验写成实际 GPU/碰撞/存读档通过。

## 受保护资源与参考边界

相对既有 `ui-v003-integrity/integrity-v003.json` 的历史时间点，以下 5 个当前工作区文件 SHA 均相同：主工程 `project.godot`、`scenes/m0/energy_station.gd`、`scenes/m0/ui.gd`、`scenes/m0/ember_harvest.gd`、`scenes/ember/map_assets_tidal_port_v001.tscn`。portable 包根 project.godot 是新版审阅入口，与主工程根配置分别看待。

包内复用的 `assets/ember/characters/robot/robot_idle_down_v001.png` 和 `assets/ember/map_assets_v001/floors/floor_steel_period_v001.png` 同时与 v001 包及当前工作区字节一致。此证明限定于这两个明确文件，相对 v001 固定包，不扩展为所有历史 robot/floor 资源未改。

3 张用户选定参考既与 v001 包相同，也与当前工作区相同，完整 SHA 见证据。无需重新判断用户选定造型；组合后的比例与风格接受程度仍由独立视觉审查给出。

## 证据

`integrity-evidence.json` 保存逐载荷哈希、来源继承、41 层坐标/recipe/像素、3栋完整图及prefab字段和保护资源结果。`independent_<建筑ID>_complete_closed.png`、`independent_<建筑ID>_fixed_shell.png` 是独立原坐标复装结果。

复验：在工程根运行 `python -X utf8 art-source/ember/ta-review-v001/building-v002-independent/integrity/verify_integrity.py`，只更新本审查目录的诊断产物。本次没有发现本范围新增阻断，不把封包或像素通过代替最终美术与运行审核。
