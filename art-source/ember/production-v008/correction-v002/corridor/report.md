# 连续南北走道母图：一次生成结果

实际使用内置 `image_gen.imagegen` **1次**，`transparent_background=false`。唯一风格参考是 correction-v001 的 `raw/floor_center_pixel_v001.png`；未使用旧写实图、旧端头，也未追加生图。

母图为 **724×2172，准确1:3，RGB实底（等效Alpha全255）**，是一张连续完整构件。工具原稿及字节不变的项目副本已保留。没有留白均分、非等比拉伸、调色、Alpha修补、局部拼片、旋转或镜像。

| 三格切片 | 原稿整格裁框，XYXY右下不包含 | 导出 |
| --- | --- | --- |
| 北端头，mask16 | `[0,0,724,724]` | Nearest 128×128 |
| NS中段，mask17 | `[0,724,724,1448]` | Nearest 128×128 |
| 南端头，mask1 | `[0,1448,724,2172]` | Nearest 128×128 |

颜色均值稳定：上/中/下板面内部平均RGB约为 `[45.90,76.18,87.80]`、`[45.44,75.30,86.61]`、`[45.90,75.84,87.11]`，最大通道差1.19/255。目视采用同一蓝灰像素簇风格，没有明显整体上下渐变；这不等于与其它独立生成素材的颜色或用户视觉认可已通过。

**结构拒收，三格只作诊断：** 两侧外梁目测约2–3px，明显不足8px目标。虽然有2列6行大板，主暗横缝测得 `[65,67)`、`[131,133)`、`[196,198)`、`[262,264)`、`[326,328)`，未落在64/128/192/256/320节奏，后部相位偏差达到6px。测量采用横向内部中位亮度定位暗缝，未改动原像素。不能把完整母图原顺序连接的连续性称为中段任意重复也已通过。

三个切片Alpha均为255，接点没有轮廓孔洞。端头→中段、中段→端头、中段重复的可见RGBA差异仍记录在JSON；它们不单独替代结构与视觉审核。GPU与真实TileMapLayer布局由根代理统一执行，当前 `production_ready=false`、用户认可未取得。

- 完整原稿：`raw/corridor_master_pixel_v001.png`
- 128px切片：`candidates/floor_end_N_pixel_v001_128.png`、`floor_narrow_NS_pixel_v001_128.png`、`floor_end_S_pixel_v001_128.png`
- 母图注册/放大：`review/corridor_registered_128x384.png`、`corridor_registered_4x.png`
- 中段重复诊断：`review/corridor_mid_repeat_128x640_cpu.png`、`corridor_mid_repeat_2x_cpu.png`
- 提示词：`corridor_master_pixel_v001.prompt.txt`、`prompts.json`
- 原始工具路径、SHA256、参考SHA、实际尺寸、裁框、接口与色调测量：`generation-record.json`、`result.json`
- 切片语义和坐标：`candidate-catalog.json`

原稿SHA256：`60f1e9d846190d87d30eb5afcbb28b2abb44e8078fbb61eab491f24a8f1d58ad`。

可复现整格导出与测量：

```powershell
& 'C:\Users\shiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'art-source\ember\production-v008\correction-v002\corridor\export_and_measure.py'
```

本次只写 `production-v008/correction-v002/corridor/`；未修改bank、correction-v001、共享规范或正式资源。
