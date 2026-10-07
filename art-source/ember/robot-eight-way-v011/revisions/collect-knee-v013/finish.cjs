// 把关节编辑限定在源排姿的腿部；不采用生成稿的背景、整体比例或重画的头身。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname,base=path.resolve(root,'../..'),W=64,H=96;
const {png,contact}=require(path.join(base,'build_fixed_rig_v011.cjs'));
const {components}=require(path.join(base,'qa/audit_walk_components.cjs'));
const palette=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A'].map(h=>[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)));
const nearest=p=>palette.reduce((b,c)=>{const d=c.reduce((s,v,i)=>s+(v-p[i])**2,0);return d<b.d?{d,c}:b;},{d:Infinity,c:palette[0]}).c;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=async f=>JSON.parse(await fs.readFile(path.join(root,f),'utf8'));
async function animated(frames,file,scale,fps){const raws=await Promise.all(frames.map(raw=>sharp(raw,{raw:{width:W,height:H,channels:4}}).resize(W*scale,H*scale,{kernel:'nearest'}).raw().toBuffer()));await fs.mkdir(path.dirname(file),{recursive:true});const delay=frames.map((_,i)=>(Math.round((i+1)*100/fps)-Math.round(i*100/fps))*10);await sharp(Buffer.concat(raws),{raw:{width:W*scale,height:H*scale*frames.length,channels:4,pageHeight:H*scale}}).gif({loop:1,delay,dither:0}).toFile(file);}
async function run(){
 const ledger=await read('source/imagegen-ledger.json'),comparison=[],qa=[],overview=[];
 for(const entry of ledger){
  const d=entry.direction;await fs.copyFile(entry.output_path,path.join(root,entry.source));
  for(const k of['source','input','prompt'])entry[k+'_sha256']=sha(await fs.readFile(path.join(root,entry[k])));
  const info=await sharp(path.join(root,entry.source)).metadata();if(info.width/info.height!==2/3)throw Error('Bad sheet layout');
  const gen=await sharp(path.join(root,entry.source)).resize(128,192,{kernel:'nearest'}).ensureAlpha().raw().toBuffer();
  const poses=await read(`source/${d}/poses.json`),old=JSON.parse(await fs.readFile(path.join(base,`revisions/collect-knee-v012/source/${d}/poses.json`),'utf8'));
  const planted=await sharp(path.join(root,`source/${d}/baseline_f0.png`)).ensureAlpha().raw().toBuffer();
  const before=[],after=[],records=[];
  for(let f=0;f<4;f++){
   const folder=`source/${d}/`,raw=await sharp(path.join(root,folder+`pose_f${f}.png`)).ensureAlpha().raw().toBuffer(),out=Buffer.from(raw);
   const guard=await sharp(path.join(root,folder+`guard_f${f}.png`)).ensureAlpha().raw().toBuffer();let edits=0;
   if(f===1||f===2)for(let y=54;y<74;y++)for(let x=12;x<51;x++){
    const at=(y*W+x)*4,from=(y*128+64+x)*4;
    // F1/F2 共用同一生成腿部，避免保持帧闪烁。已存在 alpha 与上层手臂/胸甲/脚靴均锁定。
    if(!raw[at+3]||guard[at+3]||gen[from+3]<200)continue;
    const rgb=nearest(gen.subarray(from,from+3));if(!raw.subarray(at,at+3).equals(Buffer.from(rgb))){out.set(rgb,at);edits++;}
   }
   // 胫甲转动不能越过脚底：复制原落地帧的鞋底区域，消除源片旋转侵入的边缘像素。
   if(f===1||f===2)planted.copy(out,75*W*4,75*W*4);
   const file=`frames/collect/${d}/robot_collect_${d}_f0${f}_v013.png`;
   await png(out,path.join(root,file));if(f===0||f===3)await fs.copyFile(path.join(root,folder+`baseline_f${f}.png`),path.join(root,file));
   const prior=await sharp(path.join(root,folder+`baseline_f${f}.png`)).ensureAlpha().raw().toBuffer();before.push(prior);after.push(out);
   const groups=components(out);records.push({frame:f,file,sha256:sha(await fs.readFile(path.join(root,file))),adopted_joint_color_pixels:edits,components:groups.map(({indices,...g})=>g)});
  }
  for(const [name,bg]of[['light',[236,233,216]],['dark',[24,38,49]]])await contact(before.concat(after),path.join(root,'qa',`${d}_before_after_${name}_4x.png`),4,bg,4);
  await contact(after,path.join(root,'previews',`${d}_strip_4x.png`),4,null,4);
  for(const scale of[1,4])for(const[speed,fps]of[['normal',6],['slow',1.5]])await animated(after,path.join(root,`previews/collect_${d}_${speed}_${scale}x_v013.gif`),scale,fps);
  overview.push(before[1],after[1]);qa.push({direction:d,records});
  comparison.push({direction:d,before:records.map(r=>`source/${d}/baseline_f${r.frame}.png`),after:records.map(r=>r.file),old_joints:old.frames.map(f=>f.state.joints),new_joints:poses.frames.map(f=>f.state.joints)});
 }
 await contact(overview.slice(0,8),path.join(root,'qa/front_comparison_4x.png'),4,[236,233,216],4);
 await contact(overview.slice(8),path.join(root,'qa/back_comparison_4x.png'),4,[236,233,216],4);
 await fs.writeFile(path.join(root,'source/imagegen-ledger.json'),JSON.stringify(ledger,null,2));
 await fs.writeFile(path.join(root,'comparison-metadata.json'),JSON.stringify(comparison,null,2));
 await fs.writeFile(path.join(root,'qa/frames.json'),JSON.stringify(qa,null,2));
 console.log(JSON.stringify(qa.map(q=>({direction:q.direction,edits:q.records.map(r=>r.adopted_joint_color_pixels),components:q.records.map(r=>r.components.length)}))));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
