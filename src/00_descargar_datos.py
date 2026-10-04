"""Descarga y descomprime en data/raw/ los ZIP indicados en urls.txt."""
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
            print(f"  Falló la descarga ({e}). El archivo se puede obtener desde la página del INEC.")
            continue
        if zipfile.is_zipfile(destino):
            carpeta = config.DATOS_CRUDOS / destino.stem
            with zipfile.ZipFile(destino) as z:
                z.extractall(carpeta)
            print(f"  Descomprimido en {carpeta}")
    print("\nDescarga finalizada. Los archivos se guardaron en data/raw/.")


if __name__ == "__main__":
    main()
