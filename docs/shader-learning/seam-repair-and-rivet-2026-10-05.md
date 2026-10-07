# 裂图修复 v005 与新角色「铆钉」

## 裂图调查

不仅是渲染器问题。实测 v004 的地板、墙体、水面、岸沿各有 364/644 对兼容接口 Alpha 不一致；地板、墙、水面每组 644 对均有可见 RGB 跳变。v003 虽通过 Alpha 检查，墙、岸和桥仍有 RGB 跳变。原预览还对整张 atlas 做 Lanczos 缩放，会将相邻块颜色混入边缘。

进一步看实际拼图，墙顶和水面还把母稿的独立外框当作内部纹理重复，岸沿分层留下低亮度水纹。原先仅凭位掩码/Alpha 测试判定完成并不充分。调查原始数据保存在 `art-source/ember/seam-repair-v005/` 的 baseline JSON。

## 修复范围

- v005 在 128px 图块的开放接口 8px 边带内统一共享截面；方向按实际共享边/角语义分类，使用中心/直边/窄条作为可靠截面，避免将不同转角平均成缺口。
- 水面与墙顶移除误带的内部外框；墙立面和外部包边保留。岸沿按原水面像素归属清掉漏分离水纹。
- 预览改为逐块裁切后缩放，TileSet 明确启用纹理 padding。
- 管线像素不改。其他类型不重建内部造型，不强加程序方角，不减色。

资源：`assets/ember/environment/autotiles_v005/`，7 张 PNG 和 7 个 `{类型}_terrain_v005.tres`。逻辑格 32 世界单位，贴图 128px，TileMapLayer scale=0.25。覆盖 236 个配置；本轮未复制前版的地板材质变体数量。

场景：`scenes/ember/autotile_sandbox_v005.tscn`，F6。左键画、右键擦、滚轮缩放、中键拖动。水面与岸沿自动同步。

结果：2,960 对兼容接口 RGBA 完全匹配；25,541 格 Godot Terrain 检查通过。GPU 渲染实际使用 Godot 4.7.2 Compatibility / NVIDIA，输出 `godot_render.png`；CPU 拼图 `layout_preview.png` 单独保存，不能将二者混称。真实实例化、纹理尺寸/世界格比例也通过运行检查。

修复的是已定位的断口、串色及错误重复外框。母稿本身仍存在材质重复和个别角部的美术衔接需要审阅，未登记用户已接受全部视觉效果。

## 新角色

「铆钉」：单目履带检修机器人，蓝灰装甲、黄铜护圈、青色镜头、服务工具臂与背部电池。使用 imagegen 生成全新 5×4 四向帧母稿，材质风格参考用户认可的工业场景。

- 原始母稿、提示词、来源记录：`art-source/ember/rivet-v001/`。
- 四向造型图：`assets/ember/characters/rivet/rivet_turnaround.png`。
- 动态预览：同目录 `rivet_motion_preview.gif`。
- 正式裁片：128×160 RGBA，共用缩放和脚底锚点 (64,136)，保留明暗、未压成 16 色。整图 `rivet_atlas_v001.png`。
- Godot 资源：`rivet_sprite_frames_v001.tres`，四向 idle / walk 共 8 个 clip。
- 可操作场景：`scenes/ember/rivet_character_preview.tscn`，F6，WASD / 方向键。

**一帧已明确排除**：朝下母稿第 4 列（down_03）把左右工具画反。朝下移动目前使用 3 帧，其余方向各 4 帧；共 19 个使用帧，错误帧保留在来源与图集中用于追溯，不进入动画。动画是可运行预览，尚未标记最终美术验收通过。Godot 已实际重新加载 8 组 SpriteFrames，并测试移动输入与回到待机。

旧角色与主游戏没有替换，便于对照新形象。

## 复现

```text
python tools/repair_ember_seams_v005.py
python tools/build_rivet_character.py
godot --headless --path . --editor --import --quit
godot --headless --path . --script res://tools/build_ember_autotiles.gd -- --revision=v005
godot --headless --path . --script res://tools/build_rivet_character.gd
godot --headless --path . --script res://tools/check_ember_preview_runtime.gd
godot --path . --script res://tools/capture_ember_seams.gd
```

GPU 捕获必须使用图形渲染后端，不能以 headless 输出冒充 GPU 验证。
