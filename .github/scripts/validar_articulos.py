#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valida los artículos de _posts/ antes de que se publiquen.

Existe porque publicar acá es pegar texto en el editor web de github.com: no
hay terminal, no hay build local y no hay nada que avise de un error hasta que
la página ya salió mal (o no salió). Esto revisa, en cada push, exactamente
las cosas que se rompieron alguna vez de verdad:

  - front matter incompleto o con una categoría que no existe (el artículo se
    publica pero no aparece en ninguna página de categoría);
  - delimitadores de LaTeX con un solo backslash, que kramdown se come y dejan
    la fórmula como paréntesis sueltos;
  - imágenes que apuntan a un archivo que no se subió, o sin texto alternativo;
  - assets sin optimizar.

No modifica nada: solo lee y reporta.
"""
import os
import re
import sys
import glob

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Reporte:
    """Contenedor de errores/avisos de UNA corrida de validacion.

    Antes `errores`/`avisos` eran listas de modulo, compartidas por
    cualquiera que importara este archivo. `panel_control.py` (servidor HTTP
    con un hilo por peticion) las limpiaba con `.clear()` antes de cada
    validacion y las leia despues -- dos pedidos casi simultaneos ("Revisar y
    publicar" de dos pestañas, o una vista previa corriendo a la vez que una
    publicacion real) podian pisarse el `.clear()`/`.append()` del otro y
    devolver una lista de errores mezclada, vacia o de otro articulo. Cada
    corrida ahora usa su propia instancia -- no hay nada que compartir, asi
    que no hay nada que pueda pisarse."""

    def __init__(self):
        self.errores = []
        self.avisos = []

    def error(self, archivo, linea, mensaje):
        self.errores.append((archivo, linea, mensaje))

    def aviso(self, archivo, linea, mensaje):
        self.avisos.append((archivo, linea, mensaje))


# Instancia usada por `main()` (linea de comandos / workflow de GitHub
# Actions): un solo proceso, una sola corrida, sin concurrencia que proteger
# -- por eso alcanza con una instancia de modulo y las funciones sueltas
# `error()`/`aviso()` de abajo, que quedan como quedaban antes para no romper
# nada que ya las llame asi. `panel_control.py` NO usa esta instancia: crea la
# suya propia con `va.Reporte()` para que dos pedidos HTTP nunca la compartan.
_reporte_cli = Reporte()
errores = _reporte_cli.errores
avisos = _reporte_cli.avisos


def error(archivo, linea, mensaje):
    _reporte_cli.error(archivo, linea, mensaje)


def aviso(archivo, linea, mensaje):
    _reporte_cli.aviso(archivo, linea, mensaje)


def leer(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return fh.read()


# --------------------------------------------------------------------------
# Las categorías válidas salen de _config.yml, que es la fuente única.
# Se leen con una expresión regular y no con PyYAML para no depender de nada
# instalado en el runner.
# --------------------------------------------------------------------------
def categorias_validas(reporte=None):
    reporte = reporte or _reporte_cli
    config = leer(os.path.join(RAIZ, "_config.yml"))
    # Tolera lineas de comentario dentro de la lista: sin eso, un "# ..."
    # entre dos categorias cortaba la lectura y escondia las de abajo.
    bloque = re.search(r"^categorias:\n((?:\s+(?:-|#).*\n)+)", config, re.M)
    if not bloque:
        reporte.error("_config.yml", 0, "no se encontró la lista `categorias:`")
        return set()
    return set(re.findall(r'name:\s*"([^"]+)"', bloque.group(1)))


def partir_front_matter(texto):
    """Devuelve (dict del front matter, posición donde termina)."""
    if not texto.startswith("---"):
        return None, -1
    fin = texto.find("\n---", 3)
    if fin == -1:
        return None, -1
    datos = {}
    for linea in texto[3:fin].split("\n"):
        m = re.match(r'^([a-zA-Z_][\w-]*):\s*(.*)$', linea)
        if m:
            valor = m.group(2).strip()
            if len(valor) > 1 and valor[0] == valor[-1] and valor[0] in "\"'":
                valor = valor[1:-1]
            datos[m.group(1)] = valor
    return datos, fin


OBLIGATORIOS = ["layout", "title", "date", "category", "excerpt"]

# Una linea que arranca con uno de estos tags es HTML crudo: kramdown la copia
# tal cual, sin parsear Markdown adentro.
BLOQUE_HTML = re.compile(
    r'^\s*</?(p|div|ul|ol|li|table|thead|tbody|tr|td|th|figure|figcaption|'
    r'h[1-6]|blockquote|pre|section|article|aside|nav)\b')


def validar_post(ruta, categorias, reporte=None):
    reporte = reporte or _reporte_cli
    rel = os.path.relpath(ruta, RAIZ).replace("\\", "/")
    texto = leer(ruta)
    nombre = os.path.basename(ruta)

    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})-[a-z0-9-]+\.md$", nombre)
    if not m:
        reporte.error(rel, 1, "el nombre del archivo debe ser AAAA-MM-DD-slug.md, "
                      "todo en minusculas y con guiones")
        fecha_nombre = None
    else:
        fecha_nombre = "-".join(m.groups())

    fm, fin_fm = partir_front_matter(texto)
    if fm is None:
        reporte.error(rel, 1, "no tiene front matter: el archivo tiene que empezar con "
                      "una linea `---` y cerrar con otra `---`")
        return

    for clave in OBLIGATORIOS:
        if clave not in fm or not fm[clave]:
            reporte.error(rel, 1, "falta `%s:` en el front matter" % clave)

    # Los PENDIENTE que deja el panel de control: excerpt e image son
    # obligatorios (bloquean); tags es opcional (solo avisa). En el flujo
    # normal un tags PENDIENTE nunca llega hasta aca -- publicar_articulo.py
    # lo saca al copiar --, pero un .md pegado a mano en el editor web si
    # podria traerlo. El sitio lo ignora igual (ver Sugeridos en post.html).
    # Se busca el marcador exacto (la palabra PENDIENTE, en mayusculas, como
    # la escribe el panel), no un pedazo de texto: un slug como
    # "...-tags-pendientes-..." en la ruta de la imagen no es un pendiente.
    for clave in ("excerpt", "image"):
        if re.search(r"\bPENDIENTE\b", fm.get(clave, "")):
            reporte.error(rel, 1, "`%s:` sigue en PENDIENTE: es obligatorio, hay que "
                          "completarlo con lo que entrego NotebookLM" % clave)
    temas = [t.strip().strip("\"'").strip()
             for t in fm.get("tags", "").strip().strip("[]").split(",")]
    if any(t.upper() == "PENDIENTE" for t in temas):
        reporte.aviso(rel, 1, "`tags:` sigue en PENDIENTE. Es opcional y el sitio lo "
                      "ignora al armar Sugeridos, pero conviene poner el tema "
                      "real o borrar la linea: el feed RSS publica los tags "
                      "tal cual.")

    if fm.get("layout") and fm["layout"] != "post":
        reporte.error(rel, 1, "`layout:` tiene que ser `post`, dice `%s`" % fm["layout"])

    cat = fm.get("category")
    if cat and categorias and cat not in categorias:
        reporte.error(rel, 1, "la categoria «%s» no es ninguna de las de _config.yml. "
                      "Validas: %s" % (cat, " | ".join(sorted(categorias))))

    fecha_fm = fm["date"].split()[0] if fm.get("date") else None
    if fecha_nombre and fecha_fm and fecha_fm != fecha_nombre:
        reporte.aviso(rel, 1, "la fecha del front matter (%s) no coincide con la del "
                      "nombre del archivo (%s). Puede ser intencional "
                      "(backdating) o un error -- el validador no puede "
                      "distinguirlo, asi que avisa sin bloquear."
                      % (fecha_fm, fecha_nombre))

    if fm.get("excerpt") and len(fm["excerpt"]) < 40:
        reporte.aviso(rel, 1, "el `excerpt:` es muy corto (%d caracteres): es el texto "
                      "que se lee en la tarjeta de la portada"
                      % len(fm["excerpt"]))

    validar_imagenes(rel, texto, fm, reporte)
    validar_latex(rel, texto, reporte)
    validar_titulo_repetido(rel, texto, fm, fin_fm, reporte)


def ruta_existe(ruta_web):
    if ruta_web.startswith(("http://", "https://", "//")):
        return True
    return os.path.isfile(os.path.join(RAIZ, ruta_web.lstrip("/").split("?")[0]))


def validar_imagenes(rel, texto, fm, reporte=None):
    reporte = reporte or _reporte_cli
    if fm.get("image") and not ruta_existe(fm["image"]):
        reporte.error(rel, 1, "el `image:` del front matter apunta a un archivo que no "
                      "esta en el repo: %s" % fm["image"])

    for n, linea in enumerate(texto.split("\n"), 1):
        for alt, ruta in re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', linea):
            if not ruta_existe(ruta):
                reporte.error(rel, n, "imagen que no esta en el repo: %s "
                              "(falto subirla con Add file -> Upload files?)" % ruta)
            if not alt.strip():
                reporte.error(rel, n, "imagen sin texto alternativo: ![](%s). El alt "
                              "describe la imagen a quien no puede verla." % ruta)

        for tag in re.findall(r'<img\b[^>]*>', linea):
            m_src = re.search(r'src="([^"]+)"', tag)
            if not m_src:
                reporte.error(rel, n, "un <img> sin atributo src")
                continue
            if not ruta_existe(m_src.group(1)):
                reporte.error(rel, n, "imagen que no esta en el repo: %s "
                              "(falto subirla con Add file -> Upload files?)"
                              % m_src.group(1))
            m_alt = re.search(r'alt="([^"]*)"', tag)
            if m_alt is None:
                reporte.error(rel, n, "un <img> sin atributo alt: %s" % m_src.group(1))
            elif not m_alt.group(1).strip():
                reporte.error(rel, n, "un <img> con alt vacio: %s" % m_src.group(1))

    # Toda imagen del cuerpo va dentro de un <figure> con su <figcaption>.
    # Antes esto comparaba el CONTEO GLOBAL de <figure> contra el de
    # <figcaption> en todo el archivo -- dos figuras donde una se queda sin
    # pie y otra tiene dos pasaban desapercibidas porque el total (2 y 2)
    # cuadraba igual. Ahora se revisa CADA bloque <figure>...</figure> por
    # separado.
    bloques_figure = list(re.finditer(r'<figure\b[^>]*>.*?</figure>', texto, re.S))
    for bloque in bloques_figure:
        n_figcaption = len(re.findall(r'<figcaption\b', bloque.group(0)))
        linea = texto.count("\n", 0, bloque.start()) + 1
        if n_figcaption == 0:
            reporte.error(rel, linea, "un <figure> sin su <figcaption>: cada figura "
                          "lleva siempre su pie de foto dentro del mismo bloque.")
        elif n_figcaption > 1:
            reporte.error(rel, linea, "un <figure> con %d <figcaption> adentro: cada "
                          "figura lleva exactamente uno." % n_figcaption)

    figcaptions_totales = len(re.findall(r'<figcaption\b', texto))
    figcaptions_en_figure = sum(
        len(re.findall(r'<figcaption\b', bloque.group(0))) for bloque in bloques_figure
    )
    if figcaptions_totales != figcaptions_en_figure:
        reporte.error(rel, 1, "hay un <figcaption> fuera de cualquier <figure> (o un "
                      "<figure> con mas de un <figcaption>): revisa que los bloques "
                      "esten bien formados y balanceados.")


def bloques_codigo_con_lenguaje(texto):
    """Rangos de linea (inclusive, 1-indexado) de cada bloque ```lenguaje ...
    ``` con lenguaje declarado. Ninguno de estos se escanea buscando
    delimitadores de formula: encontrado con un caso real, la sintaxis de
    Mermaid usa corchetes con backslash (ej. [/Texto\\]) que no tiene nada
    que ver con LaTeX y generaba un falso positivo. Un ``` sin lenguaje (los
    bloques de sustitucion numerica con <br>) no cuenta como excluido -- ahi
    si puede aparecer contenido real a revisar.
    """
    rangos = []
    inicio = None
    for n, linea in enumerate(texto.split("\n"), 1):
        if inicio is None:
            if re.match(r'^\s*```\w', linea):
                inicio = n
        elif re.match(r'^\s*```\s*$', linea):
            rangos.append((inicio, n))
            inicio = None
    return rangos


def validar_latex(rel, texto, reporte=None):
    r"""
    kramdown borra un backslash simple antes de ( ) [ ] -- y tambien antes de
    $. Por eso los 4 delimitadores de formula, MAS cualquier `$` que aparezca
    dentro de una formula (ej. un costo en dolares en un calculo), van
    DUPLICADOS en el .md fuente. Ver la nota de kramdown en CLAUDE.md.

    El caso de `$` se sumo el 2026-09-27 despues de un bug real: 02 decia que
    el LaTeX interno (`\\frac`, `\\cdot`, etc.) iba con backslash simple "ya
    que las letras no estan en el set que kramdown escapa" -- pero `$` no es
    una letra, y SI esta en ese set. Un build real confirmo que `\$192` llega
    como `$192` crudo al HTML, sin proteccion, y ya paso en un articulo
    publicado (cosecha de lluvia) antes de que existiera este chequeo.

    Salvedad 1: eso vale para el Markdown, no para el HTML crudo pegado en un
    .md. Si la linea arranca con un tag de bloque, kramdown no le parsea el
    contenido y el backslash simple llega intacto al sitio -- es el caso del
    articulo del Venturi, migrado desde HTML plano, cuyas formulas se ven
    bien. Esas lineas se saltan para no dar un falso positivo.

    Salvedad 2: tampoco vale dentro de un bloque de codigo con lenguaje
    declarado (```mermaid, ```python, etc.) -- ningun bloque de codigo
    deberia escanearse buscando delimitadores de formula, esos backslash son
    sintaxis de otra cosa.
    """
    reporte = reporte or _reporte_cli
    rangos_codigo = bloques_codigo_con_lenguaje(texto)
    for n, linea in enumerate(texto.split("\n"), 1):
        if BLOQUE_HTML.match(linea):
            continue
        if any(a <= n <= b for a, b in rangos_codigo):
            continue
        for m in re.finditer(r'(?<!\\)\\[()\[\]$]', linea):
            if m.group(0)[-1] == "$":
                reporte.error(rel, n, "el signo $ dentro de una formula lleva el "
                              "backslash duplicado (`\\\\$`), no uno solo (`%s`): "
                              "kramdown se come el simple igual que con `()[]`, y el "
                              "$ sale crudo, sin proteger, dentro del span de MathJax."
                              % m.group(0))
            else:
                reporte.error(rel, n, "delimitador de formula con un solo backslash: `%s`. "
                              "kramdown se lo come y la formula sale como "
                              "parentesis sueltos; va duplicado (`\\%s`)."
                              % (m.group(0), m.group(0)))

    pares = [(r'\\\\\(', r'\\\\\)', "\\\\(", "\\\\)"),
             (r'\\\\\[', r'\\\\\]', "\\\\[", "\\\\]")]
    for abre_re, cierra_re, abre, cierra in pares:
        na = len(re.findall(abre_re, texto))
        nc = len(re.findall(cierra_re, texto))
        if na != nc:
            reporte.error(rel, 1, "formulas mal cerradas: %d `%s` contra %d `%s`"
                          % (na, abre, nc, cierra))


def validar_titulo_repetido(rel, texto, fm, fin_fm, reporte=None):
    """El layout ya imprime el titulo; repetirlo en el cuerpo lo duplica."""
    reporte = reporte or _reporte_cli
    cuerpo = texto[fin_fm + 4:] if fin_fm != -1 else texto
    titulo = (fm.get("title") or "").strip()
    if not titulo:
        return
    for linea in cuerpo.strip().split("\n")[:3]:
        limpia = re.sub(r'</?[a-z]+[^>]*>', '', linea)
        limpia = limpia.replace("#", "").replace("*", "").strip()
        if limpia and limpia == titulo:
            reporte.error(rel, 1, "el cuerpo repite el titulo del articulo. El layout "
                          "ya lo imprime desde el front matter: sale dos veces "
                          "en la pagina. El cuerpo arranca en el primer `## `.")
            return


AVISO_KB = 500
ERROR_KB = 1500


def validar_assets(reporte=None):
    reporte = reporte or _reporte_cli
    patrones = ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp")
    for carpeta, _, _ in os.walk(os.path.join(RAIZ, "assets")):
        for patron in patrones:
            for ruta in sorted(glob.glob(os.path.join(carpeta, patron))):
                rel = os.path.relpath(ruta, RAIZ).replace("\\", "/")
                kb = os.path.getsize(ruta) / 1024.0
                if kb > ERROR_KB:
                    reporte.error(rel, 0, "la imagen pesa %.0f KB. Arriba de %d KB hay "
                                  "que redimensionarla antes de subirla."
                                  % (kb, ERROR_KB))
                elif kb > AVISO_KB:
                    reporte.aviso(rel, 0, "la imagen pesa %.0f KB; conviene bajarla de "
                                  "%d KB." % (kb, AVISO_KB))


def main():
    reporte = _reporte_cli
    categorias = categorias_validas(reporte)
    posts = sorted(glob.glob(os.path.join(RAIZ, "_posts", "*.md")))
    if not posts:
        reporte.error("_posts", 0, "no hay ningun articulo en _posts/")
    for ruta in posts:
        validar_post(ruta, categorias, reporte)
    validar_assets(reporte)

    for archivo, linea, mensaje in reporte.avisos:
        print("::warning file=%s,line=%d::%s" % (archivo, max(linea, 1), mensaje))
    for archivo, linea, mensaje in reporte.errores:
        print("::error file=%s,line=%d::%s" % (archivo, max(linea, 1), mensaje))

    print("")
    print("Articulos revisados: %d" % len(posts))
    print("Avisos: %d   Errores: %d" % (len(reporte.avisos), len(reporte.errores)))
    if reporte.errores:
        print("")
        print("Hay errores que van a romper el articulo publicado. El detalle de")
        print("cada regla esta en 02-instrucciones-notebooklm.md y en CLAUDE.md.")
        return 1
    print("Todo en orden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
