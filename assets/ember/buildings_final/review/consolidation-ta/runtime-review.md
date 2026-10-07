# 建筑最终组件合并：独立运行增量审查

结论：**PASS，本次继承链展开与正式示例同步范围内未发现新 P1/P2。** 该结论对应下列固定运行源码和最终快照，继承原 v004r1 的整壳即时淡出、深暗门洞与登记交互范围；不扩大为完整室内、分楼层遮挡或新的美术版本验收。

## 固定输入与静态差异

- 原 v004r1 冻结包 SHA256：`22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32`，实际重算一致。旧运行基线从该 ZIP 读取，未依赖被归档目录。
- 32 张保留 PNG 与冻结 ZIP 全部逐字节一致；9 份原运行来源哈希一致。7 个 prefab 中，3 个静态文件不变，3 个交互及 demo 仅更换正式脚本路径，场景属性未漂移。
- 51 个有效方法比对中，47 个正文在去除注释/空行后相同；另 4 个为可解释的展开：`building_asset.gd:189` 的 snapshot 直接写入原 r1 revision，`building_demo.gd:105`/`:116` 的保存和读档展开 super，`:141` 将原先两阶段地板构造合为同一 44×25 布局。保存路径保持 r1；读档仍先恢复角色，再刷新所有接触盒，最后 restore 建筑。
- 旧实现中已被 v004 rebuild 替代的拆件辅助方法移除；正式资源加载、门运动/锁电/防夹、碰撞、遮挡、输入与演员有效方法未改。完整 Shader 与冻结 v004 Shader 逐字节一致。
- 注册基线副本与 ZIP 内旧 v004 catalog JSON 完全等价，仅文本换行不同；导出/验证工具只替换该基线路径，生成算法未改。

具体哈希、方法来源与场景差异见 [runtime-integrity.json](runtime-integrity.json) 及同目录 `*-effective-method-diff.txt`。

## 本轮独立执行

在本审查目录建立隔离冷工程；没有运行用户的编辑器、修改主工程或操作清理目录。

冷导入 exit 0、stderr 0。独立定点 probe **23/23**，覆盖一扇门的旧新默认状态、锁门拒绝、半开运动、断电冻结、真实占用安全反开；实际 Physics2D 关门阻挡及开门通行；保存位置近/远且读档前位置相反时，恢复角色/接触盒顺序以及锁电与半开状态；44×25 地板、帮助/toast 布局、7 个 prefab 加载、自然处理的真实 E 键锁门反馈。

同一 probe 在真实 OpenGL Compatibility 后端再次得到 **23/23，exit 0、stderr 0**，设备为 NVIDIA RTX 4070 Laptop GPU。仅为本次合并定点验证，未重跑整套截图或 94 项原测试。

headless dummy 后端曾在旧、新字节相同 Shader 上各输出一次 `shader_compiler.cpp:1329` 提示，未造成检查失败；真实后端未出现该提示。原始日志保留，未将 headless 日志称为 stderr 0。

证据：[独立结果](cold-project/ta-runtime-incremental.json)、[真实后端日志](cold-runtime-rendered.log)、[真实后端 stderr](cold-runtime-rendered.stderr.log)、[探针](cold-project/ta_runtime_incremental.gd)、[冷导入](cold-import.log)。

## 最终同步证据与边界

最终 `review-snapshot.json` 的 9 个文件哈希及大小均重算一致；其中实际测试的 3 脚本和 Shader 与最终快照逐字节相同。`SOURCE_SYNC_MANIFEST` 59/59 对应正式来源，最终 `SYNC_MANIFEST` 59/59 对应示例实际文件。唯一来源/最终差异是验证重新生成的 `validation_v004r1.json`，与正式 `verification/validation.json` 一致，属于生成证据差异。

只读检查了新版 `tools/sync_building_demo.ps1`：白名单复制后登记 SOURCE，验证后重新登记最终 SYNC，未新增删除或运行逻辑修改。本审查没有执行该同步工具。作者 **94/94**、冷导入和截图证据仅绑定哈希，不计为本轮独立重跑。

最终运行源码哈希：

| 文件 | SHA256 |
| --- | --- |
| building_asset.gd | `31d48dadfe84825670cd1546cb20175bf7f15ef46a07b3ba51c7b3a57071b3f3` |
| building_demo.gd | `00e4a9fd2fc974061eacec1beac3c49de91459eb68b35fcd3872c930911b8e68` |
| building_demo_actor.gd | `dcc2adc73cb41d846be216f5715307d3c4be7f302e45a108b49eb34c24ce3077` |
| building_intact.gdshader | `2f47d83b1da8ed8baf5cd72c5bc242ad7a629114ac8f86b48bced4e3cc8f1dc5` |

规范 v002 更新为 TA 明确说明的 `ac27621a08fc9ac568188ad66ff99613d520a1ed8bdfe9e4329bffe40ddde9c8`；文档变更与运行合并分别登记。主工程 `project.godot` 哈希仍与 provenance 的 before 相同。清理状态只读绑定为 `ARCHIVED_PENDING_DELETE`、deleted 0，本审查未移动、删除或绕过拒绝。

最终绑定及固定副本见 [final-snapshot-binding.json](final-snapshot-binding.json)、[bound/review-snapshot.json](bound/review-snapshot.json)。
