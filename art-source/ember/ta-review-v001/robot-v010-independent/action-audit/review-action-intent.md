# 机器人 v010 独立动作/身份增量审查

**结论：本次关节修复的动作与身份增量通过，未确认新 P1/P2。原生关节承接较 v009 改善；不以哈希、遮罩内修改或 Alpha 连通替代这一视觉判断。**

审查只读 `robot-joint-repair-v010`，先绑定 [export_validation_v010.json](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/robot-v010-independent/action-audit/snapshot/export_validation_v010.json)，SHA256 `81e3f3345d85327d1a23a57336eb4a6a306d5d6aa0e3f888628abe98c5a217c7`。实际八帧与 QA、冻结 manifest、局部改动账本 SHA 一致，atlas SHA `80c26370261cf0c4a803a140c005a55a6aa883589ae2b178774323913870ca63`，512×96 的八个 64×96 格与实际帧逐像素一致。v009 对照直接来自冻结 ZIP `1abc164e76abc5e7f59978ae0d3062d07b37bd6edfe55c69335ec3f61318c60f`，不是以当前制作方的旧预览代替基线。

## 身份与体量

八帧分别比较 v009/v010 实际 PNG，并使用冻结 v009 的部件归属图核查原可见像素：头、胸壳、双手、机器人自身左腕工具变化均为 0。实际图中仍是同一浅装甲头胸、蓝灰双臂双腿与画面右侧小黄铜工具，没有工具换边、重复肢体或新增另一种零件。

可见改动为肩、肘、腕、髋、膝、踝的承接色簇与局部轮廓。每帧变化 286–328 RGBA 像素，新增不透明轮廓 39–52 像素，清除旧轮廓 0–3 像素，整体不透明面积增加约 2.5–3.4%。这些数字仅说明修改实质：不能称部件的每一块原轮廓都未变。实际同帧图看，新膝踝仍保持同一腿的护盖、轴体和靴壳身份，变化没有达到突然变成另一种设计或比例的程度。

## 关节与相邻帧

- F02/F06：v009 原来膝盖下方独立的水平深色截断，在 v010 中形成更连续的灰蓝骨架/盖面过渡。上腿、膝盖、下腿可以沿同一条结构读下去，改善不只是把透明像素变为不透明。
- F00→F01、F04→F05：支撑阶段的盖面承接连续，未见同一关节无动作理由换成另一种护盖。
- F01→F02→F03、F05→F06→F07：膝踝色簇随继承步相的屈伸/遮挡变化，仍能追踪到同一侧的膝、踝和鞋。未确认一帧掉开、工具端跳位或突然增加/消失的独立贴片。
- F07→F00：头胸与工具变化完全沿用 v009；膝踝的实际首尾图没有能具体指认的新裂缝或单帧贴片跳变。首尾 RGBA 差值有所增加，但差值本身不是抖闪判据，没有据此制造返修项。

以上判断来自完整八帧、同帧上下对照、膝踝与双臂连续局部图。此次没有控制共享浏览器，也未另跑 Godot；相邻帧判断的证据范围是逐帧/首尾实际 PNG 对照，正常速度播放由根审查另行覆盖。没有声称任何运行条件下绝无闪烁。

## 接入范围

仅通过当前 south/down 行走八帧、8 FPS、64×96、root `(32,80)` 的关节修形增量。v010 是已烘焙的逐帧像素修形；它不再保证修改后的膝踝外观严格对应 v009 的全部骨端，不是可自动复用于其他动作的重新绑定骨架。制作 README 已明确这点，属于交付范围，不是隐藏缺陷。

现有 1×/4× 对照中未发现需要新增返修的动作身份问题。最终关节观感与完整美术放行由根审查结合实际正常速度播放及用户反馈给出，不用技术导出 PASS 代替。

## 证据

- [逐帧绑定、原可见身份保护与相邻差统计](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/robot-v010-independent/action-audit/joint-action-evidence.json)
- [v009/v010 完整同帧 4× 对照](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/robot-v010-independent/action-audit/same_frame_v009_v010_4x.png)
- [膝踝全八帧 5× 对照](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/robot-v010-independent/action-audit/knees_v009_v010_all8_5x.png)
- [双臂全八帧 5× 对照](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/robot-v010-independent/action-audit/arms_v009_v010_all8_5x.png)
- [独立只读审查脚本](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/robot-v010-independent/action-audit/inspect_joint_revision.py)

所有证据仅写入本审查目录，未修改生产候选、正式角色或 v009 冻结文件。
