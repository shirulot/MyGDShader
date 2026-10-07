// 只验预览播放器的闭环索引与方向相位，不把结果当视觉无缝证明。
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.dirname(__dirname),data=JSON.parse(fs.readFileSync(path.join(root,'catalog.json')));
const elements={},buttons=['up_left','up','up_right','left','right','down_left','down','down_right'].map(dir=>({dataset:{dir},setAttribute(){}}));
const defaults={action:'walk',speed:'1',background:'#182631',scale:'4'};
function element(id){return elements[id]??={value:defaults[id]??'',textContent:'',getContext:()=>({fillRect(){},beginPath(){},moveTo(){},lineTo(){},stroke(){},drawImage(){}})};}
const ctx=vm.createContext({document:{getElementById:element,querySelectorAll:()=>buttons},Image:class{async decode(){}},fetch:async()=>({json:async()=>data}),requestAnimationFrame(){}});
vm.runInContext(fs.readFileSync(path.join(root,'preview.html'),'utf8').match(/<script>([\s\S]*?)<\/script>/)[1],ctx);
setImmediate(()=>{
  for(const c of data.clips){
    vm.runInContext(`ui.action.value=${JSON.stringify(c.action)};direction=${JSON.stringify(c.direction)};elapsed=0;phase=0;cycles=0;last=0;playing=true;refresh();`,ctx);
    const end=c.duration_ms*c.frame_count*11;
    for(let t=0;t<=end;t+=20)vm.runInContext(`tick(${t})`,ctx);
    assert(vm.runInContext('cycles>=10 && phase>=0 && phase<1',ctx),c.key);
    vm.runInContext('ui.seam.onclick();ui.step.onclick();',ctx);
    assert.equal(vm.runInContext('phase',ctx),0,c.key+' tail wraps to first');
  }
  vm.runInContext("ui.action.value='walk';direction='left';pauseAt(3)",ctx);
  const before=vm.runInContext('phase',ctx);buttons.find(b=>b.dataset.dir==='down').onclick();
  assert.equal(vm.runInContext('phase',ctx),before);
  fs.writeFileSync(path.join(root,'qa','player-check.json'),JSON.stringify({status:'pass',clips:data.clips.length,checks:['11 simulated cycles per clip','tail -> first step','direction preserves phase'],visual_browser_test:false},null,2));
  console.log('PASS 58 clips: cycle indices, tail wrap, direction phase. No visual claim.');
});
