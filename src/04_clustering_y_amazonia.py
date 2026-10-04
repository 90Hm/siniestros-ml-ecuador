"""Paso 4. Perfiles de siniestros con K-means y comparación de la Amazonía.

Es la parte descriptiva del trabajo. Agrupa los siniestros en perfiles, mide
qué tan mortal es cada perfil y compara la Amazonía con el resto del país.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

import config
from utilidades import cargar_procesados, construir_preprocesador


def main():
    datos, num, cat = cargar_procesados()
    num_cluster = [c for c in num if c != "es_amazonia"]
    cat_cluster = [c for c in cat if c != "provincia"]
    X = datos[num_cluster + cat_cluster]

    # K-means no usa la variable objetivo, solo describe los datos
    matriz = construir_preprocesador(num_cluster, cat_cluster).fit_transform(X)
    rng = np.random.default_rng(config.SEMILLA)
    idx = rng.choice(len(matriz), size=min(config.MUESTRA_SILUETA, len(matriz)), replace=False)

    # ------------------------------------------------------ elección de k
    filas = []
    for k in range(config.K_MIN, config.K_MAX + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=config.SEMILLA).fit(matriz)
        sil = silhouette_score(matriz[idx], km.labels_[idx])
        filas.append({"k": k, "inercia": km.inertia_, "silueta": sil})
        print(f"  k={k}: silueta={sil:.3f}")
    tabla_k = pd.DataFrame(filas).round(4)
    tabla_k.to_csv(config.TABLAS / "clustering_eleccion_k.csv", index=False)
    k_final = int(tabla_k.loc[tabla_k["silueta"].idxmax(), "k"])
    print(f"k elegido por mayor silueta: {k_final}")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    a1.plot(tabla_k["k"], tabla_k["inercia"], marker="o", color="#2a6f97")
    a1.set_xlabel("Número de clústeres")
    a1.set_ylabel("Inercia")
    a1.set_title("Método del codo")
    a2.plot(tabla_k["k"], tabla_k["silueta"], marker="o", color="#bc4749")
    a2.set_xlabel("Número de clústeres")
    a2.set_ylabel("Silueta")
    a2.set_title("Coeficiente de silueta")
    plt.tight_layout()
    plt.savefig(config.FIGURAS / "fig_eleccion_k.png", dpi=150)
    plt.close()

    # ------------------------------------------------------ ajuste final
    km = KMeans(n_clusters=k_final, n_init=10, random_state=config.SEMILLA).fit(matriz)
    datos = datos.assign(cluster=km.labels_)

    perfiles = []
    for c, grupo in datos.groupby("cluster"):
        fila = {
            "cluster": c,
            "siniestros": len(grupo),
            "porcentaje_del_total": round(len(grupo) / len(datos) * 100, 2),
            "porcentaje_con_fallecidos": round(grupo["objetivo_fallecidos"].mean() * 100, 2),
        }
        for v in num:
            fila[f"media_{v}"] = round(grupo[v].mean(), 3)
        for v in cat:
            fila[f"mas_frecuente_{v}"] = grupo[v].mode().iloc[0]
        perfiles.append(fila)
    pd.DataFrame(perfiles).to_csv(config.TABLAS / "clustering_perfiles.csv", index=False)

    pca = PCA(n_components=2, random_state=config.SEMILLA)
    coords = pca.fit_transform(matriz[idx])
    plt.figure(figsize=(7, 5.5))
    plt.scatter(coords[:, 0], coords[:, 1], c=km.labels_[idx], cmap="tab10", s=8, alpha=0.6)
    plt.xlabel(f"Componente 1 ({pca.explained_variance_ratio_[0] * 100:.1f} % de la varianza)")
    plt.ylabel(f"Componente 2 ({pca.explained_variance_ratio_[1] * 100:.1f} % de la varianza)")
    plt.title(f"Perfiles de siniestros con K-means, k={k_final}")
    plt.tight_layout()
    plt.savefig(config.FIGURAS / "fig_clusters_pca.png", dpi=150)
    plt.close()

    # ------------------------------------------- Amazonía frente al resto
    if "es_amazonia" in datos.columns:
        resumen = []
        for etiqueta, valor in (("Amazonía", 1), ("Resto del país", 0)):
            g = datos[datos["es_amazonia"] == valor]
            fila = {"region": etiqueta, "siniestros": len(g),
                    "con_fallecidos": int(g["objetivo_fallecidos"].sum()),
                    "porcentaje_con_fallecidos": round(g["objetivo_fallecidos"].mean() * 100, 2)}
            if "hora_num" in g:
                fila["hora_media"] = round(g["hora_num"].mean(), 2)
            if "fin_de_semana" in g:
                fila["porcentaje_fin_de_semana"] = round(g["fin_de_semana"].mean() * 100, 2)
            for v in ("causa", "clase", "zona"):
                if v in g:
                    fila[f"{v}_mas_frecuente"] = g[v].mode().iloc[0]
            resumen.append(fila)
        tabla_region = pd.DataFrame(resumen)

        contingencia = pd.crosstab(datos["es_amazonia"], datos["objetivo_fallecidos"])
        if contingencia.shape == (2, 2):
            chi2, p, _, _ = chi2_contingency(contingencia)
            tabla_region["chi2"] = round(chi2, 3)
            tabla_region["valor_p"] = p
            print(f"Chi cuadrado Amazonía vs mortalidad: chi2={chi2:.2f}, p={p:.4g}")
        tabla_region.to_csv(config.TABLAS / "amazonia_vs_resto.csv", index=False)

        plt.figure(figsize=(5.5, 4.2))
        plt.bar(tabla_region["region"], tabla_region["porcentaje_con_fallecidos"], color=["#386641", "#8d99ae"])
        plt.ylabel("Siniestros con fallecidos (%)")
        plt.title("Mortalidad de los siniestros por región")
        plt.tight_layout()
        plt.savefig(config.FIGURAS / "fig_amazonia_vs_resto.png", dpi=150)
        plt.close()
    else:
        print("No se pudo comparar la Amazonía porque no hay columna de provincia.")

    print(f"\nListo. Resultados en {config.TABLAS} y {config.FIGURAS}")


if __name__ == "__main__":
    main()
