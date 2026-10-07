param(
    [string]$Godot = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe',
    [switch]$Verify
)
# 从资源包同步独立示例。共享地板和机器人按原路径复制，建筑资源按新路径复制。
# 仅同步白名单；示例位于 examples/.gdignore 下，避免主工程重复导入示例副本。
$ErrorActionPreference = 'Stop'
$pack = Split-Path -Parent $PSScriptRoot
$repo = (Resolve-Path -LiteralPath (Join-Path $pack '../../..')).ProviderPath
$packageRelative = 'assets/ember/buildings_final'
$demo = Join-Path $pack 'examples/standalone'
$files = [Collections.Generic.List[string]]::new()
foreach ($folder in @("$packageRelative/textures", "$packageRelative/scenes")) {
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $repo $folder) -Recurse -File) {
        if ($file.Extension -in @('.png', '.json', '.tscn')) {
            $files.Add([IO.Path]::GetRelativePath($repo, $file.FullName))
        }
    }
}
foreach ($path in @(
    "$packageRelative/scripts/building_asset.gd", "$packageRelative/scripts/building_demo.gd", "$packageRelative/scripts/building_demo_actor.gd",
    "$packageRelative/shaders/building_intact.gdshader",
    'assets/ember/map_assets_v001/floors/floor_steel_period_v001.png',
    'assets/ember/characters/robot/robot_idle_down_v001.png',
    "$packageRelative/tools/build_building_coverage_v004r1.gd", "$packageRelative/tools/export_building_parts_v004r1.gd", "$packageRelative/tools/validate_capture_buildings_v004r1.gd",
    "$packageRelative/source/building-assets-v004/registration_baseline_v004.json"
)) { $files.Add($path) }
foreach ($id in @('control_tower', 'repair_workshop', 'logistics_warehouse')) {
    $files.Add("$packageRelative/source/building-assets-v004/masters/${id}_intact_v004.png")
    $files.Add("$packageRelative/source/selected-buildings-v001/references/${id}_user_selected.png")
}
# 保留脚本 UID，避免每次同步在示例中生成不同身份。
foreach ($relative in @($files.ToArray())) {
    if (Test-Path -LiteralPath (Join-Path $repo ($relative + '.uid'))) { $files.Add($relative + '.uid') }
}
foreach ($relative in $files) {
    $destination = Join-Path $demo $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $repo $relative) -Destination $destination -Force
}
$manifest = foreach ($relative in $files) {
    $path = Join-Path $demo $relative
    [ordered]@{ path = $relative.Replace('\', '/'); sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
}
# 保留复制时来源哈希；运行验证会重新生成截图和报告，须与来源快照区分。
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $demo 'SOURCE_SYNC_MANIFEST.json') -Encoding utf8
if ($Verify) {
    $logs = Join-Path $pack 'verification'
    New-Item -ItemType Directory -Path $logs -Force | Out-Null
    $import = Start-Process -FilePath $Godot -ArgumentList @('--headless', '--path', $demo, '--editor', '--import', '--quit') -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $logs 'import.log') -RedirectStandardError (Join-Path $logs 'import.err')
    if ($import.ExitCode -ne 0 -or (Get-Item -LiteralPath (Join-Path $logs 'import.err')).Length -ne 0) { throw '独立示例导入失败，请检查 verification/import.err。' }
    $run = Start-Process -FilePath $Godot -ArgumentList @('--path', $demo, '--resolution', '1408x800', '--position', '-2400,-1400', '--script', "res://$packageRelative/tools/validate_capture_buildings_v004r1.gd") -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $logs 'validation.log') -RedirectStandardError (Join-Path $logs 'validation.err')
    $result = Get-Content -LiteralPath (Join-Path $demo "$packageRelative/textures/previews/validation_v004r1.json") -Raw | ConvertFrom-Json
    if ($run.ExitCode -ne 0 -or $result.passed -ne $result.total -or (Get-Item -LiteralPath (Join-Path $logs 'validation.err')).Length -ne 0) { throw '实际运行验证失败，请检查 verification 及示例内结果。' }
    Copy-Item -LiteralPath (Join-Path $demo "$packageRelative/textures/previews/validation_v004r1.json") -Destination (Join-Path $logs 'validation.json') -Force
    Write-Output "BUILDINGS_FINAL: $($result.passed)/$($result.total), import/runtime stderr empty"
}
# 最终清单绑定示例当前实际文件，包含本轮重新生成的验证证据。
$manifest = foreach ($relative in $files) {
    $path = Join-Path $demo $relative
    [ordered]@{ path = $relative.Replace('\', '/'); sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $demo 'SYNC_MANIFEST.json') -Encoding utf8
Write-Output "Demo: $demo/project.godot"
