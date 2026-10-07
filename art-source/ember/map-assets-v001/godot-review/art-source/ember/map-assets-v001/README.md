# 三张新地图的素材来源 v001

这份目录保存素材的真实生图来源，供复核和重新注册。三张概念参考是潮汐物流港、干旱采矿站、废弃生态研究站；概念图用于说明视觉和构图，可运行地图由地板瓦片与独立 Sprite2D 重新组装。

当前阶段：30 张生成母稿已保存，27 个素材已完成注册，Sprite、Floor 和三张实际地图 GPU 报告均为技术 PASS。管道母稿已确认具有真实透明背景，无需重新生图。艺术效果仍待用户选择，技术 PASS 不代表用户已接受风格；ZIP 冷启动另由交付检查记录。

目录内容：

- `source_specs_v001.json`：画布、主体尺寸、pivot、地板材质 ID 和来源要求。
- `prompts/`：30 份生成提示词。
- `masters/`：30 张真实 PNG，以及每张对应的 `.generation.json`。
- `generation_manifest_v001.json`：母稿、提示词、generation 记录和参考图的 SHA256；保留内置 imagegen 的原始输出路径和 provenance。
- `godot-review/`：从已验证 v006 包初始化的独立工程，供素材注册与实际地图验证；它不属于母稿，也不能递归复制到自身。

30 张母稿包含 19 个独立对象、1 张八部件管道 sheet、9 张新地板纹理和 1 张岩坑背景。已注册 27 张透明 PNG 与 27 个 `scene_library` 场景：19 个对象加 8 个管段。岩坑是非通行背景，不是新增地板边界或可走区域。

19 个对象覆盖能源站、控制台、水泵、工业门、横墙/纵墙/墙角、蓝灰/灰绿/灰褐货箱、绞盘、矿石箱、输送带、研究设备柜、样本池、工业桶、岩石簇、芦苇簇和浮叶簇。管道包含横/纵直段、四向弯头与横/纵终端；管道与墙均为手摆静态装饰，不是自动补全 Terrain。

地板沿用 13 个稳定 ID。本次新生成 0 steel、3 rust、4 concrete、5 teal、6 ceramic、9 wood、10 sand、11 gravel、12 moss；1 control、2 service、7 asphalt、8 brick 保持旧材质兼容。压顶、立面、桥梁、桥头、栏杆、格栅、板缝和机器人继续使用已有资源。

空间规范为世界格 32、纹理格 128、地板图层 scale 0.25、Nearest、Camera zoom 2。地板纹理注册为 1024×1024 period，保留真实 artist RGBA，通过同一世界相位采样；不改色、不量化成少数色阶、不以程序平色重画。独立 Sprite 的尺寸和 pivot 以规格及注册报告为准，0.25 不作为所有道具的统一缩放。

Floor 与 Bridge 分别使用 47 种原生 Terrain 邻接形式；铺刷/擦除后由联合占用派生 water、facade、floor、rim、bridge、heads 六个可见图层。材质层 `FloorMaterials` 只登记材质 ID，不增加外墙或新的占用边界。南向立面、8world 压顶、默认双格桥可见主体 40world 与两侧 12world 肩部沿用共同结构。

正式结果位于 `assets/ember/map_assets_v001/`，其使用说明与验收报告是操作入口。三张地图场景：

- `res://scenes/ember/map_assets_tidal_port_v001.tscn`
- `res://scenes/ember/map_assets_dry_mine_v001.tscn`
- `res://scenes/ember/map_assets_overgrown_lab_v001.tscn`

实际截图输出为 `assets/ember/map_assets_v001/previews/sprite_library_v001.png`、`floor_library_v001.png`、`gpu_tidal_port_v001.png`、`gpu_dry_mine_v001.png`、`gpu_overgrown_lab_v001.png`。它们由 Godot 实际资源和 TileMapLayer 渲染，不把概念图当作完整场景贴图。截图存在与技术报告 PASS、用户风格接受是分别记录的状态。

当前报告记录：27 个 Sprite 的透明度、画布、pivot、来源像素与场景验证通过；地板完成 156 个材质交界、36 个桥口、21 次增量/全量 RGBA 精确比较及各 9 次撤销/重做。三张地图分别进行 2 次连续 GPU 改刷，每次检查 3 个样点、每图共 6 个样点，最大 RGB8 误差均为 0。完整检查范围和未测试项以正式报告为准。

同步输入使用 `tools/sync_map_assets_review_v001.ps1 -InputsOnly`。默认调用也只复制输入，不覆盖 review 中的成品。最终完整同步与 ZIP 打包应在报告完成后进行；清单中的本机 `raw_path` 是历史来源，运行地图不依赖它。
