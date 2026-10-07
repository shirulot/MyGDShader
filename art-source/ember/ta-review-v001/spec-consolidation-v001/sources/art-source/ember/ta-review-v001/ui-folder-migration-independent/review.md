# UI 统一目录迁移：独立增量复核

结论：**PASS_MIGRATION_ONLY**。当前统一入口 `res://assets/ember/ui_final/` 的34张PNG、18个皮肤UID、新入口与当前引用完整；运行时改动限定皮肤加载根路径。未发现本次目录迁移新增的具体返修项。原v006视觉、交互和宿主验收范围保持原回执边界，不将本次迁移扩展为新页面/新宿主通过。

| 独立检查 | 当前结果 |
|---|---|
| 冻结v006 ZIP | SHA-256仍为 `af61549eef1605a98301f822c2018d68bed4687118a2ed8c499073e71e758504`，未改动。 |
| 34张PNG | 新 `skins/` 的18张和 `previews/` 的16张均与迁移映射迁前SHA及冻结v006对应PNG逐字节相同，34/34。没有重新生成或修改图片。 |
| 18个皮肤UID | 新 `.png.import` 中UID与冻结ZIP原导入元数据一致，18/18；导入 `source_file` 已切至新路径。独立Godot加载返回的18个UID又与当前元数据逐一相符。导入缓存路径改变属于迁移，不要求 `.import` 全字节继承。 |
| inventory | 将新 `res://assets/ember/ui_final/skins/` 路径反替换后，其JSON结构与冻结v006相同，尺寸/九宫格/职责等合同未变。 |
| 当前UI运行代码 | 对冻结ZIP已有的26份UI脚本/场景比较：25份逐字节相同，唯一差异为 `scripts/ember/ui_edge_v001/edge_ui_style.gd:6` 的 `ASSET_ROOT` 一行。反替换皮肤根路径后该脚本与旧稿全文相同。 |
| 当前入口与资源引用 | 新 `ui.tscn` 实例原 `scenes/ember/ui_edge_v004/interaction_ui.tscn`；新 `demo.tscn` 实例原 `scenes/ember/ui_edge_interactive_v004.tscn`。UI脚本/场景42条直接 `res://` 引用存在；动态皮肤加载覆盖18张。 |
| 最小Godot独立加载 | Godot 4.7.2 headless，仅加载18张皮肤与两个新PackedScene入口，**20/20 PASS**；皮肤尺寸与inventory一致。未实例化UI、未重跑153项交互、未捕获新GPU图。 |
| 当前总览 | `catalog-manifest.json` 52个实际路径/href/SHA绑定均有效；HTML内嵌catalog与manifest结构相同。HTML模板中的动态href按实际catalog数据检查，不将 `${esc(item.href)}` 字面模板误报成坏文件。 |
| 导航与兼容入口 | 当前README、规范导航、TA入口、旧README、旧HTML兼容跳转等78个实际本地链接有效。旧HTML直接指向新总览；未绕过本地 `file://` 浏览器限制，本次仅读HTML及路径。 |
| 截图用途 | `previews/.gdignore`存在；16张截图仍为参考资料，18张皮肤才是活动加载源。 |

工具改动与职责已读源码核对：

- `tools/build_ui_edge_skin_v001.gd:7` 输出改至 `res://assets/ember/ui_final/skins`，当前PNG字节保持原冻结稿。
- `tools/capture_ui_interactions_v004.gd:5` 捕获输出切至 `assets/ember/ui_final/previews/`；新增单独 `EVIDENCE` 根继续保存原 `art-source/ember/ui-interactions-v004/` 的验证JSON，并确保截图目录有 `.gdignore`。在冻结ZIP的9份UI `.gd` 验证/捕获工具中，仅此捕获工具改变，差异不改UI交互逻辑。
- `tools/build_ui_final_catalog.py` 的总览/皮肤/截图根及相对链接已指新目录；未执行重建以免改生产目录。
- `tools/prepare_ui_delivery_v004.ps1:15` 收集新皮肤根、`:18` 收集两个新入口、`:43` 新审阅工程main scene指新demo；`tools/freeze_ui_delivery_v004.ps1` 当前截图清单与新预览目录对应。此为工具源码检查，未新打包或覆盖原v006 ZIP。
- `docs/shader-learning/ember-ui-style-guide.md:143` 明确新资源根、入口和旧脚本/场景仍为活动依赖；README说明迁移后加载路径/元数据有意改变，不能再称当前全部文件与旧ZIP字节相同。

作者迁移记录声明153项交互通过，并有 `art-source/ember/ui-final/validation/folder-runtime.json`。本审仅绑定这些作者报告当前SHA，不将其描述为TA独立重跑。也不再将此前迁移前“80文件字节一致”套用到当前目录；本次明确使用34PNG、18UID和25份未变运行文件等分项结论。

独立证据同目录：

- `png-uid-binding.json`：34张当前PNG与冻结ZIP逐字节绑定、18个旧/新UID。
- `reference-diff-binding.json`：52总览绑定、78本地链接、26运行文件比较、42直接引用、inventory及`.gdignore`。
- `runtime-path-diff.txt`、`capture-path-diff.txt`、`tool-zip-comparison.json`：运行时最小路径差异与捕获工具增量。
- `load-entry-minimal.gd/.json/.log`：独立20资源加载、实际UID、引擎版本和输出；脚本只写TA证据。
- `current-entry-tool-binding.json`：本次当前入口/规范/工具/作者报告SHA，以及独立加载UID交叉结果。

未修改生产文件，未删除、移动或清理任何文件。
