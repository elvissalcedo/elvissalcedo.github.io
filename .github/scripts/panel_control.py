#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Panel de control local para crear y eliminar articulos de Git_Page.

Arranca un servidor HTTP en 127.0.0.1, solo con la libreria estandar de
Python (nada que instalar). Pensado para correr con doble clic en
panel-control-gitpage.bat, que abre el navegador solo.

Tres flujos: "Crear articulo nuevo" arma la carpeta de trabajo
(_posts/articulos/<slug>/) con el .md y su front matter listos para que
Elvis pegue el contenido de NotebookLM. "Publicar borrador" reemplaza el
paso manual de correr publicar_articulo.py en la terminal -- copia el
borrador a _posts/ y assets/imagenes/ SIN commit, arma una vista previa
real con `bundle exec jekyll build` embebida en un iframe, y solo hace
`git add` + commit + push cuando Elvis aprieta "Confirmar y publicar"; si
en cambio aprieta "Volver a editar", deshace la copia sin dejar rastro.
"Eliminar articulo publicado" borra un articulo que ya esta en _posts/
(con git rm + commit local, nunca push).

URL de cada articulo nuevo: Jekyll arma la ruta automatica con
`:categories` a partir del `category:` del front matter, pero solo hace
.downcase -- no saca tildes ni cambia espacios por guiones. Para las 4
categorias de nombre compuesto (Toxicologia y Salud, Sostenibilidad y
Energia, Gestion y Politica, Filosofia y Decision) eso da una URL rota
(espacios y tildes literales). Confirmado con una build real de Jekyll en
un clon aislado. Por eso este panel escribe SIEMPRE un `permalink:`
explicito usando el slug prolijo de _config.yml, para las 8 categorias por
igual -- decision de Elvis del 2026-09-21 frente a esta alternativa.
"""
import functools
import html
import http.server
import os
import re
import shutil
import subprocess
import sys
import threading
import unicodedata
import urllib.parse
import webbrowser
from datetime import date, datetime

import publicar_articulo as pa
import validar_articulos as va

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUERTO = 8420
PUERTO_VISTA_PREVIA = 8421
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
    bloque = re.search(r"^categorias:\n((?:\s+-.*\n)+)", config, re.M)
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


def leer_front_matter(ruta):
    with open(ruta, encoding="utf-8") as fh:
        texto = fh.read()
    if not texto.startswith("---"):
        return {}
    fin = texto.find("\n---", 3)
    if fin == -1:
        return {}
    datos = {}
    for linea in texto[3:fin].split("\n"):
        m = re.match(r'^([a-zA-Z_][\w-]*):\s*(.*)$', linea)
        if m:
            valor = m.group(2).strip()
            if len(valor) > 1 and valor[0] == valor[-1] and valor[0] in "\"'":
                valor = valor[1:-1]
            datos[m.group(1)] = valor
    return datos


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def ruta_git(ruta_absoluta):
    return os.path.relpath(ruta_absoluta, RAIZ).replace(os.sep, "/")


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


def crear_carpeta_articulo(titulo, categoria, fecha, categorias):
    slug = slugify(titulo)
    if not slug:
        raise ErrorPanel(
            "Ese titulo no genera un nombre de archivo valido -- probá con "
            "letras o numeros."
        )

    slug_cat = slug_de_categoria(categoria, categorias)
    if slug_cat is None:
        raise ErrorPanel("La categoria «%s» no es ninguna de las 8 validas." % categoria)

    carpeta = os.path.join(RAIZ, "_posts", "articulos", slug)
    os.makedirs(carpeta, exist_ok=True)
    nombre_md = "%s-%s.md" % (fecha, slug)
    ruta_md = os.path.join(carpeta, nombre_md)

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
        "permalink: %s\n"
        "---\n"
    ) % (titulo_yaml, fecha, categoria, permalink)

    with open(ruta_md, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(front_matter)

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
        articulos.append({
            "archivo": nombre,
            "titulo": fm.get("title", nombre),
            "fecha": fm.get("date", "?"),
            "categoria": fm.get("category", "?"),
        })
    return articulos


PATRON_ARCHIVO_POST = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$")


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
        raise ErrorPanel(
            "`git commit` fallo:\n%s" % (resultado_commit.stderr or resultado_commit.stdout)
        )

    return titulo, mensaje, borra_imagenes


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
        if not os.path.isdir(carpeta):
            continue
        mds = [f for f in os.listdir(carpeta) if f.endswith(".md")]
        problema = None
        if len(mds) == 1:
            fm = leer_front_matter(os.path.join(carpeta, mds[0]))
            titulo = fm.get("title", nombre)
            mtime = os.path.getmtime(os.path.join(carpeta, mds[0]))
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

    with open(os.path.join(carpeta, nombre_md), encoding="utf-8") as fh:
        texto = fh.read()

    pa.verificar_sin_pendientes(texto, nombre_validado)

    texto_final, _cambios, _referenciadas = pa.procesar_referencias(
        texto, nombre_validado, set(imagenes)
    )

    destino_md, _ya_existia, destino_imagenes, copiadas = pa.copiar_articulo(
        carpeta, nombre_validado, nombre_md, imagenes, texto_final
    )
    return nombre_validado, nombre_md, destino_md, destino_imagenes, copiadas


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
    """Si el archivo ya estaba trackeado en git (una republicacion sobre un
    articulo existente), restaura su version comiteada. Si es nuevo (nunca
    se hizo git add), lo borra -- asi "Volver a editar" nunca pisa contenido
    real ya publicado."""
    if not os.path.isfile(ruta_absoluta):
        return
    rel = ruta_git(ruta_absoluta)
    resultado = git("ls-files", "--error-unmatch", "--", rel)
    if resultado.returncode == 0:
        git("checkout", "--", rel)
    else:
        os.remove(ruta_absoluta)


def descartar_vista_previa(nombre_carpeta, nombre_md, copiadas):
    if nombre_md:
        _revertir_o_borrar(os.path.join(RAIZ, "_posts", nombre_md))
    carpeta_imagenes = os.path.join(RAIZ, "assets", "imagenes", nombre_carpeta)
    for imagen in copiadas:
        _revertir_o_borrar(os.path.join(carpeta_imagenes, imagen))
    if os.path.isdir(carpeta_imagenes) and not os.listdir(carpeta_imagenes):
        os.rmdir(carpeta_imagenes)


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
  .boton-eliminar { background: #f6e9e7; color: #7a2b1f; }
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
      <a class="boton-grande boton-eliminar" href="/eliminar">Eliminar artículo publicado</a>
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

        <button type="submit">Crear carpeta del artículo</button>
      </form>
    </div>
    <a class="volver" href="/">&larr; Volver</a>
    """ % (
        bloque_error,
        html.escape(valores.get("titulo", "")),
        opciones,
        html.escape(valores.get("fecha") or hoy),
    )
    return pagina("Crear artículo nuevo", cuerpo)


def pagina_duplicado(valores, duplicado):
    cuerpo = """
    <h1>Ya existe un artículo con este nombre</h1>
    <div class="aviso">
      <p><strong>%s</strong> (%s)</p>
      <p>Encontrado en: %s</p>
      <p>¿Continuar de todas formas? Esto puede generar un duplicado si no era tu intención.</p>
    </div>
    <form method="post" action="/crear">
      <input type="hidden" name="titulo" value="%s">
      <input type="hidden" name="categoria" value="%s">
      <input type="hidden" name="fecha" value="%s">
      <input type="hidden" name="confirmar" value="1">
      <button type="submit" class="boton-peligro">Continuar de todas formas</button>
      <a class="boton boton-secundario" href="/crear">Cancelar</a>
    </form>
    """ % (
        html.escape(duplicado["titulo"]),
        html.escape(duplicado["fecha"]),
        html.escape(duplicado["donde"]),
        html.escape(valores["titulo"]),
        html.escape(valores["categoria"]),
        html.escape(valores["fecha"]),
    )
    return pagina("Ya existe un artículo con este nombre", cuerpo)


def pagina_creado(carpeta, ruta_md, nombre_md, url_final):
    ruta_carpeta_rel = ruta_git(carpeta)
    ruta_md_rel = ruta_git(ruta_md)
    cuerpo = """
    <h1>Artículo creado</h1>
    <div class="exito">
      <p>Carpeta creada: <code>%s</code></p>
      <p>Archivo: <code>%s</code></p>
      <p>URL que va a tener el artículo (ya con el permalink fijo escrito en el front matter):<br>
         <code>%s</code></p>
    </div>
    <p>Andá a NotebookLM, pegá el contenido en este .md, reemplazá los <code>PENDIENTE</code>,
       guardá las imágenes en esta misma carpeta.</p>
    <p>Si cambiás la categoría o la fecha después de esto, actualizá también el
       <code>permalink:</code> del front matter a mano -- ya no se recalcula solo.</p>
    <a class="volver" href="/">&larr; Volver al panel</a>
    """ % (html.escape(ruta_carpeta_rel), html.escape(ruta_md_rel), html.escape(url_final))
    return pagina("Artículo creado", cuerpo)


def pagina_lista_eliminar(articulos):
    if not articulos:
        filas = "<p>No hay artículos publicados en <code>_posts/</code>.</p>"
    else:
        items = []
        for a in articulos:
            items.append(
                '<li><div><strong>%s</strong><br>'
                '<span class="meta">%s -- %s -- %s</span></div>'
                '<form method="post" action="/eliminar/confirmar">'
                '<input type="hidden" name="archivo" value="%s">'
                '<button type="submit" class="boton-peligro">Eliminar</button>'
                '</form></li>'
                % (
                    html.escape(a["titulo"]),
                    html.escape(a["fecha"]),
                    html.escape(a["categoria"]),
                    html.escape(a["archivo"]),
                    html.escape(a["archivo"]),
                )
            )
        filas = '<ul class="lista-articulos">%s</ul>' % "".join(items)
    cuerpo = """
    <h1>Eliminar artículo publicado</h1>
    <div class="tarjeta">%s</div>
    <a class="volver" href="/">&larr; Volver</a>
    """ % filas
    return pagina("Eliminar artículo publicado", cuerpo)


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


def pagina_eliminado(titulo, mensaje_commit, borro_imagenes):
    cuerpo = """
    <h1>Artículo eliminado</h1>
    <div class="exito">
      <p>Eliminado localmente: <strong>%s</strong></p>
      <p>Commit local: <code>%s</code>%s</p>
    </div>
    <p>Sigue recuperable en el historial de git salvo que reescribas el
       historial a propósito. Hacé <code>git push</code> cuando quieras
       confirmar la eliminación en GitHub.</p>
    <a class="volver" href="/">&larr; Volver al panel</a>
    """ % (
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
                    '<form method="post" action="/publicar/revisar">'
                    '<input type="hidden" name="carpeta" value="%s">'
                    '<button type="submit">Revisar y publicar</button>'
                    '</form></li>'
                    % (html.escape(b["titulo"]), html.escape(b["modificado"]), html.escape(b["carpeta"]))
                )
        filas = '<ul class="lista-articulos">%s</ul>' % "".join(items)
    cuerpo = """
    <h1>Publicar borrador</h1>
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


def _campos_ocultos(nombre_carpeta, nombre_md, copiadas):
    return (
        '<input type="hidden" name="carpeta" value="%s">'
        '<input type="hidden" name="nombre_md" value="%s">'
        '<input type="hidden" name="imagenes" value="%s">'
    ) % (html.escape(nombre_carpeta), html.escape(nombre_md), html.escape(",".join(copiadas)))


def pagina_vista_previa(nombre_carpeta, nombre_md, copiadas, ruta_site, errores, avisos):
    bloque_validacion = bloque_validacion_html(errores, avisos)
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


def pagina_descartado(nombre_carpeta):
    cuerpo = """
    <h1>Vista previa descartada</h1>
    <div class="exito">
      <p>Se deshizo la copia de vista previa. La carpeta de trabajo
         <code>_posts/articulos/%s/</code> sigue intacta, lista para seguir
         editando.</p>
    </div>
    <a class="volver" href="/publicar">&larr; Volver a Publicar borrador</a>
    """ % html.escape(nombre_carpeta)
    return pagina("Vista previa descartada", cuerpo)


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

    def leer_formulario(self):
        largo = int(self.headers.get("Content-Length", 0) or 0)
        cuerpo = self.rfile.read(largo).decode("utf-8") if largo else ""
        datos = urllib.parse.parse_qs(cuerpo, keep_blank_values=True)
        return {k: v[0] for k, v in datos.items()}

    def do_GET(self):
        ruta = urllib.parse.urlsplit(self.path).path
        if ruta == "/":
            self.responder(pagina_principal())
        elif ruta == "/crear":
            self.responder(formulario_crear(leer_categorias()))
        elif ruta == "/eliminar":
            self.responder(pagina_lista_eliminar(listar_articulos()))
        elif ruta == "/publicar":
            self.responder(pagina_lista_publicar(listar_borradores()))
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
            elif ruta == "/publicar/revisar":
                self.manejar_publicar_revisar()
            elif ruta == "/publicar/confirmar":
                self.manejar_publicar_confirmar()
            elif ruta == "/publicar/descartar":
                self.manejar_publicar_descartar()
            else:
                self.responder(pagina_error("Página no encontrada", ruta, "/"), status=404)
        except (ErrorPanel, pa.ErrorPublicacion) as e:
            self.responder(pagina_error("No se pudo completar la acción", str(e), "/"))

    def manejar_crear(self):
        datos = self.leer_formulario()
        categorias = leer_categorias()
        titulo = (datos.get("titulo") or "").strip()
        categoria = (datos.get("categoria") or "").strip()
        fecha = (datos.get("fecha") or "").strip()
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

        slug = slugify(titulo)
        if not confirmar:
            duplicado = buscar_duplicado(slug)
            if duplicado:
                self.responder(pagina_duplicado(
                    {"titulo": titulo, "categoria": categoria, "fecha": fecha}, duplicado
                ))
                return

        _, carpeta, ruta_md, nombre_md, url_final = crear_carpeta_articulo(
            titulo, categoria, fecha, categorias
        )
        self.responder(pagina_creado(carpeta, ruta_md, nombre_md, url_final))

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
        titulo, mensaje_commit, borro_imagenes = eliminar_articulo(archivo)
        self.responder(pagina_eliminado(titulo, mensaje_commit, borro_imagenes))

    def manejar_publicar_revisar(self):
        datos = self.leer_formulario()
        nombre_carpeta_pedido = (datos.get("carpeta") or "").strip()

        nombre_carpeta, nombre_md, destino_md, destino_imagenes, copiadas = revisar_y_copiar_borrador(
            nombre_carpeta_pedido
        )

        resultado_build, error_bundle = construir_sitio()
        if error_bundle:
            self.responder(pagina_error_build(nombre_carpeta, nombre_md, copiadas, error_bundle))
            return
        if resultado_build.returncode != 0:
            salida = (resultado_build.stderr or "") + "\n" + (resultado_build.stdout or "")
            self.responder(pagina_error_build(nombre_carpeta, nombre_md, copiadas, salida))
            return

        errores, avisos = validar_borrador(destino_md, nombre_carpeta, copiadas)
        fm = leer_front_matter(destino_md)
        ruta_site = ruta_generada_en_site(fm, nombre_carpeta)
        self.responder(pagina_vista_previa(nombre_carpeta, nombre_md, copiadas, ruta_site, errores, avisos))

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
        descartar_vista_previa(nombre_carpeta, nombre_md, copiadas)
        self.responder(pagina_descartado(nombre_carpeta))


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


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    main()
