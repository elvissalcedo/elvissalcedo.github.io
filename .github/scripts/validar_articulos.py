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

errores = []
avisos = []


def error(archivo, linea, mensaje):
    errores.append((archivo, linea, mensaje))


def aviso(archivo, linea, mensaje):
    avisos.append((archivo, linea, mensaje))


def leer(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return fh.read()


# --------------------------------------------------------------------------
# Las 8 categorías válidas salen de _config.yml, que es la fuente única.
# Se leen con una expresión regular y no con PyYAML para no depender de nada
# instalado en el runner.
# --------------------------------------------------------------------------
def categorias_validas():
    config = leer(os.path.join(RAIZ, "_config.yml"))
    bloque = re.search(r"^categorias:\n((?:\s+-.*\n)+)", config, re.M)
    if not bloque:
        error("_config.yml", 0, "no se encontró la lista `categorias:`")
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


def validar_post(ruta, categorias):
    rel = os.path.relpath(ruta, RAIZ).replace("\\", "/")
    texto = leer(ruta)
    nombre = os.path.basename(ruta)

    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})-[a-z0-9-]+\.md$", nombre)
    if not m:
        error(rel, 1, "el nombre del archivo debe ser AAAA-MM-DD-slug.md, "
                      "todo en minusculas y con guiones")
        fecha_nombre = None
    else:
        fecha_nombre = "-".join(m.groups())

    fm, fin_fm = partir_front_matter(texto)
    if fm is None:
        error(rel, 1, "no tiene front matter: el archivo tiene que empezar con "
                      "una linea `---` y cerrar con otra `---`")
        return

    for clave in OBLIGATORIOS:
        if clave not in fm or not fm[clave]:
            error(rel, 1, "falta `%s:` en el front matter" % clave)

    if fm.get("layout") and fm["layout"] != "post":
        error(rel, 1, "`layout:` tiene que ser `post`, dice `%s`" % fm["layout"])

    cat = fm.get("category")
    if cat and categorias and cat not in categorias:
        error(rel, 1, "la categoria «%s» no es ninguna de las 8 de _config.yml. "
                      "Validas: %s" % (cat, " | ".join(sorted(categorias))))

    fecha_fm = fm["date"].split()[0] if fm.get("date") else None
    if fecha_nombre and fecha_fm and fecha_fm != fecha_nombre:
        error(rel, 1, "la fecha del front matter (%s) no coincide con la del "
                      "nombre del archivo (%s)" % (fecha_fm, fecha_nombre))

    if fm.get("excerpt") and len(fm["excerpt"]) < 40:
        aviso(rel, 1, "el `excerpt:` es muy corto (%d caracteres): es el texto "
                      "que se lee en la tarjeta de la portada"
                      % len(fm["excerpt"]))

    validar_imagenes(rel, texto, fm)
    validar_latex(rel, texto)
    validar_titulo_repetido(rel, texto, fm, fin_fm)


def ruta_existe(ruta_web):
    if ruta_web.startswith(("http://", "https://", "//")):
        return True
    return os.path.isfile(os.path.join(RAIZ, ruta_web.lstrip("/").split("?")[0]))


def validar_imagenes(rel, texto, fm):
    if fm.get("image") and not ruta_existe(fm["image"]):
        error(rel, 1, "el `image:` del front matter apunta a un archivo que no "
                      "esta en el repo: %s" % fm["image"])

    for n, linea in enumerate(texto.split("\n"), 1):
        for alt, ruta in re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', linea):
            if not ruta_existe(ruta):
                error(rel, n, "imagen que no esta en el repo: %s "
                              "(falto subirla con Add file -> Upload files?)" % ruta)
            if not alt.strip():
                error(rel, n, "imagen sin texto alternativo: ![](%s). El alt "
                              "describe la imagen a quien no puede verla." % ruta)

        for tag in re.findall(r'<img\b[^>]*>', linea):
            m_src = re.search(r'src="([^"]+)"', tag)
            if not m_src:
                error(rel, n, "un <img> sin atributo src")
                continue
            if not ruta_existe(m_src.group(1)):
                error(rel, n, "imagen que no esta en el repo: %s "
                              "(falto subirla con Add file -> Upload files?)"
                              % m_src.group(1))
            m_alt = re.search(r'alt="([^"]*)"', tag)
            if m_alt is None:
                error(rel, n, "un <img> sin atributo alt: %s" % m_src.group(1))
            elif not m_alt.group(1).strip():
                error(rel, n, "un <img> con alt vacio: %s" % m_src.group(1))

    # Toda imagen del cuerpo va dentro de un <figure> con su <figcaption>.
    figures = len(re.findall(r'<figure\b', texto))
    figcaptions = len(re.findall(r'<figcaption\b', texto))
    if figures != figcaptions:
        error(rel, 1, "hay %d <figure> y %d <figcaption>: cada figura lleva "
                      "siempre su pie de foto" % (figures, figcaptions))


def validar_latex(rel, texto):
    """
    kramdown borra un backslash simple antes de ( ) [ ]. Por eso los 4
    delimitadores de formula van DUPLICADOS en el .md fuente. Ver la nota de
    kramdown en CLAUDE.md.

    Salvedad: eso vale para el Markdown, no para el HTML crudo pegado en un
    .md. Si la linea arranca con un tag de bloque, kramdown no le parsea el
    contenido y el backslash simple llega intacto al sitio -- es el caso del
    articulo del Venturi, migrado desde HTML plano, cuyas formulas se ven
    bien. Esas lineas se saltan para no dar un falso positivo.
    """
    for n, linea in enumerate(texto.split("\n"), 1):
        if BLOQUE_HTML.match(linea):
            continue
        for m in re.finditer(r'(?<!\\)\\[()\[\]]', linea):
            error(rel, n, "delimitador de formula con un solo backslash: `%s`. "
                          "kramdown se lo come y la formula sale como "
                          "parentesis sueltos; va duplicado (`\\%s`)."
                          % (m.group(0), m.group(0)))

    pares = [(r'\\\\\(', r'\\\\\)', "\\\\(", "\\\\)"),
             (r'\\\\\[', r'\\\\\]', "\\\\[", "\\\\]")]
    for abre_re, cierra_re, abre, cierra in pares:
        na = len(re.findall(abre_re, texto))
        nc = len(re.findall(cierra_re, texto))
        if na != nc:
            error(rel, 1, "formulas mal cerradas: %d `%s` contra %d `%s`"
                          % (na, abre, nc, cierra))


def validar_titulo_repetido(rel, texto, fm, fin_fm):
    """El layout ya imprime el titulo; repetirlo en el cuerpo lo duplica."""
    cuerpo = texto[fin_fm + 4:] if fin_fm != -1 else texto
    titulo = (fm.get("title") or "").strip()
    if not titulo:
        return
    for linea in cuerpo.strip().split("\n")[:3]:
        limpia = re.sub(r'</?[a-z]+[^>]*>', '', linea)
        limpia = limpia.replace("#", "").replace("*", "").strip()
        if limpia and limpia == titulo:
            error(rel, 1, "el cuerpo repite el titulo del articulo. El layout "
                          "ya lo imprime desde el front matter: sale dos veces "
                          "en la pagina. El cuerpo arranca en el primer `## `.")
            return


AVISO_KB = 500
ERROR_KB = 1500


def validar_assets():
    patrones = ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp")
    for carpeta, _, _ in os.walk(os.path.join(RAIZ, "assets")):
        for patron in patrones:
            for ruta in sorted(glob.glob(os.path.join(carpeta, patron))):
                rel = os.path.relpath(ruta, RAIZ).replace("\\", "/")
                kb = os.path.getsize(ruta) / 1024.0
                if kb > ERROR_KB:
                    error(rel, 0, "la imagen pesa %.0f KB. Arriba de %d KB hay "
                                  "que redimensionarla antes de subirla."
                                  % (kb, ERROR_KB))
                elif kb > AVISO_KB:
                    aviso(rel, 0, "la imagen pesa %.0f KB; conviene bajarla de "
                                  "%d KB." % (kb, AVISO_KB))


def main():
    categorias = categorias_validas()
    posts = sorted(glob.glob(os.path.join(RAIZ, "_posts", "*.md")))
    if not posts:
        error("_posts", 0, "no hay ningun articulo en _posts/")
    for ruta in posts:
        validar_post(ruta, categorias)
    validar_assets()

    for archivo, linea, mensaje in avisos:
        print("::warning file=%s,line=%d::%s" % (archivo, max(linea, 1), mensaje))
    for archivo, linea, mensaje in errores:
        print("::error file=%s,line=%d::%s" % (archivo, max(linea, 1), mensaje))

    print("")
    print("Articulos revisados: %d" % len(posts))
    print("Avisos: %d   Errores: %d" % (len(avisos), len(errores)))
    if errores:
        print("")
        print("Hay errores que van a romper el articulo publicado. El detalle de")
        print("cada regla esta en 02-instrucciones-notebooklm.md y en CLAUDE.md.")
        return 1
    print("Todo en orden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
