// 批量入口仅允许七个新方向；使用已通过小样的同一保护与接缝规则。
const {processAction}=require('./composite_action_pilot_v011.cjs');
(async()=>{for(const direction of process.argv.slice(2))for(const action of['idle','collect'])await processAction(action,direction,{batch:true});})().catch(error=>{console.error(error);process.exitCode=1;});
