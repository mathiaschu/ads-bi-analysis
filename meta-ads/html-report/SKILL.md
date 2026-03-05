---
name: meta-ads-html
description: "Genera informes HTML branded para análisis de Meta Ads. Soporta CSV export de Meta Ads Manager + MCP API. Dos modos: Full (32 análisis) y Lite (18). Parseo configurable de nomenclaturas para análisis creativo. Usar cuando el usuario mencione 'informe meta ads', 'análisis meta ads html', 'reporte meta ads', 'slides meta ads', 'meta ads report', 'análisis de campañas html', 'meta ads html'."
---

# Meta Ads HTML Report Skill

## Trigger Keywords

- "informe meta ads", "análisis meta ads html", "reporte meta ads"
- "slides meta ads", "meta ads report", "meta ads html"
- "análisis de campañas html", "reporte de campañas meta"

## Relación con otras Skills

- **`meta-ads-analyzer/`** tiene los 9 docs de referencia conceptual (Breakdown Effect, Learning Phase, etc.)
- **Esta skill CONSUME** esos conceptos para generar el HTML
- Referenciar `../analyzer/references/` cuando se necesite contexto teórico

## Workflow

### Paso 1: Detectar fuente de datos

1. **CSV**: Leer headers, detectar formato Meta Ads Manager (columnas como "Campaign name", "Impressions", "Amount spent (ARS)")
2. **MCP**: Usar `mcp__meta-ads__get_insights` para obtener datos vía API
3. Puede combinar ambos (CSV histórico + MCP reciente)
4. Confirmar al usuario: fuente detectada, cantidad de filas/campañas, rango de fechas

### Paso 2: Detectar nomenclatura

1. Parsear nombres de campañas/ad sets/ads con `references/nomenclatura_parser.md`
2. Auto-detectar formato (Standard vs Alternative vs custom)
3. Si no matchea: preguntar al usuario o usar raw names
4. Extraer: producto, formato, tipo (TOF/MOF/BOF), creador, variación

### Paso 3: Elegir modo

Preguntar al usuario usando AskUserQuestion:
- **Lite** (18 análisis) — overview ejecutivo, los más accionables
- **Full** (32 análisis) — Lite + 14 análisis avanzados (nomenclatura deep-dive, forecasting, attribution)

Default: **Lite**

### Paso 4: Ejecutar análisis

```bash
python3 scripts/meta_ads_analysis.py \
  --input "PATH_AL_CSV_O_JSON" \
  --mode lite|full \
  --nomenclatura standard|alternative|auto \
  --output "/tmp/meta_ads_results.json"
```

El script:
- Auto-detecta formato CSV de Meta Ads Manager
- Parsea nomenclaturas según formato detectado
- Ejecuta los análisis del modo elegido
- Genera JSON con resultados estructurados
- Sale con código 0 si ok, 1 si error

### Paso 5: Generar HTML

1. Leer el JSON de resultados
2. Usar `references/html_template.md` como base del HTML
3. Formato: **slides full-screen** con navegación por teclado (← → + números)
4. Cada slide = 1 análisis (título + visualización + insight + recomendación)
5. Semáforo de benchmarks Argentina/LATAM (verde/amarillo/rojo)
6. Exportar HTML a:

   - Si indica path: usar ese path
   - Si no especifica: preguntar

## Análisis por Modo

### Lite (18 análisis)

| # | Categoría | Análisis |
|---|-----------|----------|
| 1 | Overview | Dashboard ejecutivo (spend, ROAS, CPA, purchases, revenue) |
| 2 | Overview | Semáforo de benchmarks (CTR, CPM, Freq, CPC vs benchmarks AR/LATAM) |
| 3 | Overview | Evolución diaria de métricas clave (spend, ROAS, CPA) |
| 4 | Campañas | Performance por campaña (tabla con métricas + semáforo) |
| 5 | Campañas | Distribución de budget vs resultados (scatter spend vs ROAS) |
| 6 | Campañas | Learning Phase status y recomendaciones |
| 7 | Ad Sets | Performance por ad set con Breakdown Effect warning |
| 8 | Ad Sets | Análisis de audiencias (segmentación por targeting) |
| 9 | Ads | Ranking de ads por eficiencia (ROAS, CPA, CTR) |
| 10 | Ads | Creative fatigue detection (frecuencia + CTR decay) |
| 11 | Funnel | Funnel completo (impressions → clicks → landing views → purchases) |
| 12 | Funnel | Drop-off analysis por etapa |
| 13 | Temporal | Estacionalidad (día de semana + hora del día) |
| 14 | Temporal | Tendencia de CPA/ROAS últimos 30/60/90 días |
| 15 | Geo | Performance por región/país |
| 16 | Placement | Performance por placement (Feed, Stories, Reels, etc.) con Breakdown Effect |
| 17 | Device | Performance por dispositivo (Mobile vs Desktop) |
| 18 | Estratégico | Top 5 recomendaciones priorizadas |

### Full (32) = Lite + 14 adicionales

| # | Categoría | Análisis |
|---|-----------|----------|
| 19 | Nomenclatura | Parseo de naming → tabla de componentes extraídos |
| 20 | Nomenclatura | Performance por tipo de contenido (UGC, Estático, Video, Carrusel) |
| 21 | Nomenclatura | Performance por etapa de funnel (TOF/MOF/BOF) |
| 22 | Nomenclatura | Performance por creador/productor |
| 23 | Nomenclatura | Performance por producto/colección |
| 24 | Nomenclatura | Matrix formato × etapa (heatmap de ROAS) |
| 25 | Creativo | Ad Relevance Diagnostics (Quality, Engagement, Conversion rankings) |
| 26 | Creativo | Hook rate analysis (3-sec video views / impressions) |
| 27 | Creativo | Video completion rates (25%, 50%, 75%, 100%) |
| 28 | Revenue | Attribution window comparison (1d click vs 7d click vs 28d) |
| 29 | Revenue | Forecast de spend/ROAS próximos 30 días |
| 30 | Avanzado | Auction overlap detection entre ad sets |
| 31 | Avanzado | Budget pacing analysis (daily underspend/overspend) |
| 32 | Avanzado | Marginal CPA trend (inferido de time-series) |

## Reglas

- **SIEMPRE** ejecutar `meta_ads_analysis.py` — no calcular análisis manualmente
- **Breakdown Effect**: NUNCA recomendar pausar segmentos solo por CPA promedio alto. Siempre explicar marginal vs average. Ver `../analyzer/references/breakdown_effect.md`
- **Métricas estandarizadas**: usar naming de `../analyzer/SKILL.md` (ej: "Clicks (all)", "CPC (Link Click)", "Reach (Accounts Center accounts)")
- **Semáforo benchmarks** (Argentina/LATAM):
  - CTR: >2% verde, 1-2% amarillo, <1% rojo
  - Frecuencia: <3 verde, 3-5 amarillo, >5 rojo
  - CPM: contextual por vertical
  - ROAS: >3x verde, 1.5-3x amarillo, <1.5x rojo
- **Weighted averages**: CTR y CPM calculados con pesos por impressions, no promedios simples
- **Learning Phase**: marcar ad sets con <50 eventos de optimización
- Si un análisis falla por datos faltantes, el JSON lo marca como `"status": "skipped"` con razón
- El HTML debe seguir **exactamente** el branding de `references/html_template.md`
- Insights deben ser accionables: no describir datos, sino qué hacer con ellos

## Referencias

- `references/analysis_catalog.md` — Metodología detallada de cada análisis
- `references/csv_mapping.md` — Mapeo de columnas CSV de Meta Ads Manager + MCP JSON
- `references/nomenclatura_parser.md` — Reglas de parseo de nomenclaturas
- `references/html_template.md` — Template HTML slides
- `../analyzer/references/` — Conceptos teóricos (Breakdown Effect, Learning Phase, etc.)
