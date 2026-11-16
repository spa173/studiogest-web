# Diseño: oficina multiagente unificada para Codex y OpenCode

**Fecha:** 16 de noviembre de 2026

**Estado:** pendiente de aprobación

**Decisión del usuario:** reemplazar las oficinas actuales y dejar una sola oficina jerárquica disponible en Codex y OpenCode.

## Intención

La instalación actual funciona, pero tiene dos modelos superpuestos. OpenCode carga 59 perfiles visibles: 23 perfiles planos, 30 perfiles bajo `oficina/` y perfiles heredados como `ux-ui` y `frontend`. El kit fuente, en cambio, genera 23 perfiles OpenCode y 22 subagentes Codex. Ambos conjuntos describen responsabilidades parecidas con nombres y rutas diferentes.

La nueva oficina tendrá una sola definición mantenible. Desde esa fuente se generarán los archivos nativos de cada plataforma, conservando el mismo significado, identificadores estables y contratos de entrega. El Documento Maestro será la referencia funcional; los agentes existentes aportarán las áreas de negocio que no aparecen allí, como Finanzas, Social y Experiencia del cliente.

### Precedencia de fuentes

Para construir los prompts se aplicará este orden:

1. La solicitud explícita del usuario y el `AGENTS.md` más cercano al trabajo mandan durante la ejecución.
2. `C:\Users\camilo\Downloads\DOCUMENTO-MAESTRO-OFICINA-MULTI-AGENTE.md`, versión 1.0 del 16 de noviembre de 2026, define el catálogo mínimo, los contratos y los gates.
3. Los perfiles del kit `equipo-agentes` y los perfiles globales bajo `oficina/` aportan restricciones operativas que no contradigan el Documento Maestro.
4. Este diseño resuelve contradicciones, elimina duplicados y fija la arquitectura final.

El ZIP `workspace-01a1e1cf-1c19-7939-9646-891d2bc49d21.zip` es la fuente aprobada para `taste-skill` y `frontend-developer`. Las demás skills se escribirán a partir del Documento Maestro y los perfiles existentes; no se asumirá otra fuente privada.

## Qué debe conseguir

- Una sola Directora que clasifique la solicitud, convoque únicamente a los departamentos necesarios y reúna los resultados.
- El mismo catálogo conceptual en Codex y OpenCode, generado desde una fuente común.
- Cobertura completa de producto, diseño, frontend, backend, móvil, datos e IA, calidad, seguridad, auditoría, plataforma, incidentes, SEO, documentación, legal y operaciones.
- Contratos verificables para brief, handoff, quality gate, escalado y cierre.
- Permisos mínimos por rol y separación entre análisis, implementación, revisión y acciones externas.
- Registro explícito de herramientas: qué capacidad necesita cada agente, qué proveedor la satisface y si está conectada.
- Instalación reemplazable, idempotente, comprobable y recuperable.

## Lo que no hará

- No fijará un modelo ni un proveedor de IA.
- No instalará dependencias de aplicación en los proyectos donde se use la oficina.
- No publicará, desplegará, enviará mensajes ni modificará servicios externos sin una petición explícita en la tarea correspondiente.
- No inventará conexiones MCP ni credenciales. Una capacidad ausente quedará marcada como `missing` y el agente deberá degradar su flujo o pedir intervención.
- No copiará instrucciones idénticas entre agentes y skills. Cada regla tendrá un dueño.

## Enfoques considerados

### 1. Oficina plana ampliada

Conservar los perfiles planos y añadir los agentes faltantes. Es el cambio más corto, pero deja demasiadas decisiones directas en la Directora y vuelve probable la duplicación.

### 2. Oficina jerárquica generada desde una fuente única — elegida

Una Directora coordina departamentos; los departamentos coordinan especialistas. Un registro canónico genera OpenCode y Codex. Permite aplicar permisos y contratos consistentes sin mantener dos oficinas manualmente.

### 3. Oficina centrada casi por completo en skills

Reduce el número de perfiles, pero Codex y OpenCode cargan y gobiernan las skills de forma diferente. La paridad sería aparente y la delegación menos visible.

## Estructura humana de la oficina

La oficina tendrá 31 perfiles conceptuales: una Directora, cinco coordinadores y veinticinco especialistas. No todos se convocan en cada tarea.

### Dirección

- `directora`: punto de entrada, clasificación, secuencia, contexto compartido, gates, escalado y síntesis.

### Producto y Experiencia

- `coord-producto-experiencia`
- `producto`
- `diseno-web`
- `ux-accesibilidad`
- `seo-growth`
- `data-analytics`

### Ingeniería y Datos

- `coord-ingenieria-datos`
- `arquitectura`
- `frontend`
- `backend`
- `mobile`
- `datos-ia`
- `integraciones`

### Calidad y Seguridad

- `coord-calidad-seguridad`
- `qa`
- `seguridad`
- `auditoria`
- `rendimiento`

### Operaciones y Entrega

- `coord-operaciones-entrega`
- `devops`
- `sre-observabilidad`
- `forensics`
- `release`
- `documentacion`

### Negocio y Gobernanza

- `coord-negocio-gobernanza`
- `marketing`
- `social-contenido`
- `finanzas`
- `legal`
- `experiencia-cliente`

Las especialidades eliminadas como perfiles separados se consolidan donde existe un dueño claro: Dirección de Arte, Movimiento e Imágenes viven en `diseno-web` mediante `taste-skill`; automatización de pruebas vive en `qa`; bases de datos viven entre `backend` y `data-analytics`; privacidad se divide entre `legal` y `seguridad`.

## Fuente única y archivos generados

El kit incorporará este núcleo:

```text
office/
  registry.json
  capabilities.json
  roles/<id>.md
  contracts/
    task.schema.json
    handoff.schema.json
    gate.schema.json
    escalation.schema.json
  permission-sets/
    readonly.json
    implementer.json
    operator.json
skills/
  taste-skill/
  frontend-developer/
  backend-developer/
  qa-engineer/
  security-auditor/
  devops-platform/
  forensics-incident/
  data-analytics/
  seo-growth/
scripts/
  Build-Office.ps1
  Install-Office.ps1
  Test-Office.ps1
```

`registry.json` será la autoridad para identificadores, departamento, padre, descripción, prompt, permission set, skills y capacidades. Se usa JSON para que PowerShell pueda validarlo sin incorporar YAML ni paquetes nuevos.

`Build-Office.ps1` generará:

- OpenCode: perfiles Markdown en `.opencode/agents/`, con `directora` como agente primario y permisos de subagente explícitos.
- Codex: perfiles TOML en `.codex/agents/` para coordinadores y especialistas, más un bloque de `AGENTS.md` que convierte el chat principal en Directora.

La jerarquía de OpenCode requiere dos saltos (`directora → coordinador → especialista`). El generador establecerá `experimental.subagent_depth` en `2` y conservará las demás opciones existentes; una profundidad menor fallará la validación.

Los archivos generados llevarán una cabecera que prohíbe su edición manual. Los cambios se hacen en `office/` y se regeneran.

## Flujo de orquestación

1. **Intake:** la Directora clasifica el trabajo como feature, bug, auditoría, despliegue, incidente, investigación u otro.
2. **Brief:** crea un contrato de tarea con objetivo, alcance, exclusiones, riesgos, artefactos y evidencia esperada.
3. **Ruta mínima:** elige departamentos. Una edición clara no convoca la oficina completa.
4. **Definición:** Producto interviene cuando el resultado o los criterios de aceptación son ambiguos.
5. **Ejecución:** Ingeniería implementa; solo se paralelizan tareas independientes y con archivos exclusivos.
6. **Gates:** Calidad, Seguridad y Operaciones verifican según el riesgo real del cambio.
7. **Escalado:** se detiene ante ambigüedad de negocio, riesgo legal, credenciales, producción, gasto, publicación o acciones irreversibles.
8. **Cierre:** la Directora separa lo realizado, lo verificado, los riesgos y lo pendiente.

Cada handoff debe contener `from`, `to`, `task_id`, `context_summary`, `scope`, `artifacts`, `evidence`, `gate_status`, `risks` y `next_action`. Un coordinador no puede declarar un gate en `pass` sin evidencia.

Los contratos son formatos de intercambio y validación, no un motor persistente de workflow. Los agentes pueden emitirlos como bloques JSON en su respuesta o guardarlos como artefactos cuando la tarea lo pida. El kit valida archivos de contrato existentes, pero no mantiene una base de datos de tareas.

### Ciclo de vida de los contratos

- `task`: `drafted → approved → in_progress → verification → completed`; desde cualquier estado activo puede pasar a `blocked` o `cancelled`, y `blocked` vuelve al estado anterior solo después de resolver una escalación.
- `gate.status`: `pending | pass | fail | waived`. `waived` exige `approved_by`, `reason` y evidencia de aceptación humana.
- `escalation.status`: `open | resolved`; una escalación abierta bloquea cualquier acción que dependa de ella.

`task.schema.json` incluirá `task_id`, `type`, `priority`, `objective`, `scope`, `out_of_scope`, `acceptance_criteria`, `constraints`, `risk`, `departments`, `artifacts` y `status`. Los tipos permitidos son `feature`, `bug`, `audit`, `deploy`, `incident`, `research` y `other`; la prioridad usa `P0` a `P3`, y el riesgo `low`, `medium`, `high` o `critical`.

`gate.schema.json` incluirá `gate_id`, `task_id`, `kind`, `owner`, `required`, `criteria`, `evidence`, `status` y, si aplica, `waiver`. Los kinds son `product`, `design`, `implementation`, `qa`, `security`, `documentation`, `release` y `post_deploy`.

`escalation.schema.json` incluirá `escalation_id`, `task_id`, `trigger`, `question`, `options`, `recommendation`, `status` y `resolution`. Los triggers son `business_ambiguity`, `legal_privacy`, `credentials`, `external_write`, `production`, `spend`, `destructive_action` y `instruction_conflict`.

### Política mínima de gates

| Trabajo | Gates obligatorios |
|---|---|
| Edición trivial sin cambio de comportamiento | verificación local y `documentation` si cambia una guía |
| Feature | `product`, `implementation`, `qa`; `design` si hay UI; `security` si toca auth, permisos, datos, red, pagos o secretos |
| Bug | reproducción y `qa`; `security` con los mismos disparadores de riesgo |
| Auditoría | `audit` y revisión del dominio afectado; no hay implementación implícita |
| Despliegue | `qa`, `security`, `documentation` y `release`, con rollback definido |
| Incidente | `forensics`, `security` y operaciones; preservación de evidencia antes de corregir |
| Investigación | evidencia y límites; sin gates de implementación |

`documentation` es obligatorio cuando cambia una API, una operación, un flujo de usuario o un procedimiento. `post_deploy` solo se exige cuando hubo despliegue. Un gate adicional puede añadirse por riesgo; nunca se retira uno obligatorio sin waiver humano.

## Skills y autoridad

Los perfiles deciden **quién** trabaja; las skills describen **cómo** ejecutar un método especializado.

- `taste-skill` es la única autoridad visual para interfaces.
- `frontend-developer` es la autoridad sobre arquitectura de cliente, estado y datos.
- Las nuevas skills cubren backend, QA, seguridad, plataforma, incidentes, analítica y SEO sin repetir la coordinación departamental.
- Una regla crítica permanece resumida en el perfil que la necesita; el detalle y los scripts viven en la skill.

Las skills se instalarán globalmente en las rutas admitidas por cada entorno y también quedarán incluidas en el kit para instalaciones por proyecto.

Cada skill nueva tendrá frontmatter de activación, límites, contrato de entrada/salida, procedimiento, gate propio, referencias necesarias y al menos cuatro evals: activación positiva, anti-trigger, caso incompleto y entrega verificable. No necesita duplicar todo el prompt del agente que la usa.

### Investigación de branding y landing pages

`diseno-web` tendrá la capacidad `web_research` y realizará una exploración de referencias antes de diseñar una web nueva, una landing o un rediseño significativo. En ajustes pequeños dentro de un sistema visual aprobado, esta fase será opcional.

La exploración debe:

- reunir entre 3 y 6 referencias actuales, combinando sitios publicados de marcas comparables, galerías curadas y guías técnicas autorizadas;
- registrar URL, fecha de consulta, tipo de página, viewport observado y el patrón concreto que aporta cada referencia;
- analizar estructura narrativa, jerarquía, tipografía, color, retícula, prueba social, CTA, tratamiento de imágenes y movimiento;
- contrastar las ideas con accesibilidad, rendimiento, contenido real y objetivos de conversión;
- producir un artefacto `reference-study.md` con moodboard razonado, patrones transferibles, decisiones que no conviene copiar y una lista `usar / evitar`;
- distinguir con claridad una referencia visual de una recomendación propia.

Las referencias se usan para aprender principios, no para clonar una composición, identidad, copy, ilustración, fotografía, animación distintiva ni *trade dress*. Si la búsqueda web no está disponible, el agente pide referencias al usuario o declara la limitación; no inventa que investigó.

El gate `design` exige el estudio de referencias cuando esta fase sea obligatoria, seguido del contrato de `taste-skill` y una dirección original coherente con la marca del proyecto.

## Matriz de permisos

Los permission sets son concretos:

- `readonly`: lectura, búsqueda, Git de inspección y web/MCP de lectura; niega edición y shell general. Permite únicamente comandos de inspección enumerados (`git status/diff/log/show`, `rg`, `Get-ChildItem`, `Get-Content`, `Select-String`) cuando la plataforma requiere shell.
- `implementer`: lectura, edición y comandos locales de build/test. Pregunta antes de escribir fuera del workspace, usar credenciales, instalar dependencias, hacer push, publicar o desplegar. Niega destrucción no autorizada.
- `operator`: lectura y diagnósticos operativos; puede preparar configuración y ejecutar health checks. Toda escritura externa, despliegue, rollback real o cambio de infraestructura pregunta primero. Destrucción queda denegada salvo autorización explícita para el objetivo exacto.

Asignación:

- Directora, Producto, Calidad/Seguridad, Negocio/Gobernanza y sus especialistas analíticos: `readonly`.
- Ingeniería/Datos, Frontend, Backend, Mobile, Datos/IA e Integraciones: `implementer`.
- Operaciones/Entrega, DevOps, SRE, Forensics y Release: `operator`; Documentación usa `implementer` limitado a documentos.
- Diseño Web usa `implementer` solo cuando la tarea autoriza implementación; por defecto entrega especificación en modo `readonly`.
- QA puede ejecutar suites de prueba, pero no corregir producto durante una revisión. Seguridad y Auditoría permanecen en solo lectura.

Las capacidades MCP se permiten además por rol: por ejemplo, `work_tracking` para Dirección/Producto, `observability` para SRE/Forensics y `deployment` para DevOps/Release. Una capacidad no amplía el permission set por sí sola.

## Herramientas, MCP y conectores

`capabilities.json` no guardará secretos ni nombres rígidos de herramientas en los prompts. Definirá capacidades lógicas:

- `repository`: Git y GitHub.
- `work_tracking`: Linear o sistema equivalente.
- `knowledge`: Notion o documentación del repositorio.
- `database`: Neon/Postgres cuando el proyecto lo use.
- `web_research`: navegador o búsqueda web.
- `design_source`: Figma cuando esté conectado.
- `communication`: Slack cuando esté conectado.
- `observability`: Datadog o equivalente.
- `deployment`: Vercel o proveedor del proyecto.
- `product_analytics`: Mixpanel o Amplitude, nunca ambos por defecto.

Estado observado al diseñar:

- Codex: GitHub, Linear y Notion instalados; REA, LGTV y Node REPL configurados localmente. LGTV no pertenece a la oficina de software y no se asignará a ningún agente.
- OpenCode: MCP `browse`, `github` y `Neon` configurados.
- Disponibles pero no conectados: Slack, Datadog, Vercel, Mixpanel, Amplitude y Figma.

El instalador conservará los MCP existentes y fusionará únicamente configuración de oficina validada. Las conexiones que exigen OAuth o una cuenta se prepararán como pendientes; el usuario completa el inicio de sesión. Ningún agente recibirá acceso a una herramienta que no necesita.

La instalación base solo detecta, asigna y reporta conexiones. No añade servidores remotos, no inicia OAuth y no altera credenciales. Un script separado `Connect-OfficeTools.ps1` mostrará el proveedor recomendado, el comando o conector oficial y el estado, pero cualquier conexión que cambie una cuenta requerirá interacción del usuario. Si hay varios proveedores para una capacidad, se conserva el ya conectado; para analítica se pide escoger uno antes de conectar.

OpenCode puede aplicar permisos por herramienta y por MCP mediante reglas; el generador las emitirá. Los subagentes Codex heredan herramientas y permisos de la sesión, por lo que la separación allí será una combinación de instrucciones, selección mínima de agente y controles del entorno, sin prometer aislamiento que la plataforma no garantiza.

## Reemplazo seguro

`Install-Office.ps1` aceptará `-Platform Codex|OpenCode|Both`, `-Scope Global|Project` y `-DryRun`.

Para la instalación global elegida:

1. Resolverá y verificará las rutas exactas.
2. Inventariará únicamente los perfiles administrados por la oficina.
3. Creará una copia fechada y con hashes antes de mover o reemplazar archivos.
4. Retirará los 23 perfiles planos, los 30 perfiles anidados y los perfiles heredados identificados, sin tocar agentes ajenos a la oficina.
5. Escribirá la nueva generación.
6. Validará OpenCode con `opencode debug agents` y Codex mediante estructura TOML, inventario y una prueba de descubrimiento disponible localmente.
7. Si falla una validación, restaurará la copia y devolverá un error.

El repositorio fuente conservará la capacidad de instalar la oficina por proyecto. Los proyectos de ejemplo `helpdesk-saas` y `studiogest-web` quedan fuera del cambio.

El inventario destructivo no se deducirá por patrón. `office/legacy-files.json` contendrá rutas relativas exactas y hashes cuando exista una fuente conocida. Incluirá los 23 perfiles globales que coinciden con el kit actual, los 30 archivos bajo la carpeta global `agents/oficina/` y los perfiles heredados detectados en la cadena de configuración del proyecto. El instalador solo retira una ruta si está dentro del directorio de agentes esperado y figura en ese inventario; un archivo con hash inesperado se respalda y requiere `-Force` explícito.

En Codex, el bloque global se instalará en `~/.codex/AGENTS.md` entre `<!-- oficina-unificada:inicio -->` y `<!-- oficina-unificada:fin -->`. En proyectos se usa el mismo bloque en el `AGENTS.md` raíz. Las instrucciones fuera de los marcadores se conservan, y un `AGENTS.md` más cercano mantiene la precedencia normal de Codex. Los marcadores antiguos `equipo-agentes` se migran una sola vez después de respaldar el archivo.

La restauración tendrá interfaz explícita: `Restore-Office.ps1 -Backup <ruta> -Platform Codex|OpenCode|Both`. El rollback automático por fallo usará el mismo mecanismo. Cada backup incluirá manifiesto, hashes, fecha, plataforma y archivos de configuración afectados.

## Verificación y gates del propio kit

`Test-Office.ps1` comprobará:

- JSON válido y referencias internas completas.
- Identificadores únicos y mismo inventario conceptual en ambas plataformas.
- Jerarquía sin ciclos; solo la Directora puede ser raíz.
- Permission sets conocidos y ausencia de permisos amplios accidentales.
- Capacidades referenciadas existentes y sin secretos.
- Salida generada sincronizada con la fuente.
- Instalación idempotente en una carpeta temporal.
- Bloqueo de conflictos no administrados.
- Copia y restauración ante fallo simulado.
- OpenCode sin perfiles antiguos ni duplicados después de la instalación.
- Skills con frontmatter válido y referencias existentes.

No se afirmará compatibilidad funcional hasta ejecutar estas verificaciones. Las conexiones externas se informarán por separado como `connected`, `needs_auth`, `missing` o `not_applicable`.

## Decisiones del constructor

El constructor puede decidir nombres de funciones PowerShell, orden interno de campos JSON, colores de agentes y redacción menor de prompts. Debe mantener los identificadores, el roster, los límites de autoridad, la política de respaldo y los contratos descritos aquí.

## Criterios de aceptación

- OpenCode muestra una sola `directora` y exactamente los 30 perfiles subordinados nuevos, sin los perfiles antiguos administrados por la oficina.
- Codex descubre los cinco coordinadores y veinticinco especialistas, mientras el chat principal asume la Dirección mediante `AGENTS.md`.
- Una modificación en `office/` regenera ambas plataformas sin editar manualmente salidas.
- El instalador puede reemplazar la oficina global, repetir la instalación sin diferencias y restaurar la versión anterior.
- Un encargo de feature atraviesa brief, implementación y gates; un cambio trivial usa una ruta corta.
- Las herramientas conectadas se asignan por capacidad y las ausentes se reportan sin bloquear trabajo local innecesariamente.
- Todas las pruebas del kit se ejecutan y sus resultados reales quedan documentados.
