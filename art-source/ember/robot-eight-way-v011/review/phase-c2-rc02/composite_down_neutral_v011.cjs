// 朝下中性姿态只采纳imagegen的膝内芯局部。鞋、甲片与图像轮廓沿用固定源。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {png,contact}=require('./build_fixed_rig_v011.cjs');
const root=__dirname,W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const colors=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A'].map(h=>[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)));
const nearest=p=>colors.reduce((best,c)=>{const d=c.reduce((sum,v,i)=>sum+(v-p[i])**2,0);return d<best.d?{d,c}:best;},{d:Infinity,c:colors[0]}).c;
const luminance=p=>p[0]*.2126+p[1]*.7152+p[2]*.0722;
async function main(){
 const folder='source/down-neutral-candidate',read=f=>fs.readFile(path.join(root,folder,f));
 const source=await sharp(await read('neutral_rig_raw.png')).ensureAlpha().raw().toBuffer();
 const bytes=await read('joint_edit_raw.png'),info=await sharp(bytes).metadata();
 if(Math.abs(info.width/info.height-2/3)>.001)throw Error('Wrong neutral edit aspect');
 const patch=await sharp(bytes).resize(W,H,{kernel:'nearest'}).ensureAlpha().raw().toBuffer(),output=Buffer.from(source),changed=[];
 const mask=Buffer.alloc(source.length);
 for(let y=66;y<=74;y++)for(let x=17;x<=29;x++){
  const at=(y*W+x)*4;if(((x+.5-24)/4.5)**2+((y+.5-70)/4)**2>1)continue;
  // 保护已有亮甲和全部透明外形；只替换原本就不透明的暗色膝内芯。
  if(!source[at+3]||patch[at+3]<160||luminance(source.subarray(at,at+3))>=125)continue;
  const color=nearest(patch.subarray(at,at+3));if(luminance(color)<60||luminance(color)>=150)continue;
  mask.set([255,255,255,255],at);output.set([...color,255],at);
  if(!source.subarray(at,at+4).equals(output.subarray(at,at+4)))changed.push([x,y]);
 }
 const file='source/action-candidate-masters/robot_neutral_down_v011.png';await png(output,path.join(root,file));
 await png(mask,path.join(root,folder,'joint_mask.png'));
 const identity=await sharp(path.join(root,'source/candidate-masters/robot_idle_down_v011.png')).ensureAlpha().raw().toBuffer();
 await contact([identity,source,output],path.join(root,'qa/down_neutral_source_rig_final_8x.png'),8,[236,233,216],3);
 const soleBands={};for(const[side,minX,maxX]of[['right',0,30],['left',31,63]]){let bottom=-1;for(let y=72;y<H;y++)for(let x=minX;x<=maxX;x++)if(output[(y*W+x)*4+3])bottom=Math.max(bottom,y);soleBands[side]=bottom;}
 const report={status:'NEUTRAL_SOURCE_CANDIDATE_PENDING_TA',file,sha256:sha(await fs.readFile(path.join(root,file))),
  imagegen_source:folder+'/joint_edit_raw.png',imagegen_sha256:sha(bytes),prompt:'prompts/down_neutral_joint_edit_v011.txt',input:folder+'/edit_target_8x.png',
  source_size:[info.width,info.height],single_global_transform:[W/info.width,H/info.height],changed_joint_pixels:changed.length,changed_coordinates:changed,
  boot_and_armor_protected:true,opaque_silhouette_unchanged_from_rig:true,sole_bottom_raster_y:soleBands,
  registration:folder+'/registration.json',accepted_walk_and_identity_files_modified:false,art_acceptance:'PENDING_TA'};
 await fs.writeFile(path.join(root,folder,'joint_patch.json'),JSON.stringify(report,null,2)+'\n');
 const manifestFile=path.join(root,'run-manifest.json'),manifest=JSON.parse(await fs.readFile(manifestFile,'utf8'));
 const entry={scope:'S double-support neutral knee seam',method:'imagegen_edit',source:report.imagegen_source,sha256:report.imagegen_sha256,prompt:report.prompt,
  actual_input:report.input,input_sha256:sha(await fs.readFile(path.join(root,report.input))),usage:'FIVE_PIXEL_KNEE_CORE_PATCH_ON_REGISTERED_NEUTRAL_SOURCE',
  original_output:'exec-9d9eadb2-bccd-4ef2-944c-5e9cdc573787.png',final_source:file,final_sha256:report.sha256,status:'STATIC_NEUTRAL_CANDIDATE_NOT_ACTION_ACCEPTANCE'};
 manifest.generation=manifest.generation.filter(item=>item.scope!==entry.scope).concat(entry);
 manifest.down_neutral_candidate={file,sha256:report.sha256,registration:report.registration,joint_patch:folder+'/joint_patch.json',art_acceptance:'PENDING_TA'};
 await fs.writeFile(manifestFile,JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify(report));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
