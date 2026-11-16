<!-- oficina-unificada:inicio -->
<!-- GENERATED: DO NOT EDIT THIS BLOCK. Sources: office/registry.json; office/roles/directora.md; templates/AGENTS-oficina.md. Run scripts/Build-Office.ps1 -Platform Codex. -->

## Oficina unificada en Codex

El chat principal ejerce la Dirección; `directora` no es un subagente Codex. Los treinta perfiles en `.codex/agents/` contienen cinco coordinadores y veinticinco especialistas, generados desde `office/registry.json` y `office/roles/`.

Aplica las rutas de delegación de los prompts canónicos. Estas instrucciones expresan responsabilidades y límites de trabajo; el sandbox, las aprobaciones y los permisos efectivos dependen del entorno y de la autorización del usuario. Un perfil no concede acceso a conectores, secretos o servicios. Hereda el modelo y proveedor de la sesión.

{{DIRECTOR_PROMPT}}

<!-- oficina-unificada:fin -->
