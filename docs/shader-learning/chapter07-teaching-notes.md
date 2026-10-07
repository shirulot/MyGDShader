# C07 教学过程记录

- 日期：2026-10-07（Asia/Irkutsk）。
- 来源 Chat：`01a116db-f9ab-7f92-9627-032d9b181488`。
- 范围：本章独立 Shader 实验；不修改 M0、总进度或长期画像。
- 当前：07.1 首轮 Alpha 读数观察待学习者实现、运行与审查；07.2/07.3 未开始。

## 已准备与核对

- 已读取 requirements.md、learner-preferences.md、curriculum.md 的 C07、progress.md、resources.md、handoff-protocol.md，以及 game-project.md / game-effect-coverage.md 的本章应用行。
- D05 复用 `assets/ember/data/calibration/alpha_edge_test_v001.png`：128×128 RGBA、Alpha 0～255，SHA256 与 technical-input catalog 一致。来源 `GENERATED_IN_PROJECT`，生成源 `art-source/ember/technical-inputs-v001/basic/generate_basic.py`；没有重新生成素材。
- 左侧主体含透明椭圆孔洞；右上纵线及右中横线各宽 1 源像素；底部渐变从左透明到右不透明。本章读取 `.a`，不套用 catalog 通用 `.r` 备注。
- 非零 Alpha 包围框为 `[12,12,117,120)`，四边透明；最少留边为底部 8 源像素。此事实不保证任意宽度外光均不裁切。
- 已建立 `scenes/chapter07/ch07_01_alpha_outline.tscn` 和同名 `.gdshader`：背景节点、独立 ShaderMaterial、Sprite2D 居中、scale=4、Nearest、Repeat Disabled。Shader 只含原 UV 的一次完整 RGBA 采样。
- Godot 4.7.2 headless 加载该场景、运行 2 帧后退出码 0，无报错。这是场景启动检查，不是肉眼效果验收或 GPU 性能测量。

## 首轮目标与提示边界

- 用原点采样的 Alpha 作为 RGB 的共同灰度，最终输出 Alpha 固定 1，使全透明区域也能显示黑色读数。
- 预期：原不透明部分白色，孔洞/外留边黑色，孤立细线白色，底部渐变黑→灰→白。
- 保留原始 UV 和原点采样，只替换输出；本轮不引入邻域、四方向组合或最终描边。
- 教师提供文字目标与数值含义，没有写入 Alpha 观察/描边答案；学习者保存并报告正常运行后，再读最新文件审查。
- 同节小步通过后继续一个方向、1 源像素邻域；Section 切换仍由学习者确认。

## 待续与证据

- 07.1 尚无学习者实现或运行证据，不登记掌握；后续保留四方向、可调宽度、孔洞、细线、半透明边和单位说明。
- 07.2 保留两层描边/假柔光、核心/外层 Alpha 职责与静态采样计数；07.3 保留三种强调及独立材质实例。
- 本章全部真实游戏应用仍待独立游戏教学验证，本次没有事件/状态接口或重开验收。
- 当前无新增长期偏好证据，沿用 learner-preferences.md 完整九条及 C04～C06 方法改进。
- 结课报告须包含七字段习惯反馈；核心及既有确认完成后，发送前核验 handoff-protocol.md 指定人类授权与接收方，再向统合者自动回报一次。起点准备不触发结课发送。
