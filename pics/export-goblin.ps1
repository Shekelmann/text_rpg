Add-Type -AssemblyName System.Drawing
$sourcePath = 'C:\Users\Алексей\.codex\generated_images\01a08230-d1e2-74d1-9c56-2b7f947b67ec\exec-2bfa90c4-ea1f-4be4-bc13-38f5d5836d9c.png'
$source = [System.Drawing.Bitmap]::new($sourcePath)
$palette = @('101412','20251c','343824','4c5030','686a3c','85834c','a29b64','bdb581','2b2620','433528','5d4733','795d42','343738','565956','8b8b7e','ba3028') | ForEach-Object { [System.Drawing.ColorTranslator]::FromHtml('#' + $_) }
$small = [System.Drawing.Bitmap]::new(128,128)
$used = [System.Collections.Generic.HashSet[int]]::new()
for ($y=0; $y -lt 128; $y++) {
    for ($x=0; $x -lt 128; $x++) {
        $c = $source.GetPixel([int][Math]::Floor(($x+0.5)*$source.Width/128), [int][Math]::Floor(($y+0.5)*$source.Height/128))
        $best = $palette[0]
        $distance = [double]::PositiveInfinity
        if ($c.A -ge 128) {
            foreach ($p in $palette) {
                $d = 2*[Math]::Pow(($c.R-$p.R),2)+3*[Math]::Pow(($c.G-$p.G),2)+[Math]::Pow(($c.B-$p.B),2)
                if ($d -lt $distance) { $distance=$d; $best=$p }
            }
        }
        $small.SetPixel($x,$y,$best)
        [void]$used.Add($best.ToArgb())
    }
}
$small.Save((Join-Path $PSScriptRoot 'goblin-level-1-128.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$preview = [System.Drawing.Bitmap]::new(768,768)
for ($y=0; $y -lt 768; $y++) {
    for ($x=0; $x -lt 768; $x++) {
        $preview.SetPixel($x,$y,$small.GetPixel([int][Math]::Floor($x/6),[int][Math]::Floor($y/6)))
    }
}
$preview.Save((Join-Path $PSScriptRoot 'goblin-level-1-preview-6x.png'),[System.Drawing.Imaging.ImageFormat]::Png)
Write-Output "Exported 128x128; colors: $($used.Count); preview: 768x768 exact 6x pixel replication."
$source.Dispose()
$small.Dispose()
$preview.Dispose()
