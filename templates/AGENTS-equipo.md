## Equipo especialista

El agente principal coordina y es responsable del resultado. En Codex, delega a los agentes del proyecto en `.codex/agents/`; sus instrucciones completas también están en `.codex/roles/`. En OpenCode, usa los perfiles de `.opencode/agents/`. Usa solo los perfiles necesarios; las tareas que comparten archivos van en secuencia. Todo agente debe informar cambios y verificaciones, no asumir que algo está probado.

Departamentos: `desarrollo`, `diseno`, `diseno-web`, `marketing`, `social-contenido`, `finanzas`, `operaciones` y `legal`.

Especialistas: `producto`, `arquitectura`, `ux-web`, `frontend-web`, `direccion-arte`, `movimiento`, `imagenes`, `backend`, `calidad`, `seguridad`, `plataforma-devops`, `datos-ia`, `documentacion` y `experiencia-cliente`.

### Diseño Web (`diseno-web`)

Todo encargo de web e interfaces va a `diseno-web`, que coordina el departamento Diseño Web con la skill `taste-skill` instalada globalmente: `direccion-arte` (perfiles/tokens/estética) → `ux-web` (flujo, estados, responsive, accesibilidad) + `movimiento` ∥ `imagenes` → `frontend-web` (implementación y auditor) → `diseno-web` firma el DoD. Los encargos de diseño no digital van a `diseno`. Antes de cualquier entrega visual, el agente correspondiente invoca y sigue la skill `taste-skill`; si no está instalada, lo declara y se detiene.
