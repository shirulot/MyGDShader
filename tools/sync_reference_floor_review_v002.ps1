# 将已保存生产文件复制进无 autoload 的独立工程。不会复制 .godot 缓存。
param([string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot))
$reviewRoot = Join-Path $WorkspaceRoot 'art-source\ember\reference-floor-v002\godot-review'
$includedFiles = @(
    'assets\ember\environment\reference_floor_v002',
    'art-source\ember\reference-floor-v002\platform_modules_master_v001.png',
    'art-source\ember\reference-floor-v002\bridge_modules_master_v001.png',
    'art-source\ember\reference-floor-v002\corner_modules_master_v001.png',
    'art-source\ember\reference-floor-v002\details_modules_master_v001.png',
    'art-source\ember\reference-floor-v002\water_texture_master_v001.png',
    'art-source\ember\reference-floor-v002\platform_modules_master_v001.prompt.txt',
    'art-source\ember\reference-floor-v002\bridge_modules_master_v001.prompt.txt',
    'art-source\ember\reference-floor-v002\corner_modules_master_v001.prompt.txt',
    'art-source\ember\reference-floor-v002\details_modules_master_v001.prompt.txt',
    'art-source\ember\reference-floor-v002\water_texture_master_v001.prompt.txt',
    'art-source\ember\reference-floor-v002\generation_manifest_v002.json',
    'art-source\ember\pixel-standard-v002\previews\scene_preview_v001.png',
    'assets\ember\characters\robot\robot_idle_down_v001.png',
    'assets\ember\buildings\station\station_base_v001.png',
    'docs\shader-learning\autotile-neighborhoods-v002.json',
    'docs\shader-learning\reference-floor-v002-production.md',
    'tools\validate_reference_floor_v002.gd',
    'tools\build_reference_floor_v002.gd',
    'tools\build_reference_details_v002.gd'
)
foreach ($relativeFile in $includedFiles) {
    $sourcePath = Join-Path $WorkspaceRoot $relativeFile
    if (-not (Test-Path -LiteralPath $sourcePath)) { throw "Missing saved deliverable: $relativeFile" }
    $destinationPath = Join-Path $reviewRoot $relativeFile
    if ((Get-Item -LiteralPath $sourcePath).PSIsContainer) {
        New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
        # 缓存由独立 Godot 编辑器创建，交付时不包含 .import sidecars。
        Get-ChildItem -LiteralPath $sourcePath -File | Where-Object { $_.Extension -ne '.import' } | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $destinationPath $_.Name) -Force
        }
    } else {
        New-Item -ItemType Directory -Path (Split-Path -Parent $destinationPath) -Force | Out-Null
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
    }
}
foreach ($fileGroup in @('scripts\ember','scenes\ember','tools')) {
    $sourceDirectory = Join-Path $WorkspaceRoot $fileGroup
    $destinationDirectory = Join-Path $reviewRoot $fileGroup
    New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceDirectory -File | Where-Object {
        $_.Name -like '*reference_floor*v002*' -and $_.Extension -in @('.gd','.tscn','.uid')
    } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $destinationDirectory $_.Name) -Force
    }
}
# 独立工程无需包含自身ZIP；保留实际可用的使用说明与预览链接。
$standaloneReadmePath = Join-Path $reviewRoot 'assets\ember\environment\reference_floor_v002\README.md'
$standaloneReadme = Get-Content -LiteralPath $standaloneReadmePath -Raw
$standaloneReadme = $standaloneReadme.Replace('完整交付：[独立工程 ZIP](../../../../art-source/ember/deliveries/reference_floor_v002_2026-10-06.zip)。','这里是独立工程包。')
Set-Content -LiteralPath $standaloneReadmePath -Value $standaloneReadme -Encoding utf8
$standaloneStandardPath = Join-Path $reviewRoot 'docs\shader-learning\reference-floor-v002-production.md'
$standaloneStandard = Get-Content -LiteralPath $standaloneStandardPath -Raw
$standaloneStandard = $standaloneStandard.Replace('[完整独立工程 ZIP](../../art-source/ember/deliveries/reference_floor_v002_2026-10-06.zip)、','独立工程包内的')
Set-Content -LiteralPath $standaloneStandardPath -Value $standaloneStandard -Encoding utf8
Write-Output "Review project ready: $reviewRoot"
