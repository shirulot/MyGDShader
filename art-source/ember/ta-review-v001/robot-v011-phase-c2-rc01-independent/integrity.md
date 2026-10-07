# 机器人 v011 C2 rc01 技术完整性审查

2026-10-07。**技术来源、固定包和最小独立冷加载通过；东南采集 F01/F02 存在已确认的局部轮廓问题，本报告不授予美术通过。** 正南新中性来源专项见 `neutral-review.md`，全部新 42 帧的视觉裁决见 `visual-review.md`。

## 固定包身份

| 项目 | 独立核对 |
|---|---|
| ZIP | `robot_eight_way_v011_phase_c2_rc01_2026-10-07.zip`；35,015,025 B；SHA-256 `e0a5fe91bcd62509d0f342e45334ce34cf374ebea1ac0203162d9b90f79b5643` |
| 清单 | 1702 个载荷 + 清单 = 1703 文件；CRC、字节数和全部载荷 SHA 精确匹配；固定目录同样 1702/1702 匹配。 |
| 清单 SHA | `27b6448dbb0de738fc87b45dc17924dafedec3af8dee47f4512f256a4f02ba4d` |
| metadata SHA | `8072ce3ef444d8c2d3c13cf072380c7398385997b008c01269d0bb3c6d210b6e` |
| atlas SHA | `c9963cd1f9c1db11a932164c57eefde0ed80e2de692f0d3700338d7bddba6cc1` |

复用中断前已完成的 [technical-binding.json](technical-binding.json)、[technical-zip-binding.json](technical-zip-binding.json) 及可复现的 [technical-verify.py](technical-verify.py)。恢复后补做实际固定目录、14 个源输入排版、原始生成文件以及未用图集格验证，见 [technical-supplement.json](technical-supplement.json)。未重新执行生产构建脚本。

## 来源与动作约束

14 张 C2 imagegen 原图、确切输入和提示词分别校验 SHA；14 个原始生成路径当前存在且与交付源字节相同。实际输入均独立重拼为原 rig 的 2 列原始帧，再 nearest 放大 4 倍，完整 RGBA 零差。提示词约束方向、固定身份、左上光、局部接缝修复及相同姿态共用接缝。

七方向各 12 个固定部件 raw hash 匹配。六个非 S 新方向与 C1 的部件逐 RGBA 比对，仅 body/pelvis 按规定共享原图两行；S 的来源变动交给专项审查，本报告仍独立重算其登记部件、姿态与最终帧。全部新 42 帧按部件变换重拼，原 rig 零差，再以原 AI 源的公共 sheet 变换、11 色量化、掩膜及保护区重算，最终 42 帧零差；所有保护区和 mask 外变更为 0。

独立验证 idle 仅上身上移 1 px，腿靴固定；collect 两靴/踝固定，骨长最大浮点残差 `1.25e-14`，端点最大残差 `1.43e-14`。S/N 下压 1 px，其余 2 px。F01/F02 除解剖左近臂以外的变换相同，远臂/躯干/腿与靴共用接缝，避免保持帧随机跳变。七向 collect F03 与对应 idle F00 全 RGBA 相同。E idle 的 2 个新增孤立暗点确实被原始不透明轮廓邻接过滤排除。

技术合规不保证每个 mask 内像素美术正确：**SE collect F01 的 `(14,52..54)` 原暗外轮廓被 AI 补丁改成不透明甲色 `#ece9d8`，F02 继承同一接缝；浅底出现原暗点悬空的读感。** 独立原因链与最小修复见 [technical-se-elbow.md](technical-se-elbow.md)。不能用 Alpha 连通、保护区零差或骨长固定豁免此问题。

## 已通过资产与导出

C1 ZIP `0c62177198973b24bb3fbfcc306ba4617af3ad754eb5a0696bdfddb4f19f51df` 内的 64 张八向 walk、6 张 SW idle/collect，以及 8 张身份母版，合计 78 张均与 C2 字节完全相同。新 S 中性姿态没有回写旧身份图或旧行走帧。

112 张最终 PNG 均为 64×96、11 色、binary Alpha，透明像素 RGB=0，与 512×2304 图集各自区域完整 RGBA 精确匹配；所有未用格完整 RGBA 为零。Godot 工程图集与根图集字节相同。24 clips 参数为 idle 2@2FPS 循环、walk 8@8FPS 循环、collect 4@6FPS 单次，root=(32,80)。

## 最小独立 Godot 冷加载

首次 TA 选择性复制工程时遗漏了固定包内的 `.png.import`，导致 Godot 自动采用 `process/fix_alpha_border=true`，与交付配置 `false` 不同，112 个嵌入帧全 RGBA 比较失败。该次 [technical-minimal-cold-load.json](technical-minimal-cold-load.json)、初始日志及隔离目录保留，**属于 TA 冷验搭建错误，不是固定交付包缺陷**；也没有把旧 FAIL 改写为 PASS。

修正方法是从同一固定 ZIP 完整解压到新的 `technical-cold-package-r1/`，保留全部原 `.import` 配置，初始 `.godot` 不存在。只添加 TA 自有探针，原 1702 载荷导入后全部 SHA 不变。Godot 4.7.2 headless 导入 4.800s、最小探针 2.260s，exit 0、stderr 0，结果 **PASS**：

- 24 clips / 112 atlas 单元实际资源加载及完整 RGBA 比对通过。
- 1×/4×节点均 nearest、centered=false、offset=(-32,-80)，参数正确。
- S/N/E 三个代表 collect 实际依次播放 `[0,1,2,3]`，各恰一次 finished，两个显示节点回到同方向 idle F00；采集中换向被锁定，root 不动。

结果见 [technical-minimal-cold-load-r1.json](technical-minimal-cold-load-r1.json)、[technical-cold-r1-receipt.json](technical-cold-r1-receipt.json)，可复现脚本 [technical-cold-r1.py](technical-cold-r1.py)。这是 headless 资源数据与代表行为验证，没有独立重跑完整 GPU 捕获、全部自然循环或切向矩阵。

## 作者证据边界

作者 `qa/godot_full_actions_v011.json` SHA 为 `3c8b2aae525bec284d5173239a014da9af7e1c68f71ac257964d172fa674060c`，与本次 atlas 绑定；224 个 GPU 文件存在，16 条循环动作各 2 圈、8 条 collect 回位和 136 条切向记录结构/报告值符合要求。以上仅绑定作者文件和记录，**不是 TA 独立复跑 224 张 GPU 或 136 次切向**。作者技术 PASS 不替代本轮美术返修决定，也不代表主游戏接入完成。
