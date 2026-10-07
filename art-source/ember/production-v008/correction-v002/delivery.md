# 连续母图：颜色与风格订正结果

2026-10-05。用户指出相邻瓦片的颜色和风格明显对不齐。本轮已实际订正：以本方像素地板为配色/像素簇参考，用一张连续地板母图切出NW外角、北边、西边、中心；用连续走道母图切出全新南北端头及中段，并对走道整幅补做一次侧梁与板缝订正。**真实铺图中颜色与材质跳变明显减轻；重复边界和完整形态仍未通过，不能作为完整通用瓦片集直接发布。**

## 直接查看

- [真实GPU修前/本轮对照](review/style_before_after_gpu.png)：左侧保留上轮旧写实端头与独立角块，右侧只含本轮新像素构件。两侧均为GPU截图的完整矩形裁切，未调色、缩放或修补艺术像素。
- [全部新构件128px原尺度GPU铺图](godot-review/connected_native_gpu.png)、[实际32世界格GPU铺图](godot-review/connected_world32_gpu.png)：修后布局旧素材数量为0。
- [627/617完整方框GPU比较](godot-review/registration_compare_gpu.png)：617只是机械注册比较，没有被宣称为合格替代。
- [本轮标准](standard.md)、[继承的完整验收标准](../correction-v001/standard.md)、[候选与坐标](candidate-catalog.json)、[完整实际提示词](prompts.json)、[生成台账](generation-record.json)。
- [独立复核](review/independent-floor-source-review.md)、[根任务逐块判定](review-results.json)、[Godot技术报告](godot-review/validation.json)。

## 修改与判定

| 项目 | 本轮结果 | 限制 |
| --- | --- | --- |
| 颜色、像素语言 | 四块地板来自同一母图；新走道采用同系蓝灰钢板、黄铜铆钉和像素倒角；实图没有上轮的大块写实/像素材质切换。 | 这是当前组合的局部改善结论，用户美术认可尚未取得。 |
| 地板自然相邻 | `[0,0,627,627]`、`[627,0,1254,627]`、`[0,627,627,1254]`、`[627,627,1254,1254]`完整方框，各自Nearest等比导出128。保留同一母图邻接关系。 | 原稿竖缝`[623,633)`被627切线分开，中心左边只余约1px暗缝，重复时与内部完整双倒角缝不同。自然相邻不代表任意重复通过。 |
| 地板617比较 | 同一母图按617方框连续切片，保留更多首端倒角。 | 板距仍约65/63px交替，且整套x1234切线截去了N边最右铆钉37个亮铜像素。整套拒收，保留比较，不替换627。 |
| 走道侧梁 | 从v001约2–3px提高到v002约8px主金属梁，端头与中段共享一张连续母图。 | 若把内侧暗隔缝及板面倒角合计，可见边框约10–11px；主梁与完整截面必须分别验收。 |
| 走道板缝 | 相位累计偏差从v001约6px减至v002约2px；主体暗缝约`[65,67)`、`[128,129)`、`[191,193)`、`[255,257)`、`[318,320)`。 | 首缝中心约66，仍偏离目标64；不能登记严格规则周期通过。 |
| 实底Alpha、导入 | 所有本轮切片Alpha全255；纹理128/世界格32/层缩放0.25/Nearest/Atlas padding；180,224像素导入Alpha及可见RGB差异0。 | 技术检查不能代替接口、完整形态和美术验收。 |
| 覆盖范围 | 7类主要诊断构件，另4个同母图617裁框比较项；实际生成3张母图。 | 不算11类新形态。E/S封边、其它外角、内角、T/十字等仍缺；完整47型及多套通用瓦片集未完成。池岸/其它家族本轮未混入修后地板证明。 |

627修订保留基准；走道选v002整幅订正结果。v001走道及最初627铺图保留在`corridor/`和`review/baseline-627-corridor-v001/`，便于复核实际改善。所有原稿、工具输出路径、参考与提示词SHA、完整裁框均留档。

本轮只使用内置`image_gen.imagegen`生成/编辑艺术母图，实际3次调用（地板1、初走道1、走道整体订正1）。Python仅执行完整方框裁切、Nearest等比导出、整块图集装配、测量和诊断截图排版，没有画艺术像素、填Alpha、局部拼材料或非等比拉伸。[冻结文件检查](protected-after.json)显示共享规范、v007、主项目与课程进度共50文件变更0。

## 复现与试铺

把`godot-review/project.godot`作为独立Godot项目打开；运行`review.tscn`可查看当前手工TileMapLayer样例。`connected_diagnostic_tileset.tres`包含所有候选与比较项，只用于审查；没有配置或宣称本轮完整47型Terrain自动选块。

在工作区根目录顺序执行，不触发新的生图：

```powershell
python art-source/ember/production-v008/correction-v002/corridor/export_and_measure.py
python art-source/ember/production-v008/correction-v002/corridor-correction/export_and_measure.py
python art-source/ember/production-v008/correction-v002/prepare_review.py
powershell -NoProfile -ExecutionPolicy Bypass -File art-source/ember/production-v008/correction-v002/godot-review/run_review.ps1
python art-source/ember/production-v008/correction-v002/compare_gpu_captures.py
python art-source/ember/production-v008/correction-v002/register_review_results.py
```

先完成共享完整周期/倒角接缝及走道首缝订正，再验证全方向端头、转角、凹角和分叉；目前`production_ready=false`，尚未接入正式资源。
