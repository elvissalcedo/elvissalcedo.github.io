# Git_Page

Sitio personal de Elvis Salcedo, ingeniero ambiental — "Elvis Salcedo |
Ingeniería Ambiental" — publicado en GitHub Pages
(`elvissalcedo.github.io`, repo `elvissalcedo/elvissalcedo.github.io`).

Este repo es ahora **el proyecto completo y autosuficiente**: instrucciones
de redacción, herramienta de conversión y el sitio en sí viven todos acá.
Ya no hace falta abrir ningún otro repositorio para el flujo normal de
publicar un artículo.

## Las 3 piezas del flujo de publicación

- **La skill de NotebookLM** ([02-instrucciones-notebooklm.md](02-instrucciones-notebooklm.md)):
  documento fuente que se sube a NotebookLM junto con el PDF del dosier y
  los artículos del radar. Define todo lo que no es contenido técnico:
  cómo identificar la fuente principal (su segunda línea en cursiva
  "Sub-tema TEMA-XXXX -- tema padre: ..."), reglas de citas APA 7
  completas, el método Feynman para explicar cada término técnico nuevo,
  la estructura narrativa fija de 7 bloques con títulos de sección
  creativos, el formato de salida Markdown exacto (fórmulas en LaTeX
  real, `\[...\]`/`\(...\)`, único formato -- ya no hay flujo alternativo
  en Unicode), la Guía de imágenes y la sección de Vacíos del
  conocimiento.
- **El prompt corto** ([03-prompt-notebooklm.txt](03-prompt-notebooklm.txt)):
  lo que Elvis pega en el chat de NotebookLM cada vez que pide un artículo
  nuevo. Checklist resumido de las reglas ya subidas en la pieza anterior
  -- no las reemplaza, es el recordatorio rápido para la sesión puntual.
  Deja que NotebookLM decida en cuántos mensajes entregar la respuesta
  según el contenido real, esperando "continuar" entre cada uno.
- **El Conversor a Git Page** ([conversor.html](conversor.html)): parser
  Markdown -> HTML hecho a mano en JS vanilla, sin build ni dependencias
  externas. Reconoce el formato que exige la pieza 1 (fórmulas LaTeX
  protegidas de la negrita/cursiva del resto del parser, tablas, imágenes
  como placeholder `[IMAGEN N]`), excluye siempre "## Guía de imágenes" y
  opcionalmente "## Preguntas / Vacíos del conocimiento", y reordena
  automáticamente la lista de Referencias por orden alfabético. Elvis
  pega acá el Markdown que copia directo del bloque de código de
  NotebookLM (sin pasar por Google Docs) y obtiene el HTML final para
  publicar en el sitio.

## El sitio

- `index.html` — portada.
- `articulo-ejemplo.html` — plantilla de artículo (carga MathJax en el
  `<head>`, ver decisión de diseño abajo).
- `lavador-venturi.html` — primer artículo real publicado.
- `prueba-latex.html` — página de prueba técnica (`noindex`) para
  verificar el renderizado de MathJax en el sitio publicado.
- `css/`, `js/`, `assets/`, `articulos/` — estilos, scripts e imágenes del
  sitio.
- `sitemap.xml`, `robots.txt` — SEO técnico.

## Decisiones de diseño importantes

- **Fórmulas siempre en LaTeX real, renderizadas por MathJax.** El sitio
  carga MathJax (CDN, versión fijada 3.2.2, mismo criterio de fijar
  versión que cualquier otra dependencia de CDN) configurado para los
  delimitadores `\(...\)` (inline) / `\[...\]` (bloque) que entrega
  NotebookLM -- sin `$...$`, para no chocar con montos en soles/dólares
  que puedan aparecer en el texto. MathJax solo procesa el texto que trae
  esos delimitadores; el HTML del artículo del Venturi (en Unicode/
  `.fraccion`, de la época en que convivían dos flujos) no los trae, así
  que queda intacto. `.formula-latex` (en `css/styles.css`) solo centra
  el párrafo contenedor; el espaciado y centrado del bloque matemático en
  sí los pone MathJax.
- **El Conversor NO desescapa caracteres.** A diferencia de un conversor
  pensado para texto que pasó por exportación de Google Docs, acá el
  Markdown viene directo del bloque de código de NotebookLM, así que no
  hay barras invertidas de escape que limpiar antes de interpretar la
  línea.
- **Tipografía Lora/Sora.** El cuerpo del artículo usa Lora serif
  (17px/1.6) por legibilidad en texto largo de divulgación. Los títulos
  (h2/h3) van en Spectral serif. Sora es la fuente de los elementos de
  interfaz (navegación, fecha/etiquetas), y JetBrains Mono para el
  detalle técnico (byline, fechas, etiquetas).

## Historial de cambios recientes

- 2026-09-17: consolidación -- se trae a este repo todo lo necesario para
  trabajar sin depender de Bitácora-Verde-Blog: `02-instrucciones-notebooklm.md`
  (fusiona las instrucciones de síntesis con el flujo LaTeX, que pasa de
  alternativa a única regla de fórmulas), `03-prompt-notebooklm.txt`
  (prompt corto simplificado, un solo camino) y `conversor.html` (copiado
  del Conversor a Git Page). Bitácora-Verde-Blog queda congelado como
  archivo histórico del período en que el blog vivía en Blogger -- no se
  le hacen más commits.
- 2026-09-17: publica el artículo del lavador Venturi y agrega soporte
  MathJax/LaTeX (`articulo-ejemplo.html`, `prueba-latex.html`).
- 2026-09-17: retira `about.html` del sitio publicado hasta tener más
  contenido (recuperable del historial de git).
- 2026-09-12: primer despliegue -- frontend base del sitio (portada,
  identidad Lora/Sora, SEO técnico, CSS de fórmulas).

## Mantenimiento de este archivo

Cada vez que hagas un commit real en este proyecto, agregá UNA línea
breve a "Historial de cambios recientes" arriba, como parte del MISMO
commit -- no reescribas el archivo entero, solo sumá la novedad. Si el
cambio afecta una decisión de diseño ya descrita arriba, actualizá esa
sección puntual también, sin tocar el resto.
