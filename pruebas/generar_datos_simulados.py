"""Genera un CSV SIMULADO con una estructura parecida a la base del INEC.

ADVERTENCIA. Estos datos son inventados y existen solo para comprobar que el
código corre de principio a fin. Nunca se deben usar en el informe.

Uso desde la raíz del proyecto:
    python pruebas/generar_datos_simulados.py
    export SINIESTROS_DATA_DIR=pruebas/datos_simulados
    export SINIESTROS_PROC_DIR=pruebas/procesados_simulados
    export SINIESTROS_OUT_DIR=pruebas/salidas_simuladas
    python src/01_eda.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
N = 12000

provincias = ["PICHINCHA", "GUAYAS", "MANABI", "AZUAY", "LOS RIOS", "EL ORO", "TUNGURAHUA",
              "PASTAZA", "NAPO", "MORONA SANTIAGO", "SUCUMBIOS", "ORELLANA", "LOJA", "SANTA ELENA"]
peso_prov = np.array([14, 18, 9, 6, 6, 6, 5, 2, 1.5, 2, 2, 2, 5, 3], dtype=float)
peso_prov /= peso_prov.sum()
clases = ["CHOQUE", "ESTRELLAMIENTO", "ATROPELLO", "VOLCAMIENTO", "ROZAMIENTO", "CAIDA DE PASAJERO"]
causas = ["CONDUCIR DESATENTO", "EXCESO DE VELOCIDAD", "EMBRIAGUEZ", "IMPERICIA", "MAL REBASAMIENTO",
          "NO RESPETAR SENALES", "FALLA MECANICA", "SIN DATO"]

hora = np.clip(rng.normal(14, 6, N), 0, 23).astype(int)
minuto = rng.integers(0, 60, N)
prov = rng.choice(provincias, N, p=peso_prov)
zona = rng.choice(["URBANA", "RURAL"], N, p=[0.7, 0.3])
clase = rng.choice(clases, N, p=[0.45, 0.12, 0.13, 0.08, 0.17, 0.05])
causa = rng.choice(causas, N, p=[0.35, 0.18, 0.08, 0.12, 0.08, 0.08, 0.04, 0.07])
mes = rng.integers(1, 13, N)
dia = rng.integers(1, 29, N)
anio = rng.choice([2023, 2024], N)

logit = (-3.3 + 0.9 * (zona == "RURAL") + 0.8 * ((hora >= 22) | (hora <= 4))
         + 0.9 * (clase == "ATROPELLO") + 0.7 * (clase == "VOLCAMIENTO")
         + 0.6 * (causa == "EXCESO DE VELOCIDAD") + 0.5 * (causa == "EMBRIAGUEZ")
         + 0.3 * np.isin(prov, ["PASTAZA", "NAPO", "MORONA SANTIAGO", "SUCUMBIOS", "ORELLANA"]))
mortal = rng.random(N) < 1 / (1 + np.exp(-logit))
fallecidos = np.where(mortal, rng.choice([1, 1, 1, 2, 3], N), 0)
lesionados = np.where(rng.random(N) < 0.75, rng.choice([1, 1, 2, 3, 4], N), 0)

df = pd.DataFrame({
    "Anio": anio, "Mes": mes, "Dia": dia,
    "Hora": [f"{h:02d}:{m:02d}" for h, m in zip(hora, minuto)],
    "Provincia": prov, "Zona": zona,
    "Clase de siniestro": clase, "Causa probable": causa,
    "Numero de vehiculos": rng.choice([1, 2, 3], N, p=[0.35, 0.55, 0.10]),
    "Num. fallecidos in situ": fallecidos,
    "Num. lesionados": lesionados,
})

# Ensuciar un poco los datos para ejercitar la limpieza
df.loc[rng.choice(N, 300, replace=False), "Hora"] = np.nan
df.loc[rng.choice(N, 200, replace=False), "Zona"] = "No identificado"
df.loc[rng.choice(N, 150, replace=False), "Provincia"] = np.nan
df = pd.concat([df, df.sample(120, random_state=1)], ignore_index=True)

destino = Path(__file__).resolve().parent / "datos_simulados"
destino.mkdir(exist_ok=True)
df.to_csv(destino / "siniestros_simulados.csv", sep=";", index=False, encoding="utf-8-sig")
print(f"Archivo simulado escrito en {destino} con {len(df):,} filas")
