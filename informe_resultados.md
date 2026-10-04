# Resultados del análisis de siniestros de tránsito

## Objetivo

En este trabajo analicé si las características temporales y geográficas disponibles ayudaban a distinguir los siniestros con al menos un fallecido en el lugar. También agrupé los registros con K-means y comparé la proporción de siniestros con fallecidos entre la Amazonía y el resto del país.

## Datos y alcance

Descargué los ocho archivos trimestrales enlazados en `urls.txt`. Como los cortes eran acumulativos, seleccioné el cierre del cuarto trimestre de 2023 y 2024 para no sumar varias veces los mismos cortes del año. Trabajé con 42.214 registros: 20.994 de 2023 y 21.220 de 2024, correspondientes a los doce meses de cada año.

En los CSV seleccionados encontré códigos numéricos para provincia, zona, clase y causa. Convertí provincia usando los códigos DPA de Ecuador. Conservé zona, clase y causa como categorías, sin asignarles nombres que no estuvieran en los diccionarios descargados. Interpreté los códigos de día de semana del archivo anual del 1 al 7, de lunes a domingo; comprobé que ese orden coincidiera con las etiquetas del corte 2023-III entre enero y septiembre.

Conté 882 filas idénticas y las conservé porque los archivos no incluyen un identificador único con el que pudiera confirmar que fueran el mismo siniestro. No encontré valores nulos en las variables de origen ni registros sin el dato de fallecidos.

Definí la variable objetivo como 1 cuando `num_fallecido` era mayor que cero. Así, identifiqué 4.180 registros positivos, equivalentes al 9,90 % del conjunto.

## Preparación y evaluación

Derivé la hora, la franja horaria, el día de semana, los indicadores de fin de semana y la pertenencia a la Amazonía. Usé seis predictores numéricos (`hora_num`, `hora_pico`, `mes`, `fin_de_semana`, `viernes_a_domingo`, `es_amazonia`) y seis categóricos (`franja_horaria`, `dia_semana`, `provincia`, `zona`, `clase`, `causa`). Excluí fallecidos, lesionados, total de víctimas y el año de origen de los predictores.

Separé los datos de forma estratificada: 33.771 registros para entrenamiento y 8.443 para prueba. La prueba incluyó 836 registros positivos. Usé la semilla 42 y validación cruzada estratificada de cinco particiones solo sobre entrenamiento. Coloqué la imputación, el escalado y la codificación dentro de los pipelines para que se ajustaran con los datos de entrenamiento de cada partición.

### Clasificación

| Modelo | Exactitud | Precisión | Recall | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Regresión logística | 0,6743 | 0,1804 | 0,6459 | 0,2820 | 0,7213 | 0,2632 |
| Árbol de decisión | 0,6007 | 0,1572 | 0,6950 | 0,2563 | 0,6896 | 0,2101 |
| Random forest | 0,7050 | 0,1911 | 0,6124 | 0,2913 | 0,7230 | 0,2681 |
| Clasificador base | 0,9010 | 0,0000 | 0,0000 | 0,0000 | 0,5000 | 0,0990 |

En la validación cruzada, random forest obtuvo un F1 medio de 0,2991, un PR-AUC medio de 0,2671 y el mayor ROC-AUC medio (0,7384). En el conjunto de prueba también obtuvo el F1 y el PR-AUC más altos entre los tres modelos. El árbol alcanzó el recall más alto (0,6950), aunque su precisión fue 0,1572.

El clasificador base logró más exactitud porque siempre predijo la clase mayoritaria, pero no identificó ningún registro con fallecidos. Los otros modelos detectaron parte de los positivos, aunque con precisión baja. Por eso comparé varias métricas y no usé la exactitud como único criterio. Consideré los modelos exploratorios; no los propuse para decisiones operativas sin validación adicional y sin definir un umbral apropiado.

## Clustering y comparación regional

Excluí provincia y el indicador de Amazonía al ajustar K-means para que la ubicación no definiera los grupos de antemano. Elegí dos clústeres: entre los valores evaluados, obtuvieron la mayor silueta (0,1989).

| Clúster | Registros | Proporción | Con fallecidos |
| --- | ---: | ---: | ---: |
| 0 | 16.092 | 38,12 % | 11,65 % |
| 1 | 26.122 | 61,88 % | 8,83 % |

Al comparar las regiones, encontré fallecidos en 223 de los 615 registros amazónicos (36,26 %) y en 3.957 de los 41.599 registros del resto del país (9,51 %). La prueba de chi-cuadrado produjo $\chi^2 = 483,017$ y $p < 0,001$. Interpreté este resultado como una asociación en los datos analizados, no como evidencia de causalidad. Para interpretar la prueba asumí independencia entre las observaciones.

## Limitaciones

- Analicé los cierres anuales de 2023 y 2024. Descargué los otros cortes trimestrales, pero no los apilé porque eran acumulativos.
- No encontré etiquetas para los códigos de zona, clase y causa en los diccionarios incluidos. Los traté como categorías y no interpreté sus números. Antes de asignarles nombres o significados, debo confirmar su equivalencia en un catálogo oficial.
- No tuve un identificador de siniestro; por eso conservé las filas idénticas y no pude determinar si eran registros repetidos o siniestros distintos.
- Usé una partición aleatoria estratificada para probar los modelos, no una evaluación temporal sobre un año futuro. Por eso no comprobé su desempeño en periodos posteriores.
- La precisión baja me mostró que muchos positivos predichos fueron falsos positivos. No propuse el modelo para decidir sobre siniestros individuales.

## Fuentes

- [INEC, Siniestros de tránsito](https://www.ecuadorencifras.gob.ec/estadisticas-siniestros-de-transito/)
- [INEC, Siniestros de tránsito trimestral](https://www.ecuadorencifras.gob.ec/siniestros-transito-trimestral/)
- [INEC, Información histórica de siniestros trimestrales](https://www.ecuadorencifras.gob.ec/informacion-historica-siniestros-transito-trimestral/)