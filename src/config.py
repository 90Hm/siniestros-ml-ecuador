"""Configuración central del proyecto.

Todo lo que el grupo pueda necesitar ajustar está en este archivo:
rutas, semilla, proporciones y el mapeo de columnas del INEC.
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Se pueden cambiar con variables de entorno, útil para probar con datos simulados
DATOS_CRUDOS = Path(os.environ.get("SINIESTROS_DATA_DIR", RAIZ / "data" / "raw"))
DATOS_PROCESADOS = Path(os.environ.get("SINIESTROS_PROC_DIR", RAIZ / "data" / "processed"))
SALIDAS = Path(os.environ.get("SINIESTROS_OUT_DIR", RAIZ / "outputs"))
FIGURAS = SALIDAS / "figuras"
TABLAS = SALIDAS / "tablas"

for _ruta in (DATOS_CRUDOS, DATOS_PROCESADOS, FIGURAS, TABLAS):
    _ruta.mkdir(parents=True, exist_ok=True)

# Parámetros del experimento
SEMILLA = 42
PROPORCION_PRUEBA = 0.20      # 80 % entrenamiento, 20 % prueba
K_PARTICIONES = 5             # validación cruzada estratificada
MUESTRA_SILUETA = 5000        # filas usadas para calcular la silueta en K-means
K_MIN, K_MAX = 2, 8           # rango de clústeres a evaluar
TRIMESTRE_ANALISIS = 4

# Patrones (expresiones regulares sobre el nombre normalizado de la columna).
# El código prueba los patrones en orden y toma la primera columna que coincida.
# Si el INEC nombra distinto una variable, se corrige aquí o en MAPEO_MANUAL.
PATRONES = {
    "fallecidos": [r"fallec.*situ", r"fallec", r"muert"],
    "lesionados": [r"lesion", r"herid"],
    "fecha": [r"^fecha", r"fecha"],
    "anio": [r"^anio$", r"^ano$", r"^year$", r"^anio_"],
    "mes": [r"^mes$", r"^mes_"],
    "dia": [r"^dia$", r"^dia_", r"dia_sem", r"dia_de"],
    "hora": [r"^hora$", r"^hora_", r"hora"],
    "provincia": [r"^prov", r"provincia"],
    "zona": [r"^zona", r"zona", r"area", r"urbano"],
    "clase": [r"clase.*sin", r"clase", r"tipo.*sin", r"tipo_de_sin"],
    "causa": [r"causa.*prob", r"causa"],
}

# Si la detección automática se equivoca, se fuerza aquí. Ejemplo:
# MAPEO_MANUAL = {"fallecidos": "num_fallecidos_in_situ", "hora": "hora_siniestro"}
MAPEO_MANUAL = {}

# Columnas que nunca deben entrar como variables explicativas porque revelan
# el resultado que se quiere predecir (fuga de información) o no aportan.
EXCLUIR_COMO_FEATURE = [
    r"fallec", r"lesion", r"herid", r"victim", r"muert", r"ileso",
    r"letal", r"gravedad", r"archivo_origen", r"^id", r"_id$", r"codigo",
    r"fecha", r"canton", r"parroquia", r"observ",
]

# Variables categóricas adicionales a incluir si existen (nombres ya normalizados)
CATEGORICAS_EXTRA = []

# Máximo de categorías distintas para incluir automáticamente una columna de texto
MAX_CATEGORIAS = 40

# Textos que el INEC o la ANT pueden usar para indicar dato faltante
VALORES_FALTANTES = {
    "", "NA", "N/A", "NAN", "NULL", "NONE", "S/D", "SD", "SIN DATO", "SIN DATOS",
    "NO IDENTIFICADO", "NO IDENTIFICADA", "NO DISPONIBLE", "DESCONOCIDO",
    "NO REGISTRA", "SIN INFORMACION", "NO ESPECIFICADO",
}

# Provincias de la Región Amazónica Ecuatoriana
PROVINCIAS_AMAZONIA = [
    "MORONA SANTIAGO", "NAPO", "PASTAZA", "ZAMORA CHINCHIPE", "SUCUMBIOS", "ORELLANA",
]

CODIGOS_PROVINCIA = {
    1: "AZUAY", 2: "BOLIVAR", 3: "CANAR", 4: "CARCHI", 5: "COTOPAXI",
    6: "CHIMBORAZO", 7: "EL ORO", 8: "ESMERALDAS", 9: "GUAYAS", 10: "IMBABURA",
    11: "LOJA", 12: "LOS RIOS", 13: "MANABI", 14: "MORONA SANTIAGO", 15: "NAPO",
    16: "PASTAZA", 17: "PICHINCHA", 18: "TUNGURAHUA", 19: "ZAMORA CHINCHIPE",
    20: "GALAPAGOS", 21: "SUCUMBIOS", 22: "ORELLANA", 23: "SANTO DOMINGO DE LOS TSACHILAS",
    24: "SANTA ELENA",
}
