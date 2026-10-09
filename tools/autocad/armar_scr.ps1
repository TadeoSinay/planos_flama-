# Igual que armar_scr.py, sin Python: ejecutar desde la raíz del repo en PowerShell
#   powershell -ExecutionPolicy Bypass -File tools\autocad\armar_scr.ps1
$salida = Join-Path (Get-Location) "salida"
$lineas = @("_.SDI 1", "_.FILEDIA 0", "_.CMDDIA 0", "_.PROXYNOTICE 0")
Get-ChildItem -Path $salida -Recurse -Filter *.dxf | Where-Object { $_.Name -notlike "*_3D.dxf" } | Sort-Object FullName | ForEach-Object {
    $dwg = [System.IO.Path]::ChangeExtension($_.FullName, ".dwg")
    if (Test-Path $dwg) { Remove-Item $dwg }
    $lineas += "_.OPEN `"$($_.FullName)`""
    $lineas += "_.AUDIT _Y"
    $lineas += "_.-PURGE _A * _N"
    $lineas += "_.-PURGE _A * _N"
    if ($_.Name -like "FL_MAT_*") { $lineas += "_.-LAYOUT _S Hoja1_Conjunto" }
    $lineas += "_.SAVEAS 2018 `"$dwg`""
}
$lineas += @("_.FILEDIA 1", "_.CMDDIA 1", "_.SDI 0", "")
$scr = Join-Path $salida "dxf_a_dwg.scr"
[System.IO.File]::WriteAllLines($scr, $lineas, (New-Object System.Text.UTF8Encoding($true)))
Write-Host "Listo: $scr"
