# Chapter 02 完成报告

- 日期：2026-10-04（Asia/Irkutsk）。
- 章节状态：`COMPLETED`（主练习）。依据学习者的运行反馈及最新保存代码审查；矩阵原理与推导按学习者决定延期，不登记为已掌握。
- 完成的 Section：02.1 UV Offset 与采样边界、02.2 中心缩放、02.3 中心旋转与非方形纹理宽高比修正。

## 实际完成的实验与证据

| Section | 实验和效果 | 掌握证据与提示边界 |
| --- | --- | --- |
| 02.1 | 双轴 UV 偏移；观察 clamp 边缘延伸、repeat 重复采样及显式越界补黑 | 学习者独立编写偏移和边界判断，报告正偏移与图案视觉移动方向相反，并解释边缘重复最后像素、repeat 将另一侧内容接回的现象。 |
| 02.2 | 围绕中心缩放；`zoom` 越大图案越大；越界补黑 | 学习者解释“先减0.5、变换后再加0.5”和采样缩放的逆关系；能区分宽高各变2倍与面积变4倍。保存实现为 `(UV - 0.5) / zoom + 0.5`。 |
| 02.3 | 正角度对应图案顺时针旋转；以中心为支点；非方形校准图旋转时保持格子形状 | 使用过完整旋转矩阵参考。学习者自行写入宽高比参数和分量运算，并在方向提示、伪代码与局部代码提示下修正顺序；明确报告格子不再拉伸，并理解横纵先换成同一长度单位再旋转。 |

- 可选“旋转＋中心缩放”挑战：最新代码审查通过。最终流程为中心化、x乘宽高比、矩阵旋转、结果x除宽高比、相对坐标除zoom、加回中心、判断最终采样边界。`zoom` 范围0.5～2、默认1。学习者尚未明确报告最后三组组合参数的实际运行结果，因此此挑战仅登记为代码审查通过。
- 可选非等比缩放：本章未完成该变体。
- 可选无缝自动滚动：repeat边界行为已观察；时间驱动留到Chapter 03，与本章双轴手动偏移分别登记。

## 能独立解释与实现的内容

- 建立Sprite2D、ShaderMaterial与Shader资源的连接；复用同一Shader，通过不同材质保存不同参数。
- 编写双轴偏移、围绕中心的缩放及最终UV的四项越界判断。
- 解释UV是采样位置；节点保持固定时，采样变化仍会改变可见图案。
- 解释采样偏移方向、缩放逆关系、中心化结构，以及非方形图片横纵UV刻度对应不同实际距离的问题。
- 在提示帮助下，将旋转模板、宽高比修正和中心缩放组合起来。此项不等同于独立推导矩阵。

## 仍需提示与延期内容

- 二维矩阵的含义、乘法原理及旋转矩阵推导。学习者明确选择当前先使用旋转模板，独立数学补课chat已另行创建。
- 变换流程中的操作顺序和标量／vec2分量操作。后续出现类似问题时，继续用一项操作和具体像素距离解释。
- 完整旋转参考后的独立修改验证通过宽高比与缩放接入开展；不将观看示意图或复用参考记录成独立推导完成。

## 典型错误与排错

1. 判断越界使用新UV，正常分支却采样原UV，导致只有遮罩变化；改为采样最终新UV。
2. 未中心化或把采样乘zoom理解成视觉放大；通过运行观察确认减中心、除zoom、加中心的结构。
3. `s`误写为`cos(angle_rad)`；修正为`sin(angle_rad)`后，恢复预期旋转。
4. 将整个vec2除以宽高比，造成整体缩放；随后又漏了旋转前x乘比例。最终补齐“旋转前x乘、旋转后x除”的对应操作。
5. 新节点绑定材质未保存，磁盘文件与编辑器状态不一致；保存后确认非方形节点已复用旋转Shader。
6. 组合挑战使用乘zoom导致视觉缩放方向与需求相反；改为除zoom，并将滑块下限设为0.5。

收尾时仅校准了两项保存的场景数据：非方形材质宽高比2.08改为512÷256所得的2.0；隐藏方形对照图遗留zoom=0改为1.0。学习者编写的Shader逻辑保留。

## 使用资源及许可

- `uv_grid_512.png`：512×512，已有项目生成校准图，来源`GENERATED_IN_PROJECT`。
- `non_square_grid_v001.png`：512×256，原生64×64正方形格子，已有D01技术输入，来源`GENERATED_IN_PROJECT`。
- 来源与生成证据见[资源台账](E:/dev/shader/godot-shader/godot-shader-simple/docs/shader-learning/resources.md)和[技术输入目录](E:/dev/shader/godot-shader/godot-shader-simple/assets/ember/data/technical_inputs_catalog_v001.json)。本章未新增外部素材。

## 关键文件路径

| 实验 | Shader | 场景 |
| --- | --- | --- |
| 双轴偏移 | [ch02_01_uv_offset.gdshader](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter02/ch02_01_uv_offset.gdshader) | [ch02_01_uv_offset.tscn](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter02/ch02_01_uv_offset.tscn) |
| 中心缩放 | [ch02_02_center_scale.gdshader](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter02/ch02_02_center_scale.gdshader) | [ch02_02_center_scale.tscn](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter02/ch02_02_center_scale.tscn) |
| 旋转、比例与组合 | [ch02_03_center_rotate.gdshader](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter02/ch02_03_center_rotate.gdshader) | [ch02_03_center_rotate.tscn](E:/dev/shader/godot-shader/godot-shader-simple/scenes/chapter02/ch02_03_center_rotate.tscn) |

## 游戏应用、事件与接口

| Section | 计划用途与触发／状态 | 当前实验参数 | 应用状态 |
| --- | --- | --- | --- |
| 02.1 | 管线能量纹、水纹滚动反映设备运行；控制流向与边界，逻辑范围固定 | `offset_x`、`offset_y`；时间／速度驱动后续接入 | `PLANNED` |
| 02.2 | 终端中心缩放观察维修目标；中心稳定，目标判定独立 | `zoom` | `PLANNED` |
| 02.3 | 终端旋转扫描校准方向；正确处理中心与非方形比例 | `angle_deg`、`aspect_ratio`；组合另有`zoom` | `PLANNED` |

- 应用运行证据及未覆盖效果：本chat完成的是独立Shader实验，尚无上述三项真实可玩应用的场景路径、玩家事件与正式接口契约验证。当前uniform仅是后续接入候选，课程完成与游戏应用验证分别登记。
- 游戏用途与验证规则以[游戏效果应用矩阵](E:/dev/shader/godot-shader/godot-shader-simple/docs/shader-learning/game-effect-coverage.md)为准。

## 建议复习及后续安排

- 建议复习项：在后续实际使用时短查中心化、UV逆向采样、变换顺序和分量运算；矩阵推导继续在独立补课chat学习。
- 对后续课程的调整建议：采用零基础数学节奏，每次只引入一个小概念，以具体数字和可见变化解释。先沿用旋转模板，在需要时再补原理。资源准备与游戏开发不替代Shader练习验收。
- 推荐下一章：Chapter 03，时间动画与程序图案。先从03.1的`TIME`、速度参数与可见动画开始，再进入重复单元与边缘控制。
- 此报告供统合者核对并登记总进度；本chat收尾未更新`progress.md`，未自动启动下一章。
