Add-Type -AssemblyName System.Drawing

$assetDirectory = Join-Path $PSScriptRoot "..\assets\shader-learning\common"
$assetDirectory = [System.IO.Path]::GetFullPath($assetDirectory)
[System.IO.Directory]::CreateDirectory($assetDirectory) | Out-Null

# 只生成 01.1 当前观察实验需要的 UV Grid；后续资源等首次使用时再添加。
$size = 512
$bitmap = [System.Drawing.Bitmap]::new($size, $size)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
$graphics.Clear([System.Drawing.Color]::FromArgb(255, 28, 32, 44))

try {
    $minorPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 68, 82, 104), 1)
    $majorPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 130, 154, 184), 2)
    $centerPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 255, 190, 70), 3)
    $font = [System.Drawing.Font]::new("Arial", 14, [System.Drawing.FontStyle]::Bold)
    $textBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)

    for ($coordinate = 0; $coordinate -le $size; $coordinate += 32) {
        $pen = if (($coordinate % 128) -eq 0) { $majorPen } else { $minorPen }
        $graphics.DrawLine($pen, $coordinate, 0, $coordinate, $size)
        $graphics.DrawLine($pen, 0, $coordinate, $size, $coordinate)
    }

    $graphics.DrawLine($centerPen, $size / 2, 0, $size / 2, $size)
    $graphics.DrawLine($centerPen, 0, $size / 2, $size, $size / 2)
    $graphics.DrawString("UV (0,0)", $font, $textBrush, 10, 10)
    $graphics.DrawString("U ->", $font, $textBrush, $size - 55, 10)
    $graphics.DrawString("V", $font, $textBrush, 10, $size - 48)
    $graphics.DrawString("|", $font, $textBrush, 14, $size - 34)
    $graphics.DrawString("v", $font, $textBrush, 13, $size - 20)

    $outputPath = Join-Path $assetDirectory "uv_grid_512.png"
    $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output "Generated: $outputPath"
}
finally {
    $minorPen.Dispose()
    $majorPen.Dispose()
    $centerPen.Dispose()
    $font.Dispose()
    $textBrush.Dispose()
    $graphics.Dispose()
    $bitmap.Dispose()
}

# 01.2 使用：色块用于比较 RGB 原色在灰度转换后的明暗差异。
$colorTest = [System.Drawing.Bitmap]::new($size, $size)
$colorGraphics = [System.Drawing.Graphics]::FromImage($colorTest)
$colorGraphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None

try {
    $colors = @(
        [System.Drawing.Color]::FromArgb(255, 255, 0, 0),
        [System.Drawing.Color]::FromArgb(255, 0, 255, 0),
        [System.Drawing.Color]::FromArgb(255, 0, 0, 255),
        [System.Drawing.Color]::FromArgb(255, 255, 255, 0),
        [System.Drawing.Color]::FromArgb(255, 0, 255, 255),
        [System.Drawing.Color]::FromArgb(255, 255, 0, 255),
        [System.Drawing.Color]::FromArgb(255, 255, 255, 255),
        [System.Drawing.Color]::FromArgb(255, 32, 32, 32)
    )

    for ($index = 0; $index -lt $colors.Count; $index++) {
        $column = $index % 4
        $row = [Math]::Floor($index / 4)
        $brush = [System.Drawing.SolidBrush]::new($colors[$index])
        try {
            $colorGraphics.FillRectangle($brush, $column * 128, $row * 256, 128, 256)
        }
        finally {
            $brush.Dispose()
        }
    }

    # 中央灰阶带提供黑到白的连续参考。
    for ($x = 0; $x -lt $size; $x++) {
        $gray = [Math]::Round(255 * $x / ($size - 1))
        $pen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, $gray, $gray, $gray))
        try {
            $colorGraphics.DrawLine($pen, $x, 224, $x, 287)
        }
        finally {
            $pen.Dispose()
        }
    }

    $colorOutputPath = Join-Path $assetDirectory "color_test_512.png"
    $colorTest.Save($colorOutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output "Generated: $colorOutputPath"
}
finally {
    $colorGraphics.Dispose()
    $colorTest.Dispose()
}
