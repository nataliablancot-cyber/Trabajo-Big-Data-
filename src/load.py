"""
load.py
=======
Persona 3 — Carga del modelo dimensional en SQLite
Proyecto Final Big Data — Precios de Carburantes en Europa

Ejecutar DESPUÉS de transform_star.py
Entrada : data/final/*.csv
Salida  : data/carburantes_europa.db  (SQLite)
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# ── Rutas ──────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent.parent
FINAL_DIR = BASE_DIR / "data" / "final"
DB_PATH   = BASE_DIR / "data" / "carburantes_europa.db"

print(f"\n── Conectando a SQLite: {DB_PATH} ──")
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()
cur.execute("PRAGMA foreign_keys = ON;")

# ════════════════════════════════════════════════════════════════════════════
# 1. DDL — Creación de tablas (si no existen)
# ════════════════════════════════════════════════════════════════════════════
DDL = """
-- ── Dimensión Tiempo ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_tiempo (
    sk_tiempo   INTEGER PRIMARY KEY,
    fecha       TEXT    NOT NULL UNIQUE,
    anio        INTEGER NOT NULL,
    trimestre   INTEGER NOT NULL,
    mes         INTEGER NOT NULL,
    semana      INTEGER NOT NULL,
    dia_semana  TEXT    NOT NULL,
    es_festivo  INTEGER NOT NULL DEFAULT 0   -- 0=False 1=True
);

-- ── Dimensión Geografía ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_geografia (
    sk_geografia    INTEGER PRIMARY KEY,
    country_code    TEXT    NOT NULL UNIQUE,
    country_code_2  TEXT,
    country_name    TEXT    NOT NULL,
    region          TEXT
);

-- ── Dimensión Producto ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_producto (
    sk_producto  INTEGER PRIMARY KEY,
    fuel_type    TEXT    NOT NULL UNIQUE,
    nombre_es    TEXT    NOT NULL,
    descripcion  TEXT,
    categoria    TEXT,
    tipo_energia TEXT
);

-- ── Dimensión Indicadores ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_indicadores (
    sk_indicador               INTEGER PRIMARY KEY,
    country_code               TEXT    NOT NULL,
    year                       INTEGER NOT NULL,
    pib_per_capita_usd         REAL,
    dependencia_energetica_pct REAL,
    UNIQUE (country_code, year)
);

-- ── Dimensión Fuente ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_fuente (
    sk_fuente  INTEGER PRIMARY KEY,
    nombre     TEXT    NOT NULL,
    organismo  TEXT,
    formato    TEXT,
    frecuencia TEXT,
    url        TEXT,
    licencia   TEXT
);

-- ── Tabla de Hechos ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_precios_carburante (
    sk_hecho             INTEGER PRIMARY KEY,
    sk_tiempo            INTEGER NOT NULL REFERENCES dim_tiempo(sk_tiempo),
    sk_geografia         INTEGER NOT NULL REFERENCES dim_geografia(sk_geografia),
    sk_producto          INTEGER NOT NULL REFERENCES dim_producto(sk_producto),
    sk_indicador         INTEGER          REFERENCES dim_indicadores(sk_indicador),
    sk_fuente            INTEGER NOT NULL REFERENCES dim_fuente(sk_fuente),
    -- Medidas
    precio_eur_litro     REAL    NOT NULL,
    impuesto_eur_litro   REAL    NOT NULL,
    precio_sin_impuesto  REAL    NOT NULL,
    pct_impuesto         REAL,
    tasa_impuesto_pct    REAL,
    -- Trazabilidad
    source_id            TEXT,
    load_timestamp       TEXT
);
"""

print("── Creando esquema SQL ──")
cur.executescript(DDL)
conn.commit()
print("   ✅ Tablas creadas (o ya existían)")

# ════════════════════════════════════════════════════════════════════════════
# 2. Carga de dimensiones (primero) y tabla de hechos (después)
# ════════════════════════════════════════════════════════════════════════════

def cargar_tabla(nombre_csv, tabla_sql, conn):
    """Carga un CSV en la tabla SQLite correspondiente."""
    ruta = FINAL_DIR / nombre_csv
    df   = pd.read_csv(ruta)
    # es_festivo: convertir bool a int para SQLite
    if "es_festivo" in df.columns:
        df["es_festivo"] = df["es_festivo"].astype(int)
    df.to_sql(tabla_sql, conn, if_exists="replace", index=False)
    n = len(df)
    print(f"   ✅ {tabla_sql:<35} {n:>7} filas cargadas")
    return n

print("\n── Cargando dimensiones ──")
resumen = {}
resumen["dim_tiempo"]        = cargar_tabla("dim_tiempo.csv",        "dim_tiempo",        conn)
resumen["dim_geografia"]     = cargar_tabla("dim_geografia.csv",     "dim_geografia",     conn)
resumen["dim_producto"]      = cargar_tabla("dim_producto.csv",      "dim_producto",      conn)
resumen["dim_indicadores"]   = cargar_tabla("dim_indicadores.csv",   "dim_indicadores",   conn)
resumen["dim_fuente"]        = cargar_tabla("dim_fuente.csv",        "dim_fuente",        conn)

print("\n── Cargando tabla de hechos ──")
resumen["fact_precios_carburante"] = cargar_tabla(
    "fact_precios_carburante.csv", "fact_precios_carburante", conn)

conn.commit()

# ════════════════════════════════════════════════════════════════════════════
# 3. Verificación con COUNT(*)
# ════════════════════════════════════════════════════════════════════════════
print("\n── Verificación COUNT(*) ──")
print(f"{'Tabla':<35} {'CSV':>8} {'SQL':>8} {'OK':>4}")
print("-" * 58)
for tabla, n_csv in resumen.items():
    n_sql = cur.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    ok    = "✅" if n_csv == n_sql else "❌"
    print(f"{tabla:<35} {n_csv:>8} {n_sql:>8} {ok:>4}")

# ════════════════════════════════════════════════════════════════════════════
# 4. Consultas de ejemplo para el informe
# ════════════════════════════════════════════════════════════════════════════
print("\n── Consultas de ejemplo ──")

q1 = """
SELECT g.country_name, AVG(f.precio_eur_litro) AS precio_medio
FROM fact_precios_carburante f
JOIN dim_geografia g ON f.sk_geografia = g.sk_geografia
JOIN dim_producto  p ON f.sk_producto  = p.sk_producto
WHERE p.fuel_type = 'gasoline'
GROUP BY g.country_name
ORDER BY precio_medio DESC
LIMIT 5;
"""
print("\nTop 5 países con mayor precio medio de gasolina:")
for row in cur.execute(q1):
    print(f"  {row[0]:<20} {row[1]:.4f} €/l")

q2 = """
SELECT t.anio, ROUND(AVG(f.pct_impuesto),2) AS pct_imp_medio
FROM fact_precios_carburante f
JOIN dim_tiempo t ON f.sk_tiempo = t.sk_tiempo
GROUP BY t.anio
ORDER BY t.anio;
"""
print("\nEvolucion anual del % de impuesto medio:")
for row in cur.execute(q2):
    print(f"  {row[0]}  {row[1]}%")

conn.close()
print(f"\n✅ Base de datos disponible en: {DB_PATH}")
