"""TA 独立完整 ZIP 冷解压与静态导出；只在新隔离副本重建。"""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
import hashlib, json, subprocess, time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
FIXED = ROOT / 'art-source/ember/enemy-patrol-profile-calibration-v021-c002-review-v003'
ZIP = ROOT / 'art-source/ember/deliveries/enemy_patrol_profile_calibration_v021_c002_v003_2026-10-07.zip'
P = OUT / 'technical-cold-load'
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(ZIP.read_bytes()) == '87d0ecf437c93451eddcdad59387f6f03191efcdfdfa1cb197b6e41e819f4ab2'
assert ZIP.stat().st_size == 44513 and not P.exists()
with ZipFile(ZIP) as z:
    names = [n for n in z.namelist() if not n.endswith('/')]
    manifest = json.loads(z.read('manifest.json'))
    files = manifest['files']
    assert len(files) == 21 and set(names) == set(files) | {'manifest.json'}
    assert manifest['new_clips'] == 0
    rows = []
    for name in names:
        parts = PurePosixPath(name)
        assert not parts.is_absolute() and '..' not in parts.parts and ':' not in name
        data = z.read(name)
        assert data == (FIXED / name).read_bytes()
        if name in files:
            assert sha(data) == files[name]['sha256'] and len(data) == files[name]['bytes']
        dst = P.joinpath(*parts.parts)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        rows.append({'file': name, 'sha256': sha(data), 'bytes': len(data), 'fixed_equal': True})
assert not (P / '.godot').exists()
binding = {'status': 'PASS', 'zip_sha256': sha(ZIP.read_bytes()), 'bytes': ZIP.stat().st_size,
           'payload': len(files), 'manifest_sha256': sha((P / 'manifest.json').read_bytes()), 'rows': rows}
(OUT / 'technical-zip-binding.json').write_text(json.dumps(binding, indent=2), encoding='utf-8')

engine = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
commands = [('import', ['--headless', '--path', str(P), '--editor', '--import', '--quit']),
            ('export', ['--path', str(P), '--position', '-32000,-32000', '--resolution', '256x256',
                        '--rendering-method', 'gl_compatibility', '--script', 'res://export.gd'])]
calls = []
for name, args in commands:
    stdout, stderr = OUT / f'technical-cold-{name}.stdout.log', OUT / f'technical-cold-{name}.stderr.log'
    start = time.monotonic()
    # Keep the temporary export window hidden/offscreen, while retaining real GPU rendering.
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    with stdout.open('wb') as o, stderr.open('wb') as e:
        proc = subprocess.run([engine, *args], stdout=o, stderr=e, timeout=50,
                              creationflags=subprocess.CREATE_NO_WINDOW, startupinfo=startup)
    calls.append({'call': name, 'exit_code': proc.returncode, 'seconds': round(time.monotonic()-start, 3),
                  'stderr_bytes': stderr.stat().st_size, 'args': args})
    if proc.returncode:
        (OUT / 'technical-cold-failed.json').write_text(json.dumps(calls, indent=2), encoding='utf-8')
        raise RuntimeError(stderr.read_text(encoding='utf-8', errors='replace'))
changes = [name for name, record in files.items() if sha((P/name).read_bytes()) != record['sha256']]
fixed_changes = [name for name, record in files.items() if sha((FIXED/name).read_bytes()) != record['sha256']]
receipt = {'status': 'PASS' if not changes and not fixed_changes else 'FAIL', 'zip_sha256': binding['zip_sha256'],
           'scope': 'Two static neutral PNG, six actual part PNG, one contact sheet reconstructed by cold Godot GPU export; no action matrix.',
           'fresh_cache_absent_before_import': True, 'original_payload_files': 21, 'reconstructed_png': 9,
           'payload_changes_after_export': changes, 'fixed_payload_changes': fixed_changes, 'calls': calls}
(OUT / 'technical-cold-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=False))
assert receipt['status'] == 'PASS'
