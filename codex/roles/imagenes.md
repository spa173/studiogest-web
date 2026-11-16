# Rol para Codex: Imágenes

Diseño web: sistema de medios de la skill `taste-skill`. 4 decisiones antes de `<img>` (tratamiento → proporción por grilla con `aspect-ratio` y `object-fit` → presupuesto de peso (hero ≤180KB; AVIF→WebP→JPEG) → consistencia de serie). `srcset`/`sizes` real, `fetchpriority="high"` en el LCP, `aspect-ratio` siempre y placeholders sin CLS; revisa toda imagen generada antes de entregarla. Si la skill no está instalada globalmente, dilo y detente.
