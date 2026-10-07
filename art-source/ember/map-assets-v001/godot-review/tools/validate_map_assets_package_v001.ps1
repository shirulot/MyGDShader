# 从最终 ZIP 解压到新目录，核对逐文件 SHA，再验证无缓存导入和三张场景启动。
# 冷启动日志放在解压目录外；不修改交付 ZIP，不影响用户已打开的 Godot。
[CmdletBinding()]
param(
    [string]$GodotPath = 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe',
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ArchivePath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskWorkspace = (Resolve-Path -LiteralPath $WorkspaceRoot).Path
if ([string]::IsNullOrWhiteSpace($ArchivePath)) {
    $ArchivePath = Join-Path $taskWorkspace 'art-source/ember/deliveries/map_assets_v001_2026-10-06.zip'
}
$taskArchive = (Resolve-Path -LiteralPath $ArchivePath).Path
$taskSource = Join-Path $taskWorkspace 'art-source/ember/map-assets-v001'
$taskColdRoot = Join-Path $taskSource ('cold-start-' + (Get-Date -Format 'yyyyMMddTHHmmss'))
if (Test-Path -LiteralPath $taskColdRoot) { throw '冷启动目标已经存在，拒绝覆盖。' }
$taskLogs = Join-Path $taskSource 'cold-start-logs'
New-Item -ItemType Directory -Path $taskLogs -Force | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::ExtractToDirectory($taskArchive,$taskColdRoot)
if (Test-Path -LiteralPath (Join-Path $taskColdRoot '.godot')) { throw 'ZIP含预热缓存，不能证明冷启动。' }
$taskManifest = Get-Content -LiteralPath (Join-Path $taskColdRoot 'file_hashes.json') -Raw | ConvertFrom-Json
foreach ($taskEntry in $taskManifest.files) {
    $taskPath = Join-Path $taskColdRoot $taskEntry.path
    if (-not (Test-Path -LiteralPath $taskPath -PathType Leaf)) { throw ('ZIP解压缺文件：' + $taskEntry.path) }
    if ((Get-Item -LiteralPath $taskPath).Length -ne $taskEntry.bytes) { throw ('ZIP解压长度不一致：' + $taskEntry.path) }
    if ((Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw ('ZIP解压SHA不一致：' + $taskEntry.path) }
}
Write-Output ('COLD_PACKAGE_HASH_PASS: ' + $taskManifest.files.Count + ' files')
$taskRuns = @()
foreach ($taskStage in @('import','tidal_port','dry_mine','overgrown_lab')) {
    $taskArguments = @('--headless','--path',('"' + $taskColdRoot + '"'))
    if ($taskStage -eq 'import') { $taskArguments += '--import' }
    else { $taskArguments += @('res://scenes/ember/map_assets_' + $taskStage + '_v001.tscn','--quit-after','20') }
    $taskOut = Join-Path $taskLogs ($taskStage + '.stdout.log')
    $taskErr = Join-Path $taskLogs ($taskStage + '.stderr.log')
    $taskStart = Get-Date
    $taskProcess = Start-Process -FilePath $GodotPath -ArgumentList $taskArguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $taskOut -RedirectStandardError $taskErr
    $taskErrors = Select-String -LiteralPath $taskErr -Pattern 'SCRIPT ERROR|ERROR:'
    if ($taskProcess.ExitCode -ne 0 -or $taskErrors) {
        Get-Content -LiteralPath $taskErr
        throw ('冷启动失败：' + $taskStage + ' exit=' + $taskProcess.ExitCode)
    }
    $taskRuns += @{stage=$taskStage; exit_code=$taskProcess.ExitCode; elapsed_ms=[int]((Get-Date)-$taskStart).TotalMilliseconds; stdout=$taskOut; stderr=$taskErr}
    Write-Output ('COLD_STAGE_PASS: ' + $taskStage)
}
$taskReport = @{status='PASS'; archive=$taskArchive; archive_sha256=(Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLowerInvariant(); extracted_root=$taskColdRoot; verified_manifest_files=$taskManifest.files.Count; initially_no_godot_cache=$true; scenes_checked=3; runs=$taskRuns; tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$taskReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskSource 'cold_start_validation_v001.json') -Encoding utf8
Write-Output 'MAP_ASSETS_COLD_START_PASS'
