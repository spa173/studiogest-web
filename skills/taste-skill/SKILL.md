---
name: taste-skill
description: Diseña, construye y audita interfaces web con dirección de arte y restricciones matemáticas verificables. Clasifica el proyecto en 5 perfiles (SaaS/dashboard, corporativo/e-commerce, landing/portfolio, editorial profundo, app móvil) y aplica escalas modulares, grilla de 8 puntos, leyes de Fitts y Hick, tokens CSS listos para usar, sistema de movimiento y sistema de imágenes. Úsala cuando el usuario pida crear, rediseñar, revisar o "mejorar el diseño" de una landing page, dashboard, panel de finanzas, e-commerce, portfolio, blog/artículo largo o app móvil; cuando diga "diseño web", "UI", "sistema de diseño", "que no se vea genérico", "que se vea profesional", "agregar animaciones", "transiciones", "elegir o generar imágenes", "hero", "conversión" o "maquetar"; y cuando haya que escribir HTML, CSS, Tailwind o componentes React con impacto visual. No usar para backend, lógica de negocio sin cambio visual ni refactors que no toquen la interfaz.
license: MIT
---

# Taste Skill — dirección de arte verificable

Esta skill convierte el "buen gusto" en **restricciones medibles en el código**. No da opiniones: entrega tokens, medidas, patrones y una auditoría ejecutable. El objetivo es que dos personas (o dos agentes) lleguen al mismo resultado de nivel estudio sin depender de inspiración.

## 0. Contrato de salida (antes de escribir una sola etiqueta)

Emite estas 4 líneas al inicio de la respuesta, siempre, en este formato exacto. Si falta una, la respuesta es inválida: vuelve a empezar.

```
PERFIL:     <1–5> — <nombre del perfil>             (ver references/perfiles.md §Árbol de decisión)
ESCALA:     <ratio(s) + base px> | MEDIDA: <ch de lectura>
ESTÉTICA:   <dirección de arte en una línea: 1 tipografía concreta, paleta de 2–3 familias de color,
            1 textura/recurso gráfico, referencia NO genérica>
MOVIMIENTO: <nivel 0–3> + <1 coreografía nombrada> | IMAGEN: <tratamiento: foto/ilustración/3D/ninguna + encuadre>
```

Ejemplo válido:

```
PERFIL:     3 — Landing / Portfolio
ESCALA:     1.414 intermedios + 1.618 solo en el salto hero, base 16px | MEDIDA: 60ch
ESTÉTICA:   Grotesk suiza (Söhne-like) + papel hueso #F7F5F0, tinta #111, acento óxido #B4451F,
            retícula visible de 8pt como recurso, referencias: Pentagram / Off-White, cero glassmorphism
MOVIMIENTO: 3 — "un solo momento hero": titular enmascarado + reveal escalonado de 3 anclas
            | IMAGEN: foto documental cálida, 3:2, grano 4%, sin stock de oficina
```

Después de declarar, carga **solo** los archivos de `references/` que la tabla §9 indique. No cargues todo.

---

## 1. Los 5 perfiles (vista rápida)

| # | Perfil | Escala tipográfica | Densidad | Movimiento | Imagen |
|---|--------|--------------------|----------|-----------|--------|
| 1 | SaaS app / dashboard / finanzas | densidad 1.067 + jerarquía 1.25, base 14–16px | Alta: 12–14px UI, filas 40–44px | 1–2 (feedback, 80–200ms) | Iconografía + gráficos, sin foto decorativa |
| 2 | Corporativo / e-commerce | 1.333, base 16px | Media | 2 (transiciones de estado, 140–240ms) | Producto: grilla uniforme `4/5`, `1/1`, `16/10` |
| 3 | Landing / portfolio | 1.414 (o 1.5) + **1.618 solo en hero** | Baja, aire | 3 (una coreografía por página) | Hero con encuadre art-directed + soporte |
| 4 | Editorial profundo | 1.25, cuerpo 18–20px | Media-baja, medida 62–72ch | 1–2 (casi nada: lectura) | Fotografía de autor + pies de foto |
| 5 | App móvil / PWA | 1.2, base 17px | Alta, targets 44px | 2 (gestos y transiciones de pantalla) | Thumbs `1/1`, placeholders con color dominante |

Detalle completo, tokens y reglas por perfil: `references/perfiles.md`.

## 2. Las 14 leyes duras (no negociables)

Si el usuario pide algo que viola una ley, dilo en una línea y aplica la ley. No las rompas en silencio.

1. **Base 16px, máximo 2 ratios.** Una escala declarada y usada. Prohibido inventar `font-size` fuera de la escala (excepciones: `0.625rem` para badges y el mínimo legal de 11px).
2. **1.618 solo en el salto hero.** Cuerpo→titular hero puede ser áureo: `clamp(2.5rem, 1.75rem + 3.2vw, 4.75rem)`. Los niveles intermedios (h2–h4) usan 1.414 o 1.5. **Nunca** apliques 1.618 a cada nivel: en español (palabras 20–30% más largas que en inglés) un h1 de 110px rompe la caja en 1366px y empuja el CTA fuera del primer viewport.
3. **Grilla:** layout y contenedores en múltiplos de **8** (8, 16, 24, 32, 48, 64, 96); componentes en múltiplos de **4** (4, 12, 20); **1px y 2px permitidos solo** en bordes, divisores y micro-badges (`padding: 2px 6px`).
4. **Medida de lectura:** 55–72ch en desktop. En móvil **no escribas `max-width: 35ch`**: los 35–40 caracteres salen solos con `width: 100%` + `padding-inline: 1rem` + `font-size: 1rem`. Ese `1rem` además evita el auto-zoom de Safari iOS al enfocar inputs.
5. **Color 60/40/10:** 60 superficie, 40 secundario/texto, **10% = 1 acento con 3 estados** (base, hover, active + anillo de foco). Aparte y separados, los **tokens semánticos de feedback** (`success`, `warning`, `danger`, `info`) son obligatorios en Perfiles 1 y 2 y para toda acción destructiva. Nunca uses el acento de marca para un error.
6. **Contraste y foco:** 4.5:1 en texto, 3:1 en UI y en texto ≥24px. Foco visible siempre: `outline: 2px solid var(--focus); outline-offset: 2px`. Prohibido `outline: none` sin sustituto.
7. **Objetivo táctil ≥44×44px** (mínimo absoluto 24×24 según WCAG 2.2) y ≥8px de separación entre acciones adyacentes.
8. **Fitts + Hick:** la acción primaria es el elemento más cercano y más grande del punto de decisión; enlaces de nav con altura ≥44px; menús de 5–7 ítems (más de 9 necesita agrupación o búsqueda).
9. **Cifras tabulares:** `font-variant-numeric: tabular-nums` en tablas, KPI, precios, contadores y timestamps. Sin esto las columnas financieras bailan.
10. **Densidad vs. drama:** en paneles, cero sombras difusas → contenedores planos con borde `1px` + cabecera de tabla `position: sticky`. En marketing sí hay sombra (modo claro) o **elevación lumínica** (modo oscuro: superficie más clara = más cerca del usuario + `1px solid rgba(255,255,255,.08)` arriba). Nunca sombra en modo oscuro.
11. **Movimiento:** solo `transform`, `opacity` y `filter`. Duración 80–320ms (entrada hero ≤500ms, una vez por página); **la salida dura ~70% de la entrada**; todo dentro de `prefers-reduced-motion: no-preference`. Nunca animes `height`, `top/left`, `width` ni `box-shadow`.
12. **Imagen:** `aspect-ratio` + `object-fit: cover` siempre; `width`/`height` declarados (CLS); LCP sin `loading="lazy"` y con `fetchpriority="high"`; AVIF → WebP → JPEG vía `<picture>`.
13. **Tipografía óptica:** `line-height` ≥1.4 en lectura, 0.95–1.15 en titulares; `letter-spacing: -0.02em` a `-0.04em` en titulares ≥36px; `text-wrap: balance` en h1–h4 y `text-wrap: pretty` en párrafos.
14. **Una idea dominante por viewport.** Si todo grita, nada se lee. Un solo "momento" de movimiento, un solo acento, un solo tamaño grande.

## 3. Composición: el default de IA está prohibido

Sustituciones obligatorias (lista completa en `references/anti-cliches.md`):

| Default genérico | En su lugar |
|---|---|
| 3 tarjetas iguales centradas | Bento asimétrico 2/3 + 1/3, o lista editorial a ancho completo |
| Hero centrado + 2 botones + blob degradado morado | Hero asimétrico 5/7 u 8/4 con prueba concreta (cifra, logo, captura real) |
| Secuencia de 5 secciones con el mismo ancho y centrado | Alternar ritmo: hero (patrón Z) → bento → editorial full-bleed → prueba social → cierre |
| Iconos de librería genéricos como única personalidad | 1 recurso propio: retícula visible, numeración, tipografía como imagen, textura de papel/grano |
| Carrusel automático, glassmorphism global, emoji como icono, texto typewriter en el H1 | Contenido estático escaneable, superficies opacas, iconos SVG 24px `currentColor` |

## 4. Movimiento (resumen operativo)

4 niveles: **0** estático · **1** feedback (hover/press/foco) · **2** transiciones de estado (dropdown, modal, tabs, navegación) · **3** coreografía de entrada (una por página, máx. 3–6 elementos, stagger de 40–60ms).

Regla de oro: **el movimiento explica jerarquía o causalidad, no decora.** Si un movimiento no comunica de dónde viene algo o qué es lo importante, se elimina.

Sistema completo — tokens de duración/easing, coreografías nombradas, View Transitions, scroll-driven con fallback, presupuesto INP y modo `reduce`: `references/movimiento.md` y `assets/motion.css`.

## 5. Imágenes (resumen operativo)

Cuatro decisiones antes de generar una etiqueta: **tratamiento** (foto/ilustración/3D/dato/ninguna) → **proporción** por grilla → **presupuesto de peso** → **consistencia** (misma luz, mismo ángulo, mismo grano, misma paleta en toda la serie).

Recordatorio duro: en e-commerce el `hover` **no existe** en táctil → precio, valoración y acción secundaria siempre visibles.

Sistema completo — `<picture>`, `srcset/sizes`, LCP, placeholders, matrices de fotos dispares, protocolo de prompts para imágenes generadas, video: `references/imagenes.md`.

## 6. Accesibilidad y rendimiento (puertas de salida)

Presupuestos: JS < 200KB gz, CSS < 50KB gz, imágenes iniciales < 500KB, hero ≤ 180KB, fuentes ≤ 100KB (máx. 2 familias / 4 pesos). LCP ≤2.5s · INP ≤200ms · CLS ≤0.1.

Obligatorio en toda entrega: navegación por teclado completa, `scroll-margin-top` bajo cabeceras fijas, `aria-live` en cambios asíncronos, espacio reservado para todo lo que carga tarde, y `color-scheme` + `light-dark()` para modo claro/oscuro real. Detalle: `references/accesibilidad-rendimiento.md`.

## 7. Tokens listos para pegar

`assets/tokens.css` — variables por perfil (tipografía fluida con `clamp`, espaciado 8pt, radios, sombras, elevación oscura, movimiento, foco) más el reset.
`assets/patrones.css` — patrones copiables: tipografía fluida, tabla sticky con cifras tabulares, grilla de producto uniforme, reveal scroll-driven con `@supports`, `prefers-reduced-motion`, botón con 3 estados.

Copia los tokens al `:root` (o al `@theme` de Tailwind v4). **No redefinas valores a mano en los componentes.**

## 8. Cómo se estructura la entrega

1. Bloques de declaración (§0).
2. `tokens.css` / `@theme` con la escala del perfil.
3. Estructura semántica del layout (una sección por bloque narrativo, no un `div` por píxel).
4. Componentes con estados (default, hover, focus-visible, active, disabled, loading, error, empty).
5. Movimiento y medios.
6. **Auditoría** (obligatoria, §9) y corrección de lo que salga.

Todo responsive se verifica mentalmente en 3 anchos: **390px, 768px, 1366px**. Y en español, no en inglés: titulares 20–30% más largos.

## 9. Router de referencias (carga solo lo que necesitas)

| Necesitas | Lee |
|---|---|
| Elegir perfil, tokens y reglas por tipo de proyecto | `references/perfiles.md` |
| Animaciones, transiciones, scroll, page transitions | `references/movimiento.md` |
| Fotos, iconos, ilustración, video, imágenes generadas | `references/imagenes.md` |
| Especificar componentes concretos (tabla, KPI, card, nav, form, hero, artículo, PDP) | `references/componentes.md` |
| Temas oscuros, contraste, teclado, CWV, presupuestos | `references/accesibilidad-rendimiento.md` |
| Evitar el look "hecho por IA" | `references/anti-cliches.md` |
| Probar que la skill funciona | `evals/evals.md` |

## 10. Auditoría obligatoria antes de entregar

```bash
python3 scripts/audit_taste.py <ruta-html-css-tsx> --profile <1-5>
```

Revisa 25 reglas (escala tipográfica, grilla de 4/8, `tabular-nums`, `aspect-ratio`, LCP, foco, `prefers-reduced-motion`, animación de propiedades de layout, `max-width` en ch en móvil, `100vh`, `!important`, z-index, entre otras). **Si hay errores, corrige el código; si hay warnings, justifica en una línea o corrige.** No entregues con errores abiertos.

## 11. Definición de terminado

- [ ] Las 4 líneas del §0 están presentes y son coherentes con el código.
- [ ] Ningún `font-size` ni espaciado fuera de escala (validado por el auditor).
- [ ] Los 3 anchos (390 / 768 / 1366) no rompen: nada se sale de la caja, el CTA del hero es visible sin scroll.
- [ ] Estados de todos los componentes interactivos definidos.
- [ ] Movimiento bajo `no-preference`, con salida más rápida que entrada, y `reduce` implementado.
- [ ] Imágenes con proporción, dimensiones y `fetchpriority` correctos; sin salto de layout.
- [ ] Contraste, foco y teclado verificados.
- [ ] Cero apariciones de los patrones de `references/anti-cliches.md`.
- [ ] Auditor sin errores abiertos.
