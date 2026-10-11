param([int]$x, [int]$y, [int]$w, [int]$h, [string]$path)
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$bitmap = New-Object System.Drawing.Bitmap $w, $h
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($x, $y, 0, 0, $bitmap.Size)
$bitmap.Save($path)
$graphics.Dispose()
$bitmap.Dispose()
