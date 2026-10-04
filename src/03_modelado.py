"""Paso 3. Modelado, validación cruzada y evaluación.

Entrena tres modelos de clasificación (regresión logística, árbol de decisión y
random forest) para predecir si un siniestro termina con al menos un fallecido
en el lugar. Compara los modelos con validación cruzada estratificada sobre el
conjunto de entrenamiento y los evalúa una sola vez sobre el conjunto de prueba.
"""
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay, PrecisionRecallDisplay, RocCurveDisplay,
    accuracy_score, average_precision_score, f1_score, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

import config
from utilidades import cargar_procesados, construir_preprocesador

METRICAS_CV = {
    "accuracy": "accuracy",
    "precision": "precision",
    "recall": "recall",
    "f1": "f1",
    "roc_auc": "roc_auc",
    "pr_auc": "average_precision",
}


def definir_modelos():
    s = config.SEMILLA
    return {
        "Regresión logística": LogisticRegression(
            C=1.0, class_weight="balanced", max_iter=1000, solver="lbfgs", random_state=s),
        "Árbol de decisión": DecisionTreeClassifier(
            max_depth=8, min_samples_leaf=20, class_weight="balanced", random_state=s),
        "Random forest": RandomForestClassifier(
            n_estimators=300, max_depth=12, min_samples_leaf=5,
            class_weight="balanced_subsample", n_jobs=-1, random_state=s),
    }


def metricas_prueba(y_real, y_pred, y_prob):
    return {
        "accuracy": accuracy_score(y_real, y_pred),
        "precision": precision_score(y_real, y_pred, zero_division=0),
        "recall": recall_score(y_real, y_pred, zero_division=0),
        "f1": f1_score(y_real, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_real, y_prob),
        "pr_auc": average_precision_score(y_real, y_prob),
    }


def main():
    # El baseline siempre predice la clase mayoritaria y no identifica positivos.
    warnings.filterwarnings("ignore", category=UserWarning)
    from sklearn.exceptions import UndefinedMetricWarning
    warnings.filterwarnings("ignore", category=UndefinedMetricWarning)

    datos, num, cat = cargar_procesados()
    X = datos[num + cat]
    y = datos["objetivo_fallecidos"]
    print(f"Registros: {len(datos):,} | positivos: {y.sum():,} ({y.mean() * 100:.2f} %)")

    X_ent, X_pru, y_ent, y_pru = train_test_split(
        X, y, test_size=config.PROPORCION_PRUEBA, stratify=y, random_state=config.SEMILLA)
    pd.DataFrame({
        "conjunto": ["entrenamiento", "prueba"],
        "registros": [len(X_ent), len(X_pru)],
        "proporcion": [1 - config.PROPORCION_PRUEBA, config.PROPORCION_PRUEBA],
        "con_fallecidos": [int(y_ent.sum()), int(y_pru.sum())],
        "porcentaje_con_fallecidos": [round(y_ent.mean() * 100, 2), round(y_pru.mean() * 100, 2)],
    }).to_csv(config.TABLAS / "division_datos.csv", index=False)

    modelos = definir_modelos()
    pipelines = {
        nombre: Pipeline([("prep", construir_preprocesador(num, cat)), ("modelo", m)])
        for nombre, m in modelos.items()
    }
    base = Pipeline([("prep", construir_preprocesador(num, cat)),
                     ("modelo", DummyClassifier(strategy="prior"))])

    filas = []
    for nombre, m in modelos.items():
        for p, v in m.get_params().items():
            filas.append({"modelo": nombre, "parametro": p, "valor": v})
    pd.DataFrame(filas).to_csv(config.TABLAS / "parametros_modelos_completos.csv", index=False)

    principales = {
        "Regresión logística": ["C", "class_weight", "max_iter", "solver"],
        "Árbol de decisión": ["max_depth", "min_samples_leaf", "class_weight", "criterion"],
        "Random forest": ["n_estimators", "max_depth", "min_samples_leaf", "class_weight", "max_features"],
    }
    pd.DataFrame([
        {"modelo": n, "parametros_principales": ", ".join(f"{p}={modelos[n].get_params()[p]}" for p in ps)}
        for n, ps in principales.items()
    ]).to_csv(config.TABLAS / "parametros_modelos.csv", index=False)

    cv = StratifiedKFold(n_splits=config.K_PARTICIONES, shuffle=True, random_state=config.SEMILLA)
    filas_cv = []
    for nombre, pipe in {**pipelines, "Clasificador base": base}.items():
        print(f"Validación cruzada ({config.K_PARTICIONES} particiones) para {nombre}...")
        res = cross_validate(pipe, X_ent, y_ent, cv=cv, scoring=METRICAS_CV, n_jobs=1)
        fila = {"modelo": nombre}
        for corto in METRICAS_CV:
            valores = res[f"test_{corto}"]
            fila[f"{corto}_media"] = valores.mean()
            fila[f"{corto}_desv"] = valores.std()
        filas_cv.append(fila)
    tabla_cv = pd.DataFrame(filas_cv).round(4)
    tabla_cv.to_csv(config.TABLAS / "comparacion_validacion_cruzada.csv", index=False)

    filas_test, predicciones = [], {}
    for nombre, pipe in {**pipelines, "Clasificador base": base}.items():
        pipe.fit(X_ent, y_ent)
        y_pred = pipe.predict(X_pru)
        y_prob = pipe.predict_proba(X_pru)[:, 1]
        predicciones[nombre] = (y_pred, y_prob)
        filas_test.append({"modelo": nombre, **metricas_prueba(y_pru, y_pred, y_prob)})
    tabla_test = pd.DataFrame(filas_test).round(4)
    tabla_test.to_csv(config.TABLAS / "comparacion_prueba.csv", index=False)
    print("\nResultados en el conjunto de prueba")
    print(tabla_test.to_string(index=False))

    k = len(pipelines)
    fig, ejes = plt.subplots(1, k, figsize=(4.6 * k, 4))
    for eje, nombre in zip(ejes, pipelines):
        ConfusionMatrixDisplay.from_predictions(
            y_pru, predicciones[nombre][0], ax=eje, cmap="Blues", colorbar=False,
            display_labels=["Sin fallecidos", "Con fallecidos"])
        eje.set_title(nombre)
    plt.tight_layout()
    plt.savefig(config.FIGURAS / "fig_matrices_confusion.png", dpi=150)
    plt.close()

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.5))
    for nombre in pipelines:
        RocCurveDisplay.from_predictions(y_pru, predicciones[nombre][1], ax=a1, name=nombre)
        PrecisionRecallDisplay.from_predictions(y_pru, predicciones[nombre][1], ax=a2, name=nombre)
    a1.plot([0, 1], [0, 1], "--", color="gray")
    a1.set_title("Curva ROC")
    a2.set_title("Curva precisión-recall")
    plt.tight_layout()
    plt.savefig(config.FIGURAS / "fig_curvas_roc_pr.png", dpi=150)
    plt.close()

    modelos_tabla = tabla_cv[tabla_cv["modelo"].isin(pipelines)]
    x = np.arange(len(modelos_tabla))
    plt.figure(figsize=(7.5, 4.2))
    plt.bar(x - 0.2, modelos_tabla["recall_media"], 0.4, yerr=modelos_tabla["recall_desv"],
            label="Recall", color="#bc4749", capsize=3)
    plt.bar(x + 0.2, modelos_tabla["f1_media"], 0.4, yerr=modelos_tabla["f1_desv"],
            label="F1", color="#2a6f97", capsize=3)
    plt.xticks(x, modelos_tabla["modelo"])
    plt.ylabel(f"Media en {config.K_PARTICIONES} particiones")
    plt.title("Recall y F1 en validación cruzada")
    plt.legend()
    plt.tight_layout()
    plt.savefig(config.FIGURAS / "fig_validacion_cruzada.png", dpi=150)
    plt.close()

    rf = pipelines["Random forest"]
    nombres = rf.named_steps["prep"].get_feature_names_out()
    imp = pd.Series(rf.named_steps["modelo"].feature_importances_, index=nombres).sort_values(ascending=False)
    imp.rename("importancia").to_csv(config.TABLAS / "importancia_random_forest.csv")
    top = imp.head(15).sort_values()
    plt.figure(figsize=(8, 5.5))
    plt.barh([t.replace("num__", "").replace("cat__", "")[:40] for t in top.index], top.values, color="#386641")
    plt.xlabel("Importancia")
    plt.title("Quince variables más importantes en el random forest")
    plt.tight_layout()
    plt.savefig(config.FIGURAS / "fig_importancia_random_forest.png", dpi=150)
    plt.close()

    lr = pipelines["Regresión logística"]
    coef = pd.Series(lr.named_steps["modelo"].coef_[0], index=lr.named_steps["prep"].get_feature_names_out())
    coef.sort_values(ascending=False).rename("coeficiente").to_csv(config.TABLAS / "coeficientes_regresion_logistica.csv")

    print(f"\nResultados guardados en {config.TABLAS} y {config.FIGURAS}.")


if __name__ == "__main__":
    main()
