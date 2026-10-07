# Robot v011 phase A rc02：独立局部技术复核

结论：**LOCAL_TECHNICAL_INCREMENT_PASS**。本轮确认 rc02 精确恢复原固定 rig 的远侧右大腿刚性甲片及两侧透明边，没有确认新增来源、注册或导出问题。技术结论限于该局部改动；八帧的最终视觉、运动和原 rc01 P2 的美术关闭由根 TA 播放审查决定，不扩大为八向动画整体通过。

## 固定包与基线

- 正式 ZIP：`art-source/ember/deliveries/robot_eight_way_v011_phase_a_rc02_2026-10-06.zip`；SHA256 `df9884f9668dc89b8c74cf746dbd975a87e9a5b566b6783b5582cb2c78b4d521`，5,141,175 B。
- 独立读取 ZIP 并解至本目录 `package/`。212 条目由 210 manifest 载荷、manifest 本身与 1 个空目录组成；全部 CRC、载荷字节数和 SHA 通过。211 个普通文件与 `review/phase-a-rc02` 固定快照逐字节一致。没有以活动目录代替固定包。
- rc01 基线 SHA256 `ee0b416f194363d4e37e751c03446c944c217af3a2f567a03eff4a00ad91e7e6`。rc02 的 8 张 `source/reference-phase-a-rc01/frames/` 与原 rc01 ZIP 对应帧逐字节相同；没有移除旧包载荷。

## 独立像素复算

从不变 `source/fixed-parts/down_left/leg_right_upper.png` 的实际可见像素推导源保护区：源 y54–62，源甲片左右各加 1px 后为 `[20,54,12,9]`。按不变 `rig_and_poses.json` 的 sourcePivot、targetPivot、radians 独立逆映射该矩形，未使用作者导出的 mask 决定允许区域；8 张重算 mask 与包内 mask 全 RGBA 相同。

| 帧 | rc01→rc02 恢复像素 | 独立保护区外 RGBA 变化 | 保护区内与原 pilot 差异 | 保留的局部修形像素* |
|---|---:|---:|---:|---:|
| F00 | 41 | 0 | 0 | 155 |
| F01 | 36 | 0 | 0 | 164 |
| F02 | 25 | 0 | 0 | 157 |
| F03 | 18 | 0 | 0 | 155 |
| F04 | 17 | 0 | 0 | 128 |
| F05 | 16 | 0 | 0 | 136 |
| F06 | 31 | 0 | 0 | 156 |
| F07 | 47 | 0 | 0 | 172 |

\* 最后一列是 rc02 相对未修形 fixed-rig pilot 的实际差异，不是本次新增改动。

八帧共恢复 231 个像素。独立计算的完整预期帧 `rc01 帧 + 保护区内原 pilot RGBA` 与每张 rc02 帧全 RGBA 相等；因此没有借恢复甲片追加其他区域改动。新关节编辑 mask 恰为旧 mask 排除该保护区；剩余 1,223 个局部修形像素的完整坐标、before/after 和输出 SHA 与新账本一致。这里核的是实际内容和保护边界，不以作者的零差声明代替计算。

原 41 个 source 载荷，包括固定部件、rig、各帧 pilot、一次生成局部编辑原图与量化图、8 张方向母版及历史参考，均与 rc01 ZIP 同字节。原矩阵没有改变。16 张非 SW 正式 PNG（S 行走 8 张与 8 张静态 pose）同字节；头胸、手与工具等原有保护结果在独立恢复区外完整保留。源分区和原局部导出流程的无变部分继承 [rc01 独立技术报告](../robot-v011-phase-a-independent/integrity.md)，未重复运行生产生成脚本。

## 资源和保存证据

- 24 张正式帧均为 64×96、Alpha 0/255；每张 SHA、metadata region 和 atlas 裁片全 RGBA一致。root `[32,80]`、texture_scale 1 保持。新 512×288 atlas SHA256 为 `b3767668e427c1a90e77bd80fb98edfd63c0517ef78f6e5fca51354c2b3ec0d7`，根目录与 Godot assets 副本一致，两份 metadata 一致。
- 10 个 clip：S/SW walk 各 8 帧、8FPS、loop；8 个 pose 各 1 帧、1FPS、nonloop。5 个 Godot 运行文件（项目、场景、脚本、SpriteFrames）与已完整审查的 rc01 同字节；本轮替换的 atlas 与 metadata 已按实际 24 帧核齐。
- 独立静态比较作者保存的 48 张 GPU 回读：24 帧各原生及 4× Nearest，48/48 全 RGBA 零差；捕获文件受固定包 manifest 约束。作者运行 JSON 绑定本次 atlas SHA，S/SW 两段记录均包含两完整 `0..7` 循环与下一轮 `0,1`，时间顺序正常。
- **本轮未启动 Godot、未重新冷导入、未重跑 GPU 或循环。** 上述 GPU/循环是对制作方保存记录的内容与绑定复核；rc01 已完成的独立运行检查只在运行文件不变的范围继承。保存记录不能独立证明本轮 TA 亲自复验了动态观感。

复算脚本：[verify_increment.py](verify_increment.py)。完整固定包差异、恢复坐标、SHA 与 48 个捕获绑定：[evidence-increment.json](evidence-increment.json)。本轮只写独立审查目录，未修改生产资源。
