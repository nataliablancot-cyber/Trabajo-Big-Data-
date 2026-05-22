import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

def tabla(ax, x, y, w, titulo, campos, color_header, color_body):
    h_header = 0.5
    h_row = 0.38
    total_h = h_header + len(campos) * h_row + 0.2
    # Cuerpo
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, total_h,
        boxstyle="round,pad=0.05",
        facecolor=color_body, edgecolor='#555', linewidth=1.5))
    # Cabecera
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y + total_h - h_header), w, h_header,
        boxstyle="round,pad=0.05",
        facecolor=color_header, edgecolor='#555', linewidth=1.5))
    ax.text(x + w/2, y + total_h - h_header/2, titulo,
            ha='center', va='center', fontsize=8.5, fontweight='bold', color='white')
    for i, campo in enumerate(campos):
        ax.text(x + 0.15, y + total_h - h_header - 0.1 - i*h_row - h_row/2,
                campo, fontsize=7.5, va='center', color='#222')

def flecha(ax, x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle='->', color='#333', lw=1.8))

# ── Posiciones ──────────────────────────────────────────────────────────
# FACT centro
tabla(ax, 5.8, 3.5, 4.4, 'FACT_PRECIOS_CARBURANTE',
    ['sk_hecho (PK)', 'sk_tiempo (FK)', 'sk_geografia (FK)',
     'sk_producto (FK)', 'sk_indicador (FK)', 'sk_fuente (FK)',
     '── MEDIDAS ──',
     'precio_eur_litro', 'impuesto_eur_litro',
     'precio_sin_impuesto', 'pct_impuesto',
     '── TRAZABILIDAD ──',
     'source_id', 'load_timestamp'],
    '#2471A3', '#D6EAF8')

# DIM_TIEMPO arriba
tabla(ax, 5.8, 9.0, 4.4, 'DIM_TIEMPO',
    ['sk_tiempo (PK)', 'fecha DATE', 'anio', 'trimestre',
     'mes', 'semana', 'dia_semana', 'es_festivo'],
    '#1E8449', '#D5F5E3')

# DIM_GEOGRAFIA izquierda
tabla(ax, 0.3, 5.5, 4.0, 'DIM_GEOGRAFIA',
    ['sk_geografia (PK)', 'country_code', 'country_code_2',
     'country_name', 'region'],
    '#1E8449', '#D5F5E3')

# DIM_PRODUCTO derecha
tabla(ax, 11.7, 5.5, 4.0, 'DIM_PRODUCTO',
    ['sk_producto (PK)', 'fuel_type', 'nombre_es',
     'descripcion', 'categoria', 'tipo_energia'],
    '#1E8449', '#D5F5E3')

# DIM_INDICADORES abajo izquierda
tabla(ax, 0.3, 0.5, 4.5, 'DIM_INDICADORES',
    ['sk_indicador (PK)', 'country_code', 'year',
     'pib_per_capita_usd', 'dependencia_energetica_pct'],
    '#B7770D', '#FEF9E7')

# DIM_FUENTE abajo derecha
tabla(ax, 11.2, 0.5, 4.5, 'DIM_FUENTE',
    ['sk_fuente (PK)', 'nombre', 'organismo',
     'formato', 'frecuencia', 'url', 'licencia'],
    '#B7770D', '#FEF9E7')

# ── Flechas FACT → dimensiones ──────────────────────────────────────────
flecha(ax, 8.0, 9.0,  8.0,  8.85)   # → DIM_TIEMPO
flecha(ax, 5.8, 6.8,  4.3,  6.8)    # → DIM_GEOGRAFIA
flecha(ax, 10.2, 6.8, 11.7, 6.8)    # → DIM_PRODUCTO
flecha(ax, 6.5, 3.5,  3.8,  2.5)    # → DIM_INDICADORES
flecha(ax, 9.5, 3.5,  12.2, 2.5)    # → DIM_FUENTE

plt.title('Diagrama en Estrella — Precios de Carburantes en Europa\n'
          'Granularidad: 1 precio · 1 país · 1 semana · 1 carburante  |  55.093 hechos',
          fontsize=12, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig('diagrama_estrella.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
print("✅ Guardado como diagrama_estrella.png")
