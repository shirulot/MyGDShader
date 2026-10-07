# Chapter 03 完成报告：时间动画与程序图案

- 日期：2026-10-06（Asia/Irkutsk）；教学期间：2026-10-04～2026-10-06。
- 章节状态：`COMPLETED`（章节教师评估，交由统合者核对登记）。
- 完成的 Section：03.1、03.2、03.3，全部主练习及原概念标准通过。
- 本 Chat 未修改 `progress.md` 总状态，未启动 C04；实验完成与游戏应用分别报告。
- 验证方式：学习者正常运行确认与教师读取最新保存逻辑。按学习者明确约定，“好了／写完了”及写后代码审查按其已正常运行处理，不重复询问同一效果，不补造特定组合、时长或测量次数。03.2／03.3 的默认起点场景曾通过本地 Godot 4.7.2 headless 加载检查；周期数字来自公式推算。

## 实际完成的实验和效果

| Section | 已完成效果及当前保存状态 | 原标准证据 |
| --- | --- | --- |
| 03.1 TIME、速度与周期运动 | 时间驱动横向纹理偏移、最终 UV 越界补黑；RGB 呼吸系数 0.3～1.0，保留原 Alpha。移动材质当前速度约 0.23，呼吸最终使用 robot v002 的 AnimatedSprite2D。 | 学习者报告向左移动、右侧变黑、明暗循环；解释每秒 0.1→0.2 UV 为速度翻倍。范围映射经说明与修正后实现，在 03.3 又正确复用。 |
| 03.2 fract、mod 与重复单元 | 四次灰度渐变、可调重复密度、fract/mod 等价对照；最终为单元末尾约 10% 的移动白色扫描线。材质当前重复 8 次、向左约 0.1 UV/秒。 | 学习者解释取小数实现单元重复，并联系 HSV 色相回绕；重复参数曾保存为 10，随后保存为 8，写后运行确认；正确将位移置于密度缩放之前。 |
| 03.3 step、smoothstep 与边缘控制 | 曾分别编写并保留注释的 step 硬切和 smoothstep 柔边，完成双边界参数化；最终为四条静止、同步的双侧柔边脉冲条带，中心亮度 0.3～1.0，周期约 6.28 秒，原 Alpha 保留。最终文件使用 smoothstep 脉冲，历史 step 对照已由教师读取并记录。 | 自行选择 step 作硬边、smoothstep 作软边；正确解释两个边界、区间内递增与权重相乘。本节最后纠正柔边宽度和纯亮区域的区别并明确确认。 |

最终脉冲轮廓采用学习者的有效调整：每单元 0.2～约 0.45 渐亮，约 0.45～0.55 保持中心亮度，约 0.55～0.8 渐暗，其余为黑色。两个权重相乘再乘时间明暗系数。输入采用程序局部 UV；渐变纹理在最终版本用于默认采样与 Alpha，不能登记成已完成纹理灰度 Mask 处理。

## 能独立解释和实现的内容、提示程度

| 部分 | 独立性与提示边界 |
| --- | --- |
| TIME 偏移与速度 | 讲清 TIME 含义和目标后，学习者自行编写偏移、速度 uniform、最终坐标采样及边界处理，并正确解释速度翻倍；教师未代写效果文件。 |
| 首次 sin 呼吸与范围映射 | 03.1 使用完整呼吸参考、数学说明和局部 RGB／Alpha 修正。不能登记 sin 首次独立推导、完全独立任意范围映射或精确周期调节。后续正确复用属于已学方法的应用。 |
| fract／mod 与移动扫描线 | 概念说明、数值例子及局部公式／代码参考后由学习者写入；最后用 if/else 收窄扫描线只给文字条件，由学习者编写。不能登记整个效果从未获得代码提示。 |
| step／smoothstep 对照、参数与脉冲组合 | 学习者说明以前学过，教师仅给简要概念与明确数值目标，没有提供此节实现代码。学习者自行编写两版、参数化、双侧过渡相乘、局部坐标重复与周期 RGB 组合。周期范围沿用 03.1 已有参考知识。 |

学习者可解释：TIME 和 UV/秒的含义；单元内 0～1 坐标与重复密度；fract 和周期为 1 的 mod 的关系；step 的硬切与 smoothstep 的平滑过渡；两个边界分别为开始、结束，低于下界为 0、高于上界为 1；本例两个权重相乘保留重叠亮区。

边界解释的最终确认：将第一条曲线的结束值从 0.45 改为 0.35、开始值保持 0.2，过渡宽度由 0.25 变为 0.15；第二条曲线不变时，纯亮中心向左扩大。学习者确认“是的，会扩大，因为 1 的范围变大了，我理解”。无需重学本节或追加补跑。

## 典型错误、排错及待加强

- 曾把最低亮度要求理解成改变 Alpha；经说明和局部修正后改为 RGB 缩放、原 Alpha 保留，后续实现保持正确。
- 柔边最初使用固定 0.4／0.6，按明确目标补成可调边界；单条柔边最初使用整幅 UV，再自行补上四次重复的局部坐标。
- 曾把柔边结束值提前概括为“白光变小”；随后区分过渡缩窄与纯亮中心扩大，并明确确认。
- 继续在实际复用中短查范围端点／跨度、空间重复密度与时间速度的区别、柔边宽度与中心区域大小的区别。参考使用和独立推导继续分开记录，不因此重开整章。
- C02 已延期的矩阵推导仍由独立数学补课处理，本章完成不代表该事项完成，也不降低后续坐标／空间标准。

## 未做的可选项目

- 03.1：暂停、恢复相位及周期调速深化。
- 03.2：双色棋盘挑战。
- 03.3：抗锯齿边缘对比。

这些不作为本章核心完成的阻塞。原游戏应用矩阵中的棋盘校准等具名用途仍须安排，不能因实验挑战可选而永久取消实际应用覆盖。

## 关键文件路径

| 实验 | 场景 | Shader |
| --- | --- | --- |
| 03.1 时间移动 | [ch03_01_time_uv.tscn](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter03/ch03_01_time_uv.tscn) | [ch03_01_time_uv.gdshader](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter03/ch03_01_time_uv.gdshader) |
| 03.1 呼吸 | [ch03_01_breathing.tscn](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter03/ch03_01_breathing.tscn) | [ch03_01_breathing.gdshader](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter03/ch03_01_breathing.gdshader) |
| 03.2 扫描线 | [ch03_02_repeat.tscn](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter03/ch03_02_repeat.tscn) | [ch03_02_repeat.gdshader](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter03/ch03_02_repeat.gdshader) |
| 03.3 脉冲条带 | [ch03_03_edges.tscn](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter03/ch03_03_edges.tscn) | [ch03_03_edges.gdshader](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter03/ch03_03_edges.gdshader) |

教师仅准备独立场景、资源与材质连接，以及只含默认采样的 Shader 起点；关键效果由学习者写入。保留学习者的 AnimatedSprite2D、乘法组合、参数命名和有效轮廓选择，未为形式清理旧参数或改动主场景、C02 或 M0 代码。

详细过程与最新教学偏好见 [chapter03-teaching-feedback.md](E:/dev/shader/godot-shader/godot-shader-simple/docs/shader-learning/chapter03-teaching-feedback.md)；03.1 历史检查点见 [chapter03-section01-checkpoint-report.md](E:/dev/shader/godot-shader/godot-shader-simple/docs/shader-learning/chapter03-section01-checkpoint-report.md)，其当时尚未接入的描述不代替下方最新应用证据。

## 使用或新增的资源及许可

| 资源 | 实际使用 | 来源／许可 |
| --- | --- | --- |
| `assets/shader-learning/common/uv_grid_512.png`，512×512 | 03.1 时间移动 | `GENERATED_IN_PROJECT`；`tools/generate_chapter01_assets.ps1`。 |
| `assets/shader-learning/2d/test_sprite_robot_512.png`，512×512 RGBA | 03.1 初始准备，最终已被学习者替换 | `GENERATED_IN_PROJECT`；`tools/generate_test_sprite.ps1`。 |
| `assets/shader-learning/2d/kenney-rts-scifi/player_scifi_unit_03.png`，128×128 RGBA | 03.1 中途实验版本 | Kenney RTS Sci-fi，CC0；同目录 `License.txt` 与资源台账。 |
| `assets/ember/characters/robot/robot_animations_v002.png`，320×384 | 03.1 最终 AnimatedSprite2D，朝上行五个 64×96 裁片 | `AI_MATERIAL_AND_POSE_REFERENCE_WITH_NATIVE_PIXEL_FINISH`，v002 经 rig／标注原生修复，不登记为 CC0。 |
| `assets/ember/data/ramps/grayscale_gradient_v001.png`，256×1 RGB | 03.3 默认渐变起点，显示为 512×512；最终边缘按 UV 生成 | D02、`GENERATED_IN_PROJECT`；`art-source/ember/technical-inputs-v001/basic/generate_basic.py`。 |

资源记录见 `resources.md`、`assets/ember/data/technical_inputs_catalog_v001.json`；robot 证据见 `asset-production-batch-02-robot.md`、`asset-production-robot-repair-v002.md`、`art-source/ember/batch-02-robot/generation-record.json` 与 `robot_frames_catalog_v002.json`。本章未新增美术生成／下载；03.2 使用 ColorRect，无纹理素材需求。

## 游戏应用场景、状态与接口

| 用途 | 当前证据与状态 | 场景／接口 |
| --- | --- | --- |
| 03.1 站点采集脉冲 | 已有实现＋用户明确报告检查点完成；本章开始 03.2 时接受该确认，本轮再次只读核对代码。待统合者同步应用台账。 | [energy_station.gd](E:/dev/shader/godot-shader/godot-shader-simple/scenes/m0/energy_station.gd:28) 将 `Game.isGameStarting && isGetPoint` 写入 `collecting`；[站点场景](E:/dev/shader/godot-shader/godot-shader-simple/scenes/m0/energy_station.tscn:11) 材质 `resource_local_to_scene = true`、默认关闭；[站点 Shader](E:/dev/shader/godot-shader/godot-shader-simple/shader/energy_station.gdshader:33) 在状态色之后叠加 0.8～1.0 RGB 脉冲，非采集倍率为 1，保留原 Alpha。 |
| 03.1 待机呼吸灯 | 本 Chat 未验证，应用台账仍 `PLANNED` | 后续设备状态应用，不能由站点采集脉冲自动视为完成。 |
| 03.2 预警条带／终端扫描线／棋盘校准网格 | 本 Chat 仅完成扫描线实验，应用台账仍 `PLANNED` | 后续按实际危险阶段、终端状态和玩法依赖接入。 |
| 03.3 预警阈值／范围软硬边 | 本 Chat 仅完成边缘与脉冲实验，应用台账仍 `PLANNED` | 实际范围与判定仍由游戏逻辑提供。 |

采集资格由既有游戏逻辑负责，视觉时间不独立决定采集、危险或伤害。游戏接口接入由独立游戏教学完成，本 Chat 不代写或扩展游戏。

应用运行证据采用用户原话“采集脉冲检查点已完成，继续 03.2”。本次为代码核对，不追加新的游玩、结算、重开或实例隔离实测次数。`progress.md`／应用矩阵仍含 2026-10-05 的旧 `PLANNED` 记录，建议统合者核对游戏教学报告后同步相应采集脉冲子集；其余具名用途继续保留。C02 管线流动、终端缩放与旋转校准同样保留后续实际应用要求。

## 对后续课程的调整建议

- 新概念先说明含义、输入输出与做法；必要时提供局部代码帮助熟悉。已教过或学习者明确熟悉的内容只给具体需求与文字方法，先由学习者实现，求助后再增加提示。
- 每次需求具体到数值、对象、单位、变化方式与预期画面；例如说明 30% 指亮条中心 RGB 系数、时间周期和同步关系。需求具体不等于主动贴公式／代码。
- 教师可搭场景和材质连接，Shader 起点只保留默认采样；学习者写完默认已运行确认，教师读取最新版本核对逻辑。
- 一次一个小目标；数学以数字与视觉说明，保留已验证的替代实现。参考提示、自行组合、独立推导和游戏应用分别登记。
- 完整课程与全效果应用矩阵继续保留，不因小游戏或商业版兼容性删减；可按依赖安排尚未接入项，不无限追加可选修整。

## 关键路径、建议复习与推荐下一章

- 已完成路径：C03.1 时间／周期 → 采集脉冲游戏检查点（用户确认）→ C03.2 重复单元／扫描线 → C03.3 软硬边／脉冲条带。
- 建议复习：在后续真实应用中短查范围映射、密度与速度、柔边宽度和纯亮区域的区别；当前无需重做本章。
- 推荐下一章：Chapter 04「Mask、距离与柔边」。由统合者核对报告与前置后安排，本 Chat 停在本章收尾，不自动教学或新开聊天。
