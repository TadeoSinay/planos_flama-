@echo off
rem ==========================================================================
rem  FLAMA S.A. - Abre en AutoCAD 2027 todas las laminas DXF de ..\salida y
rem  las guarda como DWG (formato 2018) junto a cada DXF.
rem  Ruta de AutoCAD: editar ACAD si su instalacion es distinta.
rem ==========================================================================
setlocal EnableDelayedExpansion
set "ACAD=C:\Program Files\Autodesk\AutoCAD 2027\acad.exe"
set "RAIZ=%~dp0..\salida"
set "SCR=%TEMP%\flama_dxf_a_dwg.scr"

> "%SCR%" echo SDI 1
>> "%SCR%" echo FILEDIA 0
>> "%SCR%" echo CMDDIA 0
for /r "%RAIZ%" %%F in (*_H?.dxf) do (
  >> "%SCR%" echo _OPEN "%%~fF"
  >> "%SCR%" echo _ZOOM _E
  >> "%SCR%" echo _SAVEAS 2018 "%%~dpnF.dwg"
)
>> "%SCR%" echo FILEDIA 1
>> "%SCR%" echo CMDDIA 1
>> "%SCR%" echo SDI 0

"%ACAD%" /product ACAD /language "es-ES" /b "%SCR%"
endlocal
