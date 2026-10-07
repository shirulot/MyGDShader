# 建筑 v001 独立技术审查

技术结论：**需修订**。固定 ZIP 的冷导入、47 件来源复算和原 148 项交互均通过；独立补验发现一处 P2 实际 demo 读档顺序缺陷。静态建筑、四入口物理、门安全与遮挡在本次测试范围通过，本结论不授予美术或用户外观验收。

固定包：`building_assets_v001_2026-10-06.zip`，独立计算 SHA256 为 `5870774d53e2010158523021661cf30a560386fe2826c39a66845d8e7e45dbc1`。

## P2：读档使用旧玩家接触盒，半关门被错误改为重开

- 文件位置：`scripts/ember/building_demo_v001.gd:120–124`。先循环 `building.restore(saved)`，最后才恢复 `actor.position`。
- 触发链：`scripts/ember/building_asset_v001.gd:227` 的 `restore()` 调用 `advance_state(0.0)`；该方法 63–66 行在目标小于进度时读取 `_actor_rects`，将门 `target` 改为 `1.0`。这里的接触盒属于读档前的人物，随后恢复的玩家位置已经不同。
- 最小条件：维修工坊人门半关，`progress=0.5,target=0.0`；保存时玩家远处 `(24,470)`。读档前玩家来到门前 `(336,416)`，让 demo 正常刷新接触盒，再加载该存档。
- 实测结果：玩家正确恢复到 `(24,470)`；门仍为 `progress=0.5`，但 `target` 从保存的 `0.0` 变为 `1.0`。再过两帧刷新接触盒后，target 仍为 1，恢复运动后会自动打开。保存与恢复快照不一致。
- 对照：在同一 demo / 同一存档中，把公共 `set_actor_rects()` 输入刷新为已恢复玩家的真实接触盒，再次调用原生产 `load_state()`，快照完整匹配。确认是旧接触数据影响恢复，而非无效存档。
- 影响：示例宣称保存 / 恢复门的 progress、target、锁定等状态，实际恢复可能改变运动方向。原 148 项 demo 存档只测 `target=1` 的半开态，因此没有触发这条关闭分支。
- 建议修法：在 demo 读档时，先恢复玩家位置，给所有建筑注入该位置对应的真实接触盒，再恢复建筑状态。恢复状态与遇阻判断应使用同一时点的数据。存档玩家确实占用门口时仍应执行安全重开。
- 修后复验：原失败的两项变 PASS；检查存档玩家在远处 / 在门口的半关态、断电半关态，确保既保持可恢复的运动目标，也正确处理真实占用。生成新的固定包复审，不覆盖当前 ZIP。

原失败 JSON 为 `cold-project/ta-building-probe.json` 中 `demo.load_preserves_saved_closing_target` 与 `demo.old_occupancy_does_not_reopen_after_load`；两项失败属于同一 P2。具体 before / after 快照及玩家位置完整保存。

## 独立运行与通过范围

`cold-project/` 是本技术审查独占的冷解压工程。只在该副本的 `project.godot` 新增独立 user:// 名称 `Ember TA Building v001 Independent`，避免测试存档与其他审阅工程共用；没有改生产文件或操作用户已有 Godot 编辑器。

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 独立冷导入 | 退出0、stderr空 | `cold-import.stdout.log` / `cold-import.stderr.log` |
| 包内来源复算 | 47件PASS，含44生图RGB及3数据Mask | `source47.stdout.log`、`cold-project/assets/ember/building_assets_v001/validation_v001.json` |
| 原交互测试重跑 | 148项PASS，退出0、stderr空 | `interaction148.stdout.log`、`cold-project/assets/ember/building_assets_v001/interaction_validation_v001.json` |
| TA独立边界探针 | 41项，39通过、2失败；退出1，stderr空 | `cold-project/tools/ta_building_probe.gd`、`cold-project/ta-building-probe.json`、`ta-probe.stdout.log` |

独立边界探针调用同一生产节点和 Physics2D，没有复制门的状态机。四个实际入口分别核验：全开无门碰撞、开始关闭恢复阻挡、真实机器人移动时进入安全区域并使正在关闭的门反向、反向进度增长、部分开启断电冻结、JSON状态往返、恢复供电解除碰撞，以及实际进屋隐藏屋顶 / 前墙、实际走出恢复壳体。上述 36 项均通过；demo 4 项中2项失败，另加同文件新鲜接触数据的对照1项通过。

生产的 PNG、runtime / demo / actor / validator 源码保持不变。源码审查覆盖组装、门 / 设备逻辑、示例输入、遮挡、snapshot / restore、来源与交互测试；未发现其他已证实的 P1 / P2 问题。

## 范围边界

本报告仅为技术分项。用户要求的整体建筑组合主交付及必要拆层、美术形制、像素质量与最终同尺度视觉由根级 TA 独立决定。建筑自动笔刷、多朝向、完整室内关卡、屋顶行走、破坏和新人物动画均不在固定 v001 技术承诺内。demo 使用便携工程的1536×1024逻辑画布，主工程720×720接入与示例UI适配另行处理。
