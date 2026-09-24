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
  5. antes de comitear, hace `git fetch origin` + `git rebase origin/main`
     para traer cualquier cambio que haya en el remoto (otra publicacion,
     una edicion en github.com) y evitar el rechazo "rejected... fetch
     first" mas adelante -- si el rebase no se puede aplicar solo (conflicto
     real), aborta y para sin comitear nada, nunca fuerza nada;
  6. hace `git add` + `git commit` local de los archivos nuevos -- nunca
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
import struct
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


PATRON_IMG_COMPLETO = re.compile(r'<img\b[^>]*>')


def _dimensiones_jpeg(fh):
    fh.seek(2)
    while True:
        byte = fh.read(1)
        while byte and byte != b"\xff":
            byte = fh.read(1)
        marcador = fh.read(1)
        while marcador == b"\xff":
            marcador = fh.read(1)
        if not marcador:
            return None
        codigo = marcador[0]
        # SOF0-SOF15 son los que traen las medidas; 0xC4/0xC8/0xCC en ese
        # rango son tablas Huffman y extensiones, no cabeceras de imagen.
        if 0xC0 <= codigo <= 0xCF and codigo not in (0xC4, 0xC8, 0xCC):
            datos = fh.read(7)
            if len(datos) < 7:
                return None
            alto, ancho = struct.unpack(">HH", datos[3:7])
            return ancho, alto
        largo_bytes = fh.read(2)
        if len(largo_bytes) < 2:
            return None
        largo = struct.unpack(">H", largo_bytes)[0]
        if largo < 2:
            return None
        fh.seek(largo - 2, 1)


def dimensiones_imagen(ruta):
    """(ancho, alto) de una imagen, leyendo solo su cabecera -- sin Pillow ni
    ninguna otra dependencia, porque ni el runner de GitHub Actions ni la
    maquina de Elvis tienen nada instalado mas alla de la libreria estandar.

    Cubre PNG, JPEG y GIF, que es lo que usan todos los articulos. Un .webp o
    un .svg devuelven None: esos siguen recibiendo loading="lazy" igual, solo
    se quedan sin las medidas."""
    try:
        with open(ruta, "rb") as fh:
            cabecera = fh.read(32)
            if cabecera[:8] == b"\x89PNG\r\n\x1a\n" and len(cabecera) >= 24:
                return struct.unpack(">II", cabecera[16:24])
            if cabecera[:6] in (b"GIF87a", b"GIF89a") and len(cabecera) >= 10:
                return struct.unpack("<HH", cabecera[6:10])
            if cabecera[:2] == b"\xff\xd8":
                return _dimensiones_jpeg(fh)
    except (OSError, struct.error):
        return None
    return None


def _ruta_local_de_imagen(src, carpeta_origen):
    """La imagen puede estar en la carpeta de trabajo (al publicar, cuando
    todavia no se copio a assets/) o ya publicada bajo la raiz del repo (al
    reprocesar un articulo existente). Se prueban las dos."""
    limpio = src.split("?")[0].split("#")[0]
    candidatas = []
    if carpeta_origen:
        candidatas.append(os.path.join(carpeta_origen, os.path.basename(limpio)))
    if limpio.startswith("/"):
        candidatas.append(os.path.join(RAIZ, limpio.lstrip("/").replace("/", os.sep)))
    for candidata in candidatas:
        if os.path.isfile(candidata):
            return candidata
    return None


def enriquecer_imagenes(texto, carpeta_origen=None):
    """Agrega a cada <img> del cuerpo lo que el navegador necesita para no
    trabajar de mas:

      - loading="lazy": la imagen se baja recien cuando esta por entrar en
        pantalla. Antes se bajaban todas al abrir el articulo, aunque el
        lector no llegara nunca al final.
      - decoding="async": decodificarla no frena el dibujado del texto.
      - width/height reales: el navegador le reserva el lugar exacto desde el
        principio y el texto deja de pegar saltos mientras carga. El CSS
        (.post-body img { max-width: 100% }) sigue mandando sobre el tamano
        que se ve; estos dos atributos solo declaran la proporcion.

    Nunca pisa un atributo que ya este escrito en la etiqueta, y no toca las
    imagenes externas (http, https, data:)."""
    def _sub(m):
        tag = m.group(0)
        m_src = re.search(r'src="([^"]+)"', tag)
        if not m_src:
            return tag
        src = m_src.group(1)
        if src.startswith(("http://", "https://", "//", "data:")):
            return tag

        atributos = ""
        if "loading=" not in tag:
            atributos += ' loading="lazy"'
        if "decoding=" not in tag:
            atributos += ' decoding="async"'
        if "width=" not in tag and "height=" not in tag:
            ruta = _ruta_local_de_imagen(src, carpeta_origen)
            medidas = dimensiones_imagen(ruta) if ruta else None
            if medidas:
                atributos += ' width="%d" height="%d"' % medidas
        # Convencion de nombre: una imagen llamada `infografia-*.jpg` es un
        # esquema con texto adentro, que en celular no hay que achicar al
        # ancho de la columna (ver la nota de .infografia en styles.css).
        # Asi se marca sin tocar el HTML del articulo; la otra via es
        # escribir class="infografia" a mano en el <img>.
        tag_final = tag
        if os.path.basename(src).lower().startswith("infografia-"):
            m_clase = re.search(r'class="([^"]*)"', tag_final)
            if m_clase is None:
                atributos += ' class="infografia"'
            elif "infografia" not in m_clase.group(1).split():
                # Ya tiene clases: se suma a las que estan, nunca se agrega un
                # segundo atributo class (el navegador ignoraria el segundo).
                tag_final = (tag_final[:m_clase.start(1)]
                             + (m_clase.group(1) + " infografia").strip()
                             + tag_final[m_clase.end(1):])

        if not atributos:
            return tag_final

        cuerpo = tag_final[:-1].rstrip()
        cierre = ">"
        if cuerpo.endswith("/"):          # <img ... /> autocerrada
            cuerpo = cuerpo[:-1].rstrip()
            cierre = " />"
        return cuerpo + atributos + cierre

    return PATRON_IMG_COMPLETO.sub(_sub, texto)


def quitar_tags_pendientes(texto):
    """`tags:` es OPCIONAL, a diferencia de excerpt/image: el panel lo crea
    como `tags: [PENDIENTE]` y puede quedar asi si el articulo no comparte
    tema con ningun otro. Esta funcion saca ese PENDIENTE de la copia que se
    publica -- nunca del .md de la carpeta de trabajo -- antes de
    verificar_sin_pendientes, asi que no bloquea la publicacion y nunca
    llega al sitio (ni a "Sugeridos" ni al feed, que publica los tags).

    Solo toca una linea `tags:` del front matter que contenga PENDIENTE:
    `tags: [PENDIENTE]` (o `tags: PENDIENTE`) se borra entera; si ademas trae
    temas reales (`tags: [Agua potable, PENDIENTE]`) quedan solo esos. Una
    linea `tags:` sin PENDIENTE queda exactamente igual. Respeta CRLF."""
    if not texto.startswith("---"):
        return texto
    fin = texto.find("\n---", 3)
    if fin == -1:
        return texto
    lineas = texto[:fin].splitlines(keepends=True)
    salida = []
    for linea in lineas:
        cuerpo = linea.rstrip("\r\n")
        fin_linea = linea[len(cuerpo):]
        m = re.match(r"^tags:[ \t]*(.*?)[ \t]*$", cuerpo)
        if not m:
            salida.append(linea)
            continue
        valor = m.group(1)
        if valor.startswith("[") and valor.endswith("]"):
            valor = valor[1:-1]
        temas = [t.strip().strip("\"'").strip() for t in valor.split(",")]
        # Solo el marcador exacto: un tema real como "Pendientes andinas"
        # no es un PENDIENTE, y en ese caso la linea queda intacta.
        if not any(t.upper() == "PENDIENTE" for t in temas):
            salida.append(linea)
            continue
        temas = [t for t in temas if t and t.upper() != "PENDIENTE"]
        if temas:
            salida.append("tags: [%s]%s" % (", ".join(temas), fin_linea))
        # sin temas reales: la linea se borra entera
    return "".join(salida) + texto[fin:]


def verificar_sin_pendientes(texto, nombre_carpeta):
    """El panel de control crea la carpeta de trabajo con campos PENDIENTE
    en el front matter (excerpt, image) para que Elvis los complete con lo
    que entregue NotebookLM. Publicar con alguno sin completar dejaria un
    articulo a medias en el sitio real. El `tags: [PENDIENTE]` opcional no
    llega aca: quitar_tags_pendientes() lo saca antes."""
    if "PENDIENTE" not in texto:
        return
    lineas = [
        str(n) for n, linea in enumerate(texto.split("\n"), 1) if "PENDIENTE" in linea
    ]
    fallar(
        "El articulo de «%s» todavia tiene campos sin completar (PENDIENTE) "
        "-- revisalo antes de publicar. Lineas: %s"
        % (nombre_carpeta, ", ".join(lineas))
    )


def copiar_articulo(carpeta_trabajo, nombre_carpeta, nombre_md, imagenes, texto_final,
                    al_escribir=None):
    """al_escribir(ruta), si se pasa, se llama con cada archivo destino que
    quedo tocado en disco -- tambien el que fallo a mitad de escribirse --
    para que quien llama (el panel) pueda deshacer una copia parcial. Si una
    imagen falla, el .md ya esta en _posts/ y las anteriores ya se copiaron."""
    def _tocado(ruta):
        if al_escribir and os.path.exists(ruta):
            al_escribir(ruta)

    destino_md = os.path.join(RAIZ, "_posts", nombre_md)
    ya_existia_md = os.path.exists(destino_md)
    try:
        with open(destino_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texto_final)
    finally:
        _tocado(destino_md)

    destino_imagenes = os.path.join(RAIZ, "assets", "imagenes", nombre_carpeta)
    os.makedirs(destino_imagenes, exist_ok=True)
    copiadas = []
    for imagen in imagenes:
        origen = os.path.join(carpeta_trabajo, imagen)
        destino = os.path.join(destino_imagenes, imagen)
        try:
            shutil.copyfile(origen, destino)
        finally:
            _tocado(destino)
        copiadas.append(imagen)

    return destino_md, ya_existia_md, destino_imagenes, copiadas


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def ruta_git(ruta_absoluta):
    return os.path.relpath(ruta_absoluta, RAIZ).replace(os.sep, "/")


def sincronizar_con_remoto():
    """Trae los commits nuevos de origin/main y los combina con la rama local.
    Sin esto, un `git push` automatico (el del panel de control) puede chocar
    con "rejected... fetch first" si origin avanzo mientras tanto -- otra
    publicacion, un borrado, una edicion desde el editor web de github.com.
    Devuelve None si quedo al dia, o un mensaje de error listo para mostrar si
    el rebase no se pudo aplicar solo.

    El rebase solo se ejecuta si origin/main de verdad trae commits nuevos.
    Antes se corria siempre, y eso rompia toda republicacion de un articulo ya
    publicado: `git rebase` exige el arbol de trabajo limpio y se niega a
    arrancar (`cannot rebase: You have unstaged changes`) aunque no haya nada
    que traer -- y en una republicacion el .md ya trackeado esta modificado
    justo por la copia que acaba de hacer el panel. Resultado: el flujo fallaba
    siempre, con un mensaje que culpaba a "cambios ajenos a este articulo".

    Nunca fuerza nada: si hay un conflicto real de contenido, aborta el
    rebase y para antes de tocar el commit -- jamas `--force`/`--force-with-lease`,
    eso lo resuelve Elvis a mano.
    """
    resultado_fetch = git("fetch", "origin")
    if resultado_fetch.returncode != 0:
        return "`git fetch origin` fallo:\n%s" % (resultado_fetch.stderr or resultado_fetch.stdout)

    resultado_cuenta = git("rev-list", "--count", "HEAD..origin/main")
    if resultado_cuenta.returncode == 0 and resultado_cuenta.stdout.strip() == "0":
        # Nada que traer: no se toca el arbol de trabajo ni se corre rebase.
        return None

    resultado_rebase = git("rebase", "origin/main")
    if resultado_rebase.returncode != 0:
        salida = resultado_rebase.stderr or resultado_rebase.stdout
        if "cannot rebase" in salida and (
            "unstaged changes" in salida or "uncommitted changes" in salida
        ):
            # El rebase ni siquiera arranco: hay cambios sin comitear en la
            # copia local y origin/main SI trae commits nuevos que hay que
            # combinar. No es un conflicto de contenido real.
            return (
                "origin/main trae commits nuevos, pero no se pueden combinar "
                "porque hay cambios sin comitear en la copia local (revisa "
                "`git status` en la terminal). Comitealos, guardalos con "
                "`git stash` o descartalos, y volve a intentar publicar.\n\n%s"
                % salida
            )
        git("rebase", "--abort")
        return (
            "origin/main tiene commits que tu copia local no tenia todavia "
            "(otra publicacion, un borrado, una edicion en github.com) y no "
            "se pudieron combinar solos -- probable conflicto real de "
            "contenido.\nResuelvelo a mano en la terminal: `git fetch origin` "
            "y despues `git rebase origin/main` (o `git pull --rebase origin "
            "main`), arregla los archivos en conflicto, y volve a intentar "
            "publicar.\n\n%s" % salida
        )
    return None


def confirmar_commit(nombre_carpeta, destino_md, destino_imagenes, copiadas):
    """Devuelve (mensaje_commit, error). Si no hay nada nuevo, (None, None).

    Orden: primero el commit, despues la sincronizacion con origin. Al reves
    -- como estaba antes -- el rebase se topaba con el .md recien copiado
    todavia sin comitear y se negaba a arrancar. Con el commit hecho primero
    el arbol queda limpio y el rebase hace justo lo que tiene que hacer:
    apoyar ese commit arriba de lo que haya en origin/main. Si el rebase
    falla, el commit local ya existe y no se pierde nada -- queda sin pushear
    hasta que Elvis resuelva el conflicto a mano.
    """
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

    error_sync = sincronizar_con_remoto()
    if error_sync:
        return None, (
            "El commit local ya se creo (\"%s\"), pero no se pudo sincronizar "
            "con origin/main, asi que NO se hizo push. Tu trabajo esta a "
            "salvo en ese commit.\n\n%s" % (mensaje, error_sync)
        )
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

        texto = quitar_tags_pendientes(texto)
        verificar_sin_pendientes(texto, nombre_carpeta)

        texto_final, cambios, referenciadas = procesar_referencias(
            texto, nombre_carpeta, set(imagenes)
        )
        texto_final = enriquecer_imagenes(texto_final, carpeta)
        sin_referencia = set(imagenes) - referenciadas

        # Sincronizar ANTES de escribir nada: aca el arbol de trabajo todavia
        # esta limpio, que es lo que `git rebase` necesita. Si origin/main
        # avanzo, se combina ahora; si algo falla, no se copio ningun archivo
        # todavia y no hay nada que deshacer.
        error_sync = sincronizar_con_remoto()
        if error_sync:
            fallar(error_sync)

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
