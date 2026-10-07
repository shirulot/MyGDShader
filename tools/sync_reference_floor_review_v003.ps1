# 新材质独立复用工程，从已校验v002 ZIP引入公共构造，不包含原工程autoload。
param([string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot))
$reviewRoot = Join-Path $WorkspaceRoot 'art-source\ember\reference-floor-v003\godot-review'
if (-not (Test-Path -LiteralPath (Join-Path $reviewRoot 'project.godot'))) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory((Join-Path $WorkspaceRoot 'art-source\ember\deliveries\reference_floor_v002_2026-10-06.zip'),$reviewRoot)
    $projectPath = Join-Path $reviewRoot 'project.godot'
    $projectText = Get-Content -LiteralPath $projectPath -Raw
    $projectText = $projectText.Replace('Ember Reference Floor v002','Ember Floor Materials v003').Replace('reference_floor_sandbox_v002.tscn','reference_floor_sandbox_v003.tscn')
    Set-Content -LiteralPath $projectPath -Value $projectText -Encoding utf8
}
$groups = @('assets\ember\environment\reference_floor_v003','art-source\ember\reference-floor-v003')
foreach ($group in $groups) {
    $sourceDirectory = Join-Path $WorkspaceRoot $group
    $targetDirectory = Join-Path $reviewRoot $group
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceDirectory -File | Where-Object { $_.Extension -notin @('.import','.log') } | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $targetDirectory $_.Name) -Force }
}
foreach ($group in @('scripts\ember','scenes\ember','tools')) {
    $targetDirectory = Join-Path $reviewRoot $group
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $WorkspaceRoot $group) -File | Where-Object { $_.Name -like '*reference_floor*v003*' -and $_.Extension -in @('.gd','.uid','.tscn') } | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $targetDirectory $_.Name) -Force }
}
# 共享编译器新增可选材质参数；默认路径仍保留原steel输出。
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot 'scripts\ember\reference_floor_compiler_v002.gd') -Destination (Join-Path $reviewRoot 'scripts\ember\reference_floor_compiler_v002.gd') -Force
$standardPath = Join-Path $WorkspaceRoot 'docs\shader-learning\reference-floor-v003-materials.md'
if (Test-Path -LiteralPath $standardPath) { Copy-Item -LiteralPath $standardPath -Destination (Join-Path $reviewRoot 'docs\shader-learning\reference-floor-v003-materials.md') -Force }
# 独立包不包含自身ZIP，说明链接只在工作区使用；包内入口为project.godot。
$readmePath=Join-Path $reviewRoot 'assets\ember\environment\reference_floor_v003\README.md'
if (Test-Path -LiteralPath $readmePath) {
    $readmeText=Get-Content -LiteralPath $readmePath -Raw
    $readmeText=$readmeText.Replace('完整工作区交付：[独立工程ZIP](../../../../art-source/ember/deliveries/reference_floor_v003_2026-10-06.zip)。','这里是完整独立工程包。')
    Set-Content -LiteralPath $readmePath -Value $readmeText -Encoding utf8
}
Write-Output "V003_REVIEW_READY: $reviewRoot"
