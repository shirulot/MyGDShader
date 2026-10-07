// 检查真实绑定函数，角度为画布投影角：0度代表伸直，非人体三维角度。
const fs=require('fs'),vm=require('vm'),path=require('path');
function inspect(dir){
 const code=fs.readFileSync(path.join(dir,'rig.js'),'utf8').split('Promise.all')[0];
 const context={document:{},Math};vm.createContext(context);
 vm.runInContext(code+';this.sample=pose;this.config=rig;',context);
 const poses=Array.from({length:8},(_,i)=>context.sample(i,'walk'));
 let errors=[],angles=[],reach=[];
 for(const p of poses)for(const side of ['near','far']){
  const q=p[side],a=q.hip.map((v,i)=>v-q.knee[i]),b=q.ankle.map((v,i)=>v-q.knee[i]);
  const upper=Math.hypot(...a),lower=Math.hypot(...b);
  errors.push(Math.abs(upper-12),Math.abs(lower-11));
  angles.push(180-Math.acos(Math.max(-1,Math.min(1,(a[0]*b[0]+a[1]*b[1])/upper/lower)))*180/Math.PI);
  reach.push(Math.hypot(q.hip[0]-q.ankle[0],q.hip[1]-q.ankle[1]));
 }
 const stride=context.config.stride,contacts={};
 for(const side of ['near','far'])contacts[side]=poses.filter(p=>p[side].support).map(p=>p[side].ankle.map((v,i)=>v+p.phase*stride*2*(i?.35:1)));
 return {poses,knee_flexion_projected_deg:{min:Math.min(...angles),max:Math.max(...angles)},bone_error_max:Math.max(...errors),reach_max:Math.max(...reach),contacts};
}
const current=inspect(__dirname),before=inspect(path.join(__dirname,'../human-ac-rig-pilot-v006'));
if(current.bone_error_max>1e-8||current.reach_max>=23)throw Error('IK target exceeds fixed bone reach');
const report={before:before.knee_flexion_projected_deg,after:current.knee_flexion_projected_deg,bone_error_max:current.bone_error_max,reach_max:current.reach_max,support_world_samples:current.contacts,scope:'8 sampled poses; not continuous contact or visual acceptance'};
fs.writeFileSync(path.join(__dirname,'qa/poses.json'),JSON.stringify(current.poses,null,2));
fs.writeFileSync(path.join(__dirname,'qa/kinematic-check.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report));
