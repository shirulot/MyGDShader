# 巡逻兵 idle_down／hit_down v005 独立静态视觉审查

快照：2026-10-06 19:09 UTC+08:00。审查者：TA 子审查代理 `style_specs`。从固定ZIP独立解压，只读看图；没有修改生产文件或重导帧。

**逐条结论：`idle_down` PASS；`hit_down` PASS，均限本次独立静态及相邻帧视觉范围。** 两条动作未发现身份变化、关节横切断接、工具换边或需返修的刚甲体量漂移。待机的轻动与受击的左倾／反向收稳读形可接受。根 TA 合并实际播放器抽样与技术审查后，再逐条记录完整动画结论；本报告不继承 `move_down` 的通过，不扩张到其它动作。

## 固定范围和直接检查

ZIP：`art-source/ember/deliveries/enemy_patrol_actions_v005_2026-10-06.zip`，独立实测 SHA256 `6a3687783823cfd3e9db4b5c04d26b47c91a70df825ec74f8d195378b6c01468`，54条目（53载荷与清单）。本报告目录 `visual/` 为独立解压目录，以下路径相对此目录。

- `idle_down`：4帧、4FPS、循环；`hit_down`：4帧、12FPS、单次；128×128、root(64,104)。
- 直接查看 `source/canonical.png`，两张实际atlas、`output/{idle_down,hit_down}/f00.png`至f03全部八张原生帧、两动作黑白1×／整数4×联系图，以及16张 `qa/roundtrip_<action>_<frame>_<black|white>.png`。
- 读取README、`action_rig.gd`与来源登记，采用 `ember-enemy-animation-standard-v001.md`及 `ta-art-review-standard-v001.md` §3.2。来源／骨端／导出指标由技术代理独立复核，未代替本次看图。
- 核查全身肩、肘、腕、髋、膝、踝在深浅底的承接读形；原生与4×图均用于判断有厚度的结构关系，而非只用Alpha连通或端点距离。

## 两条动作逐帧结论

| 动作／帧 | 实际视觉判断 | 结论／最小修订 |
| --- | --- | --- |
| idle f00 | 中性头胸、画面左枪／右夹爪、双腿与固定足形成完整巡逻兵。浅甲、蓝灰结构、少量黄铜沿用canonical身份。 | PASS，无静态返修。 |
| idle f01 | 躯干上浮1px，肩臂同向跟随，髋下腿段相应调整；膝甲保持厚壳，暗胫和踝袖仍承接固定靴口。深浅底未见大腿或脚被横切成孤立甲块。 | PASS；上浮轻动没有变成整机悬空。 |
| idle f02 | 躯干回到中性，画面右夹爪／臂部轻动。肩、肘、腕的安装侧与材料一致；爪形的边缘变化随小角度姿态解释，未换成另一种工具。 | PASS，无静态返修。 |
| idle f03→f00 | 下沉1px时膝胫没有一起压成薄带；固定足与腿段保持套叠。回到f00只恢复轻幅躯干位置，未出现重新居中／换造型的末首跳姿态。 | PASS；循环节奏由实际播放合并。 |
| hit f00 | 与待机中性相同，完整双足支撑准备接受短促冲击。 | PASS，中性起点有效。 |
| hit f01 | 头胸朝画面左侧倾并短移(-2,+1)，反应幅度明显大于待机。肩臂跟随，骨盆仍在双足之间；髋至膝及膝至踝的结构承接持续，靴体不被一起拖走。 | PASS；姿态可读为短促侧向冲击，无局部断接。 |
| hit f02 | 头胸转为较小的反向倾斜收稳，工具仍装在原侧，双膝／胫甲保留各自体量。邻帧改变的是回弹方向和关节位置，未见胸甲、头盔或手套无因涨缩。 | PASS；回稳姿态可辨。 |
| hit f03及回idle f00 | 精确恢复中性；原生画面没有残留错位、额外甲片、白闪或道具变形。两PNG实际SHA相同，视觉同时确认相同中性姿态。 | PASS；末帧保持／播放时序由根与技术代理合并。 |

## 全身关节和像素轮廓

肩甲、上臂与胸架之间的深色承接在白底可见，黑底中仍能结合装甲侧面读出肩臂属于同一架构；肘／腕未出现悬浮手块或只有细线挂接工具。髋座下的两条腿与骨盆连续，膝甲、后方暗胫、踝袖和靴口各有厚度与遮挡；未发现依赖深色背景吞掉透明断缝的现象。此判断只针对当前八帧，未使用机器人v008/v009的早期局部通过作为依据。

hit f01/f02的头盔侧缘、胸甲斜边、爪边有nearest旋转造成的有限像素取舍；方向随已登记侧倾改变，主体宽度／材料亮暗与刚性安装仍连贯。当前未观察到须返修的盔甲轮廓游动、孔洞／磨损迁移或工具忽大忽小。黑白图中没有新增白边、糊边、残影或全身闪色。

受击姿态本身表达「中性→短促侧偏→反向收稳→中性」，双足固定、腿部跟随承接形成可信的小幅机械反应。没有以强闪白掩盖读形；闪白及粒子仍为独立效果。正常12FPS时冲击／回稳是否足够清晰，由根 TA 的实际播放器证据补足，本子代理未声称观看连续视频。

## 范围与后续

本次未新增返修项，可保留同canonical与11固定源区、小幅关节姿态和固定双足支撑方法。仅审本巡逻兵正向待机／受击两条，不审攻击、死亡、其他方向或其余三款敌人。

正式动作受击资源必须保持单次播放；审阅播放器的延迟重播是演示行为，不能据反复播放截图误判资源循环。主玩法受击触发、伤害事件、地面碰撞与整套敌人资源不在本静态范围。

## SHA256绑定

| 文件 | SHA256 |
| --- | --- |
| source/canonical.png | `6e2c4eb57d214de69778291bcbdc4b40dfb4a5b4881fcb33338bb5f4474f348c` |
| rig.json | `419c3b66ab7a9887b9aba0385d39e71f5608fe16c4c93e8d1a0cb7884ce9cf41` |
| action_rig.gd | `e0758859a72d0a2f5de6c22c40d389144cfe13c86e3f72da52fd61a2a7430f06` |
| output/idle_down_v005.png | `84a29c3af3b2f6dff3c0136a8bc4c1104814442725fa61ac0f5ab140b1197017` |
| output/hit_down_v005.png | `21625b527b143757e553d91591b5df5506ca2654ff0875497fdf62b137d5a64c` |
| output/idle_down/f00.png | `f7b817ff8c4c6ea9af4554c37873709e9419e83f93ec540f7dd96b9b7184482d` |
| output/idle_down/f01.png | `8460e366334991eb265f3fd120e17ae5319151976830bc245c4a70fae7f955b2` |
| output/idle_down/f02.png | `3e647e017caa0444b46c5d4a2b9cac7bfa2e9dbf0e949bbeda1f060f086c7108` |
| output/idle_down/f03.png | `9677afcd311e046171c5e510a480a9943d3cc237a7d6dbcfcee25f1af4bae6af` |
| output/hit_down/f00.png | `f7b817ff8c4c6ea9af4554c37873709e9419e83f93ec540f7dd96b9b7184482d` |
| output/hit_down/f01.png | `23a499b5a29834a7fcdac2581064a8f2cfa0066fb8288659d36f945ca4e05527` |
| output/hit_down/f02.png | `1136ab75dca5fd8b9a7077ffbe31d1ad19f6a20f62521593514bdfd2068def96` |
| output/hit_down/f03.png | `f7b817ff8c4c6ea9af4554c37873709e9419e83f93ec540f7dd96b9b7184482d` |
| qa/idle_down_white_1x.png | `3204a04eccfe6b2eef79d139d01e254432e1f349b5806458c6881037c457a040` |
| qa/idle_down_black_1x.png | `d3726e2cb891ed4e062848f6eed1d8bf7b37e4bf766f7275274a87caed861a05` |
| qa/idle_down_white_4x.png | `48df7481f641313fcd3374160dbfe6afcb18d87e664d3a705bff7da1a2de33ce` |
| qa/idle_down_black_4x.png | `25496b07c3dcb9dbac3ea8b7f52cf4da84ffe0ff5ece2498557ee22e243f1312` |
| qa/hit_down_white_1x.png | `cb18e70f1932a6a9a30ca8a5c840604f9f2e75487187c5f158bba1abdf6d5d34` |
| qa/hit_down_black_1x.png | `817f9eeb720194e96fc66be07f71c16c5238dd00d47472bc0113089a13e4d61f` |
| qa/hit_down_white_4x.png | `3d7cf307cd28fd859eaafe19aa21a0b34120441ede80d17593394cc73fe3d66c` |
| qa/hit_down_black_4x.png | `490a77e9d2d5c8aefde802bc40b54f769a33550a374197bbb8e73b0ac90157a2` |
