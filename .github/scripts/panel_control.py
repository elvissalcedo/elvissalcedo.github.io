#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Panel de control local para crear y eliminar articulos de Git_Page.

Arranca un servidor HTTP en 127.0.0.1, solo con la libreria estandar de
Python (nada que instalar). Pensado para correr con doble clic en
panel-control-gitpage.bat, que abre el navegador solo.

Cinco flujos: "Crear articulo nuevo" arma la carpeta de trabajo
(_posts/articulos/<slug>/) con el .md y su front matter listos para que
Elvis pegue el contenido de NotebookLM. "Editar articulo publicado" hace
lo mismo pero partiendo de un articulo YA PUBLICADO -- copia su .md real
(sin PENDIENTE) y sus imagenes a una carpeta de trabajo nueva, para seguir
agregandole contenido; si esa carpeta ya existe (cambios sin publicar),
avisa y deja elegir entre seguir con lo que hay o reiniciarla desde lo
publicado, nunca sobreescribe en silencio. "Publicar borrador" reemplaza
el paso manual de correr publicar_articulo.py en la terminal -- copia el
borrador a _posts/ y assets/imagenes/ SIN commit, arma una vista previa
real con `bundle exec jekyll build` embebida en un iframe, y solo hace
`git fetch` + `git rebase origin/main` (via pa.confirmar_commit, para
evitar el rechazo "rejected... fetch first" si origin avanzo mientras
tanto) + `git add` + commit + push cuando Elvis aprieta "Confirmar y
publicar"; si en cambio aprieta "Volver a editar", deshace la copia sin
dejar rastro.
"Vista previa en vivo" reemplaza a Ctrl+Shift+V de VS Code: copia el
borrador igual que "Publicar borrador" pero sin chequear PENDIENTE ni
correr el validador, arranca (o reusa) `bundle exec jekyll serve
--livereload` en segundo plano, abre la URL directa del articulo y vigila
la carpeta de trabajo cada 1.5 segundos para volver a copiar solo en cada
cambio -- Jekyll se refresca solo via livereload. "Detener vista previa"
corta la vigilancia y descarta la copia, sin commitear nada.
"Eliminar articulo publicado" borra un articulo que ya esta en _posts/
(con git rm + commit local, nunca push).

URL de cada articulo nuevo: Jekyll arma la ruta automatica con
`:categories` a partir del `category:` del front matter, pero solo hace
.downcase -- no saca tildes ni cambia espacios por guiones. Para las 4
categorias de nombre compuesto (Toxicologia y Salud, Sostenibilidad y
Energia, Gestion y Politica, Filosofia y Decision) eso da una URL rota
(espacios y tildes literales). Confirmado con una build real de Jekyll en
un clon aislado. Por eso este panel escribe SIEMPRE un `permalink:`
explicito usando el slug prolijo de _config.yml, para todas las categorias por
igual -- decision de Elvis del 2026-09-21 frente a esta alternativa.
"""
import functools
import html
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import date, datetime

import publicar_articulo as pa
import validar_articulos as va

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUERTO = 8420
PUERTO_VISTA_PREVIA = 8421
PUERTO_SERVE_VIVO = 4000
URL_SITIO = "https://elvissalcedo.github.io"
SITE_DIR = os.path.join(RAIZ, "_site")


class ErrorPanel(Exception):
    """Un problema de datos de entrada: se muestra tal cual, sin traceback."""


# --------------------------------------------------------------------------
# Utilidades compartidas por los dos flujos
# --------------------------------------------------------------------------
def leer_categorias():
    """Lee la lista `categorias:` (name + slug) de _config.yml -- fuente
    unica, la misma que usa validar_articulos.py."""
    with open(os.path.join(RAIZ, "_config.yml"), encoding="utf-8") as fh:
        config = fh.read()
    # Tolera lineas de comentario dentro de la lista: sin eso, un "# ..."
    # entre dos categorias cortaba la lectura y escondia las de abajo.
    bloque = re.search(r"^categorias:\n((?:\s+(?:-|#).*\n)+)", config, re.M)
    if not bloque:
        return []
    filas = []
    for linea in bloque.group(1).splitlines():
        m = re.search(r'name:\s*"([^"]+)"\s*,\s*slug:\s*"([^"]+)"', linea)
        if m:
            filas.append({"name": m.group(1), "slug": m.group(2)})
    return filas


def slug_de_categoria(nombre_categoria, categorias):
    for c in categorias:
        if c["name"] == nombre_categoria:
            return c["slug"]
    return None


def slugify(texto):
    """minusculas, sin tildes, espacios (y cualquier separador) a guiones."""
    nfkd = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    sin_tildes = sin_tildes.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", sin_tildes).strip("-")
    return slug


# Windows sin LongPathsEnabled corta en 260 caracteres la ruta completa, y el
# .md repite el slug dos veces (carpeta + nombre de archivo): un titulo de 105
# caracteres de slug dio una ruta de 286 y un FileNotFoundError en el open().
LARGO_MAXIMO_SLUG = 60
LARGO_MAXIMO_RUTA = 240  # margen bajo 260 para imagenes y copias posteriores
LARGO_MAXIMO_RUTA_WINDOWS = 259  # MAX_PATH menos el nulo final


def slug_de_titulo(titulo):
    """slugify() recortado a LARGO_MAXIMO_SLUG, cortando en un guion completo
    (nunca a mitad de palabra). El titulo completo sigue en `title:`."""
    slug = slugify(titulo)
    if len(slug) <= LARGO_MAXIMO_SLUG:
        return slug
    recortado = slug[:LARGO_MAXIMO_SLUG + 1]
    corte = recortado.rfind("-")
    if corte > 0:
        return recortado[:corte].strip("-")
    return slug[:LARGO_MAXIMO_SLUG].strip("-")  # una sola palabra gigante


# Clave interna (no es YAML valido, no choca con ningun campo real): el .md
# no esta en UTF-8 -- tipico al guardarlo desde el Bloc de notas en ANSI.
# Antes un solo archivo asi tiraba abajo la lista entera con ERR_EMPTY_RESPONSE.
NO_UTF8 = " no_utf8"
AVISO_NO_UTF8 = ("el .md no está guardado en UTF-8 -- abrilo en VS Code y "
                 "guardalo con la codificación UTF-8")


def leer_front_matter(ruta):
    try:
        with open(ruta, encoding="utf-8") as fh:
            texto = fh.read()
        no_utf8 = False
    except UnicodeDecodeError:
        with open(ruta, encoding="utf-8", errors="replace") as fh:
            texto = fh.read()
        no_utf8 = True
    datos = {NO_UTF8: True} if no_utf8 else {}
    if not texto.startswith("---"):
        return datos
    fin = texto.find("\n---", 3)
    if fin == -1:
        return datos
    for linea in texto[3:fin].split("\n"):
        m = re.match(r'^([a-zA-Z_][\w-]*):\s*(.*)$', linea)
        if m:
            valor = m.group(2).strip()
            if len(valor) > 1 and valor[0] == valor[-1] and valor[0] in "\"'":
                valor = valor[1:-1]
            datos[m.group(1)] = valor
    return datos


_PATRON_CATEGORIA_FM = re.compile(r'^category:[ \t]*(.*?)[ \t]*\r?$', re.M)
# Solo el primer segmento (la categoria) de un permalink con la forma que
# escribe "Crear articulo nuevo": /<slug-categoria>/AAAA/MM/DD/<slug>.html.
# Un permalink de otra forma (ej. /lavador-venturi.html) no se toca.
_PATRON_PERMALINK_FM = re.compile(
    r'^permalink:[ \t]*["\']?/([^/\s"\']+)(?=/\d{4}/\d{2}/\d{2}/)', re.M)


def alinear_permalink(texto):
    """Devuelve (texto, cambio). Si el `permalink:` del front matter quedo con
    una categoria distinta de la que dice `category:` (Elvis cambio la
    categoria a mano despues de crear el articulo), reescribe SOLO ese primer
    segmento con el slug de la categoria actual -- fecha, slug y el resto del
    permalink quedan intactos. `cambio` es (slug_viejo, slug_nuevo), o None
    si ya coincidian o si no hay nada seguro que corregir (sin permalink, de
    otra forma, o una categoria que no es ninguna de _config.yml: eso ya lo
    marca el validador)."""
    if not texto.startswith("---"):
        return texto, None
    fin = texto.find("\n---", 3)
    if fin == -1:
        return texto, None
    front_matter = texto[:fin]
    m_cat = _PATRON_CATEGORIA_FM.search(front_matter)
    m_link = _PATRON_PERMALINK_FM.search(front_matter)
    if not m_cat or not m_link:
        return texto, None
    nombre = m_cat.group(1)
    if len(nombre) > 1 and nombre[0] == nombre[-1] and nombre[0] in "\"'":
        nombre = nombre[1:-1]
    slug_cat = slug_de_categoria(nombre, leer_categorias())
    if slug_cat is None or m_link.group(1) == slug_cat:
        return texto, None
    nuevo = front_matter[:m_link.start(1)] + slug_cat + front_matter[m_link.end(1):]
    return nuevo + texto[fin:], (m_link.group(1), slug_cat)


def alinear_permalink_en_disco(ruta_md):
    """Aplica alinear_permalink al .md de la carpeta de trabajo y lo guarda
    ahi, para que lo que ve Elvis en el editor coincida con lo que se publica.
    Preserva los saltos de linea (newline="") y no falla si el archivo esta
    bloqueado: los llamadores igual aplican la correccion en memoria antes de
    renderizar, asi que la vista previa no depende de que este guardado."""
    try:
        with open(ruta_md, encoding="utf-8", newline="") as fh:
            texto = fh.read()
    except (OSError, UnicodeDecodeError):
        return None
    nuevo, cambio = alinear_permalink(texto)
    if not cambio:
        return None
    try:
        with open(ruta_md, "w", encoding="utf-8", newline="") as fh:
            fh.write(nuevo)
    except OSError:
        return None
    print("permalink: /%s/... -> /%s/... en %s (para que coincida con category:)"
          % (cambio[0], cambio[1], os.path.basename(ruta_md)))
    return cambio


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def ruta_git(ruta_absoluta):
    return os.path.relpath(ruta_absoluta, RAIZ).replace(os.sep, "/")


# --------------------------------------------------------------------------
# Proteccion de cambios sin comitear
#
# Las vistas previas escriben copias reales en _posts/ y assets/imagenes/, y
# despues las deshacen. Deshacerlas con `git checkout --` a ciegas puede
# destruir trabajo de Elvis: si el .md publicado tenia una correccion hecha a
# mano todavia sin comitear, la copia la pisaba en disco y el checkout
# posterior la borraba para siempre, sin aviso.
#
# Regla: solo se descarta un archivo que ESTE proceso escribio. Cualquier otra
# cosa se guarda en un stash (recuperable con `git stash list` / `git stash
# pop`) en vez de perderse.
# --------------------------------------------------------------------------
_copias_del_panel = set()


def _clave_ruta(ruta_absoluta):
    return os.path.normcase(os.path.abspath(ruta_absoluta))


def registrar_copia(*rutas_absolutas):
    for ruta in rutas_absolutas:
        _copias_del_panel.add(_clave_ruta(ruta))


def es_copia_del_panel(ruta_absoluta):
    return _clave_ruta(ruta_absoluta) in _copias_del_panel


def hay_cambios_sin_comitear(ruta_absoluta):
    """True si el archivo esta trackeado en git y lo que hay en disco difiere
    de lo ultimo comiteado."""
    rel = ruta_git(ruta_absoluta)
    if git("ls-files", "--error-unmatch", "--", rel).returncode != 0:
        return False
    return bool(git("status", "--porcelain", "--", rel).stdout.strip())


def respaldar_en_stash(ruta_absoluta, motivo):
    """Guarda en un stash los cambios sin comitear de UN archivo en vez de
    destruirlos, y deja el archivo como estaba en el ultimo commit. Devuelve
    la etiqueta del stash, o None si no habia nada que guardar."""
    if not hay_cambios_sin_comitear(ruta_absoluta):
        return None
    rel = ruta_git(ruta_absoluta)
    etiqueta = "panel-control: %s -- %s" % (motivo, rel)
    resultado = git("stash", "push", "-m", etiqueta, "--", rel)
    if resultado.returncode != 0:
        raise ErrorPanel(
            "«%s» tiene cambios sin comitear y no los pude guardar en un "
            "stash, asi que prefiero no pisarlos. Revisalos con `git status` "
            "y comitealos (o guardalos a mano) antes de seguir.\n\n%s"
            % (rel, resultado.stderr or resultado.stdout)
        )
    return etiqueta


def proteger_articulo_publicado(nombre_md):
    """Se llama ANTES de pisar _posts/<nombre_md> con la copia del borrador.
    Si ese archivo publicado tiene cambios sin comitear que no escribimos
    nosotros, los guarda en un stash. Devuelve la etiqueta del stash o None."""
    ruta = os.path.join(RAIZ, "_posts", nombre_md)
    if es_copia_del_panel(ruta):
        return None
    return respaldar_en_stash(ruta, "cambios sin comitear guardados antes de la vista previa")


# --------------------------------------------------------------------------
# Flujo "Crear articulo nuevo"
# --------------------------------------------------------------------------
def buscar_duplicado(slug):
    """Busca el slug en la carpeta de trabajo y en los articulos ya
    publicados. Devuelve un dict con titulo/fecha/donde, o None."""
    carpeta_trabajo = os.path.join(RAIZ, "_posts", "articulos", slug)
    if os.path.isdir(carpeta_trabajo):
        md = next(
            (f for f in sorted(os.listdir(carpeta_trabajo)) if f.endswith(".md")),
            None,
        )
        if md:
            fm = leer_front_matter(os.path.join(carpeta_trabajo, md))
            return {
                "titulo": fm.get("title", slug),
                "fecha": fm.get("date", "?"),
                "donde": "carpeta de trabajo _posts/articulos/%s/" % slug,
            }

    patron = re.compile(r"^\d{4}-\d{2}-\d{2}-%s\.md$" % re.escape(slug))
    carpeta_posts = os.path.join(RAIZ, "_posts")
    for nombre in sorted(os.listdir(carpeta_posts)):
        if patron.match(nombre):
            fm = leer_front_matter(os.path.join(carpeta_posts, nombre))
            return {
                "titulo": fm.get("title", slug),
                "fecha": fm.get("date", "?"),
                "donde": "_posts/%s" % nombre,
            }
    return None


def slug_libre(slug):
    """slug, o slug-2, slug-3... el primero que no choque con nada. Con el
    recorte a LARGO_MAXIMO_SLUG, dos titulos largos distintos pueden dar el
    mismo slug; "Continuar de todas formas" antes reusaba la carpeta y
    sobrescribia su .md (misma fecha) o le metia un segundo .md (otra
    fecha), y un post publicado con el mismo slug compartia la carpeta de
    imagenes -- el mismo choque que costo las imagenes de fitorremediacion."""
    candidato, n = slug, 2
    while buscar_duplicado(candidato):
        candidato = "%s-%d" % (slug, n)
        n += 1
    return candidato


def normalizar_temas(texto):
    """"Fitorremediación,  suelos , ,Fitorremediación" -> ["Fitorremediación",
    "suelos"]: separa por comas, saca espacios de mas, descarta vacios y
    repetidos (sin distinguir mayusculas) y el marcador PENDIENTE, que no es
    un tema. Una lista vacia significa "sin temas": el .md sale sin tags."""
    temas, vistos = [], set()
    for t in (texto or "").split(","):
        t = " ".join(t.split())
        clave = t.lower()
        if t and clave != "pendiente" and clave not in vistos:
            vistos.add(clave)
            temas.append(t)
    return temas


def linea_tags(temas):
    """`tags: [Fitorremediación, Suelos]` -- legible, como los que ya se
    escriben a mano. Solo va entre comillas el tema que trae un caracter que
    YAML leeria distinto (`Agua: calidad`, `#reuso`, `[x]`...)."""
    def _yaml(t):
        if re.search(r"[:#\[\]{}\"'&*!|>%@`]", t) or t[0] in "-?":
            return '"%s"' % t.replace("\\", "\\\\").replace('"', '\\"')
        return t
    return "tags: [%s]\n" % ", ".join(_yaml(t) for t in temas)


def crear_carpeta_articulo(titulo, categoria, fecha, categorias, slug=None, temas=None):
    slug = slug or slug_de_titulo(titulo)
    if not slug:
        raise ErrorPanel(
            "Ese titulo no genera un nombre de archivo valido -- probá con "
            "letras o numeros."
        )

    slug_cat = slug_de_categoria(categoria, categorias)
    if slug_cat is None:
        raise ErrorPanel("La categoria «%s» no es ninguna de las categorías de _config.yml." % categoria)

    carpeta = os.path.join(RAIZ, "_posts", "articulos", slug)
    nombre_md = "%s-%s.md" % (fecha, slug)
    ruta_md = os.path.join(carpeta, nombre_md)
    if len(ruta_md) > LARGO_MAXIMO_RUTA:
        raise ErrorPanel(
            "La ruta del archivo quedaría de %d caracteres (máximo %d en este "
            "Windows): %s -- no se creó nada. Probá con un título más corto."
            % (len(ruta_md), LARGO_MAXIMO_RUTA, ruta_md)
        )
    if os.path.exists(ruta_md):
        raise ErrorPanel(
            "Ya existe %s -- no lo sobrescribo. No se creó nada." % ruta_git(ruta_md)
        )
    carpeta_ya_existia = os.path.isdir(carpeta)

    anio, mes, dia = fecha.split("-")
    permalink = "/%s/%s/%s/%s/%s.html" % (slug_cat, anio, mes, dia, slug)
    titulo_yaml = titulo.replace("\\", "\\\\").replace('"', '\\"')

    front_matter = (
        "---\n"
        'layout: post\n'
        'title: "%s"\n'
        "date: %s\n"
        "category: %s\n"
        'excerpt: "PENDIENTE -- completar con el resumen que entregue NotebookLM"\n'
        "image: PENDIENTE.jpg\n"
        # tags: opcional -- solo si se escribieron temas en el formulario, y
        # ya completo. Sin temas, el .md sale sin la linea (igual que los
        # articulos viejos): nada queda "pendiente" de algo que no se exige.
        "%s"
        "permalink: %s\n"
        "---\n"
    ) % (titulo_yaml, fecha, categoria, linea_tags(temas) if temas else "", permalink)

    try:
        os.makedirs(carpeta, exist_ok=True)
        with open(ruta_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(front_matter)
    except OSError as e:
        # No dejar una carpeta vacia a medias si la creamos nosotros ahora.
        if not carpeta_ya_existia and os.path.isdir(carpeta) and not os.listdir(carpeta):
            os.rmdir(carpeta)
        raise ErrorPanel(
            "No se pudo escribir el archivo %s (%s). No quedó nada creado a medias."
            % (ruta_md, e.strerror or e)
        )

    url_final = URL_SITIO + permalink
    return slug, carpeta, ruta_md, nombre_md, url_final


# --------------------------------------------------------------------------
# Flujo "Eliminar articulo publicado"
# --------------------------------------------------------------------------
def listar_articulos():
    carpeta_posts = os.path.join(RAIZ, "_posts")
    articulos = []
    for nombre in sorted(os.listdir(carpeta_posts)):
        ruta = os.path.join(carpeta_posts, nombre)
        if not nombre.endswith(".md") or not os.path.isfile(ruta):
            continue
        fm = leer_front_matter(ruta)
        if fm.get("hidden", "").strip().lower() == "true":
            # Banco de pruebas de kramdown/MathJax, no un articulo real.
            continue
        titulo = fm.get("title", nombre)
        if fm.get(NO_UTF8):
            titulo += " (aviso: %s)" % AVISO_NO_UTF8
        articulos.append({
            "archivo": nombre,
            "titulo": titulo,
            "fecha": fm.get("date", "?"),
            "categoria": fm.get("category", "?"),
        })
    return articulos


PATRON_ARCHIVO_POST = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$")


def posts_que_usan_carpeta_imagenes(slug, excepto):
    """Otros articulos de _posts/ que todavia referencian
    /assets/imagenes/<slug>/. Dos posts con distinta fecha pero el mismo slug
    comparten esa carpeta, asi que borrarla junto con uno de ellos deja al
    otro publicado con las imagenes rotas -- paso de verdad el 2026-09-22 y
    costo tres imagenes del articulo de fitorremediacion."""
    prefijo = "/assets/imagenes/%s/" % slug
    carpeta_posts = os.path.join(RAIZ, "_posts")
    en_uso = []
    for nombre in sorted(os.listdir(carpeta_posts)):
        if nombre == excepto or not nombre.endswith(".md"):
            continue
        ruta = os.path.join(carpeta_posts, nombre)
        if not os.path.isfile(ruta):
            continue
        with open(ruta, encoding="utf-8") as fh:
            if prefijo in fh.read():
                en_uso.append(nombre)
    return en_uso


def eliminar_articulo(nombre_archivo):
    if not PATRON_ARCHIVO_POST.match(nombre_archivo):
        raise ErrorPanel("Nombre de archivo invalido: %s" % nombre_archivo)

    ruta_md = os.path.join(RAIZ, "_posts", nombre_archivo)
    if not os.path.isfile(ruta_md):
        raise ErrorPanel("No encuentro «%s» en _posts/." % nombre_archivo)

    fm = leer_front_matter(ruta_md)
    titulo = fm.get("title", nombre_archivo)

    m = re.match(r"^\d{4}-\d{2}-\d{2}-(.+)\.md$", nombre_archivo)
    slug = m.group(1) if m else None
    carpeta_imagenes = os.path.join(RAIZ, "assets", "imagenes", slug) if slug else None
    borra_imagenes = bool(carpeta_imagenes and os.path.isdir(carpeta_imagenes))

    # Guard: la carpeta de imagenes solo se borra si NINGUN otro articulo
    # publicado la sigue usando. El .md de este articulo si se borra igual.
    compartida_con = posts_que_usan_carpeta_imagenes(slug, nombre_archivo) if borra_imagenes else []
    if compartida_con:
        borra_imagenes = False

    rutas_rm = [ruta_git(ruta_md)]
    if borra_imagenes:
        rutas_rm.append(ruta_git(carpeta_imagenes))

    resultado_rm = git("rm", "-r", "--", *rutas_rm)
    if resultado_rm.returncode != 0:
        raise ErrorPanel(
            "`git rm` fallo:\n%s" % (resultado_rm.stderr or resultado_rm.stdout)
        )

    mensaje = "Elimina articulo: %s" % titulo
    resultado_commit = git("commit", "-m", mensaje)
    if resultado_commit.returncode != 0:
        # Sin esto el git rm quedaba hecho a medias: archivos borrados del
        # disco y del indice, sin commit, y sin decir como volver atras.
        git("reset", "-q", "HEAD", "--", *rutas_rm)
        restaurado = git("checkout", "HEAD", "--", *rutas_rm).returncode == 0
        estado = (
            "No se borró nada: el artículo y sus imágenes quedaron restaurados como estaban."
            if restaurado else
            "ATENCIÓN: no pude restaurar los archivos solo. Para recuperarlos corré "
            "`git checkout HEAD -- %s`." % " ".join(rutas_rm)
        )
        raise ErrorPanel(
            "`git commit` falló, así que la eliminación se deshizo.\n%s\n\n%s"
            % (estado, resultado_commit.stderr or resultado_commit.stdout)
        )

    return titulo, mensaje, borra_imagenes, compartida_con


# --------------------------------------------------------------------------
# Flujo "Editar articulo publicado"
# --------------------------------------------------------------------------
def _slug_de_archivo_post(nombre_archivo):
    m = re.match(r"^\d{4}-\d{2}-\d{2}-(.+)\.md$", nombre_archivo)
    return m.group(1) if m else None


def carpeta_trabajo_existe(slug):
    return os.path.isdir(os.path.join(RAIZ, "_posts", "articulos", slug))


def _convertir_a_rutas_simples(texto, slug):
    """Inversa de lo que hace pa.procesar_referencias al publicar: el .md ya
    publicado en _posts/ tiene las rutas de imagen completas
    (/assets/imagenes/<slug>/archivo.ext, en <img>, en imagen Markdown y en
    el `image:` del front matter) -- la carpeta de trabajo espera nombres
    simples (archivo.ext), para que Publicar borrador / Vista previa en
    vivo puedan reescribirlas de nuevo al republicar. Reemplazo de texto
    simple (no regex): el prefijo es una cadena literal distintiva, no hace
    falta distinguir <img> de Markdown de front matter por separado."""
    return texto.replace("/assets/imagenes/%s/" % slug, "")


def crear_carpeta_edicion(nombre_archivo):
    """Copia un articulo YA PUBLICADO a una carpeta de trabajo nueva en
    _posts/articulos/<slug>/, con sus imagenes, para seguir editandolo con
    Vista previa en vivo / Publicar borrador. Nunca toca el articulo
    publicado -- eso solo pasa si Elvis despues confirma la republicacion
    desde Publicar borrador."""
    if not PATRON_ARCHIVO_POST.match(nombre_archivo):
        raise ErrorPanel("Nombre de archivo invalido: %s" % nombre_archivo)
    ruta_md_publicado = os.path.join(RAIZ, "_posts", nombre_archivo)
    if not os.path.isfile(ruta_md_publicado):
        raise ErrorPanel("No encuentro «%s» en _posts/." % nombre_archivo)

    slug = _slug_de_archivo_post(nombre_archivo)
    if not slug:
        raise ErrorPanel("No pude calcular el slug de «%s»." % nombre_archivo)

    carpeta_trabajo = os.path.join(RAIZ, "_posts", "articulos", slug)
    ruta_md_trabajo = os.path.join(carpeta_trabajo, nombre_archivo)

    try:
        with open(ruta_md_publicado, encoding="utf-8") as fh:
            texto = fh.read()
    except UnicodeDecodeError:
        raise ErrorPanel("No puedo abrir «%s» para editarlo: %s." % (nombre_archivo, AVISO_NO_UTF8))
    texto = _convertir_a_rutas_simples(texto, slug)

    carpeta_imagenes_publicadas = os.path.join(RAIZ, "assets", "imagenes", slug)
    imagenes = []
    if os.path.isdir(carpeta_imagenes_publicadas):
        imagenes = [
            n for n in sorted(os.listdir(carpeta_imagenes_publicadas))
            if os.path.isfile(os.path.join(carpeta_imagenes_publicadas, n))
            and os.path.splitext(n)[1].lower() in pa.EXTENSIONES_IMAGEN
        ]

    # La carpeta de trabajo repite el slug (carpeta + nombre del .md), asi
    # que su ruta es mas larga que la del publicado. Limite real de Windows,
    # no el de Crear: con 240, el articulo del mercado de carbono (252) ya
    # no se podria editar.
    mas_larga = max([ruta_md_trabajo] + [os.path.join(carpeta_trabajo, n) for n in imagenes], key=len)
    if len(mas_larga) > LARGO_MAXIMO_RUTA_WINDOWS:
        raise ErrorPanel(
            "No puedo armar la carpeta de trabajo: la ruta %s quedaría de %d "
            "caracteres y este Windows corta en %d. No se creó nada y el "
            "artículo publicado no se tocó. Para editarlo desde el panel hay que "
            "activar las rutas largas de Windows (LongPathsEnabled); si no, "
            "editá el .md directamente en _posts/."
            % (ruta_git(mas_larga), len(mas_larga), LARGO_MAXIMO_RUTA_WINDOWS)
        )

    carpeta_ya_existia = os.path.isdir(carpeta_trabajo)
    try:
        os.makedirs(carpeta_trabajo, exist_ok=True)
        with open(ruta_md_trabajo, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texto)
        for nombre in imagenes:
            shutil.copyfile(os.path.join(carpeta_imagenes_publicadas, nombre),
                            os.path.join(carpeta_trabajo, nombre))
    except OSError as e:
        # Una carpeta a medio armar despues se confunde con "cambios sin
        # publicar" en el aviso de conflicto. Si la creamos recien, se va.
        if not carpeta_ya_existia:
            shutil.rmtree(carpeta_trabajo, ignore_errors=True)
        raise ErrorPanel(
            "No se pudo armar la carpeta de trabajo (%s: %s). Se borró lo que "
            "había alcanzado a crearse; el artículo publicado no se tocó. Si una "
            "imagen está abierta en otro programa, cerralo y volvé a intentar."
            % (type(e).__name__, e.strerror or e)
        )

    return slug, carpeta_trabajo, ruta_md_trabajo, imagenes


def reiniciar_carpeta_edicion(nombre_archivo):
    """Descarta lo que hubiera en la carpeta de trabajo (cambios sin
    publicar) y la recrea de cero a partir del articulo publicado --
    solo se llama cuando Elvis elige explicitamente "Reiniciar desde lo
    publicado" en la pantalla de aviso, nunca en silencio."""
    slug = _slug_de_archivo_post(nombre_archivo)
    if not slug:
        raise ErrorPanel("No pude calcular el slug de «%s»." % nombre_archivo)
    carpeta_trabajo = os.path.join(RAIZ, "_posts", "articulos", slug)
    if os.path.isdir(carpeta_trabajo):
        # Primero un rename, que es atomico: si algo de adentro esta abierto
        # en otro programa, Windows lo rechaza entero y no se borra nada. Un
        # rmtree directo borraba hasta el archivo bloqueado y dejaba la
        # carpeta a medias. Nombre corto a proposito (rutas largas).
        descarte = os.path.join(RAIZ, "_posts", "articulos", ".descarte-%d" % (time.time_ns() % 10**9))
        try:
            os.rename(carpeta_trabajo, descarte)
        except OSError as e:
            raise ErrorPanel(
                "No pude reiniciar la carpeta de trabajo: algún archivo de adentro "
                "está en uso (%s). Cerrá el programa que lo tenga abierto y volvé a "
                "intentar. No se borró nada." % (e.strerror or e)
            )
        shutil.rmtree(descarte, ignore_errors=True)
    return crear_carpeta_edicion(nombre_archivo)


# --------------------------------------------------------------------------
# Flujo "Publicar borrador"
# --------------------------------------------------------------------------
def listar_borradores():
    base = os.path.join(RAIZ, "_posts", "articulos")
    if not os.path.isdir(base):
        return []
    borradores = []
    for nombre in sorted(os.listdir(base)):
        carpeta = os.path.join(base, nombre)
        if not os.path.isdir(carpeta) or nombre.startswith("."):
            continue  # .descarte-*: resto de un "Reiniciar", no un borrador
        mds = [f for f in os.listdir(carpeta) if f.endswith(".md")]
        problema = None
        if len(mds) == 1:
            fm = leer_front_matter(os.path.join(carpeta, mds[0]))
            titulo = fm.get("title", nombre)
            mtime = os.path.getmtime(os.path.join(carpeta, mds[0]))
            if fm.get(NO_UTF8):
                problema = AVISO_NO_UTF8
        else:
            titulo = nombre
            mtime = os.path.getmtime(carpeta)
            problema = (
                "esta carpeta no tiene ningun archivo .md" if not mds
                else "esta carpeta tiene mas de un archivo .md (%s)" % ", ".join(mds)
            )
        borradores.append({
            "carpeta": nombre,
            "titulo": titulo,
            "modificado": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
            "problema": problema,
        })
    borradores.sort(key=lambda b: b["modificado"], reverse=True)
    return borradores


def revisar_y_copiar_borrador(nombre_carpeta):
    """Reusa las funciones de publicar_articulo.py -- mismas validaciones
    todo-o-nada, mismo chequeo de PENDIENTE -- pero se queda ahi: copia el
    .md y las imagenes al working tree sin git add ni commit, para que la
    vista previa se arme sobre archivos reales sin publicar nada todavia."""
    carpeta_abs = os.path.join(RAIZ, "_posts", "articulos", nombre_carpeta)
    carpeta, nombre_validado = pa.resolver_carpeta(carpeta_abs)
    nombre_md = pa.encontrar_md(carpeta, nombre_validado)
    imagenes = pa.encontrar_imagenes(carpeta, nombre_validado)

    alinear_permalink_en_disco(os.path.join(carpeta, nombre_md))
    with open(os.path.join(carpeta, nombre_md), encoding="utf-8") as fh:
        texto, _ = alinear_permalink(fh.read())

    texto = pa.quitar_tags_pendientes(texto)
    pa.verificar_sin_pendientes(texto, nombre_validado)

    texto_final, _cambios, _referenciadas = pa.procesar_referencias(
        texto, nombre_validado, set(imagenes)
    )
    texto_final = pa.enriquecer_imagenes(texto_final, carpeta)

    # Sincronizar con origin ANTES de escribir nada: aca el arbol de trabajo
    # todavia esta limpio, que es lo que `git rebase` necesita para arrancar.
    error_sync = pa.sincronizar_con_remoto()
    if error_sync:
        raise ErrorPanel(error_sync)

    # Y recien despues pisar el .md publicado, poniendo a salvo cualquier
    # cambio sin comitear que tuviera.
    respaldo = proteger_articulo_publicado(nombre_md)

    tocados = []
    try:
        destino_md, _ya_existia, destino_imagenes, copiadas = _copiar_registrando(
            carpeta, nombre_validado, nombre_md, imagenes, texto_final, tocados
        )
    except Exception as e:
        raise ErrorPanel(_mensaje_copia_fallida(e, *deshacer_copia_parcial(tocados, nombre_validado)))
    return nombre_validado, nombre_md, destino_md, destino_imagenes, copiadas, respaldo


def validar_borrador(ruta_md_copiada, nombre_carpeta, copiadas):
    """Corre validar_articulos.py sobre el articulo recien copiado (mismas
    reglas que el workflow de GitHub Actions) y, aparte, el chequeo de peso
    solo de las imagenes de este articulo -- no de assets/ entero, para no
    mezclar avisos preexistentes de otros articulos en esta vista previa."""
    va.errores.clear()
    va.avisos.clear()
    categorias = va.categorias_validas()
    va.validar_post(ruta_md_copiada, categorias)

    carpeta_imagenes = os.path.join(RAIZ, "assets", "imagenes", nombre_carpeta)
    for imagen in copiadas:
        ruta = os.path.join(carpeta_imagenes, imagen)
        if not os.path.isfile(ruta):
            continue
        kb = os.path.getsize(ruta) / 1024.0
        rel = ruta_git(ruta)
        if kb > va.ERROR_KB:
            va.error(rel, 0, "la imagen pesa %.0f KB. Arriba de %d KB hay que "
                              "redimensionarla antes de subirla." % (kb, va.ERROR_KB))
        elif kb > va.AVISO_KB:
            va.aviso(rel, 0, "la imagen pesa %.0f KB; conviene bajarla de %d KB."
                              % (kb, va.AVISO_KB))

    return list(va.errores), list(va.avisos)


def construir_sitio():
    """Devuelve (resultado_subprocess, mensaje_error). mensaje_error solo se
    llena si `bundle` ni siquiera esta instalado -- el fallo real de Jekyll
    (returncode != 0) se maneja aparte, con la salida de resultado.

    shutil.which() (no pasar "bundle" tal cual a subprocess.run): en Windows
    `bundle` es un shim `bundle.BAT` de RubyInstaller, y CreateProcess no
    resuelve extensiones de PATHEXT sin pasar por una shell -- subprocess.run
    con la lista ["bundle", ...] tira FileNotFoundError aunque `bundle`
    funcione perfecto a mano en la terminal. Confirmado en el clon aislado."""
    ejecutable = shutil.which("bundle")
    if not ejecutable:
        return None, (
            "No encontré `bundle` instalado -- hace falta Ruby + Bundler para "
            "armar la vista previa real. Instalalos y corré `bundle install` "
            "una vez en la raíz del repo, o publicá desde la terminal con "
            "`python .github/scripts/publicar_articulo.py _posts/articulos/<carpeta>`."
        )
    resultado = subprocess.run(
        [ejecutable, "exec", "jekyll", "build"], cwd=RAIZ,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return resultado, None


def ruta_generada_en_site(fm, nombre_carpeta):
    """A partir del front matter ya copiado, calcula la ruta relativa dentro
    de _site/ donde Jekyll va a dejar el HTML del articulo -- para apuntar
    el iframe de la vista previa ahi. Prioriza el `permalink:` explicito
    (lo que escribe "Crear articulo nuevo"); si no hay, replica la regla por
    defecto de Jekyll (ver la nota sobre categorias compuestas mas arriba)."""
    permalink = (fm.get("permalink") or "").strip()
    if permalink:
        ruta = permalink.lstrip("/")
        return ruta or "index.html"
    fecha = (fm.get("date") or "").split()[0]
    if not fecha or fecha.count("-") != 2:
        return None
    anio, mes, dia = fecha.split("-")
    categoria = (fm.get("category") or "").lower()
    return "%s/%s/%s/%s/%s.html" % (categoria, anio, mes, dia, nombre_carpeta)


def _revertir_o_borrar(ruta_absoluta):
    """Deshace UNA copia de vista previa. Si el archivo ya estaba trackeado en
    git (una republicacion sobre un articulo existente), restaura su version
    comiteada; si es nuevo (nunca se hizo git add), lo borra.

    Solo hace eso con archivos que este proceso escribio (registrar_copia).
    Con cualquier otro no arriesga: si tiene cambios sin comitear los guarda
    en un stash, y si no los tiene lo deja como esta. Antes hacia
    `git checkout --` a ciegas, que destruia en silencio cualquier edicion sin
    comitear que hubiera en ese .md publicado.

    Devuelve la etiqueta del stash si tuvo que respaldar algo, o None."""
    if not os.path.isfile(ruta_absoluta):
        return None
    if not es_copia_del_panel(ruta_absoluta):
        return respaldar_en_stash(
            ruta_absoluta, "cambios sin comitear guardados en vez de descartados"
        )
    rel = ruta_git(ruta_absoluta)
    resultado = git("ls-files", "--error-unmatch", "--", rel)
    if resultado.returncode == 0:
        git("checkout", "--", rel)
    else:
        os.remove(ruta_absoluta)
    _copias_del_panel.discard(_clave_ruta(ruta_absoluta))
    return None


def descartar_vista_previa(nombre_carpeta, nombre_md, copiadas):
    """Devuelve la lista de stashes que hubo que crear para no perder nada
    (normalmente vacia)."""
    respaldos = []
    if nombre_md:
        etiqueta = _revertir_o_borrar(os.path.join(RAIZ, "_posts", nombre_md))
        if etiqueta:
            respaldos.append(etiqueta)
    carpeta_imagenes = os.path.join(RAIZ, "assets", "imagenes", nombre_carpeta)
    for imagen in copiadas:
        etiqueta = _revertir_o_borrar(os.path.join(carpeta_imagenes, imagen))
        if etiqueta:
            respaldos.append(etiqueta)
    if os.path.isdir(carpeta_imagenes) and not os.listdir(carpeta_imagenes):
        os.rmdir(carpeta_imagenes)
    return respaldos


def _es_md_de_posts(ruta_absoluta):
    return (os.path.normcase(os.path.dirname(ruta_absoluta))
            == os.path.normcase(os.path.join(RAIZ, "_posts")))


def _imagenes_de(tocados):
    return [os.path.basename(r) for r in tocados if not _es_md_de_posts(r)]


def _copiar_registrando(carpeta, nombre_carpeta, nombre_md, imagenes, texto_final, tocados):
    """pa.copiar_articulo registrando cada archivo en el momento en que queda
    escrito, no al final: antes, si una imagen fallaba a mitad de la copia, el
    .md y las imagenes anteriores quedaban en el repo sin registrar -- sin
    boton para descartarlas, y un descarte posterior las mandaba a un stash
    en vez de revertirlas. `tocados` se llena aunque la copia falle."""
    def al_escribir(ruta):
        registrar_copia(ruta)
        if ruta not in tocados:
            tocados.append(ruta)
    return pa.copiar_articulo(
        carpeta, nombre_carpeta, nombre_md, imagenes, texto_final, al_escribir=al_escribir
    )


def deshacer_copia_parcial(tocados, nombre_carpeta):
    """Deshace una copia que fallo a mitad (misma logica que "Volver a
    editar", archivo por archivo). Devuelve (stashes creados, archivos que
    no se pudieron deshacer) -- sigue con los demas aunque uno falle."""
    respaldos, fallidos = [], []
    for ruta in tocados:
        try:
            etiqueta = _revertir_o_borrar(ruta)
            if etiqueta:
                respaldos.append(etiqueta)
        except Exception as e:
            fallidos.append("%s (%s)" % (ruta_git(ruta), e))
    carpeta_imagenes = os.path.join(RAIZ, "assets", "imagenes", nombre_carpeta)
    try:
        if os.path.isdir(carpeta_imagenes) and not os.listdir(carpeta_imagenes):
            os.rmdir(carpeta_imagenes)
    except OSError:
        pass
    return respaldos, fallidos


def _mensaje_fallo_tras_copia(error, descartar):
    """Para un fallo inesperado DESPUES de una copia completa (build,
    validador, arranque de jekyll serve): descarta la copia con `descartar`
    (devuelve la lista de stashes) y arma el mensaje para la pantalla."""
    mensaje = "%s: %s -- el detalle completo quedó en la consola del panel." % (
        type(error).__name__, error)
    try:
        respaldos = descartar()
    except Exception as e:
        traceback.print_exc()
        return mensaje + ("\n\nTampoco pude descartar la copia al sitio (%s): revisá "
                          "`git status` antes de seguir." % e)
    mensaje += "\n\nSe descartó la copia al sitio; tu carpeta de trabajo no se tocó."
    if respaldos:
        mensaje += (" Había cambios sin comitear en el artículo publicado: quedaron "
                    "guardados en %s (`git stash list` / `git stash pop`)." % ", ".join(respaldos))
    return mensaje


def _mensaje_copia_fallida(error, respaldos, fallidos):
    detalle = getattr(error, "strerror", None) or error
    mensaje = ("La copia al sitio falló a mitad de camino (%s: %s). Se deshizo lo "
               "que alcanzó a copiarse; tu carpeta de trabajo no se tocó. Si una "
               "imagen está abierta en otro programa, cerralo y volvé a intentar."
               % (type(error).__name__, detalle))
    if respaldos:
        mensaje += ("\n\nHabía cambios sin comitear en el artículo publicado: quedaron "
                    "guardados en %s (recuperalos con `git stash list` / `git stash pop`)."
                    % ", ".join(respaldos))
    if fallidos:
        mensaje += ("\n\nNo pude deshacer estos archivos, revisalos a mano con "
                    "`git status`: %s" % "; ".join(fallidos))
    return mensaje


def url_actions():
    resultado = git("remote", "get-url", "origin")
    if resultado.returncode != 0:
        return None
    m = re.match(
        r'^(?:https://github\.com/|git@github\.com:)([^/]+)/(.+?)(?:\.git)?$',
        resultado.stdout.strip(),
    )
    if not m:
        return None
    return "https://github.com/%s/%s/actions" % (m.group(1), m.group(2))


def iniciar_servidor_vista_previa():
    os.makedirs(SITE_DIR, exist_ok=True)

    class ManejadorVistaPrevia(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=SITE_DIR, **kwargs)

        def log_message(self, formato, *args):
            pass

    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", PUERTO_VISTA_PREVIA), ManejadorVistaPrevia)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


# --------------------------------------------------------------------------
# Flujo "Vista previa en vivo"
# --------------------------------------------------------------------------
PATRON_MARCADOR_IMAGEN = re.compile(r'\[IMAGEN\s+\d+[^\]]*\]')

PLACEHOLDER_IMAGEN_PENDIENTE = (
    '<div style="background:#e2e0d8;border:1px dashed #a9a696;border-radius:8px;'
    'padding:40px 20px;text-align:center;color:#6b6a63;font-family:sans-serif;">'
    'Imagen pendiente</div>'
)


def _encontrar_imagenes_vivo(carpeta):
    """Version tolerante de pa.encontrar_imagenes: a diferencia de Publicar
    borrador, Vista previa en vivo no debe bloquear porque la carpeta de
    trabajo todavia no tiene ninguna imagen -- el proposito de este flujo es
    justo ir viendo el progreso (texto, formulas, estructura) mientras se
    escribe, no exigir que el articulo este terminado. Devuelve una lista
    vacia en vez de fallar."""
    return sorted(
        f for f in os.listdir(carpeta)
        if os.path.splitext(f)[1].lower() in pa.EXTENSIONES_IMAGEN
    )


def _es_referencia_simple_faltante(ref, imagenes_disponibles):
    if ref.startswith(("http://", "https://", "//")):
        return False
    if "/" in ref or "\\" in ref:
        return False
    return ref not in imagenes_disponibles


def _reemplazar_imagenes_faltantes(texto, imagenes_disponibles):
    """Reemplaza, SOLO en la copia en memoria usada para renderizar (nunca
    en el .md real de la carpeta de trabajo), cada marcador
    `[IMAGEN N -- titulo]` sin resolver y cada <img>/imagen Markdown que
    apunte a un archivo simple que todavia no esta en la carpeta, por un
    recuadro "Imagen pendiente" -- asi el resto del articulo (texto,
    formulas, estructura) se sigue viendo aunque falten imagenes, en vez de
    que pa.procesar_referencias corte la vista previa entera con un error
    (ese chequeo estricto sigue intacto para "Publicar borrador", que si
    debe bloquear por una imagen faltante)."""
    texto = PATRON_MARCADOR_IMAGEN.sub(PLACEHOLDER_IMAGEN_PENDIENTE, texto)

    def _sub_img(m):
        ref = m.group(2)
        if _es_referencia_simple_faltante(ref, imagenes_disponibles):
            return PLACEHOLDER_IMAGEN_PENDIENTE
        return m.group(0)

    texto = pa.PATRON_IMG_TAG.sub(_sub_img, texto)
    texto = pa.PATRON_MD_IMG.sub(_sub_img, texto)
    return texto


def _neutralizar_image_pendiente(texto, imagenes_disponibles):
    """El scaffold de "Crear articulo nuevo" deja `image: PENDIENTE.jpg` en
    el front matter hasta que Elvis pega el nombre real que entrega
    NotebookLM. Ese campo solo alimenta metadatos (og:image, etc.) -- nunca
    se ve en el cuerpo del articulo -- asi que no tiene sentido que bloquee
    la vista previa en vivo por un campo a medio completar (a diferencia de
    un <img> roto en el cuerpo, que si es una senal real de que falta subir
    esa imagen y debe seguir fallando). Reescribe SOLO la copia en memoria
    que se usa para renderizar -- el .md real de la carpeta de trabajo no se
    toca -- a una ruta ya armada, para que pa.procesar_referencias (sin
    tocarlo) la deje pasar por su propia rama tolerante en vez de fallar."""
    m = re.search(r'^image:\s*(\S+)\s*$', texto, re.M)
    if not m:
        return texto
    valor = m.group(1)
    if valor.startswith(("http://", "https://", "//", "/")) or valor in imagenes_disponibles:
        return texto
    return re.sub(
        r'^image:\s*\S+\s*$', "image: /assets/pendiente-vista-previa.jpg", texto, count=1, flags=re.M
    )


def copiar_para_vista_previa(nombre_carpeta, tocados=None, deshacer_si_falla=True):
    """Igual que revisar_y_copiar_borrador, pero SIN pa.verificar_sin_pendientes
    -- este flujo es solo para mirar mientras se escribe, tiene que funcionar
    con campos a medio completar. Reusa pa.copiar_articulo (la funcion real
    de copiado), no la reescribe.

    deshacer_si_falla=False es para el hilo de vigilancia: con la vista previa
    ya andando no se deshace nada, el hilo suma a su lista lo que quedo en
    `tocados` para que "Detener vista previa" lo limpie despues."""
    if tocados is None:
        tocados = []
    carpeta_abs = os.path.join(RAIZ, "_posts", "articulos", nombre_carpeta)
    carpeta, nombre_validado = pa.resolver_carpeta(carpeta_abs)
    nombre_md = pa.encontrar_md(carpeta, nombre_validado)
    imagenes = _encontrar_imagenes_vivo(carpeta)

    alinear_permalink_en_disco(os.path.join(carpeta, nombre_md))
    with open(os.path.join(carpeta, nombre_md), encoding="utf-8") as fh:
        texto, _ = alinear_permalink(fh.read())

    texto = pa.quitar_tags_pendientes(texto)
    texto = _neutralizar_image_pendiente(texto, set(imagenes))
    texto = _reemplazar_imagenes_faltantes(texto, set(imagenes))

    texto_final, _cambios, _referenciadas = pa.procesar_referencias(
        texto, nombre_validado, set(imagenes)
    )
    texto_final = pa.enriquecer_imagenes(texto_final, carpeta)

    # Mismo cuidado que en Publicar borrador: no pisar cambios sin comitear
    # del articulo publicado. En los ciclos siguientes del hilo de vigilancia
    # el archivo ya es una copia nuestra, asi que esto no vuelve a hacer nada.
    respaldo = proteger_articulo_publicado(nombre_md)

    try:
        destino_md, _ya_existia, destino_imagenes, copiadas = _copiar_registrando(
            carpeta, nombre_validado, nombre_md, imagenes, texto_final, tocados
        )
    except Exception as e:
        if not deshacer_si_falla:
            raise
        raise ErrorPanel(_mensaje_copia_fallida(e, *deshacer_copia_parcial(tocados, nombre_validado)))
    return nombre_validado, nombre_md, destino_md, destino_imagenes, copiadas, respaldo


class _EstadoVistaPrevia:
    """Estado de la (unica) vista previa en vivo activa. Solo una a la vez:
    arrancar una segunda primero detiene y descarta la anterior."""
    def __init__(self):
        self.carpeta = None
        self.nombre_md = None
        self.copiadas = []
        self.ruta_site = None
        self.evento_detener = None
        self.hilo = None
        self.ultimo_error = None


_vista_previa_activa = _EstadoVistaPrevia()
_proceso_jekyll_serve = None
_lock_jekyll_serve = threading.Lock()


def jekyll_serve_activo():
    return _proceso_jekyll_serve is not None and _proceso_jekyll_serve.poll() is None


def iniciar_jekyll_serve():
    """Arranca `bundle exec jekyll serve --livereload` en segundo plano si no
    hay uno ya corriendo (se reusa entre vistas previas sucesivas). Devuelve
    un mensaje de error, o None si ya estaba corriendo o si lo pudo arrancar.
    Mismo motivo que construir_sitio(): shutil.which("bundle"), no la lista
    ["bundle", ...] tal cual, por el shim .BAT de RubyInstaller en Windows."""
    global _proceso_jekyll_serve
    with _lock_jekyll_serve:
        if jekyll_serve_activo():
            return None
        ejecutable = shutil.which("bundle")
        if not ejecutable:
            return (
                "No encontré `bundle` instalado -- hace falta Ruby + Bundler "
                "para la vista previa en vivo. Instalalos y corré `bundle "
                "install` una vez en la raíz del repo."
            )
        _proceso_jekyll_serve = subprocess.Popen(
            [ejecutable, "exec", "jekyll", "serve", "--livereload",
             "--port", str(PUERTO_SERVE_VIVO)],
            cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return None


def esperar_jekyll_listo(tiempo_maximo=60):
    """Espera a que el servidor de jekyll serve responda -- el primer build
    real tarda unos segundos. Devuelve False si se cae o si se agota el
    tiempo (por ejemplo, un error de sintaxis que rompe el build)."""
    limite = time.time() + tiempo_maximo
    url = "http://127.0.0.1:%d/" % PUERTO_SERVE_VIVO
    while time.time() < limite:
        if not jekyll_serve_activo():
            return False
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    return False


def _huella_carpeta(carpeta):
    """mtime de cada archivo de la carpeta de trabajo -- alcanza para
    detectar ediciones del .md y altas/bajas/cambios de imagenes, sin
    dependencias nuevas (solo os.path.getmtime)."""
    huella = {}
    for nombre in os.listdir(carpeta):
        ruta = os.path.join(carpeta, nombre)
        if os.path.isfile(ruta):
            huella[nombre] = os.path.getmtime(ruta)
    return huella


def _bucle_vigilancia(nombre_carpeta, evento_detener):
    carpeta_trabajo = os.path.join(RAIZ, "_posts", "articulos", nombre_carpeta)
    huella_anterior = None
    while not evento_detener.wait(1.5):
        try:
            huella_actual = _huella_carpeta(carpeta_trabajo)
        except OSError:
            continue
        if huella_actual == huella_anterior:
            continue
        tocados = []
        try:
            _, _, destino_md, _, copiadas, _respaldo = copiar_para_vista_previa(
                nombre_carpeta, tocados, deshacer_si_falla=False
            )
        except Exception as e:
            # Cualquier excepcion, no solo las previstas: antes un OSError
            # (imagen bloqueada o a medio guardar) mataba el hilo sin aviso y
            # la vista previa dejaba de actualizarse en silencio.
            # No actualiza huella_anterior: reintenta en el proximo tick
            # aunque el archivo no vuelva a cambiar (ej. quedo a medio
            # guardar cuando se leyo). Lo que alcanzo a copiarse se suma a la
            # lista, para que "Detener vista previa" tambien lo limpie.
            _vista_previa_activa.copiadas = sorted(
                set(_vista_previa_activa.copiadas) | set(_imagenes_de(tocados))
            )
            if isinstance(e, (ErrorPanel, pa.ErrorPublicacion)):
                _vista_previa_activa.ultimo_error = str(e)
            else:
                traceback.print_exc()
                _vista_previa_activa.ultimo_error = "%s: %s -- se reintenta sola en unos segundos." % (
                    type(e).__name__, e)
            continue
        huella_anterior = huella_actual
        _vista_previa_activa.ultimo_error = None
        # Si cambio la categoria (y con ella el permalink), la pagina generada
        # cambia de ruta: /vivo/estado se lo avisa al iframe.
        _vista_previa_activa.ruta_site = ruta_generada_en_site(
            leer_front_matter(destino_md), nombre_carpeta)
        # Union con lo ya copiado, no reemplazo: si una imagen nueva aparece
        # a mitad de sesion, "Detener vista previa" tiene que poder
        # descartarla tambien (descartar_vista_previa solo revisa lo que
        # esta en esta lista).
        _vista_previa_activa.copiadas = sorted(set(_vista_previa_activa.copiadas) | set(copiadas))


def _detener_vista_previa_activa():
    """Corta la vigilancia y descarta la copia (misma logica de "Volver a
    editar" de Publicar borrador, via descartar_vista_previa). No toca
    `bundle exec jekyll serve`: se deja corriendo para reusar en la proxima
    vista previa. Devuelve el nombre de la carpeta que estaba activa."""
    if not _vista_previa_activa.carpeta:
        return None, []
    if _vista_previa_activa.evento_detener:
        _vista_previa_activa.evento_detener.set()
    if _vista_previa_activa.hilo:
        _vista_previa_activa.hilo.join(timeout=3)
    carpeta = _vista_previa_activa.carpeta
    respaldos = descartar_vista_previa(
        _vista_previa_activa.carpeta, _vista_previa_activa.nombre_md, _vista_previa_activa.copiadas
    )
    _vista_previa_activa.carpeta = None
    _vista_previa_activa.nombre_md = None
    _vista_previa_activa.copiadas = []
    _vista_previa_activa.ruta_site = None
    _vista_previa_activa.evento_detener = None
    _vista_previa_activa.hilo = None
    _vista_previa_activa.ultimo_error = None
    return carpeta, respaldos


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------
CSS = """
<style>
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    max-width: 760px; margin: 0 auto; padding: 32px 20px 60px;
    background: #f6f5f2; color: #2b2b28;
  }
  h1 { font-size: 1.5rem; margin-bottom: 4px; }
  h2 { font-size: 1.2rem; margin-top: 0; }
  .subtitulo { color: #6b6a63; margin-top: 0; margin-bottom: 28px; }
  .tarjeta {
    background: #fff; border: 1px solid #e2e0d8; border-radius: 10px;
    padding: 24px; margin-bottom: 20px;
  }
  .botones-principales { display: flex; gap: 16px; flex-wrap: wrap; }
  .boton-grande {
    flex: 1; min-width: 220px; text-align: center; padding: 28px 16px;
    border-radius: 10px; text-decoration: none; font-size: 1.1rem;
    font-weight: 600; border: 1px solid #d8d5c8;
  }
  .boton-crear { background: #eaf3ec; color: #205b34; }
  .boton-publicar { background: #e8eef6; color: #1f3f6b; }
  .boton-vivo { background: #f3ecf6; color: #4d1f6b; }
  .boton-gestionar { background: #fdf3d9; color: #7a5a10; }
  label { display: block; margin: 16px 0 6px; font-weight: 600; }
  input[type=text], input[type=date], select {
    width: 100%; padding: 10px; font-size: 1rem;
    border: 1px solid #cbc8bc; border-radius: 6px; background: #fff;
  }
  button, .boton {
    display: inline-block; margin-top: 20px; padding: 10px 20px;
    border-radius: 6px; border: none; background: #2b6b45; color: #fff;
    font-size: 1rem; cursor: pointer; text-decoration: none;
  }
  button.boton-peligro { background: #a13b2b; }
  button.boton-secundario, .boton.boton-secundario { background: #8a887e; }
  .aviso {
    background: #fdf3d9; border: 1px solid #e6c568; border-radius: 8px;
    padding: 16px; margin: 16px 0; white-space: pre-wrap;
  }
  .error {
    background: #fbe4e0; border: 1px solid #d98f7f; border-radius: 8px;
    padding: 16px; margin: 16px 0; white-space: pre-wrap;
  }
  .exito {
    background: #e6f2e9; border: 1px solid #8fc79f; border-radius: 8px;
    padding: 16px; margin: 16px 0; white-space: pre-wrap;
  }
  code, .ruta { background: #efeee7; padding: 2px 6px; border-radius: 4px; }
  .vista-previa-frame {
    width: 100%; height: 70vh; border: 1px solid #cbc8bc; border-radius: 8px;
    background: #fff; margin: 16px 0; display: block;
  }
  .form-en-linea { display: inline-block; margin-right: 12px; }
  .lista-articulos { list-style: none; padding: 0; }
  .lista-articulos li {
    display: flex; justify-content: space-between; align-items: center;
    gap: 12px; padding: 12px 0; border-bottom: 1px solid #eceae1;
  }
  .lista-articulos li:last-child { border-bottom: none; }
  .meta { color: #6b6a63; font-size: 0.9rem; }
  .volver { display: inline-block; margin-top: 20px; color: #4a4940; }

  /* "Gestionar artículos": buscador + tabla ordenable */
  .buscador-articulos {
    width: 100%; padding: 12px 14px; font-size: 1rem; margin-bottom: 16px;
    border: 1px solid #cbc8bc; border-radius: 6px; background: #fff;
  }
  .tabla-articulos { width: 100%; border-collapse: collapse; }
  .tabla-articulos th {
    text-align: left; padding: 10px 8px; border-bottom: 2px solid #d8d5c8;
    font-size: 0.85rem; color: #4a4940; white-space: nowrap;
  }
  .tabla-articulos th.ordenable { cursor: pointer; user-select: none; }
  .tabla-articulos th.ordenable:hover { color: #2b6b45; }
  .tabla-articulos th .flecha { color: #2b6b45; margin-left: 4px; }
  .tabla-articulos td {
    padding: 10px 8px; border-bottom: 1px solid #eceae1; vertical-align: middle;
  }
  .tabla-articulos td.col-titulo { max-width: 320px; }
  .tabla-articulos .acciones { white-space: nowrap; text-align: right; }
  .tabla-articulos .acciones form { display: inline-block; margin: 0 0 0 6px; }
  .boton-mini {
    margin-top: 0; padding: 6px 12px; font-size: 0.85rem;
  }
  .sin-resultados { padding: 20px 8px; color: #6b6a63; }
  .pie-tabla { text-align: center; margin-top: 16px; }
</style>
"""


def pagina(titulo, cuerpo):
    return (
        "<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\">"
        "<title>%s -- Panel de control Git_Page</title>%s</head><body>%s</body></html>"
    ) % (html.escape(titulo), CSS, cuerpo)


def pagina_principal():
    cuerpo = """
    <h1>Panel de control -- Git_Page</h1>
    <p class="subtitulo">Crear, publicar o eliminar artículos, sin editor web ni terminal.</p>
    <div class="botones-principales">
      <a class="boton-grande boton-crear" href="/crear">Crear artículo nuevo</a>
      <a class="boton-grande boton-publicar" href="/publicar">Publicar borrador</a>
      <a class="boton-grande boton-gestionar" href="/gestionar">Gestionar artículos</a>
    </div>
    """
    return pagina("Panel de control", cuerpo)


def formulario_crear(categorias, valores=None, error=None):
    valores = valores or {}
    hoy = date.today().isoformat()
    opciones = "\n".join(
        '<option value="%s"%s>%s</option>' % (
            html.escape(c["name"]),
            " selected" if valores.get("categoria") == c["name"] else "",
            html.escape(c["name"]),
        )
        for c in categorias
    )
    bloque_error = ('<div class="error">%s</div>' % html.escape(error)) if error else ""
    cuerpo = """
    <h1>Crear artículo nuevo</h1>
    %s
    <div class="tarjeta">
      <form method="post" action="/crear">
        <label for="titulo">Título del artículo</label>
        <input type="text" id="titulo" name="titulo" value="%s" required autofocus>

        <label for="categoria">Categoría</label>
        <select id="categoria" name="categoria" required>%s</select>

        <label for="fecha">Fecha</label>
        <input type="date" id="fecha" name="fecha" value="%s" required>

        <label for="temas">Temas relacionados (opcional)</label>
        <input type="text" id="temas" name="temas" value="%s"
               placeholder="Ej.: Fitorremediación, Suelos" aria-describedby="temas-ayuda">
        <p class="meta" id="temas-ayuda">Una o varias palabras separadas por coma. Los artículos
           que comparten un tema se muestran en "Sugeridos" aunque sean de otra categoría.
           Si lo dejás vacío, el artículo no lleva tema y no queda nada pendiente.</p>

        <button type="submit">Crear carpeta del artículo</button>
      </form>
    </div>
    <a class="volver" href="/">&larr; Volver</a>
    """ % (
        bloque_error,
        html.escape(valores.get("titulo", "")),
        opciones,
        html.escape(valores.get("fecha") or hoy),
        html.escape(valores.get("temas", "")),
    )
    return pagina("Crear artículo nuevo", cuerpo)


def pagina_duplicado(valores, duplicado, slug_alternativo):
    cuerpo = """
    <h1>Ya existe un artículo con este nombre</h1>
    <div class="aviso">
      <p><strong>%s</strong> (%s)</p>
      <p>Encontrado en: %s</p>
      <p>¿Continuar de todas formas? El existente no se toca: el nuevo se crea
         con el nombre <code>%s</code>, en su propia carpeta.</p>
    </div>
    <form method="post" action="/crear">
      <input type="hidden" name="titulo" value="%s">
      <input type="hidden" name="categoria" value="%s">
      <input type="hidden" name="fecha" value="%s">
      <input type="hidden" name="temas" value="%s">
      <input type="hidden" name="confirmar" value="1">
      <button type="submit" class="boton-peligro">Continuar de todas formas</button>
      <a class="boton boton-secundario" href="/crear">Cancelar</a>
    </form>
    """ % (
        html.escape(duplicado["titulo"]),
        html.escape(duplicado["fecha"]),
        html.escape(duplicado["donde"]),
        html.escape(slug_alternativo),
        html.escape(valores["titulo"]),
        html.escape(valores["categoria"]),
        html.escape(valores["fecha"]),
        html.escape(valores.get("temas", "")),
    )
    return pagina("Ya existe un artículo con este nombre", cuerpo)


def pagina_creado(carpeta, ruta_md, nombre_md, url_final, temas=None):
    ruta_carpeta_rel = ruta_git(carpeta)
    ruta_md_rel = ruta_git(ruta_md)
    if temas:
        texto_temas = ("Temas: <strong>%s</strong> (ya quedaron en <code>tags:</code>)."
                       % html.escape(", ".join(temas)))
    else:
        texto_temas = ("Sin temas: el .md no lleva <code>tags:</code>. Si después querés "
                       "relacionarlo con otro artículo, agregá a mano "
                       "<code>tags: [Tema]</code> en el front matter.")
    cuerpo = """
    <h1>Artículo creado</h1>
    <div class="exito">
      <p>Carpeta creada: <code>%s</code></p>
      <p>Archivo: <code>%s</code></p>
      <p>URL que va a tener el artículo (ya con el permalink fijo escrito en el front matter):<br>
         <code>%s</code></p>
      <p>%s</p>
    </div>
    <p>Andá a NotebookLM, pegá el contenido en este .md, reemplazá los <code>PENDIENTE</code>
       (<code>excerpt:</code> e <code>image:</code>, sin eso no se publica),
       guardá las imágenes en esta misma carpeta.</p>
    <p>Si cambiás la categoría o la fecha después de esto, actualizá también el
       <code>permalink:</code> del front matter a mano -- ya no se recalcula solo.</p>
    <a class="volver" href="/">&larr; Volver al panel</a>
    """ % (html.escape(ruta_carpeta_rel), html.escape(ruta_md_rel), html.escape(url_final), texto_temas)
    return pagina("Artículo creado", cuerpo)


# Fusiona lo que antes eran 3 pantallas separadas (Editar / Eliminar / Vista
# previa en vivo) en una sola tabla buscable y ordenable, con los 3 botones
# de accion al final de cada fila. Escala mejor que 3 listas <ul> con un solo
# boton cada una: buscar/ordenar/paginar se hace en JS sobre los datos ya
# incluidos en la pagina (nada de recargar ni pegarle al servidor por cada
# letra tipeada), asi que sigue andando sin depender de ninguna libreria.
#
# Los articulos que TODAVIA no se publicaron ni una vez (creados con "Crear
# articulo nuevo" pero nunca llevados a "Publicar borrador") no aparecen
# aca -- no existen en _posts/, que es de donde sale esta lista. Para esos,
# el boton "Vista previa" quedo en la pantalla de "Publicar borrador", que
# ya lista esas carpetas de trabajo.
def pagina_gestionar(articulos):
    filas_json = json.dumps([
        {"archivo": a["archivo"], "titulo": a["titulo"], "fecha": a["fecha"], "categoria": a["categoria"]}
        for a in articulos
    ]).replace("</", "<\\/")  # </script> dentro de un titulo no debe cortar el bloque
    cuerpo = """
    <h1>Gestionar artículos</h1>
    <p class="subtitulo">Buscá, ordená y elegí Editar, Vista previa o Eliminar
       para cualquier artículo ya publicado.</p>
    <input type="text" id="buscador" class="buscador-articulos"
           placeholder="Buscar por título, categoría o nombre de archivo…">
    <div class="tarjeta">
      <table class="tabla-articulos" id="tabla-articulos">
        <thead>
          <tr>
            <th class="ordenable" data-clave="fecha">Fecha<span class="flecha"></span></th>
            <th class="ordenable" data-clave="categoria">Categoría<span class="flecha"></span></th>
            <th class="ordenable" data-clave="titulo">Título<span class="flecha"></span></th>
            <th></th>
          </tr>
        </thead>
        <tbody id="cuerpo-tabla"></tbody>
      </table>
      <p id="sin-resultados" class="sin-resultados" style="display:none;">
        Ningún artículo coincide con la búsqueda.</p>
      <div class="pie-tabla">
        <button type="button" id="boton-mas" class="boton-secundario" style="display:none;">
          Mostrar 25 más</button>
      </div>
    </div>
    <a class="volver" href="/">&larr; Volver</a>
    <script>
    (function () {
      var TODOS = %s;
      var TANDA = 25;
      var estado = { orden: "fecha", desc: true, mostrados: TANDA };
      var cuerpo = document.getElementById("cuerpo-tabla");
      var buscador = document.getElementById("buscador");
      var botonMas = document.getElementById("boton-mas");
      var sinResultados = document.getElementById("sin-resultados");
      var encabezados = document.querySelectorAll("th.ordenable");

      function filtrados() {
        var q = buscador.value.trim().toLowerCase();
        if (!q) return TODOS;
        return TODOS.filter(function (a) {
          return (a.titulo + " " + a.categoria + " " + a.archivo).toLowerCase().indexOf(q) !== -1;
        });
      }

      function crearCeldaTexto(texto) {
        var td = document.createElement("td");
        td.textContent = texto;
        return td;
      }

      function crearFormAccion(accion, archivo, etiqueta, clase) {
        var form = document.createElement("form");
        form.method = "post";
        form.action = accion;
        var input = document.createElement("input");
        input.type = "hidden"; input.name = "archivo"; input.value = archivo;
        var boton = document.createElement("button");
        boton.type = "submit"; boton.className = "boton-mini" + (clase ? " " + clase : "");
        boton.textContent = etiqueta;
        form.appendChild(input); form.appendChild(boton);
        return form;
      }

      function render() {
        var lista = filtrados();
        lista.sort(function (a, b) {
          var x = a[estado.orden], y = b[estado.orden];
          var cmp = x < y ? -1 : x > y ? 1 : 0;
          return estado.desc ? -cmp : cmp;
        });
        cuerpo.innerHTML = "";
        sinResultados.style.display = lista.length ? "none" : "block";
        var visibles = lista.slice(0, estado.mostrados);
        visibles.forEach(function (a) {
          var tr = document.createElement("tr");
          tr.appendChild(crearCeldaTexto(a.fecha));
          tr.appendChild(crearCeldaTexto(a.categoria));
          var tdTitulo = crearCeldaTexto(a.titulo);
          tdTitulo.className = "col-titulo";
          tr.appendChild(tdTitulo);
          var tdAcciones = document.createElement("td");
          tdAcciones.className = "acciones";
          tdAcciones.appendChild(crearFormAccion("/editar/elegir", a.archivo, "Editar"));
          tdAcciones.appendChild(crearFormAccion("/gestionar/vivo", a.archivo, "Vista previa"));
          tdAcciones.appendChild(crearFormAccion("/eliminar/confirmar", a.archivo, "Eliminar", "boton-peligro"));
          tr.appendChild(tdAcciones);
          cuerpo.appendChild(tr);
        });
        botonMas.style.display = lista.length > estado.mostrados ? "inline-block" : "none";
        encabezados.forEach(function (th) {
          var flecha = th.querySelector(".flecha");
          flecha.textContent = th.dataset.clave === estado.orden ? (estado.desc ? " ▼" : " ▲") : "";
        });
      }

      buscador.addEventListener("input", function () { estado.mostrados = TANDA; render(); });
      botonMas.addEventListener("click", function () { estado.mostrados += TANDA; render(); });
      encabezados.forEach(function (th) {
        th.addEventListener("click", function () {
          if (estado.orden === th.dataset.clave) { estado.desc = !estado.desc; }
          else { estado.orden = th.dataset.clave; estado.desc = false; }
          render();
        });
      });
      render();
    })();
    </script>
    """ % filas_json
    return pagina("Gestionar artículos", cuerpo)


def pagina_confirmar_eliminar(articulo):
    cuerpo = """
    <h1>Confirmar eliminación</h1>
    <div class="aviso">
      <p>Vas a eliminar permanentemente del repo (local):</p>
      <p><strong>%s</strong></p>
      <p class="meta">Fecha: %s -- Archivo: _posts/%s</p>
      <p>Se borra el <code>.md</code> y, si existe, la carpeta de imágenes.
         El commit queda LOCAL -- nunca se hace push automático.</p>
    </div>
    <form method="post" action="/eliminar/ejecutar">
      <input type="hidden" name="archivo" value="%s">
      <label for="confirmacion">Escribí ELIMINAR para confirmar</label>
      <input type="text" id="confirmacion" name="confirmacion" autocomplete="off" required>
      <button type="submit" class="boton-peligro">Eliminar definitivamente</button>
      <a class="boton boton-secundario" href="/eliminar">Cancelar</a>
    </form>
    """ % (
        html.escape(articulo["titulo"]),
        html.escape(articulo["fecha"]),
        html.escape(articulo["archivo"]),
        html.escape(articulo["archivo"]),
    )
    return pagina("Confirmar eliminación", cuerpo)


def pagina_eliminado(titulo, mensaje_commit, borro_imagenes, compartida_con=None):
    if compartida_con:
        bloque_compartida = (
            '<div class="aviso"><strong>La carpeta de imágenes NO se borró.</strong>\n'
            'Estos artículos que siguen publicados usan imágenes de esa misma carpeta, '
            'así que borrarla los habría dejado con las imágenes rotas:\n\n%s</div>'
            % html.escape("\n".join("_posts/%s" % n for n in compartida_con))
        )
    else:
        bloque_compartida = ""
    cuerpo = """
    <h1>Artículo eliminado</h1>
    %s
    <div class="exito">
      <p>Eliminado localmente: <strong>%s</strong></p>
      <p>Commit local: <code>%s</code>%s</p>
    </div>
    <p>Sigue recuperable en el historial de git salvo que reescribas el
       historial a propósito. Hacé <code>git push</code> cuando quieras
       confirmar la eliminación en GitHub.</p>
    <a class="volver" href="/">&larr; Volver al panel</a>
    """ % (
        bloque_compartida,
        html.escape(titulo),
        html.escape(mensaje_commit),
        " (incluye la carpeta de imágenes)" if borro_imagenes else "",
    )
    return pagina("Artículo eliminado", cuerpo)


def pagina_error(titulo, mensaje, volver):
    cuerpo = """
    <h1>%s</h1>
    <div class="error">%s</div>
    <a class="volver" href="%s">&larr; Volver</a>
    """ % (html.escape(titulo), html.escape(mensaje), html.escape(volver))
    return pagina(titulo, cuerpo)


def pagina_editar_conflicto(archivo, slug, titulo, destino="editar"):
    """destino == "editar": viene del botón Editar de Gestionar artículos,
    termina en pagina_editar_listo (como siempre). destino == "vivo": viene
    del botón Vista previa de esa misma tabla, y en vez de mostrar la
    carpeta termina arrancando la vista previa en vivo directamente -- las
    dos rutas (/editar/seguir, /editar/reiniciar) leen este mismo campo
    oculto para saber a cuál de los dos destinos ir."""
    explicacion = (
        "¿Querés seguir en esa (se abre tal cual está) o reiniciarla desde "
        "lo que ya está publicado (se pierde lo que tenías sin publicar ahí)?"
        if destino == "editar" else
        "¿Querés ver en vivo esa carpeta tal cual está, o reiniciarla desde "
        "lo que ya está publicado antes de mostrarla (se pierde lo que "
        "tenías sin publicar ahí)?"
    )
    etiqueta_seguir = "Seguir con la carpeta existente" if destino == "editar" else "Ver en vivo lo que ya tenía"
    volver = "/editar" if destino == "editar" else "/gestionar"
    cuerpo = """
    <h1>Ya tenés una carpeta de trabajo para este artículo</h1>
    <div class="aviso">
      <p>«<strong>%s</strong>» ya tiene una carpeta de trabajo en
         <code>_posts/articulos/%s/</code>, con cambios sin publicar.</p>
      <p>%s</p>
    </div>
    <form class="form-en-linea" method="post" action="/editar/seguir">
      <input type="hidden" name="archivo" value="%s">
      <input type="hidden" name="destino" value="%s">
      <button type="submit">%s</button>
    </form>
    <form class="form-en-linea" method="post" action="/editar/reiniciar">
      <input type="hidden" name="archivo" value="%s">
      <input type="hidden" name="destino" value="%s">
      <button type="submit" class="boton-peligro">Reiniciar desde lo publicado</button>
    </form>
    <br>
    <a class="volver" href="%s">&larr; Elegir otro artículo</a>
    """ % (
        html.escape(titulo), html.escape(slug), html.escape(explicacion),
        html.escape(archivo), html.escape(destino), html.escape(etiqueta_seguir),
        html.escape(archivo), html.escape(destino), html.escape(volver),
    )
    return pagina("Ya tenés una carpeta de trabajo para este artículo", cuerpo)


def pagina_editar_listo(carpeta, imagenes):
    ruta_rel = ruta_git(carpeta)
    if imagenes is None:
        bloque_imagenes = ""
    elif imagenes:
        bloque_imagenes = "<p>Imágenes copiadas: %s</p>" % html.escape(", ".join(imagenes))
    else:
        bloque_imagenes = "<p>Este artículo todavía no tiene imágenes.</p>"
    cuerpo = """
    <h1>Listo para seguir editando</h1>
    <div class="exito">
      <p>Carpeta de trabajo: <code>%s</code></p>
      %s
    </div>
    <p>Ya podés seguir editando ahí. Usá <strong>"Vista previa en
       vivo"</strong> para ir mirando cambios, y <strong>"Publicar
       borrador"</strong> cuando quieras subir la actualización -- como el
       nombre coincide con el artículo original, lo va a reemplazar, no va
       a crear uno nuevo.</p>
    <a class="volver" href="/">&larr; Volver al panel</a>
    """ % (html.escape(ruta_rel), bloque_imagenes)
    return pagina("Listo para seguir editando", cuerpo)


def pagina_lista_publicar(borradores):
    if not borradores:
        filas = "<p>No hay borradores en <code>_posts/articulos/</code>.</p>"
    else:
        items = []
        for b in borradores:
            if b["problema"]:
                items.append(
                    '<li><div><strong>%s</strong><br>'
                    '<span class="meta">%s -- modificado: %s</span></div></li>'
                    % (html.escape(b["titulo"]), html.escape(b["problema"]), html.escape(b["modificado"]))
                )
            else:
                items.append(
                    '<li><div><strong>%s</strong><br>'
                    '<span class="meta">Modificado: %s</span></div>'
                    '<div>'
                    '<form class="form-en-linea" method="post" action="/vivo/iniciar">'
                    '<input type="hidden" name="carpeta" value="%s">'
                    '<button type="submit" class="boton-secundario">Vista previa</button>'
                    '</form>'
                    '<form class="form-en-linea" method="post" action="/publicar/revisar">'
                    '<input type="hidden" name="carpeta" value="%s">'
                    '<button type="submit">Revisar y publicar</button>'
                    '</form>'
                    '</div></li>'
                    % (
                        html.escape(b["titulo"]), html.escape(b["modificado"]),
                        html.escape(b["carpeta"]), html.escape(b["carpeta"]),
                    )
                )
        filas = '<ul class="lista-articulos">%s</ul>' % "".join(items)
    cuerpo = """
    <h1>Publicar borrador</h1>
    <p class="subtitulo">"Vista previa" es solo para mirar mientras escribís
       (no chequea <code>PENDIENTE</code> ni corre el validador); "Revisar y
       publicar" es el paso real, con el build completo antes de comitear.</p>
    <div class="tarjeta">%s</div>
    <a class="volver" href="/">&larr; Volver</a>
    """ % filas
    return pagina("Publicar borrador", cuerpo)


def bloque_validacion_html(errores, avisos):
    if not errores and not avisos:
        return '<div class="exito">validar_articulos.py: todo en orden, sin errores ni avisos.</div>'
    partes = []
    if errores:
        lineas = "\n".join("%s:%d -- %s" % (a, max(l, 1), m) for a, l, m in errores)
        partes.append('<div class="error"><strong>Errores de validar_articulos.py (%d):</strong>\n%s</div>'
                       % (len(errores), html.escape(lineas)))
    if avisos:
        lineas = "\n".join("%s:%d -- %s" % (a, max(l, 1), m) for a, l, m in avisos)
        partes.append('<div class="aviso"><strong>Avisos de validar_articulos.py (%d):</strong>\n%s</div>'
                       % (len(avisos), html.escape(lineas)))
    return "".join(partes)


def bloque_respaldo_html(respaldos):
    """Aviso de que hubo cambios sin comitear y se guardaron en un stash en
    vez de perderse. Acepta una etiqueta suelta, una lista, o None."""
    if not respaldos:
        return ""
    if isinstance(respaldos, str):
        respaldos = [respaldos]
    lineas = "\n".join(respaldos)
    return (
        '<div class="aviso"><strong>Se guardaron cambios sin comitear (%d):</strong>\n'
        'Ese archivo tenía ediciones tuyas todavía sin comitear, así que en vez de '
        'pisarlas las guardé en un stash de git. Para recuperarlas: mirá la lista con '
        '<code>git stash list</code> y traelas de vuelta con <code>git stash pop</code>.\n\n%s</div>'
        % (len(respaldos), html.escape(lineas))
    )


def _campos_ocultos(nombre_carpeta, nombre_md, copiadas):
    return (
        '<input type="hidden" name="carpeta" value="%s">'
        '<input type="hidden" name="nombre_md" value="%s">'
        '<input type="hidden" name="imagenes" value="%s">'
    ) % (html.escape(nombre_carpeta), html.escape(nombre_md), html.escape(",".join(copiadas)))


def pagina_vista_previa(nombre_carpeta, nombre_md, copiadas, ruta_site, errores, avisos,
                        respaldo=None):
    bloque_validacion = bloque_respaldo_html(respaldo) + bloque_validacion_html(errores, avisos)
    campos = _campos_ocultos(nombre_carpeta, nombre_md, copiadas)
    if ruta_site:
        src = "http://127.0.0.1:%d/%s" % (PUERTO_VISTA_PREVIA, ruta_site)
        bloque_iframe = '<iframe class="vista-previa-frame" src="%s"></iframe>' % html.escape(src)
    else:
        bloque_iframe = (
            '<div class="error">No pude calcular la URL del artículo para armar el iframe '
            '-- revisá manualmente en <a href="http://127.0.0.1:%d/" target="_blank">'
            'http://127.0.0.1:%d/</a></div>' % (PUERTO_VISTA_PREVIA, PUERTO_VISTA_PREVIA)
        )
    cuerpo = """
    <h1>Vista previa: %s</h1>
    %s
    %s
    <form class="form-en-linea" method="post" action="/publicar/confirmar">
      %s
      <button type="submit">Confirmar y publicar</button>
    </form>
    <form class="form-en-linea" method="post" action="/publicar/descartar">
      %s
      <button type="submit" class="boton-secundario">Volver a editar</button>
    </form>
    <br>
    <a class="volver" href="/publicar">&larr; Elegir otro borrador</a>
    """ % (html.escape(nombre_carpeta), bloque_validacion, bloque_iframe, campos, campos)
    return pagina("Vista previa", cuerpo)


def pagina_error_build(nombre_carpeta, nombre_md, copiadas, salida):
    campos = _campos_ocultos(nombre_carpeta, nombre_md, copiadas)
    cuerpo = """
    <h1>La vista previa no se pudo generar</h1>
    <div class="error">%s</div>
    <p>Los archivos ya se copiaron a <code>_posts/</code> y
       <code>assets/imagenes/</code> (todavía sin commit). Podés resolver el
       problema y reintentar desde <a href="/publicar">Publicar borrador</a>,
       o descartar la copia con el botón de abajo.</p>
    <form method="post" action="/publicar/descartar">
      %s
      <button type="submit" class="boton-secundario">Volver a editar (descartar copia)</button>
    </form>
    <a class="volver" href="/publicar">&larr; Volver</a>
    """ % (html.escape(salida), campos)
    return pagina("La vista previa no se pudo generar", cuerpo)


def pagina_publicado(mensaje_commit, resultado_push, url_acciones):
    push_ok = resultado_push.returncode == 0
    if push_ok:
        bloque_push = '<div class="exito">Push hecho con éxito.</div>'
    else:
        salida_push = (resultado_push.stderr or "") + (resultado_push.stdout or "")
        bloque_push = (
            '<div class="error">El commit se hizo, pero el push falló:\n%s\n'
            'Corré <code>git push</code> a mano cuando se resuelva.</div>' % html.escape(salida_push)
        )
    link_actions = (
        '<p><a href="%s" target="_blank" rel="noopener">Ver en GitHub Actions</a></p>' % html.escape(url_acciones)
        if url_acciones else ""
    )
    cuerpo = """
    <h1>Artículo publicado</h1>
    <div class="exito">Commit: <code>%s</code></div>
    %s
    %s
    <a class="volver" href="/">&larr; Volver al panel</a>
    """ % (html.escape(mensaje_commit), bloque_push, link_actions)
    return pagina("Artículo publicado", cuerpo)


def pagina_descartado(nombre_carpeta, respaldos=None):
    cuerpo = """
    <h1>Vista previa descartada</h1>
    """ + bloque_respaldo_html(respaldos) + """
    <div class="exito">
      <p>Se deshizo la copia de vista previa. La carpeta de trabajo
         <code>_posts/articulos/%s/</code> sigue intacta, lista para seguir
         editando.</p>
    </div>
    <a class="volver" href="/publicar">&larr; Volver a Publicar borrador</a>
    """ % html.escape(nombre_carpeta)
    return pagina("Vista previa descartada", cuerpo)


def pagina_vivo_sin_actividad():
    """GET /vivo cuando no hay ninguna vista previa corriendo. El punto de
    entrada para arrancar una ya no es esta pantalla (antes listaba las
    carpetas de _posts/articulos/, duplicando la lista de "Publicar
    borrador") -- es el botón "Vista previa" de Gestionar artículos (para lo
    ya publicado) o de Publicar borrador (para un borrador que todavía no
    se publicó nunca)."""
    cuerpo = """
    <h1>Vista previa en vivo</h1>
    <p class="subtitulo">No hay ninguna vista previa activa ahora mismo.</p>
    <div class="tarjeta">
      <p>Para arrancar una, elegí un artículo desde
         <a href="/gestionar">Gestionar artículos</a> (si ya está publicado)
         o desde <a href="/publicar">Publicar borrador</a> (si todavía no lo
         publicaste nunca) y tocá su botón «Vista previa».</p>
    </div>
    <a class="volver" href="/">&larr; Volver</a>
    """
    return pagina("Vista previa en vivo", cuerpo)


def pagina_vivo_activa(nombre_carpeta, ruta_site, ultimo_error, respaldo=None):
    if ruta_site:
        src = "http://127.0.0.1:%d/%s" % (PUERTO_SERVE_VIVO, ruta_site)
        bloque_iframe = '<iframe class="vista-previa-frame" src="%s"></iframe>' % html.escape(src)
        link_directo = (
            '<p><a href="%s" target="_blank" rel="noopener">Abrir en una pestaña aparte</a></p>'
            % html.escape(src)
        )
    else:
        bloque_iframe = (
            '<div class="error">No pude calcular la URL del artículo -- revisá manualmente en '
            '<a href="http://127.0.0.1:%d/" target="_blank">http://127.0.0.1:%d/</a></div>'
            % (PUERTO_SERVE_VIVO, PUERTO_SERVE_VIVO)
        )
        link_directo = ""
    bloque_error = bloque_respaldo_html(respaldo) + ((
        '<div class="aviso">La última actualización automática falló (va a reintentar sola): %s</div>'
        % html.escape(ultimo_error)
    ) if ultimo_error else "")
    # Si cambia el category: (y con el, el permalink), el articulo pasa a otra
    # ruta: el iframe se movia solo a la vieja y daba "Not Found". Este sondeo
    # lo lleva a la nueva, pero solo cuando Jekyll ya la termino de generar.
    script_ruta = """
    <script>
    (function () {
      var marco = document.querySelector('.vista-previa-frame');
      if (!marco) { return; }
      var enlace = marco.nextElementSibling && marco.nextElementSibling.querySelector('a');
      var actual = marco.getAttribute('src');
      setInterval(function () {
        fetch('/vivo/estado').then(function (r) { return r.json(); }).then(function (e) {
          if (e.listo && e.url && e.url !== actual) {
            actual = e.url;
            marco.src = e.url;
            if (enlace) { enlace.href = e.url; }
          }
        }).catch(function () {});
      }, 2000);
    })();
    </script>
    """
    cuerpo = """
    <h1>Vista previa en vivo: %s</h1>
    <p class="subtitulo">Se actualiza sola cada vez que guardás un cambio en
       la carpeta de trabajo (cada 1-2 segundos). No chequea <code>PENDIENTE</code>,
       no corre el validador, no comitea nada.</p>
    %s
    %s
    %s
    <form method="post" action="/vivo/detener">
      <input type="hidden" name="carpeta" value="%s">
      <button type="submit" class="boton-secundario">Detener vista previa</button>
    </form>
    %s
    """ % (
        html.escape(nombre_carpeta), bloque_error, bloque_iframe, link_directo,
        html.escape(nombre_carpeta), script_ruta,
    )
    return pagina("Vista previa en vivo", cuerpo)


def pagina_vivo_detenida(nombre_carpeta, respaldos=None):
    cuerpo = """
    <h1>Vista previa en vivo detenida</h1>
    %s
    <div class="exito">
      <p>Se dejó de vigilar la carpeta y se descartó la copia temporal --
         nada quedó comiteado. <code>_posts/articulos/%s/</code> sigue
         intacta, lista para seguir editando.</p>
    </div>
    <a class="volver" href="/vivo">&larr; Volver a Vista previa en vivo</a>
    """ % (bloque_respaldo_html(respaldos), html.escape(nombre_carpeta or ""))
    return pagina("Vista previa en vivo detenida", cuerpo)


# --------------------------------------------------------------------------
# Servidor
# --------------------------------------------------------------------------
class ManejadorPanel(http.server.BaseHTTPRequestHandler):
    # HTTP/1.0 (sin keep-alive): cada conexion se cierra despues de su
    # respuesta. Con HTTP/1.1 y HTTPServer (no threaded), una conexion que
    # queda a medio cerrar bloquea el accept() de las siguientes -- probado
    # en el clon aislado, curl se quedaba esperando para siempre.
    protocol_version = "HTTP/1.0"

    def log_message(self, formato, *args):
        pass  # consola silenciosa; los errores ya se ven en las paginas

    def responder(self, cuerpo_html, status=200):
        datos = cuerpo_html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _redirigir(self, destino):
        self.send_response(302)
        self.send_header("Location", destino)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def leer_formulario(self):
        largo = int(self.headers.get("Content-Length", 0) or 0)
        cuerpo = self.rfile.read(largo).decode("utf-8") if largo else ""
        datos = urllib.parse.parse_qs(cuerpo, keep_blank_values=True)
        return {k: v[0] for k, v in datos.items()}

    def do_GET(self):
        # Mismo criterio que do_POST: ninguna excepcion puede terminar en una
        # respuesta vacia (las listas leen todos los .md, uno roto las tiraba).
        try:
            self._do_GET()
        except Exception as e:
            traceback.print_exc()
            self.responder(pagina_error(
                "Error inesperado",
                "%s: %s -- el detalle completo quedó en la consola del panel."
                % (type(e).__name__, e),
                "/",
            ), status=500)

    def _responder_estado_vivo(self):
        """JSON para el sondeo de la vista previa en vivo: la URL actual del
        articulo y si Jekyll ya la genero (200) -- mover el iframe antes daria
        "Not Found" hasta que termine la reconstruccion."""
        ruta_site = _vista_previa_activa.ruta_site
        estado = {"url": None, "listo": False}
        if ruta_site:
            url = "http://127.0.0.1:%d/%s" % (PUERTO_SERVE_VIVO, ruta_site)
            estado["url"] = url
            try:
                with urllib.request.urlopen(url, timeout=1) as respuesta:
                    estado["listo"] = respuesta.status == 200
            except (urllib.error.URLError, OSError):
                pass
        datos = json.dumps(estado).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _do_GET(self):
        ruta = urllib.parse.urlsplit(self.path).path
        if ruta == "/":
            self.responder(pagina_principal())
        elif ruta == "/crear":
            self.responder(formulario_crear(leer_categorias()))
        elif ruta == "/gestionar":
            self.responder(pagina_gestionar(listar_articulos()))
        elif ruta in ("/editar", "/eliminar"):
            # Las 2 pantallas viejas se fusionaron en "Gestionar articulos".
            self._redirigir("/gestionar")
        elif ruta == "/publicar":
            self.responder(pagina_lista_publicar(listar_borradores()))
        elif ruta == "/vivo/estado":
            self._responder_estado_vivo()
        elif ruta == "/vivo":
            if _vista_previa_activa.carpeta:
                self.responder(pagina_vivo_activa(
                    _vista_previa_activa.carpeta, _vista_previa_activa.ruta_site,
                    _vista_previa_activa.ultimo_error,
                ))
            else:
                self.responder(pagina_vivo_sin_actividad())
        else:
            self.responder(pagina_error("Página no encontrada", ruta, "/"), status=404)

    def do_POST(self):
        ruta = urllib.parse.urlsplit(self.path).path
        try:
            if ruta == "/crear":
                self.manejar_crear()
            elif ruta == "/eliminar/confirmar":
                self.manejar_confirmar_eliminar()
            elif ruta == "/eliminar/ejecutar":
                self.manejar_ejecutar_eliminar()
            elif ruta == "/editar/elegir":
                self.manejar_editar_elegir()
            elif ruta == "/gestionar/vivo":
                self.manejar_gestionar_vivo()
            elif ruta == "/editar/seguir":
                self.manejar_editar_seguir()
            elif ruta == "/editar/reiniciar":
                self.manejar_editar_reiniciar()
            elif ruta == "/publicar/revisar":
                self.manejar_publicar_revisar()
            elif ruta == "/publicar/confirmar":
                self.manejar_publicar_confirmar()
            elif ruta == "/publicar/descartar":
                self.manejar_publicar_descartar()
            elif ruta == "/vivo/iniciar":
                self.manejar_vivo_iniciar()
            elif ruta == "/vivo/detener":
                self.manejar_vivo_detener()
            else:
                self.responder(pagina_error("Página no encontrada", ruta, "/"), status=404)
        except (ErrorPanel, pa.ErrorPublicacion) as e:
            self.responder(pagina_error("No se pudo completar la acción", str(e), "/"))
        except Exception as e:
            # Cualquier otro fallo (disco, permisos, bug) antes solo quedaba en
            # la consola y el navegador mostraba ERR_EMPTY_RESPONSE.
            traceback.print_exc()
            self.responder(pagina_error(
                "Error inesperado",
                "%s: %s -- el detalle completo quedó en la consola del panel."
                % (type(e).__name__, e),
                "/",
            ), status=500)

    def manejar_crear(self):
        datos = self.leer_formulario()
        categorias = leer_categorias()
        titulo = (datos.get("titulo") or "").strip()
        categoria = (datos.get("categoria") or "").strip()
        fecha = (datos.get("fecha") or "").strip()
        temas_texto = (datos.get("temas") or "").strip()
        temas = normalizar_temas(temas_texto)
        confirmar = datos.get("confirmar") == "1"

        if not titulo:
            self.responder(formulario_crear(categorias, datos, "El título no puede estar vacío."))
            return
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha):
            self.responder(formulario_crear(categorias, datos, "La fecha no es válida."))
            return
        if categoria not in [c["name"] for c in categorias]:
            self.responder(formulario_crear(categorias, datos, "Elegí una categoría de la lista."))
            return

        slug = slug_de_titulo(titulo)
        duplicado = buscar_duplicado(slug) if slug else None
        if duplicado:
            if not confirmar:
                self.responder(pagina_duplicado(
                    {"titulo": titulo, "categoria": categoria, "fecha": fecha, "temas": temas_texto},
                    duplicado, slug_libre(slug),
                ))
                return
            slug = slug_libre(slug)

        _, carpeta, ruta_md, nombre_md, url_final = crear_carpeta_articulo(
            titulo, categoria, fecha, categorias, slug=slug, temas=temas
        )
        self.responder(pagina_creado(carpeta, ruta_md, nombre_md, url_final, temas))

    def manejar_confirmar_eliminar(self):
        datos = self.leer_formulario()
        archivo = datos.get("archivo") or ""
        articulos = {a["archivo"]: a for a in listar_articulos()}
        if archivo not in articulos:
            self.responder(pagina_error(
                "Artículo no encontrado", "«%s» no está en la lista de artículos." % archivo, "/eliminar"
            ))
            return
        self.responder(pagina_confirmar_eliminar(articulos[archivo]))

    def manejar_ejecutar_eliminar(self):
        datos = self.leer_formulario()
        archivo = datos.get("archivo") or ""
        confirmacion = datos.get("confirmacion") or ""
        if confirmacion != "ELIMINAR":
            self.responder(pagina_error(
                "No se eliminó nada",
                "Tenías que escribir exactamente ELIMINAR para confirmar. No se borró nada.",
                "/eliminar",
            ))
            return
        titulo, mensaje_commit, borro_imagenes, compartida_con = eliminar_articulo(archivo)
        self.responder(pagina_eliminado(titulo, mensaje_commit, borro_imagenes, compartida_con))

    def manejar_editar_elegir(self):
        datos = self.leer_formulario()
        archivo = datos.get("archivo") or ""
        articulos = {a["archivo"]: a for a in listar_articulos()}
        if archivo not in articulos:
            self.responder(pagina_error(
                "Artículo no encontrado", "«%s» no está en la lista de artículos." % archivo, "/gestionar"
            ))
            return

        slug = _slug_de_archivo_post(archivo)
        if slug and carpeta_trabajo_existe(slug):
            self.responder(pagina_editar_conflicto(archivo, slug, articulos[archivo]["titulo"], "editar"))
            return

        _, carpeta, _, imagenes = crear_carpeta_edicion(archivo)
        self.responder(pagina_editar_listo(carpeta, imagenes))

    def manejar_gestionar_vivo(self):
        """Boton "Vista previa" de la fila de un articulo YA PUBLICADO, en
        Gestionar articulos. Mismo chequeo de conflicto que Editar (si ya
        habia una carpeta de trabajo con cambios sin publicar); a diferencia
        de Editar, el destino final no es la pantalla "carpeta lista" sino
        la vista previa en vivo arrancada directamente, sin pantallas de
        mas -- ver pagina_editar_conflicto(destino="vivo")."""
        datos = self.leer_formulario()
        archivo = datos.get("archivo") or ""
        articulos = {a["archivo"]: a for a in listar_articulos()}
        if archivo not in articulos:
            self.responder(pagina_error(
                "Artículo no encontrado", "«%s» no está en la lista de artículos." % archivo, "/gestionar"
            ))
            return

        slug = _slug_de_archivo_post(archivo)
        if slug and carpeta_trabajo_existe(slug):
            self.responder(pagina_editar_conflicto(archivo, slug, articulos[archivo]["titulo"], "vivo"))
            return

        slug, _carpeta, _ruta_md, _imagenes = crear_carpeta_edicion(archivo)
        self._iniciar_vivo(slug)

    def manejar_editar_seguir(self):
        datos = self.leer_formulario()
        archivo = datos.get("archivo") or ""
        destino = datos.get("destino") or "editar"
        slug = _slug_de_archivo_post(archivo)
        if not slug or not carpeta_trabajo_existe(slug):
            self.responder(pagina_error(
                "No encuentro esa carpeta de trabajo",
                "«%s» no tiene una carpeta de trabajo en _posts/articulos/ -- puede que ya se haya movido o borrado." % archivo,
                "/gestionar",
            ))
            return
        if destino == "vivo":
            self._iniciar_vivo(slug)
            return
        carpeta = os.path.join(RAIZ, "_posts", "articulos", slug)
        self.responder(pagina_editar_listo(carpeta, None))

    def manejar_editar_reiniciar(self):
        datos = self.leer_formulario()
        archivo = datos.get("archivo") or ""
        destino = datos.get("destino") or "editar"
        articulos = {a["archivo"] for a in listar_articulos()}
        if archivo not in articulos:
            self.responder(pagina_error(
                "Artículo no encontrado", "«%s» no está en la lista de artículos." % archivo, "/gestionar"
            ))
            return
        slug, carpeta, _ruta_md, imagenes = reiniciar_carpeta_edicion(archivo)
        if destino == "vivo":
            self._iniciar_vivo(slug)
            return
        self.responder(pagina_editar_listo(carpeta, imagenes))

    def manejar_publicar_revisar(self):
        datos = self.leer_formulario()
        nombre_carpeta_pedido = (datos.get("carpeta") or "").strip()

        (nombre_carpeta, nombre_md, destino_md, destino_imagenes, copiadas,
         respaldo) = revisar_y_copiar_borrador(nombre_carpeta_pedido)

        # Con la copia ya hecha, un fallo inesperado (build, validador) no
        # puede dejarla huerfana: la pagina de error generica no tiene boton
        # de "Volver a editar".
        try:
            resultado_build, error_bundle = construir_sitio()
            if error_bundle:
                cuerpo = pagina_error_build(nombre_carpeta, nombre_md, copiadas, error_bundle)
            elif resultado_build.returncode != 0:
                salida = (resultado_build.stderr or "") + "\n" + (resultado_build.stdout or "")
                cuerpo = pagina_error_build(nombre_carpeta, nombre_md, copiadas, salida)
            else:
                errores, avisos = validar_borrador(destino_md, nombre_carpeta, copiadas)
                fm = leer_front_matter(destino_md)
                ruta_site = ruta_generada_en_site(fm, nombre_carpeta)
                cuerpo = pagina_vista_previa(
                    nombre_carpeta, nombre_md, copiadas, ruta_site, errores, avisos, respaldo)
        except Exception as e:
            traceback.print_exc()
            self.responder(pagina_error(
                "No se pudo armar la vista previa",
                _mensaje_fallo_tras_copia(
                    e, lambda: descartar_vista_previa(nombre_carpeta, nombre_md, copiadas)),
                "/publicar",
            ), status=500)
            return
        self.responder(cuerpo)

    def manejar_publicar_confirmar(self):
        datos = self.leer_formulario()
        nombre_carpeta = datos.get("carpeta") or ""
        nombre_md = datos.get("nombre_md") or ""
        copiadas = [i for i in (datos.get("imagenes") or "").split(",") if i]

        destino_md = os.path.join(RAIZ, "_posts", nombre_md)
        destino_imagenes = os.path.join(RAIZ, "assets", "imagenes", nombre_carpeta)

        mensaje_commit, error_git = pa.confirmar_commit(nombre_carpeta, destino_md, destino_imagenes, copiadas)
        if error_git:
            self.responder(pagina_error("No se pudo publicar", error_git, "/publicar"))
            return
        if not mensaje_commit:
            self.responder(pagina_error(
                "No se pudo publicar",
                "No había cambios para comitear -- revisá que la vista previa se haya generado bien.",
                "/publicar",
            ))
            return

        resultado_push = git("push")
        self.responder(pagina_publicado(mensaje_commit, resultado_push, url_actions()))

    def manejar_publicar_descartar(self):
        datos = self.leer_formulario()
        nombre_carpeta = datos.get("carpeta") or ""
        nombre_md = datos.get("nombre_md") or ""
        copiadas = [i for i in (datos.get("imagenes") or "").split(",") if i]
        respaldos = descartar_vista_previa(nombre_carpeta, nombre_md, copiadas)
        self.responder(pagina_descartado(nombre_carpeta, respaldos))

    def manejar_vivo_iniciar(self):
        datos = self.leer_formulario()
        self._iniciar_vivo((datos.get("carpeta") or "").strip())

    def _iniciar_vivo(self, nombre_carpeta):
        """Arranca (o reusa) la vista previa en vivo para una carpeta de
        trabajo que YA existe en _posts/articulos/<nombre_carpeta>/. La usan
        tres caminos: el boton "Vista previa" de Publicar borrador (via
        manejar_vivo_iniciar, con la carpeta tal cual estaba), y el boton
        "Vista previa" de Gestionar articulos para un articulo YA publicado
        -- directo si no habia conflicto, o luego de que Elvis elige
        "seguir"/"reiniciar" en la pantalla de conflicto."""
        if _vista_previa_activa.carpeta and _vista_previa_activa.carpeta != nombre_carpeta:
            _detener_vista_previa_activa()

        if _vista_previa_activa.carpeta == nombre_carpeta:
            self.responder(pagina_vivo_activa(
                _vista_previa_activa.carpeta, _vista_previa_activa.ruta_site,
                _vista_previa_activa.ultimo_error,
            ))
            return

        (nombre_validado, nombre_md, destino_md, destino_imagenes, copiadas,
         respaldo) = copiar_para_vista_previa(nombre_carpeta)

        try:
            self._arrancar_vivo(nombre_validado, nombre_md, destino_md, copiadas, respaldo)
        except Exception as e:
            # Con la copia ya hecha, un fallo inesperado la dejaba huerfana:
            # sin registrar como vista previa activa, "Detener vista previa"
            # no la encontraba. Si alcanzo a registrarse, se detiene entera.
            traceback.print_exc()
            if _vista_previa_activa.carpeta == nombre_validado:
                descartar = lambda: _detener_vista_previa_activa()[1]
            else:
                descartar = lambda: descartar_vista_previa(nombre_validado, nombre_md, copiadas)
            self.responder(pagina_error(
                "No se pudo iniciar la vista previa en vivo",
                _mensaje_fallo_tras_copia(e, descartar),
                "/vivo",
            ), status=500)

    def _arrancar_vivo(self, nombre_validado, nombre_md, destino_md, copiadas, respaldo):
        error_bundle = iniciar_jekyll_serve()
        if error_bundle:
            descartar_vista_previa(nombre_validado, nombre_md, copiadas)
            self.responder(pagina_error("No se pudo iniciar la vista previa en vivo", error_bundle, "/vivo"))
            return

        if not esperar_jekyll_listo():
            descartar_vista_previa(nombre_validado, nombre_md, copiadas)
            self.responder(pagina_error(
                "No se pudo iniciar la vista previa en vivo",
                "`bundle exec jekyll serve` no respondió a tiempo -- revisá si hay "
                "algún error de sintaxis en el .md que rompa el build y volvé a intentar.",
                "/vivo",
            ))
            return

        fm = leer_front_matter(destino_md)
        ruta_site = ruta_generada_en_site(fm, nombre_validado)

        evento_detener = threading.Event()
        hilo = threading.Thread(
            target=_bucle_vigilancia, args=(nombre_validado, evento_detener), daemon=True,
        )

        _vista_previa_activa.carpeta = nombre_validado
        _vista_previa_activa.nombre_md = nombre_md
        _vista_previa_activa.copiadas = copiadas
        _vista_previa_activa.ruta_site = ruta_site
        _vista_previa_activa.evento_detener = evento_detener
        _vista_previa_activa.hilo = hilo
        _vista_previa_activa.ultimo_error = None

        hilo.start()

        self.responder(pagina_vivo_activa(nombre_validado, ruta_site, None, respaldo))

    def manejar_vivo_detener(self):
        carpeta, respaldos = _detener_vista_previa_activa()
        self.responder(pagina_vivo_detenida(carpeta, respaldos))


def main():
    # Threading: una pestana/peticion colgada (ej. el navegador pidiendo un
    # favicon) no debe bloquear el resto del panel.
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", PUERTO), ManejadorPanel)
    iniciar_servidor_vista_previa()
    url = "http://127.0.0.1:%d/" % PUERTO
    threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    print("Panel de control corriendo en %s" % url)
    print("Deja esta ventana abierta. Cerrala (o Ctrl+C) para apagar el servidor.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _detener_vista_previa_activa()
        if jekyll_serve_activo():
            _proceso_jekyll_serve.terminate()


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    main()
