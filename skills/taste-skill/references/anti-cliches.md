# Anti-clichés: el look "hecho por IA"

Estos patrones no son feos por sí solos: son **frecuentes**. Su frecuencia es lo que los convierte en ruido. La regla general: si lo has visto en diez landings esta semana, no lo uses.

## Lista negra A — Layout

| Prohibido | Sustitución |
|---|---|
| 3 tarjetas idénticas centradas ("features") | Bento asimétrico 2/3+1/3, o lista editorial con numeración grande |
| Hero centrado con H1 + párrafo + 2 botones + degradado | Hero asimétrico 5/7 u 8/4, con prueba concreta al lado |
| 6 secciones con el mismo ancho y todo centrado | Ritmo alternado: Z → bento → full-bleed → cifras → prueba → cierre |
| "Trusted by" con logos inventados en gris | Cifras verificables, reseñas con nombre y fecha, o nada |
| Sección "Cómo funciona" en 3 pasos con círculos numerados | Cualquier otra cosa: captura real, comparación antes/después, demo |
| Footer con 5 columnas y 40 enlaces | 3–4 columnas con lo que la gente usa |
| Rejilla de 9 cards en el blog | 1 destacado + lista |
| Borde de sección con "wave/blob" SVG | Corte recto, margen generoso |

## Lista negra B — Estética

- **Degradado violeta→azul** (o morado→rosa) en hero, botón o texto. Es la firma visual del default.
- **Glassmorphism global**: `backdrop-filter: blur()` en cards, nav y modales a la vez.
- **Blob 3D abstracto** como ilustración de "IA", "seguridad" o "velocidad".
- **Mockup flotante en perspectiva** con dashboard de gráficos falsos.
- **Mesh gradient / aurora** de fondo sin relación con la marca.
- Iconos de tres familias distintas (una línea, una rellena, un emoji).
- **Sombra difusa gigante** en todas las cards (`0 20px 60px rgba(0,0,0,.12)`).
- `border-radius` de 24px en todo, incluidos inputs y tablas.
- Tipografía única (Inter) en todos los niveles sin contraste óptico.
- Emoji como icono de features ✅🚀🔥.
- Texto en `gradient-clip` en el titular.
- **Contador animado** de cifras inventadas.
- Fotos de stock de "equipo diverso en oficina con laptop".
- Fondo `#F9FAFB` + texto `#111827` + acento `#6366F1` (la paleta por defecto de todo generador).

## Lista negra C — Copy y contenido

- "Lorem ipsum", "Tu texto aquí", "Company Name", "John Doe".
- "Potencia tu negocio con soluciones innovadoras" (nada concreto, nada medible).
- "El futuro de X", "Revoluciona", "Sin esfuerzo", "De próxima generación".
- Español traducido del inglés: "hacemos que el diseño sea fácil" ✗ / "diseñamos en 2 semanas" ✓.
- Secciones vacías de prueba social sin datos: "★★★★★ Excelente" sin autor.
- CTA genéricos: "Enviar", "Más información", "Comenzar". Un CTA dice **qué pasa** al pulsarlo: "Ver precios", "Reservar llamada de 20 min".

## Lista negra D — Interacción

- Carrusel automático de testimonios o logos.
- Typewriter en el H1.
- Cursor personalizado siguiendo el mouse.
- Tilt 3D en cada card.
- Parallax en móvil.
- Animación de entrada en cada sección al hacer scroll.
- Marquesina infinita de texto.
- Scroll hijacking (secuestro del scroll para una timeline).
- Preloader de 3 segundos con logo animado.
- Hover como único lugar donde aparece información crítica.

## Lista negra E — Técnica

- `!important` para ganar cascada.
- `position: absolute` para maquetar en lugar de flujo/grilla.
- `100vh` en móvil (usa `dvh`/`svh`).
- `max-width: 35ch` en móvil (deja hueco a la derecha).
- `outline: none` sin sustituto de foco.
- `z-index: 9999`.
- Colores hex sueltos en componentes cuando existen tokens.
- `onClick` en `div` sin rol ni teclado.
- Imágenes sin `width`/`height`.
- `background-image` para contenido con `alt`.

---

## Cómo sustituir un cliché (método en 3 pasos)

1. **Nombra la función** que el cliché cumplía (dar ritmo, mostrar prueba, agrupar features).
2. **Elige un recurso del sistema** que cumpla la misma función sin el patrón gastado (retícula visible, numeración grande, tipografía como imagen, dato duro, captura real, asimetría).
3. **Verifica** que el recurso elegido sea coherente con la dirección estética declarada en el bloque `ESTÉTICA`. Si no lo es, la dirección estética está mal, no el recurso.

## Test rápido de genérico (30 segundos)

- ¿Podría ser de otra empresa del mismo sector cambiando el logo? → falla.
- ¿Hay **una** decisión de diseño que solo tiene sentido para este contenido? → si no, falla.
- ¿La página se apoya en cifras, hechos o imágenes propias? → si no, falla.
- ¿Alguna sección repite exactamente la estructura de la anterior? → falla.
