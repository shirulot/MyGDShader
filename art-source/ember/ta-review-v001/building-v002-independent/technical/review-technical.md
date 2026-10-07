# 建筑 v002 独立冷包技术审查

**结论：技术通过。v001 读档顺序 P2 已关闭，本次未发现新 P1/P2。美术风格与成品视觉由根审查及视觉代理判定。**

审查固定 ZIP SHA256 `18fe88a25dc19aaaf7cdae43505ff3eb04c060b5358daf8171fcc300c4832f35`，72,303,483 bytes，279 entries / 278 payloads。独立解到本目录 cold-project。冷导入 exit 0、stderr 空；仅在冷副本 project.godot 添加独立 user storage 目录，未改生产源码、M0 或用户编辑器。

## 实测结果

| 验证 | 检查数 | 结果与意义 |
|---|---:|---|
| 原独立 TA 探针 | 41 | PASS；仅两处 preload 路由切换 v002，原测试正文未改。含四入口实际 Physics2D 遇阻、部分打开阻挡、断电冻结、JSON 往返、实际进出遮挡、原读档复现。 |
| 包内交互验收独立复跑 | 148 | PASS；加载固定包实际 runtime/示例。 |
| 包内保存矩阵独立复跑 | 32 | PASS；workshop personnel 的 8 种远近/电源组合。 |
| 新增独立四入口保存矩阵 | 128 | PASS；32 个磁盘恢复场景，全部入口各覆盖保存近/远 × 读档前近/远 × 供/断电。 |
| 包内组合验收独立 GPU 复跑 | 118 | PASS；82 来源投射/画布注册检查与 36 实例/PNG/静态场景/状态渲染检查。实际生成 24 张 GPU 对照图。 |

以上合计 467 项，所有最终运行 exit 0、stderr 空。该计数是行为与资源实测证据，不替代美术判断。

## 旧 P2 的关闭证据

修复位置：[building_demo_v002.gd:47](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v002-independent/technical/cold-project/scripts/ember/building_demo_v002.gd:47)。load_state 先恢复存档角色，再向全部建筑提交新的 ground_rect，最后 restore 各建筑；继承基类零时长安全检查保留。

原最小复现：人员门处于 progress=0.5 / target=0，保存玩家在远处；加载前玩家走到门口，加载同一文件。v002 恢复后玩家在保存的远处、门仍 target=0，后续两帧不会被旧占用误重开。原 41 探针中的两个旧失败项均 PASS。

新增矩阵使用四个真实门位：control_tower/personnel、repair_workshop/personnel、logistics_warehouse/personnel、logistics_warehouse/cargo。每次保存后故意改变门进度、供电和玩家位置，再从真实文件加载。检查同帧所有建筑接触盒与室内 Roof/FrontWall 遮挡恢复；半开门的真实 Physics2D 仍阻挡；保存占用时 target=1 安全重开，保存无人时 target=0；供电继续方向正确，断电保持 progress=0.5。未更改生产恢复方法。

## 完整 PNG / 单 Sprite / 交互预制体闭合

对三栋正式交互 tscn 实际渲染，闭门图分别与 complete_closed.png 和静态 single-Sprite tscn 对照，可见 RGBA 与 Alpha 差异均为 0。canvas/pivot 分别为 192×352/(96,328)、256×256/(128,232)、320×288/(160,264)。

旧散件 runtime 与 v002 功能合层 runtime 的 8 状态 × 3 建筑 GPU 对照差异均为 0：闭门、半开、全开、检修、锁定并亮玻璃、故障、断电、室内遮挡。比较忽略双方 Alpha=0 的隐藏 RGB；不声明 GPU 全 RGBA 字节与源 PNG 完全一致。82 个来源投射/注册检查直接读取源 PNG，不调用生产 exporter。

三份继承的 v001 基础 runtime/demo/actor 与冻结 v001 ZIP 字节完全一致；9 份本次关键源码/目录来源在最终复验后仍与冻结 v002 ZIP 字节一致。全包 PNG、母稿和清单审查由另一个独立代理覆盖。

## 可复核证据

- [技术结果汇总](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v002-independent/technical/technical-summary.json)
- [固定包/冷准备记录](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v002-independent/technical/cold-preparation.json)
- [原 TA 41 结果](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v002-independent/technical/cold-project/ta-building-probe.json)
- [独立 32 场景 / 128 检查结果](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v002-independent/technical/cold-project/ta-building-save-matrix-independent.json)
- [独立矩阵探针源码](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v002-independent/technical/cold-project/tools/ta_building_v002_save_probe.gd)
- [独立交互复跑 148](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v002-independent/technical/cold-project/assets/ember/building_assets_v002/interaction_validation_v002.json)
- [独立保存矩阵复跑 32](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v002-independent/technical/cold-project/assets/ember/building_assets_v002/save_matrix_validation_v002.json)
- [独立组合/GPU 复跑 118（含 24 图哈希）](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v002-independent/technical/cold-project/assets/ember/building_assets_v002/composition_validation_v002.json)

## 范围边界

技术通过仅限三栋声明的 south-facing 建筑、完整图/静态 Sprite/功能预制体和现有专用示例交互。未声明屋顶可达、完整室内玩法或多朝向；这些不是本轮阻塞。生产主工程和 M0 集成不在本包修改范围。
