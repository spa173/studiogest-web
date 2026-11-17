# Guía operativa: Diseño Web

Cómo encargar y verificar el trabajo del departamento **Diseño Web** (`diseno-web` + `direccion-arte`, `ux-web`, `movimiento`, `imagenes`, `frontend-web`).

## Requisito previo: instala la skill `taste-skill`

La skill **no** se incluye en este kit. Sin ella, los perfiles web se detienen y lo declaran; no improvisan el sistema de diseño.

Instalación (copia la carpeta `taste-skill/` a tu carpeta global de skills):

| Herramienta | Ruta global |
|---|---|
| OpenCode | `~/.agents/skills/taste-skill/` (en Windows: `%USERPROFILE%\.agents\skills\taste-skill\`) |
| Claude Code | `~/.claude/skills/taste-skill/` |
| Codex | Codex no tiene skills; sus roles referencian la skill y `AGENTS.md` instruye leerla. Si no existe, el agente lo declara. |

Verifica la instalación pidiendo «diseña un hero»: la respuesta debe abrir con el contrato de salida de la skill (`PERFIL / ESCALA+MEDIDA / ESTÉTICA / MOVIMIENTO+IMAGEN` en 4 líneas). Si no aparece, la skill no está donde tu herramienta la busca.

## Cómo encargar

1. Describe el objetivo y el límite («solo análisis», «no implementes», «espera mi aprobación»).
2. En OpenCode selecciona **Directora** o directamente **`diseno-web`** para temas web. En Codex, el chat principal coordina y delega por nombre: `diseno-web`, `direccion-arte`, `ux-web`, `movimiento`, `imagenes`, `frontend-web`.
3. Antes de escribir cualquier etiqueta o CSS, la respuesta abre con el **contrato de salida** de `taste-skill` (§0). Si falta, el encargo no ha empezado.

## Orden de trabajo (hand-off)

1. `diseno-web` emite o modera el contrato §0 (`PERFIL / ESCALA+MEDIDA / ESTÉTICA / MOVIMIENTO+IMAGEN`).
2. `direccion-arte` fija perfil, escala tipográfica, tokens (`:root`/`@theme`) y estética con referencia no genérica.
3. `ux-web` define flujo, estados (vacío/cargando/error/éxito), medida (55–72ch), responsive (390/768/1366) y accesibilidad WCAG 2.2 AA.
4. `movimiento` define la coreografía (niveles 0–3; 1 momento nivel 3 por vista) e `imagenes` el sistema de medios (tratamiento → proporción → peso → consistencia; LCP con `fetchpriority="high"`). 3 y 4 van en paralelo.
5. `frontend-web` implementa con los tokens (sin valores a mano) y ejecuta el auditor:

   ```powershell
   pwsh -NoProfile -File scripts/Invoke-TasteAudit.ps1 -Path <ruta-html-css> -Profile <1-5>
   ```

   El runner verifica que la entrada exista y contenga archivos auditables, normaliza UTF-8 en Windows y conserva el código de salida del auditor. **0 errores abiertos es condición de entrega.** Los warnings se corrigen o se justifican en una línea.
6. `diseno-web` verifica el checklist de terminado de la skill (§11) y firma.

## Reglas del departamento

- Estética y escala: manda `direccion-arte`. Flujo y accesibilidad: manda `ux-web`. Código: manda `frontend-web`. Discrepancias: decide `diseno-web`.
- Nada de anti-clichés de la skill (`references/anti-cliches.md`): ni gradientes morado-genéricos, ni 3 tarjetas centradas, ni carruseles automáticos.
- Encargos que no sean web (marca, editorial, materiales): van a `diseno`, no a Diseño Web.
- Codex: los roles fuente están en `codex/roles/` del kit y se copian a `.codex/roles/` en el proyecto instalado; los TOML viven en `.codex/agents/`. Se regeneran con `scripts/Build-Codex-Agents.ps1`.

## Verificación

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-Equipo.ps1` — inventario, frontmatter, TOML en sync, instalación idempotente.
- `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1` — integridad de skills, referencias y contrato estructural de escenarios.
- `opencode debug agents` — perfiles que reconoce OpenCode.
- Smoke manual: pide «diseña el hero de una landing» y comprueba que la respuesta abre con el contrato §0 y delega según el orden anterior.

## Nota para instalaciones existentes

Si ya desplegaste una versión anterior del kit en otro proyecto, el instalador **no borra** los archivos retirados: elimina manualmente `.opencode/agents/ux-ui.md`, `.opencode/agents/frontend.md`, `.codex/roles/ux-ui.md`, `.codex/roles/frontend.md`, `.codex/agents/ux-ui.toml` y `.codex/agents/frontend.toml` para evitar invocaciones obsoletas.

**Documento de diseño:** [`diseno-web.md`](diseno-web.md) · **Plan:** [`plan-diseno-web.md`](plan-diseno-web.md)
