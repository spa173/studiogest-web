---
name: frontend-developer
description: Arquitectura e ingeniería de aplicaciones frontend en React/Next.js, Vue o Svelte — estructura de carpetas, estado, fetching y caché, formularios, validación, rutas, testing, manejo de errores, rendimiento de build y accesibilidad semántica. Úsala cuando haya que decidir arquitectura de una app, crear o refactorizar componentes con lógica, conectar APIs, gestionar estado o caché, escribir tests, configurar el build/bundler, o resolver problemas de rendimiento y errores en tiempo de ejecución. No define tipografía, color, espaciado ni movimiento: eso es responsabilidad de la skill de diseño (taste-skill).
license: MIT
---

# Frontend Developer — arquitectura, estado y datos

Esta skill responde **cómo se construye**. No responde **cómo se ve**: para jerarquía visual, escalas, tokens y movimiento existe `taste-skill`, que es la única fuente de verdad estética. Si te piden "que se vea mejor", delega; si te piden "que funcione mejor", es aquí.

## Límites explícitos (evita el choque entre skills)

| Pregunta | Skill |
|---|---|
| ¿Qué escala tipográfica, color, espaciado, sombra? | `taste-skill` |
| ¿Qué animación y cuánto dura? | `taste-skill` |
| ¿Qué proporción tiene la grilla de fotos? | `taste-skill` |
| ¿Cómo estructuro carpetas, rutas y capas? | **aquí** |
| ¿Cómo cargo y cacheo datos? | **aquí** |
| ¿Dónde vive el estado? | **aquí** |
| ¿Cómo testeo y qué cubro? | **aquí** |

Regla: **no redefinas valores visuales aquí.** Si necesitas uno, se pide a `taste-skill` como token.

## 1. Estructura por feature, no por tipo

```
src/
  app/            # rutas (framework-first)
  features/<dominio>/
    components/   # UI del dominio
    hooks/        # estado y efectos del dominio
    api/          # fetch + esquemas + mapeo
    model/        # tipos, validación, reglas
  shared/
    ui/           # primitivos sin lógica de negocio (botón, input) — con tokens de taste-skill
    lib/          # utilidades puras
    config/       # env, constantes
```
Prohibido: `components/`, `hooks/`, `utils/` globales como vertedero. Si una carpeta tiene 40 archivos sin dominio, la arquitectura falló.

## 2. Estado: elige la capa mínima

| Tipo de estado | Dónde |
|---|---|
| Servidor (datos remotos) | Query cache (TanStack Query / SWR / RSC). **No** lo copies a `useState`. |
| Formulario | Estado local del form + librería de validación |
| UI efímero (abierto/cerrado, hover, tab) | `useState` local, lo más cerca posible del consumidor |
| Global de cliente (tema, sesión, carrito) | Context + reducer o store mínimo (Zustand). Uno, no tres. |
| URL (filtros, paginación, búsqueda) | **La URL** siempre que se pueda compartir o recargar |

Regla: si un estado puede vivir en la URL o en la caché del servidor, no lo pongas en un store global. El estado global es deuda.

## 3. Datos

- Un único cliente HTTP con `baseURL`, timeout, reintentos con backoff (solo en idempotentes) y manejo de 401/403 centralizado.
- **Valida en el borde**: el JSON de la API se parsea con Zod/Valibot al entrar. Nunca confíes en el tipo declarado.
- Toda consulta declara: clave estable, `staleTime`, política de revalidación y comportamiento en error.
- Muta → invalida o actualiza la caché de forma explícita. Nada de refetch masivo.
- `loading / error / empty / success` son cuatro estados reales y se renderizan distinto. Un `if (loading) return null` es un bug de UX.
- Paginación por cursor antes que por offset en listas grandes.

## 4. Componentes

- **Presentacional vs. contenedor** separados; el primitivo de UI no hace fetch.
- Props explícitas; prohibido pasar objetos gigantes "por si acaso".
- Composición antes que configuración: si un componente tiene 12 booleanos, son 6 componentes.
- Cero lógica de negocio en el JSX: se extrae a un hook o a una función pura y se testea.
- `key` estable y semántica (id, no índice) en listas que cambian.
- Manejo de errores por frontera: `error.tsx` / `ErrorBoundary` por ruta + mensaje accionable.

## 5. Formularios

Esquema único de validación compartido cliente/servidor (Zod). Validación al `blur` y al enviar, nunca por tecla. Errores asociados al campo (`aria-describedby`, `aria-invalid`). Estado de envío explícito; doble submit imposible (`isSubmitting` + deshabilitar). Autocompletado (`autocomplete`) correcto.

## 6. Rendimiento de build y runtime

- Presupuesto: JS inicial < 200KB gz; cualquier cosa mayor, justificada.
- Divide por ruta; carga por interacción lo que dependa de interacción (mapas, editores, chat, gráficos pesados).
- Server Components / SSR para el primer render de contenido; islas de cliente solo donde hay interacción.
- Evita re-render en cascada: memoiza lo medido (no por reflejo), estado lo más bajo posible, selectores estrechos en stores.
- Tareas largas: divide en chunks < 50ms, `scheduler.yield()` antes de trabajo pesado (protege INP).
- Mide con datos reales (RUM) antes de optimizar. Lighthouse es una pista, no un objetivo.

## 7. Testing

| Nivel | Qué cubre | Herramienta |
|---|---|---|
| Unitario | Funciones puras, mapeo de datos, validaciones | Vitest/Jest |
| Componente | Interacción y estados, con queries por rol | Testing Library |
| E2E | 3–5 flujos críticos (login, compra, alta) | Playwright |
| Contrato | Forma de la respuesta de API | Zod + MSW |

Prioriza lo que rompe dinero: checkout, autenticación, creación de entidades. Evita tests de implementación (clases, `data-testid` cuando existe rol accesible).

## 8. Accesibilidad estructural (semántica, no estética)

- HTML correcto primero: `button` para acciones, `a` para navegación, `label` para campos, landmarks.
- Foco gestionado en transiciones de ruta y overlays (devolver al disparador).
- Formularios y errores anunciados (`role="alert"`, `aria-live`).
- La estética del foco la define `taste-skill`; aquí se garantiza que **exista** y siga el orden correcto.

## 9. Entrega

Antes de dar por terminado: tipos sin `any` en el borde de la API · estados de error y vacío implementados · tests del flujo crítico en verde · presupuesto de bundle medido · sin `console.log` · env documentado (nombres, nunca valores).
