"""按明确范围收集规范原文和登记，保留原字节；不修改生产资源。"""
from pathlib import Path
import hashlib, json, shutil, datetime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
records={}
def add(relative, domain, role):
    path=ROOT/relative
    if not path.is_file():
        raise FileNotFoundError(path)
    records[path.relative_to(ROOT).as_posix()]={'domain':domain,'role':role}

# 总规范和专项保留全文。历史记录保留，但不自动提升为现行规则。
docnames={
 '共同':['art-style-standard-v002.md','ta-art-review-standard-v001.md'],
 '基础环境':['autotile-production-standard-v002.md','autotile-neighborhoods-v002.json','reference-floor-v002-production.md','reference-floor-v003-materials.md','reference-floor-v004-materials.md','reference-floor-v005-materials.md','reference-floor-v006-materials.md','asset-production-technical-inputs.md'],
 '机器人历史':['asset-production-robot-actions-v003.md','robot-joint-repair-v004.md','robot-foot-motion-research-v001.md'],
 '敌人':['ember-enemy-animation-standard-v001.md','ember-enemy-eight-direction-standard-v002.md','ember-enemy-eight-direction-delivery-v027.md','ember-enemy-fixed-source-workflow-v002-draft.md'],
 'UI':['ember-ui-style-guide.md'],
 '历史规划':['art-generation-standard.md','art-production-handoff.md','asset-generation-manifest.csv','autotile-generation-manifest.csv','autotile-v007-style-unification.md','pixel-floor-v001-delivery.md','ember-building-standard-v001.md']}
for domain,names in docnames.items():
    for name in names:add('docs/shader-learning/'+name,domain,'完整专项/历史原文；适用性以统一规范为准')
for relative,domain in [
 ('assets/ember/environment/reference_floor_v006/README.md','基础环境'),
 ('assets/ember/environment/reference_floor_v006/catalog.json','基础环境'),
 ('assets/ember/data/technical_inputs_catalog_v001.json','技术输入'),
 ('art-source/ember/map-assets-v001/README.md','地图'),
 ('art-source/ember/map-assets-v001/source_specs_v001.json','地图'),
 ('assets/ember/map_assets_v001/README.md','地图'),
 ('art-source/ember/map-concepts-v001/README.md','地图'),
 ('art-source/ember/robot-eight-way-v011/README.md','机器人'),
 ('art-source/ember/robot-eight-way-v011/JOINT-RULES.md','机器人'),
 ('art-source/ember/robot-eight-way-v011/source/current-robot-action-contract.json','机器人历史'),
 ('art-source/ember/robot-eight-way-v011/qa/user-feedback-collect-knee.json','机器人最新反馈'),
 ('art-source/ember/robot-eight-way-v011/revisions/collect-knee-v013/README.md','机器人候选'),
 ('art-source/ember/robot-eight-way-v011/revisions/collect-knee-v014-pilot/README.md','机器人候选'),
 ('art-source/ember/robot-eight-way-v011/revisions/action-studies-v015/README.md','机器人候选'),
 ('art-source/ember/human-template-v001/character-standard.md','人类历史'),
 ('art-source/ember/human-design-options-v001/README.md','人类形象'),
 ('art-source/ember/human-ac-basic-v001/README.md','人类历史'),
 ('art-source/ember/human-ac-basic-v002/README.md','人类候选'),
 ('art-source/ember/human-ac-basic-v002/loop-contract.md','人类候选'),
 ('art-source/ember/human-ac-basic-v002/run-manifest.json','人类候选'),
 ('assets/ember/buildings_final/README.md','建筑'),
 ('assets/ember/buildings_final/review/style-inventory-2026-10-07/README.md','建筑完整回报'),
 ('assets/ember/buildings_final/review/style-inventory-2026-10-07/parameters.json','建筑完整回报'),
 ('assets/ember/buildings_final/review/style-inventory-2026-10-07/source-bindings.json','建筑完整回报'),
 ('assets/ember/buildings_final/textures/catalog_v004r1.json','建筑'),
 ('assets/ember/buildings_final/textures/functional_layers_v004r1.json','建筑'),
 ('assets/ember/ui_final/README.md','UI'),
 ('scripts/ember/ui_edge_v001/README.md','UI历史实现说明'),
 ('scripts/ember/ui_edge_v001/energy_progress.gd','UI参数依据'),
 ('scripts/ember/ui_edge_v001/timer_badge.gd','UI参数依据'),
 ('scripts/ember/ui_edge_v001/edge_ui_style.gd','UI参数依据'),
 ('scripts/ember/ui_edge_v004/modal_window.gd','UI参数依据'),
 ('scripts/ember/ui_edge_v004/interaction_ui.gd','UI参数依据'),
 ('scripts/ember/ui_edge_preview_v001.gd','UI示例参数依据'),
 ('scripts/ember/ui_edge_v004/interactive_preview.gd','UI示例参数依据'),
 ('assets/ember/ui_final/skins/inventory.json','UI'),
 ('art-source/ember/ui-interactions-v004/README.md','UI'),
 ('art-source/ember/ui-final/folder-migration.json','UI'),
 ('art-source/ember/enemy-spec-consolidation-v001/README.md','敌人完整回报'),
 ('art-source/ember/enemy-spec-consolidation-v001/source_manifest.json','敌人完整回报'),
 ('art-source/ember/enemy-spec-consolidation-v001/approved_batches.json','敌人完整回报'),
 ('art-source/ember/enemy-design-sheets-v001/design_catalog_v001.json','敌人设定'),
 ('art-source/ember/enemy-design-sheets-v001/parts_index_zh_v001.md','敌人设定'),
 ('art-source/ember/enemy-examples-v001/source_specs_v001.json','敌人设定'),
 ('assets/ember/characters/enemies_v003/README.md','敌人'),
 ('assets/ember/characters/enemies_v003/FINAL_ACCEPTANCE.json','敌人'),
 ('assets/ember/characters/enemies_v003/catalog.json','敌人'),
 ('art-source/ember/enemy-sequences-eight-directions-v027/assembly_recipe.json','敌人'),
 ('art-source/ember/enemy-sequences-eight-directions-v027-review-v001/TA_ACCEPTANCE.json','敌人'),
 ('art-source/ember/ta-review-v001/queue-2026-10-07.md','验收快照'),
 ('art-source/ember/ta-review-v001/enemy-v027-unified-v001/review-unified-package.md','敌人验收'),
 ('art-source/ember/ta-review-v001/enemy-v027-installation-v001/review-installation.md','敌人验收'),
 ('art-source/ember/ta-review-v001/robot-collect-knee-v012-rc01-independent/review-collect-knee.md','机器人历史验收'),
 ('art-source/ember/ta-review-v001/ui-v006-independent/review-ui-v006.md','UI验收'),
 ('art-source/ember/ta-review-v001/ui-folder-migration-independent/review.md','UI验收'),
 ('art-source/ember/ta-review-v001/ui-spec-integration.md','UI规范'),
 ('assets/ember/buildings_final/review/ta-review.md','建筑验收'),
 ('assets/ember/buildings_final/review/relocation-ta-review.md','建筑验收'),
 ('assets/ember/buildings_final/review/original-v004r1/review-building-v004r1.md','建筑验收')]:
    add(relative,domain,'实际登记、来源说明或限定范围的验收记录')
for path in (ROOT/'assets/ember/buildings_final/docs').glob('*.md'):
    add(path.relative_to(ROOT),'建筑','完整专项原文')

rows=[]
for relative,meta in sorted(records.items()):
    source=ROOT/relative
    destination=HERE/'sources'/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)
    raw=source.read_bytes()
    assert destination.read_bytes()==raw
    rows.append(dict(path=relative,snapshot=destination.relative_to(HERE).as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),**meta))
report={'collected_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'scope':'four art production chats; source documents, active catalogs and scoped acceptance evidence, not a new asset acceptance','files':rows}
(HERE/'source-index.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 完整原文收集索引','',f'本次收集 {len(rows)} 份规范、合同、目录和限定范围回执；原字节保存，SHA256 见 [机器索引](source-index.json)。收集时间：'+report['collected_at']+'。','',
 '[统一阅读入口](../../../../docs/shader-learning/ember-art-unified-v001.md) · [实际参数附录](parameters.md) · [四 chat 补充](collection-notes.md)','',
 '原文中的历史“当前／通过”不自动成为现行结论。快照保留原文相对链接文本，浏览资源与引用请使用下表的原位置；快照不是完整离线资产包。','',
 '|领域|原位置|原文快照|字节|','|---|---|---|---|']
for r in rows:lines.append(f"|{r['domain']}|[{r['path']}](../../../../{r['path']})|[全文]({r['snapshot']})|{r['bytes']}|")
(HERE/'source-index.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

# 参数不再人工复抄每项，直接从当前实际登记生成附录。
ui=json.loads((ROOT/'assets/ember/ui_final/skins/inventory.json').read_text(encoding='utf-8-sig'))
lines=['# 实际登记参数附录','', '此表从本次快照对应的实际 JSON 提取，读者需同时遵守统一规范的范围、例外与历史覆盖关系。','', '## UI 全部皮肤','', '|ID|画布|九宫格 左/上/右/下|职责|','|---|---|---|---|']
for a in ui['assets']:
    lines.append('|'+str(a['id'])+'|'+'×'.join(map(str,a['canvas']))+'|'+'/'.join(map(str,a.get('nine_slice_margin_ltrb',[])))+'|'+str(a.get('dynamic_responsibility','')).replace('|','/')+'|')
catalog=json.loads((ROOT/'assets/ember/buildings_final/textures/catalog_v004r1.json').read_text(encoding='utf-8-sig'))
lines+=['','## 建筑门口与精确注册','', '|建筑ID|canvas|pivot|uniform_scale|脚印world|门ID及净口world|','|---|---|---|---|---|---|']
for b in catalog['buildings']:
    lines.append('|'+b['id']+'|'+str(b['canvas_px'])+'|'+str(b['source_pivot_px'])+'|'+str(b['uniform_scale'])+'|'+str(b['footprint_px'])+'|'+'; '.join(d['id']+': '+str(d['clear_world_px']) for d in b['doors'])+'|')
lines+=['','完整坐标区域、源路径、SHA、功能层与其他数值见 [完整收集索引](source-index.md) 对应 JSON，避免人工复抄截断精度。','']
(HERE/'parameters.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'files':len(rows),'ui_skins':len(ui['assets']),'buildings':len(catalog['buildings'])}))
