@echo off
rem ==========================================================================
rem  FLAMA S.A. - Abre en AutoCAD 2027 los 17 planos FL_MAT_*.dxf de ..\salida
rem  (3 laminas por archivo) y los guarda como DWG 2018 junto a cada DXF.
rem  Ruta de AutoCAD: editar ACAD si su instalacion es distinta.
rem ==========================================================================
setlocal EnableDelayedExpansion
set "ACAD=C:\Program Files\Autodesk\AutoCAD 2027\acad.exe"
set "RAIZ=%~dp0..\salida"
set "SCR=%TEMP%\flama_dxf_a_dwg.scr"

> "%SCR%" echo SDI 1
>> "%SCR%" echo FILEDIA 0
>> "%SCR%" echo CMDDIA 0
for /r "%RAIZ%" %%F in (FL_MAT_*.dxf) do (
  set "N=%%~nF"
  if /i not "!N:~-3!"=="_3D" (
    >> "%SCR%" echo _OPEN "%%~fF"
    >> "%SCR%" echo _ZOOM _E
    >> "%SCR%" echo _SAVEAS 2018 "%%~dpnF.dwg"
  )
)
>> "%SCR%" echo FILEDIA 1
>> "%SCR%" echo CMDDIA 1
>> "%SCR%" echo SDI 0

"%ACAD%" /product ACAD /language "es-ES" /b "%SCR%"
endlocal
