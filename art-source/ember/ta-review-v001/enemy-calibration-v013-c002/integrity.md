# v013 c002 静态固定包完整性

**STATIC_INTEGRITY_PASS_ONLY**。只核静态来源/注册与8格像素绑定；不判造型，不批准动作或完整七向。未运行Godot、未重做GPU源图生成算法、未发送制作方消息。

固定ZIP：enemy_calibration_v013_c002_2026-10-06.zip，1,218,446 bytes，20 entries / 19 manifest payload；SHA256 d4b327e220a049a81114994fe05cd9cdf7c02502d1703693c523ef70c4c9e0d7。

- ZIP CRC全部正确；无重复、绝对路径或路径穿越。仅解包至本目录package/。
- manifest的19项路径/大小/SHA完整闭合，无额外载荷。全部成员CRC/SHA留在integrity-data.json。
- catalog按巡逻、无人机两行，每行 approved_down / generated_front / down_left / down_right，8图哈希全匹配，均128×128；catalog的registration SHA与包内文件相同。
- 黑白1×联系图均512×256，4×均2048×1024。独立以8张原图Alpha合成复算，黑白两底RGB最大误差均0；4×图与1×Nearest4倍完全相同，无格内缩放/裁切替代。
- 两旧down确实没有替换：巡逻SHA f7b817ff8c4c6ea9af4554c37873709e9419e83f93ec540f7dd96b9b7184482d；无人机SHA 8996f4f7dc0a96fc3f81910d7fb4a91717ee30c36d83702c1a05bed48e645a33。与已通过v012固定ZIP的idle首帧PNG哈希相同，独立裁其实际atlas首格全RGBA零差。v012 ZIP SHA为42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe；没有重查旧120帧。

registration每unit只有一个正向等比common_scale：巡逻0.10743801652892562、无人机0.10655737704918032。三生成视图各一次source_rect/source_anchor登记，没有每视图scale或动画帧归一化字段；catalog内对应登记一致，两源图SHA匹配、源裁区均在图内。按声明派生offset=(64−source_anchor_x×scale, target_anchor_y−source_anchor_y×scale)，数值留在数据中。巡逻target y104；无人机target y80并明确用中舱轴/小探头底，不用最低外风扇。此处核声明与字段一致性，没有以此证明输出造型正确或逐像素复算GPU采样。

8张实测bbox及Alpha直方图记录在数据中，仅诊断，不按bbox比例机械判美术。保留全128画布的每单位4列深/浅底4×和8×诊断已生成，无bbox重齐底、移位或独立缩放：

- [巡逻白底4×](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-calibration-v013-c002/diagnostics/enemy_patrol_white_4x.png)
- [无人机白底4×](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-calibration-v013-c002/diagnostics/enemy_scout_drone_white_4x.png)
- [哈希及注册数据](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-calibration-v013-c002/integrity-data.json)

所有生产路径只读，包内源图/提示与旧down保留。
