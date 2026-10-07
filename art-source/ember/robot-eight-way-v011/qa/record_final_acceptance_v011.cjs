// 正式回执已由制作方阅读；把24条已通过动作绑定到获审ZIP和逐帧哈希。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=async f=>JSON.parse(await fs.readFile(path.join(root,f),'utf8'));
(async()=>{
 const revision='phase-c2-rc02',frozen=path.join(root,'review',revision);
 const receiptFile='qa/ta-receipt-phase-c2-rc02.md';
 const receipt=await fs.readFile(path.join(root,'../ta-review-v001/robot-v011-phase-c2-rc02-independent/review-c2-rc02.md'));
 const delivery=await read('qa/delivery_phase-c2-rc02.json');
 const metadata=JSON.parse(await fs.readFile(path.join(frozen,'full-action-metadata.json'),'utf8'));
 if(!receipt.toString().includes('**PASS，2026-10-07。**')||!receipt.toString().includes(delivery.zip_sha256))throw Error('Formal receipt binding missing');
 if(sha(await fs.readFile(delivery.zip))!==delivery.zip_sha256)throw Error('Accepted ZIP changed');
 const frames=metadata.clips.flatMap(c=>c.frames);
 for(const frame of frames)if(sha(await fs.readFile(path.join(frozen,frame.file)))!==frame.sha256)throw Error('Accepted frame changed');
 await fs.writeFile(path.join(root,receiptFile),receipt);
 const gate={status:'READY_FOR_FINAL_RELEASE',source_revision:revision,accepted_clips:24,accepted_frames:112,atlas_sha256:metadata.atlas_sha256,
  ta_receipt:receiptFile,ta_receipt_sha256:sha(receipt),source_zip_sha256:delivery.zip_sha256,source_manifest_sha256:delivery.sha256_manifest_sha256,
  source_metadata_sha256:delivery.metadata_sha256,scope:'Fixed eight-way assets and independent preview; main game integration is separate'};
 await fs.writeFile(path.join(root,'qa/final-release-gate.json'),JSON.stringify(gate,null,2)+'\n');
 await fs.writeFile(path.join(root,'source/final-action-acceptance-v011.json'),JSON.stringify({...gate,status:'ALL_24_CLIPS_112_FRAMES_ACCEPTED',clips:metadata.clips.map(c=>({...c,art_status:'PASS'}))},null,2)+'\n');
 console.log(JSON.stringify(gate));
})().catch(error=>{console.error(error);process.exitCode=1;});
