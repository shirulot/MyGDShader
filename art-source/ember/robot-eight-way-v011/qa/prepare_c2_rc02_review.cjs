// rc02只关闭SE肘外轮廓P2；原rc01及其报告保持只读。
const fs=require('node:fs/promises'),path=require('node:path');
const root=path.resolve(__dirname,'..'),read=async f=>JSON.parse(await fs.readFile(path.join(root,f),'utf8'));
const write=async(f,v)=>fs.writeFile(path.join(root,f),JSON.stringify(v,null,2)+'\n');
(async()=>{
 const meta=await read('full-action-metadata.json');if(meta.revision!=='v011-phase-c2-rc02')throw Error('Wrong candidate');
 const browser=(await fs.readdir(path.join(root,'qa/browser'))).filter(f=>f.startsWith('phase_c2_rc02_')).map(f=>'qa/browser/'+f);
 await write('qa/visual-review-c2-rc02.json',{
  revision:'phase-c2-rc02',atlas_sha256:meta.atlas_sha256,producer_review:'READY_FOR_INDEPENDENT_REVIEW',independent_art_acceptance:'PENDING_TA',
  scope:'Incremental SE collect F01/F02 outer elbow contour; two frames, three source pixels each',
  inherited_review:'qa/visual-review-c2-rc01.json; unaffected110 frame SHA matches original fixed candidate',
  viewed_contact_sheets:['qa/se_elbow_rc02_before_after_light_4x.png','qa/se_elbow_rc02_source_before_after_light_16x.png','qa/se_elbow_rc02_source_before_after_dark_16x.png'],
  observations:['The dark outer contour is continuous again in both reach and hold frames on the light background.','The six restored pixels are the original rigid-rig outline, not new drawing; both frames use the same three canvas points.','No other frame, identity master, source part, bone transform, foot, tool or timing changed.','Deep-background inspection and natural collect-to-idle recovery remain visually consistent.'],
  browser_checks:['SE collect F01/F02 light, F02 dark at quarter speed; native and4x visible together.','Normal replay returned to idle. Screenshots are discrete evidence; one full-page dark capture failed, the viewport was inspected with getScreenshot.'],
  browser_evidence:browser,revision_evidence:'qa/se_elbow_rc02_revision.json',engine_playback_evidence:'qa/godot_full_actions_v011.json',
  art_scope_note:'TA requested this local P2 repair; overall C2 verdict still pending until its formal receipt.'
 });
 const manifest=await read('run-manifest.json');manifest.status='PHASE_C2_RC02_READY_FOR_TA';
 manifest.full_action_delivery.atlas_sha256=meta.atlas_sha256;manifest.full_action_delivery.technical_checks='PASS';
 manifest.current_revision_fix.evidence='qa/se_elbow_rc02_revision.json';manifest.current_revision_fix.changed_frames=2;manifest.current_revision_fix.changed_pixels=6;manifest.current_revision_fix.unchanged_frames=110;
 await write('run-manifest.json',manifest);
 let readme=await fs.readFile(path.join(root,'README-full-actions.md'),'utf8');
 readme=readme.replace('C2 rc01：','C2 rc02：').replaceAll('visual-review-c2-rc01.json','visual-review-c2-rc02.json').replaceAll('cold_delivery_validation_c2_rc01.json','cold_delivery_validation_c2_rc02.json');
 if(!readme.includes('## rc02 肘部轮廓修复'))readme+='\n## rc02 肘部轮廓修复\n\nTA复审在SE collect F01/F02确认局部P2：接缝补丁将原有暗色外轮廓覆盖为与浅底相同的亮甲色，造成暗点/短线的悬空读感。两帧仅恢复(x14,y52/53/54)三个原rig像素，共6点；同姿势采用一致保护。其余110帧、8身份母版、新S中性、固定源片、骨点、步相、靴子和工具不变。源/修前/修后深浅16倍及整帧4倍比较见qa/se_elbow_rc02_*。本轮实际224GPU、136切换和8条采集恢复再次通过；美术关闭以TA新回执为准。\n';
 await fs.writeFile(path.join(root,'README-full-actions.md'),readme);
 const history=path.join(root,'README-phase-a-history.md');try{await fs.access(history);}catch(e){if(e.code!=='ENOENT')throw e;await fs.copyFile(path.join(root,'README.md'),history);}
 await fs.writeFile(path.join(root,'README.md'),'# 机器人八向 v011\n\n当前：C2 rc02，完整24段112帧已制作，新增动作及东南采集肘边修复等待最终TA回执。此前已通过70动作帧保持原字节。\n\n- 最新说明：[README-full-actions.md](README-full-actions.md)\n- 工作预览：[action-batch-review.html](action-batch-review.html)\n- 完整独立工程：[godot-full-review/project.godot](godot-full-review/project.godot)\n- 关节与靴子制作规则：[JOINT-RULES.md](JOINT-RULES.md)\n- 阶段记录：[WORKLOG.md](WORKLOG.md)；早期说明：[README-phase-a-history.md](README-phase-a-history.md)\n\n完整源包按review/phase-*冻结，旧包不回写。主游戏尚未接入。\n');
 console.log(JSON.stringify({revision:meta.revision,atlas_sha256:meta.atlas_sha256,browser_evidence:browser.length}));
})().catch(error=>{console.error(error);process.exitCode=1;});
