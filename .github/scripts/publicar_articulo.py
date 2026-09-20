#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publica un articulo desde su carpeta de trabajo.

Uso:
    python .github/scripts/publicar_articulo.py _posts/articulos/<carpeta>

Elvis arma una carpeta de trabajo con el .md del articulo y todas sus
imagenes juntas, con nombres simples (esquema.jpg, no una ruta). Este
script:

  1. copia el .md a _posts/, validando que el nombre empiece con AAAA-MM-DD-;
  2. copia las imagenes de la carpeta a assets/imagenes/<carpeta>/;
  3. reescribe cada referencia de imagen del .md copiado a su ruta real
     (/assets/imagenes/<carpeta>/archivo.ext);
  4. muestra un resumen de que copio y que reescribio;
  5. hace `git add` + `git commit` local de los archivos nuevos -- nunca
     hace push, eso lo confirma Elvis siempre a mano.

Si algo no encaja (falta la fecha en el nombre del .md, una imagen
referenciada no esta en la carpeta, un <img src> ya trae una ruta armada,
no hay ninguna imagen en la carpeta), el script para antes de tocar nada
y explica el problema en espanol simple.

La carpeta de trabajo (_posts/articulos/) queda excluida del build de
Jekyll en _config.yml: lo que vive ahi es material de trabajo, nunca se
publica tal cual.
"""
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXTENSIONES_IMAGEN = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")

PATRON_IMG_TAG = re.compile(r'(<img\b[^>]*\bsrc=")([^"]+)(")')
PATRON_MD_IMG = re.compile(r'(!\[[^\]]*\]\()([^)\s]+)(\))')
PATRON_FRONT_IMAGE = re.compile(r'^(image:\s*)(\S+)()\s*$', re.M)
PATRON_SLUG = re.compile(r'^[a-z0-9-]+$')


class ErrorPublicacion(Exception):
    """Un problema en los datos de entrada: se muestra tal cual, sin traceback."""


def fallar(mensaje):
    raise ErrorPublicacion(mensaje)


def resolver_carpeta(argumento):
    carpeta = os.path.abspath(argumento)
    if not os.path.isdir(carpeta):
        fallar("No encuentro la carpeta «%s». Revisa la ruta." % argumento)
    nombre_carpeta = os.path.basename(carpeta.rstrip("/\\"))
    if not PATRON_SLUG.match(nombre_carpeta):
        fallar(
            "El nombre de la carpeta «%s» tiene que ser solo minusculas, "
            "numeros y guiones (asi queda la URL de las imagenes: "
            "/assets/imagenes/%s/...). Renombra la carpeta y volve a correr "
            "el script." % (nombre_carpeta, nombre_carpeta)
        )
    return carpeta, nombre_carpeta


def encontrar_md(carpeta, nombre_carpeta):
    archivos_md = sorted(f for f in os.listdir(carpeta) if f.lower().endswith(".md"))
    if not archivos_md:
        fallar(
            "La carpeta «%s» no tiene ningun archivo .md adentro. Tiene que "
            "haber exactamente un articulo (el .md) junto a sus imagenes."
            % nombre_carpeta
        )
    if len(archivos_md) > 1:
        fallar(
            "La carpeta «%s» tiene mas de un archivo .md (%s). Solo puede "
            "haber uno: el articulo de esa carpeta."
            % (nombre_carpeta, ", ".join(archivos_md))
        )
    nombre_md = archivos_md[0]
    if not re.match(r'^\d{4}-\d{2}-\d{2}-.+\.md$', nombre_md):
        fallar(
            "El archivo «%s» no empieza con una fecha AAAA-MM-DD-. Por "
            "ejemplo: 2026-09-20-%s.md. Sin esa fecha al principio, Jekyll "
            "no lo reconoce como articulo -- pone la fecha real de "
            "publicacion y volve a correr el script."
            % (nombre_md, nombre_carpeta)
        )
    return nombre_md


def encontrar_imagenes(carpeta, nombre_carpeta):
    imagenes = sorted(
        f for f in os.listdir(carpeta)
        if os.path.splitext(f)[1].lower() in EXTENSIONES_IMAGEN
    )
    if not imagenes:
        fallar(
            "La carpeta «%s» no tiene ninguna imagen (.jpg, .jpeg, .png, "
            ".gif, .webp o .svg). Si el articulo de verdad no lleva "
            "imagenes, este script no es lo que hace falta todavia -- avisa "
            "para ajustarlo." % nombre_carpeta
        )
    return imagenes


def procesar_referencias(texto, nombre_carpeta, imagenes_disponibles):
    """Valida y reescribe las referencias de imagen del .md.

    Recorre <img src="...">, ![alt](...) en Markdown y el `image:` del
    front matter. Los dos primeros exigen un nombre de archivo simple (sin
    "/"); el front matter tolera una ruta ya armada (/assets/...) y la deja
    intacta, para no romper un articulo que ya la traiga bien puesta.
    Cualquier referencia invalida corta la ejecucion antes de escribir nada.
    """
    cambios = []
    referenciadas = set()

    def validar_simple(ref, contexto, estricto):
        if ref.startswith(("http://", "https://", "//")):
            if estricto:
                fallar(
                    "La imagen «%s» en %s es una URL externa. Este script "
                    "solo reescribe imagenes locales que viven en la misma "
                    "carpeta de trabajo." % (ref, contexto)
                )
            return None
        if "/" in ref or "\\" in ref:
            if estricto:
                fallar(
                    "La imagen «%s» en %s ya viene con una ruta armada. "
                    "Escribi solo el nombre del archivo (por ejemplo "
                    "\"%s\"), sin /assets/ ni ninguna carpeta adelante -- el "
                    "script arma la ruta final solo."
                    % (ref, contexto, os.path.basename(ref))
                )
            return None
        if ref not in imagenes_disponibles:
            fallar(
                "El .md hace referencia a la imagen «%s» en %s, pero ese "
                "archivo no esta en la carpeta de trabajo. Revisa el nombre "
                "(mayusculas, extension) o agrega la imagen que falta."
                % (ref, contexto)
            )
        referenciadas.add(ref)
        return "/assets/imagenes/%s/%s" % (nombre_carpeta, ref)

    def reemplazar(patron, contexto, estricto):
        def _sub(m):
            original = m.group(2)
            nuevo = validar_simple(original, contexto, estricto)
            if nuevo is None:
                return m.group(0)
            cambios.append((contexto, original, nuevo))
            return m.group(1) + nuevo + m.group(3)
        return patron.sub(_sub, texto)

    texto = reemplazar(PATRON_IMG_TAG, "un <img>", True)
    texto = reemplazar(PATRON_MD_IMG, "una imagen en formato Markdown", True)
    texto = reemplazar(PATRON_FRONT_IMAGE, "el `image:` del front matter", False)

    return texto, cambios, referenciadas


def copiar_articulo(carpeta_trabajo, nombre_carpeta, nombre_md, imagenes, texto_final):
    destino_md = os.path.join(RAIZ, "_posts", nombre_md)
    ya_existia_md = os.path.exists(destino_md)
    with open(destino_md, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto_final)

    destino_imagenes = os.path.join(RAIZ, "assets", "imagenes", nombre_carpeta)
    os.makedirs(destino_imagenes, exist_ok=True)
    copiadas = []
    for imagen in imagenes:
        origen = os.path.join(carpeta_trabajo, imagen)
        destino = os.path.join(destino_imagenes, imagen)
        shutil.copyfile(origen, destino)
        copiadas.append(imagen)

    return destino_md, ya_existia_md, destino_imagenes, copiadas


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def ruta_git(ruta_absoluta):
    return os.path.relpath(ruta_absoluta, RAIZ).replace(os.sep, "/")


def confirmar_commit(nombre_carpeta, destino_md, destino_imagenes, copiadas):
    """Devuelve (mensaje_commit, error). Si no hay nada nuevo, (None, None)."""
    rutas_rel = [ruta_git(destino_md)] + [
        ruta_git(os.path.join(destino_imagenes, i)) for i in copiadas
    ]

    resultado_add = git("add", "--", *rutas_rel)
    if resultado_add.returncode != 0:
        return None, "`git add` fallo:\n%s" % (resultado_add.stderr or resultado_add.stdout)

    resultado_status = git("status", "--porcelain", "--", *rutas_rel)
    if not resultado_status.stdout.strip():
        return None, None

    mensaje = "Publica articulo: %s" % nombre_carpeta
    resultado_commit = git("commit", "-m", mensaje)
    if resultado_commit.returncode != 0:
        return None, "`git commit` fallo:\n%s" % (resultado_commit.stderr or resultado_commit.stdout)
    return mensaje, None


def imprimir_resumen(nombre_carpeta, nombre_md, destino_md, ya_existia_md,
                      destino_imagenes, copiadas, sin_referencia, cambios,
                      mensaje_commit, error_git):
    print("=" * 70)
    print("Articulo: %s" % nombre_carpeta)
    print("=" * 70)

    print("\n.md copiado:")
    sufijo = "  (sobrescribio uno que ya existia)" if ya_existia_md else ""
    print("  %s -> %s%s" % (nombre_md, ruta_git(destino_md), sufijo))

    print("\nImagenes copiadas a %s/:" % ruta_git(destino_imagenes))
    for imagen in copiadas:
        print("  %s" % imagen)

    if sin_referencia:
        print("\nAviso: estas imagenes se copiaron pero no se usan en el .md "
              "(ni en <img>, ni en Markdown, ni en el `image:` del front "
              "matter) -- revisa si hace falta:")
        for imagen in sorted(sin_referencia):
            print("  %s" % imagen)

    print("\nRutas reescritas dentro del .md:")
    if cambios:
        for contexto, original, nuevo in cambios:
            print("  %s: %s -> %s" % (contexto, original, nuevo))
    else:
        print("  (ninguna)")

    print("\nGit:")
    if error_git:
        print("  %s" % error_git)
        print("  Los archivos ya se copiaron y reescribieron igual -- "
              "revisa el error de git y hace el commit a mano.")
    elif mensaje_commit:
        print("  commit local creado: \"%s\"" % mensaje_commit)
        print("  (no se hizo push -- confirmalo vos a mano cuando quieras publicarlo)")
    else:
        print("  no se creo ningun commit nuevo (no habia cambios respecto "
              "de lo que ya estaba en el repo)")
    print()


def main():
    if len(sys.argv) != 2:
        print("Uso: python .github/scripts/publicar_articulo.py <carpeta-de-trabajo>")
        print("Ejemplo: python .github/scripts/publicar_articulo.py _posts/articulos/lavador-venturi")
        return 1

    try:
        carpeta, nombre_carpeta = resolver_carpeta(sys.argv[1])
        nombre_md = encontrar_md(carpeta, nombre_carpeta)
        imagenes = encontrar_imagenes(carpeta, nombre_carpeta)

        with open(os.path.join(carpeta, nombre_md), encoding="utf-8") as fh:
            texto = fh.read()

        texto_final, cambios, referenciadas = procesar_referencias(
            texto, nombre_carpeta, set(imagenes)
        )
        sin_referencia = set(imagenes) - referenciadas

        destino_md, ya_existia_md, destino_imagenes, copiadas = copiar_articulo(
            carpeta, nombre_carpeta, nombre_md, imagenes, texto_final
        )

        mensaje_commit, error_git = confirmar_commit(
            nombre_carpeta, destino_md, destino_imagenes, copiadas
        )

        imprimir_resumen(
            nombre_carpeta, nombre_md, destino_md, ya_existia_md,
            destino_imagenes, copiadas, sin_referencia, cambios,
            mensaje_commit, error_git,
        )
    except ErrorPublicacion as e:
        print("\nNo se publico nada -- hay que arreglar esto primero:\n")
        print("  " + str(e))
        print()
        return 1

    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
