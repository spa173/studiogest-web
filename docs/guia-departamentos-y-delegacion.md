# Guía de departamentos y delegación

La oficina tiene **31 perfiles conceptuales**: Dirección, cinco coordinadores y veinticinco especialistas. Su única fuente canónica es [`office/registry.json`](../office/registry.json), junto con los prompts en `office/roles/`. Esta guía explica cómo encargar el trabajo; los perfiles generados se actualizan mediante `scripts/Build-Office.ps1`.

En **Codex**, el chat principal ejerce la Dirección y dispone de **30 subagentes**; `directora` no es un subagente separado. En **OpenCode**, `directora` es el agente primario y coordina **30 subagentes**. Ambas plataformas usan los mismos identificadores y responsabilidades.

## Cómo se reparte un encargo

La ruta es **Dirección → coordinador → especialista**. Dirección selecciona los departamentos necesarios; cada coordinador delega únicamente en sus especialistas. Un especialista devuelve necesidades ajenas a su coordinador; los cruces de departamento regresan a Dirección.

Una edición clara puede seguir una ruta corta. Si faltan criterios de aceptación, Producto ayuda a definirlos a través de su coordinador. Arquitectura interviene cuando hace falta acordar componentes, contratos o dependencias. Las tareas que comparten archivos se ejecutan en secuencia; el paralelismo se reserva para encargos independientes con archivos exclusivos.

Para obtener un plan antes de implementar, puedes pedir:

> Directora, analiza estos requisitos sin cambiar archivos. Pide a Producto y Experiencia que aclare el alcance y a Ingeniería y Datos que identifique dependencias. Dame las fases, el coordinador y especialista responsables, sus entregables y qué puede avanzar en paralelo. Espera mi aprobación antes de implementar.

## Los cinco departamentos

| Departamento y coordinador | Especialistas a su cargo | Cuándo encargarle trabajo |
|---|---|---|
| Producto y Experiencia — `coord-producto-experiencia` | `producto`, `diseno-web`, `ux-accesibilidad`, `seo-growth`, `data-analytics` | Alcance, experiencia, dirección visual web, accesibilidad, búsqueda y métricas de producto. |
| Ingeniería y Datos — `coord-ingenieria-datos` | `arquitectura`, `frontend`, `backend`, `mobile`, `datos-ia`, `integraciones` | Contratos técnicos, cliente, servidor, móvil, pipelines e integración entre sistemas. |
| Calidad y Seguridad — `coord-calidad-seguridad` | `qa`, `seguridad`, `auditoria`, `rendimiento` | Pruebas, regresiones, controles, seguridad y medición del rendimiento. |
| Operaciones y Entrega — `coord-operaciones-entrega` | `devops`, `sre-observabilidad`, `forensics`, `release`, `documentacion` | Plataforma, observabilidad, incidentes, preparación de releases y documentación. |
| Negocio y Gobernanza — `coord-negocio-gobernanza` | `marketing`, `social-contenido`, `finanzas`, `legal`, `experiencia-cliente` | Posicionamiento, contenido, presupuestos, obligaciones y soporte. |

## Qué entrega cada especialista

| Especialista | Entrega esperada |
|---|---|
| `producto` | Problema, objetivo, alcance, exclusiones y criterios de aceptación. |
| `diseno-web` | Estudio de referencias cuando corresponde, contrato de `taste-skill`, tokens, estados, movimiento e imágenes. |
| `ux-accesibilidad` | Recorridos, accesibilidad, problemas priorizados y propuesta de interacción. |
| `seo-growth` | Diagnóstico de indexación y descubrimiento, hipótesis y experimentos medibles. |
| `data-analytics` | Métricas, definición de eventos y análisis con supuestos y fuentes. |
| `arquitectura` | Contratos técnicos, componentes, alternativas, riesgos y dependencias. |
| `frontend` | Componentes, estado, formularios, consumo de APIs y verificaciones del cliente. |
| `backend` | APIs, servicios, persistencia, errores y pruebas relevantes. |
| `mobile` | Flujos móviles, ciclo de vida, capacidades de plataforma y pruebas aplicables. |
| `datos-ia` | Pipelines y evaluación reproducible con privacidad, coste y límites. |
| `integraciones` | Contratos entre sistemas, mapeos y manejo verificable de fallos. |
| `qa` | Casos y resultados reales de prueba, regresiones y pasos para reproducir. |
| `seguridad` | Riesgos técnicos con evidencia y mitigaciones; revisión sin editar producto. |
| `auditoria` | Evaluación independiente de controles, hallazgos y límites de evidencia. |
| `rendimiento` | Mediciones, cuellos de botella y recomendaciones contrastables. |
| `devops` | Preparación de build, CI y plataforma con comandos reproducibles. |
| `sre-observabilidad` | Diagnósticos de fiabilidad, señales, alertas y recuperación propuesta. |
| `forensics` | Evidencia preservada, cronología y análisis de incidentes. |
| `release` | Comprobación de preparación, riesgos y rollback; autorización pendiente antes de producción. |
| `documentacion` | Guías y procedimientos cotejados con el código y comandos disponibles. |
| `marketing` | Audiencia, posicionamiento y mensajes, separando datos de hipótesis. |
| `social-contenido` | Borradores, guiones y calendario por canal. |
| `finanzas` | Presupuestos y escenarios con moneda, periodo, supuestos y fuentes. |
| `legal` | Obligaciones y riesgos, distinguiendo texto contractual e interpretación. |
| `experiencia-cliente` | Recorridos de soporte, onboarding, recuperación y mejoras de ayuda. |

Dirección de arte, movimiento e imágenes se consolidan en `diseno-web`; la automatización de pruebas pertenece a `qa`. Los prompts anteriores bajo `codex/roles/` son material heredado y no definen agentes de esta oficina.

## Ejemplo: diseñar y construir una experiencia web

Dirección encarga a `coord-producto-experiencia` los criterios de Producto, la propuesta de `diseno-web` y la revisión de `ux-accesibilidad`. Para web nueva, landing o rediseño significativo, `diseno-web` investiga entre tres y seis referencias actuales y documenta patrones y decisiones en `reference-study.md`. Usa `taste-skill` como autoridad visual; si falta esa skill o no puede investigar, declara la limitación.

La implementación se encarga después a `coord-ingenieria-datos`: `frontend` sigue el contrato visual y `frontend-developer`; `backend` resuelve el servidor cuando hace falta. `diseno-web` entrega especificaciones en modo de lectura por defecto. No coordina ni invoca otros especialistas.

`coord-calidad-seguridad` organiza las pruebas y revisiones aplicables. Dirección integra los resultados y explica lo comprobado y lo pendiente. Pedir una auditoría no autoriza corregir producto.

## Entregas, gates y permisos

Cada encargo acota objetivo, alcance, exclusiones, criterios de aceptación y riesgos. El handoff incluye contexto, artefactos, evidencia, estado del gate y siguiente acción. Los contratos verificables viven en `office/contracts/`; son formatos de intercambio, no una base de datos de tareas.

Un cambio de funcionalidad requiere gates de producto, implementación y QA; diseño si toca UI y seguridad si toca autenticación, permisos, datos, red, pagos o secretos. Documentación es obligatoria cuando cambia una API, operación, flujo o procedimiento. Los estados de gate son `pending`, `pass`, `fail` y `waived`; `pass` exige evidencia y `waived` requiere aprobación humana documentada. Una auditoría entrega hallazgos y revisión del dominio; no implica implementación. Un incidente prioriza preservar evidencia antes de corregir.

OpenCode emite reglas de permisos por perfil. En Codex, los subagentes heredan herramientas y permisos de la sesión; los límites del prompt no crean aislamiento adicional. Ningún perfil fija modelo o proveedor ni obtiene acceso a una herramienta por mencionarla. Toda carencia de capacidad se declara. Publicación, despliegue, gasto y escrituras externas requieren autorización explícita para la acción.

## Usar los perfiles

En OpenCode, abre el proyecto y selecciona `directora`. Describe el resultado, los archivos o límites conocidos y si pides solo análisis. Dirección aplica la jerarquía; `experimental.subagent_depth = 2` permite sus dos saltos.

En Codex, abre el proyecto con sus instrucciones y perfiles cargados. Habla con el chat principal y pide la ruta por coordinadores, por ejemplo: “Encarga el análisis técnico a `coord-ingenieria-datos` para que consulte a `arquitectura`; no implementes todavía”. Puedes seguir la actividad de los subagentes; no necesitas abrir un chat por especialista. Usar varios consume más recursos que una consulta individual: convoca solo los necesarios.

## Encargos listos para copiar

**Solo planificar:**

> Directora, analiza esta idea con Producto y Experiencia. No cambies archivos. Entrega criterios de aceptación, preguntas pendientes y fases con responsables, entregables y dependencias. Espera mi aprobación.

**Diseñar y construir:**

> Directora, quiero mejorar [función]. Primero pide a Producto y Experiencia los criterios, el flujo y el contrato visual. No implementes hasta que apruebe la propuesta. Después encarga el cliente y servidor a Ingeniería y Datos y la revisión a Calidad y Seguridad.

**Investigar un problema:**

> Directora, investiga [problema] sin modificar archivos. Pide a Negocio y Gobernanza el recorrido de Experiencia del cliente, a Ingeniería y Datos el flujo técnico y a Calidad y Seguridad la reproducción. Reúne evidencia y recomienda el siguiente paso.

## Comprobar el Core

Desde la raíz del kit:

```powershell
pwsh -NoProfile -File scripts/Test-Office.Core.ps1
pwsh -NoProfile -File scripts/Build-Office.ps1 -Platform Both -Check
```

Los nombres heredados `Test-Equipo.ps1` y `Build-Codex-Agents.ps1` delegan al Core y emiten deprecación; no mantienen un segundo roster. El primero admite `-Section`; el segundo conserva generación Codex sin argumentos y añade `-Check`.

La instalación segura en otros proyectos y la migración global están pendientes del plan de instalación. `Install-Equipo.ps1` todavía exige su inventario anterior y no instala el Core actual. Consulta el [README](../README.md) para el alcance local y las verificaciones disponibles.
