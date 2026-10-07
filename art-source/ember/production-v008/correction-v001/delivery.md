# 按标准执行的首轮像素风订正

2026-10-05。依据用户最新要求，采用清楚的像素轮廓、成簇色块和少量明暗层次，减少写实纹理。标准已列出，首轮已实际执行8次内置生图及一次直岸整块注册修正。**局部宽度与直岸重复改善成立；整套仍未通过，不发布为可直接使用的通用TileSet。**

## 标准入口

[standard.md](standard.md)规定尺度、真实Alpha、共享接头与截面角色、板缝和边框、光照、形态覆盖、引擎与视觉双验收，以及首轮量化目标。[profiles.json](profiles.json)是可读取的试验目标，不能冒充结果。

用户要求的像素风优先于早期偏写实规范。最终单格仍128px、世界格32、层缩放0.25；未自动降回32px原图或强制16色。

## 修正结果

| 构件 | 做了什么 | 验收结论 |
| --- | --- | --- |
| 地板中心 | 从不规则细板和写实颗粒改成固定2×2板面、像素色簇，主横/竖缝64 | 实底无孔，保留为风格基准候选；用户风格认可未取得 |
| 北直边 | 从同一新中心订正北梁；首次偏薄后再定向修正，底端完全不透明 | 材质关联改善；主横缝66对中心64，仍超过1px相位筛查容差 |
| 南北窄条 | 从46px细条改为126px整格走道，同一中心板面与左右边梁 | N/S `[1,127)`宽度通过，主体连通；旧端头仅作几何对照，材质未统一，原稿主体Alpha最高251仍待修 |
| NW外角 | 首稿丢失板缝，第二次恢复四板与十字缝 | 拒收：横缝73对北边66；Alpha225～248的整格半透明背景不能充当真实角部透空 |
| 北直岸 | 重生成像素风直岸；整块方形裁框去掉两端封边 | 当前北向长直重复段视觉通过，E/W `[0,33)`在32±1px首轮范围；其他方向、角和闭环待修 |
| 池岸NW凹角 | 按缺NW真实邻域和靠格边接头重生成 | 拒收：N2px、W延伸55px；形态、截面与风格未达标 |

8次真实调用：中心1、北边2、窄条1、外角2、池岸2。直岸注册v002复用实际原稿，没有新增生图；裁框`[20,176,1234,1390]`，整块Nearest等比导出，不涂改像素或Alpha。所有原稿与失败版本保留。

## 实际验证与图片

- [6类修前/本轮对比](review/six_candidates_before_after.png)：每格128px，来源拼接，非GPU。
- [窄条接端头前后](review/narrow_width_before_after.png)：左46px，右126px，端头均为旧稿；只展示宽度改善。
- [GPU原尺度](godot-review/pixel_pilot_native_gpu.png)、[GPU世界格32](godot-review/pixel_pilot_world32_gpu.png)：实际TileMapLayer，水底与岸体独立分层。
- Godot4.7.2实际GPU，padding开启；本轮11个完整图块的180,224导入像素，Alpha与可见RGB差异均为0，所有运行阶段exit0、stderr为空。
- 本轮是手工候选诊断，**没有宣称新版47型穷举、完整自动铺刷或闭环通过**。图集中包含明确拒收样稿和旧端头，以便检视失败，不应直接作为正式笔刷库导入。
- [独立复核](independent-review.md)同意窄条宽度改善及北向直岸长段的局部结论，并拒收外角和池岸凹角。
- [冻结检查](protected-after.json)：50个共享规范、v007、主项目与课程文件，本轮变更0。

最初诊断误引用v007宽条作为“修前46px”，已替换为实际v008细条，并重新生成源图对比、图集、GPU截图和导入验证；当前图片、atlas哈希及验证报告一致。

## 来源与复现

[generation-record.json](generation-record.json)记录实际调用、原始工具路径、完整原稿、SHA256、裁框和机械导出。[prompts.json](prompts.json)保留最终使用的完整提示词及参考图，含拒收尝试。[candidate-catalog.json](candidate-catalog.json)和[review-results.json](review-results.json)分别记录来源与本轮判定。

```powershell
python art-source/ember/production-v008/correction-v001/prepare_review.py
& 'art-source/ember/production-v008/correction-v001/godot-review/run_review.ps1'
```

这两步只整理/验证现有原稿，不重新生图。独立打开`godot-review/project.godot`可查看当前手工布局；其`pilot_diagnostic_tileset.tres`含拒收对照，不作为正式资源发布。主游戏未接入本轮。

后续优先同时统一北/西边、角块和中心的板缝相位与梁截面，修正真实Alpha，再制作同风格端头及凹角。完整首批通过后再扩展47型，避免把相互不兼容的独立单块继续填入图集。
