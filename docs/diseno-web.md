# Diseño Web — nuevo departamento dentro del kit

**Fecha:** 2026-11-15 · **Estado:** aprobado e implementado (verificación estructural completa; verificación de contenido pendiente del smoke manual) · **Alcance:** repo `equipo-agentes`

## Intención y por qué

El kit ya tiene un departamento de Diseño (`diseno` con `ux-ui` y `frontend`), pero son perfiles genéricos de pocas líneas: nada en ellos sabe de perfiles de diseño, escalas tipográficas, movimiento o imágenes. El resultado es que cualquier encargo visual cae en "hazlo bonito", que es exactamente lo que la skill `taste-skill` (adjunta como `INFORME-skill-diseno-web.md` + `taste-skill/`) vino a eliminar: restricciones medibles, tokens y un auditor ejecutable.

El usuario quiere **separar los roles de diseño web como un equipo real** (estudio completo), construido sobre ese material, integrado en este kit para que sea instalable y versionable como el resto.

## Objetivos

- Crear el departamento **Diseño Web** dentro del kit: una coordinadora (`diseno-web`, principal) y especialistas, con la metodología de `taste-skill` como contrato compartido.
- Diseño Web **absorbe todo el trabajo web/de interfaces**; `diseno` queda reorientado a diseño no digital (marca, editorial, materiales, sistemas visuales offline).
- El kit **asume que `taste-skill` está instalada globalmente** en el entorno (decisión explícita del usuario): no se vendoriza la skill dentro del kit.
- Integración completa: perfiles OpenCode, roles Codex (fuente + TOML generados), instalador, tests, `templates/AGENTS-equipo.md`, README y guía de delegación actualizados.
- Autoridad declarada por eje y un veto de entrega basado en el auditor de la skill.

## No-objetivos y anti-objetivos

- **No** copiar `taste-skill/` dentro del kit ni en el instalador.
- **No** tocar otros departamentos (desarrollo, marketing, …) ni la directora salvo el enrutado web ↔ no-digital.
- **No** fijar modelo, proveedor ni claves en ningún perfil (regla del kit).
- **No** duplicar la skill: los perfiles la referencian; no embeben sus 14 leyes (salvo mención de una línea de contexto). Si falta la skill global, el agente lo dice y se detiene; no improvisa.
- Failure even if it works: un kit que "parece completo" pero donde los agentes ignoran la skill y nadie lo verifica. Por eso el auditor y el DoD son parte del contrato.

## Decisiones tomadas en la conversación

| # | Decisión | Quién |
|---|----------|-------|
| 1 | Nuevo departamento **"Diseño Web"** dentro del kit, no un paquete aparte | Usuario |
| 2 | Estudio completo: coordinadora + 5 especialistas (dirección de arte, UX/UI, movimiento, imágenes, frontend visual) | Usuario |
| 3 | Diseño Web absorbe lo web; `diseno` queda para lo no digital | Usuario |
| 4 | Skill global asumida; el kit no la vendoriza | Usuario |
| 5 | Opción B: integración completa (perfiles + Codex + instalador + tests + docs), no perfiles huérfanos | Usuario |
| 6 | Skill global **instalada por el agente desde el zip adjunto** (aprobado por el usuario): `taste-skill/` → `~/.agents/skills/taste-skill/` y `~/.claude/skills/taste-skill/`. `frontend-developer/` del zip NO se instala salvo petición expresa | Conversación + builder check Q1 |
| 7 | **Nombres nuevos** para UX y frontend (`ux-web`, `frontend-web`) en lugar de reescribir `ux-ui`/`frontend` en su sitio; el usuario acepta reescribir todas las referencias del kit | Usuario (invierte la llamada anterior del builder) |
| 8 | Departamento **Diseño Web**, coordinadora **`diseno-web`** | Usuario |
| 9 | `diseno` conserva su sitio como departamento propio, reorientado a no-digital | Usuario |

### Por qué la decisión 7

El usuario prefiere nombres explícitos web-específicos y acepta el coste de referencias. En consecuencia:

- Se crean `ux-web.md` y `frontend-web.md`; los antiguos `ux-ui.md` y `frontend.md` se **eliminan del kit** (no se dejan como alias: la autoridad quedaría ambigua, que es el fallo que el informe diagnostica).
- Todas las referencias (`directora.md`, `diseno.md`, README, guías, template AGENTS, tests, instalador) se reescriben de `ux-ui`/`frontend` a `ux-web`/`frontend-web`.
- Instalaciones ya desplegadas del kit conservarán `ux-ui.md`/`frontend.md` obsoletos (el instalador no borra archivos ajenos); el README lo advierte con instrucciones de limpieza manual.
- Codex: roles `ux-ui`/`frontend` eliminados, `ux-web`/`frontend-web` añadidos; TOMLs regenerados.

## Roster del departamento (23 perfiles OpenCode / 22 roles Codex)

Conteo: 19 actuales − `ux-ui` − `frontend` (eliminados) + 6 nuevos (`diseno-web`, `direccion-arte`, `ux-web`, `movimiento`, `imagenes`, `frontend-web`) = **23**. Codex: 18 − 2 + 6 = **22**.

| Perfil (nombre de archivo) | Modo | Rol en el estudio |
|---|---|---|
| `diseno-web.md` | all (coordinadora) | Recibe el encargo web, emite o modera el **contrato de salida** de la skill (§0: `PERFIL / ESCALA+MEDIDA / ESTÉTICA / MOVIMIENTO+IMAGEN`), reparte el trabajo, arbitra entre especialistas y firma el DoD. No diseña en detalle ni implementa. |
| `direccion-arte.md` | subagent | Dueña del **PERFIL / ESCALA / ESTÉTICA** del contrato. 5 perfiles de la skill, ratios tipográficos, techo hero 76px, anti-clichés (`references/anti-cliches.md`), tokens de color/espaciado/radios. Veto sobre escala y estética. |
| `ux-web.md` | subagent | Flujos, arquitectura de la información, estados (vacío/cargando/error/éxito), jerarquía, medida de lectura, responsive (390/768/1366), accesibilidad WCAG 2.2 AA, textos de interfaz. Veto sobre accesibilidad y estados no cubiertos. |
| `movimiento.md` | subagent | Sistema de movimiento de la skill: niveles 0–3, duraciones (80/140/200/320/500ms), salidas al 70%, coreografías nombradas, View Transitions, scroll-driven con `@supports`, `prefers-reduced-motion`. Decide el **MOVIMIENTO** del contrato. |
| `imagenes.md` | subagent | Sistema de medios: 4 decisiones antes de `<img>` (tratamiento/proporción/peso/consistencia), `<picture>` AVIF→WebP→JPEG, `srcset/sizes`, `fetchpriority` en LCP, placeholders sin CLS, protocolo de prompts para imágenes generadas (revisión obligatoria antes de entregar), iconografía SVG 24px. |
| `frontend-web.md` | subagent | Implementación: HTML semántico, CSS con los tokens de `assets/tokens.css` (sin valores a mano), componentes con 8 estados, `prefers-reduced-motion`, auditor obligatorio (`scripts/audit_taste.py <ruta> --profile <1-5>`), DoD. Veto técnico: ningún encargo web se entrega con errores abiertos del auditor. |

Reescritura asociada fuera del departamento:

| Perfil | Cambio |
|---|---|
| `diseno.md` | Reorientado a **diseño no digital**: marca, editorial impreso, materiales, sistemas visuales offline. Deriva lo web a `diseno-web`. Conserva su sitio como departamento propio. |
| `directora.md` | Añadir regla de enrutado: encargos web/interfaces → `diseno-web`; diseño no digital → `diseno`. |
| `templates/AGENTS-equipo.md` | Añadir bloque Diseño Web con la regla "antes de cualquier entrega visual, el agente correspondiente invoca y sigue la skill `taste-skill`". |
| `README.md`, `docs/guia-departamentos-y-delegacion.md` | Sección del nuevo departamento: roster, orden de hand-offs, instalación previa de la skill global. |

## Flujo de trabajo (hand-off por defecto)

1. **Brief → `diseno-web`**: emite el contrato §0 en 4 líneas (o pide a `direccion-arte` + `movimiento` las líneas que no pueda decidir). Sin contrato no empieza nadie.
2. **`direccion-arte`**: fija perfil, escala, tokens (bloque `:root`/`@theme`) y dirección estética en una línea con referencia no genérica.
3. **`ux-web`**: flujo, estados, medida, responsive, accesibilidad. (Paralelo con 4.)
4. **`movimiento` + `imagenes`**: coreografía y sistema de medios. (Paralelo con 3, después de 2.)
5. **`frontend-web`**: implementa contra el contrato; ejecuta el auditor; corrige o justifica warnings.
6. **`diseno-web`**: verifica el checklist de terminado de la skill (§11) y firma.

Los especialistas se acotan a su eje; fuera de él, reportan a `diseno-web`, no imponen.

## Instalación previa de la skill global (paso obligatorio, documentado)

El kit no la copia. **El usuario aprobó instalarla desde el zip adjunto como parte de este trabajo** (builder check, pregunta 1). La instalación se hace antes de la verificación final:

- Claude Code: `taste-skill/` → `~/.claude/skills/taste-skill/`.
- OpenCode: `taste-skill/` → `~/.agents/skills/taste-skill/` (misma ruta que el resto de skills globales del entorno).
- Codex: no tiene skills; sus roles (`codex/roles/`) referencian la skill y `AGENTS.md` instruye leerla cuando exista; si no existe, el agente lo declara y pide la instalación.
- `frontend-developer/` del zip **no** se instala salvo petición expresa del usuario.
- `docs/guia-diseno-web.md` (guía) y README documentarán estas rutas y la verificación.

Los perfiles **no hardcodean rutas absolutas**; dicen "la skill `taste-skill` debe estar instalada globalmente; si no la encuentras, dilo y detente".

## Cambios en el kit

- `.opencode/agents/`: nuevos `diseno-web.md`, `direccion-arte.md`, `ux-web.md`, `movimiento.md`, `imagenes.md`, `frontend-web.md`; eliminados `ux-ui.md`, `frontend.md`; `diseno.md` y `directora.md` reescritos.
- `codex/roles/`: nuevos los 6 del departamento; eliminados `ux-ui.md`, `frontend.md`; reescrito `diseno.md` (22 roles en total; Codex no lleva directora).
- `.codex/agents/`: regenerar con `scripts/Build-Codex-Agents.ps1`.
- `scripts/Install-Equipo.ps1`: inventario esperado 19→23 OpenCode, 18→22 Codex; resto sin cambios (autodescubre por directorio).
- `scripts/Test-Equipo.ps1`: `requiredAgents` actualizado a los 23 nombres nuevos; conteos Codex 22; mensaje final actualizado.
- `templates/AGENTS-equipo.md`: bloque Diseño Web (roster + activación de la skill); referencias `ux-ui`/`frontend` → `ux-web`/`frontend-web`.
- `README.md`, `docs/guia-departamentos-y-delegacion.md`: 8 departamentos, 14 especialistas; roster, orden de hand-offs, instalación previa de la skill global y aviso para instalaciones existentes (limpieza manual de `ux-ui.md`/`frontend.md`).
- `docs/guia-diseno-web.md`: guía operativa nueva (cómo encargar, orden, verificación, instalación de la skill global con las 3 rutas). `docs/diseno-web.md` se conserva como documento de diseño.
- `docs/plan.md` / otros docs solo si referencian roster, nombres o conteos (actualizar).

## Definición de terminado

- [ ] `scripts/Test-Equipo.ps1` pasa (conteos 23/22, sin modelos, frontmatter válido, instalación idempotente en sandbox).
- [ ] `scripts/Build-Codex-Agents.ps1` ejecutado; TOMLs regenerados y en sync.
- [ ] Instalador real contra carpeta temporal: copia 23+22+22, conserva AGENTS existente, bloquea conflictos sin `-Force`.
- [ ] `taste-skill` instalada globalmente desde el zip (`~/.agents/skills/taste-skill/` y `~/.claude/skills/taste-skill/`) y el auditor accesible (`python3 scripts/audit_taste.py --help` o lectura del script).
- [ ] Cada perfil nuevo: frontmatter correcto, `mode` válido, sin `model:`, encargo acotado, autoridad y hand-off declarados, referencia a la skill global (sin rutas absolutas inventadas), español.
- [ ] Grep de referencias cruzadas: ningún documento del kit sigue diciendo "siete departamentos / once especialistas / 18/19 perfiles" ni invocando `ux-ui`/`frontend` como perfiles inexistentes.
- [ ] Verificación de contenido tras instalar la skill: "Diseña el hero de una landing" debe producir el contrato §0 y derivar en el orden definido.

**División de la verificación** (builder check, pregunta 3): el kit estructural se verifica durante la construcción; los ítems que dependen de la skill instalada se verifican justo después de instalarla, dentro del mismo encargo.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| La skill global no está instalada y el agente improvisa | Perfiles instruyen detenerse y declararlo; docs con pasos de instalación y verificación. |
| Solape `diseno` vs `diseno-web` | Autoridad escrita en ambos perfiles y en la directora: web → `diseno-web`, no digital → `diseno`. |
| Solape `ux-web`/`frontend-web` vs referencias antiguas | Grep global de `ux-ui`/`frontend` en el kit y reescritura; aviso en README para instalaciones existentes (archivos obsoletos no se borran). |
| Rutas de skills distintas por herramienta | Sin rutas absolutas en perfiles; guía con las 3 rutas documentadas. |
| Drift con `taste-skill` (el usuario la actualice) | Perfiles no embeben las leyes; cualquier conflicto lo resuelve la skill instalada, no el kit. |
| Codex sin skills | Roles Codex referencian la skill global y la instrucción AGENTS.md; si falta, lo declaran. |
| Tests desactualizados tras cambiar roster | Actualizar `Test-Equipo.ps1` e instalador en el mismo cambio; CI local = ese script. |

## Respuestas del builder check (cerrado)

1. **La skill no estaba instalada y `design-taste-frontend` es otra cosa.** Resuelto: el usuario aprueba instalar `taste-skill` desde el zip durante este encargo (`~/.agents/skills/` y `~/.claude/skills/`); `frontend-developer/` no se instala salvo petición.
2. **Colisión de nombre guía/diseño.** Resuelto: guía nueva en `docs/guia-diseno-web.md`; `docs/diseno-web.md` se conserva como documento de diseño.
3. **DoD sin la skill.** Resuelto: estructura verificada durante la construcción; verificación dependiente de la skill justo después de instalarla, en el mismo encargo.
4. **Check de la skill en instalador/tests.** Resuelto: no; verificación documental únicamente (un check duro rompería máquinas sin la skill).

Notas del builder: el repo no tiene ningún commit (no dependemos de Git para conservar el doc); `helpdesk-saas/` y `studiogest-web/` no llevan copias del kit (fuera de alcance); `directora` no existe en Codex por diseño.
