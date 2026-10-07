// 将实际 PNG 与骨点账本并列用于复审；示意线只出现在 QA 图，绝不写回角色资产。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=path.resolve(__dirname,'..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=file=>fs.readFile(path.join(root,file));
const json=async file=>JSON.parse(await read(file));
const point=p=>p.map(n=>n.toFixed(2)).join(', ');
const projection=(a,b,f)=>(a[0]-b[0])*f[0]+(a[1]-b[1])*f[1];
const phases=[1,.6,0,-.6,-1,-.6,0,.6];

async function run(){
 const scope=await json('qa/arm_phase_revision_scope.json');
 const baseline=await json(scope.reference_root+'/walk-batch-metadata.json');
 const unchanged=[];
 // 除三向修订的24帧，其余24行走帧+8身份图逐文件保留。
 for(const c of baseline.clips.filter(c=>c.action==='pose'||!scope.directions.includes(c.direction)))for(const f of c.frames){
  const actual=sha(await read(f.file));if(actual!==f.sha256)throw Error('Preserved baseline changed: '+f.file);
  unchanged.push({file:f.file,sha256:actual});
 }
 const report={revision:'phase-b1-rc02',reference_revision:'phase-b1-rc01',technical_scope_checks:'PASS',art_acceptance:'PENDING_TA',unchanged_files:unchanged,directions:[]};
 let md='# B1 rc02 摆臂返修证据\n\n本表绑定实际最终 PNG、rc01 对照、源片和八帧骨点。LEFT/RIGHT 均为角色自己的左右；所有坐标使用同一64×96画布。S/SW/NW共24行走帧与8身份图原字节保持。\n\n东北、东南：按右向投影反转摆臂角。朝北：手腕采用与同侧脚前后运动相反的纵向目标，定长双骨求肘位。身体、腿和靴变换均未改动。东北另将母图(22,59)一枚原色腕部像素从身体归入左前臂，静态实拼仍零差。\n\n足踝坐标同时包含地面方向投影与抬脚高度；不能把抬脚造成的屏幕Y变化直接当成步相。F00/F04均为相同body bob和零抬脚的接触相，适合核对交错关系。F07/F00用于观察回环，不要求骨点相同。技术数值不代替正常速度与慢速视觉复审。\n\n';
 for(const d of scope.directions){
  const old=await json(`${scope.reference_root}/${d}/rig_and_poses.json`),now=await json(`source/fixed-rig-pilot/${d}/rig_and_poses.json`);
  const patch=await json(`qa/${d}_joint_patch_v011.json`),entry={direction:d,source_ownership_repairs:patch.source_ownership_repairs,contacts:[],frames:[]};
  const images={before:[],after:[]};
  md+=`## ${d}\n\n![实际修前与修后八帧](${d}_arm_phase_before_after_4x.png)\n\n![肩肘腕与髋膝踝示意](${d}_arm_phase_bones_4x.png)\n\n橙色为解剖左侧，蓝色为解剖右侧；实线连肩—肘—腕，虚线连髋—膝—踝。骨点示意没有用于修改任何素材。\n\n`;
  for(const side of['left','right']){
   const contact={side};
   for(const[label,ledger]of[['before',old],['after',now]]){
    const a=ledger.states[0].joints,b=ledger.states[4].joints;
    const arm=projection(b['arm_'+side].wrist,a['arm_'+side].wrist,ledger.rig.forward),leg=projection(b['leg_'+side].ankle,a['leg_'+side].ankle,ledger.rig.forward);
    contact[label]={frame_pair:[0,4],arm_delta_xy:b['arm_'+side].wrist.map((v,i)=>v-a['arm_'+side].wrist[i]),leg_delta_xy:b['leg_'+side].ankle.map((v,i)=>v-a['leg_'+side].ankle[i]),arm_forward_delta:arm,leg_forward_delta:leg,opposed:arm*leg<0};
   }
   if(!contact.after.opposed)throw Error('Unresolved contact phase: '+d+'/'+side);
   entry.contacts.push(contact);
   md+=`${side} F00→F04：腕沿朝向投影 ${contact.before.arm_forward_delta.toFixed(3)} → ${contact.after.arm_forward_delta.toFixed(3)}；踝 ${contact.after.leg_forward_delta.toFixed(3)} px；修后异号。\n\n`;
  }
  md+='| 帧/侧 | 地面步相 / 抬脚 | 修后肩 → 肘 → 腕 | 修后髋 → 膝 → 踝 |\n|---|---|---|---|\n';
  for(let i=0;i<8;i++){
   const name=`robot_walk_${d}_f${String(i).padStart(2,'0')}_v011.png`,beforeFile=`${scope.reference_root}/${d}/${name}`,afterFile=`frames/walk/${d}/${name}`;
   const beforeBytes=await read(beforeFile),afterBytes=await read(afterFile),before=await sharp(beforeBytes).ensureAlpha().raw().toBuffer(),after=await sharp(afterBytes).ensureAlpha().raw().toBuffer();
   const mask=await sharp(path.join(root,`qa/${d}_arm_revision_mask_f${String(i).padStart(2,'0')}.png`)).ensureAlpha().raw().toBuffer();
   let changed=0,outside=0;for(let at=0;at<before.length;at+=4)if(!before.subarray(at,at+4).equals(after.subarray(at,at+4))){changed++;if(!mask[at+3])outside++;}
   if(outside)throw Error('Actual output exceeds local revision mask: '+d+'/'+i);
   const unchangedTransforms=['body',...Object.keys(now.states[i].transforms).filter(k=>k.startsWith('leg_'))];
   for(const key of unchangedTransforms)if(JSON.stringify(old.states[i].transforms[key])!==JSON.stringify(now.states[i].transforms[key]))throw Error('Body or leg transform changed');
   const frame={frame:i,before_file:beforeFile,before_sha256:sha(beforeBytes),after_file:afterFile,after_sha256:sha(afterBytes),changed_pixels:changed,outside_revision_mask_changed:outside,body_leg_transforms_unchanged:true,before_joints:old.states[i].joints,after_joints:now.states[i].joints};
   images.before.push(beforeBytes);images.after.push(afterBytes);entry.frames.push(frame);
   for(const side of['left','right']){
    const a=now.states[i].joints['arm_'+side],l=now.states[i].joints['leg_'+side],p=phases[(i+(side==='left'?0:4))%8];
    md+=`| F${String(i).padStart(2,'0')} ${side} | ${p.toFixed(1)} / ${l.lift.toFixed(1)} px | (${point(a.root)}) → (${point(a.joint)}) → (${point(a.wrist)}) | (${point(l.root)}) → (${point(l.joint)}) → (${point(l.ankle)}) |\n`;
   }
  }
  // 两行各8帧：第一行rc01，第二行rc02。同一画布同一缩放，没有逐帧齐底。
  for(const bones of[false,true]){
   const cw=bones?192:256,ch=bones?216:408,ww=cw*8,hh=ch*2+52,svg=[];
   svg.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${ww}" height="${hh}"><rect width="100%" height="100%" fill="#ece9d8"/><text x="12" y="26" font-size="20" font-family="sans-serif" fill="#182631">${d}: row 1 rc01 / row 2 rc02; LEFT orange, RIGHT blue</text>`);
   for(const[row,key,ledger]of[[0,'before',old],[1,'after',now]])for(let i=0;i<8;i++){
    const x=i*cw,y=52+row*ch;
    const imageBuffer=bones?await sharp(images[key][i]).extract({left:8,top:42,width:48,height:46}).resize(192,184,{kernel:'nearest'}).png().toBuffer():await sharp(images[key][i]).resize(256,384,{kernel:'nearest'}).png().toBuffer();
    svg.push(`<text x="${x+8}" y="${y+16}" font-size="14" font-family="sans-serif" fill="#182631">${key} F${String(i).padStart(2,'0')}</text><image x="${x}" y="${y+24}" width="${cw}" height="${bones?184:384}" href="data:image/png;base64,${imageBuffer.toString('base64')}"/>`);
    if(bones)for(const[side,color]of[['left','#c45118'],['right','#126da6']]){
     const j=ledger.states[i].joints,a=j['arm_'+side],l=j['leg_'+side],screen=p=>[x+(p[0]-8)*4,y+24+(p[1]-42)*4];
     for(const[chain,dash]of[[[a.root,a.joint,a.wrist],false],[[l.root,l.joint,l.ankle],true]]){
      svg.push(`<polyline points="${chain.map(p=>screen(p).join(',')).join(' ')}" fill="none" stroke="${color}" stroke-width="1.5" ${dash?'stroke-dasharray="3 2"':''}/>`);
      for(const p of chain){const[sx,sy]=screen(p);svg.push(`<circle cx="${sx}" cy="${sy}" r="2.3" fill="${color}"/>`);}
     }
    }
   }
   svg.push('</svg>');await sharp(Buffer.from(svg.join(''))).png().toFile(path.join(__dirname,`${d}_arm_phase_${bones?'bones':'before_after'}_4x.png`));
  }
  md+='\n修前、修后的全部骨点与像素差记录见 `arm_phase_revision_evidence.json`；掩膜外实际 RGBA 差为0。\n\n';report.directions.push(entry);
 }
 await fs.writeFile(path.join(__dirname,'arm_phase_revision_evidence.json'),JSON.stringify(report,null,2)+'\n');
 await fs.writeFile(path.join(__dirname,'arm_phase_revision_evidence.md'),md);
 console.log(JSON.stringify({status:'PASS',unchanged_files:unchanged.length,revised_frames:report.directions.reduce((n,d)=>n+d.frames.length,0),contacts:report.directions.map(d=>({direction:d.direction,contacts:d.contacts}))}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
