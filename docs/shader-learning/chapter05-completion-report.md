# Chapter 05 完成报告

- 章节：Noise、阈值与溶解，Phase 2。
- 教学日期：2026-10-06～2026-10-07（Asia/Irkutsk）；报告日期：2026-10-07。
- 来源 Chat：`Chapter 05：Noise、阈值与溶解`，`01a1114c-7359-7370-9045-ff4102b73dcd`。
- 章节教师验收：`COMPLETED`，05.1～05.3 核心实验与解释通过，提示和参考使用另列。
- 总进度：供统合者核对后更新；本报告不修改 `progress.md` 或长期画像。
- 交接状态：2026-10-07 用户明确要求通知统合者后，已通过应用消息发送给 `godot-shader 教学统合者`（`01a0b9b7-0db1-71b1-bd98-f313ba43cfdd`）；工具确认发送成功，统合核对与状态登记尚未由本教师确认。
- 游戏应用：05.1～05.3 均仍为 `PLANNED`，无玩家事件或生命周期接入证据。

## 实际完成的 Section、实验和效果

| Section | 实际完成内容 | 当前保存实现 | 验收依据 |
| --- | --- | --- | --- |
| 05.1 | 低频/高频 PNG 对照、中心采样缩放、越界钳制与重复、实际使用 NoiseTexture2D/FastNoiseLite、频率与对比度观察、粗细输入选择 | observer 的有效缩放使用中心 `/scale`；采样灰度以 0.5 为中心调整对比度并钳制到 0～1；最终显示内建 Noise | 用户描述边缘延长线、重复变化、频率提高后更密集；修正采样通道后确认对比度变化；选择低频大块用于云轮廓、密集扰动用于细节 |
| 05.2 | 固定阈值不规则显隐、0～1 进度、全显/全隐端点、Alpha Mask 与 discard 裁切比较 | 当前成品使用下阈值 step、进度 1 强制全隐及 discard；此前 Alpha 版本由用户完成并运行比较 | 用户描述“不规则的切开了，切口是透明的”，按给定端点目标回复“好了”，确认 discard 版本有效；等值边界风险修正后读取保存代码通过 |
| 05.3 | 双阈值白带、进度加独立边宽、橙黄色边带、smoothstep 柔和 RGB 过渡、进度 0 原色完整性、边带职责解释 | 实际实现在 05.2 文件中；下阈值决定显隐，上阈值为进度加宽度；用平滑上升权重将边色混回原色；Alpha 保留原图 | 用户拖动进度联想到常见游戏消失特效；多次正常运行确认；最终混色顺序审查正确；宽度改变不会使灰度 0.45 重新显示的解释通过 |

05.3 的独立场景/Shader 曾由教师准备为复用起点；用户实际继续编辑了 05.2。因此完成作品入口是 05.2 场景，不能把 05.3 起点文件列为已完成边带作品。主体显隐仍为硬裁切，柔和过渡作用于 RGB；当前完成的是亮色边带，没有新增光晕或照明配置。双色边缘与 Ramp 为可选内容，未开展，不作为核心收尾阻塞。

## 最终参数与输入契约

### 05.1 观察器

- `scale`：0.01～2，默认 1，正数；使用中心除法采样，增大参数会放大已有纹理的可见图案。它控制读取范围，不重新生成 Noise。
- `contrast`：0～2，默认 1；以灰度 0.5 为中心调整，再钳制到 0～1。
- 当前场景保存 `scale≈0.6`、`contrast≈1`；线性过滤、Repeat Enabled；256×256 纹理按 2 倍显示。
- 内建资源：256×256 NoiseTexture2D、FastNoiseLite seed 7、frequency 0.08、默认 Smooth Simplex、无分形；无 mipmap、seamless 开启、normalize 默认 true。
- `noise_scale` 未参与当前输出，旧起点注释也未完全更新；均属可选整理。

### 05.2 与 05.3 合并成品

- 底图：独立机器人 RGBA 帧，64×96，Sprite2D 按 4 倍显示；保留其原 Alpha 轮廓。
- `noise_texture`：独立内嵌 256×256 NoiseTexture2D；FastNoiseLite seed 7、frequency 0.02、无分形；normalize 默认 true、seamless 默认 false、无 mipmap；Shader 采样为线性过滤、不重复。灰度数据读取 `.r`，不加 `source_color`。
- `dissolve_progress`：0～1，默认 0；增大参数使更多位置被裁掉。0 为完整原色及原 Alpha，1 为全隐；中间进度保留灰度大于等于进度的位置。
- `edge_width`：0.01～0.2，默认 0.05，单位为 Noise 灰度跨度；不是固定 UV 距离或像素厚度。当前选择正宽度，未提供零宽度关闭接口；以后脚本驱动也须维持正宽度。
- `line_color`：可调 `vec3` RGB，默认 `(1, 0.55, 0.1)`；已在材质中保存为 Vector3。尚无 `source_color` 提示，当前是向量编辑接口，不冒称标准颜色选择器已完成。命名有效，不要求改成 `edge_color`。
- 边色混合只改变 RGB，最终 Alpha 为 `origin.a`。进度 0 不参与边色分支；进度 1 在输出前全部 discard。
- 最终材质保存进度约 0.5、边宽约 0.1、橙黄色边色。此时灰度区间 `[0.5, 0.6)` 参与颜色过渡；灰度 0.45 被丢弃，0.55 约半混色，0.7 保持原色。
- 边宽为 0.05 时对应 `[0.5, 0.55)`。最后回答中的“0.5～0.55”按这个宽度澄清；加宽只抬高色带上阈值，不能恢复下阈值以下的像素。

Noise 正方形输入映射到非方形机器人 UV，未做等比例细节修正；初始溶解练习接受此映射，不将其宣称为各方向均匀的物理尺度。

## 能解释和实现的内容、提示边界

- 效果核心由学习者写入；教师准备当前小步所需的节点、材质、纹理绑定和默认采样起点，05.3 起点仅复用用户已经完成的显隐逻辑，未预写新边带。
- 05.1：用户独立采用已有中心 `/scale` 方案，教师接受其与乘法采样尺度的对应关系；能观察频率和采样尺度的视觉相似性。灰度对比度经过文字方法及局部采样参考完成，不登记无提示公式推导。
- 输入选择：用户明确说明低频大块适合云表面轮廓；第二项“密集扰动”较简短，细节用途由教师补足，不夸大为用户已独立完整论证两类信号和成本。
- 05.2：用户写入 step、进度参数、Alpha 乘积、全隐端点分支及 discard。discard 是新语法，提供过局部 API 说明；全隐分支是在等值边界提示后完成。
- 05.3：用户按双阈值方法写入白带及进度加边宽；自行保留原色主体、使用 if/else、将最小边宽设为 0.01，并加入进度大于 0 才染色的条件。这些是有效选择。
- 柔色带使用过三行局部参考及单行 mix 方向修正；最终通过的是参考、数字说明和排错后的有效实现，不登记为无提示独立推导 smoothstep 组合。
- 最后用户回答：“不会 宽度是+所以会现实的是0.5-0.55的部分 而且那部分还是混色不能完全算本机色”。可确认其理解：边宽加在上阈值，不会改变被下阈值丢弃的位置；边带内是颜色混合。当前 0.1 边宽的上界由教师再次澄清为 0.6，不据此登记所有数字例子均无提示通过。

## 典型错误与排错过程

1. 05.1 曾将坐标 `scaleUv.r` 当作采样灰度，结果是左黑右白的坐标渐变。解释 `.r` 与 `.x` 都是第一个分量，意义取决于变量；将输入改为采样颜色 `origin.r` 后修正。`vec3(一个数)` 用于将同一个灰度写入 RGB。
2. frequency 与采样 scale 看起来相似是有效观察。教师区分了“生成数据时改变频率”和“读取既有数据时改变坐标范围”，保留用户的除法缩放实现。
3. `step(progress, noise.r)` 的等值情况返回 1；进度 1 遇到灰度恰好为 1 有残留的静态风险。用户加入进度大于等于 1 强制权重 0。没有观察证据表明用户实际看到残留，不把风险当成已发生故障。
4. 双阈值第一版以上阈值参数 0.55 配合进度 0.5，固定位置白带有效；改为进度加独立宽度后完成跟随关系。
5. 第二个 step 改 smoothstep 后仍用差等于 1 筛选颜色，会排除中间权重；另曾把全局进度用于 mix，使整条带共享混色强度。用具体位置的权重与全局进度对照，并给局部参考。
6. 用户明确说明一次检查版本“刚刚代码我回退过头了”。教师重新读取，不将此前版本继续作为当前实现。随后当前版使用 smoothWeight 但颜色方向反向；只交换 mix 两个颜色参数，保留其有效 if/else。此原因只用于此次版本说明，不推广为长期操作习惯。
7. 最后解释中先把三个位置的 Noise 灰度说成消失范围逐渐变化。澄清进度固定、灰度来自不同位置后，用户给出宽度不会恢复已丢弃像素的正确理由。列为后续实际复用时的短查项，不追加整章重学。

## 使用或新增的资源及来源

| 资源 | 本章用途 | 来源与边界 |
| --- | --- | --- |
| [noise_low_v001.png](E:/dev/shader/godot-shader/godot-shader-simple/assets/ember/data/noise/noise_low_v001.png)、[noise_high_v001.png](E:/dev/shader/godot-shader/godot-shader-simple/assets/ember/data/noise/noise_high_v001.png) | 低频大块与高频细碎观察 | 已登记 D04、256×256 L、`GENERATED_IN_PROJECT`；种子 240410/240411，周期频段 1～4/10～24；周期余弦叠加测试数据，不冒称 Perlin/FastNoiseLite |
| [ch05_01_builtin_noise.tres](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter05/ch05_01_builtin_noise.tres) 与 05.2 场景内嵌 Noise | 实际学习 NoiseTexture2D/FastNoiseLite，驱动溶解 | 本章建立的 Godot 内建资源；已有 PNG 没有替代内建资源教学 |
| [robot_idle_down_v001.png](E:/dev/shader/godot-shader/godot-shader-simple/assets/ember/characters/robot/robot_idle_down_v001.png) | 溶解、边带、原 Alpha 轮廓 | 项目 AI 母稿经原生像素整理，不是 CC0；当前 v003 组合仍复用此独立帧，避免图集/动画引入额外概念 |

来源依据：[资源计划](E:/dev/shader/godot-shader/godot-shader-simple/docs/shader-learning/resources.md)、[技术输入 catalog](E:/dev/shader/godot-shader/godot-shader-simple/assets/ember/data/technical_inputs_catalog_v001.json)、[生成器](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/technical-inputs-v001/basic/generate_basic.py)、[机器人 catalog](E:/dev/shader/godot-shader/godot-shader-simple/assets/ember/characters/robot/robot_frames_catalog_v003.json)。本章没有新生成 PNG、下载外部素材或引入课程 GDScript。

## 关键文件与完成作品入口

- 05.1：[Shader](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter05/ch05_01_noise_observer.gdshader)、[场景](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter05/ch05_01_noise_observer.tscn)、[内建 Noise](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter05/ch05_01_builtin_noise.tres)。
- 05.2＋05.3 合并成品：[Shader](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter05/ch05_02_noise_dissolve.gdshader)、[场景](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter05/ch05_02_noise_dissolve.tscn)。在 Godot 打开该场景，用 Inspector 调进度、正边宽与边色向量。
- 仅为复用起点：[05.3 Shader](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter05/ch05_03_dissolve_edge.gdshader)、[05.3 场景](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter05/ch05_03_dissolve_edge.tscn)。它们没有承载最终边带实现，不作为另一份验收作品。
- 当前 05.2 文件已包含 05.3；早期 Alpha、硬白带等验证依据在教学过程，不宣称所有中间版本都保留为可切换档案。旧起点注释可选整理，不为结课回改。

## 游戏应用场景、触发/状态与参数接口

| Section | 待接入游戏用途 | 已有实验接口 | 应用还需验证 |
| --- | --- | --- | --- |
| 05.1 | 火焰/烟轮廓与水纹的不同 Noise 尺度 | Noise 输入及生成 frequency、采样 scale、contrast | 在实际设备上比较信号与成本；未实现火焰/水系统 |
| 05.2 | 代理失败、设备关停与站点冷却消散 | 0～1 dissolve_progress、noise_texture | 游戏状态决定开始/结束及伤害时机，Shader 仅显示；结束隐藏、重复触发、重开恢复尚未接线 |
| 05.3 | 溶解边带与能量色带 | 正 edge_width、line_color RGB，与进度分开 | 材质实例隔离、能量事件映射、结束/重试无残留尚未验；未来驱动须遵守正宽度和灰度输入契约 |

依据：[游戏路线](E:/dev/shader/godot-shader/godot-shader-simple/docs/shader-learning/game-project.md)、[全效果覆盖矩阵](E:/dev/shader/godot-shader/godot-shader-simple/docs/shader-learning/game-effect-coverage.md)。用户说“感觉这个特定情况下可以做消失特效”并在边带阶段联想到常见游戏效果，是用途联系证据，不代表事件驱动已实现。

## 运行证据与验证限制

- 视觉证据来自用户各小步“好了/符合预期”、不规则透明切口描述，以及“太酷了 我试着拖动了一下 就是游戏里常见的消失特效”。按正常运行确认处理，不编造次数、时长、截图或全部参数组合。
- 教师逐次读取实际保存 Shader 与材质参数；最终读取到进度约 0.5、边宽约 0.1。单独改变边宽的目标已给出，用户最终解释裁切阈值不受它影响；不把预测性回答写成额外 GPU 测量。
- 本章早先用已安装 Godot 4.7.2 stable Steam 直接核对内建 Noise 生成、纹理尺寸/属性及机器人采样连接；该工具检查不代替用户视觉运行。一次临时探针因 GUI 进程等待方式未完成便被清理，改为隐藏进程并等待退出后成功；这是工具流程修正，不是学生代码错误。
- 未做 GPU 性能实测。Alpha 与 discard 的二值画面可以相似，不能因此宣称机制相同或 discard 更快。3D 深度预通过的性能说明不直接套到本次 CanvasItem。
- 游戏应用运行证据：无，三项仍 `PLANNED`。未修改 C01～C04、M0、主入口、`project.godot`、渲染器或素材生产目录；不以本章结课替代旧游戏应用验收。

## 建议复习与后续课程调整

- 下次实际使用 Noise 时短查：正在改变生成频率，还是读取坐标范围；`.r` 来自坐标还是采样颜色。
- 下次组合软边/混色时短查：权重是二值还是连续值，mix 两个颜色的方向，参数是否为全局进度或当前位置的效果权重。
- 数字题明确标出“Inspector 参数”和“某位置采到的数据”，避免把多个灰度样本读成进度序列；短查即可，不重开整章。
- 在脚本驱动前核对 normalize 灰度范围、正宽度合同、材质实例和重开复位；这些是未来应用验证，不追加到本章实验。
- 推荐后续主线：Chapter 06：Distortion 与采样风格化，复用本章 Noise 数据；是否插入游戏接入/短复现及新 Chat 由统合者决定。本 Chat 未开始或创建下一章。

## 长期需求/习惯反馈

- **章节 / 日期 / 来源 Chat：** C05 / 2026-10-06～2026-10-07 / `Chapter 05：Noise、阈值与溶解`（`01a1114c-7359-7370-9045-ff4102b73dcd`）。反馈协议依据 [learner-preferences.md](E:/dev/shader/godot-shader/godot-shader-simple/docs/shader-learning/learner-preferences.md)。
- **新增或再次确认的明确偏好（原话与上下文）：** 教学过程中无新增独立长期偏好要求，沿用现行规则。本章有直接教学反馈：“说到底 5.1你到底教了什么 感觉最奇怪的一章 还是说继续的话我就能明白呢”。上下文为完成 Noise 输入、尺度、重复、频率与对比度后，用户仍不清楚目的联系。该证据支持教师改进用途说明，不据此归纳用户不喜欢理论或不能理解抽象概念。结课后用户再次确认交接需求：“你不应该自动通知统合者么 还是说本章没完成？”上下文为教师已保存报告但尚未发送；本次按该明确要求补发给统合者，供其将结课主动同步的期望纳入后续交接流程。
- **有效教学方式与应避免方式：** 05.1 的参数小步过多、联系效果用途讲晚，导致观察像分散的调参任务。教师用 C04 灰度权重连接 Noise 显隐后，用户同意进入 05.2；05.3 又明确说“太酷了 我试着拖动了一下 就是游戏里常见的消失特效”。建议先交代当前输入将控制哪个可见效果，再拆小步。对 `.r` 和连续权重使用具体数字与局部参考，保留用户有效实现；避免只要求更换函数而忽略下游权重处理与颜色方向。
- **旧规则修订 / 撤销 / 适用范围变化：** 无撤销。“一次一个小目标”继续有效，但不能把一个清楚目的拆成没有联系的一长串调参；这是教师方法补充，不是用户新授权减少知识覆盖、代写核心或自动跨 Section/Chapter。
- **仅本章观察、待确认项：** 坐标/采样灰度、生成 frequency/读取 scale、全局进度/局部边色权重及 mix 方向需要过提示；最后固定进度与灰度样本的区分经过澄清。柔边使用过局部参考，不记无提示推导。一次回退原因由用户明确说明“回退过头”，仅记录该次事实，不泛化为操作习惯。没有证据推断数学能力、耐心或一律偏好短说明。
- **下一章可执行调整：** 每步先写一句用途和具体可见目标；熟悉采样/混色先给精确文字需求，Noise 改采样坐标等新概念及时讲输入输出。数字例子标注参数、样本、单位；把生成参数、采样坐标与输出职责分开。更换 step/smoothstep 时明确判断和输出哪些保留、哪些同步改变。审查先读最新保存文件；允许有效 if/else、命名和正宽度选择，通过同节小步再推进。
- **统合处理：** 待核对。建议将目的先讲、再拆小步纳入教师方法改进；连续权重、样本/参数区分和参考依赖仅作为近期复习证据。没有新的永久能力判断。本 Chat 不直接更新总进度或长期画像；已按结课后的用户明确要求，将报告路径、验收结论与证据边界发送给统合者。发送成功不等于统合者已完成核对或登记。
