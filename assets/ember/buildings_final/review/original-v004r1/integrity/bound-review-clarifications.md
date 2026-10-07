# v004r1包外说明更正

2026-10-06。适用冻结包SHA256：`22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32`。本说明不改包内PNG、源码、清单或既有验证结果。

更正此前对“透空RGBA全0”的泛化表述：完整生产PNG使用已声明的共享覆盖规则；拆分固定主体时，`export_building_parts_v004r1.gd:32`使用`Color.TRANSPARENT`清空被分配给交互层的区域，实际存成白色RGB、Alpha0。因此不能声称15张功能PNG的全透明RGB一律为0。

直接读取冻结ZIP得到以下例外，三图Alpha取值仍严格只有0与255：

| 固定主体图 | Alpha0、RGB255/255/255像素数 |
|---|---:|
| control_tower/fixed_architecture.png | 109852 |
| repair_workshop/fixed_architecture.png | 27098 |
| logistics_warehouse/fixed_architecture.png | 49035 |

准确描述为：正式实体PNG使用二值Alpha；上述三个固定主体层存在全透明白色RGB。它们不改变可见复合，也不使实体覆盖变为半透明。技术美术已明确此项为说明例外，不新增P2；当前固定包保持不变，不据此重生造型或重跑GPU。完整最终TA结论仍等待UI定点及来源组合复核收尾。
