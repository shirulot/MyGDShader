# 对最终 ZIP 做真正无缓存启动：新目录解压、SHA、导入、场景和只读工具检查。
# 日志和新报告位于独立目录外；不关闭或控制用户已打开的 Godot。
[CmdletBinding()]
param(
    [string]$GodotPath = 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe',
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ArchivePath = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskWorkspace = (Resolve-Path -LiteralPath $WorkspaceRoot).Path
if (-not (Test-Path -LiteralPath $GodotPath -PathType Leaf)) { throw 'Godot 可执行文件不存在。' }
if ([string]::IsNullOrWhiteSpace($ArchivePath)) { $ArchivePath = Join-Path $taskWorkspace 'art-source/ember/deliveries/robot_actions_v003_2026-10-06.zip' }
$taskArchive = (Resolve-Path -LiteralPath $ArchivePath).Path
$taskCold = Join-Path ([IO.Path]::GetTempPath()) ('CodexRobotActionsV003-Cold-' + [guid]::NewGuid().ToString('N'))
$taskLogs = Join-Path ([IO.Path]::GetTempPath()) ('CodexRobotActionsV003-Logs-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskLogs | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$taskZip = [IO.Compression.ZipFile]::OpenRead($taskArchive)
try {
    $seen = @{}
    foreach ($entry in $taskZip.Entries) {
        $name = $entry.FullName.Replace('\','/')
        if ($name -match '(^|/)\.\.(/|$)' -or $name -match '^[/:]' -or $name -match '(^|/)\.godot(/|$)' -or $seen.ContainsKey($name)) { throw "ZIP 含不安全路径、缓存或重复项：$name" }
        $seen[$name] = $true
    }
} finally { $taskZip.Dispose() }
[IO.Compression.ZipFile]::ExtractToDirectory($taskArchive,$taskCold)
if (Test-Path -LiteralPath (Join-Path $taskCold '.godot')) { throw 'ZIP 含预热缓存，不能证明冷启动。' }
$taskManifest = Get-Content -LiteralPath (Join-Path $taskCold 'file_hashes.json') -Raw | ConvertFrom-Json
function Assert-PackageHashes {
    foreach ($entry in $taskManifest.files) {
        $path = [IO.Path]::GetFullPath((Join-Path $taskCold ([string]$entry.path)))
        if (-not $path.StartsWith($taskCold + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw '清单路径越出解压目录。' }
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "ZIP 缺少文件：$($entry.path)" }
        if ((Get-Item -LiteralPath $path).Length -ne $entry.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw "ZIP SHA 或长度不一致：$($entry.path)" }
    }
}
Assert-PackageHashes
if ($seen.Count -ne @($taskManifest.files).Count + 1) { throw 'ZIP 包含清单外文件或缺少文件。' }
Write-Output ('ROBOT_COLD_HASH_PASS: ' + @($taskManifest.files).Count + ' files')
$taskProjectText = Get-Content -LiteralPath (Join-Path $taskCold 'project.godot') -Raw
if ($taskProjectText -match '(?m)^\[autoload\]' -or $taskProjectText -notmatch [regex]::Escape([string]$taskManifest.main_scene)) { throw '独立 project 入口或 autoload 不符合要求。' }
$taskRuns = @()
foreach ($stage in @('import','sandbox','verify')) {
    $arguments = @('--headless','--path',('"' + $taskCold + '"'))
    if ($stage -eq 'import') { $arguments += @('--editor', '--import') }
    elseif ($stage -eq 'sandbox') { $arguments += @(('res://' + $taskManifest.main_scene),'--quit-after','45') }
    else {
        $arguments += @('--script',$taskManifest.cold_verify.script,'--')
        foreach ($argument in $taskManifest.cold_verify.arguments) {
            $value = [string]$argument
            $value = $value.Replace('{REPORT_PATH}',(Join-Path $taskLogs 'runtime_report.json'))
            $arguments += ('"' + $value + '"')
        }
    }
    $stdout = Join-Path $taskLogs ($stage + '.stdout.log')
    $stderr = Join-Path $taskLogs ($stage + '.stderr.log')
    $start = Get-Date
    $process = Start-Process -FilePath $GodotPath -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if ($process.ExitCode -ne 0 -or (Select-String -LiteralPath $stderr -Pattern 'SCRIPT ERROR|ERROR:' -Quiet)) {
        Get-Content -LiteralPath $stderr
        throw "冷启动失败：$stage / exit=$($process.ExitCode)"
    }
    if ($stage -eq 'verify') {
        $marker = [string]$taskManifest.cold_verify.success_stdout
        if ([string]::IsNullOrWhiteSpace($marker) -or -not (Select-String -LiteralPath $stdout -Pattern ([regex]::Escape($marker)) -Quiet)) { throw '只读验证没有输出约定的 PASS 标记。' }
        $reportPath = Join-Path $taskLogs 'runtime_report.json'
        if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf)) { throw '只读验证缺少实际生成的报告。' }
        $runtime = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
        if ([string]$runtime.status -notin @($taskManifest.cold_verify.success_statuses)) { throw '只读验证报告没有通过。' }
    }
    $taskRuns += @{stage=$stage; exit_code=$process.ExitCode; elapsed_ms=[int]((Get-Date)-$start).TotalMilliseconds; stdout=$stdout; stderr=$stderr}
    Write-Output ('ROBOT_COLD_STAGE_PASS: ' + $stage)
}
# 只读工具运行后再次核对原件，防止导入或验证偷偷改写了交付源。
Assert-PackageHashes
$taskReport = @{status='PASS'; archive=$taskArchive; archive_sha256=(Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLowerInvariant(); extracted_root=$taskCold; logs_root=$taskLogs; verified_manifest_files=@($taskManifest.files).Count; zip_entries=$seen.Count; initially_no_godot_cache=$true; source_hashes_unchanged_after_verification=$true; frame_count=$taskManifest.frame_count; animation_count=$taskManifest.animation_count; runs=$taskRuns; runtime_report_sha256=(Get-FileHash -LiteralPath (Join-Path $taskLogs 'runtime_report.json') -Algorithm SHA256).Hash.ToLowerInvariant(); tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$taskReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskWorkspace 'art-source/ember/robot-actions-v003/package_cold_start_validation_v003.json') -Encoding utf8
Write-Output 'ROBOT_ACTIONS_COLD_START_PASS'
