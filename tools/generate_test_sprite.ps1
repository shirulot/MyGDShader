# Chapter 01 的透明轮廓测试图。无外部美术素材，无需安装额外依赖。
# 运行：powershell -File tools/generate_test_sprite.ps1
Add-Type -AssemblyName System.Drawing

$assetDirectory = [System.IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot '..\assets\shader-learning\2d')
)
[System.IO.Directory]::CreateDirectory($assetDirectory) | Out-Null
$outputPath = Join-Path $assetDirectory 'test_sprite_robot_512.png'

$bitmap = [System.Drawing.Bitmap]::new(512, 512, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$brushes = @()

try {
    # 真正透明的背景；棋盘格不能画进 PNG，否则无法验证 Alpha。
    $graphics.Clear([System.Drawing.Color]::FromArgb(0, 0, 0, 0))
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias

    $outline = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 28, 45, 68))
    $body = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 42, 194, 202))
    $accent = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 255, 185, 62))
    $white = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 244, 250, 255))
    $brushes = @($outline, $body, $accent, $white)

    # 简单机器人由几何图形组成，不规则外轮廓便于发现矩形底。
    $graphics.FillRectangle($outline, 244, 66, 24, 66)
    $graphics.FillEllipse($outline, 224, 30, 64, 64)
    $graphics.FillEllipse($accent, 234, 40, 44, 44)
    $graphics.FillRectangle($outline, 160, 380, 56, 76)
    $graphics.FillRectangle($outline, 296, 380, 56, 76)
    $graphics.FillEllipse($accent, 66, 244, 72, 98)
    $graphics.FillEllipse($accent, 374, 244, 72, 98)

    $graphics.FillEllipse($outline, 104, 112, 304, 304)
    $graphics.FillEllipse($body, 116, 124, 280, 280)
    $graphics.FillEllipse($outline, 144, 190, 224, 128)
    $graphics.FillEllipse($white, 184, 224, 34, 44)
    $graphics.FillEllipse($white, 294, 224, 34, 44)
    $graphics.FillEllipse($accent, 238, 342, 36, 36)

    $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output "Generated: $outputPath (512x512 RGBA)"
}
finally {
    foreach ($brush in $brushes) { $brush.Dispose() }
    $graphics.Dispose()
    $bitmap.Dispose()
}
