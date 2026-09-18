# Git_Page

Sitio personal de Elvis Salcedo, ingeniero ambiental — "Elvis Salcedo |
Ingeniería Ambiental" — publicado en GitHub Pages con Jekyll nativo
(`elvissalcedo.github.io`, repo `elvissalcedo/elvissalcedo.github.io`).

Este repo es **el proyecto completo y autosuficiente**: instrucciones de
redacción y el sitio en sí viven todos acá. Publicar un artículo nuevo no
requiere terminal ni ningún build local -- se hace entero desde el editor
web de github.com.

## El flujo de publicación (sin terminal)

- **La skill de NotebookLM** ([02-instrucciones-notebooklm.md](02-instrucciones-notebooklm.md)):
  documento fuente que se sube a NotebookLM junto con el PDF del dosier y
  los artículos del radar. Define todo lo que no es contenido técnico:
  cómo identificar la fuente principal (su segunda línea en cursiva
  "Sub-tema TEMA-XXXX -- tema padre: ..."), reglas de citas APA 7
  completas, el método Feynman para explicar cada término técnico nuevo,
  la estructura narrativa fija de 7 bloques con títulos de sección
  creativos, el formato de salida Markdown exacto (fórmulas en LaTeX real
  con el backslash **duplicado** en los 4 delimitadores -- `\\[...\\]`/
  `\\(...\\)`, ver la nota de kramdown más abajo), la Guía de imágenes y
  la sección de Vacíos del conocimiento.
- **El prompt corto** ([03-prompt-notebooklm.txt](03-prompt-notebooklm.txt)):
  lo que Elvis pega en el chat de NotebookLM cada vez que pide un artículo
  nuevo. Checklist resumido de las reglas ya subidas en la pieza anterior
  -- no las reemplaza, es el recordatorio rápido para la sesión puntual.
  Deja que NotebookLM decida en cuántos mensajes entregar la respuesta
  según el contenido real, esperando "continuar" entre cada uno.
- **Publicar en github.com** (sin Conversor, sin Google Docs, sin build
  local): Elvis crea un archivo nuevo en `_posts/AAAA-MM-DD-slug.md` desde
  el editor web de GitHub, pega el front matter estándar (`layout: post`,
  `title`, `date`, `category`, `excerpt`) seguido del Markdown que copió
  del bloque de código de NotebookLM tal cual, reemplaza cada
  `[IMAGEN N -- título]` por `![alt](/assets/imagenes/slug/archivo.jpg)`,
  sube las imágenes a esa misma carpeta con **Add file → Upload files**, y
  confirma el commit a `main`. Jekyll arma solo el índice, el menú de
  categorías y la plantilla del artículo -- no hay que tocar `index.html`
  ni ningún otro archivo a mano. Editar o borrar un artículo publicado es
  abrir su `.md` y usar el lápiz o el tacho del editor web, igual que con
  cualquier otro archivo del repo.

## El sitio (Jekyll)

- `_config.yml` — config de Jekyll: `kramdown.math_engine: null` (clave:
  en YAML es `null`, no `nil` -- `nil` es un string literal y rompe el
  build), lista de plugins (`jekyll-feed`, `jekyll-sitemap`,
  `jekyll-seo-tag`) y la lista única `categorias` (nombre + slug) que
  alimenta el menú y las páginas de categoría -- se edita en un solo
  lugar, nunca a mano en cada archivo.
- `_layouts/default.html` — `<head>` (incluye `{% seo %}` y MathJax),
  header/footer (`_includes/`), `{{ content }}`.
- `_layouts/post.html` — plantilla de artículo: título, fecha (formateada
  en español vía `_includes/fecha-es.html`, GitHub Pages no permite
  plugins de localización), categoría, `.article-layout` (post-body + TOC
  flotante armado por `assets/js/toc.js`, sin cambios de lógica).
- `_layouts/category.html` — loop de `site.posts` filtrado por
  `page.category`, con aviso "próximamente" si la categoría está vacía.
- `_posts/` — un artículo por archivo, `AAAA-MM-DD-slug.md`. El primer
  artículo real (`lavador-venturi.html` original) vive acá como
  `2026-09-17-lavador-venturi.md`, con `permalink: /lavador-venturi.html`
  para no romper la URL ya publicada.
- `categorias/*.html` — 8 archivos, solo front matter (`layout: category`
  + `category: <Nombre>`), uno por categoría del menú.
- `index.html` — portada; `layout: default` + loop de Liquid sobre
  `site.posts`, ya no se edita a mano.
- `assets/css/styles.css`, `assets/js/toc.js`, `assets/imagenes/<slug>/` —
  estilos, scripts e imágenes por artículo. `assets/hero-banner.jpg`,
  `foto-perfil.png`, `og-cover.jpg` son assets de marca, van sueltos en
  `assets/` (no por artículo).
- `02-instrucciones-notebooklm.md`, `03-prompt-notebooklm.txt` — excluidos
  del build (`exclude:` en `_config.yml`): se usan fuera del sitio (se
  suben a NotebookLM), no tienen por qué publicarse.
- `robots.txt` — sin cambios. `sitemap.xml`/`feed.xml` ya no se escriben a
  mano -- los generan `jekyll-sitemap`/`jekyll-feed` en cada build.

## Decisiones de diseño importantes

- **Fórmulas siempre en LaTeX real, renderizadas por MathJax.** El sitio
  carga MathJax (CDN, versión fijada 3.2.2) configurado para los
  delimitadores `\(...\)` (inline) / `\[...\]` (bloque) -- sin `$...$`,
  para no chocar con montos en soles/dólares que puedan aparecer en el
  texto.
- **kramdown se come el backslash simple de `\(` `\)` `\[` `\]` -- por
  eso NotebookLM entrega esos 4 delimitadores con el backslash
  DUPLICADO.** Esto no es configurable: kramdown tiene una regla de
  escape de Markdown fija (`ESCAPED_CHARS`, en su código fuente, no en
  `_config.yml`) que borra un backslash antes de cualquier paréntesis o
  corchete, sin importar `math_engine`. Confirmado con una build local
  real (no es una suposición): `\(q_i\)` en el Markdown fuente llega como
  `(q_i)` al HTML final -- la fórmula se rompe en el sitio. La solución
  validada es que NotebookLM entregue `\\(...\\)`/`\\[...\\]` (backslash
  duplicado SOLO en los 4 delimitadores; el resto del LaTeX interno --
  `\frac`, `\cdot`, `\rho`, etc. -- va con backslash simple, normal, ya
  que las letras no están en el set de caracteres que kramdown escapa).
  Con eso, kramdown deja pasar exactamente `\(...\)`/`\[...\]` al HTML, y
  MathJax los renderiza sin tocar nada más del diseño. El post oculto
  `_posts/2026-09-17-articulo-ejemplo.md` (no aparece en el índice ni en
  el sitemap, `hidden: true` + `sitemap: false`) es el banco de pruebas
  real de este comportamiento -- si alguna vez se toca `_config.yml` o se
  actualiza kramdown, revisar ese artículo primero.
- **HTML crudo pegado en un `.md`: cuidado con tags inline pegados a
  tags de bloque en la misma línea.** kramdown solo reconoce un bloque de
  HTML crudo si la línea empieza con un tag de bloque conocido (`<p>`,
  `<div>`, `<ul>`, etc.). Un `<img>` (tag inline) seguido en la misma
  línea por `<p>...</p>` rompe esa detección y el `<p>` queda escapado
  como texto literal en vez de renderizarse. Si se pega HTML crudo
  directo en un `.md` (migración puntual, no el flujo normal en Markdown
  puro), cada elemento de bloque va en su propia línea.
- **`.formula-latex` (en `assets/css/styles.css`) solo centra el párrafo
  contenedor** -- el espaciado y centrado del bloque matemático en sí los
  pone MathJax (`mjx-container[display="true"]` ya centra por defecto,
  así que artículos nuevos en Markdown puro se ven bien sin necesidad de
  esa clase).
- **Tipografía Lora/Sora.** El cuerpo del artículo usa Lora serif
  (17px/1.6) por legibilidad en texto largo de divulgación. Los títulos
  (h2/h3) van en Spectral serif. Sora es la fuente de los elementos de
  interfaz (navegación, fecha/etiquetas), y JetBrains Mono para el
  detalle técnico (byline, fechas, etiquetas).

## Historial de cambios recientes

- 2026-09-18: borra dos huérfanos de la etapa pre-Jekyll -- `conversor.html`
  (herramienta obsoleta, queda en el historial de git) y `prueba-latex.html`
  (duplicaba a mano header/nav/MathJax y se colaba en el sitemap pese al
  `noindex`; el banco de pruebas real es `_posts/2026-09-17-articulo-ejemplo.md`,
  que sí pasa por kramdown).
- 2026-09-18: commit de la migración a Jekyll nativo -- tarjetas de
  artículo con miniatura (`post-card.html`, grid reusable en `.posts`)
  para portada y las 8 páginas de categoría (comparten `_layouts/category.html`,
  nunca HTML repetido por categoría), estandarización de "Donde:" en texto
  plano, pasos de sustitución numérica en líneas separadas y label único
  "Nota técnica:" (`02-instrucciones-notebooklm.md`, `03-prompt-notebooklm.txt`
  actualizados como reglas fijas), `Gemfile`/`.gitignore` agregados para
  build local con `bundle exec jekyll serve` (`_site/` e ignorados fuera
  del repo).
- 2026-09-18: migración completa a Jekyll nativo de GitHub Pages --
  `_config.yml`, `_layouts/`, `_includes/`, `_posts/` (migra
  `lavador-venturi.html` y `articulo-ejemplo.html`, este último oculto
  como banco de pruebas), `categorias/*.html` generadas por Liquid,
  `index.html` ahora con loop de posts. `css/`, `js/`, `articulos/` pasan
  a `assets/`. Publicar ya no depende del Conversor -- es crear un `.md`
  en `_posts/` desde el editor web de github.com. Encontrado y corregido
  durante la migración: kramdown borra el backslash simple de
  `\(`/`\)`/`\[`/`\]` sin importar `math_engine` -- NotebookLM ahora
  entrega esos 4 delimitadores con backslash duplicado (`02-instrucciones-notebooklm.md`,
  `03-prompt-notebooklm.txt` actualizados).
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
