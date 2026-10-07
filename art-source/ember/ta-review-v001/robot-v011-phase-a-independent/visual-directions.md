# 基础机器人 v011 阶段 A：八向身份独立静态审核

**结论：七个新增方向 STATIC_IDENTITY_PASS；S 的 v010 F02 可保留为静态身份/形体基准。未见需退回的工具换侧、组件增减、明显体型重设计或方向矛盾。此结论不等于双帧 idle、SW walk 或八向动画完成。**

固定 ZIP：`art-source/ember/deliveries/robot_eight_way_v011_phase_a_rc01_2026-10-06.zip`，SHA `ee0b416f194363d4e37e751c03446c944c217af3a2f567a03eff4a00ad91e7e6`。本审查从固定 ZIP 独立复制资料，不使用活动目录作为图证。

实际查看：原八向生成母图、`original_four_direction_identity_4x.png`、批准 v010 八帧对照、8 张 candidate master 的原生/8×局部、八向深浅 4×联系图与原生联系图，以及 `gpu-playback/direction_board_4x.png`。核对全部八张母版字节 SHA 与 `qa/master_registration_v011.json` 相符；源母图 SHA `991a34fc51a1fd8eeaca4ea431842acff8d0d6e19054303c4f26093abdbc82df`。证据副本/PNG SHA/裁图范围均在 `directions-evidence/image-binding.json`。未修改生产资源、未运行浏览器或 GPU。

## 身份、体积与方向

与原四向及批准 v010 比较，浅甲大头盔、深色面罩、紧凑胸腰、蓝灰关节、厚靴和少量黄铜腕工具仍能读成同一机器人。侧向头盔前沿/耳部展开、远侧四肢被遮住，背面面罩消失而露出小后槽，是合理视角变化；没有为使外框相等而要求补露隐藏工具或肢体。

|方向|实际可见关系与结论|
|---|---|
|S/down|前面罩、胸甲和画面右腕黄铜工具；直接保留批准 F02 的形体，STATIC_REFERENCE_USABLE。|
|SW/down_left|前面罩收向画面左，左侧耳/身体侧面展开；近侧解剖左腕的工具在画面右侧，STATIC_IDENTITY_PASS。|
|W/left|朝左的头盔前沿及侧耳、近侧左臂和腕工具清楚；远腿/远臂遮挡可保留，STATIC_IDENTITY_PASS。|
|NW/up_left|后头盔及偏向右侧的后槽、画面左的近侧臂/工具，读成左后斜向；没有正面大面罩，STATIC_IDENTITY_PASS。|
|N/up|完整头盔背面小槽，工具转到画面左；未新增背包或排气件，STATIC_IDENTITY_PASS。|
|NE/up_right|后头盔右侧耳展开，左腕位于远侧而工具被遮住；与 NW 的可见面不同，STATIC_IDENTITY_PASS。|
|E/right|朝右侧轮廓，近侧右臂没有被补上黄铜工具，远侧左腕遮挡可保留，STATIC_IDENTITY_PASS。|
|SE/down_right|正面罩偏向画面右、近侧右臂和远侧左腕关系成立；露出的黄铜工具仍在远侧左腕，不是换到近臂，STATIC_IDENTITY_PASS。|

八向静态顺序中，前斜向位于正面与纯侧面之间，后斜向位于侧面与背面之间，头盔可见面、身体侧面和工具遮挡关系没有发现相互冲突。此处是方向语义的静态判断，不冒称已证明实际切向连续或精确测得每个头部 yaw 为45°。

新增方向的明暗仍以画面左上亮、下部/右侧暗的大色簇为主，W/E 没有为了露工具而做相同手臂配置。肩、肘、腕、髋、膝、踝在本次静态深浅底中未见明确断接或甲片靠细线悬挂的阻塞；SW 运动关节跨帧形状另由动态专项审核，本报告不替代。

## S 的 F02 使用边界

当前 `source/candidate-masters/robot_idle_down_v011.png` 与包内 `frames/walk/down/robot_walk_down_f02_v010.png` 逐字节相同，SHA `31aef53af6a5552d9adae69f5afefab25ee35cc30059bf285dffc375f374dc79`。它保留批准的头胸、工具及关节形体，可作为本阶段 S 的身份参照与后续修形起点。

F02 仍带行走相位，不能因为文件名含 idle 就视为中性双足支撑或双帧 idle 已通过。其画面左/右靴的不透明像素末行分别为 y78/y79，仅是像素范围定位，不等于真实接地测量；最终 idle 应另审受控静止支撑和两帧微动。本次没有要求为静态身份预检重新生成 S，也没有把复制 F02 计成最终 idle 两帧。

诊断图为 `directions-evidence/directions_group_0_native_roi_8x.png` 与 `directions_group_1_native_roi_8x.png`；均使用相同原生 ROI `(10,16)-(56,84)`、最近邻8×，保留原位置，不按人物 bbox 重居中/伸缩。后续按已登记固定方向母版补隐藏部件和动作，再逐批审核；本次静态通过不外推到未制作动作。
