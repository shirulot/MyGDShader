from pathlib import Path
from collections import Counter
import json
p=Path(__file__).resolve().parent
r=json.loads((p/'technical-integrity.json').read_text(encoding='utf-8'))
summary={'part_counts':r['bindings7'],'partial_alpha_socket_sources':[x for x in r['sockets'] if x['source_opaque_pixels']!=4],
'residual_frames':[{'d':f['direction'],'action':f['action'],'frame':f['frame'],'rgba':len(f['cpu_residual']),'alpha':f['cpu_alpha_residual'],'residual':f['cpu_residual']} for f in r['frames98'] if f['cpu_residual']],
'unmatched_extra':[{'d':f['direction'],'action':f['action'],'frame':f['frame'],'pixels':[v for v in f['cpu_base_uncovered_actual_pixels'] if not v['registered_socket_source_matches']]} for f in r['frames98'] if any(not v['registered_socket_source_matches'] for v in f['cpu_base_uncovered_actual_pixels'])],
'support_totals':dict(Counter(('self_visible' if p['self_visible_cpu'] else 'occluded_or_unowned') for f in r['frames98'] for p in f['registered_fixed_feet'])),
'nonself_supports':[{'d':f['direction'],'action':f['action'],'frame':f['frame'],'probes':[p for p in f['registered_fixed_feet'] if not p['self_visible_cpu'] or p['source_owner']!=p['id']+'_foot']} for f in r['frames98'] if any(not p['self_visible_cpu'] or p['source_owner']!=p['id']+'_foot' for p in f['registered_fixed_feet'])]}
(p/'technical-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
