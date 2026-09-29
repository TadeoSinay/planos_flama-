# MCP de AutoCAD (local, Windows)

Servidor MCP propio que deja a Claude Code controlar tu AutoCAD 2027 por la API
COM oficial. Corre en tu PC; no manda nada a internet.

## Instalación (una vez)

En una terminal dentro de la carpeta del repo:

```bat
pip install -r autocad_mcp\requirements.txt
claude mcp add autocad -- python autocad_mcp\server.py
```

Reiniciá Claude Code y comprobá con `/mcp` que aparece **autocad** conectado.

## Herramientas

| Herramienta | Qué hace |
|---|---|
| `estado` | Versión de AutoCAD y dibujos abiertos |
| `abrir_plano` | Abre una lámina FLAMA (`FL-ABC-004`, hoja 1–3) |
| `abrir` | Abre cualquier DWG/DXF |
| `comando` | Ejecuta un comando de AutoCAD (usar nombres con `_`, p. ej. `_ZOOM _E`) |
| `guardar_como` | Guarda el dibujo activo en DWG o DXF 2018 |
| `convertir_todo_a_dwg` | Pasa las 51 láminas DXF a DWG |
| `importar_3d` | Abre el 3D de un modelo, lo convierte a sólidos y lo muestra en isométrica |
| `listar_capas` | Capas del dibujo activo |
| `trazar_pdf` | Traza la presentación Lamina_A3/A2 a PDF |

Después le podés pedir a Claude, por ejemplo: *"abrí el plano del ABC 10 kg en AutoCAD"*.

## Notas

- AutoCAD puede estar abierto o cerrado; si está cerrado lo inicia.
- `comando` ejecuta comandos arbitrarios en AutoCAD: Claude Code te pedirá permiso
  en cada uso salvo que lo autorices.
- No fue probado contra un AutoCAD real desde el entorno donde se escribió; si una
  herramienta falla, el mensaje de error aparece en la respuesta.
