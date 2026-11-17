# Sistema de movimiento

El movimiento es **información**: dice de dónde viene algo, qué cambió y qué es lo importante. Si no informa, se elimina. Esa es toda la teoría.

## Los 4 niveles

| Nivel | Qué cubre | Perfiles | Presupuesto |
|---|---|---|---|
| **0 — Estático** | Nada. Solo estados instantáneos. | 1 (paneles), 4 (lectura) | 0ms |
| **1 — Feedback** | hover, press, foco, check, toggle | Todos | 80–140ms |
| **2 — Estado** | dropdown, accordion, modal, drawer, tabs, toast, cambio de tema | 1, 2, 5 | 140–320ms |
| **3 — Coreografía** | entrada de sección, hero, transición de página, elemento compartido | 2, 3, 5 | ≤500ms, **1 por vista** |

Un producto de Perfil 1 usa niveles 0–2. Una landing de Perfil 3 puede usar 3, pero **una sola vez** por página. Si dudas entre nivel 2 y 3, es 2.

---

## Tokens

```css
:root{
  /* Duraciones — la escala completa. No inventes valores intermedios. */
  --dur-1: 80ms;    /* press, cambio de icono */
  --dur-2: 140ms;   /* hover, tooltip, color de borde */
  --dur-3: 200ms;   /* accordion, tabs, dropdown */
  --dur-4: 320ms;   /* modal, drawer, cambio de página */
  --dur-5: 500ms;   /* entrada hero — techo absoluto */

  /* Easing — 4 curvas, nada más */
  --ease-out:    cubic-bezier(.16, 1, .3, 1);     /* entradas: rápido, frena suave */
  --ease-in:     cubic-bezier(.3, 0, .8, .15);    /* salidas: arranca suave, acelera */
  --ease-inout:  cubic-bezier(.65, 0, .35, 1);    /* movimientos entre dos puntos */
  --ease-std:    cubic-bezier(.2, 0, 0, 1);       /* color, opacidad, foco */

  /* Resorte — solo Perfiles 3 y 5, nunca en datos ni en acciones destructivas */
  --ease-spring: linear(0, .009, .035 2.1%, .141, .281 6.7%, .723 12.9%, .938 16.7%,
                        1.017, 1.077, 1.121, 1.149 24.3%, 1.159 1.163 27.4%, 1.161,
                        1.154 29.9%, 1.129 32.8%, 1.051 39.6%, 1.017 43.1%, .991,
                        .977 51%, .974 53.8%, .975 57.1%, .997 69.8%, 1.003 76.9%, 1);

  /* Distancias — el ojo detecta el desplazamiento, no la duración */
  --move-xs: 4px;   /* tooltip, badge */
  --move-sm: 8px;   /* modal, toast, dropdown */
  --move-md: 16px;  /* card, item de lista */
  --move-lg: 32px;  /* reveal de sección (máximo) */
}
```

**Regla de salida:** toda salida dura **70% de su entrada** y usa `--ease-in`. Un modal que entra en 320ms sale en 220ms. Ir y volver en el mismo tiempo se siente pesado y es el error más común de las interfaces generadas por IA.

---

## Tabla de decisión: interacción → valores

| Interacción | Duración | Easing | Propiedad / distancia |
|---|---|---|---|
| Cambio de color, borde, fondo | `--dur-2` | `--ease-std` | `background-color`, `border-color`, `color` |
| Press de botón | `--dur-1` | `--ease-out` | `scale(.97)` |
| Hover de card | `--dur-2` | `--ease-out` | `translateY(-2px)` o `border-color` |
| Tooltip | 120 / 80 | `--ease-out` | `opacity` + `translateY(var(--move-xs))` |
| Checkbox / switch | `--dur-2` | `--ease-inout` | `transform` del pulgar, `opacity` del check |
| Dropdown / select / popover | 160 / 110 | out / in | `opacity` + `translateY(-4px)` + `scale(.98)` |
| Accordion | `--dur-3` / 140 | `--ease-inout` | `grid-template-rows: 0fr → 1fr` |
| Tabs | `--dur-2` | `--ease-out` | `opacity` (y el indicador con `translateX`) |
| Modal | 240 / 180 | out / in | `opacity` + `scale(.96 → 1)` + `translateY(8px)`; backdrop 200ms |
| Drawer lateral | 280 / 200 | out / in | `translateX(100% → 0)` |
| Toast | `--dur-3` / 140 | out / in | `translateY(12px)` + `opacity` |
| Cambio de página (View Transitions) | 220 (old) / 320 (new) | in / out | crossfade + `translateY(8px)` |
| Reveal de sección (scroll) | atado al scroll | `linear` | `opacity` + `translateY(≤32px)` |
| Skeleton | loop 1400ms | `linear` | `opacity` entre .4 y .7 (**nunca** `background-position`: repinta) |
| Stagger entre items | paso de 40–60ms | — | máx. 6 items → techo total 400ms |

---

## Los 6 verbos del movimiento

1. **Feedback** (nivel 1). Todo elemento interactivo responde en <100ms al press. Sin esto la interfaz se siente muerta, aunque tenga animaciones bonitas.
2. **Entrada** (nivel 2–3). Elemento nuevo: `opacity 0→1` + desplazamiento ≤32px. Dirección coherente con el origen (si viene de abajo, entra desde abajo).
3. **Salida** (nivel 2). Más rápida, dirección inversa, y **el elemento desaparece del DOM al terminar** (`animationend` o `transitionend`, no `setTimeout` a ojo).
4. **Cambio de estado** (nivel 2). Misma familia de propiedades: un spinner no salta de tamaño, un botón que pasa a "Añadido ✓" mantiene el ancho (min-width fijo o `content-visibility`).
5. **Cambio de contexto** (nivel 3). Página/pantalla nueva: View Transitions. Marca continuidad con `view-transition-name` en 1 o 2 elementos como máximo.
6. **Continuidad** (nivel 3). Elemento compartido que viaja entre estados (miniatura → detalle). Es el efecto con más retorno perceptivo por línea de código, y el más fácil de estropear: solo uno por flujo.

---

## Recetas listas para pegar

### Reveal al scroll (con fallback real)

Scroll-driven animations están en Chrome/Edge 115+, Safari 26+, y **en Firefox estable todavía no** (flag en `about:config`). Baseline: disponibilidad limitada → trátalo como mejora, nunca como requisito.

```css
/* Estado por defecto = visible. El usuario sin soporte ve el contenido, no un hueco. */
.reveal { opacity: 1; }

@media (prefers-reduced-motion: no-preference) {
  @supports (animation-timeline: view()) {
    .reveal {
      animation: reveal-in linear both;      /* el shorthand va PRIMERO */
      animation-timeline: view();            /* animation-timeline DESPUÉS, o se resetea */
      animation-range: entry 10% cover 30%;
    }
  }
}

@keyframes reveal-in {
  from { opacity: 0; translate: 0 32px; }
  to   { opacity: 1; translate: 0 0; }
}
```

> El error clásico: escribir `animation-timeline` antes de `animation:` — el shorthand resetea la timeline y la animación corre por tiempo. Ese bug es invisible en revisión y evidente en producción.

Limitación que debes conocer: el scroll-driven puro **no puede "pinnear"** contenido; la animación se rebobina al subir. Si el cliente pide pin/hold, es JS (GSAP ScrollTrigger).

### Entrada de modal y popover con `@starting-style`

El patrón moderno, sin JS de clases ni `setTimeout`:

```css
dialog, [popover] {
  opacity: 1; scale: 1;
  transition: opacity var(--dur-4) var(--ease-out), scale var(--dur-4) var(--ease-out),
              overlay var(--dur-4) allow-discrete, display var(--dur-4) allow-discrete;
}
@starting-style {
  dialog[open], [popover]:popover-open { opacity: 0; scale: .96; }
}
dialog::backdrop { transition: opacity var(--dur-4) var(--ease-out), overlay var(--dur-4) allow-discrete, display var(--dur-4) allow-discrete; }
@starting-style { dialog[open]::backdrop { opacity: 0; } }
```

Usa `<dialog>` y `popover` nativos: te dan foco atrapado, `Esc` y capa superior gratis. Reimplementarlos con `div` es la causa nº1 de modales inaccesibles.

### Accordion sin `height: auto`

```css
.acc-panel { display: grid; grid-template-rows: 0fr; transition: grid-template-rows var(--dur-3) var(--ease-inout); }
.acc-panel > * { overflow: hidden; }
.acc[open] .acc-panel { grid-template-rows: 1fr; }
/* Alternativa 2026: */ .acc-panel { height: 0; interpolate-size: allow-keywords; transition: height var(--dur-3) var(--ease-inout); }
```

### Transición de página

```css
@view-transition { navigation: auto; }              /* multi-página, cero JS */
::view-transition-old(root) { animation: fade-out 220ms var(--ease-in) both; }
::view-transition-new(root) { animation: fade-in  320ms var(--ease-out) both; }
/* elemento compartido: */ .thumb { view-transition-name: hero-img; }
```

Reglas: máximo 2 `view-transition-name` a la vez (cada uno cuesta memoria y complejidad), y no marques contenedores grandes con imágenes pesadas — el snapshot provoca jank.

### Stagger (solo con JS, y solo nivel 3)

```js
const items = [...document.querySelectorAll('.stagger > *')].slice(0, 6);
items.forEach((el, i) => {
  el.animate(
    [{ opacity: 0, transform: 'translateY(16px)' }, { opacity: 1, transform: 'none' }],
    { duration: 400, delay: i * 50, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'both' }
  );
});
```

CSS puro no puede escalonar sobre una timeline: si intentas `animation-delay` por `:nth-child` en 20 elementos, el techo total se dispara y el usuario espera. Máximo 6 elementos con stagger.

---

## `prefers-reduced-motion` — implementación real

No es "poner 0.01ms a todo". Es distinguir **movimiento** (que daña) de **cambio de estado** (que informa).

```css
@media (prefers-reduced-motion: reduce) {
  /* Suelo de seguridad */
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
    scroll-behavior: auto !important;
  }
  /* Excepciones curadas: los fades de opacidad se conservan, cortos */
  .fade-only { transition-duration: 100ms !important; }

  /* Se elimina de verdad */
  .parallax, .reveal { transform: none !important; opacity: 1 !important; }
  video[autoplay], .autoplay-bg { display: none !important; }
  .hero-mask * { clip-path: none !important; transform: none !important; }
}
```

```js
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
const safeAnimate = (el, kf, opts = {}) =>
  el.animate(kf, reduce.matches ? { duration: 1, ...opts } : opts);
reduce.addEventListener('change', () => location.reload()); // o re-evaluar el estado
```

Elimina siempre bajo `reduce`: parallax, zoom lento de fondo, autoplay de video, marquesinas, seguimiento de cursor, `clip-path` animados, typewriter, y desplazamientos > 8px.

---

## Rendimiento e INP

- Anima **solo** `transform`, `opacity`, `filter`. Todo lo demás (width, height, top, left, margin, box-shadow, border-radius, background-position) provoca layout o repaint en el hilo principal.
- `will-change` solo en el elemento que va a animar y solo durante la animación. Nunca `* { will-change: transform }`.
- No animes mientras el usuario hace scroll continuo si puedes usar scroll-driven (va en el compositor, hilo principal libre).
- El **elemento LCP nunca se anima desde `opacity: 0`**: retrasa el paint y empeora LCP. El hero se pinta completo; se anima lo de al lado.
- Feedback de interacción en <100ms, siempre. Si el handler tarda más, muestra el estado de carga antes de hacer el trabajo.
- Presupuesto de JS de movimiento: **<20KB gz** en total. Si un efecto obliga a una librería de 60KB, el efecto no vale.

## Cuándo usar librería (y cuándo no)

| Necesitas | Solución | Peso |
|---|---|---|
| Hover, foco, color, press | CSS `transition` | 0 |
| Entrada/salida de overlays | `@starting-style` + `<dialog>`/`popover` | 0 |
| Reveal al scroll, barra de progreso, parallax suave | `animation-timeline` + `@supports` | 0 |
| Transición de página o elemento compartido | View Transitions | 0 |
| Timeline con control (play/pause/reverse), scrub, pin, pinning de secciones | **GSAP ScrollTrigger** | ~25–50KB |
| Orquestación compleja en React (layout animations, `AnimatePresence`, gestos de arrastre) | **Motion (Framer Motion)** | ~30KB |
| Resorte físico real en muchos elementos | WAAPI + `linear()` antes que librería | 0 |

Regla: **primero nativo, luego librería, y nunca dos librerías de animación en el mismo proyecto.**

## Prohibiciones

Typewriter en el titular · contadores animados de cifras · marquesina infinita de texto · cursor personalizado que sigue el mouse · tilt 3D en cada card · parallax en móvil · animación de entrada en cada sección · loop infinito en elementos de fondo · animar `box-shadow` o `filter: blur` en áreas grandes · spinner genérico sin contexto en lugar de skeleton · animación de más de 500ms en cualquier acción · movimiento sin `reduce`.

## Checklist

- [ ] Solo `transform/opacity/filter`.
- [ ] Duraciones de la tabla de tokens, salidas al 70%.
- [ ] Un solo momento de nivel 3 por vista.
- [ ] `reduce` implementado y probado (activando la preferencia en el sistema, no leyendo el CSS).
- [ ] Nada animado en el elemento LCP.
- [ ] Estados `loading / empty / error` con transición, no con salto.
- [ ] `@supports` en todo lo scroll-driven, y el estado por defecto es "visible".
- [ ] Sin librería si el nativo alcanza.
