# Resultados del análisis de siniestros de tránsito

## Objetivo

Se evaluó si las características temporales y geográficas disponibles permitían
distinguir registros de siniestros con al menos un fallecido en el lugar. Además, se
describieron perfiles mediante K-means y se comparó la proporción de registros con
fallecidos entre la Amazonía y el resto del país.

## Datos y alcance

Se descargaron los ocho archivos trimestrales enlazados en `urls.txt`. Como los cortes
trimestrales eran acumulados, se seleccionó el cierre del cuarto trimestre de 2023 y
2024 para evitar volver a incorporar observaciones repetidas en los cortes anteriores.
El conjunto analizado tuvo 42.214 registros: 20.994 de 2023 y 21.220 de 2024. El periodo
cubrió los doce meses de ambos años.

Los CSV seleccionados codificaron provincia, zona, clase y causa con números. Se
decodificó provincia mediante los códigos DPA de Ecuador. Zona, clase y causa se
conservaron como categorías nominales, sin asignarles nombres no contenidos en los
diccionarios descargados. Los códigos de día de semana del archivo anual se mapearon de
1 a 7, de lunes a domingo; el orden coincidió exactamente con las etiquetas del corte
2023-III para los registros de enero a septiembre.

Se encontraron 882 filas con valores idénticos. Se conservaron porque los archivos no
incluyeron un identificador único que permitiera confirmar que eran duplicados y no
registros distintos con las mismas características disponibles. No se encontraron
valores nulos en las variables de origen ni registros sin dato de fallecidos.

La variable objetivo se definió como 1 cuando `num_fallecido` fue mayor que cero. Se
identificaron 4.180 registros positivos (9,90 % del total).

## Preparación y evaluación

Se derivaron la hora, la franja horaria, el día de semana, los indicadores de fin de
semana y la pertenencia a la Amazonía. Los códigos de provincia se tradujeron a nombres
DPA. Se utilizaron seis predictores numéricos (`hora_num`, `hora_pico`, `mes`,
`fin_de_semana`, `viernes_a_domingo`, `es_amazonia`) y seis categóricos (`franja_horaria`,
`dia_semana`, `provincia`, `zona`, `clase`, `causa`). No se incluyeron fallecidos,
lesionados, total de víctimas ni el año de origen como predictores.

La partición estratificada dejó 33.771 registros para entrenamiento y 8.443 para prueba;
el conjunto de prueba incluyó 836 registros positivos. Se usó semilla 42 y validación
cruzada estratificada de cinco particiones solo sobre entrenamiento. La imputación de
valores faltantes, el escalado y la codificación se ajustaron dentro de los pipelines de
cada partición.

### Clasificación

| Modelo | Exactitud | Precisión | Recall | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Regresión logística | 0,6743 | 0,1804 | 0,6459 | 0,2820 | 0,7213 | 0,2632 |
| Árbol de decisión | 0,6007 | 0,1572 | 0,6950 | 0,2563 | 0,6896 | 0,2101 |
| Random forest | 0,7050 | 0,1911 | 0,6124 | 0,2913 | 0,7230 | 0,2681 |
| Clasificador base | 0,9010 | 0,0000 | 0,0000 | 0,0000 | 0,5000 | 0,0990 |

En validación cruzada, random forest obtuvo F1 medio de 0,2991 y PR-AUC medio de
0,2671; también obtuvo el mayor ROC-AUC medio (0,7384). En la prueba, obtuvo el mayor
F1 y PR-AUC entre los tres modelos. El árbol alcanzó el recall más alto (0,6950), con
precisión de 0,1572.

El clasificador base tuvo mayor exactitud porque siempre predijo la clase mayoritaria,
pero no detectó ningún registro con fallecidos. Los modelos detectaron positivos, aunque
su precisión fue baja. Por ello, la exactitud no describió por sí sola el desempeño y
los modelos se consideraron exploratorios, no aptos para decisiones operativas sin
validación adicional y ajuste explícito del umbral.

## Clustering y comparación regional

Para K-means se excluyeron la provincia y el indicador de Amazonía, de modo que la
geografía no determinara los grupos de antemano. Se eligieron dos clústeres, que obtuvieron
la mayor silueta evaluada (0,1989):

| Clúster | Registros | Proporción | Con fallecidos |
| --- | ---: | ---: | ---: |
| 0 | 16.092 | 38,12 % | 11,65 % |
| 1 | 26.122 | 61,88 % | 8,83 % |

En la comparación regional, 223 de 615 registros amazónicos tuvieron fallecidos
(36,26 %), frente a 3.957 de 41.599 registros del resto del país (9,51 %). La prueba de
chi-cuadrado dio $\chi^2 = 483,017$ y $p < 0,001$. El resultado mostró asociación en los
datos analizados; no demostró causalidad y dependió de que las observaciones pudieran
tratarse como independientes.

## Limitaciones

- Se analizaron los cierres anuales de 2023 y 2024; los otros cortes trimestrales se
  descargaron, pero no se apilaron porque eran acumulados.
- Los diccionarios incluidos no proporcionaron etiquetas para los códigos de zona,
  clase y causa. Se modelaron como categorías y no se interpretaron sus números. La
  comparabilidad de esos códigos entre años debe confirmarse con un catálogo oficial
  antes de atribuirles significado.
- No hubo identificador de siniestro; por eso las filas idénticas se conservaron y no se
  pudo determinar si correspondían a registros repetidos o a siniestros distintos.
- La prueba fue una partición aleatoria estratificada, no una evaluación temporal sobre
  un año futuro. Las métricas no demostraron capacidad de generalización a periodos
  posteriores.
- La baja precisión indicó que muchos positivos predichos fueron falsos positivos. El
  modelo no se presentó como herramienta de decisión individual.

## Fuentes

- [INEC, Siniestros de tránsito](https://www.ecuadorencifras.gob.ec/estadisticas-siniestros-de-transito/)
- [INEC, Siniestros de tránsito trimestral](https://www.ecuadorencifras.gob.ec/siniestros-transito-trimestral/)
- [INEC, Información histórica de siniestros trimestrales](https://www.ecuadorencifras.gob.ec/informacion-historica-siniestros-transito-trimestral/)