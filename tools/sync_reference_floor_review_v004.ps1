# 新材质独立复用工程，从已校验v003 ZIP引入公共构造，不包含原工程autoload。
param([string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot))
$reviewRoot = Join-Path $WorkspaceRoot 'art-source\ember\reference-floor-v004\godot-review'
if (-not (Test-Path -LiteralPath (Join-Path $reviewRoot 'project.godot'))) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory((Join-Path $WorkspaceRoot 'art-source\ember\deliveries\reference_floor_v003_2026-10-06.zip'),$reviewRoot)
    $projectPath = Join-Path $reviewRoot 'project.godot'
    $projectText = Get-Content -LiteralPath $projectPath -Raw
    # 工厂尚未创建v004场景时，以已存在的v003场景作为导入入口，避免缺失主场景报错。
    $projectText = $projectText.Replace('Ember Floor Materials v003','Ember Floor Materials v004')
    Set-Content -LiteralPath $projectPath -Value $projectText -Encoding utf8
}
$groups = @('assets\ember\environment\reference_floor_v004','art-source\ember\reference-floor-v004')
foreach ($group in $groups) {
    $sourceDirectory = Join-Path $WorkspaceRoot $group
    $targetDirectory = Join-Path $reviewRoot $group
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceDirectory -File | Where-Object { $_.Extension -notin @('.import','.log') } | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $targetDirectory $_.Name) -Force }
}
foreach ($group in @('scripts\ember','scenes\ember','tools')) {
    $targetDirectory = Join-Path $reviewRoot $group
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $WorkspaceRoot $group) -File | Where-Object { $_.Name -like '*reference_floor*v004*' -and $_.Extension -in @('.gd','.uid','.tscn') } | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $targetDirectory $_.Name) -Force }
}
# 共享编译器新增可选材质参数；默认路径仍保留原steel输出。
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot 'scripts\ember\reference_floor_compiler_v002.gd') -Destination (Join-Path $reviewRoot 'scripts\ember\reference_floor_compiler_v002.gd') -Force
$standardPath = Join-Path $WorkspaceRoot 'docs\shader-learning\reference-floor-v004-materials.md'
if (Test-Path -LiteralPath $standardPath) { Copy-Item -LiteralPath $standardPath -Destination (Join-Path $reviewRoot 'docs\shader-learning\reference-floor-v004-materials.md') -Force }
# 顶层使用说明与启动器来自本轮模板；新建review时也得到v004入口，而非旧包的v003入口。
foreach ($entry in @(
    @{source='standalone_README_v004.md';target='README.md'},
    @{source='run_showcase_v004.ps1';target='run_showcase.ps1'},
    @{source='run_validation_v004.ps1';target='run_validation.ps1'}
)) {
    $entryPath=Join-Path $WorkspaceRoot ('art-source\ember\reference-floor-v004\'+$entry.source)
    if (Test-Path -LiteralPath $entryPath) { Copy-Item -LiteralPath $entryPath -Destination (Join-Path $reviewRoot $entry.target) -Force }
}
# 独立包不包含自身ZIP，说明链接只在工作区使用；包内入口为project.godot。
$readmePath=Join-Path $reviewRoot 'assets\ember\environment\reference_floor_v004\README.md'
if (Test-Path -LiteralPath $readmePath) {
    $readmeText=Get-Content -LiteralPath $readmePath -Raw
    $readmeText=$readmeText.Replace('工作区完整交付：[独立工程ZIP](../../../../art-source/ember/deliveries/reference_floor_v004_2026-10-06.zip)。','这里是完整独立工程包。')
    Set-Content -LiteralPath $readmePath -Value $readmeText -Encoding utf8
}
# 创建场景之后再切换默认入口；不触碰主工程project.godot。
if (Test-Path -LiteralPath (Join-Path $reviewRoot 'scenes\ember\reference_floor_sandbox_v004.tscn')) {
    $projectPath = Join-Path $reviewRoot 'project.godot'
    $projectText = Get-Content -LiteralPath $projectPath -Raw
    $projectText = $projectText.Replace('reference_floor_sandbox_v003.tscn','reference_floor_sandbox_v004.tscn')
    Set-Content -LiteralPath $projectPath -Value $projectText -Encoding utf8
}
Write-Output "V004_REVIEW_READY: $reviewRoot"

