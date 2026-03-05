---
name: ecommerce-bi
description: "Genera informes de Business Intelligence para eCommerce a partir de CSVs de ventas. Analiza Market Basket, RFM, cohortes, CLV, cross-sell, estacionalidad y más. Dos modos: Full (38 análisis) y Lite (20). Output: HTML branded report. Usar cuando el usuario mencione 'business intelligence', 'BI', 'análisis de ventas', 'market basket', 'RFM', 'cohortes', 'CLV', 'lifetime value', 'cross-sell', 'basket analysis', 'afinidad de productos', 'análisis ecommerce', 'informe de ventas', 'análisis de clientes'."
---

# eCommerce Business Intelligence Skill

## Trigger Keywords

- "business intelligence", "BI", "análisis de ventas", "market basket"
- "RFM", "cohortes", "CLV", "lifetime value", "cross-sell"
- "basket analysis", "afinidad de productos", "análisis ecommerce"
- "informe de ventas", "análisis de clientes"

## Workflow

### Paso 1: Detectar CSV

1. Identificar el archivo CSV (el usuario lo indica o está en la carpeta del cliente)
2. Leer headers del CSV
3. Auto-detectar plataforma usando `references/csv_mapping.md`:
   - **Tiendanube**: "Número de orden", "Estado de la orden", "Nombre del producto"
   - **Shopify**: "Name", "Financial Status", "Lineitem name"
   - **WooCommerce**: "Order ID", "Order Status", "Product Name"
   - **Genérico**: mapeo manual si no matchea
4. Detectar encoding (latin-1 vs utf-8) y delimitador (`;` vs `,`)
5. Confirmar al usuario: plataforma detectada, cantidad de filas, rango de fechas

### Paso 2: Elegir modo

Preguntar al usuario usando AskUserQuestion:
- **Lite** (20 análisis) — los más accionables, ideal para primera revisión
- **Full** (38 análisis) — análisis completo con forecasting, clustering, variantes

Default: **Lite**

### Paso 3: Ejecutar análisis

```bash
python3 scripts/bi_analysis.py \
  --csv "PATH_AL_CSV" \
  --mode lite|full \
  --output "/tmp/bi_results.json"
```

El script:
- Auto-detecta encoding y delimitador
- Auto-detecta plataforma y normaliza columnas
- Ejecuta los análisis del modo elegido
- Genera JSON con resultados estructurados
- Sale con código 0 si ok, 1 si error

### Paso 4: Generar HTML

1. Leer el JSON de resultados
2. Usar `references/html_template.md` como base del HTML
3. Armar el informe con:
   - Header: nombre del negocio, rango de fechas, modo, métricas hero
   - Secciones por categoría: Producto, Cliente, Revenue, Geográfico, Operativo, Estratégico
   - Cada análisis: título + tabla/chart + insight + recomendación
   - Footer: branded template
4. Exportar HTML a:

   - Si indica path: usar ese path
   - Si no especifica: preguntar

## Análisis por Modo

### Lite (20 análisis)

| # | Categoría | Análisis |
|---|-----------|----------|
| 1 | Producto | Market Basket Analysis (pares y tríos) |
| 2 | Producto | Afinidad entre categorías |
| 3 | Producto | Ranking de productos |
| 4 | Producto | Productos ancla (cross-sell drivers) |
| 5 | Producto | Long tail 80/20 |
| 6 | Producto | Productos con alta tasa de cancelación |
| 7 | Cliente | Segmentación RFM |
| 8 | Cliente | Customer Lifetime Value |
| 9 | Cliente | Análisis de cohortes (retención) |
| 10 | Cliente | Tasa de recompra y tiempo entre compras |
| 11 | Revenue | Evolución revenue mensual |
| 12 | Revenue | Ticket promedio |
| 13 | Revenue | Revenue por categoría |
| 14 | Revenue | Impacto de descuentos |
| 15 | Geográfico | Heatmap por provincia |
| 16 | Geográfico | Costo de envío vs conversión |
| 17 | Operativo | Tasa de cancelación |
| 18 | Operativo | Mix de medios de pago |
| 19 | Estratégico | Oportunidades de bundling |
| 20 | Estratégico | Estacionalidad |

### Full (38) = Lite + 18 adicionales

| # | Categoría | Análisis |
|---|-----------|----------|
| 21 | Producto | Afinidad entre colores |
| 22 | Producto | Afinidad entre talles |
| 23 | Producto | Análisis de SKU/variantes |
| 24 | Producto | Ciclo de vida del producto |
| 25 | Cliente | Patrón de upgrade |
| 26 | Cliente | Clientes VIP (top 10%) |
| 27 | Cliente | Análisis de churn |
| 28 | Revenue | Revenue por canal |
| 29 | Revenue | Análisis de precio |
| 30 | Geográfico | Penetración por ciudad |
| 31 | Geográfico | Medio de envío por zona |
| 32 | Operativo | Tiempo de fulfillment |
| 33 | Operativo | Análisis de canal |
| 34 | Operativo | Eficiencia de envío gratis |
| 35 | Estratégico | Forecast de ventas |
| 36 | Estratégico | Recomendación de cross-sell |
| 37 | Estratégico | Análisis de pricing |
| 38 | Estratégico | Identificación de nichos |

## Reglas

- **SIEMPRE** ejecutar `bi_analysis.py` — no calcular análisis manualmente
- El script maneja todas las plataformas (Tiendanube, Shopify, WooCommerce, genérico)
- Si un análisis falla por datos faltantes, el JSON lo marca como `"status": "skipped"` con razón
- El HTML debe seguir **exactamente** el branding de `html_template.md`
- Insights deben ser accionables: no describir datos, sino qué hacer con ellos
- Market Basket: solo mostrar asociaciones con support > 1% y lift > 1.0
- RFM: usar labels estándar (Champions, Loyal, Potential Loyal, New, Promising, Need Attention, About to Sleep, At Risk, Can't Lose, Hibernating, Lost)

## Referencias

- `references/analysis_catalog.md` — Metodología detallada de cada análisis
- `references/csv_mapping.md` — Mapeo de columnas por plataforma
- `references/html_template.md` — Template HTML
