param([switch]$Fresh)
$ErrorActionPreference = 'Stop'
$rootDir = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$enginePath = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
$stageFile = Join-Path $PSScriptRoot 'godot-stage-exits.json'
$stageReport = Get-Content -LiteralPath $stageFile -Raw | ConvertFrom-Json
$builderPath = 'res://tools/build_ember_robot_animation_v002.gd'

function Invoke-GodotStage([string]$Name, [string[]]$EngineArgs) {
    $stdoutPath = Join-Path $PSScriptRoot ($Name + '.stdout.log')
    $stderrPath = Join-Path $PSScriptRoot ($Name + '.stderr.log')
    # Start-Process 在 Windows 上接收一条命令行，逐个引用已知参数中的路径空格。
    $quotedArgs = ($EngineArgs | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' }) -join ' '
    $process = Start-Process -FilePath $enginePath -ArgumentList $quotedArgs -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $entry = [ordered]@{
        stage = $Name; engine_arguments = $EngineArgs; exit_code = $process.ExitCode
        stderr_bytes = (Get-Item -LiteralPath $stderrPath).Length
        stdout_log = ($Name + '.stdout.log'); stderr_log = ($Name + '.stderr.log')
        stdout_sha256 = (Get-FileHash -LiteralPath $stdoutPath -Algorithm SHA256).Hash.ToLower()
        stderr_sha256 = (Get-FileHash -LiteralPath $stderrPath -Algorithm SHA256).Hash.ToLower()
    }
    $stageReport.stages = @($stageReport.stages | Where-Object { $_.stage -ne $Name }) + @($entry)
    $stageReport.builder_sha256 = (Get-FileHash -LiteralPath (Join-Path $rootDir 'tools/build_ember_robot_animation_v002.gd') -Algorithm SHA256).Hash.ToLower()
    $stageReport | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $stageFile -Encoding utf8
    Write-Output "$Name : exit=$($entry.exit_code) stderr=$($entry.stderr_bytes)"
    if ($entry.exit_code -ne 0 -or $entry.stderr_bytes -ne 0) {
        Get-Content -LiteralPath $stderrPath
        Get-Content -LiteralPath $stdoutPath -Tail 25
        throw "Godot stage failed: $Name"
    }
}

if (-not $Fresh) {
    Invoke-GodotStage 'import' @('--headless', '--editor', '--path', $rootDir, '--import')
    $robotDir = Join-Path $rootDir 'assets/ember/characters/robot'
    foreach ($pngPath in Get-ChildItem -LiteralPath $robotDir -Filter '*_v002.png') {
        $importPath = $pngPath.FullName + '.import'
        $config = Get-Content -LiteralPath $importPath -Raw
        $values = [ordered]@{
            'compress/mode'='0'; 'compress/normal_map'='2'; 'roughness/mode'='1'
            'mipmaps/generate'='false'; 'process/fix_alpha_border'='false'
            'process/premult_alpha'='false'; 'process/normal_map_invert_y'='false'
            'detect_3d/compress_to'='0'
        }
        foreach ($key in $values.Keys) {
            $pattern = '(?m)^' + [regex]::Escape($key) + '=.*$'
            if ([regex]::Matches($config, $pattern).Count -ne 1) { throw "Missing import key: $importPath $key" }
            $config = [regex]::Replace($config, $pattern, ($key + '=' + $values[$key]))
        }
        [System.IO.File]::WriteAllText($importPath, $config, [System.Text.UTF8Encoding]::new($false))
    }
    Invoke-GodotStage 'import-settings' @('--headless', '--editor', '--path', $rootDir, '--import')
    Invoke-GodotStage 'build' @('--headless', '--path', $rootDir, '-s', $builderPath)
    Invoke-GodotStage 'verify' @('--headless', '--path', $rootDir, '-s', $builderPath, '--', '--verify-only', ('--report=' + (Join-Path $PSScriptRoot 'godot-verify-only.json')))
    Invoke-GodotStage 'render' @('--path', $rootDir, '--rendering-method', 'gl_compatibility', '--disable-vsync', '-s', $builderPath, '--', '--verify-only', ('--report=' + (Join-Path $PSScriptRoot 'godot-render.json')), ('--screenshots=' + (Join-Path $PSScriptRoot 'render')), ('--screenshot=' + (Join-Path $PSScriptRoot 'godot-robot-v002.png')))
} else {
    # 新工程只带复用所需资产/构建器/场景，无原项目缓存与 autoload。
    $freshDir = Join-Path $PSScriptRoot 'fresh-project-v001'
    if (Test-Path -LiteralPath $freshDir) { throw 'Fresh directory already exists; preserve it and choose a new audit run.' }
    New-Item -ItemType Directory -Path (Join-Path $freshDir 'assets/ember/characters'), (Join-Path $freshDir 'tools'), (Join-Path $freshDir 'scenes/ember') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $rootDir 'assets/ember/characters/robot') -Destination (Join-Path $freshDir 'assets/ember/characters') -Recurse
    Copy-Item -LiteralPath (Join-Path $rootDir 'tools/build_ember_robot_animation_v002.gd'), (Join-Path $rootDir 'tools/build_ember_robot_animation_v002.gd.uid') -Destination (Join-Path $freshDir 'tools')
    Copy-Item -LiteralPath (Join-Path $rootDir 'scenes/ember/robot_animation_sandbox_v002.tscn') -Destination (Join-Path $freshDir 'scenes/ember')
    $projectText = @'
config_version=5
[application]
config/name="Ember Robot v002 Reuse Check"
run/main_scene="res://scenes/ember/robot_animation_sandbox_v002.tscn"
[display]
window/size/viewport_width=1280
window/size/viewport_height=800
[rendering]
renderer/rendering_method="gl_compatibility"
textures/default_filters/use_nearest_mipmap_filter=false
textures/canvas_textures/default_texture_filter=0
'@
    [System.IO.File]::WriteAllText((Join-Path $freshDir 'project.godot'), $projectText, [System.Text.UTF8Encoding]::new($false))
    $copyHashes = [ordered]@{}
    foreach ($file in Get-ChildItem -LiteralPath $freshDir -Recurse -File) {
        $key = $file.FullName.Substring($freshDir.Length + 1).Replace('\', '/')
        $copyHashes[$key] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()
    }
    [ordered]@{cache_absent_before_import = -not (Test-Path -LiteralPath (Join-Path $freshDir '.godot')); autoload_absent = -not ($projectText -match '\[autoload\]'); sha256=$copyHashes} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'fresh-copy-before.json') -Encoding utf8
    Invoke-GodotStage 'fresh-import' @('--headless', '--editor', '--path', $freshDir, '--import')
    Invoke-GodotStage 'fresh-verify' @('--headless', '--path', $freshDir, '-s', $builderPath, '--', '--verify-only', ('--report=' + (Join-Path $PSScriptRoot 'fresh-godot-verify.json')))
    Invoke-GodotStage 'fresh-render' @('--path', $freshDir, '--rendering-method', 'gl_compatibility', '--disable-vsync', '-s', $builderPath, '--', '--verify-only', ('--report=' + (Join-Path $PSScriptRoot 'fresh-godot-render.json')), ('--screenshots=' + (Join-Path $PSScriptRoot 'fresh-render')), ('--screenshot=' + (Join-Path $PSScriptRoot 'fresh-godot-robot-v002.png')))
}
