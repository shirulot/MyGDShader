# 池岸像素风有限修正结果

日期：2026-10-05。按 correction-v001/standard.md 执行，使用 imagegen skill 与内置 `image_gen.imagegen`，实际调用 **2 次，已停止追加生成**。

本轮只写 `art-source/ember/production-v008/correction-v001/bank/`。旧 v008、共享规范、正式资源没有修改。最终诊断纹理仍为 **128×128px**，世界格32、层缩放0.25；`world32` 仅为普通游戏显示尺度的诊断图。

## 结果

| 构件 | 量化检查 | 视觉与语义检查 | 登记 |
| --- | --- | --- | --- |
| 北直岸 `bank_straight_N_pixel_v001` | E/W 主体均 `[0,32)`；主体8邻域单一连通，4093px | 像素簇和少量金属明暗比旧稿清楚，但左端白亮竖边、右端暗封边仍在；重复会出现端封边，不能当作贯通接头 | 仅作诊断对照，生产拒收 |
| 整体注册 `bank_straight_N_pixel_registered_v002` | E/W 主体均 `[0,33)`；比32px目标多1px，在首轮筛查容差内，未达到严格32px | 指定方形裁框裁去连续开口端20px封边后，明显端封边消失，RGBA差异减小；仍需GPU与视觉审核 | 替代为当前北直岸诊断候选，生产未采用 |
| NW凹角 `bank_inner_NW_pixel_v001` | 原稿四边均无 `Alpha>127` 主体接点；整体注册后 N=`[0,2)`，W=`[0,18)+[19,55)`，E/S无主体 | 仍是带长压顶与封端的角块；截面没有与直岸匹配，细碎写实颗粒回流 | 拒收 |

直岸重复接口的128个采样中，有32个可见RGBA不一致，6个Alpha不一致；Alpha最大差27，可见RGB最大差184。此数值用于定位差异，拒收同时依据原稿与4倍图中可见的端封边。直岸顶边最外排在三处板缝各缺1px，主体下方仍连通；没有补Alpha。

根代理随后指定唯一一次机械注册诊断：对同一原稿使用 `[20,176,1234,1390]` 的1214px方形裁框，再Nearest等比导出128。原稿与v001候选均保留。v002的重复接口仍有33个可见RGBA差异、4个Alpha差异，但Alpha最大差降为4，可见RGB最大差降为47。端封边已明显改善，数值不等不单独作为否决依据；不宣称无缝，交根代理GPU与视觉检查。`result.json.straight` 现在登记v002，`straight_v001_preserved` 保留v001结果。

凹角与西邻的新北直岸配对时，W端跨度延伸到55px，N端仅2px，明显不能匹配32px截面。没有通过缩小整块、改变裁框切去构件或局部修边伪造接口。

## 正确邻接案例与覆盖限制

`review/missing_NW_neighborhood_cpu_before_after.png` 是 **CPU诊断拼接**。中心是mask127；3×3水域只缺NW对角，N邻格是西直岸，W邻格是北直岸。N邻格读取旧v007的mask31西直岸，W邻格使用本轮注册v002北直岸。mask17是双岸窄通道，未误当作西直岸。

旧西直岸向南接口实测 `[1,26)`，只作为实际方向与位置的诊断，并不计作新版材质或32px宽度通过。没有旋转带定向光照的块，也没有闭环池岸、全方向覆盖或Godot铺刷通过宣称。根代理将统一执行GPU检查。

## 导出与可追溯文件

两张工具原稿都为1254×1254，项目 `raw/` 副本与工具原文件SHA256一致。所有完整提示词、参考顺序、原始工具路径、原稿/候选SHA256及裁框见 `prompts.json`、`generation-record.json` 和 `result.json`。

| 构件 | 方形裁框，XYXY右下不包含 | 等比导出 |
| --- | --- | --- |
| 北直岸 | `[0,176,1254,1430]` | 1254→128，Nearest |
| 北直岸注册v002 | `[20,176,1234,1390]` | 1214→128，Nearest |
| 拒收凹角 | `[65,68,1319,1322]` | 1254→128，Nearest |

v001裁框包含完整可见构件；v002只对连续直岸整体裁去两端20px封边，仍是单张方形裁框和等比缩放。画布外区域由裁切操作补透明留白。没有代码绘制美术、Alpha阈值清理、局部拉伸、材质碎片拼接、边缘复制、旋转或镜像。原稿中微弱Alpha散点仍完整保存在 `raw/`，登记实际透明范围。

- 原稿：`raw/bank_straight_N_pixel_v001.png`、`raw/bank_inner_NW_pixel_v001.png`
- 128px诊断：`candidates/bank_straight_N_pixel_v001_128.png`、`candidates/bank_inner_NW_pixel_v001_128.png`
- 当前北直岸注册诊断：`candidates/bank_straight_N_pixel_registered_v002_128.png`；4倍预览 `review/bank_straight_N_pixel_registered_v002_4x.png`
- 单块4倍图：`review/bank_straight_N_pixel_v001_4x.png`、`review/bank_inner_NW_pixel_v001_4x.png`
- 8格长直段旧/新：`review/north_repeat_before_128.png`、`review/north_repeat_after_128.png`
- 普通世界格显示：`review/north_repeat_before_world32.png`、`review/north_repeat_after_world32.png`
- 真实缺NW邻域旧/新：`review/missing_NW_neighborhood_cpu_before_after.png` 及 `_2x.png`
- 候选坐标与状态：`candidate-catalog.json`
- 实测与来源：`generation-record.json`、`result.json`
- 全部提示词：`prompts.json`、`prompts/*.txt`

可复现机械导出和测量：

```powershell
& 'C:\Users\shiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'art-source\ember\production-v008\correction-v001\bank\prepare_candidates.py'
```

本轮改善是直岸像素簇、v001的32px端口落位，以及v002机械注册后的端封边去除。当前v002仍为33px宽诊断候选，凹角拒收，尚未形成可生产接入的无缝池岸。原稿完成、整理与测量完成；GPU待根代理，用户视觉认可未取得，完整套未完成。
