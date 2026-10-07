# 机器人 C2 rc02 独立技术增量复审

2026-10-07。**固定包、六像素修复边界、原资产保持、112 帧图集绑定及最小独立冷加载全部通过。** 美术结论另见 [visual-review.md](visual-review.md)，正式放行由主 TA 合并实际网页检查后记录。

| 对象 | 本次独立核验 |
| --- | --- |
| ZIP | `robot_eight_way_v011_phase_c2_rc02_2026-10-07.zip`，35,321,800 B |
| ZIP SHA256 | `64a3a18625dccc2fc1bde35ae44388a7acfb92ddb9aa4c83db811d2e5c10aa1b` |
| 成员 | 1723 payload + manifest = 1724 文件；CRC、安全路径、大小、SHA 全部通过 |
| manifest SHA256 | `004fa3465f364febbe904a6623afe0c857552d09dfee02a05c51f7f6093efa68` |
| metadata SHA256 | `10627793008ccf5b09861f1e9a55d7270d8847c8b8bf602ce997bbcc61ed79fa` |
| atlas SHA256 | `0340a11ca59efdb18c64385fa24ec8faa833f0c3c6b056b5c6a97d3f3f5b4268` |
| 固定目录 | `robot-eight-way-v011/review/phase-c2-rc02` 的全部 1723 payload 与 ZIP 逐字节匹配 |

脚本 [technical-visual-bind.py](technical-visual-bind.py) 从两个已核 SHA 的 ZIP 直接比较，不执行生产构建。结果：[technical-visual-binding.json](technical-visual-binding.json)。

## 精确修复与继承范围

只有 `frames/collect/down_right/robot_collect_down_right_f01_v011.png` 与 `...f02_v011.png` 两张正式帧改变。每帧恰好将原坐标 `(14,52)`、`(14,53)`、`(14,54)` 从 `(236,233,216,255)` 恢复为 `(16,24,32,255)`；这六个输出像素均与同一包未编辑 raw rig 的相同坐标完整 RGBA 一致。没有新增颜色或绘制新连接线。

F01 新 SHA 为 `c7e3b7d8edc706284a68bf40f7b523ac60dfe84bcd30a518a9acce450cf273f3`；F02 为 `686c11388a2ac8c6b1efd97a762c87379e5888b690cd4b3001ceaf434ab69320`。两张关节 mask 也只移除对应的三格编辑许可，patch 记录明确登记三个恢复点。源复合代码在 SE collect F01/F02 分支校验原像素为 `101820ff` 后扩展保护区，与最终像素闭合。

其余 110 张正式 PNG 对 rc01 全部字节相同。rc01 的 495 个旧 `source/` 文件、31 个 `prompts/` 文件、其中 26 个 `rig_and_poses.json` 均保持原字节；包含八张身份母版、新 S 中性姿态、固定部件、原始生成图、生成输入和 pose 登记。rc02 另新增一份 rc01 metadata 来源记录，不是更改母图。`run-manifest.json` 的生成记录保持，仅版本／状态／冻结目录／修复说明及 atlas 哈希相应更新。

因此 rc01 已完成的 42 新帧全身逐帧审查与 S 中性来源审查可按未变内容继承；本轮不重复完整重建全部骨架／AI 接缝。旧 64 walk 与 C1 SW 六帧仍处于这 110 张不变帧之内。

112 张 PNG 均为 64×96、binary Alpha，透明像素 RGBA 为零；atlas 使用 11 个不透明颜色。所有帧的 atlas 区域完整 RGBA 相同、所有未用格完整 RGBA 为零，整个 atlas 对 rc01 也恰好六个像素变化。Godot 工程图集与根图集逐字节相同。24 clips 的帧次序、区域、FPS、loop 和 root 登记保持：idle 2@2FPS、walk 8@8FPS、collect 4@6FPS 单次；root (32,80)。

包内其余变化为对应预览／GPU 图／QA 记录／版本文档和制作脚本；完整新增与变更路径列表保留在绑定 JSON 中，没有把整个包误称为仅两个文件变化。

## 最小独立冷加载与采集恢复

使用 [technical-cold.py](technical-cold.py) 从固定 ZIP 完整解包到全新 `technical-cold-package/`，起始没有 `.godot`，保留原 `.png.import` 配置，只添加 TA 自有探针。Godot 4.7.2 headless 导入和探针均 exit 0、stderr 0；原 1723 payload 在运行后全部 SHA 不变。

独立结果 [technical-minimal-cold-load.json](technical-minimal-cold-load.json)／[technical-cold-receipt.json](technical-cold-receipt.json)：

- 24 clips、112 atlas cells 实际加载，所有区域完整 RGBA 对比通过。
- 1×／4×显示节点的 nearest、centered=false、offset=(-32,-80) 与锚点登记正确。
- SE collect 实际经过 `[0,1,2,3]`，恰好一次 finished，两个节点都回到 `idle_down_right` F00。
- 采集中发起换向，方向仍被锁定；root 位置保持。

这次只做 SE 代表行为和全部资源加载，没有独立复跑 224 张 GPU 捕获、全部循环或 136 次切向。作者重新提交的完整 GPU／切向证据属于已绑定包内材料，不冒称为本次 TA 独立执行。检查范围仍是资源交付，不代表主游戏接入完成。
