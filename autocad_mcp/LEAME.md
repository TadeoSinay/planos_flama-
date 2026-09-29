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

## Herramientas (22)

| Grupo | Herramientas |
|---|---|
| Estado y archivos | `autocad_status`, `autocad_open_drawing`, `autocad_new_drawing`, `autocad_save_as`, `autocad_plot_pdf` |
| Consulta (solo lectura) | `autocad_list_layers`, `autocad_list_entities` (filtros + paginación), `autocad_mass_properties` |
| Dibujo 2D | `autocad_add_line`, `autocad_add_circle`, `autocad_add_text` |
| Sólidos 3D | `autocad_add_box`, `autocad_add_cylinder`, `autocad_add_revolved_solid` (perfil r-z girado sobre Z), `autocad_boolean`, `autocad_delete_entity` |
| Vista y comandos | `autocad_set_view`, `autocad_run_command` |
| Flujo FLAMA | `autocad_list_flama_models`, `autocad_open_flama_sheet`, `autocad_convert_flama_to_dwg`, `autocad_open_flama_3d` |

Cada herramienta declara si es de solo lectura o destructiva (anotaciones MCP),
valida sus parámetros y, si algo falla, devuelve el error con la acción sugerida.

`evaluacion.xml` tiene 10 preguntas de verificación con respuesta conocida para
comprobar que el MCP funciona de punta a punta con tu AutoCAD.

Después le podés pedir a Claude, por ejemplo: *"abrí el plano del ABC 10 kg en AutoCAD"*.

## Notas

- AutoCAD puede estar abierto o cerrado; si está cerrado lo inicia.
- `autocad_run_command` ejecuta comandos arbitrarios en AutoCAD: Claude Code te pedirá permiso
  en cada uso salvo que lo autorices.
- No fue probado contra un AutoCAD real desde el entorno donde se escribió; si una
  herramienta falla, el mensaje de error aparece en la respuesta.
