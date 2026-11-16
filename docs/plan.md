# Plan: equipo de agentes reutilizable

> Implementación en línea autorizada por la petición del usuario de configurar el equipo en un repositorio.

**Objetivo:** crear un repositorio Git independiente con reglas para Codex, perfiles especialistas para OpenCode e instalación segura en otros repositorios.

**Arquitectura:** Kit versionable con `.opencode/agents/*.md`, `.codex/agents/*.toml`, `AGENTS.md`, prompts fuente de Codex y scripts PowerShell sin dependencias externas. El instalador agrega las reglas comunes como bloque delimitado y copia agentes sin pisar archivos existentes.

**Tecnología:** Markdown, JSONC, PowerShell, Git.

**Diseño:** [`diseno.md`](diseno.md)

## Restricciones

- No editar el proyecto Claw3D ni la app local existente.
- No incluir claves, tokens ni nombres de proveedor/modelo.
- Mantener archivos de usuario al instalar; sobrescritura solo mediante `-Force`.

## Pasos

- [x] Inspeccionar el workspace y confirmar repositorios/cambios existentes.
- [x] Añadir documentación, reglas comunes y diecinueve perfiles de OpenCode (en su momento; hoy veintitrés).
- [x] Añadir prompts de referencia y perfiles Codex invocables para departamentos y especialistas.
- [x] Añadir instalación idempotente y validación local sin dependencias.
- [x] Inicializar Git y validar el inventario/configuración.
- [x] Explicar cómo iniciar el equipo aquí y cómo instalarlo en otro proyecto.
- [x] Incorporar los siete departamentos del TikTok como perfiles OpenCode y subagentes invocables de Codex (en su momento; hoy ocho departamentos).
- [x] Añadir el departamento Diseño Web (skill `taste-skill`): ocho departamentos y catorce especialistas; ver [`diseno-web.md`](diseno-web.md) y [`guia-diseno-web.md`](guia-diseno-web.md).

## Enfoque de revisión

- Agente especialista duplicado o ausente → validador cuenta y exige los IDs requeridos.
- JSONC inválido o modelo fijado por error → validador parsea la configuración y confirma que no hay proveedor/modelo.
- Instalación sobre AGENTS existente → ensayo local confirma que lo conserva y no duplica el bloque.
- Nombre OpenCode en conflicto → ensayo confirma que se detiene sin `-Force`.
- Ruta del objetivo inválida o igual al kit → el instalador debe fallar antes de escribir.
