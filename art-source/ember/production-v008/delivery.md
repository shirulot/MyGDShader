# v008 首批修正与官方铺刷诊断

**最新像素订正入口：** [连续母图颜色与风格修订 correction-v002](correction-v002/delivery.md)。用户指出颜色与风格衔接不齐后，新增同源地板四格及全新走道端头，不再把旧写实端头混入修后布局。最新GPU对照、剩余半缝/相位问题和生产状态以该修订报告为准；下文保留v008原批次历史证据。

2026-10-05。已实际生成15张原稿、登记8类候选，并完成独立Godot项目的真实GPU检查。**局部缺陷已有修正，整套视觉和接口仍未通过，完整新版47套尚未完成。** 本目录是可审阅的生产候选，不是正式资源发布包。

用户要求按“直接用来布局地图”重新审核后，结论为**不能直接使用为完整通用瓦片集**。具体阻碍、真实端口位置和后续验收条件见[直接使用审核](direct-use-review.md)；技术检查通过不能代替该结论。

## 直接看结果

- [8类旧／新同尺度对比](review/eight_samples_before_after.png)：每张128px；来源图排版，不是GPU截图。
- [地板实际GPU试铺](godot-review/initial_gpu.png)、[放大试铺](godot-review/trial_zoom4_gpu.png)：左为旧版重排基线，右为42旧＋5新样；仍有明显板缝、材质及宽度跳变。
- [池岸实际GPU分层检查](godot-review/bank_samples_gpu.png)：独立水底与静态岸沿，只有三类样稿及北向局部连接，不代表完整池岸闭环。
- [逐块来源标记](review/floor_official_layout_sources.png)、[候选清单](candidate-catalog.json)、[生成台账](generation-record.json)、[完整提示词](prompts.json)。
- [独立审核早期结论](independent-review.md)、[根代理续修自检](continuation-self-review.md)。独立报告中的北边v001／岸内角v002是当时快照，不是第三版的独立审核结论。

## 官方范式

规范引用的[官方完整47模板](https://docs.godotengine.org/en/3.5/_images/autotile_template_3x3_minimal.png)已保存至inputs；实测12×4、47唯一mask，空槽(10,1)。位序保持N NE E SE S SW W NW。红白表示邻接条件，不是精确美术剪影。

Godot4按[Match Corners And Sides及Terrain Peering Bits](https://docs.godotengine.org/en/stable/tutorials/2d/using_tilesets.html#creating-terrain-sets-autotiling)配置。official目录有旧版47完整块重排基线，以及42旧＋5新样的混合诊断图集。每格登记真实来源、原坐标和哈希；只移动完整128px图块，不涂模板轮廓、拼材料碎片或旋转光照。

## 当前候选

“采用”仅表示纳入自检，未通过正式接口、整体美术或用户验收。

| 构件 | mask | 当前原稿 | 修正与限制 |
|---|---:|---|---|
| 地板中心 | 255 | floor_center_v001 | 满实底无孔，蓝灰金属；板缝与相邻块不同。v007中心原本也已无Alpha孔，不重复声称旧孔未修。 |
| 北外边 | 124 | floor_edge_N_v003 | 完整RGB实底，消除v002南侧Alpha渐隐、v001裁切后半黄铜；北梁偏薄，板缝／梁宽待统一。 |
| 地板西北外角 | 28 | floor_outer_NW_v001 | 自然制造倒角，N/W外露、E/S开放；与直边梁宽有差异。 |
| 地板西北凹角 | 127 | floor_inner_NW_v002 | 真正NW局部开口，无内部圆孔；去掉两颗重复黄铜，接缝仍不一致。 |
| 南北窄条 | 17 | floor_narrow_NS_v002 | 中央完整走道、左右透明，N/S贯通；新约46px端口与旧约126px端头不匹配。 |
| 北池岸 | 124 | bank_straight_N_v001 | 整体注册后约30px总厚；暗立面比例仍待美术审查。 |
| 池岸外角 | 28 | bank_outer_NW_v002 | 横竖总岸宽约31/32px，方向厚度改善；接口仍不同。 |
| 池岸凹角 | 127 | bank_inner_NW_v003 | 连续弧形岸带，N/W各32px主体端口，E/S透明；跨度约半格，弧口位置及其他方向待统一。 |

15次实际调用：中心1、其他地板8、池岸6。全部未经缩小的原始生成字节、提示词、拒收原因保存至raw和生成台账；子目录源文件亦保留。北边v002因南侧渐隐拒收；池岸凹角v001/v002因短L／悬空端口拒收。第三版未通过程序填Alpha或复制接口像素伪造通过。

## 验证结果

- Godot4.7.2真实GPU；纹理128、世界格32、TileMapLayer缩放0.25、Atlas padding开启。
- 两份地板各穷举256邻域，共512邻域、10,300格；随机绘制／擦除及全部47合法mask选择失败0。
- 地板两图集各786,432像素、池岸49,152像素的导入Alpha／可见RGB差异为0。
- 引擎视口模拟左画、右擦、滚轮缩放，保存5张地板GPU读回；另保存1张池岸GPU读回。当前运行阶段exit0、stderr为空，报告位于godot-review。
- [10对实际样稿接口](interface-observations.json)仍是**0/10严格RGBA相等**。主体连通和正确选块不能替代接口及视觉验收。
- review还包含中心、长北边、L、凹洞、窄条、擦除收口的128px来源试铺；其他方向沿用v007，明确不计新版全方向美术。
- [冻结检查](protected-after.json)：50个v007、共享规范、项目入口及课程进度文件，变更0；主游戏与课程Shader未接入本批。

## 可操作试铺与复现

将godot-review/project.godot作为**独立项目**打开，运行review.tscn。左画、右擦、滚轮缩放、中键平移、R重置。它用于审查混合候选，不是已定稿的新美术库。

在工作区根目录顺序执行以下命令可重做当前整理及检查，不重新生图：

```powershell
python art-source/ember/production-v008/floor/export_candidates.py
python art-source/ember/production-v008/register_bank_v003.py
python art-source/ember/production-v008/collect_delivery.py
python art-source/ember/production-v008/prepare_official_floor.py --with-samples
python art-source/ember/production-v008/render_cpu_trials.py
python art-source/ember/production-v008/godot-review/prepare_inputs.py
python art-source/ember/production-v008/prepare_bank_gpu.py
& 'art-source/ember/production-v008/godot-review/run_validation.ps1'
& 'art-source/ember/production-v008/godot-review/run_bank_capture.ps1'
```

第三版登记脚本保留本机工具输出的实际路径；原稿副本也完整保存在工作区。规范chat可从本文件与候选目录接收审核。

## 尚需修正

继续统一地板梁宽、板缝尺度及窄条与端头／T／角的端口宽度，再修颜色与Alpha接口；池岸需统一凹角弧口位置和其他方向。首批接口与视觉尚未通过，依据交接要求暂不扩展47张新版美术、不把混合诊断发布为正式修复版。墙面轻微亮度差等项仍按原交接排期。
