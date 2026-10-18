# 赤隼八向静态切图 v001

从已去掉两个多余头角的 `red_falcon_8dir_horns_removed.png` 裁出；没有重新生成、镜像或补绘角色。

- `game_128/`（ZIP 内）：8 张 128×128 透明 PNG，脚底根点 (64,104)，Nearest，共同缩放 0.25，二值 Alpha。
- `source_512/`：8 张 512×512 透明 PNG，脚底根点 (256,416)。保留裁切区域原始 RGBA 和像素细节，用于后续单方向制作。
- 顺序：down/S、down_left/SW、left/W、up_left/NW、up/N、up_right/NE、right/E、down_right/SE。
- 方向名继承原设定图标签；本次不重新设计原图的侧向姿态，不声明已通过八向造型或动画验收。
- 源图每格先独立裁切，再透明补齐成正方形。共用地面线 y=554；X 在静态母版阶段按两脚接触区域校准一次。源坐标、偏移与 SHA256 见 manifest.json。
- 128 版只是规范尺寸导出，并非人工逐像素重绘。原图仍有的细节或造型问题会保留。

Godot 中使用 128 版：Sprite2D 的 centered=false，offset=(-64,-104)，纹理过滤 Nearest。scale=(1,1) 时画布为128世界单位；实际可见主体尺寸见 manifest。此交付未改动现有场景或玩家。

重跑脚本需要 Python、Pillow、NumPy。脚本仅写本批次专用目录，并验证源文件未变、八方向完整、裁切像素一致、128版二值Alpha与边缘无截断。
