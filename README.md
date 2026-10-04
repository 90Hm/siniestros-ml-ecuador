# Análisis de siniestros de tránsito en Ecuador

En este proyecto analizo los registros de siniestros de tránsito publicados por el INEC y la Agencia Nacional de Tránsito. Mi objetivo es estudiar qué características se relacionan con que un siniestro tenga al menos un fallecido en el lugar. También comparo los registros de la Amazonía con los del resto del país y describo perfiles mediante agrupamiento.

## Datos y periodo

Descargo los archivos trimestrales desde las páginas oficiales del [INEC](https://www.ecuadorencifras.gob.ec/estadisticas-siniestros-de-transito/). En `urls.txt` guardé los enlaces de los cuatro trimestres de 2023 y 2024.

Los archivos trimestrales son acumulativos: cada nuevo corte vuelve a incluir observaciones de los anteriores. Para no sumar varias veces esos cortes, configuré el análisis con el cierre del cuarto trimestre de cada año (`TRIMESTRE_ANALISIS = 4`). Trabajé con los cierres de 2023 y 2024.

En los archivos anuales, provincia, zona, clase y causa aparecen como códigos numéricos. Convertí los códigos de provincia con la codificación DPA. Dejé zona, clase y causa como categorías, sin atribuirles etiquetas que no aparecen en los diccionarios incluidos por el INEC.

## Qué hace el código

- `src/00_descargar_datos.py`: con este paso leo `urls.txt`, descargo los ZIP del INEC y los descomprimo en `data/raw/`.
- `src/01_eda.py`: aquí cargo los CSV, identifico las columnas y genero tablas y gráficos de exploración. Registro el mapeo en `outputs/tablas/mapeo_columnas.csv`.
- `src/02_preprocesamiento.py`: aquí limpio textos, defino la variable objetivo y derivo variables de calendario y ubicación. Guardo los datos preparados en `data/processed/` y los predictores en `outputs/tablas/features_utilizadas.csv`.
- `src/03_modelado.py`: con este script divido los datos en entrenamiento y prueba, comparo regresión logística, árbol de decisión y random forest, y guardo sus métricas y gráficos.
- `src/04_clustering_y_amazonia.py`: aquí elijo el número de grupos con la silueta, describo los perfiles y comparo por separado la proporción de registros con fallecidos entre la Amazonía y el resto del país.
- `src/config.py`: en este archivo centralicé las rutas, la semilla, los parámetros, los patrones de detección y las categorías geográficas.
- `src/utilidades.py`: aquí reuní las funciones que reutilizo para leer y normalizar datos, detectar columnas, derivar el calendario y preparar los modelos.
- `pruebas/generar_datos_simulados.py`: uso este script para crear datos inventados y comprobar que el flujo se ejecuta. No los uso para los resultados del informe.

Guardo las tablas en `outputs/tablas/` y las figuras en `outputs/figuras/`. En [informe_resultados.md](informe_resultados.md) resumo los resultados que obtuve y sus limitaciones.

## Cómo lo ejecuto en Linux

Desde la carpeta del proyecto creo un entorno virtual, instalo las dependencias y ejecuto los pasos en orden:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python src/00_descargar_datos.py
python src/01_eda.py
python src/02_preprocesamiento.py
python src/03_modelado.py
python src/04_clustering_y_amazonia.py
```

Para salir del entorno virtual uso `deactivate`.

## Decisiones que tomé

Definí `objetivo_fallecidos` como 1 cuando `num_fallecido` es mayor que cero. No incluí fallecidos, lesionados ni total de víctimas entre las variables predictoras, porque revelarían directamente información relacionada con el objetivo.

Usé una partición estratificada de 80 % para entrenamiento y 20 % para prueba, con semilla 42. Hice validación cruzada estratificada de cinco particiones solo sobre entrenamiento y reservé prueba para la evaluación final. La imputación, el escalado y la codificación están dentro del pipeline para que sus parámetros se ajusten solo con cada partición de entrenamiento.

Encontré filas con valores idénticos, pero las conservé: los archivos no incluyen un identificador único que me permita confirmar si son registros duplicados o siniestros diferentes con las mismas características disponibles. Dejé el conteo en la bitácora del preprocesamiento.

Para K-means excluí provincia y el indicador de Amazonía; así evité que la ubicación definiera directamente los grupos. La comparación regional la calculé por separado. Como los registros de fallecidos son minoría, comparé precisión, recall, F1, ROC-AUC y PR-AUC, además de exactitud y un clasificador base.

## Archivos generados y datos

No incluyo los CSV descargados ni los datos procesados en el repositorio. Para regenerar el análisis ejecuto primero el descargador. Generé las tablas y figuras de `outputs/` con los archivos y parámetros descritos en el informe.

Usé las bases publicadas por el INEC bajo [Creative Commons Atribución 4.0](https://creativecommons.org/licenses/by/4.0/).
