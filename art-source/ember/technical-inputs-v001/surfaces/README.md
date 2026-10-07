# D09 / D11 / D12 技术输入

本目录记录 10 张程序派生输入及其可编辑几何、高度场、测量和审阅证明。
catalog.json 的 assets 数组是集成入口；PNG 位于各条目的 res://file。
构建器和核验器只使用本机 Python、NumPy、Pillow，不使用生图接口。

```powershell
& 'C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' art-source/ember/technical-inputs-v001/surfaces/tools/build_surface_inputs.py
& 'C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' art-source/ember/technical-inputs-v001/surfaces/tools/validate_surface_inputs.py
```

建筑高度由登记的部件轮廓、真实 Alpha 和低起伏平面/倒角产生。station 与 console
保留各自画布和锚点，安全窗口及其一像素邻域为恒高平面。外部透明像素的法线
统一为 (128,128,255)，RGB 法线的裁剪由原底图 Alpha 提供。

floor_clean 高度来自已验收原生整理脚本的板缝、装配压痕，底图采样区是
ground_details 图集左上 [0,0,32,32)。四边两像素高程保持零，支持周期采样。

metal 以底图中确切的 #566B78 涂层标签建立可追溯的分区，登记的微表层缝高差
不超过 0.06 个艺术原生像素单位。使用环形 5×5 二项低通并在已登记 5px 接边带
归零；首尾法线和高度梯度一致。没有从亮度取高度，也没有添加底图不存在的大板格。
concrete 明确使用平面高度 0，避免把聚合斑颜色误认成实测表面凹凸。

所有高度是供教学灯光使用的艺术近似，不是物理尺寸、深度测量或真实三维模型。
heightfields/*.npy 为 float32 [y,x] 源，高度预览的 0..255 自动归一化只用于看图。

法线使用 OpenGL +X,+Y,+Z。PNG 图像 y 朝下，因此
n = normalize((-dh/dx × strength, +dh/dy × strength, 1))。
strength 已烘入 RGB：station/console 0.85，地板/金属/混凝土 1.0。
使用无损 RGB8、normal_map=0 保留读回字节；禁止对技术通道做 sRGB 解码。
建筑/地板原生像素预览用 Nearest；3D 数据建议 Linear、mipmap、XY Repeat。

金属 roughness=0.65、metallic=0.55，实际 L8 为 166/255、140/255；
混凝土 roughness=1、metallic=0，实际为 255/255、0/255。常量是明确指定的
艺术 PBR 参数，不是从 albedo 估计的真实物理测量。材质取 R 通道。

grass 权重只在源 Alpha=255 的位置有效，公式为
round(clamp((119-y)/109,0,1)×255)。最高实际可见像素 y10=255，根像素 y119=0，
锚点为根边界 [32,120]；透明外为 0，没有把画布底部 128 当作根。

review/*registration_light*.png 是底图/高度/法线和四向 CPU 隔离照明的并排证明。
它们没有冒充 Godot 截图；移动 Light2D、CanvasTexture、PBR 和真实读回由根代理
在独立新资源中验证。validation-v001.json 包括独立差分复算、字节和注册核验。

Godot 原生约定参考：[CanvasTexture](https://docs.godotengine.org/en/stable/classes/class_canvastexture.html)、
[2D lights and shadows](https://docs.godotengine.org/en/stable/tutorials/2d/2d_lights_and_shadows.html)。
