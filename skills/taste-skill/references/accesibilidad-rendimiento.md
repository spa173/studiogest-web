# Accesibilidad, temas y rendimiento

Puertas de salida, no "buenas prácticas". Si algo de esta lista falla, la entrega no está terminada.

## 1. Modo claro / modo oscuro

Un mismo sistema, dos mapeos. Declara los tokens semánticos una vez y cambia solo los valores.

```css
:root {
  color-scheme: light dark;

  /* Tinta en 3 niveles — jerarquía cromática de texto (obligatoria en Perfil 4) */
  --ink:    light-dark(#14130F, #F4F1EA);   /* lectura */
  --ink-2:  light-dark(#565248, #A8A399);   /* metadatos, fechas */
  --ink-3:  light-dark(#7C776C, #7E7A72);   /* pies de foto, notas legales */

  /* Superficies: en claro se ordenan por sombra; en oscuro, por LUMINOSIDAD */
  --bg:        light-dark(#FBFAF7, #0C0C0D);
  --surface-1: light-dark(#FFFFFF, #141416);  /* card */
  --surface-2: light-dark(#F4F2EC, #1B1B1E);  /* dropdown, input */
  --surface-3: light-dark(#EAE7DF, #232327);  /* modal, elemento más cercano */

  --border:      light-dark(rgb(0 0 0 / .10), rgb(255 255 255 / .10));
  --border-top:  light-dark(rgb(0 0 0 / .06), rgb(255 255 255 / .08)); /* borde superior translúcido */

  /* Sombra SOLO en claro. En oscuro, la elevación es lumínica. */
  --shadow-1: light-dark(0 1px 2px rgb(0 0 0 / .06), none);
  --shadow-2: light-dark(0 8px 24px -12px rgb(0 0 0 / .18), none);
}
@media (prefers-color-scheme: dark) {
  .card, .modal, .popover { border-top: 1px solid var(--border-top); }
}
```

Reglas de modo oscuro:
- **Prohibida la sombra difusa.** Un modal con `box-shadow` sobre fondo oscuro es un borrón invisible que además cuesta rendimiento.
- Cada nivel de elevación sube **un paso de luminosidad** (#141416 → #1B1B1E → #232327 → #2B2B30). Nunca 4 grises distintos sin orden.
- Nunca uses negro puro (#000) como fondo: el contraste con texto claro es violento y el OLED provoca sangrado.
- En oscuro, el acento baja de saturación y sube de luminosidad (un `#B4451F` se convierte en `#E2744A`); si no, el texto sobre el acento no llega a 4.5:1.
- Todo esto funciona gratis con `light-dark()` + `color-scheme`; no dupliques hojas de estilo.

## 2. Contraste

| Elemento | Mínimo |
|---|---|
| Texto de cuerpo | 4.5:1 |
| Texto grande (≥24px, o ≥18.66px bold) | 3:1 |
| Bordes de input, iconos con función, estados de foco | 3:1 |
| Texto sobre imagen o sobre acento | 4.5:1 medido en la zona real |
| Placeholder | 4.5:1 (no lo dejes en gris claro) |

Nunca uses el color como único portador: añade icono, forma, subrayado, peso o texto. Aplica a errores, precios con descuento, estados y series de gráficos.

## 3. Teclado y foco

- Orden de tabulación = orden visual. Cero `tabindex` positivos.
- `:focus-visible` con 2px + `outline-offset: 2px`; el anillo tiene que verse sobre **cualquier** fondo (usa doble anillo: `box-shadow: 0 0 0 4px var(--surface), 0 0 0 6px var(--focus)` si el fondo varía).
- Skip link al `main` (visible al foco).
- `Esc` cierra overlays y devuelve el foco al disparador.
- Cabeceras fijas: `scroll-margin-top` en anclas y `:target`.
- Menús y combobox: flechas, `Home/End`, `Enter`, `Esc`, `aria-expanded`, `aria-activedescendant`.
- Nada de "div con onClick" para acciones: usa `<button>` (si navega, `<a>`).

## 4. Semántica y ARIA

- Un solo `<h1>`, jerarquía de encabezados sin saltos.
- `<main>`, `<nav>`, `<header>`, `<footer>`, `<aside>`; landmarks no duplicados sin `aria-label`.
- Formularios con `<label for>`; `aria-describedby` para ayudas y errores; `aria-invalid` en error.
- Cambios asíncronos (`aria-live="polite"`), nunca `assertive` para toasts.
- `aria-label` en icono-botones y en enlaces cuyo texto es "leer más".
- Acordeones con `<details>` o `aria-expanded` + `aria-controls`.
- `lang` correcto en `<html>` (y en fragmentos en otro idioma).

## 5. Presupuestos de rendimiento

| Recurso | Presupuesto |
|---|---|
| JS total (gz) | < 200KB · framework incluido |
| CSS (gz) | < 50KB |
| Imágenes iniciales | < 500KB (hero ≤180KB) |
| Fuentes | ≤2 familias / ≤4 pesos / <100KB total, WOFF2, `font-display: swap` + fallback con `size-adjust` |
| Terceros | < 100KB y ninguno bloqueante |
| Página completa | < 1MB |

**Métricas:** LCP ≤2.5s · INP ≤200ms · CLS ≤0.1 (p75 real, no Lighthouse).

Prácticas:
- Fuentes: `preload` del peso crítico, autohospedadas (rendimiento y privacidad), `font-display: swap`, y métrica de respaldo ajustada para evitar reflow.
- Autohospeda o elimina cualquier script que no sea imprescindible; carga chat, mapas y video **bajo interacción**.
- `content-visibility: auto` + `contain-intrinsic-size` en secciones bajo el fold.
- Sin dependencias para cosas de 20 líneas (carrusel, acordeón, tooltip).
- INP: divide tareas largas (>50ms), `yield` antes del trabajo pesado, handlers ligeros, `passive` en listeners de scroll/touch.
- Evita N+1 y waterfalls en SSR: datos en paralelo, streaming, skeletons con la forma final.

## 6. Movimiento y accesibilidad

Ver `movimiento.md` §`prefers-reduced-motion`. Resumen: `reduce` desactiva parallax, autoplay, marquesinas y desplazamientos; conserva fades cortos. Nada parpadea más de 3 veces por segundo (riesgo fotosensible).

## 7. Checklist de salida

- [ ] Contraste verificado en texto, UI y badges.
- [ ] Recorrido completo con teclado, foco siempre visible.
- [ ] `prefers-reduced-motion` y `prefers-color-scheme` probados de verdad.
- [ ] Modo oscuro con elevación lumínica (sin sombras).
- [ ] CLS ≈ 0: dimensiones en imágenes, espacio reservado para embeds, fuentes con fallback métrico.
- [ ] LCP: hero priorizado, sin lazy, sin animación de opacidad.
- [ ] Presupuestos de §5 dentro de rango.
- [ ] Formularios con label, autocomplete y errores asociados.
