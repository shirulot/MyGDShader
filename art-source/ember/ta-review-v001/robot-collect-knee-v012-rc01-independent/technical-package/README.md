# 机器人采集膝盖修订 v012 · 候选 rc01

用户指出v011采集前探与保持帧的膝盖明显扭曲。本候选改为双腿稳定支撑、上身及工具臂前探：不再将锁脚下压交给屏幕平面的定长双骨IK。旧模型会把深度方向的屈膝压成屏幕横向膝外移；这是制作代码与旧姿态的检查结论。

本候选改变了采集动作的支撑方案，不能用旧TA回执当作新姿态已经通过的依据。膝盖、腰髋、重心与工具动作需要重新看。本轮未接入主游戏。

## 查看

- `compare.html`：八向同步前后对照，原生／4倍，正常／四分之一速度，深浅底，逐帧及可关闭髋膝踝骨点。通过HTTP打开。
- `qa/*_before_after_<light|dark>_4x.png`：每向上排原版四帧、下排候选四帧。
- `qa/*_hip_knee_ankle_<light|dark>_6x.png`：同排列的髋膝踝局部。骨点原坐标见comparison-metadata.json中的old_joints/new_joints。
- `runtime/previews/full/collect_*`：候选八向，1×／4×、正常／慢速GIF/WebP，单次编码。旧版同规格在`previews/before/`。
- `runtime/project.godot`：独立运行工程；Q/E换向，1待机、2行走、3采集，空格暂停。采集中锁向，完成后回同向idle F00。

## 变更与来源

完整工程仍为24段112帧。只改八向采集F01/F02共16张，80张待机／行走以及16张采集首尾共96张PNG保持原字节；清单在qa/change-scope.json和run-manifest.json。原v011固定目录和ZIP保持不变。

髋、膝、踝与靴恢复各自原中性登记支撑位置，胸头和工具臂继续沿用原采集变换。先重组已有imagegen固定部件，再对腰髋允许区使用新imagegen编辑源。仅采纳允许区中的颜色修形，原透明度、上身其它区域和腿靴不随生成图变化；F01/F02相同腰髋部位使用同一编辑来源。生成稿的光晕和其余变动未装入PNG。

`source/imagegen-ledger.json`记录八张有效生成源、确切输入、提示词及SHA。东南首张编辑稿因输入重组残点修订已弃用，留存但不进入候选。`source/fixed-source-record/`保存原固定部件及原姿态记录，`fixed-source-mapping.json`绑定其原路径与SHA。生产脚本在当前v011工作区读取原工具模块；runtime工程本身可独立打开。

## 核对边界

64×96、root(32,80)、11色、二值Alpha；采集4帧@6FPS单次。qa/validation.json核对112PNG、96保留／16修改、源哈希、固定支撑坐标与靴像素、64份新采集动图参数。runtime/evidence核对真实Godot112格RGBA/动作参数，以及八向32采集帧的1×/4×共64个实际GPU样本和八条单次完成回待机。技术通过不替代新一轮视觉审查。
