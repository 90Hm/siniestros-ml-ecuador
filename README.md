# Predicción de la gravedad de los siniestros de tránsito en Ecuador

Proyecto de la asignatura Minería de Datos de la Universidad Estatal Amazónica.
Aplicamos tres técnicas de clasificación y una de agrupamiento a las bases abiertas
de siniestros de tránsito del INEC, con el objetivo de estimar si un siniestro termina
con al menos un fallecido en el lugar.

## Datos

Las bases las publica el INEC a partir de los registros administrativos de la Agencia
Nacional de Tránsito, con licencia Creative Commons Atribución 4.0. Se descargan por
trimestre desde las páginas de Siniestros de Tránsito del INEC
(https://www.ecuadorencifras.gob.ec/estadisticas-siniestros-de-transito/).
El repositorio no incluye los datos, hay que descargarlos con el paso 0.

Los archivos trimestrales son cortes acumulados del año. Para evitar contar varias
veces las observaciones que reaparecen en cada corte, el análisis selecciona el cuarto
trimestre de cada año (`TRIMESTRE_ANALISIS = 4`). Los cierres de 2023 y 2024 usan
códigos numéricos para provincia, zona, clase y causa. Provincia se decodifica con la
codificación DPA; las otras categorías se conservan como códigos nominales porque los
diccionarios incluidos por el INEC no contienen sus etiquetas.

## Estructura

```
src/
  config.py                      parámetros, rutas y mapeo de columnas
  utilidades.py                  funciones compartidas
  00_descargar_datos.py          descarga y descomprime las bases del INEC
  01_eda.py                      exploración, nulos, duplicados, atípicos y gráficos
  02_preprocesamiento.py         limpieza, transformaciones y variables derivadas
  03_modelado.py                 tres modelos, validación cruzada y evaluación
  04_clustering_y_amazonia.py    K-means y comparación de la Amazonía
informe_resultados.md            resultados, decisiones y limitaciones del análisis
pruebas/
  generar_datos_simulados.py     datos inventados solo para probar que el código corre
urls.txt                         direcciones de descarga
```

## Cómo ejecutarlo

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows .venv\Scripts\activate
pip install -r requirements.txt

python src/00_descargar_datos.py
python src/01_eda.py
python src/02_preprocesamiento.py
python src/03_modelado.py
python src/04_clustering_y_amazonia.py
```

Las tablas quedan en `outputs/tablas/` y las figuras en `outputs/figuras/`.

## Revisión de datos y alcance

- `urls.txt` contiene los ocho enlaces trimestrales de 2023 y 2024. El análisis selecciona
  los cierres anuales de cada año; `01_eda.py` deja el mapeo observado en
  `outputs/tablas/mapeo_columnas.csv`.
- `MAPEO_MANUAL` está vacío porque los nombres lógicos necesarios se detectan en los
  CSV descargados. El año se obtiene del nombre del archivo cuando no viene como columna.
- `02_preprocesamiento.py` deja la lista de predictores en
  `outputs/tablas/features_utilizadas.csv`. Fallecidos, lesionados y total de víctimas
  no se usan como predictores del objetivo.
- Las filas con valores idénticos se contabilizan, pero se conservan: el archivo no trae
  un identificador único para demostrar que dos filas describen el mismo siniestro.

## Decisiones de diseño

- La variable objetivo es `objetivo_fallecidos`, igual a 1 si el siniestro tiene al menos
  un fallecido en el lugar.
- La división es 80 % entrenamiento y 20 % prueba, estratificada, con semilla 42.
- La validación cruzada es estratificada de 5 particiones y se hace solo sobre el
  conjunto de entrenamiento. El conjunto de prueba se usa una sola vez.
- La imputación, el escalado y la codificación van dentro de un `Pipeline`; sus
  estadísticas se ajustan con el entrenamiento de cada partición.
- Para el desbalance de clases se usan pesos de clase, no remuestreo.
- Se incluye un clasificador base que siempre predice la clase mayoritaria, para mostrar
  por qué la exactitud sola engaña cuando los siniestros mortales son minoría.
- K-means no recibe provincia ni el indicador de Amazonía; la comparación regional se
  calcula por separado para que la geografía no determine los clústeres de antemano.

## Licencia de los datos

Los datos pertenecen al INEC y se usan bajo la licencia CC BY 4.0.
