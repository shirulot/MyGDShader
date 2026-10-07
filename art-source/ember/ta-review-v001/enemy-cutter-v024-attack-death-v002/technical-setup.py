"""复用已审 C24 的独立探针，仅调整 v002 新注册与 N 机身动作公式。"""
from pathlib import Path

OUT=Path(__file__).resolve().parent
OLD=OUT.with_name('enemy-cutter-v024-attack-death-v001')
for name in ['technical-cold-probe.gd','technical-cold.py']:
    (OUT/name).write_bytes((OLD/name).read_bytes())
prepare=(OLD/'technical-prepare.py').read_text(encoding='utf-8')
for a,b in {
    'v024_v001_2026-10-07.zip':'v024_v002_2026-10-07.zip',
    'v024-review-v001':'v024-review-v002',
    '3802515':'3807029',
    'c3c1d9fb84d909fb113ee0a9d7ddac6afa98b8132f669ae0f5be5fa0963d572c':'3fc81f650daf58c949f216c4b9a783b03348d9ba11fcf512f7e6f08f92ff80be',
    '444e71fa6255dc25e5eb824a882c58bb07f94ba444364df20eac1039b1e99a7c':'fd2bf874e376a4ec7194e975a45c3b47a9cbee471ee6a09591b3fb5534f11a70',
    '327':'329','326':'328',
}.items():prepare=prepare.replace(a,b)
# 保留本次 runner，不再跨批次覆盖它。
start=prepare.index("prior=OUT.with_name(")
end=prepare.index("(OUT/'technical-zip-binding.json')",start)
prepare=prepare[:start]+prepare[end:]
(OUT/'technical-prepare.py').write_text(prepare,encoding='utf-8')

audit=(OLD/'technical-audit.py').read_text(encoding='utf-8')
# v002 修正 owner 的入口条件：盘面即便超出旧工具 polygon 也参与归属。
audit=audit.replace("use=poly(t['polygon'])\n", "use=poly(t['polygon'])|poly(t['blade_polygon'])\n")
old="        polygons={};supports={}"
new="""        # N 攻击绕固定机身轴做正交小旋转，实际脚掌仍为恒等变换。
        if action=='attack' and 'attack_body_poses' in cfg:
            bx,by,angle=cfg['attack_body_poses'][i];body=np.array([bx,by]);center=np.array(cfg['attack_body_pivot']);body_basis=rot(angle)
            transforms['body']=trans(body_basis,center+body-body_basis@center)
        body_basis=np.array([transforms['body']['basis_x'],transforms['body']['basis_y']]).T
        body_origin=np.array(transforms['body']['position'])
        polygons={};supports={}"""
assert old in audit;audit=audit.replace(old,new)
audit=audit.replace("start=np.array(s['start'])+body;end=", "start=body_basis@np.array(s['start'])+body_origin;end=")
# v001 的缺陷结论是历史，不自动移植到本轮。
start=audit.index("result['status']='RETURN_P2")
end=audit.index("(OUT/'technical-integrity.json')",start)
audit=audit[:start]+audit[end:]
(OUT/'technical-audit.py').write_text(audit,encoding='utf-8')
print('Independent probe setup ready; no frozen files changed.')
