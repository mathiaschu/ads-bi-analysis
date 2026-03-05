---
name: google-ads-html
description: "Genera informes HTML branded para análisis de Google Ads. Soporta CSV export de Google Ads + MCP API (GAQL). Dos modos: Full (30 análisis) y Lite (18). Cubre Search, Shopping, PMax y cuentas mixtas. Usar cuando el usuario mencione 'informe google ads', 'reporte google ads html', 'google ads report', 'análisis google ads html', 'google ads html', 'reporte de campañas google'."
---

# Google Ads HTML Report Skill

## Trigger Keywords

- "informe google ads", "reporte google ads html", "google ads report"
- "análisis google ads html", "google ads html", "reporte de campañas google"
- "informe search ads", "informe pmax", "informe shopping"

## Relación con otras Skills

- **`google-ads-analyzer/`** tiene 12 docs de referencia conceptual (Quality Score, Smart Bidding, PMax, Impression Share, etc.)
- **Esta skill CONSUME** esos conceptos para generar el HTML
- Referenciar `../analyzer/references/` cuando se necesite contexto teórico

## Workflow

### Paso 1: Detectar fuente de datos

1. **CSV**: Leer headers, detectar formato Google Ads (columnas como "Campaign", "Impressions", "Clicks", "Cost")
2. **MCP**: Usar `mcp__google-ads__search` con queries GAQL para obtener datos vía API
3. Puede combinar ambos (CSV histórico + MCP reciente)
4. **Tipo de export**: detectar si es campaign report, keyword report, search term report o ad report según headers (ver `references/csv_mapping.md`)
5. **Múltiples CSVs**: Google Ads exporta reports separados — el script acepta `--input` como directorio o múltiples archivos separados por coma
6. Confirmar al usuario: fuente detectada, tipo de cuenta (Search/Shopping/PMax/mixta), cantidad de filas, rango de fechas

### Paso 2: Detectar tipo de cuenta

1. Revisar nombres de campañas para detectar tipos: Search, Shopping, PMax, Display, Video, Demand Gen
2. Identificar si es cuenta mixta (múltiples tipos)
3. Esto determina qué análisis aplican (ej: QS solo aplica a Search, Asset Groups solo a PMax)

### Paso 3: Elegir modo

Preguntar al usuario usando AskUserQuestion:
- **Lite** (18 análisis) — overview ejecutivo, los más accionables
- **Full** (30 análisis) — Lite + 12 análisis avanzados (PMax deep-dive, Smart Bidding, Auction Insights, etc.)

Default: **Lite**

### Paso 4: Ejecutar análisis

```bash
python3 scripts/google_ads_analysis.py \
  --input "PATH_AL_CSV_O_JSON" \
  --mode lite|full \
  --currency auto \
  --output "/tmp/google_ads_results.json"
```

El script:
- Auto-detecta tipo de export (campaign/keyword/search term/ad), encoding, delimitador
- Auto-detecta moneda desde headers o datos
- Normaliza columnas a nombres canónicos
- Ejecuta los análisis del modo elegido
- Marca últimos 7 días con `conversion_lag_warning`
- Genera JSON con resultados estructurados
- Sale con código 0 si ok, 1 si error

### Paso 5: Generar HTML

1. Leer el JSON de resultados
2. Usar `references/html_template.md` como base del HTML
3. Formato: **slides full-screen** con navegación por teclado (← → + números)
4. Cada slide = 1 análisis (título + visualización + insight + recomendación)
5. Semáforo de benchmarks (verde/amarillo/rojo)
6. Banner de conversion lag warning para últimos 7 días
7. Exportar HTML a:

   - Si indica path: usar ese path
   - Si no especifica: preguntar

## Análisis por Modo

### Lite (18 análisis)

| # | Categoría | Análisis |
|---|-----------|----------|
| 1 | Overview | Dashboard ejecutivo (spend, conversions, CPA, ROAS, clicks, impressions) |
| 2 | Overview | Semáforo benchmarks (CTR, CPC, Conv Rate, IS vs benchmarks industria) |
| 3 | Overview | Evolución diaria de métricas clave (spend, conversions, CPA) |
| 4 | Campañas | Performance por campaña (tabla + semáforo + tipo de campaña) |
| 5 | Campañas | Distribución de budget vs resultados (spend vs ROAS scatter) |
| 6 | Campañas | Smart Bidding status y evaluación (tCPA/tROAS target vs actual) |
| 7 | Keywords | Quality Score distribution (histograma + breakdown por componente) |
| 8 | Keywords | Top keywords por conversión (tabla con QS, CPC, Conv Rate, CPA) |
| 9 | Keywords | Impression Share analysis (IS, IS Lost Budget, IS Lost Rank) |
| 10 | Search Terms | Wasted spend analysis (search terms sin conversiones, gasto acumulado) |
| 11 | Search Terms | Oportunidades de keywords (search terms con conversiones no cubiertas) |
| 12 | Ads | Ranking de ads/RSA por eficiencia (CTR, Conv Rate, CPA) |
| 13 | Ads | Ad strength distribution (Excellent/Good/Average/Poor) |
| 14 | Funnel | Funnel completo (impressions → clicks → conversions) con drop-off |
| 15 | Temporal | Estacionalidad (día de semana + hora del día) |
| 16 | Geo | Performance por ubicación geográfica |
| 17 | Device | Performance por dispositivo (Mobile/Desktop/Tablet) |
| 18 | Estratégico | Top 5 recomendaciones priorizadas (impacto + esfuerzo) |

### Full (30) = Lite + 12 adicionales

| # | Categoría | Análisis |
|---|-----------|----------|
| 19 | PMax | Asset group performance (impressions, conversions, cost por grupo) |
| 20 | PMax | Ad strength por asset group + recomendaciones de assets |
| 21 | PMax | Canibalización PMax vs Search branded (overlap de search terms) |
| 22 | Smart Bidding | Learning period status y timeline |
| 23 | Smart Bidding | Target vs actual performance (tCPA drift, tROAS drift) |
| 24 | Keywords | Match type analysis (exact vs phrase vs broad — efficiency por tipo) |
| 25 | Keywords | Negative keyword coverage gaps |
| 26 | Ads | Ad copy analysis (headlines/descriptions con mejor CTR) |
| 27 | Conversion | Conversion tracking health (primary vs secondary, lag impact) |
| 28 | Conversion | Attribution model comparison (last click vs DDA) |
| 29 | Auction | Auction insights (IS overlap, outranking share vs competidores) |
| 30 | Estratégico | Budget forecast y oportunidad de scaling (IS headroom) |

## Reglas Mandatorias

- **SIEMPRE** ejecutar `google_ads_analysis.py` — no calcular análisis manualmente
- **SIEMPRE** dividir `cost_micros` / 1,000,000 (Google Ads API devuelve costos en micros)
- **SIEMPRE** identificar `currency_code` antes de formatear valores monetarios
- **SIEMPRE** comparar vs período anterior (MoM mínimo)
- **SIEMPRE** descontar últimos 7 días para métricas de conversión (conversion lag)
- **NUNCA** juzgar PMax sin asset groups + ad strength (ver `../analyzer/references/performance_max.md`)
- **NUNCA** recomendar aumentar budget si IS Lost by Rank > 50% (problema de QS/relevancia, no de budget)
- **Disambiguar** conversions (primary) vs all_conversions (primary + secondary)
- **Weighted averages**: CTR = sum(clicks) / sum(impressions), CPC = sum(cost) / sum(clicks)
- Si un análisis falla por datos faltantes, el JSON lo marca como `"status": "skipped"` con razón
- El HTML debe seguir **exactamente** el branding de `references/html_template.md`
- Insights deben ser accionables: no describir datos, sino qué hacer con ellos

## Semáforo Benchmarks (Search eCommerce AR/LATAM)

| Métrica | Verde | Amarillo | Rojo |
|---------|-------|----------|------|
| CTR | > 3% | 1.5–3% | < 1.5% |
| CPC | < benchmark vertical | ~ benchmark | > 2x benchmark |
| Conv Rate | > 3% | 1–3% | < 1% |
| Impression Share | > 80% | 50–80% | < 50% |
| Quality Score | 7–10 | 5–6 | 1–4 |
| ROAS | > 4x | 2–4x | < 2x |

## Referencias

- `references/analysis_catalog.md` — Metodología detallada de cada análisis
- `references/csv_mapping.md` — Mapeo de columnas CSV de Google Ads + MCP GAQL
- `references/html_template.md` — Template HTML slides
- `../analyzer/references/` — Conceptos teóricos (Quality Score, Smart Bidding, PMax, IS, etc.)
