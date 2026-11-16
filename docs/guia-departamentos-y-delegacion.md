# Guía para trabajar con los departamentos y agentes

La oficina tiene una directora que coordina el trabajo, ocho responsables de departamento y catorce especialistas. No tienes que escoger todos los agentes: empieza con la **Directora** y pídele que proponga quién hace falta. Convoca departamentos o especialistas directamente cuando ya sepas qué necesitas.

## Quién analiza el encargo y decide a quién delegar

Sí existe una coordinadora para eso: **Directora** (`directora` en OpenCode; agente principal en Codex). Su perfil pide aclarar el resultado, identificar riesgos, definir pasos verificables, delegar tareas acotadas e integrar las respuestas.

Para requisitos de producto, la Directora puede pedir apoyo a **Producto** (`producto`). Producto convierte tu idea en problema, objetivo, alcance, exclusiones, casos límite y criterios de aceptación. Para ordenar dependencias técnicas, consulta a **Arquitectura** (`arquitectura`). En conjunto:

1. **Producto** aclara qué hay que resolver y cómo sabremos que quedó bien.
2. **Arquitectura** identifica dependencias y el orden técnico, si hay cambios de software.
3. **La Directora** propone fases, asigna cada fase al agente adecuado e indica qué puede avanzar en paralelo.
4. **Tú revisas el plan** y aclaras o apruebas los pasos que quieras encargar.
5. **Los agentes asignados** entregan análisis o cambios concretos.
6. **Calidad** revisa el resultado; **Seguridad** participa si hay cuentas, datos, permisos, pagos o conexiones.
7. **La Directora** reúne los resultados y te explica qué se hizo y qué queda pendiente.

No hay un agente separado llamado “analista de delegación”: ese trabajo corresponde a la Directora. Para que primero te dé un plan y no empiece a ejecutar, indícalo de forma explícita:

> **Antes de cambiar archivos, analiza estos requisitos. Consulta a Producto para aclarar el alcance. Después dime, paso por paso, qué agente debe intervenir, qué entregable le asignarías, de qué depende su tarea y qué se puede hacer en paralelo. Señala dudas y espera mi aprobación antes de implementar.**

La secuencia cambia según el encargo. Una campaña no necesita Backend; una pantalla no necesita Finanzas. Pide solo las revisiones que aporten valor.

## Qué hace cada departamento

| Departamento | Úsalo para | Compañeros habituales | Ejemplo de encargo |
|---|---|---|---|
| **Desarrollo** (`desarrollo`) | Planear e implementar cambios técnicos en una aplicación. | Arquitectura, Frontend Web, Backend, Calidad, Seguridad, Plataforma/DevOps, Datos e IA, Documentación. | "Implementa el inicio de sesión. Primero revisa la arquitectura y propón el orden de trabajo; no despliegues." |
| **Diseño** (`diseno`) | Diseñar diseño no digital: marca, identidad, editorial impreso, materiales y sistemas visuales offline. | Marketing y Producto. Las interfaces web delegan en **Diseño Web**. | "Diseña la identidad para el lanzamiento. Revisa primero la marca existente; no toques la interfaz web." |
| **Diseño Web** (`diseno-web`) | Web e interfaces con dirección de arte verificable (skill `taste-skill`): landing, dashboard, e-commerce, portfolio, app, sistema de diseño web. | Dirección de Arte, UX Web, Movimiento, Imágenes, Frontend Web, Producto. | "Rediseña el hero de la landing. Empieza por el contrato de taste-skill; deja la implementación para después de mi aprobación." |
| **Marketing** (`marketing`) | Investigar audiencia y posicionamiento, preparar mensajes, SEO y experimentos de conversión. | Social y Contenido, Producto y Datos e IA. | “Propón cómo presentar el Help Desk a pequeñas empresas. Separa datos comprobados de hipótesis.” |
| **Social y Contenido** (`social-contenido`) | Preparar calendario, guiones, publicaciones y piezas editoriales por canal. | Marketing y Diseño. | “Crea una semana de publicaciones para presentar el producto; entrega borradores y no publiques nada.” |
| **Finanzas** (`finanzas`) | Preparar presupuestos, precios, proyecciones y escenarios financieros. | Datos e IA y Producto. | “Compara tres precios mensuales. Expón moneda, periodo, supuestos y datos que faltan.” |
| **Operaciones** (`operaciones`) | Mejorar procesos internos, procedimientos, responsables y métricas; evaluar automatizaciones. | Experiencia del cliente, Plataforma/DevOps, Seguridad y Documentación. | “Mapea cómo atendemos un reporte de error y señala dónde conviene automatizar sin perder controles.” |
| **Legal** (`legal`) | Revisar contratos, obligaciones, riesgos y documentación de cumplimiento. | Seguridad, Producto y Documentación. | “Resume las obligaciones y riesgos de este contrato; separa lo que dice el texto de lo que estás interpretando.” |

Los departamentos coordinan el trabajo de su área; no reemplazan la aprobación humana. En particular, pide borradores para campañas y documentos legales. No delegues a un agente que publique, firme, pague o cambie cuentas externas.

Finanzas y Legal no tienen un segundo subespecialista dentro del equipo actual: sus responsables hacen el análisis inicial. Puedes pedir a Datos e IA que revise cálculos o fuentes, y a Seguridad o Documentación que apoyen en riesgos técnicos y registros, respectivamente.

## Qué especialista conviene convocar

| Especialista | Convócalo cuando quieras… | Lo que debe entregarte |
|---|---|---|
| **Producto** (`producto`) | Analizar una necesidad, ordenar requisitos o definir qué significa “terminado”. | Objetivo, alcance, exclusiones, casos límite y criterios de aceptación. |
| **Arquitectura** (`arquitectura`) | Entender cómo encaja un cambio en el sistema o qué dependencias tiene. | Componentes afectados, opciones, riesgos y orden técnico sugerido. |
| **Dirección de Arte** (`direccion-arte`) | Elegir perfil, escala tipográfica, tokens y estética de una web. | PERFIL/ESCALA/ESTÉTICA del contrato de `taste-skill`, tokens y dirección de arte; veto sobre escala y estética. |
| **UX Web** (`ux-web`) | Revisar o diseñar tareas del usuario, navegación, accesibilidad y estados de pantalla web. | Flujo, problemas priorizados y propuesta de interacción; no implementa por defecto. |
| **Movimiento** (`movimiento`) | Decidir y aplicar animaciones, transiciones y coreografías web. | Niveles 0–3, duraciones, `prefers-reduced-motion` y coreografía nombrada. |
| **Imágenes** (`imagenes`) | Tratar, proporcionar y optimizar medios (fotos, ilustración, generadas, iconografía). | 4 decisiones por medio, `<picture>`, presupuesto LCP y revisión de imágenes generadas. |
| **Frontend Web** (`frontend-web`) | Construir o corregir la interfaz web acordada. | Cambios de interfaz en los archivos asignados con auditor `audit_taste.py` en verde. |
| **Backend** (`backend`) | Construir APIs, servicios, persistencia o integraciones de servidor. | Cambios de servidor, contratos, manejo de errores y verificaciones. |
| **Calidad** (`calidad`) | Buscar errores, regresiones y casos límite en un cambio. | Hallazgos priorizados, pasos para reproducir y qué no pudo verificarse. |
| **Seguridad** (`seguridad`) | Revisar autenticación, permisos, secretos, datos sensibles y superficies de red. | Riesgos con evidencia y mitigaciones concretas. |
| **Plataforma/DevOps** (`plataforma-devops`) | Revisar builds, CI, configuración, despliegues, logs y recuperación. | Comandos y cambios reproducibles, observabilidad y riesgos; no despliega por defecto. |
| **Datos e IA** (`datos-ia`) | Diseñar procesamiento de datos, evaluación de modelos o integraciones de IA. | Enfoque reproducible con privacidad, coste y alternativa de respaldo. |
| **Documentación** (`documentacion`) | Crear o actualizar guías técnicas y de uso. | Instrucciones cotejadas con el código y los comandos disponibles. |
| **Experiencia del cliente** (`experiencia-cliente`) | Revisar onboarding, soporte, errores y recuperación desde el punto de vista del usuario. | Pasos confusos, mensajes y mejoras de ayuda o soporte. |

### Ejemplo: diseñar una experiencia web

Para definir cómo se usa una función web, encarga el trabajo a **Diseño Web** y pídele que coordine al departamento. Su coordinadora `diseno-web` emite el contrato de `taste-skill` (perfil, escala, estética, movimiento e imagen) y reparte: **Dirección de Arte** fija tokens y escala; **UX Web** analiza el recorrido, los estados vacíos, cargando y error, la accesibilidad y el lenguaje; **Movimiento** e **Imágenes** definen la coreografía y los medios; **Frontend Web** implementa con el auditor en verde. Reúne eso en una propuesta de flujo y pantallas. Cuando apruebes la propuesta, se implementa y después **Calidad** comprueba los casos importantes.

Si solo quieres una auditoría de una pantalla existente, puedes convocar directamente a `ux-web`. Si quieres que aparezca implementada en la aplicación, aclara que autorizas también la fase de Frontend Web.

## Cómo usar los agentes en cada herramienta

### OpenCode

1. Abre el proyecto correcto y elige **Directora** como agente principal.
2. Describe el resultado que buscas y cualquier límite: “solo analizar”, “no modificar archivos” o “espera mi aprobación”.
3. Si ya sabes qué perfil quieres, selecciónalo en el menú de agentes o menciónalo por su nombre, por ejemplo `@producto` o `@ux-web`.
4. Revisa el plan y los cambios antes de continuar.

### Codex

1. Abre el mismo proyecto y crea una sesión nueva para que cargue sus instrucciones y perfiles.
2. El chat principal de Codex cumple el papel de **Directora**; no busques `directora` como perfil separado. Los perfiles de departamento y especialistas son subagentes, no chats para abrir desde el selector.
3. Escribe a Codex como coordinador principal. Pídele que use subagentes por nombre, por ejemplo: “Delega el análisis de requisitos a `producto` y la revisión técnica a `arquitectura`; no implementes todavía”.
4. Para tareas independientes, especifica que las ejecute en paralelo. Si dos tareas tocarían los mismos archivos, pide que las haga en secuencia.
5. Revisa los resultados de los subagentes en el panel de actividad y pide a Codex un resumen integrado.

Los agentes de Codex heredan el modelo y los permisos de la sesión principal. Usar varios puede consumir más tiempo y uso del modelo que una consulta individual.

## Tres encargos listos para copiar

**Solo planificar:**

> Directora, analiza esta idea con Producto. No cambies archivos. Dame requisitos, preguntas pendientes y un plan por fases con el agente, el entregable y las dependencias de cada fase. Espera mi aprobación.

**Diseñar y luego construir:**

> Directora, quiero mejorar [función]. Primero pide a Producto que defina criterios de aceptación; luego a Diseño Web que proponga el flujo y el contrato visual. No implementes hasta que yo apruebe el diseño. Después, si lo apruebo, divide la implementación entre Frontend Web y Backend y pide una revisión a Calidad.

**Revisar un problema existente:**

> Directora, investiga [problema] sin modificar archivos. Pide a Experiencia del cliente que describa el recorrido del usuario, a Arquitectura que localice el flujo técnico y a Calidad que proponga cómo reproducirlo. Después reúne evidencia y recomiéndame el siguiente paso.

## Qué esperar de un buen resultado

El agente debe indicar qué revisó, qué entregó, qué verificó y qué quedó pendiente. Si su plan depende de una decisión tuya, debe detenerse y preguntarte. Los agentes no trabajan continuamente fuera de la sesión ni sustituyen tu aprobación para publicar, desplegar, firmar o gastar dinero.
