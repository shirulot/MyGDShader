"""只打包可运行候选；不分发网络参考图，不改历史冻结包。"""
from pathlib import Path
import hashlib, json, zipfile
root=Path(__file__).resolve().parent
base=root.parent.parent
runtime=root/'runtime'
metadata=json.loads((runtime/'full-action-metadata.json').read_text(encoding='utf-8'))
check=json.loads((runtime/'evidence/runtime-import-validation.json').read_text(encoding='utf-8'))
assert check['technical_checks']=='PASS' and check['atlas_sha256']==metadata['atlas_sha256']
(runtime/'README.md').write_text('''# v013 弯膝采集候选

打开 project.godot 查看独立 Godot 工程。完整素材为八方向、24 段、112 帧。
本次修改采集 F1/F2 共16帧，原96帧保留。恢复髋部下沉、膝关节前屈，鞋底固定。
当前为待用户视觉反馈版本。Godot导入核对通过；图形进程被自动审批拒绝，未完成本轮Godot GPU播放检查。
网页 preview.html 需本地HTTP服务。未接入主游戏。
''',encoding='utf-8')
files=sorted(p for p in runtime.rglob('*') if p.is_file() and '.godot' not in p.parts and p.suffix!='.log')
manifest={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
destination=base.parent/'deliveries/robot_collect_knee_v013_candidate_2026-10-07.zip'
assert not destination.exists(), 'Do not overwrite a candidate package'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,'robot-v013/'+p.relative_to(runtime).as_posix())
    z.writestr('robot-v013/sha256-manifest.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(destination) as z:
    assert all(hashlib.sha256(z.read('robot-v013/'+f)).hexdigest()==h for f,h in manifest.items())
receipt={'status':'CANDIDATE_PENDING_USER_REVIEW','file':str(destination),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'payload_files':len(files),'atlas_sha256':metadata['atlas_sha256'],'gpu_check':'NOT_RUN_AUTOMATIC_APPROVAL_REJECTED','preserved_frames':96,'changed_frames':16}
(root/'qa/package.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
feedback_path=base/'qa/user-feedback-collect-knee.json'
feedback=json.loads(feedback_path.read_text(encoding='utf-8'))
feedback.update(status='REOPENED_USER_REQUIRES_KNEE_FLEXION',latest_user_feedback='膝关节要用上，参考网络上的类似动作帧改变；不接受v012锁腿回避弯膝',current_candidate='revisions/collect-knee-v013',current_preview='http://127.0.0.1:8141/revisions/collect-knee-v013/compare.html',resolution='PENDING_USER_VISUAL_REVIEW; historical v012 receipt is not acceptance of knee-flexion requirement')
feedback_path.write_text(json.dumps(feedback,ensure_ascii=False,indent=2),encoding='utf-8')
readme=base/'README.md'
text=readme.read_text(encoding='utf-8')
notice='> 当前采集动作已由用户重新打开：v012锁腿不符合需求。最新为 [v013弯膝候选](revisions/collect-knee-v013/README.md) / [前后对照](http://127.0.0.1:8141/revisions/collect-knee-v013/compare.html)，等待视觉反馈。以下v012信息为历史记录。\n\n'
if not text.startswith(notice):readme.write_text(notice+text,encoding='utf-8')
print(json.dumps(receipt))
