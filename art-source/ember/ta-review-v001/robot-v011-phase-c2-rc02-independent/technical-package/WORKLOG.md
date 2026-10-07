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

## B1 rc01 撤回与 rc02 返修

B1 rc01 曾固定为575个载荷，ZIP 10,860,493 B /577条目，SHA `6b082c9f3db5e4138a828257e4a1555a18da0e6b6dbe9bc73eb2a96502ebd8ad`。提交后制作侧主动发现 NE/SE 摆臂与同侧腿同向，撤回美术放行申请。TA正式回执 `qa/ta-receipt-phase-b1-rc01.md` 独立确认步相P2；局部关节、来源和已做审计结果保留。此前所称catalog SHA `c319f53a4c0e0f5eccf3015972dc209bc7b1145a1e5cdbfac613dc474c1a1b23` 对应sha256-manifest.json，walk-batch-metadata.json为 `bc8cda346f5e99d1fac8ef2ae10b2ea2d05cbf27401c35f8a0b18b0b3b000d1e`。

rc02 反转 NE/SE 摆臂投影，N采用纵向手腕反相与定长双骨求肘；body与腿/靴变换完全保留。三向局部新imagegen肩肘源、prompt与当时实际输入均已保存，只合成旧/新手臂覆盖范围。NE (22,59) 原腕部像素从body归回左前臂，保持RGBA，避免反相后留下孤点；掩膜额外包含这一像素的前后位置。没有补画细线或整人重生。

实际差分确认S/SW/NW的24帧与8母版原字节保持，24返修帧掩膜外差0，刚性保护区差0，静态实拼差0，无独立alpha碎点。`qa/arm_phase_revision_evidence.md/json` 包含三向全部八帧左右肩肘腕/髋膝踝、修前后与骨点图。浏览器已核对N/NE/SE正常浅底、慢速深底与F07→F00，记录是离散截图。

rc02导出56图/48动图PASS；重新实际GPU112样本、六向各两圈、32同相位切向PASS，新atlas SHA `137196518cba1eabfcb8b58579a33fe493ad6865ed8304426f98414ff6a42f01`。Skill动作审计仍有三条小步幅提示，未以消除警告为由变更已通过SW。准备另冻B1 rc02交TA增量复审，不修改旧冻结包。

2026-10-07 B1 rc02已冻结：695载荷 / ZIP696条目，14,354,117 B，ZIP SHA b301fdea0e3f634d02a0da4eac437e1ce890515b582216daadc82c82211b4aaf。sha256-manifest.json SHA b5b7c17e7a8574927dc7bfcab871a6a55e1a41da6a3e52c3fa230b955864f9c0；walk-batch-metadata.json SHA 5adc21d2224c9289b8659a376e4e8a4f22b973be9468eb81995eeb496c332990。ZIP逐项哈希差0；新冷副本实际Godot112 GPU样本、六向各两圈、32同相位换向PASS。外置记录qa/cold_delivery_validation_b1_rc02.json，未回写冻结包。

B2准备：W/E各11个固定片已登记，隐藏肢体来自一次imagegen完整部件源，登记只执行一次，8帧不做bbox缩放。可见原母版像素覆盖隐藏源，侧面中性姿态实拼均0差、body无手腕/脚部残点、全部IK可达。正在生成对应侧面关节局部编辑稿；原始排姿不能当最终素材。

B1 rc02正式TA PASS：NW/N/NE/SE 32帧通过，旧步相P2关闭；加S/SW当前六向walk48帧通过，未来帧不继承。回执qa/ta-receipt-phase-b1-rc02.md，按原字节绑定登记source/walk-acceptance-v011.json。
B2 rc01 W/E新增16帧已装回局部imagegen补丁，前批56文件保持。72图/64动图、实际Godot144GPU样本、八向各两圈、64次相邻同相位切向PASS。新atlas d048f38b527ed137c4fa6be137c74ca7ff482acf6c965daea5790a4a04d83cea。独立侧向来源、相位、工具侧报告qa/side_walk_evidence_v011.json；侧向待TA复审。UI已更新六向通过状态，未改实际PNG/图集。

B2 rc01已冻结：882载荷 / ZIP883条目，16,594,983 B，ZIP SHA 538d7bb49eb2e4480046eee50306a232b7a3f130219564e1618dbfbfff19164c。manifest SHA 029f4be1debf25a02cad16ed93deba08f29cc0826456b9653280db4bca2d2f0e；walk metadata SHA 10da92ebabd495ff080732fa39f251a30ed734e8d0e95fdceaeadb42ec3c729d。逐项hash零差，独立冷副本实际144GPU、八向两圈、64换向PASS。外置记录qa/cold_delivery_validation_b2_rc01.json。

阶段C1：先做已过SW的idle2/collect4六帧小样。新增body/pelvis分片采用原body两行重叠，原母版中性实拼RGBA零差。idle帧1仅胸头肩臂上移1px，骨盆双脚不动；collect双脚固定、身体下压2px、工具臂前摆，末帧严格回idle基准。原始排姿已输出，连接补丁生成中；未声称最终动作通过。

C1第一张采集连接编辑稿改变了F01/F02下压幅度和手臂姿势，并带有发光背景，登记为REJECTED_NOT_USED。未装回素材；正按严格原姿势叠合要求重试。待机编辑源已保存，后续只允许第二帧腰部接缝。

B2 rc01正式TA PASS：新增W/E 16帧通过，八向walk64帧全部完成阶段验收。登记source/walk-acceptance-v011.json，C1前复核全部64帧与8身份母版原字节，72文件不变。

C1 rc01待机/采集六帧已合成：idle改动0/10像素、collect改动5/80/71/0像素；保护区与掩膜外改动0。collect F01/F02身体/腿/远臂相同排姿复用同一接缝，避免保持帧重画。idle下半身固定，collect鞋底固定，collect F03与idle F00相同。第二张采集imagegen源只使用受限局部，背景伪影未装回。两张有效编辑源与一张拒绝稿的实际输入、prompt、SHA已登记。

15图/16动画导出PASS；实际Godot30GPU样本、idle与walk各两圈、collect四帧非循环一次完成后回idle F00 PASS。补充包外输出参数后重跑仍PASS，exit0/stderr0。Skill方格诊断只加透明边，idle与collect均错误0警告0。制作方检查联系图和浏览器正常/慢速、深浅底、F01/F02、末帧回位；截图仅离散观察。新动作美术仍待独立TA，未把技术结果当作视觉放行。

## C1通过与C2完整动作候选

C1 rc01已冻结858载荷，ZIP19,576,548B/859条目，SHA `0c62177198973b24bb3fbfcc306ba4617af3ad754eb5a0696bdfddb4f19f51df`。冷副本实际30GPU及collect回idle通过，858载荷不变。TA正式回执`qa/ta-receipt-phase-c1-rc01.md`确认SW新增idle2/collect4六帧PASS，登记`source/action-acceptance-v011.json`。当前已通过70动作帧和8身份母版。

C2 rc01补余下S/W/NW/N/NE/E/SE各idle2+collect4，共42新帧。S从保留的F02身份建立单独双脚中性源：右小腿/靴整片向下1px，加5个局部imagegen膝内芯像素。新源SHA `3f87b8de245deebbf24f02c711ab85226ef41fd77edc1164753fb0281f46d4dd`，旧身份和walk不变。七向各12片，中性实拼零差，S body/pelvis重叠58–59行，其他54–55。S/N采集下压1px以匹配正背投影，其他2px；全部IK无钳制、脚踝不移动。

14个imagegen编辑源、确切输入、提示词与哈希登记到manifest。通过限制掩膜、固定甲片/工具/靴保护、F01/F02共享相同姿态区域，保持原比例。E idle初步产生两点暗色孤点；批量路径加入“新增像素必须接触原始不透明轮廓”规则，排除生成光晕而非画连接线。已通过SW分支行为不变。S/W/NW/N/NE/E/SE的idle改动分别0/3、0/2、0/6、0/0、0/4、0/11、0/10；collect分别10/75/71/0、0/15/15/0、6/82/77/0、9/79/67/0、10/44/40/0、4/22/23/0、8/88/78/0。保护区与掩膜外差0。

完整24段112帧、192个动画导出PASS；已通过70帧与8母版字节保持。统一atlas SHA `c9963cd1f9c1db11a932164c57eefde0ed80e2de692f0d3700338d7bddba6cc1`。独立Godot完整工程实际224个GPU图、16条自然两圈、8向采集完成回idle、136次切换均PASS，exit0/stderr0。首次脚本类型推断错误已修复，早期import日志是历史失败，最终实际GPU通过才是本次有效结果。

制作方检查六张深浅联系图和七向网页慢速采集关节，SE正常采集结束确实回idle；截图为离散证据。全idle/collect skill审计错误0警告0。新入口`action-batch-review.html`和`godot-full-review/project.godot`。42新帧及S中性源仍待独立TA；下一步冻结C2、从新解压包实际GPU验证后送审。不改旧冻结包或主工程。

C2 rc01已冻结并送TA：1702载荷，ZIP35,015,025B/1703条目，ZIP SHA e0a5fe91bcd62509d0f342e45334ce34cf374ebea1ac0203162d9b90f79b5643，catalog SHA 27b6448dbb0de738fc87b45dc17924dafedec3af8dee47f4512f256a4f02ba4d，full metadata SHA 8072ce3ef444d8c2d3c13cf072380c7398385997b008c01269d0bb3c6d210b6e。新冷副本实际224GPU、16条两圈、136切换、8条采集恢复均PASS，exit0/stderr0；冻结/ZIP/引擎运行后冷副本1702载荷hash零差。包外回执qa/cold_delivery_validation_c2_rc01.json。已通过70帧和8身份母版不变，42新帧及S中性仍待独立美术结论。

C2 rc01独立复审先行确认局部P2：SE collect F01/F02肘外暗边被亮甲色覆盖，在浅底读成悬空暗点/短线；非Alpha断肢、非body残边。rc02通过扩大原rig轮廓保护，只恢复每帧(x14,y52/53/54)三个源像素，合计6点；其余110帧逐文件hash原样，源片/骨点/工具/鞋/时序不改。变更证据qa/se_elbow_rc02_revision.json、来源和深浅局部/整帧对照，网页已复查两帧与正常回idle。新版112PNG/192动画导出、224实际GPU、16条自然两圈、136切换及8条采集回位均PASS，atlas 0340a11ca59efdb18c64385fa24ec8faa833f0c3c6b056b5c6a97d3f3f5b4268。rc01固定包保持不变，rc02待新冻结与TA复核；整体C2回执尚未收到，未将新增42帧美术擅自放行。
