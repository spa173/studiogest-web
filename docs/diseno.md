# Diseño: kit reutilizable de equipo para Codex y OpenCode

## Intención

Reemplazar la oficina visual autónoma que el usuario decidió cancelar por un equipo de agentes que trabaje con él dentro de los repositorios de software, usando Codex para coordinar y OpenCode para perfiles persistentes.

## Objetivos

- Mantener a una directora, ocho responsables de departamento y catorce especialistas con instrucciones en español.
- Compartir reglas de trabajo con herramientas que leen `AGENTS.md`.
- Permitir instalar los perfiles OpenCode en cualquier repositorio sin destruir archivos existentes.
- No depender de un modelo, proveedor, clave, servicio local o aplicación externa concretos.
- Explicar el uso desde una conversación y cómo verificar lo instalado.

## Fuera de alcance

- Crear avatares 3D, procesos que trabajen en segundo plano o un sistema de empleados autónomos.
- Elegir modelo, configurar claves, pagar servicios, desplegar o enviar mensajes a terceros.
- Alterar el código de Claw3D u otros proyectos para habilitar esta configuración.

## Enfoques considerados

1. **Configuración global en el equipo:** disponible en todos los proyectos, pero acoplada a una sola máquina y difícil de compartir/versionar.
2. **Incrustar los perfiles directamente en Claw3D:** cómodo para ese proyecto, pero mezcla el kit reutilizable con un producto que el usuario dijo que quiere cancelar.
3. **Repositorio independiente con instalador (elegido):** mantiene instrucciones y perfiles versionables en un lugar; el usuario los aplica a los repositorios de trabajo, preservando sus reglas y configuraciones.

## Decisiones

- La directora de OpenCode es agente principal predeterminado; los responsables de departamento y los especialistas son subagentes.
- No se especifica el campo `model`: cada perfil hereda el modelo activo de la sesión.
- Codex recibe reglas compartidas en `AGENTS.md` y prompts reutilizables por rol; la disponibilidad de delegación depende de la sesión de Codex.
- El instalador respeta los archivos existentes, no imprime secretos y requiere `-Force` para reemplazar un perfil con el mismo nombre.
- La persona usuaria conserva el control de tareas, cambios y acciones externas.

## Criterios de aceptación

- El kit existe como repositorio Git independiente.
- OpenCode descubre la directora, los ocho responsables de departamento y los catorce perfiles especialistas.
- El instalador es idempotente para las reglas comunes, conserva AGENTS existente y se niega a sobrescribir agentes sin `-Force`.
- Un script local valida configuración, nombres y perfiles.
- La guía explica tanto el primer uso como su instalación en otro proyecto.
