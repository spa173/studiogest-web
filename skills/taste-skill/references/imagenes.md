# Sistema de imágenes y medios

La imagen no es relleno: es la decisión de arte más costosa y la que más delata una interfaz generada por IA (fotos de stock incongruentes, proporciones dispares, degradados genéricos, mockups falsos). Cuatro decisiones antes de escribir una etiqueta:

**tratamiento → proporción → peso → consistencia.**

## 1. Tratamiento

| Tratamiento | Cuándo | Perfiles | Coste |
|---|---|---|---|
| **Ninguna** (color, tipografía, dato) | Cuando la UI ya comunica: paneles de datos, dashboards, herramientas | 1 | 0 |
| **Fotografía documental** | Producto, lugar, persona, oficio, prueba real | 2, 3, 4 | Alto (producción) |
| **Fotografía de producto** | Catálogo, PDP, e-commerce | 2 | Alto (consistencia) |
| **Ilustración de sistema** | Conceptos abstractos, estados vacíos, onboarding | 1, 5 | Medio |
| **Gráfico / dato como imagen** | Métricas, mapas, diagramas | 1, 4 | Bajo |
| **3D / render** | Solo si el producto es físico y el render aporta ángulo | 2 | Alto |

Prohibido como sustituto de una decisión: foto de stock genérica de "equipo diverso en oficina", mockup flotante con gráficos falsos, blob 3D abstracto, degradado de malla como "fondo".

Si el proyecto es Perfil 1, **el default es "ninguna"**. Un dashboard con foto decorativa está mal.

## 2. Proporción (bloqueada por grilla, nunca libre)

| Contexto | `aspect-ratio` |
|---|---|
| Moda / vertical / retrato de producto | `4 / 5` |
| Catálogo general, avatar, thumbnail cuadrado | `1 / 1` |
| B2B, maquinaria, hero corporativo | `16 / 10` |
| Editorial, fotografía de autor, hero de landing | `3 / 2` |
| Video, loop de fondo | `16 / 9` |
| Banda ancha de portada (Perfil 3) | `21 / 9` en desktop, `4 / 5` en móvil (art direction) |

Toda imagen de una misma grilla comparte proporción y `object-fit: cover`:

```css
.media { aspect-ratio: 4 / 5; overflow: hidden; background: var(--surface-media); }
.media > img { inline-size: 100%; block-size: 100%; object-fit: cover; object-position: 50% 40%; display: block; }
```

`background: var(--surface-media)` (un neutro cálido o frío, nunca blanco puro) es la red de seguridad: si la imagen falla o tarda, la grilla sigue alineada y no hay destello blanco.

## 3. Presupuesto de peso

| Pieza | Máximo | Formato |
|---|---|---|
| Hero / LCP | 180KB | AVIF (fallback WebP) |
| Imagen de contenido | 120KB | AVIF / WebP |
| Thumbnail de grilla | 60KB | AVIF / WebP |
| Total de imágenes en carga inicial | 500KB | — |
| Loop de video de fondo | 1.5MB, ≤6s, sin audio | H.264 MP4 / VP9 |
| Icono SVG | <3KB | SVG optimizado (sin metadatos del editor) |
| Fuente | <100KB por familia (WOFF2, subset latin) | WOFF2 |

Un original de 4000px en el servidor es normal; **lo que se sirve nunca lo es.**

## 4. Markup correcto

```html
<picture>
  <source
    type="image/avif"
    srcset="hero-640.avif 640w, hero-1024.avif 1024w, hero-1600.avif 1600w, hero-2000.avif 2000w"
    sizes="(min-width: 1200px) 1120px, 100vw">
  <source
    type="image/webp"
    srcset="hero-640.webp 640w, hero-1024.webp 1024w, hero-1600.webp 1600w, hero-2000.webp 2000w"
    sizes="(min-width: 1200px) 1120px, 100vw">
  <img
    src="hero-1024.jpg" width="1600" height="900" alt="Taller de cerámica en La Candelaria, Medellín"
    fetchpriority="high" decoding="async">
</picture>
```

Reglas no negociables:

- `width` + `height` **siempre** (o `aspect-ratio` en el CSS): sin esto no hay CLS ≤0.1.
- `sizes` refleja el ancho **real** del layout, no `100vw` por defecto. Un `sizes` mal puesto descarga la imagen equivocada y tira el presupuesto.
- LCP: `fetchpriority="high"` + `<link rel="preload" as="image" imagesrcset="..." imagesizes="...">` en el `<head>`. **Nunca** `loading="lazy"` en el hero.
- Resto: `loading="lazy"` **y** `decoding="async"`. Lazy solo por debajo del fold: en Safari el lazy del primer viewport llega tarde.
- `2x` solo para retinas reales (avatares, logos), no para fotos: cuadruplica el peso sin ganancia visible.
- Nunca imágenes de fondo en CSS para contenido: no las descubre el preload scanner, no tienen `alt`, no son responsive. `background-image` solo para texturas y patrones decorativos.

## 5. Placeholders, vacíos y fallos

- **Skeleton con la misma proporción** que la imagen final, `opacity` pulsante 1400ms (nunca `background-position`).
- LQIP (16–24px, base64 inline) o color dominante como `background-color` del contenedor. Ambos son gratis en CLS.
- `onerror` → placeholder con el color de la marca y el nombre del producto, no un icono de imagen rota.
- Estado vacío de galería: ilustración de sistema + texto que explica qué falta y qué hacer.

## 6. Matriz de fotos dispares (el bug clásico de e-commerce)

Cuando el cliente entrega 40 fotos de 12 fuentes distintas:

1. Fija `aspect-ratio` por categoría y `object-fit: cover` → la grilla nunca se rompe.
2. `object-position` por producto si el corte decapita el producto (`50% 35%` suele funcionar en vertical).
3. Normaliza el fondo: si no puedes re-fotografiar, aplica un contenedor con `--surface-media` y `padding` interior uniforme (8–12%) para que el producto respire igual en todos.
4. Opcional de nivel estudio: un `filter` común (por ejemplo `saturate(.95) contrast(1.03)`) o duotono con `mix-blend-mode` para unificar temperatura de color. Documenta el filtro como token, no lo repitas por componente.
5. Nunca uses `object-fit: contain` mezclado con `cover` en la misma grilla.

## 7. Texto sobre imagen

- Contraste ≥4.5:1 **medido sobre la zona real** donde cae el texto, no sobre el promedio de la imagen.
- Recurso: scrim con degradado del token (`linear-gradient(to top, rgb(0 0 0/.72), rgb(0 0 0/0) 55%)`), no `filter: brightness()` sobre toda la imagen.
- El texto nunca cae sobre la zona de mayor detalle. Si el encuadre no deja aire, el texto no va encima: va debajo.
- Titulares sobre foto: tamaño ≥ `--fs-h2` + `letter-spacing` negativo + `text-wrap: balance`. Un titular de 20px sobre foto es ilegible siempre.

## 8. Iconografía

- SVG inline o sprite, `currentColor`, caja de **24×24** con trazo de **1.5px** (2px en 32px), esquinas coherentes.
- Alineados a la retícula de 4px; nunca iconos de 18,5px.
- Prohibido: emoji como icono, icon fonts (parpadeo de texto, accesibilidad rota), mezclar dos familias de iconos, iconos de colores distintos en la misma fila.
- Icono + texto es la regla en acciones destructivas o poco comunes; icono solo cuando el símbolo es universal (×, +, ⌕, ←).
- Todo icono-botón necesita `aria-label`.

## 9. Ilustración de sistema (si eliges este camino)

Fija 5 parámetros y no los cambies: **grosor de línea**, **2–3 colores + neutros**, **radio de esquina**, **tipo de relleno** (plano o tramado, nunca degradado), **ángulo/perspectiva**. Genera la serie completa con la misma descripción base y verifica el conjunto lado a lado.

## 10. Imágenes generadas: protocolo de prompt

Un agente que genera imágenes sin protocolo produce un collage de estéticas. Usa esta plantilla:

```
[SUJETO + acción concreta] · [ENCUADRE: plano general/medio/detalle, focal 35/50/85mm]
· [LUZ: una sola fuente, dirección, hora del día, contraste alto/bajo]
· [PALETA: 2–3 colores nombrados + neutros, hex aproximados] · [MATERIAL/TEXTURA: grano 3–5%, papel, hormigón]
· [COMPOSICIÓN: aire negativo del 30–40% en el lado {izq/der} para texto] · [PROHIBIDO: ...]
```

Ejemplo:
> Taller de cerámica en Medellín, manos moldeando barro, plano medio, 50mm · luz de ventana lateral cálida de tarde, sombras suaves · paleta hueso #F2EDE4, terracota #B4451F, verde seco #5A6350 · grano fino 4% · aire negativo amplio a la izquierda para titular · PROHIBIDO: oficina genérica, sonrisa a cámara, degradados, brillo plástico, texto en la imagen, manos deformes.

Reglas de serie: misma descripción base para todas las imágenes del set, cambiando solo el sujeto; misma luz y misma paleta. **Revisa la imagen generada antes de entregarla** (manos, texto inventado, simetría, número de dedos, marcas falsas). Si contiene texto, descártala: el texto va en HTML.

Prohibido generar: capturas de dashboards con datos falsos presentadas como producto, logos de terceros, personas reales identificables, y cualquier imagen con texto incrustado.

## 11. Video

- `poster` obligatorio, `muted`, `playsinline`, `loop`, `preload="none"`, sin controles si es decorativo y sin audio nunca.
- Autoplay solo si: `prefers-reduced-motion: no-preference`, loop ≤6s y ≤1.5MB. En caso contrario, poster + botón de play.
- El video **nunca** es el elemento LCP: el poster es una imagen y se prioriza como tal.
- En conexiones lentas (`navigator.connection.saveData` o `effectiveType` 2g/3g) no cargues el video.

## 12. `alt` y accesibilidad de medios

- `alt` describe la función o el contenido, no la apariencia: "Zapatilla de trail roja, perfil lateral" ✓ / "imagen" ✗.
- Decorativa → `alt=""` (nunca omitir el atributo).
- Imagen que es enlace → `alt` describe el destino.
- Gráficos con datos → tabla o resumen textual equivalente, no solo `alt`.
- Fotos de autor (Perfil 4) con pie de foto en HTML (`<figcaption>`), no incrustado en la imagen.

## Checklist

- [ ] Tratamiento declarado y coherente con el perfil.
- [ ] `aspect-ratio` + `object-fit: cover` + fondo de respaldo en toda grilla.
- [ ] `width`/`height` en toda imagen (CLS = 0 por medios).
- [ ] LCP con `fetchpriority="high"` y preload; nada de lazy en el primer viewport.
- [ ] AVIF/WebP servidos, `sizes` real, presupuesto de peso respetado.
- [ ] Placeholder/skeleton con la proporción correcta.
- [ ] Texto sobre imagen con scrim y contraste verificado.
- [ ] Iconos SVG `currentColor` 24px, una sola familia.
- [ ] Series de imágenes consistentes (luz, paleta, ángulo).
- [ ] `alt` útil en todas; decorativas con `alt=""`.
