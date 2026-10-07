# 敌人动作首批提交 · 技术美术总监审阅

用户已明确要求“结束后汇报情况给chat 技术美术总监 让他审核”。本提交对应 2026-10-06 冻结的 `enemy_sequences_v001`，四款敌人、仅正向 `down`、待机/移动/攻击/受击/死亡，共 20 条、120 帧。交付定位为可播放动作审阅稿 `PLAYABLE_VISUAL_SAMPLES / TA_REVIEW`，美术自检 `NEEDS_REVISION`，TA 状态 `PENDING_TA`，`production_ready=false`。本批 20 条均未标为正式美术通过。

## 固定版本与入口

工作区：`E:/dev/shader/godot-shader/godot-shader-simple`。以下路径均相对于工作区。

- 生产规范：`docs/shader-learning/ember-enemy-animation-standard-v001.md`。
- 统一美术规范：`docs/shader-learning/art-style-standard-v002.md`；审核依据：`docs/shader-learning/ta-art-review-standard-v001.md`。
- 已认可身份参考：`art-source/ember/enemy-design-sheets-v001/design_catalog_v001.json`，对应三视图、零件拆分与四份参考母稿。
- 完整选源、共同注册、帧时序：`art-source/ember/enemy-sequences-v001/sequence_specs_v001.json`，SHA256 `225fd6333590f80e526f7422d58ac89ba74edd5d52607daf1a092f5cf2c368a7`。
- 最终资源目录：`assets/ember/characters/enemies_v001/sequence_catalog_v001.json`，SHA256 `568c280046c007c88240a40574592cc46e7f19b54ece1e0171a94807a3ba40e6`。
- 最终美术证据：`art-source/ember/enemy-sequences-v001/qa/visual_art_review_v001.md` 及 `.json`。JSON SHA256 `34c7cefdc7fb0bdd12167f5c12c7f931432d67524ebb6b63c1f7d0548342b99c`，逐条绑定 20 源图与 20 atlas，另含 12 张证据图的哈希。
- 浏览器播放器：`art-source/ember/enemy-sequences-v001/previews/enemy_sequences_player_v001.html`，自包含，可离线打开；当前可访问 `http://127.0.0.1:6106/enemy_sequences_player_v001.html`，支持暂停、逐帧、1×/4×、深/浅底色。
- 独立 Godot 工程：`art-source/ember/deliveries/enemy_sequences_v001_2026-10-06/project.godot`；根目录 `run_preview.ps1` 为本机可直接执行入口。
- ZIP：`art-source/ember/deliveries/enemy_sequences_v001_2026-10-06.zip`，38,453,242 字节，319 条目逐项 SHA 验证通过。ZIP SHA256 `cf49b8c85a74a36654e280a44b371ed12d99f1130a4ef407b784720c68d358da`。ZIP 内容已冻结，后续 TA 提交回执与包冷启动报告单独保存于源 QA 目录。

完整提示词、修源提示词、20 份选中透明母稿、独立帧 PNG、20 atlas、4 份 SpriteFrames 与 4 份可复用场景均随包交付。旧版替换母稿不放入最终包，可在工作区历史候选中追溯。尚未提供锁定刚性零件的可编辑原生像素动画母稿或逐帧人工精修。

## 已执行验证与参数

所有帧为 128×128，虚拟地面锚点 `(64,104)`，Nearest，`AnimatedSprite2D.centered=false`、`offset=(-64,-104)`。每条动作只有一个共同缩放与偏移，保留源 RGBA，不按每帧包围盒重新缩放、居中或齐底。

待机 4 帧/4 FPS、移动 8 帧/8 FPS循环；攻击 6 帧/10 FPS、受击 4 帧/12 FPS、死亡 8 帧/10 FPS 单次。f03 释放与 f07 残骸保持仅为视觉审阅标记，未接入伤害、AI或位移逻辑。预览控制器延时重播单次动作，资源本身 `loop=false`。

最终导出、Godot 隔离资源导入、20 动作真实 GPU 播放、全帧联系图均技术 PASS，播放已遍历全部 120 帧并观察循环与单次结束。全帧联系图格内 RGBA 与原 atlas 核对 120/120。技术 PASS 不等于美术验收 PASS。

ZIP 完成后，独立包根首次 `--headless --editor --import --quit` 与主场景 `--headless --quit-after 120` 均退出 0，stderr 均为空；未加载主项目 Game autoload。318 份清单文件 SHA 全部匹配，ZIP SHA 未变。冷启动报告及日志单独保存在 `art-source/ember/enemy-sequences-v001/qa/package_cold_start_v001.json` 和 `package_cold_*` 日志；ZIP 内不会倒填这些后生成证据。包内首次导入缓存不在 ZIP 中。

全部 1×/4×联系图位于 `assets/ember/characters/enemies_v001/previews/`，文件模式为 `enemy_*_all_frames_down_1x_v001.png` / `4x_v001.png`。首个移动闸门请查看 `enemy_patrol_move_down_strip_1x_v001.png` / `4x_v001.png`。Godot 白/黑底实际透明证据和七个播放时间点截图同在该目录。图片查看器中的透空隐藏 RGB 不能当作引擎实际不透明底板。

## 修复结果与明确未完成项

工蜂移动已采用 `enemy_cutter_move_down_master_v003.png`，20 条目录、当前 atlas、逐帧 PNG、SpriteFrames、HTML及实际 Godot 均已重新导出，旧换手版没有留在交付中。新母稿 SHA256 `431ebb054feefa7d325b41171885062066af5afcab1cca80487a1e49b7bae803`；新 atlas SHA256 `5cedf96310573c4c8d99f05e52cd304054ac3b800112e2f33d0d6b0b77fcd36a`。八帧保持圆锯在观众左、夹爪在观众右。

仍需返修：

1. 巡逻兵移动的接触/下沉/经过/抬升步相与闭环节奏未过关，应作为首个生产闸门；四款跨动作中性姿态的刚性部件身份也未锁定。
2. 多条动作有跨行定位差。工蜂移动底排高 3～4 原生像素；巡逻兵死亡末段上移 8 像素，工蜂死亡有 7 像素差，重装死亡有 5 像素差。报告中的 bbox 下边缘是位置诊断，不是登记过的语义脚底，不能拿齐 bbox 代替支撑检查。
3. 工蜂受击 f02 的工具臂与后步腿插座仍有歧义；新候选没有修好，保留较好的 v001 并明确登记。
4. 侦察机移动/死亡仍有三叶或两条叶片的投影读形，死亡末帧底缘 y85，距离固定地面投影 y104 仍差 19 像素，不能称落地完成。
5. 全批源 RGBA 保留连续 Alpha，包括 250～254。正式实体 0/255 Alpha 闸门失败，未做程序阈值清理；实体原生像素、轮廓和固定零件仍需人工制作。

请优先审巡逻兵 `move_down`，给出整体与逐条 `PASS / CONDITIONAL / NEEDS_REVISION / PENDING` 结论及最小返修范围；不要因资源数量齐全、GPU或完整性 PASS 放行正式生产。其他方向、敌人AI/碰撞/伤害集成尚未开展。
