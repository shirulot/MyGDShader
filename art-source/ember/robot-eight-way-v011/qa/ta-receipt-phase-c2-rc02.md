# 机器人 v011 C2 rc02 TA 正式复审回执

**PASS，2026-10-07。** SE collect F01/F02外肘轮廓P2已关闭；本次余下七方向idle/collect共14段42帧正式通过。与原八向walk64帧和C1 SW六帧合计，机器人八方向三动作共24段112帧已完成分批资产验收。主游戏集成仍是独立范围。

## 固定交付

| 对象 | 绑定值 |
| --- | --- |
| ZIP | `robot_eight_way_v011_phase_c2_rc02_2026-10-07.zip` |
| SHA256 | `64a3a18625dccc2fc1bde35ae44388a7acfb92ddb9aa4c83db811d2e5c10aa1b` |
| 大小／成员 | 35,321,800 bytes；1723载荷＋manifest＝1724文件 |
| manifest SHA256 | `004fa3465f364febbe904a6623afe0c857552d09dfee02a05c51f7f6093efa68` |
| metadata SHA256 | `10627793008ccf5b09861f1e9a55d7270d8847c8b8bf602ce997bbcc61ed79fa` |
| atlas SHA256 | `0340a11ca59efdb18c64385fa24ec8faa833f0c3c6b056b5c6a97d3f3f5b4268` |

## 修复与实际视觉结论

两个SE采集帧各自仅恢复原坐标(14,52..54)三格，由不透明甲色`#ece9d8`恢复为同一未编辑rig的原暗色`#101820`，共六像素次；mask同时撤销对应编辑许可。没有重画连接线、删暗点或换背景。局部源／修前／修后浅深ROI、原生与4×、根实际网页F01/F02/F03均确认外肘轮廓恢复连续，保持段一致、回位正常，未发现新增P1/P2。

其余110张正式PNG原字节保持；495个旧source文件、31个prompt文件和26个pose登记均保持，包含八身份母版、S新中性与固定部件。atlas变化也恰六点，所有112格完整RGBA等于对应PNG，未用格透明。整个包的变化还包括派生预览、QA和版本记录，未误称只有两个文件变化。

因此原[rc01全部42新帧实看](../robot-v011-phase-c2-rc01-independent/visual-review.md)及[S中性专项](../robot-v011-phase-c2-rc01-independent/neutral-review.md)的未变内容继续有效，原唯一P2由本次最小复审关闭；不要求重做已通过造型。证据：[本次视觉](visual-review.md)、[根实际网页](root-preview.md)、[技术绑定](integrity.md)。

## 技术验证与范围

完整新ZIP独立解包，无Godot缓存、保留交付`.png.import`，冷导入及探针exit0/stderr0。24段112格实际加载的RGBA、nearest、centered=false、offset(-32,-80)通过；SE collect真实经过0→1→2→3、一次finished后两显示节点回idle F00，采集中换向锁定和root固定通过。1723原载荷运行后哈希保持。[独立cold回执](technical-cold-receipt.json)、[行为结果](technical-minimal-cold-load.json)。

本轮未重复224GPU、全部循环或136切向矩阵，作者完整记录只作绑定，不写成TA独立重跑。动作规格保持64×96、root(32,80)、11色板、二值Alpha；idle2@2FPS循环、walk8@8FPS循环、collect4@6FPS单次。分批验收对象为固定资产及最小独立运行，不是主游戏业务玩法验收。

可按已通过像素与资源配置定版精简Godot运行包；如果重打包／改路径，提交从本固定包到运行包的映射和保持证明做迁移增量检查，不重生或改写已过帧。rc01返修记录保留，其他生产队列继续各自处理。
