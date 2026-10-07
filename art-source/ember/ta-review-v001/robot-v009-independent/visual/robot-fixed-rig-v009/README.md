# 机器人脚部修订 v009

朝下行走 8 帧，8 FPS，原生 64×96，root (32,80)，512×96 图集。本版是用户脚踝反馈的局部修订候选，等待技术美术复审。

## 查看

- `foot-compare.html`：v008 与 v009 同帧同速播放，原生/4×、脚部固定局部、慢速、逐帧及浅底。当前本机入口 <http://127.0.0.1:8139/foot-compare.html>。
- `review.html`：同源母稿、关节轴及接触点对照。
- `previews/robot_walk_down_fixed_rig_v009_two_normal_loops_4x.gif`：实际原生帧导出的循环预览。
- `godot-review/project.godot`：独立 Godot 工程，真实 SpriteFrames 1×/4× 播放。
- `research.md`：网上参考、旧版问题帧与本项目的取舍。

## 修改内容

保留 v008 的 23 张部件 PNG、17 个袖套/关节结构和同一相机投影。冻结原始母稿 SHA256 为 `c65f68455554edb03aea0a7b7b3cea6e1a779fa9d5aa49cba9b4aa5c4f6fbfff`；静态绑定母稿与 v008 精确相同。

新增 `source/foot_motion_v009.json`：先控制刚性鞋的脚跟/脚尖枢轴和俯仰，从鞋计算踝点，再求固定长度的腿部 IK。最大抬脚由 3 px 降为 0.8 px，最大下沉由 1.6 px 降为 0.8 px，鞋俯仰为 -4° 至 +3°。左右相差四帧，原生源造型的左右差异保留。头胸、手与工具源层、部件数量、材料、光向及手臂运动方式沿用；身体上下位移幅度有所收敛。

小腿最短投影从原骨长的约 22.6% 增至 52.1%。这是姿态修改的量测结果，并非通用合格阈值；没有强制拉长投影或修改实际骨长。结构、靴口体积、承重和过渡仍需直接观察。

## 接触数据含义

`contacts.*.contact_world` / `contact_projected` 为独立鞋控制器的脚跟或脚尖枢轴；`sole_world` 是鞋底中心，滚动时允许高于地面。`actual_gpu_contact_pixel_alpha` 沿用 v008 的字段名，表示源鞋底登记像素映射后仍为实体的取样，不能单独证明物理脚跟/脚尖与像素轮廓完全一致。

本版鞋面仍是浅角度 2.5D 平面投影，仅支持这次的小角度姿态。大幅转脚需要从同一结构补充鞋底/侧面；本小样不验证主玩法移动速度、脚与地图碰撞或其他朝向动作。

## 证据与复现

- `qa/foot_motion_comparison_v009.json`：旧新逐帧投影、源层哈希、可见部件来源映射。
- `fixed_rig_render_v009.json`：真实 GPU 渲染，固定骨长/源层/调色板及二值 Alpha。
- `fixed_rig_playback_v009.json`：8 个实际导入图集区域、16 个 1×/4× GPU 对照、自然播放两轮。
- `qa/export_validation_v009.json`：整格导出与编码保真。
- `alpha_structure_diagnostic_v009.json`：透明实体连通诊断；连通不等于美术通过。
- `qa/production_protection_v009.json`：正式角色文件保护校验。

在项目根运行源帧渲染：

```powershell
& 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe' --path 'art-source/ember/robot-fixed-rig-v009/godot-review' --script 'res://render_fixed_rig_v009.gd' -- --workspace='E:/dev/shader/godot-shader/godot-shader-simple'
```

该命令会重新渲染候选并更新证据；固定交付后应在新目录复现，不能覆盖已交审版本。格式导出工具是 `tools/export_robot_fixed_rig_v009.cjs`。

交付携带 `godot-review/assets/robot_walk_down_atlas_v009.png.import`，明确关闭 `process/fix_alpha_border` / `process/premult_alpha` 与 mipmap，保持含透明区域在内的完整 RGBA 契约。冷解包验证结果在交付目录的独立报告中绑定 ZIP SHA256。

v008 原帧、原包与正式角色资源均保留；这版没有接入主玩法。首次姿态试验的半纹素边界映射诊断保存在 `draft-01-half-texel-review/`，不属于成品候选帧。
