"""逐项实看AI母稿及原生草案后填写的语义标注，便于学习/审阅。

这里的矩形是人明确选定的安全内区，不从连通暗色猜整个窗口。
新资产只有实际观看后才加入CONFIG；没有自动补齐/假通过条目。
"""
from pathlib import Path
import json
BASE=Path(__file__).resolve().parents[1]
def rect(bounds,color):return {'type':'rect','bounds':bounds,'color':color}
def line(points,color):return {'type':'line','points':points,'color':color}
def window(ident,frame,active,canvas):
    x0,y0,x1,y1=active;c=[(x0+x1)/2,(y0+y1)/2]
    return {'id':ident,'visual_frame_bounds':frame,'safe_active_rect':active,
       'center':c,'center_basis':'safe_active_rect_geometric_center',
       'normalized_uv':[c[0]/canvas[0],c[1]/canvas[1]],
       'rect_convention':'[x0,y0,x1,y1), right/bottom excluded',
       'mask_delivery_status':'NOT_PRODUCED; registered geometry only; technical channel mask is separate budget'}
def component(name,bounds,z,purpose,**extra):
    return {'name':name,'rects':[bounds],'z_index':z,'purpose':purpose,**extra}
CONFIG={
'console_base':{
 'observations':'实际母稿为浅色装甲立台、单大屏、三按钮及两侧黄铜连接；原生草案大屏清楚，但内屏细微颜色梯度需整理为可控中性色块。',
 'adjustments':['原生大屏[36,33,60,47)消除渐变与碎灰，改为单一深蓝灰安全区；底部一行更深形成玻璃边界',
                '左上框缘补连续3px金属亮边；保留3按钮与右下维修孔，固定基座边界80',
                '屏幕安全区拆实际RGBA组件与二值选择mask；未交付运行灯/技术通道Mask'],
 'patches':[rect([36,33,60,47],2),line([[36,46],[59,46]],1),line([[36,31],[58,31]],4)],
 'runtime_windows':[window('console_screen',[33,29,63,50],[36,33,60,47],[96,96])],
 'components':[component('screen_neutral',[36,33,60,47],1,'独立中性屏幕内区，方便后续材质驱动')]},
'pump_base':{
 'observations':'实际母稿有水平左右黄铜接头、圆泵壳、上部电机与基座；原生管口为黄铜块，需补可辨深色接口，中心小表窗保留。',
 'adjustments':['原生圆壳表窗[77,140,85,144)归并为中性深蓝灰，非发光运行状态',
                '左右外接口增加3px深槽与上缘金属点，安装坐标对应真实接头；不画出水/地影',
                '减少1px随机钢灰点并保持左右接头受同一左上光照；底界176'],
 'patches':[rect([77,140,85,144],2),line([[27,132],[27,136]],1),line([[133,132],[133,136]],1),line([[29,129],[31,129]],8)],
 'runtime_windows':[window('pump_gauge',[73,136,89,146],[77,140,85,144],[160,192])],
 'emitter_points':[{'id':'pipe_inlet','at':[27,134],'purpose':'静态管口接口，非已烘焙粒子'},
                   {'id':'pipe_outlet','at':[133,134],'purpose':'输水接口；外部管线/水效另制作'}]},
'ventilator_base':{
 'observations':'实际母稿三片钢灰扇叶、中央黄铜轴、深风腔与上后方矩形出烟口都清楚；原生草案无需整体变形。',
 'adjustments':['上后方出烟口内区[75,56,86,61)归并为连续暗腔；记录实际烟粒子发射中心而不生成烟',
                '三扇叶原生边缘亮点改成短连贯高光；中心轴保留黄铜，中性深腔补于可动叶片之下',
                '逐像素选择真实三叶与轴组件，导出fan_rotor和选择mask；housing源PNG可独立编辑，重组与最终严格相同'],
 'patches':[rect([75,56,86,61],1),line([[75,80],[81,80]],4),line([[58,104],[63,104]],4)],
 'emitter_points':[{'id':'exhaust_smoke','at':[80.5,58.5],'region':[75,56,86,61],
                    'purpose':'出烟口几何中心；烟/火焰/热浪没有烘焙于底图'}],
 'components':[{'name':'fan_rotor','z_index':2,'underpaint':1,'purpose':'实际3片扇叶与轴；移开后机壳有中性腔底',
                'polygons':[[[70,80],[73,78],[85,79],[85,88],[83,94],[75,94]],
                            [[57,103],[66,101],[74,103],[76,108],[70,114],[62,118],[58,113]],
                            [[88,104],[94,101],[104,105],[101,114],[93,117],[87,110]],
                            [[74,94],[86,94],[90,98],[90,105],[86,109],[74,109],[70,105],[70,98]]]}]},
'cooler_base':{
 'observations':'实际母稿三根立管与换热核心/两侧铜管结构形成识别，顶左高光清楚；内侧小窗不属于背景孔。',
 'adjustments':['安全小窗[75,122,85,128)重画为中性深色矩形并留边框，不让母稿渐变/伪光点进入运行窗口',
                '中心立管顶段高光整理为5px短线、右侧保留较暗管面以固定左上光照；固定基座176',
                '把窗口内区与高处换热管导出实际独立源层，不宣称运行通道Mask已完成'],
 'patches':[rect([75,122,85,128],2),line([[79,55],[79,59]],4)],
 'runtime_windows':[window('cooling_core',[72,118,89,131],[75,122,85,128],[160,192])],
 'components':[component('exchange_pipes_high',[57,50,105,91],2,'可编辑上部换热管与实际遮挡像素'),
               component('core_window',[75,122,85,128],1,'核心中性窗口内区')]},
'relay_base':{
 'observations':'实际母稿上部横天线、窄桅杆、竖直核心与底座；高部件在原生52..128行，远高于机器人，必须登记遮挡源层。',
 'adjustments':['核心窗[91,166,101,187)归并连续中性暗色；顶部天线浅色短条归并以去孤立颗粒',
                '上部桅杆和横天线按y<128拆实际high_mast源层与选择mask；不是只写文字已分层',
                '底座统一足界240，原生高天线不缩短以假装小设备'],
 'patches':[rect([91,166,101,187],2),line([[78,74],[85,74]],5),line([[105,74],[112,74]],4)],
 'runtime_windows':[window('relay_core',[87,162,106,192],[91,166,101,187],[192,256])],
 'components':[component('mast_high',[0,0,192,128],2,'高处通信桅杆/天线，前景遮挡层；完整同画布同anchor'),
               component('core_window',[91,166,101,187],1,'中性核心安全内窗')]},
'wall_lamp':{
 'observations':'实际母稿有壁面安装板、两个上部铜螺栓、向下防护罩及小笼状镜片；原生22×42可与地灯安装方式区分。',
 'adjustments':['笼内[30,45,33,50)玻璃整理为连续中性深灰，去微亮点，灯不发光',
                '上安装板一枚钢灰线像素归并，保留右侧电缆弯环与孔；安装边界56',
                '输出真实lens_neutral源组件用于后续灯色，不烘焙光圈'],
 'patches':[rect([30,45,33,50],2),line([[28,15],[34,15]],5)],
 'runtime_windows':[window('lamp_lens',[28,41,35,52],[30,45,33,50],[64,64])],
 'components':[component('lens_neutral',[30,45,33,50],1,'未点亮玻璃安全内区')]}
}
# 以下六项也已逐张看过实际母稿、原生草案及结构修正版。
CONFIG.update({
'floor_lamp':{
 'observations':'实际母稿是窄立柱与方形落地脚，灯头为浅壳框住深玻璃；比壁灯没有背板、向上头罩更明确。',
 'adjustments':['灯头安全内区[30,26,34,32)归并深蓝灰，去原生采样亮灰点；保留1px玻璃框和四脚螺栓',
                '上帽金属高光整理为3px短条，左上光照方向保持；底脚边界56',
                'lens_neutral源层真实同64画布，预留材质发光而不烘焙灯光'],
 'patches':[rect([30,26,34,32],2),line([[30,13],[33,13]],4)],
 'runtime_windows':[window('lamp_lens',[28,24,36,34],[30,26,34,32],[64,64])],
 'components':[component('lens_neutral',[30,26,34,32],1,'未点亮玻璃安全内区')]},
'telepad_base':{
 'observations':'实际母稿为低矮八角平台，四内侧marker窗和宽平圆盘；原生中心实心可步入，外圈无自发光和护罩。',
 'adjustments':['四marker分别以明确原生矩形归并中性暗色，保留围框，不能把中央圆盘误设发光窗',
                '顶侧钢面连续亮边缩为短条，去细碎颜色梯度；低基座厚度与底界144保持',
                '记录中心轴[64,110]供传送效果叠加，接地anchor[64,144]独立；四窗导出实际选择源层'],
 'patches':[rect([61,90,68,92],1),rect([42,102,45,108],1),rect([84,102,87,108],1),rect([61,119,68,121],1),line([[61,79],[67,79]],4)],
 'runtime_windows':[window('marker_n',[59,88,70,94],[61,90,68,92],[128,160]),
                   window('marker_w',[40,100,48,110],[42,102,45,108],[128,160]),
                   window('marker_e',[82,100,90,110],[84,102,87,108],[128,160]),
                   window('marker_s',[59,117,71,123],[61,119,68,121],[128,160])],
 'interaction_center':[64,110],
 'emitter_points':[{'id':'teleport_axis','at':[64,110],'purpose':'平台几何中心，运行护盾/传送另叠加，无烘焙效果'}],
 'components':[{'name':'marker_windows','rects':[[61,90,68,92],[42,102,45,108],[84,102,87,108],[61,119,68,121]],'z_index':1,'purpose':'实际4个中性marker内窗源组件'}]},
'terminal_body':{
 'observations':'实际母稿单屏外框、键盘格、单侧铜连接和落地脚可辨；原生采样屏内出现母稿半透明噪色，需要明确变为单一中性安全区。',
 'adjustments':['安全内屏[38,30,57,41)逐像素归并，彻底清除母稿屏内梯度/形似内容的暗颗粒，屏幕内容应由真实场景提供',
                '键盘左上短亮边归并3px，保留两排物理按键及右侧铜接口；底脚80',
                'inner_screen源RGBA+mask与base同画布，可独立绑定场景屏幕材质'],
 'patches':[rect([38,30,57,41],2),line([[39,53],[42,53]],4)],
 'runtime_windows':[window('terminal_scene_screen',[34,26,61,45],[38,30,57,41],[96,96])],
 'components':[component('inner_screen',[38,30,57,41],1,'中性屏幕内区，真实场景内容后接入')]},
'screen_frame':{
 'observations':'实际母稿四个陶瓷铜栓角、钢灰边条和透空中心；母稿边宽不完全一致，原生草案64×61，需要九宫格结构整理。',
 'adjustments':['NATIVE_NINE_SLICE_REBUILD: 保留4个实际8px不同光照角块；重画恒厚8px材质截面，不镜像光照',
                '原生source region [16,16,80,80)为64×64；slice_region使用[x,y,w,h]=[16,16,64,64]，四边8px',
                '中心[24,24,72,72)完整真透明，draw_center=false；完整96画布四边16px，不把留白当九宫格边条'],
 'patches':[{'type':'pixel','at':[24,17],'color':4}],
 'native_reconstruction_file':'layers/screen_frame_native.png',
 'native_reconstruction_record':'annotations/architectural-rebuild-record.json',
 'tiling':{'axes':[],'repeat':False,'stretch':'nine_slice',
    'source_region':[16,16,80,80],'source_region_convention':'[x0,y0,x1,y1)',
    'slice_region':[16,16,64,64],'slice_region_convention':'[x,y,width,height]',
    'slice_margins':{'left':8,'top':8,'right':8,'bottom':8},
    'center_rect':[24,24,72,72],'draw_center':False},
 'runtime_windows':[], 'components':[]}
})
CONFIG.update({
'fuse':{
 'observations':'实际母稿为横陶瓷管、两种不同端头，左端为分叉、右端细槽；原生38×12较小，孔槽需在本体像素网格清楚保留。',
 'adjustments':['陶瓷管中部[25,47,41,50)整理为连续浅装甲块、下一行钢亮灰，消除模型微颗粒但保留上亮下暗',
                '左叉口归并2×2透明缺口；右端依据母稿细槽原生切1×3真透明孔，形成方向/描边可观察结构',
                '不加灯或文字；底界56，同64画布保留8px以上留边'],
 'patches':[rect([25,47,41,50],5),line([[26,50],[40,50]],4),
            rect([13,49,16,51],'transparent'),rect([48,48,49,51],'transparent')],
 'calibration_features':{'orientation':'左叉/右细槽，不对称','through_hole_rects':[[48,48,49,51]],'notch_rects':[[13,49,16,51]]}},
'antenna_coil':{
 'observations':'实际母稿三匝铜绕组、圆芯、方脚、右侧连接器；原生两个上部线圈外沿小孔实际Alpha为0，不能填黑假装孔。',
 'adjustments':['三匝绕组正面原生短高光归并为连续6px铜色段，保留匝间深色核心，不绘制信号发光',
                '明确保留实际两处2×1透明穿孔[20,27,22,28)、[33,27,35,28)，剪去半透明点而不填孔',
                '底脚与右侧连接器维持母稿不对称轮廓，安装边界56'],
 'patches':[line([[25,33],[30,33]],8),line([[25,39],[30,39]],7),line([[25,45],[30,45]],7),
            rect([20,27,22,28],'transparent'),rect([33,27,35,28],'transparent')],
 'calibration_features':{'orientation':'右侧独有铜接口','through_hole_rects':[[20,27,22,28],[33,27,35,28]]}},
'split_ring':{
 'observations':'实际母稿C形三分之四钢环、浅色陶瓷圈、右下明确开口和铜端头；原生中央孔与开口真实相通。',
 'adjustments':['右下gap[41,48,44,51)归并成连续透明开口，消除采样可能残留孤立桥点，不填底色',
                '左上陶瓷高光整理为3px短段、内缘钢灰用1px轮廓清楚收边，保留偏右铜端头',
                '中央孔保持不规则透视椭圆原生负形，不用几何圆环替换母稿整体轮廓'],
 'patches':[rect([41,48,44,51],'transparent'),line([[25,27],[28,27]],5)],
 'calibration_features':{'orientation':'右下开口/铜端头','opening_rect':[41,48,44,51],
                        'central_hole_seed':[32,40],'hole_connected_to_exterior':True}}
})
CONFIG.update({
'log_cartridge':{
 'observations':'实际母稿两根顶铜触点、长方陶瓷记录壳、中央深凹槽和右下铜锁扣；没有文字内容，原生23×34识别明确。',
 'adjustments':['中心物理凹槽[29,36,35,46)归并为6px宽中性深色块、最下2行加深；它不是发光运行屏幕',
                '两铜触点的顶边分别整理成2px材质亮点，保留槽中性及单侧锁扣不对称方向',
                '去半透明halo与孤立钢灰点；64画布底界56，日志正文留给UI'],
 'patches':[rect([29,36,35,46],2),rect([29,44,35,46],1),line([[27,23],[28,23]],8),line([[34,23],[35,23]],8)],
 'non_runtime_glass':[{'id':'physical_recess','rect':[29,36,35,46],'emits':False}]},
'toolbox':{
 'observations':'实际母稿工具箱上手柄、浅陶瓷四角、两铜锁扣与左侧铰链；母稿带明显模型灰halo，原生高Alpha采样已去除，手柄内槽仍需明确透明孔。',
 'adjustments':['NATIVE_HANDLE_APERTURE: 按实际母稿手柄内槽位置切原生[28,33,37,35)9×2真透明孔，不让halo/灰底残留',
                '顶手柄亮钢短条[28..35,30]连续归并，箱盖上缘保留钢灰平面，两锁扣不作为运行状态灯',
                '去所有halo和随机单点；原生44×27底界56，完整轮廓保持，未把灰halo缩图后冒充投影'],
 'patches':[rect([28,33,37,35],'transparent'),line([[28,30],[35,30]],4)],
 'calibration_features':{'through_hole_rects':[[28,33,37,35]],'orientation':'左侧单独铰链，正面2锁扣'}},
'helmet':{
 'observations':'实际母稿浅陶瓷壳、深visor边与右侧黄铜扣，属于同一制造系统的现场头盔；它是静态叙事物，不新增角色动作或发射点。',
 'adjustments':['visor内侧[23,41,32,47)归并为中性深灰，去母稿微渐变，原有倾斜壳缘轮廓仍保留',
                '左上陶瓷亮簇归并成3px连续色块，右侧壳面继续较暗；不镜像或改变右侧铜扣',
                '实体1px外轮廓、二值Alpha、原生33×34底界56；玻璃无运行状态光、无地面影'],
 'patches':[rect([23,41,32,47],2),line([[23,30],[25,30]],5)],
 'non_runtime_glass':[{'id':'helmet_visor','rect':[23,41,32,47],'emits':False}]}
})
for door in ['door_closed','door_open']:
    closed=door=='door_closed'
    CONFIG[door]={
      'observations':'实际闭门/开门两母稿均已看；框体制造语汇一致但母稿高度偏方。原生重建94px高，共框共安装点；开门母稿空洞用于语义参考。',
      'adjustments':['NATIVE_STRUCTURAL_REBUILD: 原生保留母稿20px过梁/12px框脚材料块；柱截面重新安排长度，接缝/铜件/门板在目标网格重画',
                     '两态共享frame_native.png同一像素结构与右柱中性窗口；anchor(48,112)固定，不整体warp',
                     'ROOT_PROPORTION_CORRECTION: 内柱共同收薄，通路宽32改44以容纳既有40px机器人，外框bbox不变',
                     ('门板两片用钢灰折角与黄铜把手原生重画，保留中心缝' if closed else '整段通路[26,38,70,112)真Alpha透明，不填黑、地板、阈条或阴影'),
                     '前景过梁/立柱导出同画布可编辑源PNG和显式选择mask；框脚余像素保留foundation层'],
      'patches':[rect([72,64,74,69],2)],
      'native_reconstruction_file':f'layers/door_shared/{door}_native.png',
      'native_reconstruction_record':'annotations/architectural-rebuild-record.json',
      'runtime_windows':[window('door_status',[70,62,76,71],[72,64,74,69],[96,128])],
      'components':[{'name':'foreground_frame','rects':[[0,0,96,38],[0,38,26,100],[70,38,96,100]],
                    'z_index':2,'purpose':'两态精确共用过梁/立柱，前景遮挡源层'}],
      'tiling':{'axes':[],'repeat':False,'shared_frame_file':'layers/door_shared/frame_native.png',
                'opening_rect':[26,38,70,112],'opening_is_alpha_transparent':not closed,
                'installation_point':[48,112]}}
    if closed:CONFIG[door]['components'].insert(0,component('sliding_leaves',[26,38,70,110],1,'原生两片关门钢板，共框分层'))
def main():
    for ident,data in CONFIG.items():
        data.setdefault('emitter_points',[]);data.setdefault('runtime_windows',[])
        data.setdefault('components',[])
        (BASE/'annotations'/f'{ident}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'annotated_assets':len(CONFIG)}))
if __name__=='__main__':main()
