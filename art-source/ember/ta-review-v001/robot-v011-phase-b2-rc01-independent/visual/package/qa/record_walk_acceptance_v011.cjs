// 只登记已经读过的B1 rc02正式TA回执；未来帧不继承这份PASS。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const receipt='qa/ta-receipt-phase-b1-rc02.md',bytes=await fs.readFile(path.join(root,receipt));
 if(!bytes.toString('utf8').includes('PASS，仅本批 NW / N / NE / SE 四条 walk，共32帧'))throw Error('Unexpected receipt scope');
 const metadata=JSON.parse(await fs.readFile(path.join(root,'source/reference-phase-b1-rc02-metadata.json'),'utf8'));
 const clips=metadata.clips.filter(c=>c.action==='walk');
 for(const c of clips)for(const f of c.frames)if(sha(await fs.readFile(path.join(root,f.file)))!==f.sha256)throw Error('Accepted frame changed');
 const registry={status:'SIX_WALK_DIRECTIONS_ACCEPTED',receipts:['qa/ta-receipt-phase-a-rc02.md',receipt],current_receipt_sha256:sha(bytes),directions:clips.map(c=>c.direction),clips,excludes:['left walk','right walk','final idle','collect','main game integration']};
 await fs.writeFile(path.join(root,'source/walk-acceptance-v011.json'),JSON.stringify(registry,null,2)+'\n');
 const file=path.join(root,'run-manifest.json'),m=JSON.parse(await fs.readFile(file,'utf8'));
 m.walk_acceptance_registry='source/walk-acceptance-v011.json';
 if(!m.review_history.some(r=>r.revision==='phase-b1-rc02'))m.review_history.push({revision:'phase-b1-rc02',decision:'PASS',scope:'NW/N/NE/SE 32 walk frames; previous S/SW retained',review:receipt,review_sha256:sha(bytes),zip_sha256:'b301fdea0e3f634d02a0da4eac437e1ce890515b582216daadc82c82211b4aaf'});
 await fs.writeFile(file,JSON.stringify(m,null,2)+'\n');console.log('Recorded six accepted walk directions with exact frame hashes');
})().catch(e=>{console.error(e);process.exitCode=1;});
