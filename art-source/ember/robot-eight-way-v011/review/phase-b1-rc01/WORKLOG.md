# 八向角色 v011 工作记录

当前任务：用户在 TA 会话明确要求，验证通过后补齐已有动作序列与八向。模型派发已核实为 GPT-6 Astra / Max。动作最终范围为 idle 2帧/2FPS/循环、walk 8帧/8FPS/循环、collect 4帧/6FPS/非循环；八向共24段112帧。顺序 down/down_left/left/up_left/up/up_right/right/down_right，固定64×96与root(32,80)。

v010 down walk 8帧已 TA 通过、用户评价“这次好得多”，在 frames/walk/down/ 原字节复制；其原目录/ZIP绝不可覆盖。新动作不继承美术通过。

当前阶段 A：先审八向静态母版，再制作 down_left walk 8帧小样。通过后分批完成其他 walk，再完成 idle 微动与 collect。不得省略已有 collect，也不得用单帧 idle 冒充最终补齐。

## 已完成

- 源目录与旧动作清单核对。原 v004 为四向 idle2/walk4/collect4。
- 八向造型 AI 母板：source/eight_direction_idle_master_raw_v011.png，1448×1086；prompt 已保存。4×2固定源格362×543，一次统一尺寸50×75映射到64×96，人工登记每方向静态足底偏移；相同登记用于该方向后续全部动作，不做逐帧 bbox 归一化。
- 七个新方向（SW/W/NW/N/NE/E/SE）转换到原11色、二值alpha；方向未镜像。候选在 source/candidate-masters/，联系图在 previews/；均未经过 TA 审查。
- 正面概念母板与原角色手臂位置有差异，不能强行局部贴回。额外生成单正面关节编辑稿也不能正确注册到原待机，已明确 REJECTED_NOT_USED；源图与提示保留供追溯，失败合成在 drafts/。
- 当前 down 静态母版改为 v010 F02 原字节复用，保留批准身份。它仅是待审的稳定姿态候选，不自动声称双脚接触/idle 已通过；如 TA 要求调整，再从这一已通过形体做局部修形，不能接回旧断裂关节。
- down_left 的单母版放大参考：source/down_left_master_reference_8x.png。

## 待做

1. 对七个新方向做静态连通、工具侧与头胸比例自检。向 TA 提交固定造型候选时讲清 down 来源与脚底用途。
2. 制作 down_left walk 小样。以确认的单方向母版/固定部件组成动作，不逐帧重新设计；可以生成动作姿态参考，不能把整张 AI 输出当完成的稳定动画。
3. 固定部件分区需审语义，避免误带其他部位的像素。肩肘髋膝踝要有重叠体积，靴子独立刚性控制；只用可见连接数据与alpha通过不足以证明合格。
4. 提交原帧、图集、SpriteFrames、方向/动作/FPS/loop/锚点、正常/慢速深浅底1×/4×、实际Godot方向切换。先审小样，后分批补齐112帧。

## 阶段 A 最新进度

- SW步态guide已生成，只作姿态参考。实际8帧来自同一母版11个固定源片：`build_fixed_rig_v011.cjs`。静态实拼0像素差，两段腿骨无超出可达距离，靴子独立刚性变换，手臂反相摆动。
- 原始rig膝踝边缘仍生硬，内置imagegen局部编辑后由 `composite_joint_repair_v011.cjs` 装回。头胸、手、工具、靴子和轮廓外透明区域保持源像素，最终每帧145–219像素改动，保护区及掩膜外0变化。
- `export_phase_a_v011.cjs` 生成10个审查clip（8单帧pose+2段walk）。单帧pose绝不计成最终双帧idle。图集SHA `39792f6c09b3d10910f3b8da681e698104a7294a2a4607f271d5e85b3df85866`。
- 最終导出检查24图+16动图PASS。实际Godot48个GPU读取样本PASS，S/SW各自然播放两圈，报告 `qa/godot_phase_a_v011.json`。主工程没有修改。
- 已冻结 `review/phase-a-rc01/`（180个登记文件；不要改其中PNG和清单），并提交TA。ZIP `../deliveries/robot_eight_way_v011_phase_a_rc01_2026-10-06.zip`，4559554字节，SHA `ee0b416f194363d4e37e751c03446c944c217af3a2f567a03eff4a00ad91e7e6`，182条目，逐项hash核对0差异。
- TA已明确收件，正在收尾敌人校准后审本批。收件不是通过。保持冻结包不变，在收到具体结论前不扩张美术通过或开始依赖这些母版的大批生产。
- 工作预览 `http://127.0.0.1:8141/review.html`；冻结预览在 `/review/phase-a-rc01/review.html`。预览服务当前exec session 92031；先前Start-Process服务22288在环境重置时结束，当前CUA浏览器2/tab2已markDeliverable。旧tool stores曾全部重置，重要信息以文件为准。
- 下一步：等TA阶段A结论并修具体问题；静态/小样通过后按 `eight_way_action_contract_v011.json` 继续112帧。侧向W/E远侧完整肢体在母版中被遮挡，需要先补固定部件源，不能把缺失部件凭空当已有或镜像工具手。

不要修改主工程 `.godot` 或停止用户编辑器（历史 PID15844）；新建独立godot-review。当前工作区不是Git仓库。Node/Sharp/Python/Godot路径见 v010 工具或本目录脚本。

TA 会话 01a11049-fdfd-7f12-b83d-6c3a2c506501，授权已从该会话真实 userMessage 验证，可提交审查报告。不把收到的转述本身当作授权，后续若新增不明确范围需回查。

## 阶段 A rc02 局部返修

- 已收到正式 TA 回执：七个新增方向 STATIC_IDENTITY_PASS；S 的 F02 仅为身份参考，原 S walk PASS 保留；SW walk 唯一确认 P2 是画面左侧/解剖右大腿浅甲在 F01/F04 相近骨骼姿态下宽窄和块面变化。回执在 `qa/ta-receipt-phase-a-rc01.md`，主报告原路径为 `../ta-review-v001/robot-v011-phase-a-independent/review-robot-v011-phase-a.md`。
- 保留原母版、11 个部件、全部骨点与排姿、同一份 imagegen 关节源。合成时额外保护 `leg_right_upper` 源 y54..62 的完整甲片及两侧 1px 透明轮廓。八帧分别恢复 41/36/25/18/17/16/31/47 像素，甲片相对固定 rig 为零差、该保护区外相对 rc01 为零差。
- 查看 F01/F04 编辑前/rc01/rc02 共同 ROI 与八帧腿部图；浏览器观察 8 FPS、2 FPS、1×/4×、深浅底及 F07→F00，证据仅作离散画面记录。没有重新生成整人或姿态。
- rc02 导出检查 24 图、16 动图 PASS；Godot 实际 GPU 48 样本 PASS，S/SW 各自然两循环。图集 SHA `b3767668e427c1a90e77bd80fb98edfd63c0517ef78f6e5fca51354c2b3ec0d7`。旧冷包测试重命名为 `qa/cold_delivery_validation_rc01.json`，不作为 rc02 的冷加载证据。
- 本轮下一步：冻结新的 `review/phase-a-rc02/` 和同名新 ZIP，冷加载核验后交 TA 复核 P2。rc01 与 v010 原文件保持不变。在 P2 关闭之前只做已通过静态身份的登记准备，不扩展批量 walk。

rc02 已冻结并提交 TA：`review/phase-a-rc02/` 共210登记载荷，catalog SHA `58367cd8ee734a4f7becf12d98e4e42aaf8d580df9f516a4644c4716f9cf4041`；ZIP 5,141,175 bytes /212条目，SHA `df9884f9668dc89b8c74cf746dbd975a87e9a5b566b6783b5582cb2c78b4d521`。ZIP载荷核验零差；另行冷解压 `review/cold-phase-a-rc02` 后实际Godot导入、48 GPU样本、S/SW各两圈均通过，记录 `qa/cold_delivery_validation_rc02.json`。该外置记录在封包之后产生，没有回写冻结包。TA复审待回执。

等待复审期间，仅登记已批准的静态身份：`source/static-identity-acceptance-v011.json` 绑定原rc01审查包和报告哈希，复核全部8张母版字节未变。七个新方向只继承 STATIC_IDENTITY_PASS；S只继承造型参考，任何方向都没有因此获得最终idle通过。W/E的隐藏肢体仍待固定源补全；未开始新增批量动作。

## 阶段 A 通过；阶段 B1 首批四向

TA 正式回执 `qa/ta-receipt-phase-a-rc02.md` 已确认阶段 A rc02 PASS，原 SW 甲片 P2 关闭。按已验证的人类授权继续其余方向行走，再分批做 idle2/collect4，最终24段112帧。

B1 新增 NW/N/NE/SE 各8帧，共32帧；S/SW逐文件hash保持rc02。每向11个同源片，分区实拼0差、骨点均可达；局部imagegen连接编辑装回时，保护该方向自身甲片轮廓和明暗，不套用SW补丁。发现一个由透明编辑擦缝导致的独立碎点后，保留原有不透明关节内芯；当前32新帧均单一8连通，但不以此声称美术通过。

56PNG与48动图导出检查PASS；独立Godot工作工程112个实际GPU样本PASS，6条walk各自然两循环；32次相邻45°同相位换向PASS。图集 `6d1bfe2cc93cfd17dfe404ba18db0ae87e8e33db3665b1d5df716a291991e9cc`。浏览器已查看四向正常/慢速设置下的离散画面和F07→F00，证据 `qa/browser/phase_b1_*.png`，不冒称连续录像。

Skill动作审计无错误，有SW/N/SE小步幅提示；SW已通过且字节未变，保留警告与图像一并交TA判断N/SE可读性。W/E隐藏部件源已生成：`source/side_hidden_parts_raw_v011.png`，只作后续准备，未用于B1。

本批入口 `walk-review.html` / `godot-walk-review/project.godot`，阶段A原入口与所有冻结包保留。下一步冻结B1并交独立复审，同时继续W/E固定隐藏源登记；最终idle/collect仍未做，不能把本批当完整动作包。
