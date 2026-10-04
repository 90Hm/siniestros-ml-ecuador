"""Paso 1. Exploración de los datos.

Genera estadísticas descriptivas, porcentaje de nulos por variable, duplicados,
valores atípicos y las visualizaciones que pide la guía.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
from utilidades import (
    cargar_datos, derivar_calendario, detectar_columnas, extraer_hora,
    guardar_mapeo, NOMBRES_DIA, normalizar_valor,
)


def guardar_fig(nombre):
    plt.tight_layout()
    plt.savefig(config.FIGURAS / nombre, dpi=150)
    plt.close()


def main():
    print("Cargando datos...")
    df = cargar_datos()
    cols = detectar_columnas(df)
    guardar_mapeo(cols)

    n_filas, n_cols = df.drop(columns=["archivo_origen"]).shape
    print(f"Registros: {n_filas:,} | Variables: {n_cols}")
    if n_filas < 1000 or n_cols < 5:
        print("ADVERTENCIA: la guía exige al menos 1000 registros y 5 variables.")
    pd.DataFrame(
        {"indicador": ["registros", "variables", "archivos_leidos"],
         "valor": [n_filas, n_cols, df["archivo_origen"].nunique()]}
    ).to_csv(config.TABLAS / "dimensiones.csv", index=False)

    datos = df.drop(columns=["archivo_origen"])

    numericas = datos.select_dtypes(include="number")
    if not numericas.empty:
        numericas.describe().T.round(3).to_csv(config.TABLAS / "estadisticas_numericas.csv")
    categoricas = datos.select_dtypes(exclude="number")
    if not categoricas.empty:
        resumen = pd.DataFrame({
            "distintos": categoricas.nunique(),
            "mas_frecuente": categoricas.mode().iloc[0],
            "frecuencia": categoricas.apply(lambda s: s.value_counts().iloc[0] if s.notna().any() else 0),
        })
        resumen.to_csv(config.TABLAS / "estadisticas_categoricas.csv")

    nulos = (datos.isna().mean() * 100).round(2).sort_values(ascending=False)
    nulos.rename("porcentaje_nulos").to_csv(config.TABLAS / "nulos_por_variable.csv")
    print(f"Variables con nulos: {(nulos > 0).sum()} de {len(nulos)}")

    n_dup = int(datos.duplicated().sum())
    pd.DataFrame({
        "duplicados": [n_dup],
        "porcentaje": [round(n_dup / len(datos) * 100, 3)],
    }).to_csv(config.TABLAS / "duplicados.csv", index=False)
    print(f"Registros duplicados: {n_dup:,} ({n_dup / len(datos) * 100:.2f} %)")

    trabajo = pd.DataFrame(index=df.index)
    if cols["hora"]:
        trabajo["hora_num"] = extraer_hora(df[cols["hora"]])
    for clave in ("fallecidos", "lesionados"):
        if cols[clave]:
            trabajo[clave] = pd.to_numeric(df[cols[clave]], errors="coerce")
    for c in numericas.columns:
        if c not in trabajo.columns and numericas[c].nunique() > 10:
            trabajo[c] = numericas[c]

    filas = []
    for c in trabajo.columns:
        s = trabajo[c].dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        inf, sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n_out = int(((s < inf) | (s > sup)).sum())
        filas.append({"variable": c, "q1": q1, "q3": q3, "limite_inferior": inf,
                      "limite_superior": sup, "atipicos": n_out,
                      "porcentaje": round(n_out / len(s) * 100, 2)})
    if filas:
        pd.DataFrame(filas).round(3).to_csv(config.TABLAS / "valores_atipicos.csv", index=False)
        k = len(filas)
        fig, ejes = plt.subplots(1, k, figsize=(3.2 * k, 3.5))
        for eje, c in zip(np.atleast_1d(ejes), trabajo.columns[:k]):
            eje.boxplot(trabajo[c].dropna(), vert=True)
            eje.set_title(c)
        guardar_fig("fig_boxplots_atipicos.png")

    objetivo = None
    if cols["fallecidos"]:
        objetivo = (pd.to_numeric(df[cols["fallecidos"]], errors="coerce").fillna(0) > 0).astype(int)

    if cols["hora"]:
        hora = extraer_hora(df[cols["hora"]])
        conteo = hora.value_counts().sort_index()
        plt.figure(figsize=(8, 4))
        plt.bar(conteo.index, conteo.values, color="#2a6f97")
        plt.xlabel("Hora del día")
        plt.ylabel("Número de siniestros")
        plt.title("Siniestros de tránsito según la hora")
        guardar_fig("fig_siniestros_por_hora.png")

        if objetivo is not None:
            tasa = objetivo.groupby(hora).mean() * 100
            plt.figure(figsize=(8, 4))
            plt.plot(tasa.index, tasa.values, marker="o", color="#bc4749")
            plt.xlabel("Hora del día")
            plt.ylabel("Siniestros con fallecidos (%)")
            plt.title("Porcentaje de siniestros mortales según la hora")
            guardar_fig("fig_tasa_mortal_por_hora.png")

    _, dia_semana = derivar_calendario(df, cols)
    if dia_semana.notna().any():
        conteo = dia_semana.dropna().astype(int).value_counts().sort_index()
        plt.figure(figsize=(8, 4))
        plt.bar([NOMBRES_DIA[i] for i in conteo.index], conteo.values, color="#386641")
        plt.ylabel("Número de siniestros")
        plt.title("Siniestros de tránsito según el día de la semana")
        plt.xticks(rotation=30)
        guardar_fig("fig_siniestros_por_dia.png")

    if cols["provincia"]:
        prov = df[cols["provincia"]].map(normalizar_valor)
        top = prov.value_counts().head(10).sort_values()
        plt.figure(figsize=(8, 4.5))
        plt.barh(top.index, top.values, color="#6a4c93")
        plt.xlabel("Número de siniestros")
        plt.title("Diez provincias con más siniestros")
        guardar_fig("fig_top_provincias.png")

    if objetivo is not None:
        cuenta = objetivo.value_counts().sort_index()
        plt.figure(figsize=(5, 4))
        plt.bar(["Sin fallecidos", "Con fallecidos"], [cuenta.get(0, 0), cuenta.get(1, 0)],
                color=["#8d99ae", "#bc4749"])
        plt.ylabel("Número de siniestros")
        plt.title("Balance de la variable objetivo")
        guardar_fig("fig_balance_objetivo.png")
        print(f"Siniestros con fallecidos: {objetivo.mean() * 100:.2f} %")

    if cols["causa"]:
        causa = df[cols["causa"]].map(normalizar_valor)
        top = causa.value_counts().head(10).sort_values()
        plt.figure(figsize=(9, 4.5))
        plt.barh([t[:45] for t in top.index], top.values, color="#f4a261")
        plt.xlabel("Número de siniestros")
        plt.title("Diez causas probables más frecuentes")
        guardar_fig("fig_top_causas.png")

    print(f"\nTablas guardadas en {config.TABLAS}; figuras guardadas en {config.FIGURAS}.")


if __name__ == "__main__":
    main()
