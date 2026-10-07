# 最终建筑路径迁移：独立运行增量审查

结论：**RUNTIME_RELOCATION_PASS**。统一目录 `assets/ember/buildings_final/` 在本次路径迁移范围内未发现新 P1/P2。既有 v004r1 整壳即时 Alpha 0.14、深暗门洞和登记交互范围继续适用；本轮没有扩大室内/分楼层功能范围，也没有重审造型。

## 代码与来源

独立基线来自前次 TA 固定 SOURCE 清单及保留的冷副本，先重算旧文件哈希再比对。3 份正式脚本、Shader、7 个场景和3份 GDScript 工具共 **14 份**，严格按 `relocation-plan.mapping` 替换路径后与新文件正文一致；演员脚本和 Shader 本身逐字节不变。两份正式 catalog/functional JSON 也只有相同路径替换，几何、锚点、运动时间、状态或保存数据没有变化。

因此保存/读档的角色→全部接触盒→建筑 restore 顺序，门/锁电/防夹、输入、碰撞和遮挡的前次有效实现均没有行为代码漂移；本轮没有重复旧 23 项或作者 94 项行为矩阵。

32 张正式/预览 PNG 与原 r1 ZIP 逐字节一致。迁入 `delivery/` 的原 ZIP 重算 SHA 仍为 `22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32`。主工程 `project.godot` SHA 仍为 `f1b0b9d3a429cbc38d19cfcb9c0d683f15e6543a53c175b78b2c6296ca6718ba`，与迁移前及前次 TA 记录相同。

## 路径与同步闭合

当前代码/场景及两份正式 JSON 中 **53 个实际引用点**，在主工程和独立示例双侧 **106 次存在性核验**全部通过。没有查到当前正式运行代码中的旧建筑入口引用；保留的注册 baseline 是历史数值对照，未将其中旧 source 路径当作当前加载入口。

`SOURCE_SYNC_MANIFEST` 66/66 对应正式来源，最终 `SYNC_MANIFEST` 66/66 对应示例当前文件，均逐项重算。二者当前唯一差异是验证重新生成的 `validation_v004r1.json`；正式图片与脚本没有因验证改写。

同步 PowerShell 工具并非逐字路径替换：除包根/示例位置调整，还新增 UID 白名单复制。这项单独读了完整 diff；SOURCE 在复制后登记，最终 SYNC 在验证后登记的流程保持，未新增删除、运行行为或审核绕过。**本审查没有执行同步工具。**

7 个正式 `.gd/.gdshader.uid` 与迁移前 SHA 相同。示例原先独立生成的 7 个 UID 更新后，现均逐字节匹配正式来源；当前 14 份运行/场景文件使用明确 `res://` 路径，没有 `uid://` 引用耦合。故该身份记录更新不造成资源误指向，另行登记而不声称全部副本字节保持。

冷导入生成的 `.import`、示例验证 JSON 与历史 UID 变化属于缓存/生成证据或同步身份调整；本轮没有将“作者 115 个保护成员”当作可独立复现的成员清单，也没有泛称全部移动文件不变。完整文件迁移清单由另外的完整性审查覆盖。

## 本轮独立运行

从新 standalone 最终清单复制隔离工程，保持当前包路径，使用单独 user 目录。Godot 4.7.2 **冷导入 exit 0、stderr 0**；随后在独立隐藏窗口的真实 OpenGL Compatibility 后端执行定点 **18/18，exit 0、stderr 0**：

- 新 7 个 PackedScene 均能加载及实例化资源；
- 三个交互 prefab 实际入树执行 `_ready`，成功读取各自定义、门登记与完整纹理，新 Shader 路由正确，脚印为 256×128 / 384×128 / 608×224；
- 新 demo 实际 `_ready` 成功创建三栋正式定义，共享地板 1100 格和原 64×96 角色纹理真实加载成功。

未操作用户编辑器、主工程或生产文件，没有新增造型/GPU 全套复验。作者 `verification/validation.json` 的 **94/94 仅绑定哈希**，不计为独立测试。

证据：[逐项迁移绑定](relocation-integrity.json)、[18项实际加载结果](cold-project/ta-relocation-load.json)、[独立探针](cold-project/ta_relocation_load.gd)、[冷导入](cold-import.log)、[真实后端日志](cold-load.log)、[同步工具 diff](sync-tool.diff.txt)。本轮输入快照保存在 `bound/`。
