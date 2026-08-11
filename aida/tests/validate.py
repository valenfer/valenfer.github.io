# -*- coding: utf-8 -*-
"""Validador del sitio estático AIDA · Nodo 20.

Usa exclusivamente la librería estándar de Python.
Ejecutar desde la raíz del repositorio:

    python aida/tests/validate.py
"""

import html.parser
import os
import posixpath
import re
import sys

AIDA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
RAIZ = os.path.normpath(os.path.join(AIDA, os.pardir))

BASE_URL = "https://valenfer.github.io/aida/"
ENLACE_X = "https://x.com/aida_asitente"

ARCHIVOS_ESPERADOS = [
    "index.html",
    "styles.css",
    "main.js",
    "cuaderno/index.html",
    "registros/una-ia-pequena.html",
    "registros/agentes-supervisados.html",
    "registros/privacidad-sin-aislamiento.html",
    "laboratorio.html",
    "proyectos.html",
    "acerca.html",
    "assets/favicon.svg",
    "README.md",
    "tests/validate.py",
    "assets/aida-retrato.jpg",
]

PAGINAS = [
    ("index.html", BASE_URL),
    ("cuaderno/index.html", BASE_URL + "cuaderno/"),
    ("registros/una-ia-pequena.html", BASE_URL + "registros/una-ia-pequena.html"),
    ("registros/agentes-supervisados.html", BASE_URL + "registros/agentes-supervisados.html"),
    ("registros/privacidad-sin-aislamiento.html", BASE_URL + "registros/privacidad-sin-aislamiento.html"),
    ("laboratorio.html", BASE_URL + "laboratorio.html"),
    ("proyectos.html", BASE_URL + "proyectos.html"),
    ("acerca.html", BASE_URL + "acerca.html"),
]

ERRORES = []


def error(mensaje):
    ERRORES.append(mensaje)


class Recolector(html.parser.HTMLParser):
    """Extrae enlaces, imágenes, recursos y atributos clave de un documento HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.enlaces = []
        self.imagenes = []
        self.recursos = []
        self.canonicas = []
        self.langs = []
        self.enlaces_x = []
        self.sospechosos_x = []
        self.imagenes_sin_alt = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            href = attrs.get("href")
            if href:
                self.enlaces.append(href)
                if href == ENLACE_X:
                    self.enlaces_x.append(href)
                if "x.com" in href or "twitter.com" in href:
                    self.sospechosos_x.append(href)
        elif tag == "img":
            src = attrs.get("src")
            alt = attrs.get("alt")
            if src:
                self.imagenes.append(src)
            if src and alt is None:
                self.imagenes_sin_alt.append(src)
        elif tag in ("link", "script"):
            clave = "href" if tag == "link" else "src"
            valor = attrs.get(clave)
            if valor:
                self.recursos.append(valor)
                if tag == "link" and "canonical" in (attrs.get("rel") or "").split():
                    self.canonicas.append(valor)
        elif tag == "html":
            self.langs.append(attrs.get("lang"))


def ruta_desde_aida(pagina_relativa):
    return os.path.normpath(os.path.join(AIDA, pagina_relativa.replace("/", os.sep)))


def resolver(pagina, destino):
    """Resuelve un enlace/recurso relativo desde una página hasta una ruta local."""
    rel = posixpath.normpath(posixpath.join(posixpath.dirname(pagina), destino))
    return ruta_desde_aida(rel)


def comprobar_archivos():
    for rel in ARCHIVOS_ESPERADOS:
        if not os.path.isfile(ruta_desde_aida(rel)):
            error("Falta el archivo esperado: {}".format(rel))


def comprobar_paginas():
    for pagina, canonical_esperada in PAGINAS:
        ruta = ruta_desde_aida(pagina)
        if not os.path.isfile(ruta):
            error("No existe la página: {}".format(pagina))
            continue

        with open(ruta, "r", encoding="utf-8") as fh:
            contenido = fh.read()

        for linea in contenido.splitlines():
            sin_urls = re.sub(r"(https?://[^\s\"'>]+|file:///[^\s\"'>]+)", "", linea)
            if re.search(r"[A-Za-z]:[\\/]", sin_urls):
                error("{}: posible ruta local absoluta en: {!r}".format(pagina, linea.strip()))

        recolector = Recolector()
        try:
            recolector.feed(contenido)
            recolector.close()
        except Exception as exc:  # noqa: BLE001
            error("{}: HTML no parseable: {}".format(pagina, exc))
            continue

        if not recolector.langs or recolector.langs[0] != "es":
            error("{}: lang no es 'es' (encontrado: {})".format(pagina, recolector.langs))

        if len(recolector.canonicas) != 1 or recolector.canonicas[0] != canonical_esperada:
            error("{}: canonical incorrecta (esperada {}, encontrada {})".format(
                pagina, canonical_esperada, recolector.canonicas))

        if not recolector.enlaces_x:
            error("{}: falta el enlace exacto a X ({})".format(pagina, ENLACE_X))
        for sospechoso in recolector.sospechosos_x:
            if sospechoso != ENLACE_X:
                error("{}: enlace a X con ortografía no exacta: {}".format(pagina, sospechoso))

        for img in recolector.imagenes:
            if img in recolector.imagenes_sin_alt:
                error("{}: imagen sin atributo alt: {}".format(pagina, img))
            if not img.startswith(("http://", "https://", "data:")):
                destino = resolver(pagina, img)
                if not os.path.isfile(destino):
                    error("{}: imagen no encontrada: {} (resuelta a {})".format(pagina, img, destino))

        for rec in recolector.recursos:
            if rec.startswith(("http://", "https://", "//", "data:")):
                continue
            destino = resolver(pagina, rec)
            if not os.path.isfile(destino):
                error("{}: recurso no encontrado: {} (resuelto a {})".format(pagina, rec, destino))

        for enl in recolector.enlaces:
            if enl.startswith(("#", "http://", "https://", "//", "mailto:", "tel:")):
                continue
            destino = resolver(pagina, enl)
            if not os.path.isfile(destino) and not os.path.isdir(destino):
                error("{}: enlace roto: {} (resuelto a {})".format(pagina, enl, destino))


def main():
    if os.path.normpath(os.getcwd()) != RAIZ:
        print("Advertencia: ejecuta el validador desde la raíz del repositorio.")
        print("  python aida/tests/validate.py")

    comprobar_archivos()
    comprobar_paginas()

    if ERRORES:
        print("Se encontraron {} problema(s):".format(len(ERRORES)))
        for e in ERRORES:
            print(" - " + e)
        return 1

    print("OK: todos los archivos, enlaces, recursos y metadatos son válidos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
