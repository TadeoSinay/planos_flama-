"""Servidor MCP local para controlar AutoCAD (Windows) desde Claude Code.

Usa la API COM/ActiveX de AutoCAD (AutoCAD.Application), la misma que usan
las macros VBA. Debe ejecutarse en la misma PC donde está instalado AutoCAD.

Registro en Claude Code (una vez, desde la carpeta del repo):
    claude mcp add autocad -- python autocad_mcp\\server.py
"""

import os
import time

import pythoncom
import win32com.client
from mcp.server.fastmcp import FastMCP

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(REPO, "salida")

mcp = FastMCP("autocad")


def _acad():
    """Conecta con AutoCAD abierto, o lo inicia si no está corriendo."""
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("AutoCAD.Application")
    except Exception:
        app = win32com.client.Dispatch("AutoCAD.Application")
        time.sleep(5)
    app.Visible = True
    return app


def _esperar(app, seg=120):
    """Espera a que AutoCAD termine el comando en curso."""
    t0 = time.time()
    while time.time() - t0 < seg:
        try:
            if app.GetAcadState().IsQuiescent:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def _doc(app):
    if app.Documents.Count == 0:
        app.Documents.Add()
    return app.ActiveDocument


@mcp.tool()
def estado() -> str:
    """Versión de AutoCAD, dibujo activo y dibujos abiertos."""
    app = _acad()
    docs = [app.Documents.Item(i).FullName or app.Documents.Item(i).Name for i in range(app.Documents.Count)]
    act = app.ActiveDocument.FullName if app.Documents.Count else "-"
    return f"AutoCAD {app.Version}\nActivo: {act}\nAbiertos: {docs}"


@mcp.tool()
def abrir(ruta: str) -> str:
    """Abre un DWG/DXF. Acepta ruta absoluta o relativa al repo
    (p. ej. 'salida/FL-ABC-004/FL-ABC-004_H1.dxf')."""
    app = _acad()
    p = ruta if os.path.isabs(ruta) else os.path.join(REPO, ruta)
    if not os.path.exists(p):
        return f"No existe: {p}"
    d = app.Documents.Open(p)
    _esperar(app)
    d.SendCommand("_ZOOM _E ")
    _esperar(app)
    return f"Abierto: {d.FullName}"


@mcp.tool()
def abrir_plano(codigo: str, hoja: int = 1) -> str:
    """Abre la lámina de un modelo FLAMA, p. ej. codigo='FL-ABC-004', hoja=1..3."""
    return abrir(os.path.join(SALIDA, codigo, f"{codigo}_H{hoja}.dxf"))


@mcp.tool()
def comando(texto: str) -> str:
    """Ejecuta un comando en la línea de comandos del dibujo activo.
    Usar nombres globales con '_' (funcionan en AutoCAD en español), por ejemplo
    '_ZOOM _E ' o '_LINE 0,0 100,0  '. Cada espacio equivale a ENTER."""
    app = _acad()
    d = _doc(app)
    if not texto.endswith(" ") and not texto.endswith("\n"):
        texto += " "
    d.SendCommand(texto)
    ok = _esperar(app)
    return "Comando ejecutado" if ok else "El comando sigue en curso (espera de datos)"


@mcp.tool()
def guardar_como(ruta: str, formato: str = "dwg2018") -> str:
    """Guarda el dibujo activo. formato: dwg2018 | dxf2018."""
    app = _acad()
    d = _doc(app)
    p = ruta if os.path.isabs(ruta) else os.path.join(REPO, ruta)
    tipos = {"dwg2018": 64, "dxf2018": 65}  # AcSaveAsType: ac2018_dwg / ac2018_dxf
    d.SaveAs(p, tipos.get(formato, 64))
    return f"Guardado: {p}"


@mcp.tool()
def convertir_todo_a_dwg() -> str:
    """Abre cada lámina DXF de salida/ y la guarda como DWG 2018 a su lado."""
    app = _acad()
    hechos = []
    for raiz, _, archivos in os.walk(SALIDA):
        for a in sorted(archivos):
            if a.endswith(".dxf") and "_H" in a:
                p = os.path.join(raiz, a)
                d = app.Documents.Open(p)
                _esperar(app)
                d.SaveAs(p[:-4] + ".dwg", 64)
                d.Close(False)
                hechos.append(a)
    return f"{len(hechos)} láminas guardadas como DWG"


@mcp.tool()
def importar_3d(codigo: str) -> str:
    """Abre el modelo 3D de un extintor (DXF con mallas), lo convierte en sólidos
    y lo muestra en isométrica con estilo realista."""
    app = _acad()
    p = os.path.join(SALIDA, codigo, f"{codigo}_3D.dxf")
    if not os.path.exists(p):
        return f"No existe: {p}"
    d = app.Documents.Open(p)
    _esperar(app)
    for c in ("SMOOTHMESHCONVERT 2 ", "_CONVTOSOLID _ALL  ", "_-VIEW _SWISO ", "_VSCURRENT _R ", "_ZOOM _E "):
        d.SendCommand(c)
        _esperar(app)
    return f"Modelo 3D abierto: {d.FullName}"


@mcp.tool()
def listar_capas() -> str:
    """Capas del dibujo activo con color y grosor de línea."""
    app = _acad()
    d = _doc(app)
    out = []
    for i in range(d.Layers.Count):
        l = d.Layers.Item(i)
        out.append(f"{l.Name}  color={l.Color}  grosor={l.Lineweight}")
    return "\n".join(out)


@mcp.tool()
def trazar_pdf(ruta_pdf: str) -> str:
    """Traza a PDF la presentación activa (Lamina_A3 / Lamina_A2) a escala 1:1."""
    app = _acad()
    d = _doc(app)
    for i in range(d.Layouts.Count):
        lay = d.Layouts.Item(i)
        if lay.Name.startswith("Lamina_"):
            d.ActiveLayout = lay
            break
    p = ruta_pdf if os.path.isabs(ruta_pdf) else os.path.join(REPO, ruta_pdf)
    d.SetVariable("BACKGROUNDPLOT", 0)
    ok = d.Plot.PlotToFile(p, "DWG To PDF.pc3")
    return f"PDF: {p}" if ok else "No se pudo trazar"


if __name__ == "__main__":
    mcp.run()
