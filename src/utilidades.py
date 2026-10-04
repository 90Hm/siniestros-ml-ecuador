"""Funciones compartidas por todos los scripts."""
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import config


# ----------------------------------------------------------------------------
# Texto y nombres de columnas
# ----------------------------------------------------------------------------
def quitar_tildes(texto):
    return unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()


def normalizar_nombre(texto):
    """'Núm. Fallecidos In Situ' -> 'num_fallecidos_in_situ'."""
    t = quitar_tildes(texto).strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")


def normalizar_valor(texto):
    """Mayúsculas, sin tildes y sin espacios sobrantes, para comparar categorías."""
    return re.sub(r"\s+", " ", quitar_tildes(texto).strip().upper())


def _periodo_trimestral(nombre):
    nombre = normalizar_nombre(Path(nombre).stem)
    anio = re.search(r"^((?:19|20)\d{2})_", nombre)
    trimestre = re.search(r"_(iv|iii|ii|i)(?:trimestre|trim|t)(?:_|$)", nombre)
    if not anio or not trimestre:
        return None
    numero = {"i": 1, "ii": 2, "iii": 3, "iv": 4}[trimestre.group(1)]
    return int(anio.group(1)), numero


# ----------------------------------------------------------------------------
# Lectura de archivos
# ----------------------------------------------------------------------------
def _detectar_formato(ruta):
    """Prueba combinaciones de codificación y separador hasta que una funcione."""
    for enc in ("utf-8-sig", "latin-1"):
        for sep in (";", ",", "|", "\t"):
            try:
                muestra = pd.read_csv(ruta, sep=sep, encoding=enc, nrows=50)
                if muestra.shape[1] > 3:
                    return enc, sep
            except Exception:
                continue
    raise ValueError(f"No se pudo detectar el formato de {ruta}")


def cargar_datos(directorio=None):
    """Lee el trimestre configurado por año, normaliza nombres y apila los cortes."""
    directorio = Path(directorio or config.DATOS_CRUDOS)
    omitir = ("tabulad", "diccionario", "sintaxis")
    archivos = [
        a for a in sorted(directorio.rglob("*"))
        if a.is_file() and a.suffix.lower() == ".csv"
        and not any(p in a.name.lower() for p in omitir)
    ]
    if not archivos:
        raise FileNotFoundError(
            f"No hay archivos CSV en {directorio}. Descargue las bases de datos "
            "abiertas del INEC y colóquelas ahí (ver README)."
        )
    periodos = {archivo: _periodo_trimestral(archivo.name) for archivo in archivos}
    if any(periodos.values()):
        if not all(periodos.values()):
            raise ValueError("Mezcla de CSV trimestrales y archivos sin periodo reconocible en el mismo directorio.")
        anios = sorted({periodo[0] for periodo in periodos.values()})
        seleccionados = [
            archivo for archivo in archivos
            if periodos[archivo][1] == config.TRIMESTRE_ANALISIS
        ]
        anios_seleccionados = {periodos[archivo][0] for archivo in seleccionados}
        if anios_seleccionados != set(anios):
            raise ValueError(
                f"No hay un CSV del trimestre {config.TRIMESTRE_ANALISIS} para cada año."
            )
        archivos = seleccionados
        print(f"Usando el corte del trimestre {config.TRIMESTRE_ANALISIS} para cada año: "
              f"{', '.join(str(anio) for anio in anios)}")
    partes = []
    for archivo in archivos:
        enc, sep = _detectar_formato(archivo)
        df = pd.read_csv(archivo, sep=sep, encoding=enc, low_memory=False)
        df.columns = [normalizar_nombre(c) for c in df.columns]
        periodo = periodos[archivo]
        if periodo and "anio" not in df.columns:
            df["anio"] = periodo[0]
        df["archivo_origen"] = archivo.name
        partes.append(df)
        print(f"  Leído {archivo.name}: {len(df):,} filas, {df.shape[1]} columnas")
    return pd.concat(partes, ignore_index=True, sort=False)


# ----------------------------------------------------------------------------
# Detección de columnas
# ----------------------------------------------------------------------------
def detectar_columnas(df):
    """Devuelve {variable_logica: nombre_de_columna o None}."""
    encontradas = {}
    for clave, patrones in config.PATRONES.items():
        encontradas[clave] = None
        for patron in patrones:
            coincide = [c for c in df.columns if re.search(patron, c)]
            if coincide:
                encontradas[clave] = coincide[0]
                break
    encontradas.update(config.MAPEO_MANUAL)
    return encontradas


def guardar_mapeo(cols):
    tabla = pd.DataFrame({"variable_logica": list(cols), "columna_detectada": list(cols.values())})
    tabla.to_csv(config.TABLAS / "mapeo_columnas.csv", index=False)
    print("\nMapeo de columnas detectado")
    for k, v in cols.items():
        print(f"  {k:<11} -> {v}")
    print("  Si alguna está mal o falta, corríjala en MAPEO_MANUAL de config.py\n")


# ----------------------------------------------------------------------------
# Hora y calendario
# ----------------------------------------------------------------------------
def extraer_hora(serie):
    """Devuelve la hora entera 0-23 a partir de '14:30', '1430', '14', o fechas con hora."""
    def convertir(valor):
        if pd.isna(valor):
            return np.nan
        s = str(valor).strip()
        m = re.search(r"(?<!\d)(\d{1,2})\s*[:h]\s*(\d{1,2})", s)
        if m:
            h = int(m.group(1))
        elif re.fullmatch(r"\d{3,4}", s):
            h = int(s) // 100
        elif re.fullmatch(r"\d{1,2}(\.0+)?", s):
            h = int(float(s))
        else:
            return np.nan
        return float(h) if 0 <= h <= 23 else np.nan
    return serie.map(convertir)


MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}
DIAS_SEMANA = {
    "lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4,
    "sabado": 5, "domingo": 6,
}
NOMBRES_DIA = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


def _mes_a_numero(serie):
    num = pd.to_numeric(serie, errors="coerce")
    nombres = serie.astype(str).map(lambda x: MESES.get(quitar_tildes(x).strip().lower(), np.nan))
    return num.fillna(nombres)


def derivar_calendario(df, cols):
    """Devuelve (mes, dia_semana 0-6) usando la fecha o la combinación año, mes y día."""
    mes = pd.Series(np.nan, index=df.index)
    dia_semana = pd.Series(np.nan, index=df.index)

    if cols.get("fecha"):
        fecha = pd.to_datetime(df[cols["fecha"]], errors="coerce", dayfirst=True)
        if fecha.notna().mean() > 0.5:
            return fecha.dt.month.astype(float), fecha.dt.dayofweek.astype(float)

    if cols.get("mes"):
        mes = _mes_a_numero(df[cols["mes"]]).astype(float)

    if cols.get("dia"):
        crudo = df[cols["dia"]].astype(str).map(lambda x: quitar_tildes(x).strip().lower())
        por_nombre = crudo.map(DIAS_SEMANA)
        if por_nombre.notna().mean() > 0.5:
            dia_semana = por_nombre.astype(float)
        else:
            por_codigo = pd.to_numeric(df[cols["dia"]], errors="coerce")
            if por_codigo.notna().mean() > 0.5 and por_codigo.dropna().between(1, 7).all():
                dia_semana = (por_codigo - 1).astype(float)
            elif cols.get("anio") and cols.get("mes"):
                fecha = pd.to_datetime(
                    {
                        "year": pd.to_numeric(df[cols["anio"]], errors="coerce"),
                        "month": mes,
                        "day": pd.to_numeric(df[cols["dia"]], errors="coerce"),
                    },
                    errors="coerce",
                )
                dia_semana = fecha.dt.dayofweek.astype(float)
    return mes, dia_semana


def franja_horaria(hora):
    """Madrugada 0-5, mañana 6-11, tarde 12-17, noche 18-23."""
    return pd.cut(
        hora, bins=[-1, 5, 11, 17, 23],
        labels=["madrugada", "manana", "tarde", "noche"],
    ).astype("object")


# ----------------------------------------------------------------------------
# Preprocesador para los modelos
# ----------------------------------------------------------------------------
def construir_preprocesador(columnas_num, columnas_cat):
    """Escala las numéricas y codifica en one-hot las categóricas.

    Va dentro del Pipeline de cada modelo, así en la validación cruzada
    se ajusta solo con los datos de entrenamiento de cada partición.
    """
    try:
        codificador = OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20, sparse_output=False)
    except TypeError:  # versiones antiguas de scikit-learn
        codificador = OneHotEncoder(handle_unknown="ignore", sparse=False)
    numerico = Pipeline(
        [
            ("imputar", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("escalar", StandardScaler()),
        ]
    )
    categorico = Pipeline(
        [
            ("imputar", SimpleImputer(strategy="constant", fill_value="SIN_DATO")),
            ("codificar", codificador),
        ]
    )
    return ColumnTransformer(
        [
            ("num", numerico, columnas_num),
            ("cat", categorico, columnas_cat),
        ]
    )


def cargar_procesados():
    """Lee la tabla procesada y la lista de variables que dejó el paso 2."""
    ruta = config.DATOS_PROCESADOS / "siniestros_modelado.csv"
    if not ruta.exists():
        raise FileNotFoundError("Falta data/processed/siniestros_modelado.csv. Ejecute antes 02_preprocesamiento.py")
    datos = pd.read_csv(ruta)
    variables = pd.read_csv(config.TABLAS / "features_utilizadas.csv")
    num = variables.loc[variables["tipo"] == "numerica", "variable"].tolist()
    cat = variables.loc[variables["tipo"] == "categorica", "variable"].tolist()
    return datos, num, cat
