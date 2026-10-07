# Ember 敌人序列审阅批次 v001

本目录存放首批四款敌人的正向序列。每款规划待机、移动、攻击、受击和死亡五个动作，共 20 条序列、120 帧；具体已导出的条目以 `sequence_catalog_v001.json` 为准。

这是可播放的序列审阅样稿，当前美术状态为 **NEEDS_REVISION / PENDING_TA**。源图由内置 imagegen 生成；固定格导出、Godot 播放检查和原生像素美术验收分别记录，切图或播放通过不等同于动作注册、美术细化或所有动作已完成像素精修。

已保留每条序列的共同注册与原始位移，没有通过代码逐帧齐底来掩盖源图问题。死亡接地、部分动作的跨行位移及步态节奏仍须依据最终 TA 报告检查；因此本批次用于比较和继续修订。

## 固定接口

- 每帧 128×128、透明 RGBA，统一锚点 `(64,104)`。
- 方向首批为 `down`；左右工具不通过镜像制作。
- 动作名：`idle_down`、`move_down`、`attack_down`、`hit_down`、`death_down`。
- 帧数 / FPS：待机 4 / 4，移动 8 / 8，攻击 6 / 10，受击 4 / 12，死亡 8 / 10。
- 仅待机、移动资源循环。攻击、受击、死亡为单次，死亡保持末帧。
- 攻击 f03 与死亡 f07 的视觉事件保存在 metadata 中；不自动接入伤害、AI 或碰撞。

## 文件布局

每个单位目录包含原生固定网格图集 `idle_down_v001.png` 等、独立帧 `frames/idle_down/f00.png` 等、`<单位>_frames_v001.tres`、`<单位>_v001.tscn` 和逐动作 metadata。

`SpriteFrames` 复用图集区域，场景根节点为 `AnimatedSprite2D`，使用 Nearest、`centered=false`、`offset=(-64,-104)`。这是纯视觉资源，不含敌人移动、攻击判定或 AI。

## 注册与溯源

每条序列使用 f00 标定一次共同倍率和偏移。母稿整页仅执行一次 Nearest 缩放，再按完整格切出并统一放入 128×128 画布。其余帧不按包围盒重新居中或独立放大，因此原图中的姿态位移和注册误差可以如实审阅。

metadata 记录源图及 PNG 的 SHA256、每帧可见包围盒（alpha≥0.1）、半透明像素、非零 alpha 裁切、行内底沿偏差、重复帧、FPS、循环和事件。阈值仅用于测量，不用于删除 alpha；导出工具不抠图、改色、重画或补齐关节。

## 播放与验证

独立审阅工程位于 `art-source/ember/enemy-sequences-v001/preview-project/`，不会加载主游戏的 `Game` 单例。可在该工程打开 `scenes/enemy_sequences_review_v001.tscn`，按 F6 运行当前场景。空格暂停/继续，R 重播，B 切换深色／黑色／白色底，Esc 关闭预览。GPU 截图会分别保存黑白底的同一实际帧，以核对透明灰边与伪背景。

自包含浏览器播放器位于 `art-source/ember/enemy-sequences-v001/previews/enemy_sequences_player_v001.html`，只复用导出的图集。单次动作在展示控制器中停留后重播，其资源本身仍不循环。

播放器可切换 1× 原生与 4× 最近邻显示，暂停后用左右箭头或每卡片滑条逐帧检查；攻击 f03 和死亡 f07 会显示对应视觉事件。底色可切换深色、黑色与白色。

完整帧联系图位于 `previews/<单位>_all_frames_down_1x_v001.png` 与 `4x_v001.png`：五行依次是待机、移动、攻击、受击、死亡，每行从左到右从 f00 开始，多余列透明。四款联系图覆盖全部 120 帧，保留完整画布；`enemy_patrol_move_down_strip_1x_v001.png` 和 `4x_v001.png` 单独列出巡逻兵 8 帧步态。逐格 RGBA 一致性核对保存在 `sequence_frame_contacts_v001.json`。

实际 Godot GPU 截图与逐帧访问记录位于本目录的 `previews/`；源图 alpha 审计、导出和资源验证报告位于 `art-source/ember/enemy-sequences-v001/qa/`。当新增母稿、调整共同注册参数或美术重生后，应重新检查该条序列，再更新预览。

导出脚本：`tools/export_enemy_sequences_v001.gd`。预览组装和验证脚本：`tools/build_enemy_sequence_preview_v001.gd`。完整规范：`docs/shader-learning/ember-enemy-animation-standard-v001.md`。
