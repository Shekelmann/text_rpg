param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][ValidateSet('wolf','leshy','likho')][string]$EnemyId
)
Add-Type -AssemblyName System.Drawing
$sizes = @{wolf=120; leshy=108; likho=96}
$offsets = @{wolf=10; leshy=8; likho=12}
$palettes = @{
    wolf = @('101412','242727','363b40','4c535b','656e77','858b8b','a5a496','c4bda7','29251f','40362a','594532','73573c','3d412b','5d6040','8d7953','b08c58')
    leshy = @('101412','25291e','3b4228','586136','798044','9b9d62','30302b','575348','807866','aaa18b','c7bea4','33251c','503421','735034','987044','a53c2e')
    likho = @('101412','212629','30383d','414a50','555f66','70797b','919891','b2b6a7','d0ceba','25221f','37302a','4d4032','69533d','82694d','373c35','53594c')
}
$palette = $palettes[$EnemyId] | ForEach-Object { [System.Drawing.ColorTranslator]::FromHtml('#'+$_) }
$source = [System.Drawing.Bitmap]::new($SourcePath)
$small = [System.Drawing.Bitmap]::new(128,128)
$size = $sizes[$EnemyId]
$left = (128-$size)/2
$top = $offsets[$EnemyId]
$used = [System.Collections.Generic.HashSet[int]]::new()
for ($y=0; $y -lt 128; $y++) {
    for ($x=0; $x -lt 128; $x++) {
        $best=$palette[0]
        if ($x -ge $left -and $x -lt ($left+$size) -and $y -ge $top -and $y -lt ($top+$size)) {
            $c=$source.GetPixel([int][Math]::Floor(($x-$left+0.5)*$source.Width/$size),[int][Math]::Floor(($y-$top+0.5)*$source.Height/$size))
            $distance=[double]::PositiveInfinity
            if ($c.A -ge 128) {
                foreach ($p in $palette) {
                    $d=2*[Math]::Pow(($c.R-$p.R),2)+3*[Math]::Pow(($c.G-$p.G),2)+[Math]::Pow(($c.B-$p.B),2)
                    if ($d -lt $distance) {$distance=$d; $best=$p}
                }
            }
        }
        $small.SetPixel($x,$y,$best)
        [void]$used.Add($best.ToArgb())
    }
}
$small.Save((Join-Path $PSScriptRoot "$EnemyId-128.png"),[System.Drawing.Imaging.ImageFormat]::Png)
Write-Output "$EnemyId : 128x128, $($used.Count) colors"
$source.Dispose()
$small.Dispose()
