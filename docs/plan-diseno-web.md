# Diseño Web — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir el departamento Diseño Web (coordinadora `diseno-web` + 5 especialistas) al kit `equipo-agentes`, integrándolo en OpenCode, Codex, instalador, tests y documentación, con `taste-skill` como contrato global.

**Architecture:** El kit es un repo de perfiles markdown (`.opencode/agents/`) + roles fuente Codex (`codex/roles/`) compilados a TOML (`scripts/Build-Codex-Agents.ps1`) + instalador PowerShell (`scripts/Install-Equipo.ps1`) + verificación ejecutable (`scripts/Test-Equipo.ps1`). El trabajo es: perfiles nuevos, retirada de `ux-ui`/`frontend`, reescritura acotada de `diseno`/`directora`, actualización mecánica de conteos y documentos, e instalación global de la skill desde el zip adjunto.

**Tech Stack:** Markdown (perfiles), PowerShell 5.1+ (scripts), TOML (generado, nunca editado a mano), Python (auditor de la skill, ya existente en `taste-skill/scripts/audit_taste.py`).

**Spec:** `docs/diseno-web.md` (léelo primero; este plan deriva de él)

## Global Constraints

- Todo el contenido de perfiles y docs va **en español**.
- **Ningún perfil ni rol fija `model:`** ni proveedor ni claves (regla del kit; `Test-Equipo.ps1` lo verifica).
- Frontmatter OpenCode obligatorio: `---`, `description:`, `mode: (primary|subagent|all)`. Codex: primera línea `# Rol para Codex: <Nombre>` (el builder deriva `description` de ahí).
- **La skill `taste-skill` NO se copia dentro del kit.** Los perfiles dicen "la skill `taste-skill` debe estar instalada globalmente; si no la encuentras, dilo y detente". **Prohibido** hardcodear rutas absolutas de usuario en perfiles.
- Roster final: **23 perfiles OpenCode** (19 − `ux-ui` − `frontend` + 6 nuevos) / **22 roles Codex** (18 − 2 + 6). `directora` no existe en Codex.
- Borrados permitidos **solo** `.opencode/agents/ux-ui.md`, `.opencode/agents/frontend.md`, `codex/roles/ux-ui.md`, `codex/roles/frontend.md` y sus TOMLs regenerados. Nada más se borra.
- El repo **no tiene commits**: nada depende de Git; la verificación es ejecutable (`Test-Equipo.ps1`) o por inspección directa.
- Instalaciones ya desplegadas del kit conservan `ux-ui.md`/`frontend.md` obsoletos (el instalador no borra archivos ajenos); el README debe advertirlo.
- Ejecución de scripts en Windows/PowerShell: `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-Equipo.ps1`.
- El encargo incluye **instalar `taste-skill` globalmente** desde el zip adjunto (`workspace-01a1e1cf-….zip`) a `~/.agents/skills/taste-skill/` y `~/.claude/skills/taste-skill/`. `frontend-developer/` NO se instala.

## Review Focus

1. **Referencias colgadas a `ux-ui`/`frontend`** en docs, AGENTS y template tras el renombrado — Task 6 y Task 7 lo prueban con grep (cero coincidencias fuera de `docs/diseno-web.md`, que las menciona a propósito, y del aviso de limpieza del README).
2. **Conteos desalineados entre instalador y tests** (ambos deben esperar 23/22) — Task 1 fija las expectativas y Task 5 demuestra PASS con los 23 archivos presentes.
3. **TOMLs Codex desincronizados** respecto a los roles fuente — Task 4 ejecuta siempre `Build-Codex-Agents.ps1` y `Test-Equipo.ps1` compara nombres rol↔TOML.
4. **Skill global ausente durante la verificación final** → perfiles muertos citando artefactos inexistentes — Task 7 instala desde el zip antes del smoke; si la instalación falla, STOP y reportar, no declarar éxito.
5. **Instalación real en proyecto ajeno rompe AGENTS.md o duplica bloques** — `Test-Equipo.ps1` ya cubre idempotencia y conflicto; Task 5 lo ejecuta completo, incluido el sandbox.

---

### Task 1: Fijar las nuevas expectativas en instalador y tests (tests primero, deben fallar)

**Files:**
- Modify: `scripts/Install-Equipo.ps1` (línea del inventario: `19`→`23`, `18`→`22`)
- Modify: `scripts/Test-Equipo.ps1` (`$requiredAgents`, conteos Codex `18`→`22`, mensaje final `19`→`23` y wording)

**Interfaces:**
- Consumes: roster del spec §Roster.
- Produces: suite de verificación que falla hasta completar Tasks 2–4 y pasa en Task 5. Nombres exactos requeridos por OpenCode tras el cambio: `directora, desarrollo, diseno, diseno-web, marketing, social-contenido, finanzas, operaciones, legal, producto, arquitectura, ux-web, frontend-web, backend, calidad, seguridad, plataforma-devops, datos-ia, documentacion, experiencia-cliente, direccion-arte, movimiento, imagenes`.

- [ ] **Step 1: Editar `Test-Equipo.ps1`**
  - `$requiredAgents` = lista exacta de arriba (23 nombres).
  - `if ($codexRoles.Count -ne 22)` y `if ($codexAgents.Count -ne 22)`.
  - Mensajes de error y final: 23 perfiles OpenCode, 22 subagentes Codex, "ocho departamentos y catorce especialistas".
- [ ] **Step 2: Editar `Install-Equipo.ps1`** — inventario esperado: `$sourceAgents.Count -ne 23 -or $sourceCodexRoles.Count -ne 22 -or $sourceCodexAgents.Count -ne 22`.
- [ ] **Step 3: Ejecutar y comprobar que FALLA por roster**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-Equipo.ps1`
Expected: error `Los perfiles OpenCode no coinciden con el roster requerido.` (los perfiles nuevos aún no existen).

- [ ] **Step 4: Commit** — no hay repo productivo que proteger, pero dejar rastro: `git add scripts/Test-Equipo.ps1 scripts/Install-Equipo.ps1; git commit -m "test: espera roster del departamento Diseño Web (23/22)"`. Si Git no está configurado, anotarlo y seguir sin commit.

### Task 2: Crear los 6 perfiles OpenCode del departamento

**Files:**
- Create: `.opencode/agents/diseno-web.md` (`mode: all`)
- Create: `.opencode/agents/direccion-arte.md` (`mode: subagent`)
- Create: `.opencode/agents/ux-web.md` (`mode: subagent`)
- Create: `.opencode/agents/movimiento.md` (`mode: subagent`)
- Create: `.opencode/agents/imagenes.md` (`mode: subagent`)
- Create: `.opencode/agents/frontend-web.md` (`mode: subagent`)

**Interfaces:**
- Consumes: skill `taste-skill` global (contrato §0, 14 leyes, refs `perfiles.md`, `movimiento.md`, `imagenes.md`, `anti-cliches.md`, `componentes.md`, assets `tokens.css`, auditor `scripts/audit_taste.py`, DoD §11).
- Produces: perfiles invocables por nombre; el enrutado de `directora.md` (Task 3) y la guía (Task 6) los referencian.

Contenido mínimo de cada perfil (frontmatter + cuerpo, español, estilo del kit: 3–6 líneas densas, sin adornos):

- **diseno-web** (coordinadora): recibe encargos web; emite el contrato §0 de la skill (`PERFIL / ESCALA+MEDIDA / ESTÉTICA / MOVIMIENTO+IMAGEN`) en 4 líneas antes de repartir; ordena el hand-off (direccion-arte → ux-web + (movimiento ∥ imagenes) → frontend-web → firma DoD); arbitra conflictos con autoridad final web; **veto de entrega**: nada se entrega con errores abiertos del auditor. No diseña en detalle ni escribe código. Deriva diseño no digital a `diseno`.
- **direccion-arte**: dueña de PERFIL/ESCALA/ESTÉTICA; 5 perfiles (1 SaaS, 2 corporativo, 3 landing, 4 editorial, 5 móvil), ratios, techo hero 76px, `references/perfiles.md` y `anti-cliches.md`; tokens de color/espaciado/radios; 1 acento con 3 estados; veto sobre escala y estética.
- **ux-web**: flujo, arquitectura de la información, estados (vacío/cargando/error/éxito), medida 55–72ch (sin `max-width:35ch` en móvil), responsive 390/768/1366, WCAG 2.2 AA (contraste 4.5:1, foco 2px, targets ≥44px), textos de interfaz; veto sobre accesibilidad y estados no cubiertos.
- **movimiento**: niveles 0–3, 80/140/200/320/500ms, salidas al ~70%, stagger 40–60ms, 1 momento nivel 3 por vista, `transform/opacity/filter` solamente, `prefers-reduced-motion`, View Transitions / scroll-driven con `@supports`; decide el campo MOVIMIENTO del contrato.
- **imagenes**: 4 decisiones antes de `<img>` (tratamiento/proporción/peso/consistencia); `<picture>` AVIF→WebP→JPEG, `srcset/sizes`, `fetchpriority="high"` en LCP, `aspect-ratio`+`object-fit`, placeholders sin CLS, scrim para texto sobre imagen; protocolo de prompts e iconografía SVG 24px `currentColor`; revisa siempre la imagen generada antes de entregar.
- **frontend-web**: implementa contra el contrato; HTML semántico; CSS solo con tokens de `assets/tokens.css` (prohibido valores a mano); componentes con 8 estados (default/hover/focus-visible/active/disabled/loading/error/empty); ejecuta `python3 scripts/audit_taste.py <ruta> --profile <1-5>` (o `python` en Windows) y corrige hasta 0 errores; veto técnico de entrega.

Todos: bloque final común — "La skill `taste-skill` debe estar instalada globalmente; si no la encuentras, dilo y detente. No improvises el sistema visual. Reporta archivos y decisiones; edita solo tu eje."

- [ ] **Step 1:** Escribir los 6 archivos con el contenido mínimo anterior.
- [ ] **Step 2:** Comprobar frontmatter de cada uno con grep: cada archivo empieza por `---`, contiene `description:` y `mode:` válido, y **no** contiene `model:`.

Run: `Get-ChildItem .opencode\agents\diseno-web.md, .opencode\agents\direccion-arte.md, .opencode\agents\ux-web.md, .opencode\agents\movimiento.md, .opencode\agents\imagenes.md, .opencode\agents\frontend-web.md | % { $_.Name + ': ' + (Select-String -Path $_.FullName -Pattern '^mode: (all|subagent)$').Matches.Value }`
Expected: seis líneas con `mode:` válidos.

### Task 3: Retirar `ux-ui`/`frontend` y reorientar `diseno` y `directora`

**Files:**
- Delete: `.opencode/agents/ux-ui.md`, `.opencode/agents/frontend.md`
- Modify: `.opencode/agents/diseno.md` (reorientar a diseño no digital; derivar lo web a `diseno-web`; conservar `mode: all`)
- Modify: `.opencode/agents/directora.md` (añadir enrutado: encargos web/interfaces → `diseno-web`; diseño no digital → `diseno`; los demás departamentos sin cambios)

- [ ] **Step 1:** Borrar los 2 archivos OpenCode.
- [ ] **Step 2:** Reescribir `diseno.md` y `directora.md` conservando tono/longitud del kit (3–6 líneas densas).
- [ ] **Step 3:** Grep de referencias en el kit (excluye `docs/diseno-web.md`, que los menciona a propósito):

Run: `grep -ri "ux-ui\|frontend" --include=*.md --include=*.jsonc --exclude-dir=.git --exclude=diseno-web.md . ` (o `Select-String` equivalente)
Expected: cero coincidencias de `ux-ui`; `frontend` solo aparece como `frontend-web` o en contextos históricos/aviso de limpieza.

### Task 4: Codex — roles fuente, retirada y regeneración de TOMLs

**Files:**
- Create: `codex/roles/diseno-web.md`, `direccion-arte.md`, `ux-web.md`, `movimiento.md`, `imagenes.md`, `frontend-web.md` (formato fuente: `# Rol para Codex: <Nombre>` + 1–3 líneas densas con el mismo encargo/autoridad que el perfil OpenCode)
- Delete: `codex/roles/ux-ui.md`, `codex/roles/frontend.md`
- Modify: `codex/roles/diseno.md` (no digital; derivar web a `diseno-web`)
- Regenerate: `.codex/agents/*.toml` vía script

- [ ] **Step 1:** Crear/reescribir/borrar los roles.
- [ ] **Step 2:** `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Build-Codex-Agents.ps1` — Expected: "Perfiles Codex generados en: …".
- [ ] **Step 3:** Verificar inventario: 22 `.md` en `codex/roles/`, 22 `.toml` en `.codex/agents/`, nombres coincidentes.

Run: `(Get-ChildItem codex\roles -Filter *.md).Count; (Get-ChildItem .codex\agents -Filter *.toml).Count`
Expected: `22` y `22`.

### Task 5: Suite del kit en verde

- [ ] **Step 1:** `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-Equipo.ps1`
Expected: `VALIDACIÓN OK: 23 perfiles OpenCode y 22 subagentes Codex…` (incluye sandbox de instalación: idempotencia, conservación de AGENTS.md, bloqueo de sobrescritura sin `-Force`, rechazo de instalar en el propio kit).
- [ ] **Step 2:** Si falla, corregir la causa (nunca relajar el test) y repetir hasta PASS.

### Task 6: Documentación y template

**Files:**
- Modify: `templates/AGENTS-equipo.md` (bloque Diseño Web: roster, orden de hand-offs, regla "antes de cualquier entrega visual, invoca la skill `taste-skill`", referencias actualizadas)
- Modify: `README.md` (8 departamentos / 14 especialistas; sección Diseño Web; instalación previa de la skill con rutas; aviso de limpieza para instalaciones ya desplegadas — `ux-ui.md`/`frontend.md` obsoletos, borrado manual)
- Modify: `docs/guia-departamentos-y-delegacion.md` (roster, hand-offs, enrutado web/no-digital)
- Modify: `docs/diseno.md`, `docs/plan.md` y cualquier doc con conteos/números (19→23 OpenCode, 18→22 Codex, "siete departamentos/once especialistas"→"ocho/catorce"; grep lo delata)
- Create: `docs/guia-diseno-web.md` (guía operativa: cómo encargar, orden del flujo, verificación — `opencode debug agents`, contrato §0 visible en la respuesta, `audit_taste.py` — e instalación de la skill global en las 3 rutas)
- Modify: `docs/diseno-web.md` (Estado → "aprobado; implementación en curso"; corregir referencia de la guía a `guia-diseno-web.md`)

- [ ] **Step 1:** Grep de números obsoletos: `grep -ri "19 perfiles\|18 subagentes\|siete departamentos\|once especialistas\|18 TOML\|ux-ui" --exclude-dir=.git .` — expected: vacío (salvo menciones intencionales en `docs/diseno-web.md` y aviso de README).
- [ ] **Step 2:** Actualizar todo lo encontrado hasta que el grep salga limpio.

### Task 7: Instalación global de `taste-skill` y verificación final

- [ ] **Step 1:** Localizar el zip y extraer `taste-skill/` a `%USERPROFILE%\.agents\skills\taste-skill\` y `%USERPROFILE%\.claude\skills\taste-skill\` (crear carpetas; no sobrescribir sin comprobar si ya existen y difieren — si difieren, STOP y reportar).
- [ ] **Step 2:** Verificar que el auditor corre: `python "$env:USERPROFILE\.agents\skills\taste-skill\scripts\audit_taste.py" --help` (o `python3` si es el intérprete disponible). Expected: ayuda del script, exit 0.
- [ ] **Step 3:** Repetir `Test-Equipo.ps1` (PASS) y comprobar que `taste-skill` pasa su propio auditor como sanidad: `python …\audit_taste.py "$env:USERPROFILE\.agents\skills\taste-skill\assets" --profile 3`. Expected: 0 errores (según el informe, sus assets pasan limpios).
- [ ] **Step 4:** Smoke opcional (si hay sesión OpenCode disponible): pedir "diseña el hero de una landing" y confirmar que la respuesta abre con el contrato §0 de 4 líneas. Si no hay sesión, documentar que el smoke queda pendiente de prueba manual por el usuario.

---

## Self-Review

- **Spec coverage:** instalación de la skill (spec §Instalación previa) → Task 7; roster y hand-offs → Task 2/3/4; diseno reorientado + directora enrutado → Task 3; instalador/tests/conteos → Task 1/5; docs, template, README, guía → Task 6; DoD dividido (estructura vs skill) → Task 5 y Task 7. Sin huecos.
- **Review Focus** asignados a tareas: (1)→Task 3/6, (2)→Task 1/5, (3)→Task 4/5, (4)→Task 7, (5)→Task 5.
- **Contradicciones con el spec:** ninguna; el spec ya fija eliminación (no alias) y nombres nuevos. Precaución: el spec decía "docs/diseno-web.md guía operativa" pero se resolvió a `docs/guia-diseno-web.md` (Task 6 lo refleja).
