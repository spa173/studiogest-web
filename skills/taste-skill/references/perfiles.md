# Perfiles, escalas y tokens

Cinco perfiles. Se elige **uno** por superficie. Un proyecto puede tener dos (landing comercial = 3, dashboard = 1): se declaran ambos y no se mezclan tokens en la misma vista.

## Árbol de decisión

1. ¿El usuario **opera** un producto con datos, filtros, tablas, sesión y tareas repetidas? → **Perfil 1**
2. ¿Hay **precio, catálogo o carrito**, o es una web institucional de varias páginas con jerarquía comercial? → **Perfil 2**
3. ¿Es **una sola página** cuyo trabajo es persuadir o impresionar (headline, prueba, CTA, portfolio)? → **Perfil 3**
4. ¿El valor está en **leer texto largo** (artículo, ensayo, newsletter, documentación)? → **Perfil 4**
5. ¿Se usa sobre todo con el **pulgar**, en menos de 768px, con gestos y transiciones entre pantallas? → **Perfil 5**

Empates:
- "Hazme la web de un SaaS" → la **landing** es Perfil 3 (con capturas reales de UI), el **producto** es Perfil 1. Pregunta si no está claro y declara ambos.
- "Portfolio que además vende prints" → Perfil 3 dominante; el checkout hereda Perfil 2 solo en el flujo de compra.
- "Blog corporativo" → Perfil 4 para el artículo, Perfil 2 para el índice comercial.

---

## Perfil 1 — SaaS app, dashboard, finanzas

**Trabajo del diseño:** que el operador lea datos rápido, sin errores y sin fatiga. La densidad es una función, no un defecto. La estética es consecuencia de la precisión.

### Escala doble (la clave del perfil)

Una sola escala no sirve: necesitas **densidad** para la UI y **jerarquía** para la página.

```
/* densidad — Segunda Menor 1.067 · base 14px */
--fs-2xs: 0.6875rem;  /* 11px — solo badges y ejes de gráfico */
--fs-xs:  0.75rem;    /* 12px — etiquetas, cabeceras de tabla, metadatos */
--fs-sm:  0.8125rem;  /* 13px — celdas densas, texto secundario */
--fs-md:  0.875rem;   /* 14px — base de la UI */
--fs-lg:  1rem;       /* 16px — inputs, cuerpo de formularios, prosa */

/* jerarquía — Tercera Mayor 1.25 sobre 16px */
--fs-h4:  1rem;       /* 16px */
--fs-h3:  1.25rem;    /* 20px */
--fs-h2:  1.5rem;     /* 24px */
--fs-h1:  1.75rem;    /* 28px */
--fs-kpi: 2rem;       /* 32px — cifra de KPI; nunca más grande que esto */
```

Nada fluido dentro de la app: los tamaños están bloqueados porque el ancho de columna está bloqueado. La fluidez va en el **contenedor**, no en el tipo.

### Medidas
- Fila de tabla: **40px** (compacta) o **44px** (cómoda). Celda: `padding: 8px 12px`.
- Cabecera de tabla: 12px, mayúsculas, `letter-spacing: 0.04em`, `position: sticky; top: 0`, `z-index` del token.
- Sidebar: 240px / 280px. Contenido: máx. 1280px con `padding-inline: 24px`.
- Grilla de página: 8 columnas internas con `gap: 16px`.
- Radio: **6px**. Sombra: **ninguna** en contenedores; solo en popovers/menús (`0 8px 24px -8px rgba(0,0,0,.16)`).
- Separación entre bloques: 24px; entre secciones: 32px.
- `line-height`: 1.45 en celdas, 1.5 en prosa, 1.2 en cifras grandes.

### Reglas duras propias
- **Cero sombras difusas** en tablas, cards y paneles: `1px solid var(--border)` + fondo de superficie.
- `font-variant-numeric: tabular-nums` en **todo**: tablas, KPI, importes, fechas, contadores, badges de tendencia.
- Alineación numérica: importes y métricas **a la derecha**; texto a la izquierda; nunca centrar números en columnas.
- Estado del sistema visible sin interacción: `success / warning / danger / info` como tokens propios, con icono + texto (no solo color).
- Acciones destructivas: color `danger`, no el acento de marca, y confirmación con `dialog` nativo.
- Foco por teclado de nivel producto: `:focus-visible` 2px, orden lógico, `⌘K`/`Ctrl+K` para búsqueda, navegación de tabla con flechas si hay muchos datos.
- Divulgación progresiva: filtros avanzados colapsados, columnas configurables, detalle en panel lateral (no modal a pantalla completa).
- Vacíos y errores son pantallas, no texto gris: explican la causa y ofrecen la acción siguiente.

### Anti-patrones del perfil
Tarjetas con sombra grande, hero decorativo, iconos de 40px, ilustraciones en el dashboard, degradados, tipografía fluida, animaciones de entrada por scroll (el operador entra 200 veces al día: la animación es un castigo), `line-height` 1.8, centrar texto.

---

## Perfil 2 — Corporativo y e-commerce

**Trabajo del diseño:** confianza y transacción. Dos motores: la institución (solidez, escala, evidencia) y la tienda (producto, precio, fricción cero). Comparten la misma escala.

### Escala — Cuarta Justa 1.333 · base 16px

```
--fs-xs:   0.75rem;   /* 12px */
--fs-sm:   0.875rem;  /* 14px */
--fs-base: 1rem;      /* 16px */
--fs-lg:   1.125rem;  /* 18px */
--fs-h4:   1.3125rem; /* 21px */
--fs-h3:   1.75rem;   /* 28px */
--fs-h2:   2.375rem;  /* 38px */
--fs-h1:   3.125rem;  /* 50px */
```

1.333 es el ratio más "institucional" de la lista: pasos claros sin dramatismo. h1 nunca pasa de 56px.

### Medidas
- Contenedor: 1280px (texto 1200px). `padding-inline: 16px` móvil / 24px tablet / 32px desktop.
- Grilla: 12 columnas, `gap: 24px`; gutters en múltiplos de 8.
- Radio: 8px (moderno) o 0px (editorial corporativo). Elige uno y no lo mezcles.
- Sombra: `0 1px 2px rgba(0,0,0,.05), 0 8px 24px -12px rgba(0,0,0,.10)` — discreta, solo en cards elevadas.
- `line-height`: 1.5 cuerpo, 1.1 titulares.
- Grid de producto: `minmax(220px, 1fr)`, gap 16px móvil / 24px desktop.

### Reglas duras propias
- **Proporción de medios uniforme** por categoría: `4/5` moda y vertical, `1/1` catálogo general, `16/10` B2B/maquinaria, `3/2` inmobiliaria. `object-fit: cover` + `aspect-ratio` + fondo neutro `--surface-media` de respaldo. Una foto vertical y otra panorámica en la misma fila jamás deben desalinear la grilla.
- **Nada crítico detrás de `hover`**: precio, valoración, disponibilidad y acción secundaria siempre visibles. El hover solo añade (segunda imagen, "vista rápida").
- Precio con `tabular-nums` y moneda en formato local (`$ 1.299.000` en CO). Descuento: precio tachado + ahorro, con `danger` solo en el porcentaje.
- Estado de compra completo: `default → hover → active → disabled (agotado) → loading (añadiendo) → success (añadido) → error (pago)`. Este ciclo es la mitad del trabajo del perfil.
- Prueba social concreta: cifras, reseñas con fecha, logos reales. Nada de "Trusted by 10.000 companies" sin fuente.
- Formularios largos (checkout): un paso por pantalla, resumen persistente, autocompletado (`autocomplete` real), errores en línea junto al campo.

### Anti-patrones del perfil
Grid con fotos de proporciones distintas, hover como único sitio donde aparece el precio, carrusel de producto, "Oferta" en rojo de marca, degradados de fondo, iconos de redes sociales gigantes, textos legales en 10px, banner de cookies que tapa el CTA.

---

## Perfil 3 — Landing page y portfolio

**Trabajo del diseño:** una sola decisión por scroll. Atención → comprensión → prueba → acción. Aquí sí hay drama, pero **un** drama.

### Escala — 1.414 en intermedios, 1.618 solo en el hero

```
--fs-hero: clamp(2.5rem, 1.75rem + 3.2vw, 4.75rem);      /* 40 → 76px */
--fs-h2:   clamp(1.75rem, 1.35rem + 1.6vw, 2.75rem);     /* 28 → 44px */
--fs-h3:   clamp(1.375rem, 1.2rem + 0.85vw, 1.875rem);   /* 22 → 30px */
--fs-h4:   clamp(1.125rem, 1.05rem + 0.4vw, 1.375rem);   /* 18 → 22px */
--fs-lead: clamp(1.0625rem, 1rem + 0.35vw, 1.3125rem);   /* 17 → 21px */
--fs-base: 1rem;
--fs-meta: 0.8125rem;                                    /* 13px */
```

**Por qué no 1.618 en todo:** con 1.618 sobre 16px, h3 = 42px, h2 = 68px y h1 = 110–177px. En español, un titular de 110px en 1366px de ancho rompe la caja, crea 5 líneas y empuja el CTA fuera del primer viewport, matando el patrón Z. El salto áureo se reserva al contraste cuerpo→hero, que es donde el ojo lo percibe; los niveles intermedios usan 1.414 (o 1.5 si necesitas más contraste). El techo de 76px es el límite práctico para texto en español a 1440px.

### Medidas
- Contenedor: 1200px (texto 680px). `padding-inline: 20px` móvil / 32px / 48px desktop.
- Ritmo vertical: sección 96–128px desktop, 56–72px móvil. **Nunca** el mismo valor en todas.
- Grilla: 12 columnas. Hero asimétrico: `5/7`, `7/5` u `8/4`. Bento: `2fr 1fr` + filas mixtas.
- `line-height`: 1.05 titulares, 1.6 prosa. Titulares ≥36px con `letter-spacing: -0.03em`.
- Radio: 12–16px en cards si es moderno; 0–4px si es editorial. Nunca dos radios distintos en el mismo nivel.

### Reglas duras propias
- **Ritmo asimétrico obligatorio:** alterna estructuras entre secciones. Hero (patrón Z) → bento asimétrico → editorial full-bleed → cifras → prueba → CTA final. Si cinco secciones seguidas tienen el mismo ancho y centrado, la página parece plantilla.
- **Patrón Z / F:** titular arriba-izquierda, elemento visual arriba-derecha, prueba abajo-izquierda, CTA abajo-derecha. El CTA primario, en el borde del recorrido natural del ojo, visible a 1366×768 sin scroll.
- Una sola coreografía de entrada (§`movimiento.md`), máximo 3–6 elementos.
- Cifras y prueba en cifras tabulares, y **una sola** fuente de prueba social repetida con variaciones (no cinco formas de decir lo mismo).
- El titular se escribe **después** de la estructura, y siempre se prueba a 3 anchos con el texto real en español.
- `text-wrap: balance` en titulares; comprueba que no queda una palabra huérfana.

### Anti-patrones del perfil
Tres tarjetas iguales, hero centrado con dos botones, degradado morado/violeta, blob o mesh de fondo, glassmorphism, "Powered by AI", mockup flotante con gráficos falsos, animación en cada sección, typewriter en el H1, contadores animados de cifras inventadas.

---

## Perfil 4 — Editorial profundo

**Trabajo del diseño:** desaparecer. La interfaz no compite con el texto; lo sostiene y ayuda a escanear.

### Escala — Tercera Mayor 1.25 · base 18–20px

```
--fs-sm:    0.875rem;  /* 14px */
--fs-base:  1.125rem;  /* 18px — cuerpo móvil */
--fs-body:  1.25rem;   /* 20px — cuerpo desktop */
--fs-lead:  1.5rem;    /* 24px — entradilla */
--fs-h3:    1.75rem;   /* 22–28px */
--fs-h2:    clamp(1.75rem, 1.4rem + 1.2vw, 2.25rem);  /* 28 → 36px */
--fs-h1:    clamp(2rem, 1.55rem + 2vw, 3.375rem);     /* 32 → 54px */
```

### Medidas
- Medida de lectura: **62–72ch** con `font-size: 20px` y `line-height: 1.65`. En móvil se resuelve con aire lateral, no con `max-width` pequeño.
- Columna de texto: 680–720px centrada con `margin-inline: auto`; elementos de escape (imagen full-bleed, cita, tabla) salen del contenedor con `margin-inline: calc(50% - 50vw)`.
- Metadatos (fecha, autor, tiempo de lectura): 14px, tono medio, sin negrita.
- Pies de foto: 13–14px, tono suave, `line-height: 1.4`, alineados a la izquierda.
- Separación entre párrafos: `--sp-md` (16–20px) con `margin-block: 0` y `+ p { margin-top: ... }` para no crear huecos al inicio.

### Reglas duras propias
- **Jerarquía cromática de texto en 3 niveles obligatoria:** `--ink` (lectura), `--ink-2` (metadatos/fechas), `--ink-3` (pies de foto, notas). Tres tonos, no cinco.
- **Índice lateral fijo (TOC)** en artículos >1.500 palabras: `position: sticky; top: 96px`, activo por `IntersectionObserver`, y `scroll-margin-top: 96px` en cada `h2` (sin esto el título queda bajo la cabecera fija). En móvil, TOC colapsable arriba.
- Progreso de lectura discreto (2px, `scroll()` con fallback); nada de barras animadas llamativas.
- Cero animaciones de entrada por párrafo. Se permite fade de imágenes ≤200ms.
- Tipografía con personalidad: una serif de texto real o una grotesk con ejes ópticos. Cursivas y versalitas disponibles de verdad, no sintetizadas por el navegador.
- Notas al pie, citas y bloques de código con tratamiento propio (borde izquierdo 2px + fondo de superficie, monoespaciada 15px con `tabular-nums`).

### Anti-patrones del perfil
Justificar el texto, `line-height` 1.9, medida de 100 caracteres, sans-serif genérica a 16px en todo, imágenes que rompen la línea base sin margen, TOC que no se actualiza, "drop cap" de 6 líneas, share buttons flotantes que tapan texto.

---

## Perfil 5 — App móvil / PWA

**Trabajo del diseño:** una mano, un pulgar, interrupciones. Cada píxel compite contra el mundo real.

### Escala — 1.2 · base 17px

```
--fs-2xs:  0.75rem;  /* 12px */
--fs-xs:   0.8125rem;/* 13px */
--fs-sm:   0.875rem; /* 14px */
--fs-base: 1rem;     /* 16px — mínimo en inputs, evita autozoom iOS */
--fs-body: 1.0625rem;/* 17px — cuerpo iOS */
--fs-h4:   1.25rem;  /* 20px */
--fs-h3:   1.5rem;   /* 24px */
--fs-h2:   1.8125rem;/* 29px */
--fs-h1:   2.1875rem;/* 35px */
```

### Medidas
- Zona de pulgar: acciones primarias en el tercio inferior. Cabeceras: solo título y una acción.
- `padding-inline: 16px` **siempre** (los 35–40 caracteres de medida salen solos; no pongas `max-width` en ch).
- Target táctil 44×44px mínimo, 48px recomendado, separación ≥8px.
- Barra inferior: 56px + `env(safe-area-inset-bottom)`. Cabeceras fijas con `env(safe-area-inset-top)`.
- Alturas de pantalla: `100dvh`, **nunca `100vh`** (la barra de Safari rompe el cálculo).
- Listas: filas 56–64px, `:active` como feedback (el `hover` no existe).
- Inputs: `font-size: 16px` mínimo, `inputmode`, `autocomplete`, `enterkeyhint` correctos.

### Reglas duras propias
- Diseña primero el estado **con una mano y sin conexión**: skeleton, error, vacío, offline, recargando. TikTok no es el referente; la app del banco sí.
- Gestos con alternativa visible (swipe para borrar → botón en menú contextual). Nunca gesto como único camino.
- Transiciones de pantalla 200–280ms con `View Transitions` o `translate`, respetando `reduce`.
- Feedback inmediato: `<100ms` a todo toque (INP), y `prefers-reduced-motion` para las animaciones de gesto.
- Modo oscuro es el caso por defecto, no una variante: prueba primero en oscuro.

### Anti-patrones del perfil
`100vh`, `max-width: 35ch`, inputs de 14px, cards con hover, textos de 12px como cuerpo, modales a pantalla completa para tareas simples, scroll horizontal accidental, banner fijo que tapa contenido.

---

## Tokens compartidos (no dependen del perfil)

```css
/* Espaciado — 8pt con escalón fino de 4pt para componentes */
--sp-3xs: 2px;   /* SOLO bordes, divisores, micro-badges */
--sp-2xs: 4px;   /* SOLO componentes: chips, iconos, gaps internos */
--sp-xs:  8px;
--sp-sm:  12px;  /* componentes */
--sp-md:  16px;
--sp-lg:  24px;
--sp-xl:  32px;
--sp-2xl: 48px;
--sp-3xl: 64px;
--sp-4xl: 96px;
--sp-5xl: 128px; /* solo secciones de Perfil 3 */

/* Radios (elige uno por nivel y no lo mezcles) */
--r-xs: 4px; --r-sm: 6px; --r-md: 8px; --r-lg: 12px; --r-xl: 16px; --r-full: 999px;

/* Movimiento (ver movimiento.md) */
--dur-1: 80ms; --dur-2: 140ms; --dur-3: 200ms; --dur-4: 320ms; --dur-5: 500ms;

/* Capas */
--z-base: 0; --z-sticky: 10; --z-drawer: 30; --z-modal: 40; --z-toast: 50; --z-tooltip: 60;
```

**Regla de oro del sistema:** si necesitas un valor nuevo, primero demuestra que ningún token sirve. Un sistema que crece en cada componente no es un sistema.
