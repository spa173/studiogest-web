# Evals de `taste-skill`

Una skill sin evals es una hipótesis. Estas pruebas se corren **en sesión limpia**, sin mencionar la skill, la escala ni los tokens, y sin decirle al agente qué perfil elegir.

## Protocolo

1. Sesión nueva, sin historial. Pega el prompt tal cual.
2. Registra: ¿se activó la skill? ¿emitió el contrato de 4 líneas? ¿el perfil es el correcto?
3. Corre `python3 scripts/audit_taste.py <salida> --profile <N>`.
4. Puntúa con la rúbrica de abajo. **Objetivo: ≥ 8/10 en las 8 pruebas.**

## Rúbrica (10 puntos)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Activación correcta (se usa cuando debe, no cuando no debe) | 2 |
| 2 | Contrato de 4 líneas presente y coherente con el código | 2 |
| 3 | Perfil y escala correctos para el tipo de proyecto | 1 |
| 4 | Auditor sin errores (warnings justificados) | 2 |
| 5 | Cero patrones de `references/anti-cliches.md` | 1 |
| 6 | Movimiento con `reduce`, salidas correctas y un solo momento hero | 1 |
| 7 | Medios con proporción, dimensiones y LCP correctos | 1 |

---

## E1 · Landing de SaaS (el caso ambiguo)

> "Hazme la web de mi SaaS de facturación para restaurantes. Que se vea profesional y convierta."

- **Esperado:** Perfil 3 (landing comercial) y lo declara; **no** construye un dashboard. Menciona que el dashboard interno sería Perfil 1.
- **Falla si:** entrega un mockup de app, tres cards de features, hero centrado con degradado, o un h1 de 110px.
- **Extra:** el CTA principal es visible a 1366×768 sin scroll.

## E2 · Dashboard de finanzas

> "Necesito la pantalla de cartera de mi app: tabla de facturas, filtros y KPIs."

- **Esperado:** Perfil 1; escala doble 1.067/1.25; `tabular-nums` en importes; sin sombras difusas; cabecera sticky; estados vacío/error/carga.
- **Falla si:** usa tipografía fluida, hero decorativo, anima entradas, o centra los importes.

## E3 · E-commerce con fotos dispares

> "Tienda de zapatillas. Tengo fotos de proveedores de tamaños distintos."

- **Esperado:** Perfil 2; `aspect-ratio: 4/5` + `object-fit: cover` + fondo de respaldo; precio/valoración/acción visibles sin hover; ciclo de estados de compra.
- **Falla si:** deja el precio en el hover, mezcla proporciones o usa `contain` y `cover`.

## E4 · Landing en español con titular largo

> "Landing para una consultora de ciberseguridad en Medellín. El titular es 'Protegemos la operación de empresas que no pueden detenerse'."

- **Esperado:** mide el titular con el texto real, techo ≤76px, `text-wrap: balance`, sin palabra huérfana, CTA en el primer viewport a 1366px.
- **Falla si:** aplica 1.618 en cascada, o el titular ocupa 4+ líneas y empuja el CTA fuera.

## E5 · Artículo largo

> "Página de artículo para nuestro blog: 2.500 palabras, con índice y fotos."

- **Esperado:** Perfil 4; medida 62–72ch; 3 niveles de tinta; TOC sticky con `scroll-margin-top`; casi cero movimiento.
- **Falla si:** texto justificado, 100 caracteres por línea, TOC sin estado activo, animación por párrafo.

## E6 · Animaciones sin librería

> "Agrega animaciones al lanzamiento del hero y transiciones entre páginas, sin que pese."

- **Esperado:** View Transitions + `@starting-style`; scroll-driven dentro de `@supports`; `reduce`; un solo momento de nivel 3; ≤500ms; sin librería.
- **Falla si:** importa GSAP/Framer para un fade, anima `height`, o no implementa `prefers-reduced-motion`.

## E7 · Imágenes generadas consistentes

> "Genera las 4 imágenes de la sección de producto de una marca de café de especialidad."

- **Esperado:** protocolo de prompt (sujeto, encuadre, luz, paleta, grano, aire negativo); serie coherente; `alt` útil; proporción fija; describe el set antes de generarlo.
- **Falla si:** cuatro estéticas distintas, texto incrustado en la imagen, manos deformes sin corregir, o "stock de oficina".

## E8 · Auditoría de código ajeno

> "Revisa este CSS y dime qué está mal: [pega CSS con 37px, padding 13px, outline:none, height 100vh]"

- **Esperado:** nombra las leyes violadas con el código (`T02-grilla`, `T05-foco`…), propone el token concreto y corre el auditor.
- **Falla si:** da opiniones genéricas ("podrías mejorar el espaciado") sin números.

## Regresión del auditor

```bash
python3 scripts/audit_taste.py evals/fixtures --profile 1   # debe FALLAR con 11 errores
python3 scripts/audit_taste.py assets      --profile 3      # debe PASAR con 0 errores
```

Si la primera orden devuelve menos de 11 errores, el auditor perdió una regla. Si la segunda devuelve alguno, los assets de referencia se degradaron.

## Anti-test · no debe activarse

> "Refactoriza el endpoint `/api/orders` para paginar con cursor."

- **Esperado:** la skill no se activa (sin cambio visual). Si se activa y empieza a hablar de tipografía, la descripción está demasiado amplia.

---

## Cómo iterar cuando una prueba falla

| Síntoma | Arreglo |
|---|---|
| No se activa | Añade a `description` las palabras literales del prompt que falló |
| Se activa de más | Acota los disparadores (y añade el "no usar para…") |
| Ignora las leyes | Mueve la ley al §2 de `SKILL.md`; lo que vive solo en `references/` se lee menos |
| Rompe el layout en español | Revisa que el techo de 76px y el paso de 3 anchos estén en el contrato |
| Inventa valores | Reforzar: "si no hay token, propone uno nuevo, no un valor suelto" |
| Se le olvida el movimiento | Añadir el nivel de movimiento al contrato (ya está: línea 4) |
