"""Paso 2. Limpieza, transformación y generación de variables.

Deja en data/processed/siniestros_modelado.csv la tabla lista para modelar y
en outputs/tablas/ el registro de cada transformación aplicada.
"""
import re

import numpy as np
import pandas as pd

import config
from utilidades import (
    cargar_datos, derivar_calendario, detectar_columnas, extraer_hora,
    franja_horaria, guardar_mapeo, NOMBRES_DIA, normalizar_valor,
)


def main():
    registro = []  # bitácora de transformaciones para el informe

    def anotar(paso, detalle, afectados):
        registro.append({"paso": paso, "detalle": detalle, "registros_o_columnas_afectados": afectados})
        print(f"  [{paso}] {detalle}: {afectados}")

    print("Cargando datos...")
    df = cargar_datos()
    cols = detectar_columnas(df)
    guardar_mapeo(cols)

    if not cols["fallecidos"]:
        raise SystemExit("No se encontró la columna de fallecidos. Defínala en MAPEO_MANUAL (config.py).")

    anotar("carga", "registros iniciales", len(df))

    # ------------------------------------------------ 1. texto y datos faltantes
    texto = [c for c in df.select_dtypes(exclude="number").columns if c != "archivo_origen"]
    for c in texto:
        df[c] = df[c].map(lambda v: normalizar_valor(v) if pd.notna(v) else np.nan)
        df[c] = df[c].where(~df[c].isin(config.VALORES_FALTANTES), np.nan)
    anotar("limpieza de texto", "columnas de texto en mayúsculas, sin tildes y con faltantes unificados", len(texto))

    # --------------------------------------------------------------- 2. duplicados
    sin_origen = [c for c in df.columns if c != "archivo_origen"]
    n_dup = int(df.duplicated(subset=sin_origen).sum())
    anotar(
        "duplicados",
        "filas idénticas contabilizadas y conservadas porque no hay ID único para confirmar duplicados",
        n_dup,
    )

    # ------------------------------------------------------------ 3. variable objetivo
    fallecidos = pd.to_numeric(df[cols["fallecidos"]], errors="coerce")
    sin_etiqueta = int(fallecidos.isna().sum())
    df = df.loc[fallecidos.notna()].reset_index(drop=True)
    fallecidos = fallecidos.loc[fallecidos.notna()].reset_index(drop=True)
    anotar("objetivo", "registros sin dato de fallecidos eliminados", sin_etiqueta)
    y = (fallecidos > 0).astype(int)
    anotar("objetivo", "siniestros con al menos un fallecido en el lugar", int(y.sum()))

    # ------------------------------------------------ 4. variables derivadas
    X = pd.DataFrame(index=df.index)

    if cols["hora"]:
        hora = extraer_hora(df[cols["hora"]])
        nulos_hora = int(hora.isna().sum())
        X["hora_num"] = hora
        X["franja_horaria"] = franja_horaria(hora)
        hora_pico = (hora.between(7, 9) | hora.between(17, 19)).astype(float)
        X["hora_pico"] = hora_pico.where(hora.notna(), np.nan)
        anotar("feature engineering", "hora_num, franja_horaria y hora_pico creadas; los nulos se imputarán en el pipeline", nulos_hora)

    mes, dia_semana = derivar_calendario(df, cols)
    if mes.notna().any():
        X["mes"] = mes
    if dia_semana.notna().any():
        X["dia_semana"] = dia_semana.map(
            lambda i: NOMBRES_DIA[int(i)] if pd.notna(i) else "SIN_DATO"
        )
        fin_de_semana = (dia_semana >= 5).astype(float)
        viernes_a_domingo = (dia_semana >= 4).astype(float)
        X["fin_de_semana"] = fin_de_semana.where(dia_semana.notna(), np.nan)
        X["viernes_a_domingo"] = viernes_a_domingo.where(dia_semana.notna(), np.nan)
        anotar("feature engineering", "dia_semana, fin_de_semana y viernes_a_domingo creadas", len(X))

    if cols["provincia"]:
        provincia_cruda = df[cols["provincia"]]
        provincia_codigo = pd.to_numeric(provincia_cruda, errors="coerce")
        provincia_nombre = provincia_codigo.map(config.CODIGOS_PROVINCIA)
        provincia_texto = provincia_cruda.map(
            lambda valor: normalizar_valor(valor) if pd.notna(valor) else np.nan
        )
        X["provincia"] = provincia_nombre.fillna(provincia_texto).fillna("SIN_DATO")
        X["es_amazonia"] = X["provincia"].isin(config.PROVINCIAS_AMAZONIA).astype(int)
        anotar("feature engineering", "es_amazonia creada a partir de la provincia", int(X["es_amazonia"].sum()))

    for clave in ("zona", "clase", "causa"):
        if cols[clave]:
            X[clave] = df[cols[clave]].astype("string").fillna("SIN_DATO")

    # ---- variables adicionales detectadas automáticamente (revisar el resultado)
    ya_usadas = {cols[k] for k in ("fallecidos", "lesionados", "fecha", "anio", "mes", "dia", "hora",
                                   "provincia", "zona", "clase", "causa") if cols[k]}
    excluir = [re.compile(p) for p in config.EXCLUIR_COMO_FEATURE]
    extras_cat, extras_num = [], []
    for c in df.columns:
        if c in ya_usadas or c in X.columns or any(p.search(c) for p in excluir):
            continue
        if df[c].isna().mean() > 0.60:
            continue
        if df[c].dtype == object or str(df[c].dtype) in ("string", "str"):
            if df[c].nunique() <= config.MAX_CATEGORIAS:
                extras_cat.append(c)
        elif df[c].nunique() > 1:
            extras_num.append(c)
    for c in config.CATEGORICAS_EXTRA:
        if c in df.columns and c not in extras_cat and c not in X.columns:
            extras_cat.append(c)
    for c in extras_cat:
        X[c] = df[c].fillna("SIN_DATO")
    for c in extras_num:
        X[c] = pd.to_numeric(df[c], errors="coerce")
    if extras_cat or extras_num:
        anotar("variables adicionales", "incluidas automáticamente, revisar features_utilizadas.csv", len(extras_cat) + len(extras_num))

    # ------------------------------------------------------ 5. tipos y resultado
    categoricas = [c for c in X.columns if X[c].dtype == object or str(X[c].dtype) in ("string", "str")]
    numericas = [c for c in X.columns if c not in categoricas]

    tabla_vars = pd.DataFrame(
        [{"variable": c, "tipo": "categorica"} for c in categoricas]
        + [{"variable": c, "tipo": "numerica"} for c in numericas]
    )
    tabla_vars.to_csv(config.TABLAS / "features_utilizadas.csv", index=False)

    salida = X.copy()
    salida["objetivo_fallecidos"] = y.values
    salida.to_csv(config.DATOS_PROCESADOS / "siniestros_modelado.csv", index=False)
    pd.DataFrame(registro).to_csv(config.TABLAS / "bitacora_preprocesamiento.csv", index=False)

    print(f"\nRegistros finales: {len(salida):,}")
    print(f"Variables numéricas ({len(numericas)}): {numericas}")
    print(f"Variables categóricas ({len(categoricas)}): {categoricas}")
    print(f"Porcentaje de la clase positiva: {y.mean() * 100:.2f} %")
    print("\nREVISE features_utilizadas.csv. Si aparece una variable que revele el resultado "
          "(por ejemplo, algo derivado de víctimas), agregue su patrón a EXCLUIR_COMO_FEATURE.")


if __name__ == "__main__":
    main()
