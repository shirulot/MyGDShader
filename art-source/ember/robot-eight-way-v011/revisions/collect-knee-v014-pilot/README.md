# V014 左侧屈膝采集试样

用户选择第二套 Dead Revolver 动作参考后，生成的一组左向六帧动作试样。当前状态：等待动作视觉反馈。没有替换旧版本或游戏运行资源。

## 查看

- `preview.html`：参考、V013、V014 并排对照，暂停、慢放、逐帧选择。
- `previews/left_collect_normal.gif` / `left_collect_slow.gif`：动画。
- `previews/left_collect_strip_4x.png`：六帧展开图。
- `frames/left_collect_f00.png` 至 `f05.png`：64×96 透明 PNG。

## 动作与来源

参考：https://deadrevolver.itch.io/pixel-prototype-player-sprites

用户选中的公开预览是六帧蹲姿起伏，不是完整站立到下蹲过渡。本试样借鉴其腿部折叠，补成站立、屈膝、下蹲、伸手采集、起身、站立。公开参考图只用于本地对照，不代表取得该素材包的再分发许可。

通过内置 imagegen，以 `source/robot-six-cell-edit-target.png` 为角色参照，以 `references/deadrevolver-knee-closeup.png` 为动作参照编辑。完整提示词见 `prompt.txt`。生成原稿留在 `source/generated-v1.png`。`finish.py` 仅切片、统一尺度、鞋底落地点平移、11 色限色、二值透明、导出，没有绘制新的身体结构，也没有按每帧轮廓重新缩放。F5 复用生成的 F0 保证循环端点一致。

## 验证与限制

六帧均为 64×96，使用同一缩放系数；脚底末行 y=79；首尾一致；每帧均为单个四邻域连通图形。技术检查见 `qa/validation.json`。网页加载了旧四帧和新六帧，可逐帧对照。

本试样是生图重绘，不能声称原角色像素或所有装甲细节原样保留。靴形、头盔和手臂仍有帧间差异，伸手和起身过渡也需要用户观看后判断。连通性只说明没有透明空隙切断整体，不证明膝关节结构已完全正确。尚未扩展八方向、替换正式 SpriteFrames 或做 Godot 运行验收。

## 重现整理

运行 `finish.py`（Python + Pillow）可从已保存的生成稿重新导出 PNG、GIF 和 QA 数据；不会重新调用生图服务。
