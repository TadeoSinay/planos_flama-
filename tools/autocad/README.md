# DXF → DWG en AutoCAD

Los planos se generan como DXF R2018 (capas, tipos de línea, estilo de cotas FLAMA-IRAM, letra ISO3098 = isocpeur.ttf
y una presentación por lámina con su configuración de página). En la nube no hay AutoCAD ni convertidor ODA, así que
el DWG se saca en la PC:

1. Cerrar todos los dibujos y dejar uno nuevo vacío (el script usa SDI = 1).
2. Desde la raíz del repo: `python tools/autocad/armar_scr.py` (o `armar_scr.ps1` en PowerShell). Crea
   `salida/dxf_a_dwg.scr` con rutas absolutas y borra los DWG viejos.
3. En AutoCAD: `SCRIPT` → `salida/dxf_a_dwg.scr`. Por cada DXF: abre, `AUDIT` (corrige), `-PURGE` (dos pasadas) y
   `SAVEAS 2018` al lado del DXF. Al final vuelve SDI, FILEDIA y CMDDIA a 1 / 0 / 1.
4. Revisar uno por presentación (Hoja1… Hoja4) y subir los DWG al repo.

Alternativa sin AutoCAD: ODA File Converter (gratuito) — carpeta de entrada `salida`, salida `salida`, «ACAD2018 DWG»,
«Recurse folder» y «Audit each file».
