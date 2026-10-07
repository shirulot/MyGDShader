"""生成可离线浏览的最终 UI 目录，只引用现有文件，不复制或修改图片和运行代码。"""

from pathlib import Path
import hashlib
import json
import os


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/ember/ui_final"
SKINS = ROOT / "assets/ember/ui_final/skins"
PREVIEWS = OUT / "previews"
ARCHIVE = ROOT / "art-source/ember/deliveries/ui_edge_interactions_v006_2026-10-06.zip"
EXPECTED_ARCHIVE = "af61549eef1605a98301f822c2018d68bed4687118a2ed8c499073e71e758504"


def file_record(path: Path) -> dict:
    """相对链接便于整个项目移动；SHA 用于证明总览引用的是哪份实际文件。"""
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "href": Path(os.path.relpath(path, OUT)).as_posix(),
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


skin_labels = {
    "panel_backplate_96": ("窗口底板", "底板与边框"),
    "text_backplate_96": ("读数底板", "底板与边框"),
    "bracket_corner_16": ("角括号", "底板与边框"),
    "life_outline_24x32": ("生命空槽", "生命与能量"),
    "life_fill_24x32": ("生命填充", "生命与能量"),
    "energy_track_32x16": ("能量轨道", "生命与能量"),
    "energy_fill_8x8": ("能量填充", "生命与能量"),
    "energy_mask_8x8": ("能量技术蒙版", "生命与能量"),
    "copper_clamp_12x24": ("铜端夹", "生命与能量"),
    "drawer_handle_10x32": ("终端拉手", "底板与边框"),
    "selection_row_96": ("当前状态行底", "状态与交互"),
    "selection_tick_4x32": ("状态强调线", "状态与交互"),
    "status_safe_32": ("安全 · 菱形", "状态与交互"),
    "status_warning_32": ("预警 · 三角", "状态与交互"),
    "status_burst_32": ("爆发 · 星形", "状态与交互"),
    "status_cooldown_32": ("冷却 · 时钟", "状态与交互"),
    "button_focus_96": ("焦点角层", "状态与交互"),
    "portrait_frame_96": ("设备肖像框", "底板与边框"),
}
preview_labels = [
    ("overview", "HUD 与详情总览"),
    ("hud", "横向生命 HUD"), ("details", "设备详情"),
    ("terminal", "侧终端"), ("pause", "暂停菜单"),
    ("settings", "界面设置"), ("help", "操作说明"),
    ("confirm_restart", "重新开始确认"), ("confirm_title", "返回起始页确认"),
    ("title", "起始页"), ("success", "成功结算"),
    ("failure", "失败结算"), ("toast", "非阻断提示"),
    ("compact_settings_320x480", "320 × 480 小屏设置"),
    ("settings_slider_focused_720", "滑条 · 获得焦点"),
    ("settings_slider_unfocused_720", "滑条 · 失去焦点"),
]
component_labels = [
    ("edge_hud", "现场 HUD", "生命、时间、能量、标记与侧终端组合"),
    ("life_indicator", "横向生命", "空槽常驻；生命值单独控制填充"),
    ("timer_badge", "时间牌", "独立 Label 输出倒计时"),
    ("energy_progress", "能量条", "只裁填充，轨道与端夹保持完整"),
    ("station_marker", "设备标记", "根据设备与可见世界范围显示"),
    ("state_row", "状态行", "图形、颜色与文字来自同一状态"),
    ("station_drawer", "侧终端", "非模态设备信息与返回入口"),
    ("bracket_button", "角括号按钮", "独立底层状态、文字和焦点层"),
]
documents = [
    ("UI 风格与制作规范", "docs/shader-learning/ember-ui-style-guide.md"),
    ("使用与接入说明", "art-source/ember/ui-interactions-v004/README.md"),
    ("资源文字索引", "assets/ember/ui_final/README.md"),
    ("皮肤尺寸合同", "assets/ember/ui_final/skins/inventory.json"),
    ("TA v006 正式回执", "art-source/ember/ta-review-v001/ui-v006-independent/review-ui-v006.md"),
    ("规范与清理独立复核", "art-source/ember/ta-review-v001/ui-final-closeout-review.md"),
    ("规范保存与统合回执", "art-source/ember/ta-review-v001/ui-spec-integration.md"),
]

inventory = json.loads((SKINS / "inventory.json").read_text(encoding="utf-8-sig"))
assets = []
for source in inventory["assets"]:
    identifier = source["id"]
    title, group = skin_labels[identifier]
    assets.append({
        **file_record(SKINS / f"{identifier}.png"),
        "id": identifier, "title": title, "group": group,
        "canvas": source["canvas"],
        "slice": source["nine_slice_margin_ltrb"],
        "note": source["dynamic_responsibility"],
    })

catalog = {
    "revision": "v006",
    "archive": file_record(ARCHIVE),
    "assets": assets,
    "previews": [{**file_record(PREVIEWS / f"{name}.png"), "title": title}
                 for name, title in preview_labels],
    "components": [{**file_record(ROOT / f"scenes/ember/ui_edge_v001/components/{name}.tscn"),
                    "title": title, "note": note} for name, title, note in component_labels],
    "flow": file_record(OUT / "ui.tscn"),
    "demo": file_record(OUT / "demo.tscn"),
    "documents": [{**file_record(ROOT / path), "title": title} for title, path in documents],
}
if catalog["archive"]["sha256"] != EXPECTED_ARCHIVE:
    raise ValueError("最终 ZIP 与已通过版本不一致；停止生成总览。")

HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ember · 最终 UI 资源总览</title>
<style>
:root{color-scheme:dark;--bg:#101820;--panel:#182631;--line:#2b3e4b;--ink:#ece9d8;--muted:#829ba3;--cyan:#51c5c2;--brass:#b77c4b}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:76px}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 'Microsoft YaHei','Noto Sans CJK SC',sans-serif}a{color:var(--cyan);text-underline-offset:4px}button,input,select{font:inherit}button{cursor:pointer}button,a,input,select{outline-offset:5px}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--cyan)}[hidden]{display:none!important}button:disabled{cursor:default}code{font:13px/1.7 Consolas,monospace;overflow-wrap:anywhere}h1,h2,h3,p{margin:0}h1{font-size:clamp(28px,4vw,42px);line-height:1.35;letter-spacing:2px}h2{font-size:23px}h3{font-size:17px}header,main,footer{max-width:1280px;margin:auto;padding:32px}header{padding-top:52px}.eyebrow{font:12px Consolas,monospace;letter-spacing:3px;color:var(--muted);margin-bottom:12px}.intro{max-width:760px;margin:18px 0;color:var(--muted)}.badges,.actions,.stats{display:flex;gap:12px;flex-wrap:wrap}.badge{font-size:12px;padding:3px 10px;border:1px solid var(--line);color:var(--cyan)}.stats{margin-top:26px;gap:32px}.stats strong{font:26px Consolas,monospace;color:var(--ink);margin-right:8px}.stats span{color:var(--muted);font-size:13px}.button{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:8px 16px;border:1px solid var(--line);color:var(--ink);background:transparent;text-decoration:none}.button:hover{background:var(--panel);border-color:var(--muted)}.primary{border-color:var(--cyan);color:var(--cyan)}nav{position:sticky;top:0;z-index:2;background:var(--bg);border-block:1px solid var(--line);display:flex;gap:28px;padding:14px max(32px,calc((100vw - 1216px)/2));overflow-x:auto}nav a{white-space:nowrap;text-decoration:none;color:var(--ink);font-size:14px}section+section{margin-top:60px}.section-head{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:18px}.muted{color:var(--muted);font-size:13px}.hero{padding:0;border:1px solid var(--line);background:#0e171e;display:block;width:100%;cursor:zoom-in}.hero img{width:100%;display:block}.previews{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:18px}.preview{padding:0;text-align:left;color:var(--ink);border:1px solid var(--line);background:transparent;cursor:zoom-in;overflow:hidden}.preview:hover{border-color:var(--muted)}.preview img{display:block;width:100%;height:230px;object-fit:contain;image-rendering:pixelated;background:#0b1218}.preview span{display:block;padding:12px 14px;font-size:14px}.filters{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}input,select{background:var(--panel);border:1px solid var(--line);color:var(--ink);min-height:42px;padding:8px 12px}input{flex:1;min-width:200px}select{min-width:170px}.skins{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.skin{border:1px solid var(--line);padding:16px}.checker{height:210px;display:grid;place-items:center;background-color:#1b2830;background-image:conic-gradient(#25343e 25%,transparent 0 50%,#25343e 0 75%,transparent 0);background-size:16px 16px;border:0;width:100%;cursor:zoom-in;margin-bottom:14px}.checker img{image-rendering:pixelated;max-width:none}.skin .muted{margin-top:4px}.skin p{font-size:13px;color:var(--muted);margin:10px 0;min-height:64px}.skin code{display:block;margin:10px 0;color:var(--muted);font-size:12px}.skin .button{padding:5px 10px;min-height:34px;font-size:12px}.empty{padding:32px;border:1px solid var(--line);text-align:center;color:var(--muted)}.flow{border-left:3px solid var(--cyan);background:var(--panel);padding:20px 24px;margin-bottom:18px}.flow p{margin:8px 0 12px;color:var(--muted)}.flow code{display:block;margin-bottom:12px}.components{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.component{padding:18px;border:1px solid var(--line)}.component p{font-size:13px;color:var(--muted);margin:8px 0}.component code{display:block;margin:10px 0}.component .button{font-size:12px;min-height:34px}.docs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.doc{padding:16px;border:1px solid var(--line);text-decoration:none}.doc:hover{background:var(--panel)}.run{padding:24px;border:1px solid var(--line);margin:24px 0}.run p{margin:8px 0;color:var(--muted)}.run code{display:block;margin:14px 0}.notice{font-size:13px;color:var(--muted);border-left:2px solid var(--brass);padding:10px 16px;margin-top:20px}footer{color:var(--muted);border-top:1px solid var(--line);font-size:12px}.status{min-height:24px;color:var(--cyan);font-size:13px;margin-top:10px}dialog{max-width:calc(100vw - 32px);max-height:calc(100vh - 32px);padding:18px;background:var(--bg);border:1px solid var(--muted);color:var(--ink)}dialog::backdrop{background:#061015e0}.dialog-head{display:flex;align-items:center;justify-content:space-between;gap:24px;margin-bottom:14px}.dialog-image{display:block;max-width:calc(100vw - 72px);max-height:calc(100vh - 170px);height:auto;object-fit:contain;image-rendering:pixelated;margin:auto;background:repeating-conic-gradient(#25343e 0 25%,#1b2830 0 50%) 0/16px 16px}.dialog-foot{margin-top:14px;font-size:12px;color:var(--muted)}@media(max-width:900px){.previews,.skins{grid-template-columns:repeat(2,minmax(0,1fr))}.preview img{height:200px}}@media(max-width:560px){header,main,footer{padding:24px 18px}header{padding-top:32px}nav{padding:12px 18px;gap:20px}.previews,.skins,.components,.docs{grid-template-columns:1fr}.section-head{align-items:start;flex-direction:column}.preview img{height:280px}.stats{gap:20px}input,select{width:100%}.filters{display:block}.filters>*+*{margin-top:10px}.flow{padding:18px}section+section{margin-top:44px}}
</style>
</head>
<body>
<header>
 <div class="eyebrow">EMBER / UI LIBRARY / V006</div>
 <h1>边缘标记 · 最终资源总览</h1>
 <p class="intro">横向生命、细线与角括号、蓝灰终端。已保留的皮肤、可复用组件和真实 Godot 示例集中在这里，可直接查看原图、复制资源路径或打开完整交付包。</p>
 <div class="badges"><span class="badge">v006 组件与专项示例 · TA PASS</span><span class="badge">原生资源 · 引擎实图</span></div>
 <div class="stats"><span><strong>18</strong>皮肤 PNG</span><span><strong>8</strong>基础组件</span><span><strong>16</strong>引擎截图</span><span><strong>1</strong>完整交互入口</span></div>
</header>
<nav aria-label="资源导航"><a href="#examples">最终效果</a><a href="#skins">皮肤资源</a><a href="#components">可复用组件</a><a href="#use">运行与规范</a></nav>
<main>
 <section id="examples"><div class="section-head"><h2>最终效果与窗口示例</h2><span class="muted">点击查看原图；均为已有 Godot 截图</span></div><div id="overview"></div><div class="previews" id="preview-grid"></div></section>
 <section id="skins"><div class="section-head"><h2>皮肤资源</h2><span class="muted" id="skin-count">18 / 18 个素材</span></div><p class="muted" style="margin-bottom:16px">棋盘格表示透明区域，素材按 2× 最近邻展示。九宫格边距顺序：左／上／右／下。技术蒙版不作为可见皮肤。</p><div class="filters"><input id="search" type="search" aria-label="搜索皮肤" placeholder="搜索名称、文件名或用途…"><select id="group" aria-label="筛选皮肤分类"><option value="">全部分类</option><option>底板与边框</option><option>生命与能量</option><option>状态与交互</option></select></div><div class="skins" id="skin-grid"></div><p class="empty" id="empty" hidden>没有匹配的素材，试试其他关键词。</p></section>
 <section id="components"><div class="section-head"><h2>可复用组件</h2><span class="muted">保留已通过的原资源路径</span></div><div class="flow"><h3>完整交互 UI</h3><p>HUD、详情、终端、暂停、设置、帮助、确认、起始、结算与 Toast。接入宿主时从这个场景开始。</p><code id="flow-path"></code><button class="button primary" id="copy-flow">复制总入口路径</button></div><div class="components" id="component-grid"></div></section>
 <section id="use"><div class="section-head"><h2>运行、规范与交付</h2><span class="muted">资源总览可离线打开；请保留项目相对目录</span></div><div class="run"><h3>运行完整 Godot 示例</h3><p>在当前项目中打开下面场景，按 F6。点击「设备详情」或「菜单」查看全部窗口；键盘 Tab 切焦点、Enter 确认、Esc 返回。</p><code id="demo-path"></code><div class="actions"><button class="button primary" id="copy-demo">复制示例路径</button><a class="button" id="archive" download>下载独立工程 ZIP</a></div><p class="muted">独立 ZIP 解压后，用 Godot 打开其中 project.godot 并运行。完整宿主示例包含地图依赖。</p></div><div class="docs" id="document-grid"></div><p class="notice">当前通过范围为 UI 组件与潮汐港专项交互宿主。原目录中的 v001、v004 是活动依赖路径，当前交付修订为 v006。审核目录里的 cold-project 已清理为证据保留区，复验使用上面的完整 ZIP。</p><p class="status" id="copy-status" role="status" aria-live="polite"></p></section>
</main>
<footer>只引用现有资源，没有复制或重新生成图片。<a href="../../../art-source/ember/ui-final/cleanup-report.json">历史清理记录</a> · <a href="../../../art-source/ember/ui-final/folder-migration.json">目录迁移记录</a> · <a href="catalog-manifest.json">总览文件绑定</a></footer>
<dialog id="image-dialog" aria-labelledby="dialog-title"><div class="dialog-head"><strong id="dialog-title"></strong><button class="button" id="dialog-close">关闭</button></div><img id="dialog-image" class="dialog-image" alt=""><p class="dialog-foot"><a id="original-link" target="_blank" rel="noopener">单独打开原图</a><span id="image-dimensions"></span></p></dialog>
<script id="catalog-data" type="application/json">__CATALOG_JSON__</script>
<script>
'use strict';
const catalog = JSON.parse(document.getElementById('catalog-data').textContent);
const byId = id => document.getElementById(id);
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const images = [...catalog.previews, ...catalog.assets];
// 只用清单内的图片打开原图，浏览总览不会改动图片或 Godot 工程。
const imageButton = (item, hero=false) => `<button class="${hero?'hero':'preview'}" data-image="${esc(item.href)}" aria-label="查看${esc(item.title)}原图"><img src="${esc(item.href)}" alt="${esc(item.title)}">${hero?'':`<span>${esc(item.title)}</span>`}</button>`;
byId('overview').innerHTML = imageButton(catalog.previews[0], true);
byId('preview-grid').innerHTML = catalog.previews.slice(1).map(item => imageButton(item)).join('');
byId('skin-grid').innerHTML = catalog.assets.map(item => `<article class="skin" data-search="${esc([item.id,item.title,item.note,item.group].join(' ').toLowerCase())}" data-group="${esc(item.group)}"><button class="checker" data-image="${esc(item.href)}" aria-label="查看${esc(item.title)}原图"><img src="${esc(item.href)}" width="${item.canvas[0]*2}" height="${item.canvas[1]*2}" alt="${esc(item.title)}"></button><h3>${esc(item.title)}</h3><div class="muted">${item.canvas.join(' × ')} px · ${esc(item.group)}</div><div class="muted">九宫格 ${item.slice.join(' / ')}</div><p>${esc(item.note)}</p><code>res://${esc(item.path)}</code><div class="actions"><button class="button" data-copy="res://${esc(item.path)}">复制资源路径</button><a class="button" href="${esc(item.href)}" download>PNG</a></div></article>`).join('');
byId('component-grid').innerHTML = catalog.components.map(item => `<article class="component"><h3>${esc(item.title)}</h3><p>${esc(item.note)}</p><code>res://${esc(item.path)}</code><button class="button" data-copy="res://${esc(item.path)}">复制场景路径</button></article>`).join('');
byId('document-grid').innerHTML = catalog.documents.map(item => `<a class="doc" href="${esc(item.href)}">${esc(item.title)} ↗</a>`).join('');
byId('flow-path').textContent = 'res://' + catalog.flow.path;
byId('demo-path').textContent = 'res://' + catalog.demo.path;
byId('copy-flow').dataset.copy = 'res://' + catalog.flow.path;
byId('copy-demo').dataset.copy = 'res://' + catalog.demo.path;
byId('archive').href = catalog.archive.href;
function filterSkins() {
 const query = byId('search').value.trim().toLowerCase(), group = byId('group').value;
 let count = 0;
 document.querySelectorAll('.skin').forEach(card => {
  card.hidden = !(card.dataset.search.includes(query) && (!group || card.dataset.group === group));
  if (!card.hidden) count++;
 });
 byId('skin-count').textContent = `${count} / ${catalog.assets.length} 个素材`;
 byId('empty').hidden = count > 0;
}
byId('search').addEventListener('input', filterSkins);
byId('group').addEventListener('change', filterSkins);
// 原生 dialog 负责模态焦点和 Esc；关闭时显式恢复到原图片按钮。
let imageTrigger = null;
document.addEventListener('click', async event => {
 const imageControl = event.target.closest('[data-image]');
 if (imageControl) {
  const item = images.find(image => image.href === imageControl.dataset.image);
  if (!item) return;
  imageTrigger = imageControl;
  byId('dialog-title').textContent = item.title;
  byId('dialog-image').alt = item.title;
  byId('image-dimensions').textContent = '';
  byId('dialog-image').onload = () => { byId('image-dimensions').textContent = ` · ${byId('dialog-image').naturalWidth} × ${byId('dialog-image').naturalHeight} px`; };
  byId('dialog-image').src = item.href;
  byId('original-link').href = item.href;
  byId('image-dialog').showModal();
  byId('dialog-close').focus();
 }
 const copyControl = event.target.closest('[data-copy]');
 if (copyControl) {
  try {
   // 本地文件打开时可能没有 Clipboard API，保留传统复制作为后备。
   let copied = false;
   if (navigator.clipboard?.writeText) {
    try { await navigator.clipboard.writeText(copyControl.dataset.copy); copied = true; } catch { /* 再尝试本地文件兼容路径。 */ }
   }
   if (!copied) {
    const helper = document.createElement('textarea'); helper.value = copyControl.dataset.copy;
    helper.style.position = 'fixed'; helper.style.opacity = '0'; document.body.append(helper); helper.select();
    copied = document.execCommand('copy'); helper.remove(); copyControl.focus();
    if (!copied) throw new Error('copy unavailable');
   }
   const original = copyControl.textContent; copyControl.textContent = '已复制';
   byId('copy-status').textContent = '已复制：' + copyControl.dataset.copy;
   setTimeout(() => { copyControl.textContent = original; }, 1600);
  } catch { byId('copy-status').textContent = '浏览器未允许自动复制，请选中上方路径手动复制。'; }
 }
});
byId('dialog-close').addEventListener('click', () => byId('image-dialog').close());
byId('image-dialog').addEventListener('close', () => imageTrigger?.focus());
</script>
</body></html>'''

OUT.mkdir(parents=True, exist_ok=True)
# 转义 '<'，避免资源说明中的字符串意外结束内嵌 JSON 标签。
embedded = json.dumps(catalog, ensure_ascii=False).replace("<", "\\u003c")
(OUT / "index.html").write_text(HTML.replace("__CATALOG_JSON__", embedded), encoding="utf-8")
(OUT / "catalog-manifest.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"catalog": str(OUT / "index.html"), "skins": len(assets),
                  "components": len(catalog["components"]), "previews": len(catalog["previews"]),
                  "archive_verified": True}, ensure_ascii=False))
