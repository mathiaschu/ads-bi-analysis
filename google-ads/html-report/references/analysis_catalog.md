# Google Ads HTML Skill — Analysis Catalog

Metodología de referencia para los 30 análisis del Google Ads HTML Report.
Cada análisis define: Category, Mode, Required columns, Method, Output JSON.

---

## Output JSON estándar

Todos los análisis producen un objeto con esta estructura base:

```json
{
  "id": 1,
  "title": "...",
  "category": "...",
  "status": "ok" | "skipped",
  "skip_reason": "solo si status=skipped",
  "data": { ... },
  "insight": "...",
  "recommendation": "..."
}
```

- `status: "skipped"` cuando faltan columnas requeridas o no hay datos suficientes
- `insight`: hallazgo principal en 1-2 oraciones
- `recommendation`: acción concreta derivada del insight

---

## Benchmarks Search eCommerce AR/LATAM (referencia global)

| Métrica | Verde (bueno) | Amarillo (ok) | Rojo (alerta) |
|---------|--------------|---------------|---------------|
| CTR | > 3% | 1.5–3% | < 1.5% |
| CPC | < benchmark vertical | ~ benchmark | > 2x benchmark |
| Conv Rate | > 3% | 1–3% | < 1% |
| Impression Share | > 80% | 50–80% | < 50% |
| Quality Score | 7–10 | 5–6 | 1–4 |
| ROAS | > 4x | 2–4x | < 2x |

Los promedios de CTR y CPC se calculan siempre **ponderados por impresiones/clicks**.

---

## Reglas transversales

- **Conversion lag**: los últimos 7 días del período tienen datos de conversión incompletos. Marcar con `"conversion_lag_warning": true`.
- **cost_micros**: cuando los datos vienen de la API (GAQL), SIEMPRE dividir por 1,000,000.
- **Promedio ponderado**: CTR = sum(clicks) / sum(impressions). CPC = sum(cost) / sum(clicks). ROAS = sum(conv_value) / sum(cost).
- **Primary vs Secondary**: `conversions` = primary only. `all_conversions` = primary + secondary. Preferir primary para CPA/ROAS.

---

## LITE — Análisis 1 a 18

---

### 1. Dashboard ejecutivo

**Category:** Overview
**Mode:** LITE

**Required columns:**
- cost, conversions, conversion_value, impressions, clicks, date

**Method:**
1. Sumar cost total del período
2. Sumar conversions (primary)
3. Sumar conversion_value (revenue)
4. Calcular ROAS = conversion_value / cost
5. Calcular CPA = cost / conversions
6. Calcular CTR = clicks / impressions (ponderado)
7. Período = min(date) → max(date)
8. Comparar vs período anterior de igual duración (MoM)

**Output JSON:**
```json
{
  "id": 1,
  "title": "Dashboard ejecutivo",
  "category": "Overview",
  "status": "ok",
  "data": {
    "period": "2024-01-01 → 2024-01-31",
    "cost": 12500.00,
    "conversions": 320,
    "conversion_value": 45000.00,
    "roas": 3.6,
    "cpa": 39.06,
    "impressions": 850000,
    "clicks": 18500,
    "ctr": 2.18,
    "avg_cpc": 0.68,
    "conversion_lag_days": 7,
    "mom_change": {
      "cost": 12.5,
      "conversions": 8.3,
      "roas": -2.1,
      "cpa": 4.1
    }
  }
}
```

---

### 2. Semáforo de benchmarks

**Category:** Overview
**Mode:** LITE

**Required columns:**
- impressions, clicks, cost, conversions, conversion_value

**Method:**
1. Calcular métricas globales ponderadas: CTR, CPC, Conv Rate, ROAS
2. Calcular Impression Share si disponible
3. Asignar semáforo (verde/amarillo/rojo) según tabla benchmarks
4. Calcular QS promedio si hay datos de keyword

**Output JSON:**
```json
{
  "id": 2,
  "title": "Semáforo de benchmarks",
  "category": "Overview",
  "status": "ok",
  "data": {
    "metrics": [
      { "name": "CTR", "value": 2.18, "unit": "%", "status": "yellow", "benchmark": ">3% verde, <1.5% rojo" },
      { "name": "CPC", "value": 0.68, "unit": "USD", "status": "green", "benchmark": "contextual" },
      { "name": "Conv Rate", "value": 1.73, "unit": "%", "status": "yellow", "benchmark": ">3% verde, <1% rojo" },
      { "name": "ROAS", "value": 3.6, "unit": "x", "status": "yellow", "benchmark": ">4x verde, <2x rojo" },
      { "name": "Impression Share", "value": 62.0, "unit": "%", "status": "yellow", "benchmark": ">80% verde, <50% rojo" },
      { "name": "Quality Score", "value": 6.2, "unit": "/10", "status": "yellow", "benchmark": "7+ verde, <5 rojo" }
    ]
  }
}
```

---

### 3. Evolución diaria de métricas clave

**Category:** Overview
**Mode:** LITE

**Required columns:**
- date, cost, conversions, conversion_value, impressions, clicks

**Method:**
1. Agrupar por `date`
2. Por cada día: cost, conversions, CPA, ROAS, CTR
3. Media móvil de 7 días para CPA y ROAS
4. Marcar últimos 7 días con conversion_lag_warning
5. Detectar tendencia (up/flat/down) comparando primera vs segunda mitad

**Output JSON:**
```json
{
  "id": 3,
  "title": "Evolución diaria de métricas clave",
  "category": "Overview",
  "status": "ok",
  "data": {
    "daily": [
      { "date": "2024-01-01", "cost": 400, "conversions": 10, "roas": 3.2, "cpa": 40.0, "ctr": 2.1, "conversion_lag_warning": false }
    ],
    "moving_avg_7d": [
      { "date": "2024-01-07", "roas_ma7": 3.4, "cpa_ma7": 38.5 }
    ],
    "trend": "up"
  }
}
```

---

### 4. Performance por campaña

**Category:** Campañas
**Mode:** LITE

**Required columns:**
- campaign_name, cost, impressions, clicks, conversions, conversion_value

**Method:**
1. Agrupar por campaign_name
2. Por campaña: cost, impressions, clicks, conversions, conversion_value, ROAS, CPA, CTR, CPC
3. Detectar campaign_type (Search/Shopping/PMax/Display/Video)
4. Asignar semáforo ROAS por fila
5. Ordenar por cost descendente

**Output JSON:**
```json
{
  "id": 4,
  "title": "Performance por campaña",
  "category": "Campañas",
  "status": "ok",
  "data": {
    "campaigns": [
      {
        "name": "Search - Brand",
        "type": "Search",
        "cost": 3500,
        "impressions": 120000,
        "clicks": 8500,
        "conversions": 180,
        "conversion_value": 25000,
        "roas": 7.14,
        "cpa": 19.44,
        "ctr": 7.08,
        "cpc": 0.41,
        "roas_status": "green",
        "cost_share_pct": 28.0
      }
    ]
  }
}
```

---

### 5. Distribución de budget vs resultados

**Category:** Campañas
**Mode:** LITE

**Required columns:**
- campaign_name, cost, conversion_value, conversions

**Method:**
1. Agrupar por campaña: cost, conversion_value, ROAS, conversions
2. Calcular % spend y % revenue por campaña
3. Identificar ineficiencias (% revenue << % spend)
4. Datos para scatter: X = cost, Y = ROAS, size = conversions

**Output JSON:**
```json
{
  "id": 5,
  "title": "Distribución de budget vs resultados",
  "category": "Campañas",
  "status": "ok",
  "data": {
    "scatter_points": [
      {
        "campaign": "Search - Brand",
        "cost": 3500,
        "roas": 7.14,
        "conversions": 180,
        "cost_share_pct": 28,
        "revenue_share_pct": 55
      }
    ],
    "efficiency_gaps": [
      { "campaign": "Display - Prospecting", "cost_share_pct": 20, "revenue_share_pct": 5, "verdict": "ineficiente" }
    ]
  }
}
```

---

### 6. Smart Bidding status y evaluación

**Category:** Campañas
**Mode:** LITE

**Required columns:**
- campaign_name, bid_strategy_type

**Optional:** target_cpa, target_roas, cost, conversions, conversion_value

**Method:**
1. Identificar bid strategy por campaña
2. Si tCPA: comparar target_cpa vs actual CPA (cost/conversions)
3. Si tROAS: comparar target_roas vs actual ROAS
4. Calcular drift % = (actual - target) / target * 100
5. Flag campañas con drift > 20% como "underperforming"

**Output JSON:**
```json
{
  "id": 6,
  "title": "Smart Bidding status y evaluación",
  "category": "Campañas",
  "status": "ok",
  "data": {
    "strategies": [
      {
        "campaign": "Search - Brand",
        "strategy": "Target CPA",
        "target": 25.0,
        "actual": 19.44,
        "drift_pct": -22.2,
        "status": "outperforming"
      },
      {
        "campaign": "Search - Generic",
        "strategy": "Target ROAS",
        "target": 3.0,
        "actual": 2.1,
        "drift_pct": -30.0,
        "status": "underperforming"
      }
    ],
    "summary": { "total": 5, "outperforming": 2, "on_target": 1, "underperforming": 2 }
  }
}
```

---

### 7. Quality Score distribution

**Category:** Keywords
**Mode:** LITE

**Required columns:**
- keyword, quality_score

**Optional:** expected_ctr, ad_relevance, landing_page_experience, impressions, cost

**Method:**
1. Histograma de QS (1-10)
2. QS promedio ponderado por impressions
3. Breakdown por componente (Expected CTR, Ad Relevance, Landing Page)
4. Identificar keywords con QS < 5 y alto spend

**Output JSON:**
```json
{
  "id": 7,
  "title": "Quality Score distribution",
  "category": "Keywords",
  "status": "ok",
  "data": {
    "histogram": [
      { "qs": 1, "count": 5 },
      { "qs": 2, "count": 8 },
      { "qs": 7, "count": 45 },
      { "qs": 10, "count": 12 }
    ],
    "avg_qs_weighted": 6.8,
    "components": {
      "expected_ctr": { "above": 40, "average": 35, "below": 25 },
      "ad_relevance": { "above": 55, "average": 30, "below": 15 },
      "landing_page": { "above": 30, "average": 45, "below": 25 }
    },
    "low_qs_high_spend": [
      { "keyword": "zapatos deportivos", "qs": 3, "cost": 1200, "weak_component": "landing_page" }
    ]
  }
}
```

---

### 8. Top keywords por conversión

**Category:** Keywords
**Mode:** LITE

**Required columns:**
- keyword, conversions, cost, clicks, impressions

**Optional:** quality_score, conversion_rate, avg_cpc

**Method:**
1. Filtrar keywords con >= 1 conversión
2. Calcular CPA, Conv Rate, CTR, CPC por keyword
3. Ordenar por conversiones descendente
4. Top 20
5. Asignar semáforo por CPA

**Output JSON:**
```json
{
  "id": 8,
  "title": "Top keywords por conversión",
  "category": "Keywords",
  "status": "ok",
  "data": {
    "keywords": [
      {
        "keyword": "comprar zapatillas online",
        "conversions": 45,
        "cost": 1800,
        "cpa": 40.0,
        "conv_rate": 5.2,
        "ctr": 4.1,
        "cpc": 0.85,
        "quality_score": 8,
        "cpa_status": "green"
      }
    ]
  }
}
```

---

### 9. Impression Share analysis

**Category:** Keywords
**Mode:** LITE

**Required columns:**
- campaign_name, search_impression_share

**Optional:** search_lost_is_budget, search_lost_is_rank, search_top_is, search_abs_top_is

**Method:**
1. IS promedio ponderado por impresiones por campaña
2. IS Lost Budget vs IS Lost Rank
3. Clasificar: si Lost Rank > Lost Budget → problema de QS/relevancia, no de budget
4. Priorizar campañas con IS < 50%
5. Estimar impressions perdidas = impressions * (1 / IS - 1)

**Output JSON:**
```json
{
  "id": 9,
  "title": "Impression Share analysis",
  "category": "Keywords",
  "status": "ok",
  "data": {
    "campaigns": [
      {
        "campaign": "Search - Brand",
        "is": 85.2,
        "lost_budget": 5.1,
        "lost_rank": 9.7,
        "top_is": 72.0,
        "abs_top_is": 48.0,
        "is_status": "green",
        "diagnosis": "Rank loss dominante — mejorar QS o subir bid"
      }
    ],
    "account_avg_is": 62.5
  }
}
```

---

### 10. Wasted spend analysis

**Category:** Search Terms
**Mode:** LITE

**Required columns:**
- search_term, cost, conversions

**Optional:** clicks, impressions

**Method:**
1. Filtrar search terms con conversions = 0
2. Sumar cost acumulado de esos términos
3. Ordenar por cost descendente
4. Calcular % del spend total que es wasted
5. Agrupar por temática si posible

**Output JSON:**
```json
{
  "id": 10,
  "title": "Wasted spend analysis",
  "category": "Search Terms",
  "status": "ok",
  "data": {
    "total_wasted": 4500,
    "wasted_pct": 12.3,
    "top_wasted_terms": [
      { "search_term": "zapatos gratis", "cost": 450, "clicks": 120, "conversions": 0 },
      { "search_term": "zapatillas baratas china", "cost": 320, "clicks": 85, "conversions": 0 }
    ],
    "total_zero_conv_terms": 234
  }
}
```

---

### 11. Oportunidades de keywords

**Category:** Search Terms
**Mode:** LITE

**Required columns:**
- search_term, conversions, search_term_status

**Optional:** cost, clicks, conversion_rate

**Method:**
1. Filtrar search terms con conversions >= 1 y status != "Added"
2. Estos son términos que convierten pero no están como keyword exacta
3. Ordenar por conversions descendente
4. Calcular CPA y Conv Rate de cada uno
5. Top 20 oportunidades

**Output JSON:**
```json
{
  "id": 11,
  "title": "Oportunidades de keywords",
  "category": "Search Terms",
  "status": "ok",
  "data": {
    "opportunities": [
      {
        "search_term": "zapatillas running mujer",
        "conversions": 8,
        "cost": 240,
        "cpa": 30.0,
        "conv_rate": 4.5,
        "status": "None",
        "recommendation": "Agregar como Exact match"
      }
    ],
    "total_opportunities": 45,
    "potential_conversions": 120
  }
}
```

---

### 12. Ranking de ads/RSA por eficiencia

**Category:** Ads
**Mode:** LITE

**Required columns:**
- ad_group_name, clicks, impressions, conversions, cost

**Optional:** headline_1, description_1, ad_strength, ctr, conversion_rate

**Method:**
1. Agrupar por ad (ad_group + headlines)
2. Calcular CTR, Conv Rate, CPA por ad
3. Ordenar por conversions descendente
4. Top 15
5. Incluir ad_strength si disponible

**Output JSON:**
```json
{
  "id": 12,
  "title": "Ranking de ads/RSA por eficiencia",
  "category": "Ads",
  "status": "ok",
  "data": {
    "ads": [
      {
        "ad_group": "Zapatillas Running",
        "headline": "Zapatillas Running - Envío Gratis",
        "impressions": 45000,
        "clicks": 2100,
        "conversions": 85,
        "ctr": 4.67,
        "conv_rate": 4.05,
        "cpa": 28.0,
        "ad_strength": "Good"
      }
    ]
  }
}
```

---

### 13. Ad strength distribution

**Category:** Ads
**Mode:** LITE

**Required columns:**
- ad_strength

**Optional:** impressions, clicks, conversions, cost

**Method:**
1. Contar ads por nivel: Excellent, Good, Average, Poor
2. Calcular % de cada nivel
3. Performance promedio por nivel (CTR, Conv Rate, CPA)
4. Identificar ads "Poor" con alto spend

**Output JSON:**
```json
{
  "id": 13,
  "title": "Ad strength distribution",
  "category": "Ads",
  "status": "ok",
  "data": {
    "distribution": [
      { "strength": "Excellent", "count": 3, "pct": 10, "avg_ctr": 5.2, "avg_cpa": 25.0 },
      { "strength": "Good", "count": 12, "pct": 40, "avg_ctr": 3.8, "avg_cpa": 32.0 },
      { "strength": "Average", "count": 10, "pct": 33, "avg_ctr": 2.5, "avg_cpa": 45.0 },
      { "strength": "Poor", "count": 5, "pct": 17, "avg_ctr": 1.2, "avg_cpa": 68.0 }
    ],
    "poor_high_spend": [
      { "ad_group": "Generic - Shoes", "ad_strength": "Poor", "cost": 2500 }
    ]
  }
}
```

---

### 14. Funnel completo

**Category:** Funnel
**Mode:** LITE

**Required columns:**
- impressions, clicks, conversions

**Optional:** conversion_value, cost

**Method:**
1. Funnel: Impressions → Clicks → Conversions
2. Calcular rates entre etapas: CTR (click/impr), Conv Rate (conv/click)
3. Drop-off por etapa
4. Si hay conversion_value: agregar revenue al final

**Output JSON:**
```json
{
  "id": 14,
  "title": "Funnel completo",
  "category": "Funnel",
  "status": "ok",
  "data": {
    "steps": [
      { "name": "Impressions", "value": 850000, "rate_from_prev": null, "pct_of_top": 100 },
      { "name": "Clicks", "value": 18500, "rate_from_prev": 2.18, "pct_of_top": 2.18 },
      { "name": "Conversions", "value": 320, "rate_from_prev": 1.73, "pct_of_top": 0.038 }
    ],
    "overall_conversion_rate": 0.038,
    "cost_per_step": {
      "cpm": 14.71,
      "cpc": 0.68,
      "cpa": 39.06
    }
  }
}
```

---

### 15. Estacionalidad

**Category:** Temporal
**Mode:** LITE

**Required columns:**
- day_of_week OR date, cost, conversions

**Optional:** hour_of_day, impressions, clicks

**Method:**
1. Agrupar por día de semana: cost, conversions, CPA, CTR
2. Si hay datos horarios: agrupar por hora
3. Heatmap: día × hora con CPA o Conv Rate
4. Identificar mejores y peores momentos

**Output JSON:**
```json
{
  "id": 15,
  "title": "Estacionalidad",
  "category": "Temporal",
  "status": "ok",
  "data": {
    "by_day": [
      { "day": "Monday", "cost": 1800, "conversions": 48, "cpa": 37.5, "ctr": 2.3 },
      { "day": "Sunday", "cost": 1200, "conversions": 22, "cpa": 54.5, "ctr": 1.8 }
    ],
    "by_hour": [
      { "hour": 9, "cost": 520, "conversions": 18, "cpa": 28.9 },
      { "hour": 22, "cost": 380, "conversions": 5, "cpa": 76.0 }
    ],
    "best_day": "Monday",
    "worst_day": "Sunday",
    "best_hours": [9, 10, 14],
    "worst_hours": [2, 3, 22]
  }
}
```

---

### 16. Performance por ubicación geográfica

**Category:** Geo
**Mode:** LITE

**Required columns:**
- country OR region OR city, cost, conversions

**Optional:** impressions, clicks, conversion_value

**Method:**
1. Agrupar por ubicación más específica disponible
2. Calcular CPA, ROAS, CTR, Conv Rate por ubicación
3. Ordenar por conversiones descendente
4. Top 15 ubicaciones
5. Asignar semáforo por CPA

**Output JSON:**
```json
{
  "id": 16,
  "title": "Performance por ubicación geográfica",
  "category": "Geo",
  "status": "ok",
  "data": {
    "locations": [
      {
        "location": "Buenos Aires",
        "cost": 5000,
        "conversions": 150,
        "cpa": 33.3,
        "roas": 4.2,
        "ctr": 2.8,
        "cost_share_pct": 40,
        "cpa_status": "green"
      }
    ],
    "geo_level": "region"
  }
}
```

---

### 17. Performance por dispositivo

**Category:** Device
**Mode:** LITE

**Required columns:**
- device, cost, conversions, impressions, clicks

**Optional:** conversion_value, conversion_rate

**Method:**
1. Agrupar por device (Mobile, Desktop, Tablet)
2. Calcular CTR, CPC, Conv Rate, CPA, ROAS por device
3. Calcular % share de cost y conversions
4. Identificar gaps de eficiencia entre devices

**Output JSON:**
```json
{
  "id": 17,
  "title": "Performance por dispositivo",
  "category": "Device",
  "status": "ok",
  "data": {
    "devices": [
      {
        "device": "Mobile",
        "cost": 7500,
        "impressions": 550000,
        "clicks": 12000,
        "conversions": 180,
        "ctr": 2.18,
        "cpc": 0.63,
        "conv_rate": 1.5,
        "cpa": 41.67,
        "roas": 3.2,
        "cost_share_pct": 60,
        "conv_share_pct": 56
      }
    ]
  }
}
```

---

### 18. Top 5 recomendaciones priorizadas

**Category:** Estratégico
**Mode:** LITE

**Required columns:**
- Resultados de análisis 1-17

**Method:**
1. Analizar resultados de todos los análisis previos
2. Identificar top 5 oportunidades de mejora
3. Priorizar por impacto estimado × facilidad de implementación
4. Categorizar: Quick Win, Medium Effort, Strategic
5. Incluir métrica específica que mejoraría

**Output JSON:**
```json
{
  "id": 18,
  "title": "Top 5 recomendaciones priorizadas",
  "category": "Estratégico",
  "status": "ok",
  "data": {
    "recommendations": [
      {
        "priority": 1,
        "title": "Agregar 45 negative keywords del wasted spend analysis",
        "impact": "high",
        "effort": "low",
        "category": "Quick Win",
        "estimated_savings": 4500,
        "metric_impacted": "CPA -12%"
      },
      {
        "priority": 2,
        "title": "Mejorar landing page de keywords con QS < 5",
        "impact": "high",
        "effort": "medium",
        "category": "Medium Effort",
        "estimated_savings": null,
        "metric_impacted": "QS +2pts, CPC -15%"
      }
    ]
  }
}
```

---

## FULL — Análisis 19 a 30 (adicionales)

---

### 19. Asset group performance (PMax)

**Category:** PMax
**Mode:** FULL

**Required columns:**
- asset_group_name, impressions, clicks, conversions, cost

**Optional:** conversion_value, ad_strength

**Method:**
1. Filtrar solo campañas PMax
2. Agrupar por asset_group_name
3. Calcular CTR, CPA, ROAS por asset group
4. Ordenar por conversiones descendente
5. Si no hay datos PMax: skip

**Output JSON:**
```json
{
  "id": 19,
  "title": "Asset group performance (PMax)",
  "category": "PMax",
  "status": "ok",
  "data": {
    "asset_groups": [
      {
        "name": "Zapatillas Running",
        "impressions": 120000,
        "clicks": 3500,
        "conversions": 85,
        "cost": 2800,
        "ctr": 2.92,
        "cpa": 32.94,
        "roas": 4.1,
        "ad_strength": "Good"
      }
    ]
  }
}
```

---

### 20. Ad strength por asset group (PMax)

**Category:** PMax
**Mode:** FULL

**Required columns:**
- asset_group_name, ad_strength

**Method:**
1. Listar ad_strength por asset group
2. Recomendar mejoras para grupos con strength < "Good"
3. Referenciar `google-ads-analyzer/references/performance_max.md` para requisitos de assets

**Output JSON:**
```json
{
  "id": 20,
  "title": "Ad strength por asset group",
  "category": "PMax",
  "status": "ok",
  "data": {
    "asset_groups": [
      {
        "name": "Zapatillas Running",
        "ad_strength": "Good",
        "recommendation": "Agregar 2 headlines más y 1 video para alcanzar Excellent"
      },
      {
        "name": "Accesorios",
        "ad_strength": "Poor",
        "recommendation": "Faltan imágenes landscape y descripciones. Mínimo: 5 headlines, 5 descriptions, 3 images"
      }
    ]
  }
}
```

---

### 21. Canibalización PMax vs Search branded

**Category:** PMax
**Mode:** FULL

**Required columns:**
- campaign_name, campaign_type, search_term, conversions, cost

**Method:**
1. Identificar search terms de campañas PMax que son branded (contienen nombre de marca)
2. Comparar con search terms de campañas Search branded
3. Calcular overlap (mismos términos en ambos)
4. Estimar conversiones "cannibalized" por PMax
5. Si no hay overlap data: skip

**Output JSON:**
```json
{
  "id": 21,
  "title": "Canibalización PMax vs Search branded",
  "category": "PMax",
  "status": "ok",
  "data": {
    "overlap_terms": [
      { "term": "marca zapatillas", "pmax_conversions": 12, "search_conversions": 45, "pmax_cost": 480 }
    ],
    "total_overlap_cost": 2400,
    "cannibalization_risk": "medium",
    "recommendation": "Considerar brand exclusions en PMax"
  }
}
```

---

### 22. Learning period status (Smart Bidding)

**Category:** Smart Bidding
**Mode:** FULL

**Required columns:**
- campaign_name, date, conversions, bid_strategy_type

**Method:**
1. Identificar campañas con Smart Bidding
2. Detectar cambios recientes en bid strategy o target
3. Contar conversiones en últimos 14 días
4. Si < 30 conversiones en 14d: probablemente en learning
5. Estimar días restantes

**Output JSON:**
```json
{
  "id": 22,
  "title": "Learning period status",
  "category": "Smart Bidding",
  "status": "ok",
  "data": {
    "campaigns": [
      {
        "campaign": "Search - Generic",
        "strategy": "Target CPA",
        "conv_last_14d": 18,
        "status": "learning",
        "est_days_remaining": 10,
        "recommendation": "No editar hasta salir de learning (~10 días)"
      }
    ],
    "summary": { "total_smart_bidding": 5, "in_learning": 2, "stable": 3 }
  }
}
```

---

### 23. Target vs actual performance (Smart Bidding drift)

**Category:** Smart Bidding
**Mode:** FULL

**Required columns:**
- campaign_name, bid_strategy_type, target_cpa OR target_roas, cost, conversions, conversion_value, date

**Method:**
1. Por campaña con Smart Bidding: calcular actual CPA/ROAS por semana
2. Comparar con target
3. Calcular drift % semanal
4. Identificar tendencia del drift (mejorando / empeorando)
5. Referenciar `google-ads-analyzer/references/smart_bidding.md`

**Output JSON:**
```json
{
  "id": 23,
  "title": "Target vs actual performance",
  "category": "Smart Bidding",
  "status": "ok",
  "data": {
    "campaigns": [
      {
        "campaign": "Search - Generic",
        "strategy": "Target CPA",
        "target": 35.0,
        "weekly_actuals": [
          { "week": "2024-W01", "actual_cpa": 42.0, "drift_pct": 20.0 },
          { "week": "2024-W02", "actual_cpa": 38.0, "drift_pct": 8.6 }
        ],
        "trend": "improving",
        "current_drift_pct": 8.6
      }
    ]
  }
}
```

---

### 24. Match type analysis

**Category:** Keywords
**Mode:** FULL

**Required columns:**
- keyword, match_type, cost, conversions, impressions, clicks

**Method:**
1. Agrupar por match_type (Exact, Phrase, Broad)
2. Calcular CTR, CPC, Conv Rate, CPA, ROAS por tipo
3. Comparar eficiencia entre tipos
4. Calcular % de spend y % de conversions por tipo

**Output JSON:**
```json
{
  "id": 24,
  "title": "Match type analysis",
  "category": "Keywords",
  "status": "ok",
  "data": {
    "match_types": [
      {
        "type": "Exact",
        "keywords": 45,
        "cost": 4200,
        "conversions": 120,
        "cpa": 35.0,
        "ctr": 5.2,
        "conv_rate": 4.8,
        "cost_share_pct": 34,
        "conv_share_pct": 45
      },
      {
        "type": "Broad",
        "keywords": 12,
        "cost": 5500,
        "conversions": 95,
        "cpa": 57.9,
        "ctr": 1.8,
        "conv_rate": 1.2,
        "cost_share_pct": 44,
        "conv_share_pct": 36
      }
    ]
  }
}
```

---

### 25. Negative keyword coverage gaps

**Category:** Keywords
**Mode:** FULL

**Required columns:**
- search_term, conversions, cost, search_term_status

**Method:**
1. Identificar search terms irrelevantes (0 conversions, alto spend)
2. Agrupar por temática/patrón
3. Verificar si ya están como negatives (search_term_status = "Excluded")
4. Generar lista de negative keywords sugeridas
5. Estimar ahorro mensual

**Output JSON:**
```json
{
  "id": 25,
  "title": "Negative keyword coverage gaps",
  "category": "Keywords",
  "status": "ok",
  "data": {
    "suggested_negatives": [
      { "term": "gratis", "occurrences": 15, "total_cost": 890, "pattern": "freebie seekers" },
      { "term": "tutorial", "occurrences": 8, "total_cost": 340, "pattern": "informational intent" }
    ],
    "total_potential_savings": 2800,
    "already_excluded": 23,
    "new_suggestions": 18
  }
}
```

---

### 26. Ad copy analysis

**Category:** Ads
**Mode:** FULL

**Required columns:**
- headline_1 OR rsa_headlines, impressions, clicks, conversions

**Optional:** description_1, rsa_descriptions, cost

**Method:**
1. Extraer headlines y descriptions únicos
2. Calcular CTR y Conv Rate por headline
3. Identificar patrones en headlines exitosos (CTA, precio, urgencia, beneficio)
4. Top 10 headlines por CTR y top 10 por Conv Rate

**Output JSON:**
```json
{
  "id": 26,
  "title": "Ad copy analysis",
  "category": "Ads",
  "status": "ok",
  "data": {
    "top_headlines_ctr": [
      { "headline": "Envío Gratis Hoy", "ctr": 6.2, "impressions": 45000 }
    ],
    "top_headlines_conv": [
      { "headline": "50% OFF - Solo Hoy", "conv_rate": 5.8, "conversions": 42 }
    ],
    "patterns": [
      { "pattern": "Urgencia (Hoy, Ahora, Último)", "avg_ctr": 4.5, "count": 8 },
      { "pattern": "Precio/Descuento", "avg_ctr": 3.8, "count": 12 },
      { "pattern": "Envío Gratis", "avg_ctr": 5.1, "count": 5 }
    ]
  }
}
```

---

### 27. Conversion tracking health

**Category:** Conversion
**Mode:** FULL

**Required columns:**
- conversions, all_conversions, date

**Optional:** conversion_value, all_conversion_value, view_through_conversions

**Method:**
1. Comparar conversions vs all_conversions (ratio primary/total)
2. Detectar conversion lag: comparar últimos 7 días vs promedio del período
3. Si últimos 7 días tienen < 60% del daily average: flag conversion lag
4. View-through conversions como % del total
5. Evaluar health general

**Output JSON:**
```json
{
  "id": 27,
  "title": "Conversion tracking health",
  "category": "Conversion",
  "status": "ok",
  "data": {
    "primary_conversions": 320,
    "all_conversions": 485,
    "primary_pct": 66.0,
    "secondary_only": 165,
    "view_through": 42,
    "view_through_pct": 8.7,
    "conversion_lag": {
      "last_7d_daily_avg": 6.2,
      "period_daily_avg": 10.3,
      "lag_ratio": 0.60,
      "status": "significant_lag"
    },
    "health": "good"
  }
}
```

---

### 28. Attribution model comparison

**Category:** Conversion
**Mode:** FULL

**Required columns:**
- conversions, date, campaign_name

**Optional:** conversion_value

**Method:**
1. Si hay datos de múltiples modelos: comparar Last Click vs DDA
2. Si solo hay un modelo: estimar impacto basado en campaign types
3. Campaigns tipo "upper funnel" (Display, Video, PMax broad) típicamente pierden atribución en Last Click
4. Campaigns tipo "lower funnel" (Brand Search, Retargeting) ganan en Last Click

**Output JSON:**
```json
{
  "id": 28,
  "title": "Attribution model comparison",
  "category": "Conversion",
  "status": "ok",
  "data": {
    "model_used": "Data-Driven Attribution",
    "campaign_attribution_bias": [
      { "campaign": "Search - Brand", "type": "Lower funnel", "likely_bias": "Overcounted in Last Click" },
      { "campaign": "PMax - Prospecting", "type": "Upper funnel", "likely_bias": "Undercounted in Last Click" }
    ],
    "recommendation": "Usar DDA como modelo principal. No comparar CPA de brand search vs prospecting directamente."
  }
}
```

---

### 29. Auction insights

**Category:** Auction
**Mode:** FULL

**Required columns:**
- competitor_domain, auction_is, auction_overlap

**Optional:** auction_outranking, auction_pos_above, auction_top_rate, auction_abs_top_rate

**Method:**
1. Listar top 10 competidores por overlap rate
2. Calcular IS vs competidores
3. Outranking share (qué % de veces aparecemos arriba)
4. Identificar competidores más agresivos (alto overlap + bajo outranking = nos ganan)
5. Tendencia si hay datos temporales

**Output JSON:**
```json
{
  "id": 29,
  "title": "Auction insights",
  "category": "Auction",
  "status": "ok",
  "data": {
    "competitors": [
      {
        "domain": "competidor1.com",
        "impression_share": 45.0,
        "overlap_rate": 78.0,
        "outranking_share": 55.0,
        "top_rate": 62.0,
        "abs_top_rate": 38.0,
        "threat_level": "high"
      }
    ],
    "our_is": 62.5,
    "top_threat": "competidor1.com"
  }
}
```

---

### 30. Budget forecast y oportunidad de scaling

**Category:** Estratégico
**Mode:** FULL

**Required columns:**
- cost, conversions, conversion_value, search_impression_share, search_lost_is_budget, date

**Method:**
1. Calcular IS Lost by Budget: % de impressions perdidas por budget
2. Estimar conversiones adicionales si se captura ese IS
3. Forecast: si aumentamos budget X% → estimamos Y% más conversiones
4. Solo recomendar scaling si IS Lost Rank < 20% (no escalar con QS bajo)
5. Calcular punto de rendimientos decrecientes

**Output JSON:**
```json
{
  "id": 30,
  "title": "Budget forecast y oportunidad de scaling",
  "category": "Estratégico",
  "status": "ok",
  "data": {
    "current_daily_budget": 420,
    "is_lost_budget": 15.2,
    "is_lost_rank": 22.3,
    "scaling_opportunity": {
      "headroom_pct": 15.2,
      "estimated_additional_conversions": 48,
      "estimated_additional_cost": 1900,
      "estimated_marginal_cpa": 39.6,
      "viable": true
    },
    "forecast_scenarios": [
      { "budget_increase_pct": 10, "est_conv_increase_pct": 7, "est_new_cpa": 40.2 },
      { "budget_increase_pct": 25, "est_conv_increase_pct": 15, "est_new_cpa": 42.8 },
      { "budget_increase_pct": 50, "est_conv_increase_pct": 22, "est_new_cpa": 48.1 }
    ],
    "recommendation": "Headroom de 15% por budget. Escalar 10-25% es viable sin degradar CPA significativamente."
  }
}
```
