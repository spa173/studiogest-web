# Equipo de desarrollo asistido por IA

Este repositorio contiene una oficina de software reutilizable para trabajar con **Codex y OpenCode**. Codex o el agente principal de OpenCode coordina; los perfiles especialistas analizan o implementan partes concretas. El equipo comparte los archivos y las reglas del repositorio de trabajo.

## Contenido

- `.opencode/agents/`: una directora, ocho responsables de departamento y catorce especialistas en español.
- `AGENTS.md`: reglas comunes para Codex y otros agentes compatibles.
- `.codex/agents/`: 22 subagentes de proyecto que Codex puede invocar por nombre.
- `codex/roles/`: prompts fuente de esos subagentes, también copiables como referencia.
- `scripts/Install-Equipo.ps1`: instala el kit en otro repositorio sin borrar su configuración.
- `scripts/Build-Codex-Agents.ps1`: regenera los perfiles TOML de Codex cuando cambies los prompts fuente.
- `docs/`: diseño, plan de instalación y guía operativa.

La guía de [departamentos, especialistas y delegación](docs/guia-departamentos-y-delegacion.md) explica a quién encargar cada parte y cómo pedir primero un plan de trabajo.

Los perfiles no contienen claves, no eligen proveedor ni fijan modelo: OpenCode usa el modelo seleccionado en la sesión. Cada producto conserva su propio `AGENTS.md`, historial y cambios.

## Empezar aquí

### Usar el equipo en este repositorio

1. Abre esta carpeta en OpenCode. En una sesión nueva, selecciona **Directora** como agente principal. Si la sesión ya estaba abierta, crea una nueva o cambia el agente desde el selector.
2. Selecciona un modelo que ya te funcione en OpenCode.
3. Describe el resultado que quieres. La directora revisará las reglas, propondrá un plan breve cuando haga falta y decidirá qué especialista conviene consultar.
4. Revisa los cambios en Git antes de aceptarlos.

Para confirmar qué perfiles reconoce OpenCode, abre una terminal en esta carpeta y ejecuta `opencode debug agents`.

### Usarlo en otro proyecto

Desde PowerShell, instala el kit en la carpeta del proyecto:

```powershell
& "<ruta-a-este-kit>\scripts\Install-Equipo.ps1" -Target "<ruta-del-proyecto>"
```

Ejemplo:

```powershell
& "C:\Users\camilo\Documents\Codex\2026-11-13\como-creamos\outputs\equipo-agentes\scripts\Install-Equipo.ps1" -Target "C:\ruta\a\mi-proyecto"
```

Después, abre **la carpeta del proyecto** en OpenCode o Codex. En OpenCode usa `directora`. En Codex, el agente principal lee `AGENTS.md` y puede delegar por nombre a agentes como `desarrollo`, `diseno`, `legal` o `calidad`; las definiciones del proyecto se cargan desde `.codex/agents/` y sus prompts de referencia están en `.codex/roles/`.

El instalador:

- copia `.opencode/agents/` sin modificar perfiles con el mismo nombre; si hay conflicto, se detiene y pide `-Force` explícito;
- instala subagentes Codex en `.codex/agents/` y sus prompts en `.codex/roles/`, con la misma protección contra sobrescritura;
- crea `.opencode/opencode.jsonc` solo si no existe;
- añade el bloque de reglas de oficina a `AGENTS.md` sin duplicarlo y conserva el contenido existente.

Antes de usar `-Force`, revisa los archivos de agente que ya existan: serán reemplazados por las versiones del kit.

## Equipo

Los ocho departamentos son Desarrollo, Diseño, Diseño Web, Marketing, Social y Contenido, Finanzas, Operaciones y Legal. Cada uno cuenta con un perfil de coordinación. Se conectan con catorce especialistas: Producto, Arquitectura, UX Web, Frontend Web, Dirección de Arte, Movimiento, Imágenes, Backend, Calidad, Seguridad, Plataforma/DevOps, Datos e IA, Documentación y Experiencia del cliente. La directora general coordina las tareas que cruzan departamentos.

### Diseño Web: requiere la skill `taste-skill`

El departamento Diseño Web (`diseno-web` y sus especialistas) trabaja con la skill `taste-skill` (ver la [guía de Diseño Web](docs/guia-diseno-web.md)), que **no se incluye en este kit**: debes instalarla globalmente (o pedir a tu agente que la instale) copiando `taste-skill/` a tu carpeta global de skills, por ejemplo `~/.agents/skills/taste-skill/` (OpenCode) o `~/.claude/skills/taste-skill/` (Claude Code). Sin la skill, los perfiles web se detienen y lo declaran; no improvisan el sistema de diseño.

Si tu proyecto ya tenía instalada una versión anterior de este kit, el instalador **no borra** los archivos retirados: `.opencode/agents/ux-ui.md`, `.opencode/agents/frontend.md`, `.codex/roles/ux-ui.md`, `.codex/roles/frontend.md`, `.codex/agents/ux-ui.toml` y `.codex/agents/frontend.toml`; bórralos manualmente para evitar que tu agente los invoque por error.

El TikTok presenta 42 skills en Claude Code. Este kit lleva los ocho departamentos a perfiles y encargos compatibles con OpenCode y Codex; no copia literalmente las instrucciones internas de Claude Code.

## Tareas recomendadas para probar

- **Solo análisis:** “Directora, revisa este proyecto y dime los tres riesgos técnicos principales. No cambies archivos; consulta a Arquitectura y Seguridad.”
- **Cambio pequeño:** “Agrega validación de correo al formulario. Revisa primero el patrón existente; implementa y pide a Calidad una revisión enfocada.”
- **Trabajo dividido:** “Diseña el endpoint y la pantalla de administración. Primero acordemos el contrato; luego divide backend y Frontend Web, y reúne ambos resultados antes de editar archivos compartidos.”

Un agente es un colaborador de IA con instrucciones y herramientas, no una persona autónoma ni un proceso que trabaja continuamente. Tú apruebas alcance, modelo, cambios y acciones externas.

## Validar el kit

```powershell
& ".\scripts\Test-Equipo.ps1"
```

El script comprueba los perfiles y valida la configuración JSONC como JSON (este archivo no usa comentarios ni comas finales).
