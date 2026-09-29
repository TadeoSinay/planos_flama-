"""autocad_mcp - servidor MCP local (stdio) para controlar AutoCAD en Windows.

Usa la API COM/ActiveX oficial de AutoCAD ("AutoCAD.Application"). Debe
ejecutarse en la misma PC donde está instalado AutoCAD (probado con la API
documentada de AutoCAD 2027; también sirve para versiones recientes).

Registro en Claude Code (una vez, desde la carpeta del repo):
    claude mcp add autocad -- python autocad_mcp\\server.py
"""

from __future__ import annotations

import json
import math
import os
import time
from enum import Enum
from typing import Annotated, Optional

import pythoncom
import win32com.client
from mcp.server.fastmcp import FastMCP
from pydantic import Field

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(REPO, "salida")
CODIGO_RE = r"^FL-[A-Z0-9]+-\d{3}$"

mcp = FastMCP("autocad_mcp")

RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
ADD = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
DEST = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}


# --------------------------------------------------------------------- base
class AcadError(Exception):
    pass


def _acad():
    """Conecta con AutoCAD abierto o lo inicia."""
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject("AutoCAD.Application")
    except Exception:
        try:
            app = win32com.client.Dispatch("AutoCAD.Application")
        except Exception as e:
            raise AcadError("No se pudo iniciar AutoCAD por COM. Verificá que AutoCAD esté "
                            "instalado y que esta terminal corra con el mismo usuario de Windows.") from e
        time.sleep(5)
    app.Visible = True
    return app


def _esperar(app, seg: float = 120) -> bool:
    t0 = time.time()
    while time.time() - t0 < seg:
        try:
            if app.GetAcadState().IsQuiescent:
                return True
        except Exception:  # AutoCAD ocupado: reintentar
            pass
        time.sleep(0.3)
    return False


def _doc(app):
    if app.Documents.Count == 0:
        app.Documents.Add()
    return app.ActiveDocument


def _pt(x: float, y: float, z: float = 0.0):
    return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (float(x), float(y), float(z)))


def _ruta(ruta: str) -> str:
    return ruta if os.path.isabs(ruta) else os.path.join(REPO, ruta)


def _ok(**datos) -> str:
    return json.dumps(datos, ensure_ascii=False, indent=1)


def _err(e: Exception, sugerencia: str = "") -> str:
    msg = f"Error: {e}"
    if isinstance(e, pythoncom.com_error):
        msg = f"Error COM de AutoCAD: {e.args[1] if len(e.args) > 1 else e}"
        sugerencia = sugerencia or ("AutoCAD puede estar con un comando o diálogo abierto; "
                                    "presioná ESC en AutoCAD y reintentá.")
    return msg + (f" | Sugerencia: {sugerencia}" if sugerencia else "")


def _entidad(e) -> dict:
    d = {"handle": e.Handle, "tipo": e.ObjectName, "capa": e.Layer}
    try:
        mn, mx = e.GetBoundingBox()
        d["min"] = [round(v, 3) for v in mn]
        d["max"] = [round(v, 3) for v in mx]
    except Exception:
        pass
    return d


def _capa(doc, capa: Optional[str], ent):
    if capa:
        doc.Layers.Add(capa)
        ent.Layer = capa
    return ent


# --------------------------------------------------------------------- estado / archivos
@mcp.tool(name="autocad_status", annotations=RO)
def autocad_status() -> str:
    """Versión de AutoCAD, dibujo activo, dibujos abiertos y cantidad de entidades
    en el espacio modelo. Usar primero para comprobar la conexión."""
    try:
        app = _acad()
        docs = [app.Documents.Item(i).Name for i in range(app.Documents.Count)]
        act = app.ActiveDocument if app.Documents.Count else None
        return _ok(version=app.Version, activo=act.FullName or act.Name if act else None,
                   abiertos=docs, entidades_modelo=act.ModelSpace.Count if act else 0)
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_open_drawing", annotations=ADD)
def autocad_open_drawing(
    ruta: Annotated[str, Field(description="Ruta del DWG/DXF, absoluta o relativa al repo, "
                                           "p. ej. 'salida/FL-ABC-004/FL-ABC-004_H1.dxf'", min_length=3)],
) -> str:
    """Abre un DWG o DXF y hace zoom extensión."""
    p = _ruta(ruta)
    if not os.path.exists(p):
        return _err(FileNotFoundError(p), "Usá autocad_list_flama_models para ver los archivos disponibles.")
    try:
        app = _acad()
        d = app.Documents.Open(p)
        _esperar(app)
        app.ZoomExtents()
        return _ok(abierto=d.FullName, entidades_modelo=d.ModelSpace.Count)
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_new_drawing", annotations=ADD)
def autocad_new_drawing() -> str:
    """Crea un dibujo nuevo vacío (plantilla por defecto) y lo deja activo."""
    try:
        app = _acad()
        d = app.Documents.Add()
        return _ok(nuevo=d.Name)
    except Exception as e:
        return _err(e)


class Formato(str, Enum):
    dwg2018 = "dwg2018"
    dxf2018 = "dxf2018"


@mcp.tool(name="autocad_save_as", annotations=DEST)
def autocad_save_as(
    ruta: Annotated[str, Field(description="Ruta de destino (absoluta o relativa al repo). Sobrescribe si existe.")],
    formato: Annotated[Formato, Field(description="dwg2018 o dxf2018")] = Formato.dwg2018,
) -> str:
    """Guarda el dibujo activo con otro nombre/formato. Sobrescribe el archivo destino."""
    try:
        app = _acad()
        d = _doc(app)
        p = _ruta(ruta)
        d.SaveAs(p, 64 if formato == Formato.dwg2018 else 65)  # AcSaveAsType ac2018_dwg / ac2018_dxf
        return _ok(guardado=p)
    except Exception as e:
        return _err(e, "Comprobá que la carpeta exista y que el archivo no esté abierto en otro programa.")


@mcp.tool(name="autocad_plot_pdf", annotations=DEST)
def autocad_plot_pdf(
    ruta_pdf: Annotated[str, Field(description="Archivo PDF de salida (absoluto o relativo al repo)")],
    presentacion: Annotated[Optional[str], Field(description="Nombre de la presentación; por defecto "
                                                             "la primera que empiece con 'Lamina_'")] = None,
) -> str:
    """Traza a PDF una presentación del dibujo activo con su configuración de página
    (las láminas FLAMA ya traen 'DWG To PDF.pc3' a escala 1:1)."""
    try:
        app = _acad()
        d = _doc(app)
        objetivo = None
        for i in range(d.Layouts.Count):
            lay = d.Layouts.Item(i)
            if (presentacion and lay.Name == presentacion) or (not presentacion and lay.Name.startswith("Lamina_")):
                objetivo = lay
                break
        if objetivo is None:
            return _err(ValueError("presentación no encontrada"),
                        "Abrí primero una lámina FLAMA o indicá el nombre exacto de la presentación.")
        d.ActiveLayout = objetivo
        d.SetVariable("BACKGROUNDPLOT", 0)
        p = _ruta(ruta_pdf)
        ok = d.Plot.PlotToFile(p, "DWG To PDF.pc3")
        return _ok(pdf=p, presentacion=objetivo.Name, trazado=bool(ok))
    except Exception as e:
        return _err(e)


# --------------------------------------------------------------------- consulta
@mcp.tool(name="autocad_list_layers", annotations=RO)
def autocad_list_layers() -> str:
    """Capas del dibujo activo con color ACI, grosor (1/100 mm) y tipo de línea."""
    try:
        d = _doc(_acad())
        capas = [{"nombre": l.Name, "color": l.Color, "grosor": l.Lineweight, "tipo_linea": l.Linetype,
                  "activa": l.LayerOn} for l in (d.Layers.Item(i) for i in range(d.Layers.Count))]
        return _ok(total=len(capas), capas=capas)
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_list_entities", annotations=RO)
def autocad_list_entities(
    capa: Annotated[Optional[str], Field(description="Filtrar por capa (exacta)")] = None,
    tipo: Annotated[Optional[str], Field(description="Filtrar por ObjectName, p. ej. 'AcDbLine', "
                                                     "'AcDb3dSolid', 'AcDbRotatedDimension'")] = None,
    limit: Annotated[int, Field(ge=1, le=200, description="Máximo de resultados")] = 50,
    offset: Annotated[int, Field(ge=0, description="Resultados a saltear (paginación)")] = 0,
) -> str:
    """Lista entidades del espacio modelo (handle, tipo, capa y caja envolvente),
    con filtros y paginación."""
    try:
        ms = _doc(_acad()).ModelSpace
        sel = []
        for i in range(ms.Count):
            e = ms.Item(i)
            if (capa is None or e.Layer == capa) and (tipo is None or e.ObjectName == tipo):
                sel.append(e)
        pag = [_entidad(e) for e in sel[offset:offset + limit]]
        return _ok(total=len(sel), count=len(pag), offset=offset,
                   has_more=offset + len(pag) < len(sel), next_offset=offset + len(pag), entidades=pag)
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_mass_properties", annotations=RO)
def autocad_mass_properties(
    handle: Annotated[str, Field(description="Handle de un sólido 3D (de autocad_list_entities)")],
) -> str:
    """Volumen, centroide y caja envolvente de un sólido 3D."""
    try:
        e = _doc(_acad()).HandleToObject(handle)
        if e.ObjectName != "AcDb3dSolid":
            return _err(ValueError(f"{handle} es {e.ObjectName}"), "Indicá el handle de un AcDb3dSolid.")
        return _ok(handle=handle, volumen_mm3=round(e.Volume, 3),
                   centroide=[round(v, 3) for v in e.Centroid], **_entidad(e))
    except Exception as e:
        return _err(e)


# --------------------------------------------------------------------- dibujo 2D
@mcp.tool(name="autocad_add_line", annotations=ADD)
def autocad_add_line(
    x1: float, y1: float, x2: float, y2: float,
    capa: Annotated[Optional[str], Field(description="Capa (se crea si no existe)")] = None,
) -> str:
    """Agrega una línea en el espacio modelo (coordenadas en mm)."""
    try:
        d = _doc(_acad())
        e = _capa(d, capa, d.ModelSpace.AddLine(_pt(x1, y1), _pt(x2, y2)))
        return _ok(**_entidad(e))
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_add_circle", annotations=ADD)
def autocad_add_circle(
    cx: float, cy: float,
    radio: Annotated[float, Field(gt=0)],
    capa: Optional[str] = None,
) -> str:
    """Agrega una circunferencia (centro y radio en mm)."""
    try:
        d = _doc(_acad())
        e = _capa(d, capa, d.ModelSpace.AddCircle(_pt(cx, cy), radio))
        return _ok(**_entidad(e))
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_add_text", annotations=ADD)
def autocad_add_text(
    texto: Annotated[str, Field(min_length=1, max_length=500)],
    x: float, y: float,
    altura: Annotated[float, Field(gt=0, description="Altura en mm (ISO 3098: 2,5 / 3,5 / 5 / 7 / 10)")] = 3.5,
    capa: Optional[str] = None,
) -> str:
    """Agrega un texto de una línea."""
    try:
        d = _doc(_acad())
        e = _capa(d, capa, d.ModelSpace.AddText(texto, _pt(x, y), altura))
        return _ok(**_entidad(e))
    except Exception as e:
        return _err(e)


# --------------------------------------------------------------------- sólidos 3D
@mcp.tool(name="autocad_add_box", annotations=ADD)
def autocad_add_box(
    cx: float, cy: float, cz: float,
    largo: Annotated[float, Field(gt=0)], ancho: Annotated[float, Field(gt=0)], alto: Annotated[float, Field(gt=0)],
    capa: Optional[str] = None,
) -> str:
    """Sólido prisma rectangular centrado en (cx, cy, cz)."""
    try:
        d = _doc(_acad())
        e = _capa(d, capa, d.ModelSpace.AddBox(_pt(cx, cy, cz), largo, ancho, alto))
        return _ok(**_entidad(e))
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_add_cylinder", annotations=ADD)
def autocad_add_cylinder(
    cx: float, cy: float, cz: float,
    radio: Annotated[float, Field(gt=0)], alto: Annotated[float, Field(gt=0)],
    capa: Optional[str] = None,
) -> str:
    """Sólido cilindro de eje Z, centrado en (cx, cy, cz)."""
    try:
        d = _doc(_acad())
        e = _capa(d, capa, d.ModelSpace.AddCylinder(_pt(cx, cy, cz), radio, alto))
        return _ok(**_entidad(e))
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_add_revolved_solid", annotations=ADD)
def autocad_add_revolved_solid(
    perfil_rz: Annotated[list[list[float]], Field(
        min_length=3, description="Perfil cerrado [[r, z], ...] en mm (r >= 0), p. ej. la pared de un "
                                  "recipiente; se revoluciona 360° alrededor del eje Z")],
    capa: Optional[str] = None,
) -> str:
    """Crea un sólido de revolución (recipientes, cuellos, toberas) a partir de un
    perfil poligonal cerrado en el plano XZ, girado alrededor del eje Z."""
    try:
        d = _doc(_acad())
        ms = d.ModelSpace
        coords = []
        for r, z in perfil_rz:
            coords += [float(r), float(z)]
        # polilínea en XY (x=r, y=z) y giro de 90° sobre X: queda en el plano XZ
        pl = ms.AddLightWeightPolyline(win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, coords))
        pl.Closed = True
        pl.Rotate3D(_pt(0, 0, 0), _pt(1, 0, 0), math.pi / 2)
        regs = ms.AddRegion(win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [pl]))
        sol = ms.AddRevolvedSolid(regs[0], _pt(0, 0, 0), _pt(0, 0, 1), 2 * math.pi)
        regs[0].Delete()
        pl.Delete()
        return _ok(**_entidad(_capa(d, capa, sol)))
    except Exception as e:
        return _err(e, "El perfil debe ser cerrado, plano (y=0), sin autointersecciones y con r >= 0.")


class Booleana(str, Enum):
    union = "union"
    resta = "resta"
    interseccion = "interseccion"


@mcp.tool(name="autocad_boolean", annotations=DEST)
def autocad_boolean(
    handle_a: Annotated[str, Field(description="Sólido que se conserva y recibe el resultado")],
    handle_b: Annotated[str, Field(description="Sólido operando (se consume)")],
    operacion: Booleana,
) -> str:
    """Operación booleana entre dos sólidos 3D (B se elimina, A queda con el resultado)."""
    try:
        d = _doc(_acad())
        a, b = d.HandleToObject(handle_a), d.HandleToObject(handle_b)
        a.Boolean({"union": 0, "interseccion": 1, "resta": 2}[operacion.value], b)
        return _ok(**_entidad(a))
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_delete_entity", annotations=DEST)
def autocad_delete_entity(handle: Annotated[str, Field(description="Handle de la entidad a borrar")]) -> str:
    """Borra una entidad por handle."""
    try:
        d = _doc(_acad())
        e = d.HandleToObject(handle)
        tipo = e.ObjectName
        e.Delete()
        return _ok(borrado=handle, tipo=tipo)
    except Exception as e:
        return _err(e)


# --------------------------------------------------------------------- vista / comandos
class Vista(str, Enum):
    superior = "_TOP"
    anterior = "_FRONT"
    izquierda = "_LEFT"
    iso_so = "_SWISO"
    iso_se = "_SEISO"


@mcp.tool(name="autocad_set_view", annotations=RO)
def autocad_set_view(
    vista: Vista = Vista.iso_so,
    estilo: Annotated[str, Field(description="Estilo visual: _2dwireframe, _Hidden, _Realistic, _Conceptual")] = "_Realistic",
) -> str:
    """Cambia el punto de vista y el estilo visual del espacio modelo."""
    try:
        app = _acad()
        d = _doc(app)
        d.SendCommand(f"_-VIEW {vista.value} ")
        _esperar(app)
        d.SendCommand(f"_VSCURRENT {estilo} ")
        _esperar(app)
        app.ZoomExtents()
        return _ok(vista=vista.name, estilo=estilo)
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_run_command", annotations=DEST)
def autocad_run_command(
    texto: Annotated[str, Field(min_length=1, max_length=2000, description=
        "Secuencia para la línea de comandos. Usar nombres globales con '_' (funcionan en AutoCAD en "
        "español), p. ej. '_ZOOM _E'. Cada espacio equivale a ENTER.")],
) -> str:
    """Ejecuta una secuencia de comandos en el dibujo activo (acceso completo:
    puede modificar o borrar geometría). Preferir las herramientas específicas."""
    try:
        app = _acad()
        d = _doc(app)
        d.SendCommand(texto if texto.endswith((" ", "\n")) else texto + " ")
        ok = _esperar(app)
        return _ok(ejecutado=ok, nota=None if ok else "El comando sigue esperando datos; completalo o presioná ESC.")
    except Exception as e:
        return _err(e)


# --------------------------------------------------------------------- flujo FLAMA
@mcp.tool(name="autocad_list_flama_models", annotations=RO)
def autocad_list_flama_models() -> str:
    """Modelos FLAMA disponibles en salida/ con sus archivos (láminas, PDF, STEP, 3D)."""
    if not os.path.isdir(SALIDA):
        return _err(FileNotFoundError(SALIDA), "Generá los planos con 'python generar.py'.")
    res = {c: sorted(os.listdir(os.path.join(SALIDA, c))) for c in sorted(os.listdir(SALIDA))
           if os.path.isdir(os.path.join(SALIDA, c))}
    return _ok(total=len(res), modelos=res)


@mcp.tool(name="autocad_open_flama_sheet", annotations=ADD)
def autocad_open_flama_sheet(
    codigo: Annotated[str, Field(pattern=CODIGO_RE, description="Código FLAMA, p. ej. 'FL-ABC-004'")],
    hoja: Annotated[int, Field(ge=1, le=3, description="1 conjunto, 2 corte y detalles, 3 especificaciones")] = 1,
) -> str:
    """Abre una lámina FLAMA (DWG si ya fue convertida, si no el DXF)."""
    base = os.path.join(SALIDA, codigo, f"{codigo}_H{hoja}")
    p = base + ".dwg" if os.path.exists(base + ".dwg") else base + ".dxf"
    return autocad_open_drawing(p)


@mcp.tool(name="autocad_convert_flama_to_dwg", annotations=DEST)
def autocad_convert_flama_to_dwg(
    codigo: Annotated[Optional[str], Field(pattern=CODIGO_RE, description="Un modelo; vacío = todos")] = None,
) -> str:
    """Abre las láminas DXF de salida/ y las guarda como DWG 2018 junto a cada DXF."""
    try:
        app = _acad()
        hechos, errores = [], []
        for raiz, _, archivos in os.walk(SALIDA):
            for a in sorted(archivos):
                if not (a.endswith(".dxf") and "_H" in a) or (codigo and not a.startswith(codigo)):
                    continue
                p = os.path.join(raiz, a)
                try:
                    d = app.Documents.Open(p)
                    _esperar(app)
                    d.SaveAs(p[:-4] + ".dwg", 64)
                    d.Close(False)
                    hechos.append(a[:-4] + ".dwg")
                except Exception as e:
                    errores.append(f"{a}: {e}")
        return _ok(convertidos=len(hechos), errores=errores)
    except Exception as e:
        return _err(e)


@mcp.tool(name="autocad_open_flama_3d", annotations=ADD)
def autocad_open_flama_3d(
    codigo: Annotated[str, Field(pattern=CODIGO_RE, description="Código FLAMA, p. ej. 'FL-ABC-100'")],
    a_solidos: Annotated[bool, Field(description="Convertir mallas a sólidos 3D (CONVTOSOLID)")] = True,
) -> str:
    """Abre el modelo 3D de un extintor (DXF con una malla por pieza), opcionalmente lo
    convierte en sólidos y lo muestra en isométrica realista. Para el sólido exacto
    usar el comando IMPORTAR con el .step del modelo (se importa en segundo plano)."""
    p = os.path.join(SALIDA, codigo, f"{codigo}_3D.dxf")
    if not os.path.exists(p):
        return _err(FileNotFoundError(p), "Usá autocad_list_flama_models.")
    try:
        app = _acad()
        d = app.Documents.Open(p)
        _esperar(app)
        if a_solidos:
            d.SetVariable("SMOOTHMESHCONVERT", 2)  # facetado optimizado
            d.SendCommand("_CONVTOSOLID _ALL  ")
            _esperar(app, 600)
        d.SendCommand("_-VIEW _SWISO ")
        _esperar(app)
        d.SendCommand("_VSCURRENT _Realistic ")
        _esperar(app)
        app.ZoomExtents()
        solidos = sum(1 for i in range(d.ModelSpace.Count) if d.ModelSpace.Item(i).ObjectName == "AcDb3dSolid")
        return _ok(abierto=d.FullName, solidos=solidos, entidades=d.ModelSpace.Count)
    except Exception as e:
        return _err(e)


if __name__ == "__main__":
    mcp.run()
