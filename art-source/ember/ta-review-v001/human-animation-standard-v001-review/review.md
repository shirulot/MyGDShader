# 人形动画专项规范审阅

日期：2026-10-07。结论：**PASS_SPEC_WITH_CLARIFICATIONS**，仅规范接纳。适用人类A/C后续小样及扩展制作，不批准现有动画。

审阅文件：[专项规范](../../../../docs/shader-learning/human-character-animation-standard-v001.md)，本轮原文SHA256 `d973e35e50ad8767e9d50e650d09ab4cd6a5770ae6d7bcc99b3d7d3b1fcf7cbf`。原文字节另存同目录 `submitted-standard.md`，后续作者修订不覆盖这份快照。对照现行统一规范、TA验收规范、v002循环合同、v003正式返修和v004作者README。

## 接纳内容

角色身份、固定方向投影、真实关节与支撑关系优先于数量；root与身体运动分离；禁止逐帧居中/齐底/缩放或锁腰掩盖问题；不对称部件按解剖学侧登记；可编辑源、姿态、接触与遮挡可追溯。完整正向步态及末首四帧检查、真实动态观察与Godot验收均与现行TA闸门一致。64×96/root(32,80)继续保持。C耳机侧别保留待证，骨盆预算和试样时序不升格为全局硬阈值。

## 执行澄清

1. **阶段顺序（P2）**：§3/§7的八向母版要求用于扩量闸门，不应阻塞当前三组代表小样。先冻结A右下和C左下等本轮方向母版，利用已有源做C八向身份登记，未定方向如实标待审；三组通过后关闭其余方向母版差异再扩量。
2. **循环与单次范围（P2）**：§8的≥10周期、尾首连续只适用于循环段。跳跃、采集进入/退出等按登记状态图完整播放及过渡检查。单次动作允许切向与否、取消点和事件次数先登记；不能把同相位切向实现为再次触发采集、伤害或释放。
3. **跳跃高度归属（P2）**：§4固定地面root不等于锁死角色视觉高度。明确画内升降、独立视觉节点高度与玩法位置各自职责；原图已经画出的腾空位移不能再由节点完整叠一次。
4. **通过范围（P2）**：`production_ready`必须绑定角色/方向/动作/版本及运行验收场景。三类检查通过只覆盖实际审过的交付，不能隐含主游戏速度、交互、碰撞及事件集成通过。

上述边界已纳入统一规范§5.3。作者可在专项下次修订吸收文字，三组小样制作可继续；不要求修改任何冻结包。本轮没有改作者专项原文、素材或脚本。

## 外部参考核对

2026-10-07打开作者页面核对参考职责；未安装工具、购买素材、运行第三方仓库，也未以A/C实测其能力。

- [LPC Revised](https://github.com/ElizaWy/LPC/wiki/Style-Guide)支持统一投影、色板、光向与尺度方法；不移植它的具体网格与配色。
- [Universal LPC](https://github.com/liberatedpixelcup/Universal-LPC-Spritesheet-Character-Generator)的素材许可按条目登记，不能统一写CC0。
- [Hormelz](https://hormelz.itch.io/8-directional-2d-businessman-character)作者页列明八向、256×256、动作JSON/GIF及CC0；方向dir1从左下开始，dir8朝下，需要显式映射。此次只核对页面，未独立核对本地参考下载包身份。
- [Carlos Zepter](https://carloszepter.itch.io/top-down-chibi-character-template)页面列有分离身体部件的.ase文件；[Dead Revolver](https://deadrevolver.itch.io/pixel-prototype-player-sprites)是横版动作参考。都不能凭公开预览声称本地已有完整源。
- [PixelLab](https://www.pixellab.ai/docs/tools/animate-with-skeleton)支持参考角色/骨架编辑，并明确自动骨架需要人工修正；所列输入为方形画布，64×96适配须固定补边/还原。
- [PixelOver](https://docs.pixelover.io/manual/introduction/)列有分层、骨骼、IK、关键帧和3D场景；[Aseprite MCP](https://github.com/letsagents/aseprite-mcp)是编辑器自动操作接口。均不是本项目动画稳定性已得到验证的证据。

## 状态与下一步

v003保持NEEDS_REVISION；v004仍为注册诊断候选，未解除源图形变，也未新增TA运行通过。下一批仍为A右下idle/walk、C左下run及C八向身份登记；按正式素材审查提交可编辑源和真实动态证据。旧左向及v002/v003/v004保持。其他资源线的原有状态不变。
