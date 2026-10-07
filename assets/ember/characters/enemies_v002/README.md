# 已通过的敌人正向动作

四款×五动作（20条/120帧）已由技术美术总监正式通过。该目录逐字节复制自固定v012汇总，不覆盖旧enemies_v001。各自 .tres 内含全部五动作，PNG可独立使用。

给AnimatedSprite2D赋对应 .tres；centered=false，offset=Vector2(-64,-104)，Nearest。动作名idle_down、move_down、attack_down、hit_down、death_down；前三者帧数分别4/8/6，后两者4/8；FPS依次4/8/10/12/10；仅idle和move循环。

范围仅down/front资源及动作，未接入敌人AI/碰撞/伤害。原固定包与全部正式回执在art-source/ember/enemy-sequences-v012；包SHA42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe。

source_binding.json记录汇总时的相对路径（res://output/）；本目录移植时去掉output/前缀即可定位同一PNG。资源本身使用内嵌纹理，不依赖这些记录路径。
