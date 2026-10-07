# 走道 v002：根代理生成后的机械导出

本原稿由**根代理实际调用内置生图一次**生成；本导出代理本次生图调用为0。仅写 `correction-v002/corridor-correction/`，未修改旧v001、参考母图、共享标准或正式资源。

原稿为724×2172，准确1:3，整图实底。项目原稿与工具原文件SHA256一致：`f42ba73fa045e639acdabb2f78754565b8c4ce21ada8d4368d9a281cc6112aa1`。完整提示词、工具原路径和两个实际参考的SHA256均已登记到 `generation-record.json` / `result.json`。

| 切片 | 原稿整格裁框，XYXY右下不包含 | 导出 |
| --- | --- | --- |
| 北端头，mask16 | `[0,0,724,724]` | Nearest 128×128 |
| NS直条，mask17 | `[0,724,724,1448]` | Nearest 128×128 |
| 南端头，mask1 | `[0,1448,724,2172]` | Nearest 128×128 |

三格先整裁，再等比Nearest。Alpha均为255，全部边缘主体为 `[0,128)`。没有涂像素、调色、修Alpha、局部拉伸、拼局部、旋转或镜像。

**侧梁明显改善，但截面角色必须区分。** 128px图中主金属带目测为W=`[0,8)`、E=`[120,128)`，约8px；内侧暗隔缝分别为 `[8,10)`、`[118,120)`，板面亮倒角落在x10/x117。把隔缝和板面倒角一起计入的完整可见边框约11px。上述金属带边界是4倍图的视觉估计；暗隔缝另由亮度中位数定位。不能把“主金属带约8px”写成完整边框与配对地板截面已通过。

**板缝相位改善，首缝仍未达1px筛查容差。** 五道内部主暗缝测得 `[65,67)`、`[128,129)`、`[191,193)`、`[255,257)`、`[318,320)`，中心约66、128.5、192、256、319。相对于64/128/192/256/320，偏差为 +2、+0.5、0、0、−1px。其余四道明显改善，首道仍偏约2px，未登记全部板缝通过。

测量用内部横向Rec709亮度中位数、阈值36定位暗缝，仅作只读诊断；磨损、铆钉和倒角会影响局部RGB，暗芯并不是完整倒角宽度。JSON保留原生尺寸扫描与32/36/40阈值敏感性，便于复核。

上/中/下内部均值RGB约为 `[44.87,76.23,87.27]`、`[45.34,77.35,88.65]`、`[46.16,77.85,88.96]`，最大通道差1.69/255。蓝灰像素风一致性保持，未见明显全局渐变；颜色均值不能替代与配对地板的视觉审核。

接点Alpha没有差异；端头→中段、中段→端头、中段重复的RGB平均绝对差分别约89.66、4.63、13.67。第一项较大包含接点相邻排的亮倒角→暗隔缝转换，不能仅据此断言可见接缝，也不能只因母图连续宣称任意重复通过。已提供完整切片的CPU重复图，由根代理执行真实TileMapLayer/GPU审核。

当前状态：**诊断候选，结构筛查未全部通过，`production_ready=false`，GPU待根代理，用户视觉认可未取得。**

- 切片与邻接语义：`candidate-catalog.json`
- 128px候选：`candidates/floor_end_N_pixel_v002_128.png`、`floor_narrow_NS_pixel_v002_128.png`、`floor_end_S_pixel_v002_128.png`
- 单块4倍图：`review/floor_*_pixel_v002_4x.png`
- 母图注册对照：`review/corridor_registered_128x384.png`、`corridor_registered_4x.png`
- 中段重复：`review/corridor_mid_repeat_128x640_cpu.png`、`corridor_mid_repeat_2x_cpu.png`、`corridor_mid_repeat_world32_cpu.png`
- 来源、完整提示词、参考SHA、裁框、实测：`generation-record.json`、`result.json`、`prompts.json`

可复现：

```powershell
& 'C:\Users\shiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'art-source\ember\production-v008\correction-v002\corridor-correction\export_and_measure.py'
```
