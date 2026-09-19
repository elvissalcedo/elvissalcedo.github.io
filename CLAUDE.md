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
  la estructura narrativa elegida caso por caso entre 7 bloques posibles
  (solo Desarrollo técnico y Referencias son obligatorios; NotebookLM
  propone la estructura en un mensaje corto y espera el "ok" de Elvis) con
  títulos de sección creativos, el bloque de front matter listo para pegar, el formato de
  salida Markdown exacto (fórmulas en LaTeX real
  con el backslash **duplicado** en los 4 delimitadores -- `\\[...\\]`/
  `\\(...\\)`, ver la nota de kramdown más abajo), la Guía de imágenes y
  la sección de Vacíos del conocimiento.
- **El prompt corto** ([03-prompt-notebooklm.txt](03-prompt-notebooklm.txt)):
  lo que Elvis pega en el chat de NotebookLM cada vez que pide un artículo
  nuevo. Ya no repite las reglas: remite al documento fuente y solo marca
  los pasos de la sesión (identificar el dosier, proponer la estructura y
  esperar el "ok", un bloque de código por mensaje, autocrítica final).
  Deja que NotebookLM decida en cuántos mensajes entregar la respuesta
  según el contenido real, esperando "continuar" entre cada uno.
- **Publicar en github.com** (sin Conversor, sin Google Docs, sin build
  local): Elvis crea un archivo nuevo en `_posts/AAAA-MM-DD-slug.md` desde
  el editor web de GitHub y pega, en este orden, el front matter y el
  cuerpo tal como se los entregó NotebookLM. **El front matter lo redacta
  NotebookLM**, no Elvis: viene al principio del bloque de código único del
  primer mensaje (cada mensaje de la entrega va completo en un solo bloque,
  sin bloques anidados) con `layout`,
  `title`, `category`, `excerpt` e `image` ya completos, y solo hay que
  poner la fecha real donde dice `date: AAAA-MM-DD`. El cuerpo arranca en
  el primer `## ` -- el título no se repite ahí, lo imprime el layout.
  Después reemplaza cada `[IMAGEN N — título]` por el bloque
  `<figure class="post-figure">` que la Guía de imágenes ya dejó armado,
  completando la ruta `/assets/imagenes/<slug>/<archivo>`, sube las
  imágenes a esa misma carpeta con **Add file → Upload files**, y confirma
  el commit a `main`. **Lo que NO se pega:** la sección
  `## Guía de imágenes` se queda siempre en el chat de NotebookLM (es
  material de trabajo, trae rutas locales y prompts); `## Preguntas /
  Vacíos del conocimiento` se publica o no según el artículo -- el del
  Venturi la publica. Nada de esto se filtra solo: se publica exactamente
  el texto pegado. Jekyll arma solo el índice, el menú de
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
  flotante armado por `assets/js/articulo.js`).
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
- `assets/css/styles.css`, `assets/js/articulo.js`, `assets/imagenes/<slug>/` —
  estilos, scripts e imágenes por artículo. `assets/hero-banner.jpg`
  (2400x745, fondo del header), `og-cover.jpg` (1200x630, la tarjeta de Open
  Graph que sale al compartir) y `foto-perfil.png` son assets de marca, van
  sueltos en `assets/` (no por artículo). Antes de subir una imagen conviene
  dejarla en el ancho que de verdad se usa: una foto de cámara o de banco sin
  tocar pesa 3 MB y el sitio no necesita ni el 10 % de eso.
- `02-instrucciones-notebooklm.md`, `03-prompt-notebooklm.txt` — excluidos
  del build (`exclude:` en `_config.yml`): se usan fuera del sitio (se
  suben a NotebookLM), no tienen por qué publicarse.
- `robots.txt` — sin cambios. `sitemap.xml`/`feed.xml` ya no se escriben a
  mano -- los generan `jekyll-sitemap`/`jekyll-feed` en cada build.

## Automatización (GitHub Actions)

- `.github/workflows/validar.yml` corre en cada push a `main` y en cada PR.
  Dos trabajos, los dos de solo lectura: uno pasa
  `.github/scripts/validar_articulos.py` sobre `_posts/`, el otro hace el
  build real de Jekyll con el mismo bundle `github-pages` que usa producción
  y comprueba que se generen `index.html`, `sitemap.xml` y `feed.xml` y que
  el post oculto siga fuera del índice y del sitemap.
- El validador revisa lo que ya se rompió alguna vez de verdad: front matter
  incompleto, `category:` que no es ninguna de las 8 de `_config.yml`, fecha
  del front matter distinta de la del nombre del archivo, `image:` o `<img>`
  apuntando a un archivo que no se subió, imágenes sin `alt`, `<figure>` sin
  su `<figcaption>`, delimitadores de fórmula con un solo backslash, el
  título repetido al principio del cuerpo y assets pesados (aviso arriba de
  500 KB, error arriba de 1500 KB).
- **Es una red de seguridad, no un portón.** GitHub Pages publica por su
  cuenta, en paralelo: si el workflow falla, el artículo igual salió, pero
  Elvis recibe el aviso en vez de enterarse semanas después. Convertirlo en
  portón real exige pasar el despliegue a Actions (`actions/deploy-pages`),
  que es un cambio grande y no se hizo.
- La regla del backslash tiene una salvedad que el validador respeta: en una
  línea que arranca con un tag HTML de bloque, kramdown no parsea Markdown y
  el backslash simple llega intacto. Por eso el artículo del Venturi, migrado
  desde HTML plano, pasa la validación con `\[...\]` de un solo backslash.

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

- 2026-09-19: `02-instrucciones-notebooklm.md` corrige dos errores reales del
  artículo de biofiltros -- la sección 6 exige copiar el `[N, p. X]` de una
  imagen EXACTO tal como aparece en el dosier (nunca reconstruirlo de memoria,
  ni mezclar el autor de una entrada con la página de otra) y la sección 3
  exige citar decretos/normas legales con el organismo emisor como autor
  (nunca el código del decreto suelto) y agregar SIEMPRE su entrada en
  Referencias aunque el dosier no lo liste como `[HECHO-N]`. Suma los dos
  ítems correspondientes al checklist de la sección 8.
- 2026-09-19: `02-instrucciones-notebooklm.md`, análisis de arquitecto de punta
  a punta -- eleva la regla de `[HECHO-N]` y las imágenes-como-fuente a la
  sección 2 (Jerarquía de fuentes), suma 3 ítems al checklist final de la
  sección 8 (autor real por `[HECHO-N]`, apartarse del orden del dosier,
  imágenes de texto revisadas) para que no queden solo mencionados y nunca
  verificados, agrega reglas contra desarrollar una fórmula propia y contra
  heredar el tono institucional del dosier, y permiso explícito de que
  reordenar hechos no es un riesgo de inventar contenido. Elvis confirmó que
  limpia el chat de NotebookLM antes de cada artículo nuevo, así que se
  reformulan las reglas anti-repetición (títulos, tablas, digresión, mensaje
  de estructura) que asumían memoria entre artículos -- pasan a ser
  autochequeos dentro del artículo actual; esa misma corrección se aplicó a
  dos reglas que se habían agregado en el mismo commit por el mismo motivo.
- 2026-09-18: `02-instrucciones-notebooklm.md` corrige dos fallas reales de
  NotebookLM -- la sección 4 agrega la regla "no calques el orden del dosier"
  (el orden de ficha técnica del dosier no es un orden narrativo, y el
  mensaje corto de estructura debe explicar en qué se aparta de él) y la
  sección 6 aclara que una imagen de página de texto es fuente de contenido
  a leer e incorporar al Desarrollo técnico, no solo una opción para la Guía
  de imágenes. De paso se corrige voseo preexistente en la sección 4
  ("planificá", "decidí vos", "buscá", "Variá", "alterná", "señalá", "hacé",
  "cambiá", "mandale", "Esperá"), que violaba la regla de español neutro de
  la sección 1.
- 2026-09-18: la sección 3 de `02-instrucciones-notebooklm.md` aclara que el
  sistema `[HECHO-N]` del dosier siempre tiene un autor real y rastreable en
  su propia lista de Referencias -- la regla de "sin autor identificable,
  cita por el título" nunca aplica al dosier en sí mismo. Corrige un error
  real encontrado en un artículo: 68 autocitas al título del dosier tratado
  como autor anónimo.
- 2026-09-18: la sección 4 de `02-instrucciones-notebooklm.md` reemplaza el
  menú fijo de 7 bloques (Gancho, Explicación/analogía, Desarrollo técnico,
  Conflicto/complejidad, Digresión conectada, Cierre, Referencias) por
  reglas concretas contra el "efecto fábrica" (nada de muletillas repetidas,
  variar largo de párrafo y sintaxis, no repetir cantidad de subtítulos,
  tabla solo si aporta, chequeo final de que no se parezca a los últimos
  artículos) -- la estructura ya no se elige de una lista, la determina el
  dosier de cada artículo. Se mantienen intactas la regla de títulos
  creativos y la excepción de los 3 títulos fijos (`## Referencias`,
  `## Guía de imágenes`, `## Preguntas / Vacíos del conocimiento`), que las
  secciones 6 y 7 siguen usando tal cual.
- 2026-09-18: la estructura narrativa deja de ser un esqueleto fijo -- la
  sección 4 de `02-instrucciones-notebooklm.md` lista 7 bloques posibles (solo
  Desarrollo técnico y Referencias obligatorios) y NotebookLM manda antes un
  mensaje corto con la estructura elegida y espera el "ok". `03-prompt-notebooklm.txt`
  se reescribe corto (212 palabras), remitiendo al documento en vez de repetir
  sus reglas, y sin voseo.

- 2026-09-18: NotebookLM entrega cada mensaje completo en un único bloque de
  código (si no, la interfaz renderiza el markdown y se pierden `##` y los
  backslash duplicados al copiar); el front matter y las entradas de la Guía de
  imágenes dejan de llevar bloque propio, que quedaba anidado y cerraba el de
  afuera antes de tiempo.

- 2026-09-18: `Gemfile.lock` suma la plataforma `x86_64-linux` -- se generó en
  Windows y solo listaba `x64-mingw-ucrt`, así que el job de build del workflow
  habría fallado en el runner Linux al hacer `bundle install`.
- 2026-09-18: un post con `hidden: true` ahora también sale con
  `<meta name="robots" content="noindex, nofollow">`: estaba fuera de la portada
  y del sitemap, pero su permalink seguía siendo una URL pública indexable.
- 2026-09-18: se agrega `.github/workflows/validar.yml` -- valida el front
  matter, las categorías, las fórmulas, las imágenes y el peso de los assets de
  cada artículo, y corre el build de Jekyll en cada push. Solo lee, no modifica
  nada, y no bloquea el despliegue de GitHub Pages.
- 2026-09-18: la grilla de tarjetas sale a `_includes/lista-posts.html` (la
  repetían `index.html` y `_layouts/category.html` palabra por palabra, incluido
  el filtro de `hidden`) y los `style=""` inline de los títulos de los dos
  layouts pasan a la clase `.page-title` en el CSS.
- 2026-09-18: el artículo del Venturi recupera su jerarquía de encabezados --
  sus 11 títulos de sección eran `<p><strong>`, no `<h2>`/`<h3>`, así que el
  artículo salía sin índice flotante (toc.js busca `h2`) y con el título
  impreso dos veces. Solo cambian esas etiquetas: ni una palabra, cifra,
  fórmula o referencia del texto se tocó.
- 2026-09-18: los tres documentos del flujo quedan consistentes entre sí --
  se sacan las últimas referencias al Conversor (ya no filtra nada: se publica
  lo que Elvis pega, así que ahora está escrito explícitamente qué secciones NO
  se copian), NotebookLM pasa a entregar el bloque de front matter ya armado y
  el cuerpo arranca en el primer `## ` (antes repetía el título y salía dos
  veces), y se saca el voseo de los dos documentos, que lo prohíben y estaban
  escritos en voseo.
- 2026-09-18: optimización de imágenes -- `hero-banner.jpg` 2998 -> 261 KB
  (2400 px de ancho), `og-cover.jpg` deja de ser una copia byte a byte del hero
  y pasa a ser una tarjeta Open Graph real de 1200x630 (111 KB). Total de
  `assets/`: 7.1 MB -> 1.5 MB. `foto-perfil.png` NO se toca: es la foto
  personal de Elvis, se deja bit a bit como está hasta que él pida otra cosa.
- 2026-09-18: `Gemfile` simplificado -- `github-pages` (fijado en ~> 232) ya
  trae Jekyll y los tres plugins, así que se borran las declaraciones sueltas
  de `jekyll-feed`/`jekyll-sitemap`/`jekyll-seo-tag` que podían resolverse a
  una versión distinta de la de producción.
- 2026-09-18: jekyll-seo-tag queda como única fuente de metadatos -- se saca
  la barra "|" de `site.title` (kramdown la leía como tabla y el <title> de la
  portada salía roto), se agregan `tagline`, `author`, `twitter.card` y una
  `og:image` por defecto vía `defaults`, y se borran los `title`/`description`
  escritos a mano en `index.html` y en las 8 `categorias/*.html` (que además
  pierden el `permalink:` redundante: la ruta del archivo ya lo define).
- 2026-09-18: las tablas de artículo pasan a tener estilo propio en
  `styles.css` (colgado de `.post-body table`, no de una clase, así una tabla
  Markdown pelada ya sale bien) y `assets/js/toc.js` se renombra a
  `assets/js/articulo.js`, que además de armar el índice envuelve cada tabla
  en un `.tabla-scroll` accesible -- scroll horizontal en celular sin escribir
  ningún `<div>` a mano en el Markdown.
- 2026-09-18: limpieza de `assets/css/styles.css` -- se borran las reglas sin
  uso: `.fraccion`/`blockquote.formula` (fórmulas Unicode de la era Blogger,
  reemplazadas por LaTeX+MathJax), `.page-header`/`.page-section`/`.profile-photo`
  (about.html está retirada), `.miniatura-video` (galería inexistente) y
  `.site-nav a.pendiente` (el nav no tiene links pendientes).
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
