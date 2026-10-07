# 06.2 水面素材对比（课后追加，2026-10-07）

用户要求先试项目中已有的水 tile，再生成一张水面图，保留两者并查看实际效果。

## 运行入口

- `scenes/chapter06/ch06_02_heat_haze.tscn`：原 06.2 入口已换成生成水面，仍使用原来的学习 Shader，可继续编辑。
- `scenes/chapter06/ch06_02_water_compare.tscn`：在 Godot 打开后按 F6，左右并排显示两版水面。
- `scenes/chapter06/ch06_02_water_existing.tscn`：已有 tile 版，单独显示。
- `scenes/chapter06/ch06_02_water_generated.tscn`：生成图版，单独显示。
- `scenes/chapter06/ch06_02_heat_haze_calibration.tscn`：保留原校准底图，便于回看直线如何被采样偏移。

## 两张素材

| 版本 | 运行纹理 | 来源与尺寸 |
|---|---|---|
| 现有 tile | `assets/ember/vfx/water/ch06_water_existing_v001.png` | v007 水 atlas 的纯中心格：Rect(768,640,128,128)，按原生尺寸 4×4 拼成 512×512；不拉伸原 tile。 |
| 新生成水面 | `assets/ember/vfx/water/ch06_water_generated_v001.png` | 内置 image_gen 生成的 1254×1254 RGB 原图，逐字节复制到项目；Sprite 缩放为 512×512 显示。 |

生成图母稿保存在 `art-source/ember/chapter06-water-preview/water_generated_master_v001.png`；
最终提示词保存在同目录的 `water_generated_v001.prompt.txt`。两张素材各有来源记录：
`existing-provenance.json` 和 `generated-provenance.json`。新图用于本 Shader 演示，尚未作为无缝 TileSet 验收。

## 预览用的代码

捕获过程中原学习 Shader 正在被编辑。为了让两版比较可重现，水面独立场景使用
`scenes/chapter06/ch06_02_water_preview.gdshader`，这是保存时原 Shader 的逐字副本。
它保留原来的 TIME、Noise 采样和横向偏移公式，没有另做水面动画算法。
保存时的 Mask 分支已被注释，所以这段对比是**全图横向波动**，不是仅圆形区域波动。
原文件 `ch06_02_heat_haze.gdshader` 继续保留用户的编辑。

两版均使用同一代码副本、Noise、Mask 绑定、Linear 采样、Repeat Disabled 和
`noise_speed=0.1`。最大横向偏移是 `0.01` UV，即显示宽度的 1%，两版均为最多 5.12 显示像素。
生成图保留 1254 原生像素，因此源像素位移最多为 12.54，再乘 Sprite 缩放得到相同显示位移。

现有 tile 纹理低对比，移动比较含蓄；生成图的曲线水纹更明显，便于观察横向采样变化。

## 实际效果与验证

`art-source/ember/chapter06-water-preview/water_compare_gpu.png` 是 Godot 4.7.2、
OpenGL Compatibility、RTX 4070 Laptop GPU 的实际输出，不是 AI 合成的运行截图。
同目录 GIF 和无损动画 WebP 均由实际 GPU PNG 帧封装，未重绘水面。
GIF 受调色板格式限制；WebP 保留无损帧。动画按照实际捕获时间差播放。

36 帧全部为 1112×680，两侧水面各 512×512；两侧每次相邻帧比较均有像素变化，
图框以外的标题和说明区始终没有像素变化。素材原文件哈希与来源记录一致。
捕获请求是 3 秒／12 FPS，实际捕获跨度为 4.890449 秒；这些数值是捕获记录，不是游戏性能结论。
短片会重复播放，未将它处理成完整 Shader 周期的无缝循环。

完整记录见 `capture-report.json`、`animation-report.json` 和 `validation-report.json`。

## 重现预览

已有素材可用 `build_existing.gd` 再次拼装；这会重写派生 PNG 与拼装来源记录。
GPU 录制必须使用正常图形渲染，不能加 `--headless`：

```powershell
& 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe' --path 'E:/dev/shader/godot-shader/godot-shader-simple' --script 'res://art-source/ember/chapter06-water-preview/capture_compare.gd'
```

录制脚本输出实际 PNG 帧；`encode_animation.cjs` 使用 sharp 封装 GIF 和无损 WebP。
