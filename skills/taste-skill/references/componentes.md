# Especificación de componentes

Cada componente se especifica con **medidas, estados y reglas**. Si un estado no está definido, el componente no está terminado.

## Los 8 estados obligatorios

`default · hover · focus-visible · active · disabled · loading · error · empty`

No aplican a todos, pero hay que **decidir explícitamente** cuáles aplican. `hover` no aplica en táctil: si la información solo vive ahí, desaparece para el 60% del tráfico.

---

## Botones

| Propiedad | Primario | Secundario | Terciario / ghost | Destructivo |
|---|---|---|---|---|
| Alto | 44px (48 móvil) | 44px | 40px | 44px |
| Padding | `0 20px` | `0 20px` | `0 12px` | `0 20px` |
| Radio | `--r-md` | `--r-md` | `--r-sm` | `--r-md` |
| Fondo | `--accent` | `transparent` + borde `1px --border-strong` | transparente | `--danger` |
| Texto | `--on-accent` | `--ink` | `--ink-2` | `#fff` |
| Peso | 550–600 | 500 | 500 | 600 |

- **Un solo primario por vista** (y por sección). Dos botones primarios = ninguno.
- Jerarquía por **contraste y tamaño**, no por color: el secundario no es "el primario en otro color".
- `min-width` fijo para que el cambio a "Añadiendo…" o "✓ Añadido" no mueva el layout.
- Área táctil ≥44px incluso si el visual es de 36px (padding invisible).
- Loading: el label no desaparece; se atenúa y entra un spinner de 16px al lado. Nunca un botón vacío.
- Disabled: `opacity: .45` **y** `cursor: not-allowed` **y** `aria-disabled`; acompaña un texto que explique por qué.
- Foco: `outline: 2px solid var(--focus); outline-offset: 2px` (el `offset` evita que el anillo se coma el borde).

## Formularios

- Input: alto 44px, `padding: 0 12px`, `font-size ≥16px` (evita autozoom iOS), radio `--r-sm`.
- Label **siempre visible arriba** (14px, 500). Placeholder = ejemplo, nunca la etiqueta.
- Ayuda debajo (13px, `--ink-2`); error debajo (13px, `--danger`) con icono y `aria-describedby`; el borde pasa a 2px `--danger`.
- Ancho del campo proporcional al dato esperado: código postal ≠ dirección. Un formulario con todos los campos al 100% se lee como plantilla.
- Validación al `blur` y al enviar, nunca en cada tecla. Error en línea + resumen al principio si hay más de 3.
- Agrupa en fieldsets con leyenda cuando hay más de 6 campos. Máximo 7 campos visibles por paso (Hick).
- `autocomplete`, `inputmode`, `enterkeyhint`, `required` correctos: son gratis y multiplican la conversión móvil.

## Navegación

**Perfil 1 (app):** sidebar 240–280px, ítems de 36–40px, icono 20px + label 14px, estado activo con fondo `--surface-2` + barra 2px del acento a la izquierda, grupos con etiqueta 11px mayúsculas. Cabecera 56–64px con búsqueda (`⌘K`), breadcrumb y cuenta. Colapsable a iconos en <1024px.

**Perfiles 2 y 3:** cabecera 64–72px, logo a la izquierda, 5–7 ítems (Hick), CTA a la derecha. Sticky con reducción de altura al hacer scroll (72 → 60px) y sombra solo cuando ya hay scroll. Menú móvil: panel lateral, cierre con `Esc`, foco atrapado, `scroll-lock` en `body` compensando el ancho de la barra.

**Perfil 5:** barra inferior 56px + `env(safe-area-inset-bottom)`, 3–5 destinos, icono 24px + label 10–11px, estado activo por color **y** peso.

Ninguna cabecera fija sin `scroll-margin-top` en los anclajes (`scroll-margin-top: 88px`).

## Hero

- **Perfil 3:** asimetría `5/7` u `8/4`. Titular ≤3 líneas a 76px máx., subtítulo ≤2 líneas a `--fs-lead`, 1 CTA primario + 1 enlace secundario, y **una prueba concreta** (cifra, logo, captura) en el primer viewport. Alto: `min-height: 88svh` (no `100vh`) para que el CTA se vea a 1366×768 con barra de navegador.
- **Perfil 2:** hero corporativo con `16/10`, titular de 38–50px, overlay de contraste y CTA visible; nada de video pesado.
- **Perfil 1:** no hay hero. Hay una **barra de título** de 56px con nombre de la vista + acciones, y debajo los KPIs.

## Cards

- Padding interno: 16–24px (nunca 12px en Perfil 3). Gap de grilla 16–24px.
- **Una** idea por card: título ≤6 palabras, cuerpo ≤3 líneas, una acción.
- Borde `1px` en Perfiles 1–2 (sin sombra); sombra suave o elevación lumínica en Perfil 3.
- Toda la card clicable → un solo enlace cubriendo la card (`::after` absoluto), con el resto del texto no interactivo. Nunca dos enlaces dentro de una card clicable.
- Imagen siempre con `aspect-ratio` fijo (ver `imagenes.md`).
- Hover: `translateY(-2px)` + borde acentuado, 140ms. Nunca `scale(1.05)`.

## Tablas (Perfil 1)

- Cabecera: `position: sticky; top: 0`, 12px mayúsculas `letter-spacing: .04em`, fondo `--surface` **opaco** (si es translúcido, el contenido se ve a través al hacer scroll).
- Filas 40–44px; `:hover` con `--surface-1`; selección con `--accent-soft`.
- Números a la derecha con `tabular-nums` y mismo número de decimales; texto a la izquierda; nunca centrar.
- Columna de acciones fija a la derecha (`position: sticky; right: 0`) en tablas anchas.
- Densidad conmutable (compacta/cómoda) guardada en preferencias.
- Sin tabla: lista de definiciones en móvil (<768px), no scroll horizontal de una tabla de 9 columnas.
- Vacío, error y carga son **filas de estado** dentro de la tabla, con la misma altura: nada de saltos.

## KPIs y métricas

- Cifra `--fs-kpi` (32px Perfil 1), `tabular-nums`, peso 600, `letter-spacing: -0.02em`.
- Etiqueta 12–13px `--ink-2` arriba; delta con icono + color semántico + texto (`+12,4%` en `success`, `−3,1%` en `danger`) y periodo explícito ("vs. mes anterior").
- El color nunca es el único portador del dato: siempre símbolo o texto.
- Máximo 4 KPIs por fila (Hick + ancho de lectura). La quinta métrica va a una segunda fila o a un gráfico.

## Badges, chips y pills

- Alto 20–24px, `padding: 2px 6px`, radio `--r-full` (pill) o `--r-xs` (tag), 11–12px, peso 500.
- Fondo `--semantic-soft` + texto `--semantic-ink` del mismo tono. Contraste ≥4.5:1 también en badges pequeños.
- Máximo 2 badges por item. Si necesitas 3, el problema es la taxonomía.

## Modales, drawers y toasts

- Usa `<dialog>` / `popover` nativos (foco atrapado y `Esc` gratis).
- Ancho: modal 480px (máx. 560), drawer 400–480px, nunca a pantalla completa salvo flujo móvil de Perfil 5.
- Anatomía: título (20px) + descripción (14px) + contenido + acciones alineadas a la derecha (primaria la más a la derecha).
- Cierre: `Esc`, botón ×, clic en backdrop. **No** cerrar al clic en el contenido.
- Toast: abajo-derecha en desktop, abajo-centrado en móvil, 4–6s, cierre manual, `role="status"`. Máximo 3 apilados.
- El scroll del body se bloquea sin saltar: `overflow: hidden` + `padding-right: scrollbarWidth`.

## Cards de producto y PDP (Perfil 2)

- Card: imagen `4/5` (moda) o `1/1` → marca 12px, nombre 14–16px (2 líneas máx.), precio 16px `tabular-nums`, valoración con estrellas + número, talla/color en línea si aplica, botón secundario visible (no solo en hover).
- PDP: galería 55–60% / panel de compra 40–45% y sticky. Precio, stock, envío y CTA en el primer viewport. Selector de talla con tallas agotadas tachadas y accesibles por teclado.
- Un solo CTA primario ("Añadir al carrito"); "Comprar ahora" es secundario. Pagos y garantías debajo, en 12–13px.

## Artículo (Perfil 4)

- `h1` ≤3 líneas, `--fs-lead` como entradilla, metadatos (autor, fecha, tiempo de lectura) en 14px `--ink-2`.
- Cuerpo 20px / 1.65 / 62–72ch. `h2` con `scroll-margin-top: 96px` y ancla copiable.
- Elementos de escape a `100vw` con `margin-inline: calc(50% - 50vw)`.
- Cita: borde izquierdo 2px del acento, 24px, sin comillas decorativas gigantes.
- TOC sticky con estado activo; en móvil, `<details>` colapsable arriba.
- Siguiente lectura al final: 2–3 artículos, no una rejilla de 9.

## Estados vacíos y errores

- Estructura: ilustración/icono (64–96px) + título (18–20px) + causa en una frase + acción primaria.
- El copy dice **qué pasó y qué hacer**, en el idioma del usuario, sin culpar. Nunca "Error 500".
- Página 404: búsqueda + 3 enlaces útiles. Sin chistes.

## Footer

- 3–4 columnas máx. (Perfil 2–3), 14px, títulos 12px mayúsculas `--ink-2`.
- Cierre con razón social, contacto real y selector de idioma/moneda si existe.
- Sin redes sociales a 40px, sin "hecho con ❤️", sin sitemap de 60 enlaces.
