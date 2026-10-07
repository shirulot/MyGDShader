// 实际姿态函数的空间骨长、循环闭合和支撑采样检查；不能替代视觉检查。
const fs=require('fs'),vm=require('vm'),path=require('path');
const code=fs.readFileSync(path.join(__dirname,'rig.js'),'utf8').split('Promise.all')[0];
const context={document:{},Math,Image:class {}};vm.createContext(context);
vm.runInContext(code+';this.sample=pose;this.config=rig;this.mounts=mounts;',context);
const poses=Array.from({length:8},(_,i)=>context.sample(i,'walk')),config=context.config;
let error=0,projected=[];
for(const p of poses)for(const side of ['near','far']){
 const q=p[side],v=q.spatial;
 error=Math.max(error,Math.abs(Math.hypot(...v.knee)-12),Math.abs(Math.hypot(v.ankle[0]-v.knee[0],v.ankle[1]-v.knee[1])-11));
 projected.push({frame:p.phase*8,side,thigh:Math.hypot(q.hip[0]-q.knee[0],q.hip[1]-q.knee[1]),shin:Math.hypot(q.ankle[0]-q.knee[0],q.ankle[1]-q.knee[1])});
}
let contactError=0;const contacts={};
for(const side of ['near','far']){
 contacts[side]=poses.filter(p=>p[side].support).map(p=>p[side].ankle.map((v,i)=>v+p.phase*config.stride*2*(i?config.projection.forwardY:config.projection.forwardX)));
 for(const v of contacts[side])contactError=Math.max(contactError,Math.hypot(v[0]-contacts[side][0][0],v[1]-contacts[side][0][1]));
}
const end=context.sample(8,'walk'),start=poses[0];let cycleError=0;
for(const side of ['near','far'])for(const joint of ['hip','knee','ankle','shoulder','elbow','wrist'])cycleError=Math.max(cycleError,Math.hypot(...end[side][joint].map((v,i)=>v-start[side][joint][i])));
if(Math.max(error,contactError,cycleError)>1e-8)throw Error('Kinematic invariant failed');
const report={spatial_bone_error_max:error,projected_lengths:projected,support_world_samples:contacts,contact_sample_error:contactError,cycle_endpoint_error:cycleError,scope:'8 sampled poses, not pixel contact / visual / Godot acceptance'};
for(const [name,data] of Object.entries({'kinematic-check':report,poses,'mounts':context.mounts}))fs.writeFileSync(path.join(__dirname,'qa',name+'.json'),JSON.stringify(data,null,2));
console.log(JSON.stringify({bone_error:error,contact_error:contactError,cycle_error:cycleError}));
