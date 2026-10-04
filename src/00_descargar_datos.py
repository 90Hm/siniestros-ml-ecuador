"""Paso 0. Descarga y descomprime las bases de datos abiertas del INEC.

Lee las direcciones de urls.txt (una por línea, las que empiezan con # se
ignoran), descarga cada archivo ZIP en data/raw/ y lo descomprime.

Este script se ejecuta en su computador. Si alguna descarga falla, baje el ZIP
a mano desde la página del INEC y descomprímalo en data/raw/.
"""
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import config

ARCHIVO_URLS = config.RAIZ / "urls.txt"


def main():
    if not ARCHIVO_URLS.exists():
        raise SystemExit(f"No existe {ARCHIVO_URLS}")
    urls = [l.strip() for l in ARCHIVO_URLS.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith("#")]
    if not urls:
        raise SystemExit("urls.txt no tiene direcciones. Agregue al menos una.")

    for url in urls:
        nombre = Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).name
        destino = config.DATOS_CRUDOS / nombre
        seguro = urllib.parse.quote(url, safe=":/?=&%")
        print(f"Descargando {nombre} ...")
        try:
            req = urllib.request.Request(seguro, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r, open(destino, "wb") as f:
                f.write(r.read())
        except Exception as e:
            print(f"  No se pudo descargar ({e}). Descárguelo a mano desde la página del INEC.")
            continue
        if zipfile.is_zipfile(destino):
            carpeta = config.DATOS_CRUDOS / destino.stem
            with zipfile.ZipFile(destino) as z:
                z.extractall(carpeta)
            print(f"  Descomprimido en {carpeta}")
    print("\nListo. Revise que en data/raw/ estén solo las bases de datos abiertas (CSV).")


if __name__ == "__main__":
    main()
