# Oficina unificada para Codex y OpenCode

Este repositorio define una sola oficina de **31 perfiles conceptuales**: Dirección, cinco coordinadores y veinticinco especialistas. Convoca únicamente los departamentos necesarios y conserva un responsable por archivo compartido.

La fuente canónica es [`office/registry.json`](office/registry.json): fija identificadores, jerarquía, departamentos, prompts, permisos, skills y capacidades. Los prompts viven en `office/roles/`, los contratos en `office/contracts/` y las políticas en `office/permission-sets/` y `office/capabilities.json`.

`scripts/Build-Office.ps1` genera ambas plataformas desde esa fuente:

| Plataforma | Dirección | Perfiles subordinados |
|---|---|---|
| Codex | El chat principal recibe el bloque administrado de `AGENTS.md`. | 30 subagentes TOML en `.codex/agents/`: cinco coordinadores y veinticinco especialistas. |
| OpenCode | `directora` es el agente primario. | 30 subagentes Markdown en `.opencode/agents/`; 31 archivos contando `directora`. |

Los archivos generados llevan una cabecera con su origen. Edita `office/` y regenera; las verificaciones detectan cambios manuales en las salidas. La plantilla del bloque de Dirección es `templates/AGENTS-oficina.md`; el generador conserva las instrucciones de `AGENTS.md` fuera de sus marcadores.

## Usar la oficina en este repositorio

Abre esta carpeta en Codex o OpenCode. En Codex, el chat principal ejerce la Dirección: los perfiles subordinados son subagentes, no chats independientes. En OpenCode, selecciona `directora` en una sesión nueva; `opencode debug agents` permite inspeccionar los perfiles que reconoce tu instalación.

La ruta de trabajo es **Dirección → coordinador → especialista**. OpenCode configura `experimental.subagent_depth = 2`. Ningún perfil fija un modelo o proveedor; hereda la selección de la sesión. En Codex, los subagentes también heredan los permisos efectivos del entorno: sus instrucciones no crean un sandbox separado.

La [guía de departamentos y delegación](docs/guia-departamentos-y-delegacion.md) detalla las rutas, entregables y ejemplos de encargo.

## Generar y verificar

Necesitas PowerShell 7 o posterior. Desde la raíz del kit:

```powershell
pwsh -NoProfile -File scripts/Build-Office.ps1 -Platform Both
pwsh -NoProfile -File scripts/Build-Office.ps1 -Platform Both -Check
pwsh -NoProfile -File scripts/Test-Office.Core.ps1
```

`-Platform` acepta `Codex`, `OpenCode` o `Both`. `-Check` detecta deriva sin escribir archivos. La suite Core valida registro, contratos, prompts, generación determinista, conservación de instrucciones y compatibilidad de los comandos antiguos. Puedes ejecutar una sección: `Registry`, `Contracts`, `Roles`, `OpenCode`, `Codex` o `Compatibility` mediante `-Section`.

Se conservan dos entrypoints con aviso de deprecación:

| Comando heredado | Equivalente canónico |
|---|---|
| `scripts/Test-Equipo.ps1` | `scripts/Test-Office.Core.ps1`; admite `-Section` y ejecuta todo por defecto. |
| `scripts/Build-Codex-Agents.ps1` | `scripts/Build-Office.ps1 -Platform Codex`; admite `-Check`. |

El generador heredado conserva su invocación sin argumentos y su alcance Codex. Ahora produce los treinta subagentes y el bloque de Dirección desde `office/`; ya no consume `codex/roles/`.

## Departamentos

| Coordinador | Especialistas |
|---|---|
| `coord-producto-experiencia` | `producto`, `diseno-web`, `ux-accesibilidad`, `seo-growth`, `data-analytics` |
| `coord-ingenieria-datos` | `arquitectura`, `frontend`, `backend`, `mobile`, `datos-ia`, `integraciones` |
| `coord-calidad-seguridad` | `qa`, `seguridad`, `auditoria`, `rendimiento` |
| `coord-operaciones-entrega` | `devops`, `sre-observabilidad`, `forensics`, `release`, `documentacion` |
| `coord-negocio-gobernanza` | `marketing`, `social-contenido`, `finanzas`, `legal`, `experiencia-cliente` |

`diseno-web` concentra dirección de arte, movimiento e imágenes y utiliza `taste-skill` como autoridad visual. `frontend` usa `frontend-developer` para arquitectura de cliente. El registro declara las skills requeridas; la generación Core no las instala ni confirma conexiones externas. Si falta una capacidad o skill necesaria, el agente debe declararlo y proponer una alternativa verificable.

## Instalación en otros proyectos

El Core genera y verifica la oficina local. La migración e instalación segura global o por proyecto pertenece al plan posterior: respaldo, inventario exacto, conflictos y restauración requieren su propia validación.

`scripts/Install-Equipo.ps1`, `codex/roles/` y `templates/AGENTS-equipo.md` son recursos heredados pendientes de esa migración. El instalador conserva el contrato anterior y actualmente rechaza el inventario unificado; no es el procedimiento para instalar esta oficina. No elimines perfiles a mano por patrón ni uses las guías históricas como garantía de instalación actual.

## Encargos para empezar

- “Directora, analiza este proyecto sin cambiar archivos. Pide a Ingeniería y Datos una revisión de arquitectura y a Calidad y Seguridad los riesgos principales. Reúne evidencia y límites.”
- “Directora, agrega validación al formulario. Revisa las convenciones, encarga la implementación a Ingeniería y Datos y la revisión a Calidad y Seguridad. No publiques.”
- “Directora, prepara primero un plan para la pantalla y su endpoint. Acordemos el contrato y los criterios de aceptación antes de implementar.”

Cada entrega debe distinguir cambios, verificaciones reales, riesgos y pendientes. Publicar, desplegar, usar credenciales o cambiar servicios externos requiere autorización explícita para esa acción.
