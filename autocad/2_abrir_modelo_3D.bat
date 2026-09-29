@echo off
rem ==========================================================================
rem  FLAMA S.A. - Abre el modelo 3D de un extintor en AutoCAD 2027.
rem  Uso:  2_abrir_modelo_3D.bat FL-ABC-004
rem  Carga el DXF 3D (mallas por pieza), convierte las mallas en solidos
rem  (CONVTOSOLID), aplica estilo visual realista y guarda <codigo>_3D.dwg.
rem  El solido exacto (superficies B-rep) esta en <codigo>.step: comando IMPORT.
rem ==========================================================================
setlocal
if "%~1"=="" (echo Indique el codigo, p.ej. FL-ABC-004 & exit /b 1)
set "ACAD=C:\Program Files\Autodesk\AutoCAD 2027\acad.exe"
set "DIR=%~dp0..\salida\%~1"
set "SCR=%TEMP%\flama_3d.scr"
> "%SCR%" echo SDI 1
>> "%SCR%" echo FILEDIA 0
>> "%SCR%" echo _OPEN "%DIR%\%~1_3D.dxf"
>> "%SCR%" echo SMOOTHMESHCONVERT 2
>> "%SCR%" echo _CONVTOSOLID _ALL
>> "%SCR%" echo.
>> "%SCR%" echo _-VIEW _SWISO
>> "%SCR%" echo _VSCURRENT _R
>> "%SCR%" echo _ZOOM _E
>> "%SCR%" echo _SAVEAS 2018 "%DIR%\%~1_3D.dwg"
>> "%SCR%" echo FILEDIA 1
>> "%SCR%" echo SDI 0
"%ACAD%" /product ACAD /language "es-ES" /b "%SCR%"
endlocal
