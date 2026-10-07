"""仅归档真实内置生图工具已返回的单资产PNG，保留原输出及哈希证据。"""
import argparse, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cli=argparse.ArgumentParser();cli.add_argument('id');cli.add_argument('source',type=Path)
    args=cli.parse_args()
    specs=json.loads((BASE/'planned-catalog-v001.json').read_text(encoding='utf-8'))['assets']
    spec=next(s for s in specs if s['id']==args.id)
    if not args.source.is_file(): raise FileNotFoundError(args.source)
    out=BASE/'generated'/f'{args.id}_master_v001.png'
    if out.exists() and sha(out)!=sha(args.source): raise ValueError('禁止无声覆盖已归档不同母稿')
    shutil.copyfile(args.source,out)
    record_path=BASE/'generation-record.json'
    data=json.loads(record_path.read_text(encoding='utf-8')) if record_path.exists() else {
       'tool':'built-in image_gen.imagegen','scope':'B02-B12 18 artistic units; component masks are source derivatives',
       'style_approval':'本批整体风格尚待根审阅，不虚报用户最终确认','assets':[]}
    im=Image.open(out)
    item={'id':args.id,'manifest_id':spec['manifest_id'],'tool':'built-in image_gen.imagegen',
          'archived_at_utc':datetime.now(timezone.utc).isoformat(),'tool_output':str(args.source),
          'master':out.relative_to(ROOT).as_posix(),'sha256':sha(out),'size':list(im.size),'mode':im.mode,
          'prompt':spec['prompt'],'prompt_sha256':sha(BASE/spec['prompt']),
          'references':[{'file':p,'sha256':sha(ROOT/p)} for p in spec['references']],
          'successful_tool_output':True,'production_approval':'NOT_EVALUATED'}
    data['assets']=[a for a in data['assets'] if a['id']!=args.id]+[item]
    data['successful_outputs']=len(data['assets'])
    record_path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'archived':item['master'],'size':item['size'],'sha256':item['sha256']}))
if __name__=='__main__':main()
