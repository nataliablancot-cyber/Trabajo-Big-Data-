# Trabajo Final Big Data — Precios de Carburantes en Europa
**Asignatura:** Introducción a los Sistemas Big Data — Valor de la Información  
**Curso:** 2025-2026

## Descripción
Pipeline ETL completo que transforma datos de precios de carburantes semanales de la UE
(2005-2026) junto con indicadores macroeconómicos en un modelo dimensional (estrella)
almacenado en SQLite y analizado con PySpark en Google Colab.

## Estructura del repositorio
```
Trabajo-Big-Data-/
├── data/
│   ├── raw/                        ← Fuentes originales sin modificar
│   │   ├── Weekly_Oil_Bulletin_Prices_His...
│   │   ├── Oil_Bulletin_Duties_and_taxes.x...
│   │   ├── API_NY.GDP.PCAP.CD_DS2_en_...
│   │   └── nrg_ind_id$defaultview_linear...
│   ├── processed/                  ← Datos intermedios
│   │   ├── dataset_unificado.csv
│   │   ├── impuestos_procesados.csv
│   │   └── pipeline_tracking.json
│   └── final/                      ← Tablas del modelo estrella
│       ├── dim_tiempo.csv
│       ├── dim_geografia.csv
│       ├── dim_producto.csv
│       ├── dim_indicadores.csv
│       ├── dim_fuente.csv
│       └── fact_precios_carburante.csv
├── src/
│   ├── transform_star.py           ← Persona 3: modelo dimensional
│   └── load.py                     ← Persona 3: carga en SQLite
├── notebooks/
│   ├── 01_analisis_inicial_fuentes.ipynb   ← Persona 1
│   ├── 02_etl_completo_persona_2.ipynb     ← Persona 2
│   └── 03_pyspark_cubo_colab.ipynb         ← Persona 4
├── outputs/tablas/
│   └── tabla_calidad_origenes.csv
├── requirements.txt
└── .gitignore
```

## Fuentes de datos
| # | Fuente | Organismo | Formato | Frecuencia | Licencia |
|---|--------|-----------|---------|------------|----------|
| 1 | Weekly Oil Bulletin Prices | Comisión Europea | Excel/CSV | Semanal | Open Data UE |
| 2 | Oil Bulletin Duties & Taxes | Comisión Europea | Excel | Semestral | Open Data UE |
| 3 | GDP per capita | Banco Mundial | CSV | Anual | CC BY 4.0 |
| 4 | Energy Dependency | Eurostat | CSV | Anual | Open Data UE |

## Modelo dimensional
- **Granularidad FACT:** 1 registro = precio de 1 tipo de carburante en 1 país en 1 semana
- **Tabla de hechos:** `fact_precios_carburante` (56k registros)
- **Dimensiones:** `dim_tiempo` · `dim_geografia` · `dim_producto` · `dim_indicadores` · `dim_fuente`

## Cómo ejecutar
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Generar modelo estrella y CSV finales
python src/transform_star.py

# 3. Cargar en SQLite
python src/load.py
```

## Cuaderno PySpark
El análisis final está en Google Colab:  
`notebooks/03_pyspark_cubo_colab.ipynb`  
Lee los CSV directamente desde la URL raw de este repositorio.

## Tecnologías
Python 3.10 · pandas · SQLite · PySpark · Google Colab · GitHub
