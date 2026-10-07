# Ember 敌人动作候选 · TA 审阅 v001

本批已生成四款已认可敌人的正向 `down` 动作候选：每款待机、移动、攻击、受击、死亡，共 **20 条序列、120 帧**。母稿使用内置 imagegen 生成，按共同标定切成透明 PNG，再提供 Godot `SpriteFrames` 和 `AnimatedSprite2D` 样稿场景。交付定位为 **`PLAYABLE_VISUAL_SAMPLES / TA_REVIEW`**，供逐帧审阅与返修选版，不宣称已完成正式实体像素或获 TA 生产放行。

技术导出、资源与 GPU 播放通过仅证明候选可按登记参数播放。严格美术审查另有返修项：部分动作的 root 跳变、工蜂 `hit` 的 `f02` 挂接、侦察机转子叶形连续性及死亡末态落地、实体的连续 Alpha。新修来源仍需在同一审查范围复核；哪些问题已经解决、哪些仍阻塞，以绑定最终规格/目录 SHA256 的 [视觉审阅报告](qa/visual_art_review_v001.json) 为准。

## 查看动作

- 浏览器：打开 [自包含 HTML 播放器](previews/enemy_sequences_player_v001.html)，可暂停、继续及从头重播。图像直接嵌入页面，解压后可离线查看。
- 工作区 Godot：导入本目录的 `preview-project/project.godot`，打开 `res://scenes/enemy_sequences_review_v001.tscn` 运行。这个工程只读取复制后的敌人资源，不加载正式项目的 `Game` 单例。
- 独立 ZIP：包根的 `project.godot` 是可直接导入的完整预览入口；运行 `run_preview.ps1 -GodotPath 'D:\Godot\godot.exe'`。包根 README 也给出播放器入口。

逐帧联系图位于 `assets/ember/characters/enemies_v001/previews/`：每款 `<unit>_all_frames_down_1x_v001.png` 与 `_4x_v001.png`，以及 `enemy_patrol_move_down_strip_1x_v001.png` / `_4x_v001.png`。全帧联系图为五行八列，行顺序为待机、移动、攻击、受击、死亡，不足八帧的多余格透空；巡逻兵移动条带用于先审步相和循环。1 倍是导出画布的诊断视图，4 倍是整图最近邻放大；两者保留完整帧和源 RGBA，不代表原生像素精修已完成。

| 单位 | 全帧 1 倍 | 全帧 4 倍 |
|---|---|---|
| 巡逻兵 | [1×](../../../assets/ember/characters/enemies_v001/previews/enemy_patrol_all_frames_down_1x_v001.png) | [4×](../../../assets/ember/characters/enemies_v001/previews/enemy_patrol_all_frames_down_4x_v001.png) |
| 切割工蜂 | [1×](../../../assets/ember/characters/enemies_v001/previews/enemy_cutter_all_frames_down_1x_v001.png) | [4×](../../../assets/ember/characters/enemies_v001/previews/enemy_cutter_all_frames_down_4x_v001.png) |
| 履带重装机 | [1×](../../../assets/ember/characters/enemies_v001/previews/enemy_tracked_heavy_all_frames_down_1x_v001.png) | [4×](../../../assets/ember/characters/enemies_v001/previews/enemy_tracked_heavy_all_frames_down_4x_v001.png) |
| 悬浮侦察机 | [1×](../../../assets/ember/characters/enemies_v001/previews/enemy_scout_drone_all_frames_down_1x_v001.png) | [4×](../../../assets/ember/characters/enemies_v001/previews/enemy_scout_drone_all_frames_down_4x_v001.png) |

巡逻兵移动循环：[1× 条带](../../../assets/ember/characters/enemies_v001/previews/enemy_patrol_move_down_strip_1x_v001.png)、[4× 条带](../../../assets/ember/characters/enemies_v001/previews/enemy_patrol_move_down_strip_4x_v001.png)。

Godot 预览按四行单位、五列动作同时播放，显示放大 2 倍并使用 Nearest。**空格**暂停/继续，**R**从第 0 帧重播，**Esc**关闭本预览。攻击、受击与死亡资源保持不循环；为了反复审阅，展示控制器在结尾停留后重播，死亡末帧停留 1.25 秒。这种展示重播不会写成资源循环。

## 动作参数

| 动作名 | 帧数 | FPS | 资源循环 | 时序 |
|---|---:|---:|---|---|
| `idle_down` | 4 | 4 | 是 | 1 秒 |
| `move_down` | 8 | 8 | 是 | 1 秒 |
| `attack_down` | 6 | 10 | 否 | 0.6 秒；`f03` 是视觉释放点 |
| `hit_down` | 4 | 12 | 否 | 约 0.333 秒 |
| `death_down` | 8 | 10 | 否 | 0.8 秒；`f07` 为稳定残骸 |

逐帧编号从 `f00.png` 开始。图集按行优先，从左到右、从上到下排列；待机与受击为 2×2 格，移动与死亡为 4×2 格，攻击为 3×2 格。每款累计 30 帧。

| 单位 | 原样稿画布 / 原锚点 | 中性主体上限 | 保留结构 |
|---|---|---|---|
| `enemy_patrol` 轻型巡逻兵 | 64×96 / (32,80) | 40×64 | 角色右臂枪、左夹手；两腿两脚 |
| `enemy_cutter` 近战切割工蜂 | 80×80 / (40,64) | 56×48 | 四条承重腿、右圆锯臂、左夹爪臂 |
| `enemy_tracked_heavy` 履带重装机 | 112×96 / (56,80) | 80×64 | 两组履带、一个短炮、低顶部圆盖 |
| `enemy_scout_drone` 悬浮侦察机 | 96×80 / (48,56) | 64×40 | 两风扇、两四叶转子、两电机；无腿 |

角色自身右侧在正面图中对应画面左侧。工具不能换边；左右方向不能用简单镜像替代独立制作。

## 画布、注册与来源

全部导出帧使用 **128×128 透明画布**，固定虚拟接地点 **(64,104)**。Godot 场景设置 `centered=false`、`offset=(-64,-104)`、Nearest。侦察机的锚点是恒定地面投影点，悬浮、受击和坠落只改变机身像素。画布包含动作留白，不能将整张 128×128 当作碰撞占地。

源页先等分固定格。每条动作以 `f00` 中性参考姿态对照已认可的尺寸样图，登记整条序列共用的 `cell_canvas_px`、`offset_px`、`reference_frame` 与 `reference_bbox_px`；全页只做一次最近邻缩放，再用同一偏移放入 128×128 画布。**不逐帧按可见包围盒缩放、居中或重新对齐**，因此动作幅度与来源中的位置偏差均保留。实际生成格尺寸可以不同于 512×512 布局模板，以规格和测量报告记录的真实尺寸为准。

导出保留源 RGBA，不通过代码重画、改色、填补关节或抹掉浅透明边缘。**正式实体像素要求二值 Alpha：实体 255、透空 0，烟光与受击特效另层**。当前候选含连续 Alpha，包括近不透明的 250～254 和半透明轮廓，因此源保真不等于实体像素闸门通过；不会用程序阈值化掩盖这个返修项。可见范围统计使用 alpha ≥ 0.1 作为诊断阈值，该阈值不用于删除源像素。透明母稿、原始提示词及修订提示词、生成来源记录均随包保留；已被规格当前来源替换的旧母稿不进入交付包。来源记录保留生成时的绝对路径以供追溯，独立包的播放入口使用包内相对资源，不依赖原工作区路径。

## 文件入口

- [序列规格与共用注册参数](sequence_specs_v001.json)：20 条序列的母稿、提示词、帧数、FPS、循环、事件及注册记录。
- [生产规范](../../../docs/shader-learning/ember-enemy-animation-standard-v001.md)。
- [TA 技术美术审查与汇报规范](../../../docs/shader-learning/ta-art-review-standard-v001.md)。
- `masters/`：规格当前选中的透明母稿及对应 `.generation.json` 来源记录。
- `prompts/`：每动作提示词，修订母稿另带其修订提示词。
- `templates/`：固定网格布局参考与四款中性尺寸参考。
- [候选导出资产](../../../assets/ember/characters/enemies_v001/)：20 个图集、120 个透明逐帧 PNG、20 份动作 metadata、4 份 SpriteFrames、4 个样稿场景及总目录。
- `qa/`：来源 alpha / 网格测量、注册、导出、资源验证、实际 GPU 播放、全帧联系图和 `visual_art_review_v001.json`；技术状态与视觉/TA 状态分别记录。

单款资源命名：`<unit>/<action>_down_v001.png`、`<unit>/frames/<action>_down/f00.png`、`<unit>/<unit>_frames_v001.tres`、`<unit>/<unit>_v001.tscn`。图集每格为 128×128，SpriteFrames 用 AtlasTexture 引用各格。单独逐帧 PNG 便于进一步像素修整。

## 检查与打包

审阅交付前检查 20 条序列与 120 帧齐全、帧顺序、alpha、越界/空帧、重复帧、共用画布与注册参数、资源 FPS/循环，以及实际 Godot 播放是否遍历每一帧。先审巡逻兵正向移动的小样、支撑/重心与接触→下沉→经过→抬升→另一脚接触→闭环，再决定其他动作与新方向的放行。体量偏差、部件唯一性与循环衔接需要结合实际播放审阅；包围盒变化也可能来自预期的肢体活动或死亡塌落，不能单独证明机体缩放。

打包工具只接受固定的完整批次和通过的导出、资源、GPU 播放报告，并将母稿、图集、逐帧与场景的 SHA256 和实际文件核对。TA 审阅包要求带上绑定当前规格与目录的视觉报告，但允许它记录 `NEEDS_REVISION`；打包完整性 PASS 不会改写视觉结论或授予正式可用状态。它按规格精确选择母稿，收录 1 倍/4 倍联系图与巡逻兵移动条带，排除已替换旧稿、`.godot`、`.import`、`preview_server.json`、日志和 ZIP 文件，并生成全包文件清单和 ZIP 内逐项 SHA256 验证。

在工作区根目录执行：

```powershell
pwsh -NoProfile -File tools/package_enemy_sequences_v001.ps1 -CheckOnly
pwsh -NoProfile -File tools/package_enemy_sequences_v001.ps1
```

`-CheckOnly` 只读检查，不生成或重建交付目录。资料未齐或报告未通过时脚本报出缺项并停止。默认交付目录与 ZIP 为 `art-source/ember/deliveries/enemy_sequences_v001_2026-10-06`；已有同名交付时指定新的 `-DeliveryName`，脚本不删除旧包。包内 `file_hashes.json` 记录 SHA256（不含清单自身）；外部 `qa/package_validation_v001.json` 记录最终 ZIP SHA256 和文件核验结果。

## 后续制作范围

本批仅 `down` 正向五动作，不包含敌人 AI、碰撞、伤害判定、角色位移或独立弹丸/闪白/烟雾特效。视觉事件仅登记。后续 `left/right/up` 各方向需分别制作和审阅，同时保持左上光照、非对称工具与部件数量；当前三视图提供造型依据，不替代各方向的动画序列。
