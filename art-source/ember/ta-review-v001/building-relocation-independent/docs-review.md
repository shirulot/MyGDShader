# 建筑集中目录：文档迁移增量审查

结论：**PASS_DOCS_RELOCATION**。现行 `assets/ember/buildings_final/docs/ember-building-standard-v002.md` 与已过规范快照仅Markdown链接目标变化，正文、数字、规则和验收范围无扩张；当前README、四份生产说明及当前review索引的直接链接有效。没有需要修改现行规范正文的具体问题。

固定对照：

- 已审核原文 `assets/ember/buildings_final/review/consolidation/ember-building-standard-v002-reviewed.md` SHA-256：`ac27621a08fc9ac568188ad66ff99613d520a1ed8bdfe9e4329bffe40ddde9c8`。
- 当前规范 SHA-256：`5d3861adf4be17d82ec691771ca1600272f21ee5a142ee011ad65271c5559e5c`。
- 逐字对照仅21个Markdown链接目标改变，去除链接目标后全文相同。仍保留最新用户要求优先、完整母图连续结构、最终3个注册缩放与世界脚印、门防夹/断电恢复、灯面与真实照明区分、整壳即时0.14与未实现完整室内等边界。
- `README.md:21` 说明即时Alpha切换、深暗门口，以及完整室内/分楼层/风机/真实环境照明不在范围；`:37–42` 指正式资源与独立同步副本，并给出项目根目录下新工具命令。未把资料集中称为新增玩法完成。
- `tools/sync_building_demo.ps1` 的包根从当前脚本位置解析到 `assets/ember/buildings_final`，README所示新工具确实存在；脚本声明同步白名单、新资源根和共享地板/机器人原依赖。这里只核说明与路径，不执行同步或94项验证。
- 当前README、四份`docs/*.md`及`review/README.md`共54个直接本地链接存在；规范中跨出资源包访问共享总体/地板/瓦片规范的相对层级正确。

历史路径处理：`review/README.md:3` 已说明报告文字、哈希与历史路径不作追溯性改写，`:9` 指向迁移映射。`review/history/README.md` 是原最终入口的历史副本，共25个链接，其中24个旧目录链接在迁移位置解析不到；不构成本次P2，不改其原文或原SHA。`review/consolidation/`与`original-v004r1/`的旧报告同样按快照解释。独立检查的数字不冒充制作方`current_document_links_checked=62`。

供根更新共享导航的直接映射如下；这是**当前入口映射**，不要求改写历史快照里的文本：

| 旧入口/根 | 当前入口/根 |
|---|---|
| `docs/shader-learning/ember-building-standard-v002.md` | `assets/ember/buildings_final/docs/ember-building-standard-v002.md` |
| `docs/shader-learning/building-intact-master-v004.md` | `assets/ember/buildings_final/docs/building-intact-master-v004.md` |
| `docs/shader-learning/building-production-coverage-v004r1.md` | `assets/ember/buildings_final/docs/building-production-coverage-v004r1.md` |
| `docs/shader-learning/selected-buildings-breakdown-v001.md` | `assets/ember/buildings_final/docs/selected-buildings-breakdown-v001.md` |
| `art-source/ember/buildings-final/README.md` | `assets/ember/buildings_final/README.md` |
| `art-source/ember/buildings-final/demo/project.godot` | `assets/ember/buildings_final/examples/standalone/project.godot` |
| `assets/ember/building_assets_v004r1/` | `assets/ember/buildings_final/textures/` |
| `scenes/ember/building_assets_v004r1/` | `assets/ember/buildings_final/scenes/` |
| `art-source/ember/selected-buildings-v001/` | `assets/ember/buildings_final/source/selected-buildings-v001/` |
| `art-source/ember/building-assets-v004/`、`building-assets-v004r1/` | `assets/ember/buildings_final/source/`中的同名目录 |
| `art-source/ember/deliveries/building_assets_v004r1_2026-10-06.zip` | `assets/ember/buildings_final/delivery/building_assets_v004r1_2026-10-06.zip` |
| `art-source/ember/ta-review-v001/building-v004r1-independent/` | `assets/ember/buildings_final/review/original-v004r1/` |
| `art-source/ember/ta-review-v001/buildings-final-incremental/` | `assets/ember/buildings_final/review/consolidation-ta/` |
| `art-source/ember/buildings-final/ta-review.md` | `assets/ember/buildings_final/review/ta-review.md` |
| `tools/sync_building_demo.ps1`等本包4个工具 | `assets/ember/buildings_final/tools/`中同名文件 |
| `scripts/ember/building_asset.gd`、`building_demo.gd`、`building_demo_actor.gd` | `assets/ember/buildings_final/scripts/`中同名文件 |
| `shaders/ember/building_intact.gdshader` | `assets/ember/buildings_final/shaders/building_intact.gdshader` |

共享README、TA规范、总体美术规范与当前review索引由根统一修链；本次未修改这些文件。上述映射已在新包现行规范/README中生效，不需要另改正文。

证据同目录：`docs-diff-binding.json`、`docs-path-diff.txt`保留规范逐行差异；`current-link-audit.json`将当前链接与历史快照链接分开记录；`docs-review-binding.json`绑定README/工具/当前规范/旧规范/迁移表SHA；`old-new-path-mapping.json`复制制作方迁移表中的完整旧→新物理映射。当前入口别名与物理保存位置不同的历史README已在本报告说明。

未重审PNG、未运行引擎或浏览器、未同步/删除/移动文件，生产文档未改。
