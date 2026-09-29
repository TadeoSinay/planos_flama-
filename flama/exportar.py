"""Exportación: DXF (láminas con layout de impresión), PDF, STEP y DXF 3D."""

import ezdxf
import cadquery as cq
from ezdxf.addons.drawing import Frontend, RenderContext, layout, config
from ezdxf.addons.drawing import pymupdf as pmb
from ezdxf.render import MeshVertexMerger

from .lamina import FORMATOS

PAGE_NAMES = {"A3": "ISO_full_bleed_A3_(420.00_x_297.00_MM)",
              "A2": "ISO_full_bleed_A2_(594.00_x_420.00_MM)",
              "A1": "ISO_full_bleed_A1_(841.00_x_594.00_MM)"}


def preparar_layouts(doc, hojas):
    """Una presentación por lámina (ventana 1:1 sobre su zona del espacio modelo),
    con configuración de página ISO full bleed y 'DWG To PDF.pc3'.
    hojas: [(nombre, formato, ox)]"""
    for nombre, fmt, ox in hojas:
        W, H = FORMATOS[fmt]
        psp = doc.layouts.new(nombre)
        psp.page_setup(size=(W, H), margins=(0, 0, 0, 0), units="mm", offset=(0, 0), rotation=0,
                       scale=1, name=PAGE_NAMES[fmt], device="DWG To PDF.pc3")
        vp = psp.add_viewport(center=(W / 2, H / 2), size=(W, H), view_center_point=(ox + W / 2, H / 2),
                              view_height=H)
        vp.dxf.status = 2
    if "Layout1" in doc.layouts.names():
        doc.layouts.delete("Layout1")
    doc.layouts.set_active_layout(hojas[0][0])


def _config(color=False):
    return config.Configuration(
        background_policy=config.BackgroundPolicy.WHITE,
        color_policy=config.ColorPolicy.COLOR if color else config.ColorPolicy.BLACK,
        lineweight_policy=config.LineweightPolicy.ABSOLUTE,
        min_lineweight=0.18,
    )


def pdf_hojas(doc, hojas, color=False):
    """PDF de varias páginas, una por lámina, a tamaño real.
    color=True conserva los colores (señalética); si no, todo en negro."""
    import pymupdf
    out = pymupdf.open()
    colores = {}
    if color:  # sólo los rellenos con color verdadero: capas en negro (ACI 7)
        for l in doc.layers:
            colores[l.dxf.name] = l.dxf.color
            l.dxf.color = 7
    ctx = RenderContext(doc)
    for nombre, fmt, ox in hojas:
        W, H = FORMATOS[fmt]
        back = pmb.PyMuPdfBackend()
        Frontend(ctx, back, config=_config(color)).draw_layout(doc.layouts.get(nombre), finalize=True)
        page = layout.Page(W, H, layout.Units.mm, margins=layout.Margins.all(0))
        data = back.get_pdf_bytes(page, settings=layout.Settings(fit_page=False, scale=1.0))
        out.insert_pdf(pymupdf.open("pdf", data))
    for n, c in colores.items():
        doc.layers.get(n).dxf.color = c
    return out


def dxf_a_png(doc, ruta, fmt, dpi=110):
    back, page, st = _render(doc, fmt)
    with open(ruta, "wb") as fh:
        fh.write(back.get_pixmap_bytes(page, fmt="png", dpi=dpi, settings=st))


def step(piezas, ruta):
    asm = cq.Assembly(name="conjunto")
    for k, v in piezas.items():
        asm.add(v, name=k)
    asm.export(ruta, "STEP")


def dxf_3d(piezas, ruta, tol=0.5, ang=0.35):
    """Modelo 3D en DXF: una entidad MESH por pieza (capa por pieza).
    En AutoCAD: CONVTOSOLID convierte cada malla en 3DSOLID. El sólido exacto
    (superficies B-rep) se entrega en STEP."""
    doc = ezdxf.new("R2018", units=4)
    msp = doc.modelspace()
    for i, (k, v) in enumerate(piezas.items()):
        capa = "3D-" + k.upper()
        doc.layers.add(capa, color=(i % 9) + 1)
        verts, tris = v.tessellate(tol, ang)
        mb = MeshVertexMerger(precision=4)  # malla cerrada (vértices soldados)
        mb.add_mesh(vertices=[(p.x, p.y, p.z) for p in verts], faces=[tuple(t) for t in tris])
        mb.render_mesh(msp, dxfattribs={"layer": capa})
    doc.header["$INSUNITS"] = 4
    doc.saveas(ruta)
