# Ember 四款敌人正向序列帧 · v012 汇总

本目录汇总巡逻兵、履带重装机、切割工蜂、悬浮侦察机的待机、移动、攻击、受击、死亡：20条动作、120帧。只复制固定审阅包中的PNG，再生成四个可直接使用的Godot SpriteFrames；没有重新生成人物或改变任何帧像素。

技术美术总监已正式通过全部20条正向动作。逐条范围与固定包绑定见 `TA_ACCEPTANCE.json`；五份正式回执见 `review_reports/`。侦察机使用已批准的原v011，未包含另存的未审伸缩颈实验。

## 使用

- 在 Godot 中导入 `output/enemy_patrol.tres`、`enemy_tracked_heavy.tres`、`enemy_cutter.tres`、`enemy_scout_drone.tres`。
- 给 `AnimatedSprite2D.sprite_frames` 赋对应资源，设 `centered=false`、`offset=Vector2(-64,-104)`、纹理过滤 Nearest。
- 动作名：`idle_down`、`move_down`、`attack_down`、`hit_down`、`death_down`。
- idle：4帧/4FPS/循环；move：8帧/8FPS/循环；attack：6帧/10FPS/单次；hit：4帧/12FPS/单次；death：8帧/10FPS/单次。
- 死亡资源停在最后一帧。演示页的自动重播只用于查看，不应复制为游戏死亡逻辑。
- PNG均为128×128透明画布，固定根坐标(64,104)。侦察机采用地面投影根，机体悬浮/坠落不改变节点锚点。

本目录可作为独立Godot项目打开，运行 `preview.tscn` 查看四款×五动作；左侧正常2×，右侧1FPS原生1×。也可使用现有浏览器汇总入口 http://127.0.0.1:6106/review-current/index.html。

## 来源与验证

`assembly_recipe.json`逐动作记录原固定包、ZIP SHA、图集SHA、逐帧SHA和时间参数。`reviewed_packages/`保留五份固定审阅包，包括全部原始源图、零件绑定和各轮技术证明。旧版本不覆盖。

`qa/assembly_integrity.json`验证20条时间参数、120个PNG原SHA以及保存后SpriteFrames逐帧RGBA一致性。`qa/assembly_runtime.json`记录20条资源各自正常/慢速实际播放，全40个播放器遍历完整；`qa/assembly_runtime.png`是实际Godot运行截图。

TA通过的是本次正向像素资源及动作外观。其余朝向、AI、伤害、碰撞、世界移动速度匹配和精确玩法事件接口不在本次范围。技术自检和汇总不会替代独立美术回执。
