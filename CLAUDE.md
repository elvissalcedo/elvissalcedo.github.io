# Git_Page

Sitio personal de Elvis Salcedo, ingeniero ambiental — "Elvis Salcedo |
Ingeniería Ambiental" — publicado en GitHub Pages con Jekyll nativo
(`elvissalcedo.github.io`, repo `elvissalcedo/elvissalcedo.github.io`).

Este repo es **el proyecto completo y autosuficiente**: el sitio en sí vive
acá. Publicar un artículo nuevo no requiere terminal ni ningún build local
-- se hace entero desde el editor web de github.com. Para cuando Elvis sí
tiene el repo clonado (VS Code), hay además un script opcional que
automatiza la organización de imágenes (`publicar_articulo.py`, ver la
sección dedicada más abajo).

Las instrucciones de redacción para NotebookLM (`02-instrucciones-notebooklm.md`,
el documento fuente, y `03-prompt-notebooklm.txt`, el prompt corto) **ya no
forman parte de este repo** -- Elvis los sacó de git y GitHub el 2026-09-22
a propósito. Siguen existiendo en el disco de Elvis, en la raíz de esta
misma carpeta, como archivos sueltos sin versionar: `.gitignore` los
excluye explícitamente para que git nunca los vuelva a rastrear ni a
subir. Sirven como referencia personal de Elvis para operar NotebookLM,
pero un clon nuevo de este repo NO los va a traer, y ninguna instrucción
de este archivo debe asumir que existen en el repo -- si hace falta
consultar su contenido, hay que pedírselo a Elvis o leerlos directo del
disco, nunca asumir que un `git show`/`git log` los va a encontrar.

## El flujo de publicación (sin terminal)

- **La skill de NotebookLM** (`02-instrucciones-notebooklm.md`, local, no
  versionado -- ver nota arriba): documento fuente que se sube a
  NotebookLM junto con el PDF del dosier y los artículos del radar. Define
  todo lo que no es contenido técnico: cómo identificar la fuente
  principal (su segunda línea en cursiva "Sub-tema TEMA-XXXX -- tema
  padre: ..."), reglas de citas APA 7 completas, el método Feynman para
  explicar cada término técnico nuevo, la estructura narrativa elegida
  caso por caso entre 7 bloques posibles (solo Desarrollo técnico y
  Referencias son obligatorios, más dos funciones fijas de forma libre:
  un antecedente que va de lo global a lo puntual y la idea central
  explicada primero en simple; NotebookLM propone la estructura en un
  mensaje corto y espera el "ok" de Elvis) con títulos de sección
  creativos, preguntas finales orientadas a analizar/evaluar/crear
  (Bloom, sin nombrarlo) y vacíos planteados como oportunidad solo
  cuando el vacío lo sugiere, el bloque de front matter listo para pegar, el formato de
  salida Markdown exacto (fórmulas en LaTeX real con el backslash
  **duplicado** en los 4 delimitadores -- `\\[...\\]`/`\\(...\\)`, ver la
  nota de kramdown más abajo), la Guía de imágenes y la sección de Vacíos
  del conocimiento.
- **El prompt corto** (`03-prompt-notebooklm.txt`, local, no versionado --
  ver nota arriba): lo que Elvis pega en el chat de NotebookLM cada vez
  que pide un artículo nuevo. Ya no repite las reglas: remite al documento
  fuente y solo marca los pasos de la sesión (identificar el dosier,
  proponer la estructura y esperar el "ok", un bloque de código por
  mensaje, autocrítica final). Deja que NotebookLM decida en cuántos
  mensajes entregar la respuesta según el contenido real, esperando
  "continuar" entre cada uno.
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

## Alternativa con terminal: publicar_articulo.py

- Cuando Elvis trabaja desde VS Code con el repo clonado (no siempre es el
  editor web de github.com), `.github/scripts/publicar_articulo.py`
  reemplaza los pasos manuales de armar a mano la ruta de cada imagen.
  Elvis arma una única carpeta de trabajo con el .md del artículo y todas
  sus imágenes juntas, con nombres simples (`esquema.jpg`, nunca una
  ruta) -- convención sugerida: `_posts/articulos/<slug>/AAAA-MM-DD-slug.md`.
  Los `<img src="archivo.jpg">` del cuerpo (y el `image:` del front
  matter, si también es un nombre simple) se escriben sin pensar en
  `/assets/imagenes/` ni en el slug final.
- Se corre desde la raíz del repo: `python .github/scripts/publicar_articulo.py
  _posts/articulos/<carpeta>`. Copia el .md a `_posts/`, copia las
  imágenes a `assets/imagenes/<carpeta>/`, reescribe cada referencia de
  imagen a su ruta real, le agrega a cada `<img>` lo que el navegador
  necesita para no trabajar de más (`loading="lazy"`, `decoding="async"` y
  las medidas reales leídas de la cabecera del archivo, sin Pillow ni
  ninguna dependencia -- ver la nota sobre `height: auto` en Decisiones de
  diseño), marca como infografía las imágenes cuyo nombre empieza con
  `infografia-`, imprime un resumen de qué copió y qué reescribió,
  sincroniza con origin y recién ahí hace `git add` + un commit local
  (`Publica artículo: <carpeta>`) -- nunca push, eso lo confirma Elvis
  siempre a mano. La sincronización (`git fetch origin` + `git rebase
  origin/main`) **solo rebasea si origin/main trae commits nuevos de
  verdad**: antes corría siempre y eso rompía toda republicación de un
  artículo ya publicado, porque `git rebase` se niega a arrancar con el
  árbol sucio aunque no haya nada que traer -- y el `.md` recién copiado
  siempre lo ensucia. El error culpaba a "cambios ajenos a este artículo".
- Es todo o nada: para antes de copiar o reescribir nada si el nombre del
  .md no empieza con `AAAA-MM-DD-`, si hay cero o más de un .md en la
  carpeta, si la carpeta no tiene ninguna imagen, si un `<img src>` o una
  imagen Markdown ya trae una ruta armada en vez de un nombre simple, o si
  una imagen referenciada no está en la carpeta -- y explica cuál de estos
  problemas encontró, en español simple.
- `_posts/articulos/` está en el `exclude:` de `_config.yml` a propósito:
  Jekyll reconoce como posts los archivos `AAAA-MM-DD-*.md` de cualquier
  subcarpeta de `_posts/`, no solo los de la raíz, así que sin ese exclude
  cualquier borrador que quede ahí adentro se publicaría dos veces -- la
  copia real en `_posts/` y el original roto, con `<img src="archivo.jpg">`
  sin resolver.
- Es un agregado, no un reemplazo: el flujo sin terminal de la sección
  anterior sigue funcionando igual para cuando Elvis publica desde el
  editor web sin tener el repo clonado a mano.
- Para antes de publicar si encuentra la palabra `PENDIENTE` en cualquier
  parte del `.md` (front matter o cuerpo) -- son los campos que deja el
  panel de control de la sección siguiente para completar con lo que
  entregue NotebookLM. El mensaje de error señala las líneas exactas.

## Panel de control local (panel-control-gitpage.bat)

- Vía local para crear, editar, publicar, previsualizar en vivo y eliminar
  artículos, sin editor web ni terminal más allá de un doble clic.
  `panel-control-gitpage.bat` (raíz del repo) arranca
  `.github/scripts/panel_control.py` -- un servidor HTTP en
  `127.0.0.1:8420`, solo con librería estándar de Python (nada que
  instalar) -- y abre el navegador solo en la pantalla principal, con
  tres botones: Crear artículo nuevo, Publicar borrador y Gestionar
  artículos (esta última fusiona lo que antes eran tres pantallas
  separadas -- Editar, Eliminar y la lista de Vista previa en vivo -- ver
  más abajo).
- **Crear artículo nuevo:** formulario con título, categoría (las 8 de
  `_config.yml`) y fecha. Arma el slug del título (minúsculas, sin
  tildes, espacios a guiones), avisa con una pantalla de confirmación
  explícita si ya existe una carpeta o archivo con ese slug (nunca crea
  el duplicado solo; si se confirma igual, lo crea como `<slug>-2`, nunca
  en la misma carpeta), y crea `_posts/articulos/<slug>/<fecha>-<slug>.md`
  -- con el slug recortado a 60 caracteres en un guion (`slug_de_titulo`),
  porque la ruta repite el slug dos veces y Windows sin rutas largas corta
  en 260 (el `title:` conserva el título completo)
  con el front matter listo salvo `excerpt:`/`image:` en `PENDIENTE` --
  para que Elvis pegue ahí el contenido de NotebookLM. Igual que
  `publicar_articulo.py`, esta carpeta de trabajo sigue sin publicarse
  hasta que se corra ese script.
- El `permalink:` del front matter se escribe siempre explícito
  (`/<slug-categoría>/AAAA/MM/DD/slug.html`, con el slug prolijo de
  `_config.yml`) -- nunca la ruta automática de Jekyll. Confirmado con una
  build real en un clon aislado: Jekyll arma esa ruta a partir del
  `category:` del front matter pero solo hace `.downcase`, sin sacar
  tildes ni cambiar espacios por guiones, así que las 4 categorías de
  nombre compuesto (Toxicología y Salud, Sostenibilidad y Energía, Gestión
  y Política, Filosofía y Decisión) salían con una URL rota (espacio y
  tilde literales). Decisión de Elvis del 2026-09-21 frente a la
  alternativa de cambiar `_config.yml` para todo el sitio.
- **Publicar borrador:** reemplaza el paso manual de correr
  `publicar_articulo.py` en la terminal, con vista previa real antes de
  comitear. Lista las carpetas de `_posts/articulos/` (título del front
  matter, fecha de última modificación del `.md`), con un botón "Vista
  previa" junto al de "Revisar y publicar" en cada fila (arranca
  `_iniciar_vivo` directo, sin chequear `PENDIENTE` ni comitear nada -- ver
  el mecanismo compartido en "Vista previa" más abajo); al elegir "Revisar
  y publicar", reusa
  las mismas funciones de `publicar_articulo.py` (todo-o-nada, chequeo de
  `PENDIENTE`) pero se queda ahí -- copia el `.md` a `_posts/` y las
  imágenes a `assets/imagenes/<slug>/` **sin `git add` ni commit**, corre
  `validar_articulos.py` sobre ese artículo puntual (no sobre `assets/`
  entero, para no mezclar avisos preexistentes de otros artículos) y
  `bundle exec jekyll build` real, y embebe el HTML generado en un iframe
  -- se ve exactamente como va a salir publicado, imágenes y fórmulas
  incluidas. El iframe apunta a un segundo servidor HTTP en
  `127.0.0.1:8421` que sirve `_site/` tal cual (necesario para sortear las
  restricciones de `file://` con el `<script type="module">` de Mermaid).
  Debajo, dos botones: **"Confirmar y publicar"** hace `git add` + commit
  (`Publica artículo: <slug>`) + `git fetch origin` + `git rebase
  origin/main` + `git push` en un solo paso (vía `pa.confirmar_commit`) --
  el clic de Elvis en la vista previa real ya es la confirmación explícita,
  no hace falta preguntar de nuevo. **El commit va PRIMERO y la
  sincronización después**, nunca al revés: `git rebase` exige el árbol de
  trabajo limpio, y en una republicación el `.md` ya trackeado está
  modificado justo por la copia que acaba de hacer el panel. Con el commit
  hecho, el árbol queda limpio y el rebase hace lo que tiene que hacer;
  si falla, el commit local ya existe y no se pierde nada (queda sin
  pushear hasta que Elvis resuelva el conflicto a mano). **"Volver a
  editar"** deshace la copia, pero solo de archivos que el panel escribió
  en esa misma sesión (`registrar_copia`): si el `.md` estaba trackeado lo
  restaura con `git checkout`, si es nuevo lo borra, y si encuentra
  cualquier otra cosa con cambios sin comitear la guarda con `git stash`
  en vez de descartarla, avisando en pantalla cómo recuperarla. La carpeta
  de trabajo en `_posts/articulos/` nunca se toca en ninguno de los casos.
- En Windows, `bundle` es un shim `bundle.BAT` de RubyInstaller --
  `subprocess.run(["bundle", ...])` sin más tira `FileNotFoundError`
  aunque `bundle` funcione perfecto a mano en la terminal, porque
  `CreateProcess` no resuelve extensiones de `PATHEXT` sin pasar por una
  shell. `construir_sitio()` resuelve la ruta real con `shutil.which()`
  antes de llamar a `subprocess.run` -- encontrado en una prueba real en
  un clon aislado, no una suposición.
- **Gestionar artículos** (`/gestionar`): pantalla única que fusiona lo que
  hasta el 2026-09-23 eran tres pantallas separadas -- Editar, Eliminar y la
  lista de "Vista previa en vivo" -- porque las tres listaban básicamente lo
  mismo (`listar_articulos()`, los artículos reales de `_posts/`) con un
  solo botón cada una; no escalaba a cientos de artículos. Un buscador
  arriba filtra la tabla en vivo (título, categoría o nombre de archivo) sin
  recargar la página, las 3 columnas (Fecha, Categoría, Título) se ordenan
  con un clic (segundo clic invierte, con una flechita que muestra el
  estado), y solo se renderizan 25 filas a la vez con un botón "Mostrar 25
  más" al pie -- el buscador y el orden actúan sobre la lista completa, no
  solo sobre lo ya mostrado. Todo esto es JS vanilla sin librerías (mismo
  criterio que el resto del proyecto): los datos van embebidos como JSON en
  la página (`json.dumps(...).replace("</", "<\\/")`, para que un título con
  `</script>` adentro no corte el bloque) y el DOM se arma con
  `document.createElement`/`textContent` fila por fila, nunca con
  `innerHTML` de texto libre. Cada fila termina en 3 botones: **Editar**,
  **Vista previa** y **Eliminar** (`boton-peligro`), cada uno un
  mini-`<form>` que apunta a la misma ruta que usaba su pantalla vieja.
  `/editar` y `/eliminar` (GET) ahora redirigen (302) a `/gestionar` --
  nadie que tuviera esas URLs guardadas se queda con un enlace roto.
- **Editar** (botón de una fila): sin cambios de fondo respecto a como
  funcionaba en su pantalla propia. Si ya existe una carpeta de trabajo con
  ese slug en `_posts/articulos/` (por ejemplo, porque Elvis ya la había
  empezado antes), avisa explícitamente -- "Ya tenés una carpeta de trabajo
  para este artículo, con cambios sin publicar" -- y deja elegir entre
  **"Seguir con la carpeta existente"** (la abre tal cual está, no la toca)
  o **"Reiniciar desde lo publicado"** (la borra y la recrea de cero); nunca
  sobreescribe en silencio. Si no existe carpeta, crea
  `_posts/articulos/<slug>/` y copia ahí el `.md` publicado real (con su
  `title`/`date`/`category`/`excerpt`/`image`/`permalink` reales, nada de
  `PENDIENTE`) más las imágenes de `assets/imagenes/<slug>/` que existan.
  `_convertir_a_rutas_simples()` deshace, con un reemplazo de texto literal
  (no regex), lo que `pa.procesar_referencias` hizo al publicar: el `.md`
  real tiene las rutas completas (`/assets/imagenes/<slug>/archivo.ext`, en
  `<img>`, en imagen Markdown y en el `image:` del front matter) y la
  carpeta de trabajo espera nombres simples, para que "Publicar
  borrador"/"Vista previa" puedan reescribirlas de nuevo al republicar. El
  artículo publicado nunca se toca hasta que Elvis confirme la
  republicación desde "Publicar borrador". Probado de punta a punta en un
  clon aislado con un artículo real (3 imágenes): carpeta de trabajo creada
  con el contenido real y las 3 imágenes; una oración y una imagen nuevas
  agregadas a mano; "Vista previa" mostrando el contenido viejo y el nuevo a
  la vez; "Publicar borrador" → "Confirmar y publicar" modificando el mismo
  archivo en `_posts/` (no uno nuevo) con `validar_articulos.py` en 0
  errores; y, eligiendo el mismo artículo de nuevo con la carpeta de
  trabajo ya existiendo, el aviso de conflicto apareció, "Seguir" dejó el
  archivo con el mismo MD5 antes y después, y "Reiniciar" reconstruyó
  limpio desde lo publicado.
- **Vista previa** (botón de una fila, para un artículo YA publicado):
  arranca la vista previa en vivo directamente para ese artículo, sin pasar
  por la pantalla intermedia "carpeta lista" de Editar. Internamente arma
  (o reusa) la misma carpeta de trabajo que usaría Editar -- mismo chequeo
  de conflicto, mismo aviso "Ya tenés una carpeta de trabajo..." si
  corresponde -- pero en vez de terminar en `pagina_editar_listo`, termina
  arrancando la vista previa: `pagina_editar_conflicto()` ahora recibe un
  parámetro `destino` ("editar" o "vivo") que viaja como campo oculto por
  `/editar/seguir` y `/editar/reiniciar`, y esas dos rutas miran ese campo
  para decidir si muestran la carpeta o arrancan la vista previa
  directamente. El mecanismo real de arranque (`_iniciar_vivo`, antes el
  cuerpo entero de `manejar_vivo_iniciar`) es una sola función compartida
  por 3 caminos: este botón de Gestionar articulos, el botón "Vista previa"
  que "Publicar borrador" agrega junto a cada borrador (para un artículo
  que **todavía no se publicó ni una vez** -- ver nota más abajo), y la
  ruta `/vivo/iniciar` en sí. Copia el `.md` y las imágenes a
  `_posts/`/`assets/imagenes/<slug>/` (`pa.copiar_articulo`, sin el chequeo
  de `PENDIENTE` que sí exige "Publicar borrador"), arranca -- o reusa, si
  ya está corriendo -- `bundle exec jekyll serve --livereload` en segundo
  plano en `127.0.0.1:4000`, y abre la URL directa del artículo (calculada
  con `ruta_generada_en_site`, nunca la portada) en un iframe. Un hilo en
  segundo plano vigila la carpeta de trabajo cada 1.5 segundos (mtime de
  cada archivo) y, ante cualquier cambio, vuelve a copiar -- eso dispara la
  reconstrucción automática de `jekyll serve --livereload`, que ya
  refresca el navegador solo. El campo `image: PENDIENTE.jpg` que deja el
  scaffold de "Crear artículo nuevo" se neutraliza SOLO en la copia en
  memoria usada para renderizar (nunca en el `.md` real de la carpeta de
  trabajo). Tampoco bloquea que la carpeta de trabajo todavía no tenga
  ninguna imagen, ni que el `.md` tenga marcadores `[IMAGEN N -- título]`
  sin reemplazar: el propósito de este flujo es ir viendo el progreso
  mientras se escribe, no exigir que el artículo esté terminado.
  `_encontrar_imagenes_vivo()` (tolerante) y
  `_reemplazar_imagenes_faltantes()` sustituyen, también SOLO en la copia
  en memoria, cada marcador sin resolver por un recuadro "Imagen
  pendiente" -- en vez de que `pa.procesar_referencias` corte la vista
  previa entera con un error. Ese chequeo estricto sigue intacto para
  "Publicar borrador". **"Detener vista previa"** corta la vigilancia y
  descarta la copia -- pero deja corriendo `jekyll serve` para reusarlo en
  la próxima. Solo una vista previa activa a la vez: arrancar una segunda
  detiene y descarta la anterior sola. GET `/vivo` sin ninguna vista previa
  corriendo ya no lista carpetas (duplicaba "Publicar borrador"): muestra
  un aviso simple con enlaces a "Gestionar artículos" y "Publicar
  borrador". Probado de punta a punta en un clon aislado, incluida una
  corrida real de `bundle exec jekyll serve` (no simulada) disparada desde
  el botón de una fila de Gestionar artículos: URL directa confirmada (no
  portada), HTML servido con el contenido real del artículo, y "Detener
  vista previa" con `git status` limpio.
- Un artículo creado con "Crear artículo nuevo" que **todavía no se publicó
  ni una vez** no aparece en Gestionar artículos (no existe en `_posts/`,
  de ahí sale esa lista) -- para esos, el botón "Vista previa" quedó en
  "Publicar borrador", que ya lista esas carpetas de trabajo y no cambió su
  chequeo de `PENDIENTE` ni de `validar_articulos.py` para el botón
  "Revisar y publicar" que sigue ahí al lado.
- **Eliminar** (botón de una fila): sin cambios de fondo. Pide escribir
  `ELIMINAR` en un campo de texto para confirmar -- cualquier otro texto no
  borra nada. Al confirmar: `git rm` del `.md` y de la carpeta
  `assets/imagenes/<slug>/` si existe, commit LOCAL únicamente (`Elimina
  artículo: <título>`) -- nunca push. **La carpeta de imágenes NO se borra
  si algún otro post de `_posts/` todavía referencia algo de ahí adentro**
  (`posts_que_usan_carpeta_imagenes`): dos artículos con distinta fecha
  pero el mismo slug comparten esa carpeta, y borrarla con uno se lleva
  puestas las imágenes del otro. Pasó de verdad el 2026-09-22 y costó tres
  imágenes del artículo de fitorremediación. En ese caso el `.md` se borra
  igual y la pantalla dice con qué artículos estaba compartida. **Si
  `git commit` falla** (un hook, la identidad de git sin configurar), se
  deshace el `git rm` (`git reset` + `git checkout` de lo borrado) y la
  pantalla lo explica -- antes quedaba borrado en el índice sin commit, sin
  forma clara de saber qué había pasado.

## El sitio (Jekyll)

- `_config.yml` — config de Jekyll: `kramdown.math_engine: null` (clave:
  en YAML es `null`, no `nil` -- `nil` es un string literal y rompe el
  build), lista de plugins (`jekyll-feed`, `jekyll-sitemap`,
  `jekyll-seo-tag`) y la lista única `categorias` (nombre + slug) que
  alimenta el menú y las páginas de categoría -- se edita en un solo
  lugar, nunca a mano en cada archivo.
- **Analítica: GoatCounter** (`elvissalcedo.goatcounter.com`), sin cookies ni
  datos personales. Un solo `<script async>` al final del `<body>` de
  `_layouts/default.html`, así que cuenta todas las páginas y nunca frena el
  dibujo ni las fuentes. Por su cuenta no cuenta nada en `localhost`/`127.x`
  ni dentro de un iframe: la vista previa del panel no ensucia los datos. Por
  ahora solo acumula visitas; nada del sitio las lee todavía (un futuro "Lo
  más leído" las usaría).
- `_layouts/default.html` — `<head>` (incluye `{% seo %}`, las fuentes de
  Google y MathJax/Mermaid), header/footer (`_includes/`), `{{ content }}`.
  Las fuentes se piden acá con `preconnect` + `<link>`, NO con un `@import`
  dentro de `styles.css`: con el `@import` el navegador tenía que bajar
  primero la hoja de estilos para recién entonces descubrir que faltaban las
  fuentes, una detrás de la otra. MathJax y Mermaid se cargan solo si la
  página los necesita de verdad -- el layout mira el HTML ya generado
  (`content contains '\('`, `'\['`, `'formula-latex'`, `'language-mermaid'`)
  y se los saltea en la portada y en las páginas de categoría, que no tienen
  ni una fórmula ni un diagrama.
- `_layouts/post.html` — plantilla de artículo: "← Volver al inicio", migas
  de pan (Inicio › Categoría › Título, con el slug de la categoría sacado de
  `site.categorias`, más su JSON-LD `BreadcrumbList`), título, fecha
  (formateada en español vía `_includes/fecha-es.html`, GitHub Pages no
  permite plugins de localización), categoría, `.article-layout` (post-body +
  TOC flotante armado por `assets/js/articulo.js`) y al final **Sugeridos**:
  de 0 a 5 tarjetas compactas, SOLO de artículos relacionados de verdad --
  primero la misma categoría y después los que compartan al menos un tema
  en `tags:` (comparados en minúsculas). Nunca se rellena con artículos sin
  relación: si no hay ninguno, la sección no aparece (hoy, con una sola
  entrada por categoría y sin `tags:`, no aparece en ninguno). Para unir dos
  artículos de categorías distintas sobre el mismo tema basta con darles un
  `tags:` en común. Sin analítica: el sitio no la tiene.
- `_layouts/category.html` — loop de `site.posts` filtrado por
  `page.category`, con aviso "próximamente" si la categoría está vacía.
- `_includes/header.html` + `_includes/nav-enlaces.html` — el menú se
  escribe una sola vez (`nav-enlaces.html`) y se muestra de dos formas:
  completo en escritorio y, en pantallas <= 768px, dentro del panel
  "Secciones" (un `<details>`: funciona sin JavaScript). La fila de
  "Secciones" comparte lugar con el buscador.
- **Buscador:** `search.json` (Liquid, `sitemap: false`: título, URL, fecha,
  categoría y extracto de cada post visible) + `assets/js/buscador.js`, que
  dibuja el campo, carga Fuse.js 7.5.0 desde jsdelivr con `import()` (desde
  la 7.x solo se publica como módulo ES) y filtra mientras se escribe. Ni
  Fuse ni el índice se bajan hasta que alguien toca el campo. Iguala tildes
  por su cuenta ("maiz" encuentra "maíz"): Fuse no lo hace. Sin JavaScript
  el buscador no se dibuja.
- Ancho: los artículos siguen en `.page-body` (860px, columna de lectura de
  580px con el índice). La portada y las categorías piden por front matter
  `clase_main: page-body-listado` (`--ancho-listado`, 1480px; tarjetas de
  300px mínimo: 3 columnas a 1280px, 4 desde ~1600px) y el encabezado se
  alinea con esa grilla en esas páginas (`body.con-page-body-listado`).
- Portada: el artículo más reciente (visible) va arriba en una tarjeta
  destacada (`lista-posts.html` con `destacar=true`, solo en `index.html`;
  las categorías no destacan ninguno): extracto completo, imagen a la
  izquierda desde 1100px y apilada debajo de eso, sin `loading="lazy"`
  porque es lo primero que se ve. Debajo, separada por una línea fina
  (`.portada-cuerpo`), la grilla con el resto y al costado el lateral
  (`_includes/portada-lateral.html`): las 8 categorías con su conteo (las
  vacías atenuadas, no ocultas) y los 5 artículos más recientes: miniatura
  de 76x57 a la izquierda (la misma `image:` de su tarjeta; un hueco pintado
  si el artículo no tiene) y título y fecha a la derecha. La miniatura no
  suma alto: un título de 3 renglones más la fecha (~86px) siempre es más
  alto que ella (57px). Se llama "recientes" a propósito: el sitio no mide visitas, así
  que no hay "lo más leído". Desde 1100px va al costado (300px); debajo, a
  lo ancho después de la grilla (sus dos bloques lado a lado en tablet). Es
  sticky solo en pantallas de 1040px de alto o más: el peor caso del lateral
  mide 985px (títulos topeados en 3 renglones, medido con 100 artículos de
  prueba), y en una pantalla más baja el sticky tapaba los últimos
  recientes. Una segunda línea separa el contenido del pie de página, solo
  en la portada (`body.es-portada`).
- `_posts/` — un artículo por archivo, `AAAA-MM-DD-slug.md`. El primer
  artículo real (`lavador-venturi.html` original) vive acá como
  `2026-09-17-lavador-venturi.md`, con `permalink: /lavador-venturi.html`
  para no romper la URL ya publicada.
- `categorias/*.html` — 8 archivos, solo front matter (`layout: category`
  + `category: <Nombre>`), uno por categoría del menú.
- `index.html` — portada; `layout: default` + loop de Liquid sobre
  `site.posts`, ya no se edita a mano.
- `assets/css/styles.css`, `assets/js/articulo.js`, `assets/imagenes/<slug>/` —
  estilos, scripts e imágenes por artículo. `articulo.js` hace seis cosas,
  todas sin librerías: el botón "Volver arriba" (en todas las páginas; al
  usarlo, el foco del teclado va al nombre del sitio, `.site-header h1`,
  visible en cualquier ancho -- antes iba al primer enlace del menú, que en
  celular ahora queda oculto), el cierre del panel "Secciones" con Escape o
  tocando afuera, el
  índice flotante de escritorio, el índice plegable de celular, el
  envoltorio deslizable de las tablas anchas y el de las infografías
  densas, y el marcado accesible de las fórmulas que no entran a lo ancho. `assets/hero-banner.jpg`
  (2400x745, fondo del header), `og-cover.jpg` (1200x630, la tarjeta de Open
  Graph que sale al compartir) y `foto-perfil.png` son assets de marca, van
  sueltos en `assets/` (no por artículo). Antes de subir una imagen conviene
  dejarla en el ancho que de verdad se usa: una foto de cámara o de banco sin
  tocar pesa 3 MB y el sitio no necesita ni el 10 % de eso.
- `02-instrucciones-notebooklm.md`, `03-prompt-notebooklm.txt` — desde el
  2026-09-22 ya NO viven en este repo (ver nota al principio del archivo):
  son archivos locales sueltos en el disco de Elvis, ignorados por git vía
  `.gitignore`. **`_config.yml` los sigue listando en `exclude:` y esa
  entrada NO se puede sacar**, al revés de lo que decía antes esta misma
  línea: los dos archivos siguen existiendo en el disco de Elvis y Jekyll
  construye desde la carpeta de trabajo, no desde git, así que sin el
  exclude un build local (la vista previa del panel) se llevaría puesto el
  documento interno de 54 KB adentro de `_site/`. Comprobado el 2026-09-23
  con un build real: con el exclude, `_site/` no los contiene.
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

- **El cuerpo del artículo NO se justifica en celular, ni siquiera con
  guiones automáticos.** Medido el 2026-09-23 en Edge real a 390px, sobre
  los 5 artículos (2.526 renglones), con el diccionario de guionado español
  cargado de verdad: justificado solo deja el 77 % de los renglones con
  espacios de 1,5x o más; justificado + `hyphens: auto` baja a 55 % (26 %
  con espacios del doble o más) y además parte una palabra en 4 de cada 10
  renglones -- justo los términos técnicos ("fitorreme-diación",
  "biodisponibi-lidad") y hasta los títulos h2. Alineado a la izquierda: 0 %.
  En escritorio (columna de 580px) sigue justificado.
- **Una miniatura de tarjeta necesita `overflow: hidden` para respetar el
  16:9.** Con `overflow` visible, `aspect-ratio` deja que la altura natural
  de la imagen le gane a la proporción: una infografía vertical (la del
  maíz) estiraba su tarjeta y la fila entera de la grilla.
- **La foto de la tarjeta destacada NO usa `aspect-ratio` en la vista de
  dos columnas.** En un ítem de grilla, `aspect-ratio` + un alto hace que el
  navegador calcule el ANCHO a partir del alto: con un extracto largo al
  lado, la foto se salía de su columna y tapaba el texto (medido a 1000px).
  Llena su celda con `min-height` y `object-fit: cover`.

- **Una infografía densa se marca a mano: no hay forma de detectarla
  sola.** Una imagen con mucho texto adentro (un esquema con etiquetas, un
  diagrama con leyendas) se vuelve ilegible si se la achica a los ~343px de
  ancho que tiene la columna en un celular. Esas imágenes no se achican: se
  muestran hasta 720px de ancho, se recorren de costado dentro de su caja
  (mismo patrón que las tablas anchas y las fórmulas largas) y tocándolas se
  abre el archivo original, donde el pellizco del teléfono hace zoom sin
  nada de por medio. En escritorio no cambia nada. Se marcan de dos
  maneras: **nombrando el archivo `infografia-loquesea.jpg`** (la vía
  recomendada -- `publicar_articulo.py` le pone la clase solo, sin tocar el
  `.md`) o escribiendo `class="infografia"` en el `<img>`. **Detectarlas
  automáticamente no es posible** y se midió antes de descartarlo: sobre las
  13 imágenes del sitio, la infografía densa del artículo de
  fitorremediación da 0,227 bytes/píxel y un diagrama simple
  (`rutas-intercambio-ionico`) da 0,245 -- más alto; las dos imágenes de
  2100px son las más livianas por píxel. Ninguna medida disponible (peso,
  dimensiones, proporción) separa una cosa de la otra sin leer el texto de
  adentro.
- **`width`/`height` en cada `<img>` van SIEMPRE junto a `height: auto` en
  el CSS.** `publicar_articulo.py` escribe las medidas reales de cada imagen
  en la etiqueta para que el navegador le reserve el lugar antes de que
  cargue (y el texto no pegue saltos). Pero esas medidas son también un
  tamaño *especificado*: sin `height: auto` en `.post-body img`, el
  navegador achica el ancho a la columna y deja el alto del atributo, y la
  imagen sale aplastada. Los dos cambios son uno solo, nunca se toca uno sin
  el otro.
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
  MathJax los renderiza sin tocar nada más del diseño. El post oculto que
  servía de banco de pruebas real de este comportamiento
  (`_posts/2026-09-17-articulo-ejemplo.md`, `hidden: true` + `sitemap: false`)
  fue borrado por Elvis el 2026-09-22 -- si alguna vez se toca
  `_config.yml` o se actualiza kramdown y hace falta revalidar este
  comportamiento, ya no hay un artículo de prueba dedicado; conviene armar
  uno nuevo con el mismo criterio (oculto del índice y del sitemap) antes
  de tocar nada.
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

- 2026-09-24: miniaturas en "Artículos recientes" del lateral de la portada
  (76x57, `loading="lazy"`, hueco pintado si falta `image:`). Peor caso
  vuelto a medir con 103 artículos de prueba y los 5 recientes con títulos
  topeados en 3 renglones: sigue en 985px, así que el umbral del sticky
  (1040px de alto) no cambia. Categorías, líneas y sticky sin cambios.

- 2026-09-24: instala GoatCounter (script `async` al final del `<body>` del
  layout base, en las 13 páginas HTML). Verificado en Edge real: en local y
  dentro de un iframe no cuenta; con el dominio real simulado manda una
  visita por página con la ruta correcta (envío interceptado en el
  navegador, nunca llegó a GoatCounter). Sin cambios en nada más.

- 2026-09-24: portada en secciones -- líneas finas entre la destacada y la
  grilla y entre el contenido y el pie, y un lateral nuevo con categorías y
  conteo + los 5 artículos más recientes (título y fecha). Al costado desde
  1100px, debajo de la grilla en tablet y celular. La destacada y las
  tarjetas no cambian. Probado en Edge real vía CDP de 390 a 1920px sobre el
  sitio real (4 artículos) y sobre una copia aislada con 100 artículos de
  prueba (conteos, ocultos, títulos largos, sticky).

- 2026-09-24: portada y categorías a 1480px (antes 1120; 4 columnas desde
  ~1600px, encabezado alineado), artículo más reciente destacado arriba de
  la portada (extracto completo), tarjetas con borde y sombra en todos los
  anchos, y Sugeridos solo con artículos relacionados de verdad (misma
  categoría o `tags:` en común, hasta 5, cero si no hay ninguno -- ya no
  rellena con los más recientes). Primer uso real de `tags:`: los dos
  artículos de fitorremediación (Agua y Suelo) llevan
  `tags: [Fitorremediación]` y se sugieren entre sí. Probado en Edge real vía CDP de 390 a
  2560px (217 pruebas), con Sugeridos verificado sobre una copia aislada con
  artículos de prueba (7 del mismo tema, ocultos, `tags:` entre categorías).

- 2026-09-23: navegación y portada -- en celular (<= 768px) el menú de 9
  entradas sobre la foto pasa a un panel "Secciones" (`<details>`, sin JS)
  junto a un buscador predictivo nuevo (`search.json` + `buscador.js`,
  Fuse.js 7.5.0 cargado solo al usarlo); migas de pan con JSON-LD y
  "Sugeridos" (misma categoría, respaldo por fecha) en cada artículo; portada
  y categorías a 1120px (3 columnas) sin tocar el ancho de lectura, con el
  encabezado alineado a la grilla en esas páginas (`body.con-page-body-listado`,
  la regla base de `.inner` no cambia); tarjetas
  con borde y sombra más marcada en celular; miniaturas que respetan el 16:9
  (`overflow: hidden`); foco de "Volver arriba" al nombre del sitio;
  `panel-control-gitpage.bat` al `exclude:` (se publicaba). Justificado en
  celular probado con guiones y descartado con números (ver Decisiones de
  diseño). 130 pruebas en Edge real vía CDP a 390/768/769/1280px, incluido
  sin JavaScript y con "oscurecer páginas".

- 2026-09-23: el panel alinea solo el `permalink:` con el `category:` del
  front matter (`alinear_permalink`, solo el primer segmento; fecha, slug,
  carpeta y nombre del `.md` no se tocan) al guardar en la vista previa en
  vivo y en "Revisar y publicar", y lo reescribe también en el `.md` de la
  carpeta de trabajo (preserva CRLF). Un permalink de otra forma (ej.
  `/lavador-venturi.html`) o una categoría inválida no se tocan. El iframe
  de la vista previa en vivo sigue la ruta nueva vía `/vivo/estado` (antes
  quedaba en la vieja: "Not Found").
- 2026-09-23: el panel fusiona "Editar artículo publicado", "Eliminar
  artículo publicado" y la lista de "Vista previa en vivo" en una sola
  pantalla, "Gestionar artículos" (`/gestionar`) -- las tres listaban lo
  mismo con un solo botón cada una, y no escalaba a cientos de artículos.
  Buscador en vivo (título/categoría/archivo, sin recargar), columnas
  Fecha/Categoría/Título ordenables con un clic, "Mostrar 25 más" en vez de
  renderizar todo de una, y 3 botones por fila (Editar, Vista previa,
  Eliminar) -- todo con JS vanilla sin librerías, datos embebidos como
  JSON. El botón "Vista previa" de una fila arranca la vista previa en
  vivo directo para ese artículo publicado (mismo chequeo de conflicto que
  Editar, vía el nuevo parámetro `destino` de `pagina_editar_conflicto`);
  "Publicar borrador" suma su propio botón "Vista previa" por fila, para
  un artículo que todavía no se publicó nunca. `/editar` y `/eliminar`
  redirigen (302) a `/gestionar`. 94 pruebas sobre un clon aislado
  (incluidas 2 corridas de Node.js ejecutando el JS real que sirve el
  panel, no una reimplementación, y una corrida real de
  `bundle exec jekyll serve` disparada desde el botón de una fila).
- 2026-09-23: el panel deja de fallar en silencio. "Crear" daba
  `FileNotFoundError` con un título largo (ruta de 286 caracteres, límite
  260, `LongPathsEnabled` en 0) y el navegador quedaba en
  `ERR_EMPTY_RESPONSE`: slug recortado a 60, control de largo y error en
  pantalla. Revisados los otros 4 flujos: copia parcial deshecha si falla a
  mitad (`pa.copiar_articulo` avisa archivo por archivo), el hilo de "Vista
  previa en vivo" sobrevive a cualquier excepción, slug duplicado ->
  `<slug>-2`, "Editar" con control de largo en 259 (el del mercado de
  carbono mide 252) y "Reiniciar" que renombra antes de borrar, copia
  descartada ante fallos posteriores (build, jekyll serve), páginas GET
  que no se caen por un `.md` fuera de UTF-8, y "Eliminar" que deshace el
  `git rm` si el commit falla. 61 pruebas sobre un clon aislado, incluido
  un build real de Jekyll.
- 2026-09-23: tres arreglos de seguridad del panel y siete cambios de
  diseño del sitio, todos verificados con evidencia real (24 pruebas de
  Python sobre clones de git aislados y mediciones en un Edge de verdad --
  el headless no ejecuta scroll, `requestAnimationFrame` ni
  `IntersectionObserver`, así que no sirve para validar interfaz de
  scroll). **Panel:** (1) la republicación de un artículo ya publicado
  estaba rota desde `afb8ecd` -- el rebase corría siempre y `git rebase`
  se niega a arrancar con el árbol sucio; ahora solo rebasea si origin
  trae algo y `confirmar_commit` comitea antes de sincronizar; (2)
  `_revertir_o_borrar` ya no hace `git checkout` a ciegas: solo descarta
  archivos que el panel escribió en esa sesión y guarda cualquier otro
  cambio sin comitear en un `git stash`; (3) `eliminar_articulo` no borra
  una carpeta de imágenes que otro post siga usando. **Sitio:** fórmulas
  largas y infografías densas deslizables en celular en vez de ilegibles
  o desbordadas; `overflow-wrap` en el cuerpo (un DOI de la bibliografía
  arrastraba la página 80px de costado -- ese era el desborde real, no
  MathJax); `loading="lazy"` + medidas reales en las 13 imágenes de los 4
  artículos, con `height: auto` como complemento obligatorio; MathJax y
  Mermaid solo en las páginas que los usan (la portada ya no los baja);
  texto justificado solo en escritorio; encabezado compacto en celular
  (292px contra ~360); fuentes desde el `<head>` en vez de `@import`;
  índice plegable "En este artículo" en celular (el flotante quedaba al
  final de 20.000px de scroll) y botón "Volver arriba" en todo el sitio.
  Además: `__pycache__/` al `.gitignore` y fuera el `grep` del workflow
  que vigilaba el post de pruebas borrado el 2026-09-22.
- 2026-09-22: agrega `sincronizar_con_remoto()` a `publicar_articulo.py`
  (usada por `confirmar_commit`, y por lo tanto también por "Confirmar y
  publicar" del panel de control) -- hace `git fetch origin` + `git rebase
  origin/main` automáticamente antes de cada commit de publicación, para
  evitar el rechazo real "rejected... fetch first" que sufrió Elvis cuando
  origin/main avanzó por edición web de GitHub mientras él tenía commits
  locales sin pushear. Nunca fuerza nada: si el rebase no puede aplicarse
  solo, aborta y devuelve el error sin comitear. Distingue dos casos reales
  probados en este mismo incidente -- cambios sin comitear que chocan con
  el intento de traer origin (mensaje claro, distinto de un conflicto) vs.
  un conflicto de contenido real entre commits.
- 2026-09-22: Elvis borra el post oculto de pruebas
  `_posts/2026-09-17-articulo-ejemplo.md` (banco de pruebas real del
  comportamiento de kramdown con los delimitadores `\\(...\\)`/`\\[...\\]`
  -- ver la nota de diseño correspondiente más abajo, que se actualiza
  para reflejar que ya no existe).
- 2026-09-22: Elvis retira `02-instrucciones-notebooklm.md` y
  `03-prompt-notebooklm.txt` del repo (borrados en GitHub vía editor web,
  decisión intencional -- no un accidente). Siguen existiendo en su disco
  como archivos sueltos sin versionar; se agregan a `.gitignore` para que
  git nunca vuelva a rastrearlos ni preguntar por ellos, y este archivo se
  actualiza en la introducción y en la sección "El sitio (Jekyll)" para
  dejar constancia de que ya no forman parte del proyecto versionado --
  un clon nuevo de este repo no los va a traer.
- 2026-09-21: agrega el quinto flujo del panel de control, "Editar
  artículo publicado" (sección dedicada más arriba) -- no había forma de
  reabrir un artículo ya publicado para seguirle agregando contenido.
  Copia el `.md` real (sin `PENDIENTE`) y sus imágenes a una carpeta de
  trabajo nueva, convirtiendo las rutas completas de imagen de vuelta a
  nombres simples (`_convertir_a_rutas_simples()`, inversa de lo que hace
  `pa.procesar_referencias` al publicar). Si la carpeta de trabajo ya
  existe (cambios sin publicar), avisa y deja elegir entre "Seguir con la
  carpeta existente" o "Reiniciar desde lo publicado" -- nunca sobreescribe
  en silencio. Como el nombre del archivo coincide con el original, una
  republicación posterior desde "Publicar borrador" lo reemplaza en vez de
  duplicarlo. Probado de punta a punta en un clon aislado con un artículo
  real de 3 imágenes: carpeta creada con contenido real, edición con
  "Vista previa en vivo" mostrando lo viejo y lo nuevo a la vez,
  republicación que modificó el mismo archivo en `_posts/` (no uno nuevo)
  con el validador en 0 errores, y el aviso de conflicto al re-elegir el
  mismo artículo con cambios sin publicar simulados -- "Seguir" con MD5
  idéntico antes/después, "Reiniciar" descartando el cambio simulado y
  reconstruyendo limpio desde lo publicado.
- 2026-09-21: "Vista previa en vivo" deja de bloquear por falta de
  imágenes -- antes fallaba duro si la carpeta de trabajo no tenía
  ninguna imagen (`pa.encontrar_imagenes` original), lo cual contradecía
  el propósito del flujo (mirar el progreso mientras se escribe, no exigir
  que esté terminado). Suma `_encontrar_imagenes_vivo()` (lista vacía en
  vez de fallar) y `_reemplazar_imagenes_faltantes()`, que sustituye, SOLO
  en la copia en memoria usada para renderizar, cada marcador
  `[IMAGEN N -- título]` sin reemplazar y cada `<img>`/imagen Markdown que
  apunte a un archivo que todavía no está en la carpeta, por un recuadro
  "Imagen pendiente". "Publicar borrador" no se tocó -- sigue usando
  `pa.encontrar_imagenes` y `pa.procesar_referencias` sin cambios, con el
  mismo rigor de siempre. Probado en un clon aislado con un borrador sin
  ninguna imagen y dos marcadores `[IMAGEN N]` sin resolver: la vista
  previa cargó igual (antes fallaba), el HTML servido no tiene ningún
  marcador literal (los dos se reemplazaron por el recuadro), todo el
  texto y la estructura del artículo se ven completos, la carpeta
  `assets/imagenes/<slug>/` vacía se crea y se borra sola al detener (sin
  quedar huérfana), y "Publicar borrador" sobre el mismo borrador siguió
  bloqueando con el mensaje de siempre.
- 2026-09-21: agrega el cuarto flujo del panel de control, "Vista previa
  en vivo" (sección dedicada más arriba) -- reemplaza a Ctrl+Shift+V de VS
  Code, sin chequear `PENDIENTE` ni correr el validador ni comitear nada.
  Reusa `pa.copiar_articulo` y `descartar_vista_previa` (mismas funciones
  de "Publicar borrador"), arranca o reusa `bundle exec jekyll serve
  --livereload` en segundo plano y abre la URL directa del artículo; un
  hilo vigila la carpeta de trabajo cada 1.5 segundos (mtime) y vuelve a
  copiar ante cualquier cambio, dejando que `--livereload` refresque el
  navegador solo. Probado de punta a punta en un clon aislado: URL directa
  (no portada), edición reflejada en segundos, imagen nueva servida sola,
  descarte limpio (`git status` sin nada pendiente, carpeta de trabajo
  intacta) y funcionamiento con `PENDIENTE` sin completar. Encontrados y
  corregidos dos bugs reales en esa prueba: una imagen agregada a mitad de
  sesión quedaba huérfana al detener (el hilo no acumulaba la lista de
  copiadas -- corregido a unión, no reemplazo) y `image: PENDIENTE.jpg`
  rompía la copia entera porque `pa.procesar_referencias` exige que ese
  nombre de archivo exista de verdad (corregido neutralizando ese campo
  SOLO en la copia en memoria usada para renderizar, nunca en el `.md`
  real de la carpeta de trabajo).
- 2026-09-21: agrega el tercer flujo del panel de control, "Publicar
  borrador" (sección dedicada más arriba) -- reemplaza el paso manual de
  correr `publicar_articulo.py` en la terminal, con vista previa real
  (`bundle exec jekyll build` + iframe contra un segundo servidor HTTP en
  `127.0.0.1:8421` sirviendo `_site/`, más los errores/avisos de
  `validar_articulos.py` visibles junto a la vista previa) antes de
  comitear. "Confirmar y publicar" hace commit + push en un solo paso;
  "Volver a editar" deshace la copia -- restaura con `git checkout` si el
  archivo ya estaba trackeado (republicación de un artículo existente,
  nunca lo borra), o lo borra si es nuevo. Encontrado durante la prueba en
  un clon aislado (con un remoto local de mentira para probar el push
  real sin tocar GitHub ni este repo): en Windows, `subprocess.run(["bundle",
  ...])` tira `FileNotFoundError` porque `bundle` es un shim `.BAT` de
  RubyInstaller y `CreateProcess` no resuelve `PATHEXT` sin pasar por una
  shell -- se resuelve con `shutil.which("bundle")` antes de llamar al
  subprocess. Probado de punta a punta: bloqueo por `PENDIENTE` antes de
  copiar nada, vista previa real con imagen y fórmula LaTeX renderizadas
  (confirmado bajando el HTML servido en el puerto 8421, no solo mirando
  el `.md`), descarte limpio verificado con `git status` y con un test
  unitario aparte del caso "archivo ya trackeado" (restaura, no borra) vs.
  "archivo nuevo" (borra), y confirmación real con commit + push al
  remoto de prueba.
- 2026-09-21: agrega el panel de control local (`panel-control-gitpage.bat`
  + `.github/scripts/panel_control.py`) -- tercera vía para crear y eliminar
  artículos con formulario web, sin editor de github.com ni terminal más
  allá de un doble clic (sección dedicada más arriba). `publicar_articulo.py`
  suma `verificar_sin_pendientes()`: para antes de copiar nada si encuentra
  `PENDIENTE` en el `.md` (los campos que deja el panel para completar con
  NotebookLM), señalando las líneas exactas. Encontrado durante la prueba en
  un clon aislado (no una suposición): la URL automática de Jekyll para las
  4 categorías de nombre compuesto sale rota (`.downcase` sin sacar tildes
  ni cambiar espacios por guiones); Elvis eligió que el panel escriba
  siempre un `permalink:` explícito con el slug prolijo de `_config.yml` en
  vez de tocar la config del sitio entero. Probado de punta a punta en el
  clon: creación con `permalink` correcto, detección de duplicados sin
  crear doble, publicación bloqueada por `PENDIENTE` sin completar,
  publicación real con `bundle exec jekyll build` generando la URL
  calculada exacta y `validar_articulos.py` en 0 errores, y eliminación con
  confirmación de texto exacta (`ELIMINAR`) que borra `.md` + carpeta de
  imágenes en un commit local sin push. De paso se corrigió un bug real del
  propio servidor: `http.server.HTTPServer` (no threaded) con HTTP/1.1 se
  colgaba si una conexión anterior quedaba a medio cerrar, bloqueando todas
  las peticiones siguientes -- se pasó a `ThreadingHTTPServer` + HTTP/1.0.
- 2026-09-21: el workflow `validar.yml` venía en rojo desde el commit
  748e8c0 (cuando `publicar_articulo.py` reemplazó el artículo del Venturi
  entero con el contenido nuevo de NotebookLM) sin que nadie lo hubiera
  revisado -- rastreado recién ahora con `git log -p` contra la corrida más
  reciente en GitHub Actions (API pública, sin `gh` instalado). Tres
  correcciones: (1) saca el título duplicado del cuerpo del Venturi (mismo
  problema que ya se había corregido una vez en a84f90c, volvió al
  reemplazar el artículo completo -- el cuerpo vuelve a arrancar en el
  primer `## `); (2) `validar_articulos.py`, la regla de fecha del front
  matter vs. fecha del nombre de archivo pasa de error a aviso -- un
  desfase puede ser backdating intencional (como este mismo artículo,
  `date: 2025-01-12` con permalink fijo para preservar la fecha de
  publicación original) o un error real, y el validador no puede
  distinguir la intención; (3) `validar_articulos.py`, la regla de
  delimitador de fórmula con un solo backslash ahora excluye cualquier
  bloque de código con lenguaje declarado (```mermaid, ```python, etc.) --
  la sintaxis de nodo de Mermaid usa corchetes con backslash (`[/Texto\]`)
  que no tiene nada que ver con LaTeX y generaba un falso positivo real en
  los diagramas del Venturi. Confirmado con el validador local: 0 errores,
  0 falsos positivos, solo 2 avisos no bloqueantes (el backdating y el peso
  preexistente de `foto-perfil.png`).
- 2026-09-21: corrige el corte de descendentes (g, j, q, y -- "gaseosa" salía
  "easeosa", "líquido" salía "líauido") en los 3 diagramas Mermaid del
  artículo del Venturi. Intento previo (CSS `line-height` sobre el `<div>`
  del `foreignObject`) mejoraba pero no eliminaba el bug -- confirmado con
  capturas a `--force-device-scale-factor=4`, sin reescalado propio, que
  incluso `line-height: 1` seguía mordiendo la "y" en el diagrama más
  achicado: es un bug de rasterizado de Chromium con `foreignObject` dentro
  de un SVG escalado vía CSS, no algo que un ajuste de CSS pueda terminar de
  resolver. La solución real: `flowchart: { htmlLabels: false }` en
  `_layouts/default.html`, que hace que Mermaid dibuje el texto como
  `<text>` SVG puro -- verificado que elimina el bug de raíz (cero
  `foreignObject` reales en los 3 diagramas tras el cambio). Costo real:
  las etiquetas de nodo ya no aceptan `<br>`/`<small>`, así que las 4 que
  los usaban en `_posts/2026-09-17-lavador-venturi.md` se reescriben con
  `\n` (salto de línea propio de Mermaid, no HTML) -- se pierde el tamaño
  reducido del texto secundario que daba `<small>`, y el estilo visual de
  los subgrafos cambia levemente (título arriba del recuadro en vez del
  estilo anterior). La regla CSS del intento previo se saca por quedar
  código muerto (ya no hay ningún `foreignObject` en los diagramas).
  `02-instrucciones-notebooklm.md` queda pendiente de sumar esta regla de
  Mermaid si Elvis lo confirma en un commit aparte.
- 2026-09-21: restaura la etiqueta completa "Alta Velocidad / Inyección de
  Agua" del primer diagrama Mermaid del Venturi -- el commit anterior la
  había acortado a solo "Alta Velocidad" para resolver el corte de texto,
  pero se perdía información real del diagrama. La solución correcta no
  era acortar el contenido: era sacar el `<br>` y unir las dos frases en
  una sola línea con "/", que es justo lo que hoy mide 19 unidades de alto
  en el `foreignObject` (una sola línea real) en vez de las 38 que
  necesitaba el `<br>` de 2 líneas -- confirmado sin corte con Edge
  headless a 1280px.
- 2026-09-21: corrige el primer diagrama Mermaid del artículo del Venturi
  ("Mecánica del cizallamiento"), que se veía apretado en el sitio real --
  el SVG no tenía ninguna regla CSS del sitio (a diferencia de
  `.post-body img`), así que `assets/css/styles.css` suma
  `.post-body .mermaid-diagrama svg { max-width: 100%; height: auto;
  display: block; margin: 0 auto; }`, mismo criterio que las imágenes.
  Eso solo no alcanzaba: la etiqueta del edge "Alta Velocidad<br>Inyección
  de Agua" tenía su `foreignObject` calculado en apenas 38 unidades de
  alto para 2 líneas de texto -- ya ajustado a tamaño nativo, y peor
  todavía una vez que el diagrama se achica ~24% para caber en la columna
  real de ~580px (860px de `.page-body` menos el índice flotante de
  200px + gap). Ese recorte está horneado en la geometría que genera
  Mermaid, ningún CSS del sitio lo iba a arreglar después -- se acorta la
  etiqueta a una sola línea ("Alta Velocidad", sin `<br>`) en el `.md`.
  Confirmado con Edge headless (DOM ejecutado + captura de pantalla) que
  el diagrama completo se ve sin cortes.
- 2026-09-21: corrige el renderizado de `\begin{align*}` en el artículo del
  Venturi -- agrega el paquete `ams` a la config de MathJax en
  `_layouts/default.html` (`packages: {'[+]': ['ams']}`, faltaba junto a
  `inlineMath`/`displayMath`), pero ese no era el único bug: kramdown
  convierte un salto de línea real después de una corrida de backslashes en
  un `<br>` sin importar cuántos backslashes tenga -- el separador de fila
  `\\` de cada `align*` se estaba comiendo entero. Probado con 4 variantes
  reales sobre un post de prueba temporal (borrado después): la única
  combinación que sobrevive intacta es 4 backslashes SIN salto de línea
  inmediato, así que los 4 bloques `align*` del artículo se colapsan a una
  sola línea física cada uno. Confirmado con Edge headless (DOM ejecutado +
  captura de pantalla) que las 4 ecuaciones renderizan multi-línea reales,
  no texto crudo. De paso, se confirma a nivel de bytes que el `&` de cada
  fila era y sigue siendo el carácter ASCII correcto -- el "ε=" que se veía
  en el sitio era un efecto visual del fallo de MathJax, no una corrupción
  del `.md`. `02-instrucciones-notebooklm.md` suma las dos reglas
  aprendidas (separador de 4 backslashes en una sola línea; asterisco de
  `align*` escapado como `\*`) junto al ítem correspondiente del checklist
  de la sección 8.
- 2026-09-21: agrega soporte real de Mermaid en `_layouts/default.html`
  (`mermaid@10` vía CDN fijado, reemplaza cada `pre > code.language-mermaid`
  por su SVG usando `.textContent`, nunca `.innerHTML` -- kramdown escapa
  las flechas de Mermaid). Corrige el artículo del Venturi: el cuerpo
  entero usaba `$`/`$$` en vez de `\\(...\\)`/`\\[...\\]` (no solo la lista
  `Donde:` de Cálculo 1, que fue lo pedido -- el resto del artículo estaba
  igual de roto), se escapa el guion bajo pegado a `\text{...}` donde
  correspondía, se agrega un paréntesis faltante antes de `\text{SO}_2`, y
  se corrigen dos bugs reales de sintaxis en el segundo diagrama Mermaid
  (`direction` dentro de un `subgraph` con título entre comillas rompe el
  parser; subgraph IDs con espacios sin comillas). Verificado con Edge
  headless (DOM ejecutado y captura de pantalla, no solo grep del HTML
  estático). `02-instrucciones-notebooklm.md` suma la prohibición explícita
  de `$`/`$$` y una nueva regla de Diagramas Mermaid (sección 5), con los
  dos ítems correspondientes al checklist de la sección 8.
- 2026-09-20: `02-instrucciones-notebooklm.md` corrige la sección 5 -- el
  `image:` del front matter usa SOLO el nombre simple del archivo (ej.
  `diagrama.jpg`), no la ruta armada con slug adivinado
  (`/assets/imagenes/[slug]/[archivo]`). Mismo criterio y mismo motivo que
  la corrección de la sección 6 del commit anterior: `publicar_articulo.py`
  reescribe ese campo solo cuando ya es un nombre simple.
- 2026-09-20: `02-instrucciones-notebooklm.md` corrige la sección 6 (Guía de
  imágenes) -- el `<img src>` de cada `<figure>` ya no lleva una ruta armada
  (`/assets/imagenes/<slug>/<archivo>`), solo el nombre simple del archivo
  (ej. `diagrama.jpg`), porque `publicar_articulo.py` arma la ruta final a
  partir del nombre real de la carpeta de trabajo de Elvis y NotebookLM no
  puede adivinarla. Encontrado por un error real: NotebookLM generó
  `/_posts/articulos/lavador-venturi/diagrama.jpg`, una ruta que no existe.
- 2026-09-20: `02-instrucciones-notebooklm.md` amplía el bloque de
  conflicto/complejidad de la sección 4 con reglas de pensamiento sistémico
  (interconexión, multicausalidad, dinámica temporal, bucles de
  retroalimentación) para usar cuando el dosier las tenga de verdad, nunca
  forzadas, y suma la regla de mencionar en el cuerpo artículos ya publicados
  que se relacionen genuinamente con el sub-tema del día. Suma los dos ítems
  correspondientes al checklist de la sección 8.
- 2026-09-20: redimensiona `esquema-fitorremediacion-maiz.jpg` (2877 KB ->
  301 KB) y `grafica-comparativa-eca-suelo.jpg` (2034 KB -> 76 KB) a 860 px de
  ancho (2x la columna de artículo), calidad JPEG 85 progresivo -- mismo
  criterio que `hero-banner.jpg`/`reactor-poae-electroquimica.png`. Estas dos
  imágenes, sin redimensionar desde que se subieron el 2026-09-18, hacían
  fallar el job "Front matter, fórmulas e imágenes" del workflow en las 18
  corridas siguientes por superar el límite de 1500 KB del validador; no era
  un bug del workflow, que detectaba el problema real cada vez.
- 2026-09-20: agrega `.github/scripts/publicar_articulo.py` -- Elvis arma una
  carpeta de trabajo con el .md y sus imágenes juntas, nombradas simple
  (`esquema.jpg`, sin ruta), y el script copia el .md a `_posts/`, copia las
  imágenes a `assets/imagenes/<carpeta>/`, reescribe cada `<img src>` (y el
  `image:` del front matter) a su ruta real, y deja un commit local sin
  push. `_posts/articulos/` se suma al `exclude:` de `_config.yml` porque
  Jekyll también reconoce posts en subcarpetas de `_posts/`, no solo en la
  raíz -- sin el exclude, cualquier borrador ahí adentro se publicaría dos
  veces. Nueva sección "Alternativa con terminal" arriba.
- 2026-09-20: `02-instrucciones-notebooklm.md` suma una regla a la sección 4
  (junto al mensaje corto de plan) que exige revisar TODAS las fuentes
  secundarias subidas al notebook -- no solo el dosier -- antes de proponer
  la estructura y la cantidad de mensajes, y calcular el volumen real de
  contenido considerando también esas fuentes. Suma el ítem correspondiente
  al checklist de la sección 8.
- 2026-09-19: `02-instrucciones-notebooklm.md` suma dos reglas nuevas en la
  sección de formato de fórmulas, a partir de los dos bugs reales del
  artículo de biofiltros -- prohíbe explícitamente cualquier etiqueta HTML
  (`<br>`, `<strong>`) dentro de un bloque `\\[ \\]`/`\\( \\)` (cada paso de
  sustitución en forma de fórmula va en su propio bloque, separado por línea
  en blanco) y exige escapar el guion bajo de subíndice pegado a `\text{...}`
  (`\text{Carga}\_{...}`) para que kramdown no lo lea como cursiva. Suma
  también un ítem de doble verificación específica al checklist de la
  sección 8.
- 2026-09-19: corrige el artículo de biofiltros publicado -- las 3 imágenes se
  habían subido sueltas en `assets/imagenes/` en vez de la subcarpeta
  `assets/imagenes/fitorremediacion-biofiltros-agua/` que pide el `.md`, se
  mueven a su ruta correcta; los bloques `\[ ... \]` de Cálculo 1 y Cálculo 2
  tenían un `<br>` metido adentro del LaTeX (MathJax no procesa HTML dentro de
  `\[ \]`), se separan en dos bloques independientes; y un guion bajo repetido
  en el mismo párrafo (`\text{Carga}_{...}`, `\text{DBO}_5`/`C_{\text{entrada}}`/
  `E_{\text{DBO}_5}`) hacía que kramdown lo interpretara como cursiva y lo
  convirtiera en `<em>`, corrompiendo la fórmula igual aunque el `<br>` ya
  estuviera afuera -- se escapa como `\_` (escape estándar de Markdown, no el
  bug de paréntesis/corchetes). De paso, `reactor-poae-electroquimica.png` baja
  de 3.9 MB a 273 KB (foto de cámara sin redimensionar, mismo criterio que
  `hero-banner`).
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
