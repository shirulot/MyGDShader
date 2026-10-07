# 机器人行走动作试样 v006

状态为TRIAL。这是生成模型动作试样，供观察关节与连续动作，不是原生64×96正式角色资源，也未接入Godot或替换旧素材。编码核验PASS不代表动作美术验收通过。此次审阅记录中，F03→F04与F07→F00换步仍较生硬，抬脚经过相位不充分；这些局限未通过裁切、位移或补画掩盖。

- `review.html`：原始完整格8FPS播放，暂停、0–7滑块和深/浅背景切换；旁边是统一缩小到64×96后4倍显示的诊断。通过本地静态服务打开即可审阅。
- 母图：`E:\dev\shader\godot-shader\godot-shader-simple\art-source\ember\robot-motion-study-v006\source\drafts\robot_walk_down_master_v006_first.png`，实测1448×1086。
- 固定4列×2行，按行读取F00至F07；完整单格362×543。
- `frames/`：八张透明PNG等分原格；逐RGBA字节核验与母图对应区域相等。未裁角色bbox、移动、对齐、清理碎片或补画。
- `previews/robot_walk_down_study_v006.webp`：透明lossless WebP，8FPS，每帧125ms。逐时间RGBA核验结果为`true`，详见JSON；若失败，不宣称编码保留全RGBA。
- `previews/robot_walk_down_study_v006_checker.gif`：棋盘背景、256色量化观看预览。GIF使用130/120ms交替时长，总周期1秒，不宣称原色无损。
- `previews/robot_walk_down_contact_v006.png`：原尺寸完整格联系图，标签位于格外。
- 文件名含`scaled_diagnostic`的文件：全组采用相同固定格缩放及相同补边，保持宽高比、Nearest；明确属于缩小检查图，不是原生像素素材。

JSON记录母图/每帧/预览SHA、RGBA比对、Alpha分布、bbox及最低可见Alpha边界漂移。最低Alpha像素只是脚底代理值；碎片或其他图案也可能影响该值，工具不据此改图。

复现命令：

`node tools/export_robot_motion_study_v006.cjs --master=<母图绝对路径> --output=<本目录绝对路径> --sharp-module=<Sharp模块目录>`
