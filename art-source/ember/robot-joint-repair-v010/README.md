# 机器人关节修复 v010

朝下行走 8 帧，原生 64×96，8 FPS，循环，固定 root (32,80)。这是在 v009 步相上进行的逐帧局部修形候选，尚未接入正式角色。

## 查看和使用

- `joint-compare.html`：v009 / v010 同帧同速对照，可看原生 1×、4×、逐帧、慢速与深浅背景。本机入口 http://127.0.0.1:8140/joint-compare.html 。
- `frames/robot_walk_down_f00_v010.png` 至 `f07`：8 张完整透明整格 PNG，禁止按帧 bbox 再缩放、齐底。
- `robot_walk_down_atlas_v010.png`：512×96，横向 8 格。
- `previews/`：深浅底 1× / 4× GIF、联系表、透明无损 WebP。
- `godot-review/project.godot`：独立 Godot 工程。空格暂停，左右键逐帧，B 切换背景。
- Godot 集成使用 `godot-review/robot_sprite_frames_v010.tres` 和同目录 `assets/`。AnimatedSprite2D 使用 nearest，centered=false，offset=(-32,-80)；项目纹理缩放应为整数倍。

## 这次修改

之前的关节在像素上连通，但窄连接、横穿肢体的深色带，以及上下独立描边的关节盖，仍会读成断裂。尤其 F02 / F06 的膝部，旧轮廓有明显的横向断面。

本次用图像编辑生成关节修改稿，再在固定格坐标内局部合成。膝、踝、肘把盖面、内骨架及盖面边缘一起替换，使上下结构形成承接；肩、髋、腕使用局部中间调补足连接。更改范围见 `qa/before_joint_regions_v010.png`：S 肩、E 肘、W 腕、H 髋、K 膝、A 踝。标记覆盖检查和编辑区域，并不声称每个标记处都有独立透明裂缝。

头、胸、双手、腕部工具的原可见像素，以及编辑遮罩外全 RGBA，均与 v009 完全一致。局部关节共更改每帧 286–328 个像素，包含每帧 0–3 个旧轮廓像素的清除。完整改动账本和原/新 RGBA 位于 `qa/local_composite_v010.json`。

原生成稿为 1448×1086；只有生成稿以一次统一 nearest 变换映射到 256×192 联系板，再量化到原有 11 色。原 v009 PNG 没有重采样、逐帧缩放或重定位。生成稿连带改变了其他部位，因此整张生成稿不作为成品交付。成品是上述局部合成后的 8 张 PNG。

本版是已烘焙的逐帧像素修形。v009 的骨架只用于定位与保留步相，本版不能宣称所有修改后的轮廓仍严格对应原 3D 骨端，也不支持把这些补丁自动套到其他动作上。后续动作需从同一结构重新出帧并复审。

## 专用 skill

采用本地 `game-character-sprites` 的参考锁定、单动作单朝向、固定格导出和逐帧检查流程。它默认正方形格和逐帧包围盒装配；本项目保留已经锁定的 64×96 规格，不使用会逐帧重缩放的默认装配脚本。其只读审计脚本在 `qa/audit_sprite_motion_rect.py` 中仅适配了矩形格，检查结果见 `qa/skill_motion_audit_v010.json`。

另参考 [pixel-art-sprites](https://github.com/omer-metin/skills-for-antigravity/blob/main/skills/pixel-art-sprites/SKILL.md) 的轮廓、像素簇、原生尺寸与有限色板规则。该 skill 是制作指导，不是能保证关节正确的专用生成模型。本次未安装新的全局 skill 或接入收费服务。详细筛选见 `skill-findings.md`。

## 验证与制作源

- `qa/export_validation_v010.json`：固定格、二值 alpha、原色板、编辑范围保护、GIF 解码保真。连通数只作诊断。
- `fixed_rig_playback_v010.json`：真实 Godot 导入区域全 RGBA 比对、16 个 1×/4× GPU 比对、自然播放两轮。沿用验证器文件名，不能理解成重新绑定过的骨架。
- `qa/production_protection_v010.json`：正式角色及 v008/v009 冻结文件保护。
- `source/joint_edit_raw_v010.png`、`prompts/joint_edit_v010.txt`：生成原稿与实际提示词。
- `source/reference-v009/`：这次合成所用原帧、部件归属图和姿态数据。
- `build_joint_patch_v010.cjs`：固定格采样、量化与遮罩合成；`export_and_validate_v010.cjs`：预览导出与数据检查。依赖 Node.js 和 Sharp；冻结交付请先复制整个目录再重建，避免覆盖送审像素。

技术通过不代表用户的关节观感已验收。视觉状态与独立复审回执以 `run-manifest.json` 为准。v008、v009 已因用户关节反馈标记需要修订。
