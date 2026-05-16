"""
transform_star.py
=================
Persona 3 — Construcción del modelo dimensional (esquema en estrella)
Proyecto Final Big Data — Precios de Carburantes en Europa

Entrada : data/processed/dataset_unificado.csv
Salida  : data/final/
            dim_tiempo.csv
            dim_geografia.csv
            dim_producto.csv
            dim_indicadores.csv
            dim_fuente.csv
            fact_precios_carburante.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# ── Rutas ──────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "processed" / "dataset_unificado.csv"
FINAL_DIR  = BASE_DIR / "data" / "final"
FINAL_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE   = BASE_DIR / "data" / "processed" / "pipeline_tracking.json"

# ── Tracking helper ────────────────────────────────────────────────────────
tracking = []

def log_step(fase, entrada, salida, descartados=0, motivo=""):
    tracking.append({
        "fase": fase,
        "timestamp": datetime.utcnow().isoformat(),
        "registros_entrada": int(entrada),
        "registros_salida": int(salida),
        "descartados": int(descartados),
        "motivo": motivo
    })
    print(f"[{fase}] entrada={entrada} | salida={salida} | desc={descartados} | {motivo}")

# ════════════════════════════════════════════════════════════════════════════
# 1. CARGA
# ════════════════════════════════════════════════════════════════════════════
print("\n── Cargando dataset_unificado.csv ──")
df = pd.read_csv(INPUT_FILE, parse_dates=["date"])
n0 = len(df)
log_step("LOAD_UNIFICADO", n0, n0, 0, "Lectura del dataset unificado")

# ════════════════════════════════════════════════════════════════════════════
# 2. LIMPIEZA PREVIA
# ════════════════════════════════════════════════════════════════════════════
n_antes = len(df)
df = df.dropna(subset=["country_name"])
log_step("CLEAN_country_name_nulo", n_antes, len(df),
         n_antes - len(df), "Filas sin country_name eliminadas")

# Imputación de indicadores con media país+año, luego mediana global
for col in ["energy_dependency", "gdp_per_capita"]:
    df[col] = df.groupby(["country_code", "year"])[col].transform(
        lambda x: x.fillna(x.mean())
    )
    df[col] = df[col].fillna(df[col].median())

log_step("CLEAN_imputacion_indicadores", len(df), len(df), 0,
         "energy_dependency y gdp_per_capita imputados con media país+año")

df["source_id"]      = "dataset_unificado"
df["load_timestamp"] = datetime.utcnow().isoformat()
n_clean = len(df)

# ════════════════════════════════════════════════════════════════════════════
# 3. DIM_TIEMPO
# ════════════════════════════════════════════════════════════════════════════
print("\n── Construyendo DIM_TIEMPO ──")
fechas = df["date"].drop_duplicates().dropna().sort_values()
dim_tiempo = pd.DataFrame({
    "fecha"     : fechas,
    "anio"      : fechas.dt.year.astype("int16"),
    "trimestre" : fechas.dt.quarter.astype("int8"),
    "mes"       : fechas.dt.month.astype("int8"),
    "semana"    : fechas.dt.isocalendar().week.astype("int8"),
    "dia_semana": fechas.dt.day_name(),
    "es_festivo": False
}).reset_index(drop=True)
dim_tiempo.insert(0, "sk_tiempo", range(1, len(dim_tiempo) + 1))
dim_tiempo.to_csv(FINAL_DIR / "dim_tiempo.csv", index=False)
log_step("BUILD_DIM_TIEMPO", n_clean, len(dim_tiempo), 0,
         f"{len(dim_tiempo)} fechas únicas (2005-2026)")

# ════════════════════════════════════════════════════════════════════════════
# 4. DIM_GEOGRAFIA
# ════════════════════════════════════════════════════════════════════════════
print("\n── Construyendo DIM_GEOGRAFIA ──")
dim_geo = (df[["country_code","country_code_2","country_name"]]
           .drop_duplicates().sort_values("country_name").reset_index(drop=True))
dim_geo.insert(0, "sk_geografia", range(1, len(dim_geo) + 1))

region_map = {
    "AUT":"Europa Occidental","BEL":"Europa Occidental","DEU":"Europa Occidental",
    "FRA":"Europa Occidental","LUX":"Europa Occidental","NLD":"Europa Occidental",
    "IRL":"Europa Occidental","GBR":"Europa Occidental",
    "DNK":"Europa Nórdica","FIN":"Europa Nórdica","SWE":"Europa Nórdica",
    "PRT":"Europa Sur","ESP":"Europa Sur","ITA":"Europa Sur",
    "GRC":"Europa Sur","CYP":"Europa Sur","MLT":"Europa Sur",
    "POL":"Europa Central","CZE":"Europa Central","SVK":"Europa Central",
    "HUN":"Europa Central","SVN":"Europa Central","HRV":"Europa Central",
    "ROU":"Europa Oriental","BGR":"Europa Oriental",
    "EST":"Europa Báltica","LVA":"Europa Báltica","LTU":"Europa Báltica"
}
dim_geo["region"] = dim_geo["country_code"].map(region_map).fillna("Europa")
dim_geo.to_csv(FINAL_DIR / "dim_geografia.csv", index=False)
log_step("BUILD_DIM_GEOGRAFIA", n_clean, len(dim_geo), 0,
         f"{len(dim_geo)} países únicos de la UE")

# ════════════════════════════════════════════════════════════════════════════
# 5. DIM_PRODUCTO
# ════════════════════════════════════════════════════════════════════════════
print("\n── Construyendo DIM_PRODUCTO ──")
dim_producto = pd.DataFrame([
    {"sk_producto":1,"fuel_type":"diesel","nombre_es":"Gasóleo",
     "descripcion":"Combustible destilado para motores diésel",
     "categoria":"Destilado medio","tipo_energia":"Fósil"},
    {"sk_producto":2,"fuel_type":"gasoline","nombre_es":"Gasolina",
     "descripcion":"Combustible nafta para motores de explosión",
     "categoria":"Nafta","tipo_energia":"Fósil"},
])
dim_producto.to_csv(FINAL_DIR / "dim_producto.csv", index=False)
log_step("BUILD_DIM_PRODUCTO", n_clean, len(dim_producto), 0,
         "2 tipos de carburante: diesel y gasolina")

# ════════════════════════════════════════════════════════════════════════════
# 6. DIM_INDICADORES
# ════════════════════════════════════════════════════════════════════════════
print("\n── Construyendo DIM_INDICADORES ──")
dim_ind = (df[["country_code","year","gdp_per_capita","energy_dependency"]]
           .drop_duplicates(subset=["country_code","year"])
           .sort_values(["country_code","year"]).reset_index(drop=True))
dim_ind.insert(0, "sk_indicador", range(1, len(dim_ind) + 1))
dim_ind = dim_ind.rename(columns={
    "gdp_per_capita"   : "pib_per_capita_usd",
    "energy_dependency": "dependencia_energetica_pct"
})
dim_ind.to_csv(FINAL_DIR / "dim_indicadores.csv", index=False)
log_step("BUILD_DIM_INDICADORES", n_clean, len(dim_ind), 0,
         f"{len(dim_ind)} combinaciones país-año")

# ════════════════════════════════════════════════════════════════════════════
# 7. DIM_FUENTE
# ════════════════════════════════════════════════════════════════════════════
print("\n── Construyendo DIM_FUENTE ──")
dim_fuente = pd.DataFrame([
    {"sk_fuente":1,"nombre":"Weekly Oil Bulletin Prices",
     "organismo":"Comisión Europea / DG Energy","formato":"Excel/CSV",
     "frecuencia":"Semanal",
     "url":"https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en",
     "licencia":"Open Data UE"},
    {"sk_fuente":2,"nombre":"Oil Bulletin Duties and Taxes",
     "organismo":"Comisión Europea / DG Energy","formato":"Excel",
     "frecuencia":"Semestral",
     "url":"https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en",
     "licencia":"Open Data UE"},
    {"sk_fuente":3,"nombre":"World Bank GDP per capita",
     "organismo":"Banco Mundial","formato":"CSV","frecuencia":"Anual",
     "url":"https://data.worldbank.org/indicator/NY.GDP.PCAP.CD",
     "licencia":"CC BY 4.0"},
    {"sk_fuente":4,"nombre":"Eurostat Energy Dependency",
     "organismo":"Eurostat","formato":"CSV","frecuencia":"Anual",
     "url":"https://ec.europa.eu/eurostat/databrowser/view/nrg_ind_id",
     "licencia":"Open Data UE"},
])
dim_fuente.to_csv(FINAL_DIR / "dim_fuente.csv", index=False)
log_step("BUILD_DIM_FUENTE", n_clean, len(dim_fuente), 0, "4 fuentes documentadas")

# ════════════════════════════════════════════════════════════════════════════
# 8. FACT_PRECIOS_CARBURANTE
# ════════════════════════════════════════════════════════════════════════════
print("\n── Construyendo FACT_PRECIOS_CARBURANTE ──")

tiempo_map   = dim_tiempo.set_index("fecha")["sk_tiempo"]
geo_map      = dim_geo.set_index("country_code")["sk_geografia"]
producto_map = dim_producto.set_index("fuel_type")["sk_producto"]
ind_map      = dim_ind.set_index(["country_code","year"])["sk_indicador"]

fact = df.copy()
fact["sk_tiempo"]    = fact["date"].map(tiempo_map)
fact["sk_geografia"] = fact["country_code"].map(geo_map)
fact["sk_producto"]  = fact["fuel_type"].map(producto_map)
fact["sk_indicador"] = [ind_map.get((r.country_code, r.year), pd.NA)
                        for r in fact.itertuples()]
fact["sk_fuente"]    = 1  # Weekly Oil Bulletin

# Medidas derivadas
fact["precio_sin_impuesto"] = (fact["price_eur_litre"] - fact["tax_eur_litre"]).round(4)
fact["pct_impuesto"]        = ((fact["tax_eur_litre"] / fact["price_eur_litre"]) * 100).round(2)

fact_final = fact[[
    "sk_tiempo","sk_geografia","sk_producto","sk_indicador","sk_fuente",
    "price_eur_litre","tax_eur_litre","precio_sin_impuesto",
    "pct_impuesto","tax_value","source_id","load_timestamp"
]].rename(columns={
    "price_eur_litre": "precio_eur_litro",
    "tax_eur_litre"  : "impuesto_eur_litro",
    "tax_value"      : "tasa_impuesto_pct"
}).reset_index(drop=True)

fact_final.insert(0, "sk_hecho", range(1, len(fact_final) + 1))

# Verificar FK nulos
for col in ["sk_tiempo","sk_geografia","sk_producto","sk_indicador"]:
    n_null = fact_final[col].isnull().sum()
    if n_null > 0:
        print(f"  ⚠ {col}: {n_null} FK nulas — revisar")

fact_final.to_csv(FINAL_DIR / "fact_precios_carburante.csv", index=False)
log_step("BUILD_FACT", n_clean, len(fact_final), 0,
         "Tabla de hechos: 5 FK, 5 medidas, trazabilidad completa")

# ════════════════════════════════════════════════════════════════════════════
# 9. GUARDAR TRACKING
# ════════════════════════════════════════════════════════════════════════════
if LOG_FILE.exists():
    with open(LOG_FILE) as f:
        existing = json.load(f)
else:
    existing = []
existing.extend(tracking)
with open(LOG_FILE, "w") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

print("\n✅ Modelo estrella generado en data/final/")
print(f"   dim_tiempo({len(dim_tiempo)}) | dim_geografia({len(dim_geo)}) | "
      f"dim_producto({len(dim_producto)}) | dim_indicadores({len(dim_ind)}) | "
      f"dim_fuente({len(dim_fuente)}) | fact({len(fact_final)})")
