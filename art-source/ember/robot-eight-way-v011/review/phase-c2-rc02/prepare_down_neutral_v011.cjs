// 朝下身份来自已通过的walk F02，该帧有0.8世界像素的右脚抬起，不能冒充中性待机。
// 先把同源右小腿/靴作为一个部件下移1栅格，膝部保留2行重叠；接缝交给imagegen局部修形。
// 只生成排姿输入，不覆盖身份母版、已通过walk或最终idle。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {png,stamp,contact}=require('./build_fixed_rig_v011.cjs');
const root=__dirname,W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function main(){
 const sourceFile='frames/walk/down/robot_walk_down_f02_v010.png';
 const bytes=await fs.readFile(path.join(root,sourceFile));
 if(sha(bytes)!=='31aef53af6a5552d9adae69f5afefab25ee35cc30059bf285dffc375f374dc79')throw Error('Approved S reference changed');
 const source=await sharp(bytes).ensureAlpha().raw().toBuffer();
 const upper=Buffer.from(source),rightLower=Buffer.alloc(source.length);
 // 分区仅覆盖画面左侧的解剖右小腿和靴，头胸、双臂与左腿不动。
 for(let y=68;y<H;y++)for(let x=0;x<31;x++){
  const at=(y*W+x)*4;source.copy(rightLower,at,at,at+4);if(y>=70)upper.fill(0,at,at+4);
 }
 const output=Buffer.alloc(source.length);
 stamp(output,rightLower,{sourcePivot:[22,75.2],targetPivot:[22,76.2],radians:0});
 stamp(output,upper,{sourcePivot:[32,80],targetPivot:[32,80],radians:0});
 const folder='source/down-neutral-candidate';
 await png(source,path.join(root,folder,'identity_f02_8x.png'),8);
 await png(rightLower,path.join(root,folder,'right_lower_original.png'));
 await png(upper,path.join(root,folder,'other_original.png'));
 await png(output,path.join(root,folder,'neutral_rig_raw.png'));
 await png(output,path.join(root,folder,'edit_target_8x.png'),8);
 await contact([source,output],path.join(root,'qa/down_neutral_before_patch_8x.png'),8,[236,233,216],2);
 const changes=[];for(let at=0;at<source.length;at+=4)if(!source.subarray(at,at+4).equals(output.subarray(at,at+4)))changes.push([at/4%W,Math.floor(at/4/W)]);
 const report={status:'RAW_NEUTRAL_POSE_NOT_ART_ACCEPTED',source:sourceFile,source_sha256:sha(bytes),source_phase:'right_passing',
  source_support:'left only; right sole world y79.2, declared ground y80',target:'double support registered stance',
  transform:{part:'anatomical right lower leg and boot',translation:[0,1],rotation:0,scale:1,source_region:{x:[0,30],y:[68,95]},overlap_rows:[68,69]},
  requested_right_sole_world_y:80,rounding_note:'0.8 pixel lift rounds to 1 pixel at the native raster; source shoe is never resized or folded',
  immutable_outside_region:true,changed_pixels:changes.length,changed_coordinates:changes,raw_rgba_sha256:sha(output)};
 await fs.writeFile(path.join(root,folder,'registration.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({source_sha256:sha(bytes),changed_pixels:changes.length,target:path.join(folder,'edit_target_8x.png')}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
