# Meta Ads HTML Skill — Analysis Catalog

Metodología de referencia para los 32 análisis del Meta Ads Analyzer.
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

## Benchmarks AR/LATAM (referencia global)

| Métrica | Verde (bueno) | Amarillo (ok) | Rojo (alerta) |
|---------|--------------|---------------|---------------|
| CTR | > 2% | 1% – 2% | < 1% |
| Frecuencia | < 3 | 3 – 5 | > 5 |
| ROAS | > 3x | 1.5x – 3x | < 1.5x |
| CPM | < $5 USD | $5 – $10 USD | > $10 USD |
| CPC | < $0.50 USD | $0.50 – $1.50 USD | > $1.50 USD |

Los promedios de CTR y CPM se calculan siempre **ponderados por impresiones**.

---

## Reglas transversales

- **Breakdown Effect**: cuando se segmenta por placement, dispositivo, región u otra dimensión, siempre advertir que los CPA/ROAS por segmento son promedios marginales, no el CPA/ROAS real del negocio. No tomar decisiones de pause basadas solo en esa vista.
- **Learning Phase**: un ad set está en learning phase si tuvo < 50 eventos de optimización en los últimos 7 días. No pausar ni editar hasta salir de learning.
- **Promedio ponderado**: CTR = sum(clicks) / sum(impressions). CPM = sum(spend) / sum(impressions) * 1000.
- **Parseo de naming**: aplica solo a análisis 19-24. Los campos extraídos del nombre son: `producto`, `formato`, `etapa`, `creador`, `variacion`.

---

## LITE — Análisis 1 a 18

---

### 1. Dashboard ejecutivo

**Category:** Overview
**Mode:** LITE

**Required columns:**
- spend, actions (purchase), action_values (purchase), impressions, clicks

**Method:**
1. Sumar spend total del período
2. Sumar purchases (del array `actions` donde `action_type = "purchase"`)
3. Sumar revenue (de `action_values` donde `action_type = "purchase"`)
4. Calcular ROAS = revenue / spend
5. Calcular CPA = spend / purchases
6. Calcular CTR = clicks / impressions (ponderado)
7. Período = min(date_start) → max(date_stop)

**Output JSON:**
```json
{
  "id": 1,
  "title": "Dashboard ejecutivo",
  "category": "Overview",
  "status": "ok",
  "data": {
    "period": "2024-01-01 → 2024-01-31",
    "spend": 12500.00,
    "revenue": 45000.00,
    "roas": 3.6,
    "purchases": 320,
    "cpa": 39.06,
    "impressions": 850000,
    "clicks": 12500,
    "ctr": 1.47
  },
  "insight": "El período cerró con ROAS 3.6x y CPA $39. El spend total fue $12.5K.",
  "recommendation": "ROAS en zona verde. Evaluar escalar presupuesto si hay margen de audiencia."
}
```

---

### 2. Semáforo de benchmarks

**Category:** Benchmarks
**Mode:** LITE

**Required columns:**
- impressions, clicks, spend, frequency, ctr, cpm, cpc, action_values (purchase), actions (purchase)

**Method:**
1. Calcular métricas globales ponderadas: CTR (clicks/impressions), CPM (spend/impressions*1000), frecuencia promedio ponderada, CPC promedio, ROAS global
2. Asignar semáforo (verde/amarillo/rojo) según tabla de benchmarks AR/LATAM
3. Calcular desviación de cada métrica respecto al benchmark central

**Output JSON:**
```json
{
  "id": 2,
  "title": "Semáforo de benchmarks",
  "category": "Benchmarks",
  "status": "ok",
  "data": {
    "metrics": [
      { "name": "CTR", "value": 1.47, "unit": "%", "status": "yellow", "benchmark_green": ">2%", "benchmark_red": "<1%" },
      { "name": "CPM", "value": 7.20, "unit": "USD", "status": "yellow", "benchmark_green": "<5", "benchmark_red": ">10" },
      { "name": "Frecuencia", "value": 2.8, "unit": "", "status": "green", "benchmark_green": "<3", "benchmark_red": ">5" },
      { "name": "CPC", "value": 0.90, "unit": "USD", "status": "yellow", "benchmark_green": "<0.50", "benchmark_red": ">1.50" },
      { "name": "ROAS", "value": 3.6, "unit": "x", "status": "green", "benchmark_green": ">3x", "benchmark_red": "<1.5x" }
    ]
  },
  "insight": "ROAS y frecuencia en verde. CTR, CPM y CPC en zona amarilla.",
  "recommendation": "Testear creativos con mayor engagement para mejorar CTR y bajar CPM."
}
```

---

### 3. Evolución diaria de métricas clave

**Category:** Tendencias
**Mode:** LITE

**Required columns:**
- date_start, spend, actions (purchase), action_values (purchase), impressions, clicks

**Method:**
1. Agrupar por `date_start`
2. Por cada día: spend, purchases, revenue, ROAS, CPA, CTR (ponderado)
3. Ordenar cronológicamente
4. Calcular media móvil de 7 días para ROAS y CPA (si hay >= 7 días de datos)

**Output JSON:**
```json
{
  "id": 3,
  "title": "Evolución diaria de métricas clave",
  "category": "Tendencias",
  "status": "ok",
  "data": {
    "daily": [
      { "date": "2024-01-01", "spend": 400, "roas": 3.2, "cpa": 42.0, "ctr": 1.3 },
      { "date": "2024-01-02", "spend": 420, "roas": 3.8, "cpa": 38.5, "ctr": 1.6 }
    ],
    "moving_avg_7d": [
      { "date": "2024-01-07", "roas_ma7": 3.4, "cpa_ma7": 40.1 }
    ]
  },
  "insight": "ROAS muestra tendencia ascendente en la segunda quincena del período.",
  "recommendation": "Identificar qué creativos o audiencias se activaron en esa quincena y escalar."
}
```

---

### 4. Performance por campaña

**Category:** Campañas
**Mode:** LITE

**Required columns:**
- campaign_name, spend, impressions, clicks, actions (purchase), action_values (purchase), frequency

**Method:**
1. Agrupar por `campaign_name`
2. Por campaña: spend, impressions, clicks, purchases, revenue, ROAS, CPA, CTR (ponderado), CPM (ponderado), frecuencia promedio
3. Asignar semáforo de ROAS por fila (verde/amarillo/rojo)
4. Ordenar por spend descendente

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
        "name": "Campaña A - TOF",
        "spend": 6000,
        "roas": 4.1,
        "cpa": 35.0,
        "ctr": 1.9,
        "cpm": 6.5,
        "frequency": 2.4,
        "purchases": 171,
        "revenue": 24600,
        "roas_status": "green"
      }
    ]
  },
  "insight": "Campaña A lidera en ROAS (4.1x) con el 48% del spend total.",
  "recommendation": "Evaluar mover budget desde campañas en rojo hacia Campaña A si la audiencia aguanta escala."
}
```

---

### 5. Distribución de budget vs resultados

**Category:** Eficiencia
**Mode:** LITE

**Required columns:**
- campaign_name, spend, action_values (purchase), actions (purchase)

**Method:**
1. Agrupar por campaña: spend total, revenue total, ROAS, purchases
2. Calcular % del spend total que representa cada campaña
3. Calcular % del revenue total que representa cada campaña
4. Identificar campañas donde % revenue >> % spend (eficientes) y viceversa (ineficientes)
5. Datos para scatter: eje X = spend, eje Y = ROAS, tamaño burbuja = purchases

**Output JSON:**
```json
{
  "id": 5,
  "title": "Distribución de budget vs resultados",
  "category": "Eficiencia",
  "status": "ok",
  "data": {
    "scatter_points": [
      {
        "campaign": "Campaña A - TOF",
        "spend": 6000,
        "roas": 4.1,
        "purchases": 171,
        "spend_share_pct": 48,
        "revenue_share_pct": 61
      }
    ],
    "efficiency_gap": [
      { "campaign": "Campaña B - BOF", "spend_share_pct": 30, "revenue_share_pct": 18, "verdict": "ineficiente" }
    ]
  },
  "insight": "Campaña A genera 61% del revenue con solo 48% del spend. Campaña B consume 30% del budget y genera 18% del revenue.",
  "recommendation": "Reasignar budget de Campaña B hacia Campaña A. Revisar audiencias y creativos de Campaña B."
}
```

---

### 6. Learning Phase status

**Category:** Optimización
**Mode:** LITE

**Required columns:**
- adset_name, date_start, spend, actions (purchase o evento de optimización)

**Method:**
1. Agrupar por `adset_name`, filtrar últimos 7 días de datos disponibles
2. Sumar eventos de optimización (purchases u objetivo configurado) por ad set en esos 7 días
3. Marcar como "learning" si < 50 eventos, "active" si >= 50
4. Calcular cuántos eventos faltan para salir de learning
5. Estimar días restantes en learning = (50 - eventos_actuales) / (eventos_actuales / 7)

**Output JSON:**
```json
{
  "id": 6,
  "title": "Learning Phase status y recomendaciones",
  "category": "Optimización",
  "status": "ok",
  "data": {
    "summary": { "total_adsets": 8, "in_learning": 3, "active": 5 },
    "adsets": [
      {
        "name": "Ad Set Retargeting 7D",
        "events_last_7d": 22,
        "status": "learning",
        "events_needed": 28,
        "est_days_remaining": 8.9
      },
      {
        "name": "Ad Set Prospecting LAL",
        "events_last_7d": 67,
        "status": "active",
        "events_needed": 0,
        "est_days_remaining": 0
      }
    ]
  },
  "insight": "3 de 8 ad sets están en learning phase. No editar ni pausar estos ad sets hasta que salgan.",
  "recommendation": "Consolidar audiencias o aumentar presupuesto en los ad sets en learning para acelerar la salida."
}
```

---

### 7. Performance por ad set con Breakdown Effect warning

**Category:** Ad Sets
**Mode:** LITE

**Required columns:**
- adset_name, spend, impressions, clicks, actions (purchase), action_values (purchase), frequency

**Method:**
1. Agrupar por `adset_name`
2. Por ad set: spend, impressions, clicks, purchases, revenue, ROAS, CPA, CTR (ponderado), frecuencia
3. Ordenar por ROAS descendente
4. Incluir advertencia de Breakdown Effect en el output

**Output JSON:**
```json
{
  "id": 7,
  "title": "Performance por ad set con Breakdown Effect warning",
  "category": "Ad Sets",
  "status": "ok",
  "data": {
    "breakdown_effect_warning": "Los ROAS/CPA por ad set son promedios marginales. No reflejan el incrementalidad real. Usar para diagnóstico, no para pausas automáticas.",
    "adsets": [
      {
        "name": "Ad Set LAL 2% - Compras",
        "spend": 3200,
        "roas": 4.8,
        "cpa": 30.0,
        "ctr": 2.1,
        "frequency": 1.9,
        "purchases": 107,
        "roas_status": "green"
      }
    ]
  },
  "insight": "Ad Set LAL 2% es el más eficiente con ROAS 4.8x y baja frecuencia.",
  "recommendation": "Escalar este ad set. Revisar ad sets con frecuencia > 5 que muestren CPA elevado."
}
```

---

### 8. Análisis de audiencias

**Category:** Audiencias
**Mode:** LITE

**Required columns:**
- adset_name, spend, impressions, actions (purchase), action_values (purchase), reach, frequency

**Method:**
1. Agrupar por `adset_name` (proxy de audiencia)
2. Extraer tipo de audiencia del nombre: LAL, Intereses, Retargeting, Broad, etc. (regex sobre el nombre)
3. Por tipo de audiencia: spend total, reach total, frecuencia promedio ponderada, ROAS, CPA
4. Calcular saturación de audiencia: frecuencia > 5 = saturada

**Output JSON:**
```json
{
  "id": 8,
  "title": "Análisis de audiencias",
  "category": "Audiencias",
  "status": "ok",
  "data": {
    "by_audience_type": [
      {
        "type": "LAL",
        "spend": 4800,
        "reach": 210000,
        "frequency_avg": 2.1,
        "roas": 4.2,
        "cpa": 34.0,
        "saturation_status": "ok"
      },
      {
        "type": "Retargeting",
        "spend": 3200,
        "reach": 18000,
        "frequency_avg": 6.8,
        "roas": 5.1,
        "cpa": 28.0,
        "saturation_status": "saturada"
      }
    ]
  },
  "insight": "Retargeting tiene ROAS 5.1x pero frecuencia 6.8 (saturada). LAL es eficiente y con margen de escala.",
  "recommendation": "Ampliar audiencia de retargeting (ventana de 14-30 días). Escalar LAL."
}
```

---

### 9. Ranking de ads por eficiencia

**Category:** Creativos
**Mode:** LITE

**Required columns:**
- ad_name, spend, impressions, clicks, actions (purchase), action_values (purchase)

**Method:**
1. Agrupar por `ad_name`
2. Calcular: spend, purchases, revenue, ROAS, CPA, CTR (ponderado), CPM (ponderado)
3. Filtrar ads con spend >= $50 (excluir ads con gasto mínimo)
4. Ordenar por ROAS descendente
5. Marcar top 3 (winners) y bottom 3 (losers)

**Output JSON:**
```json
{
  "id": 9,
  "title": "Ranking de ads por eficiencia",
  "category": "Creativos",
  "status": "ok",
  "data": {
    "min_spend_filter": 50,
    "total_ads_analyzed": 24,
    "winners": [
      {
        "rank": 1,
        "ad_name": "UGC_Maria_TOF_V1",
        "spend": 1800,
        "roas": 6.2,
        "cpa": 24.0,
        "ctr": 3.1,
        "purchases": 75
      }
    ],
    "losers": [
      {
        "rank": 24,
        "ad_name": "Estatico_Producto_BOF_V3",
        "spend": 420,
        "roas": 0.8,
        "cpa": 112.0,
        "ctr": 0.6,
        "purchases": 4
      }
    ]
  },
  "insight": "UGC_Maria_TOF_V1 es el ad más eficiente con ROAS 6.2x. El bottom 3 tiene ROAS < 1x.",
  "recommendation": "Pausar el bottom 3. Crear variaciones del winner top 1."
}
```

---

### 10. Creative fatigue detection

**Category:** Creativos
**Mode:** LITE

**Required columns:**
- ad_name, date_start, impressions, clicks, frequency, spend

**Method:**
1. Agrupar por `ad_name` y `date_start` (serie temporal por ad)
2. Para cada ad: calcular CTR diario, frecuencia acumulada
3. Detectar fatiga: CTR decae >= 30% respecto a los primeros 7 días de actividad, Y frecuencia > 3
4. Calcular "días activo" por ad
5. Clasificar: Fresco (sin fatiga), En riesgo (frecuencia 3-5, CTR decayendo), Fatigado (frecuencia >5, CTR decaído > 30%)

**Output JSON:**
```json
{
  "id": 10,
  "title": "Creative fatigue detection",
  "category": "Creativos",
  "status": "ok",
  "data": {
    "ads": [
      {
        "ad_name": "UGC_Maria_TOF_V1",
        "days_active": 22,
        "frequency_current": 4.2,
        "ctr_first_7d": 3.1,
        "ctr_last_7d": 2.4,
        "ctr_decay_pct": 22.6,
        "fatigue_status": "en_riesgo"
      },
      {
        "ad_name": "Estatico_Banner_TOF_V2",
        "days_active": 45,
        "frequency_current": 7.1,
        "ctr_first_7d": 1.8,
        "ctr_last_7d": 0.7,
        "ctr_decay_pct": 61.1,
        "fatigue_status": "fatigado"
      }
    ],
    "summary": { "fresco": 8, "en_riesgo": 6, "fatigado": 4 }
  },
  "insight": "4 ads están fatigados con CTR decaído > 30% y frecuencia > 5. 6 más están en riesgo.",
  "recommendation": "Pausar los 4 ads fatigados. Renovar creativos para los 6 en riesgo antes de que fatiguen."
}
```

---

### 11. Funnel completo

**Category:** Funnel
**Mode:** LITE

**Required columns:**
- impressions, clicks, link_clicks, actions (purchase)

**Method:**
1. Sumar totales: impressions, clicks (todos), link_clicks, purchases
2. Calcular tasas de conversión entre etapas:
   - Imp → Click: CTR = clicks / impressions
   - Click → Link Click: link_click_rate = link_clicks / clicks
   - Link Click → Purchase: conversion_rate = purchases / link_clicks
3. Calcular "pérdida" absoluta en cada etapa

**Nota:** `link_clicks` puede no estar disponible en todos los exports. Si no existe, usar `clicks` como proxy para "landing views".

**Output JSON:**
```json
{
  "id": 11,
  "title": "Funnel completo",
  "category": "Funnel",
  "status": "ok",
  "data": {
    "funnel_stages": [
      { "stage": "Impresiones", "volume": 850000, "rate_to_next": 1.47, "rate_unit": "%" },
      { "stage": "Clicks (todos)", "volume": 12500, "rate_to_next": 72.0, "rate_unit": "%" },
      { "stage": "Link Clicks", "volume": 9000, "rate_to_next": 3.56, "rate_unit": "%" },
      { "stage": "Compras", "volume": 320, "rate_to_next": null, "rate_unit": null }
    ],
    "overall_conversion_rate": 0.0376
  },
  "insight": "El funnel muestra mayor caída entre clicks y link clicks (28% no llega a la landing).",
  "recommendation": "Revisar coherencia entre el copy del ad y la landing page para reducir abandono post-click."
}
```

---

### 12. Drop-off analysis por etapa

**Category:** Funnel
**Mode:** LITE

**Required columns:**
- impressions, clicks, link_clicks, actions (purchase)

**Method:**
1. Basado en los volúmenes del Análisis 11
2. Calcular usuarios perdidos en cada transición de etapa
3. Calcular % de usuarios perdidos respecto al universo total de impresiones
4. Identificar la etapa con mayor drop-off absoluto y relativo

**Output JSON:**
```json
{
  "id": 12,
  "title": "Drop-off analysis por etapa",
  "category": "Funnel",
  "status": "ok",
  "data": {
    "dropoffs": [
      { "transition": "Impresiones → Clicks", "users_lost": 837500, "dropoff_pct": 98.5, "severity": "normal" },
      { "transition": "Clicks → Link Clicks", "users_lost": 3500, "dropoff_pct": 28.0, "severity": "high" },
      { "transition": "Link Clicks → Compras", "users_lost": 8680, "dropoff_pct": 96.4, "severity": "normal" }
    ],
    "biggest_opportunity": "Clicks → Link Clicks"
  },
  "insight": "La transición Clicks → Link Clicks pierde 28% de usuarios, superior al benchmark típico de 10-15%.",
  "recommendation": "Verificar que los CTAs de los ads dirijan correctamente. Revisar velocidad y experiencia de la landing."
}
```

---

### 13. Estacionalidad

**Category:** Tendencias
**Mode:** LITE

**Required columns:**
- date_start, spend, impressions, actions (purchase), action_values (purchase)

**Method:**
1. Agrupar por día de semana (0=Lunes a 6=Domingo): calcular ROAS promedio, CPA promedio, spend total por día de semana
2. Si hay datos con hora (timestamp): agrupar por hora del día (0-23)
3. Normalizar métricas respecto al promedio global para mostrar variación relativa
4. Identificar días/horas de mejor y peor performance

**Nota:** Meta Ads CSV estándar no incluye desglose por hora. Si no hay datos horarios, skipear esa subsección.

**Output JSON:**
```json
{
  "id": 13,
  "title": "Estacionalidad",
  "category": "Tendencias",
  "status": "ok",
  "data": {
    "by_day_of_week": [
      { "day": "Lunes", "day_index": 0, "spend": 1800, "roas": 3.2, "cpa": 42.0, "vs_avg_roas_pct": -11 },
      { "day": "Martes", "day_index": 1, "spend": 1950, "roas": 3.9, "cpa": 35.0, "vs_avg_roas_pct": 8 }
    ],
    "by_hour": null,
    "best_day": "Jueves",
    "worst_day": "Domingo"
  },
  "insight": "Jueves y viernes concentran el mejor ROAS. Los fines de semana el CPA sube 25% sobre el promedio.",
  "recommendation": "Configurar dayparting para aumentar budget Jueves-Viernes y reducir el fin de semana (si la plataforma lo permite con la estructura actual)."
}
```

---

### 14. Tendencia de CPA/ROAS últimos 30/60/90 días

**Category:** Tendencias
**Mode:** LITE

**Required columns:**
- date_start, spend, actions (purchase), action_values (purchase)

**Method:**
1. Calcular ROAS y CPA agregados para las últimas ventanas disponibles: 30d, 60d, 90d (respecto al último día de datos)
2. Si hay < 30 días de datos, usar todo el período disponible
3. Calcular tendencia (slope) de ROAS en el tiempo usando regresión lineal simple sobre los promedios semanales
4. Clasificar tendencia: positiva / estable / negativa (slope > 0.05, -0.05 a 0.05, < -0.05 por semana)

**Output JSON:**
```json
{
  "id": 14,
  "title": "Tendencia de CPA/ROAS últimos 30/60/90 días",
  "category": "Tendencias",
  "status": "ok",
  "data": {
    "windows": [
      { "window": "30d", "roas": 3.8, "cpa": 36.5, "spend": 14200 },
      { "window": "60d", "roas": 3.4, "cpa": 40.1, "spend": 28100 },
      { "window": "90d", "roas": 3.1, "cpa": 44.3, "spend": 41500 }
    ],
    "trend": {
      "direction": "positiva",
      "roas_slope_per_week": 0.11,
      "interpretation": "El ROAS mejora ~0.11x por semana en el último trimestre"
    }
  },
  "insight": "Tendencia positiva: el ROAS mejoró de 3.1x (90d) a 3.8x (30d). El CPA bajó $7.8 en el trimestre.",
  "recommendation": "Mantener la estrategia actual. El sistema está optimizando bien."
}
```

---

### 15. Performance por región/país

**Category:** Segmentación
**Mode:** LITE

**Required columns:**
- country o region, spend, impressions, clicks, actions (purchase), action_values (purchase)

**Method:**
1. Agrupar por `country` o `region` (usar el que esté disponible)
2. Calcular: spend, impressions, clicks, purchases, revenue, ROAS, CPA, CTR (ponderado), CPM (ponderado)
3. Calcular % del spend y % del revenue por región
4. Ordenar por spend descendente
5. Advertir Breakdown Effect

**Output JSON:**
```json
{
  "id": 15,
  "title": "Performance por región/país",
  "category": "Segmentación",
  "status": "ok",
  "data": {
    "breakdown_effect_warning": "Los ROAS por región son marginales. No pausar regiones basándose solo en este análisis.",
    "by_region": [
      {
        "region": "Argentina",
        "spend": 9800,
        "spend_share_pct": 78,
        "revenue": 36200,
        "revenue_share_pct": 80,
        "roas": 3.7,
        "cpa": 37.0,
        "ctr": 1.6,
        "cpm": 6.8
      }
    ]
  },
  "insight": "Argentina concentra 78% del spend y 80% del revenue con ROAS 3.7x.",
  "recommendation": "Si se vende a otros países, evaluar campañas separadas por país para optimización independiente."
}
```

---

### 16. Performance por placement con Breakdown Effect

**Category:** Segmentación
**Mode:** LITE

**Required columns:**
- placement, spend, impressions, clicks, actions (purchase), action_values (purchase)

**Method:**
1. Agrupar por `placement`
2. Calcular: spend, impressions, clicks, purchases, revenue, ROAS, CPA, CTR (ponderado), CPM (ponderado)
3. Placements comunes: Feed, Stories, Reels, Audience Network, Messenger
4. Incluir advertencia de Breakdown Effect prominente
5. Ordenar por ROAS descendente

**Output JSON:**
```json
{
  "id": 16,
  "title": "Performance por placement con Breakdown Effect",
  "category": "Segmentación",
  "status": "ok",
  "data": {
    "breakdown_effect_warning": "CRÍTICO: El Breakdown Effect es especialmente fuerte en placement. Los ROAS por placement son promedios marginales y NO deben usarse para excluir placements automáticamente. Audience Network y Stories siempre van a mostrar CPA más alto por ser canales de apoyo.",
    "by_placement": [
      { "placement": "Facebook Feed", "spend": 5200, "roas": 4.1, "cpa": 33.0, "ctr": 1.9, "cpm": 7.2 },
      { "placement": "Instagram Reels", "spend": 3100, "roas": 2.8, "cpa": 48.0, "ctr": 1.2, "cpm": 5.1 },
      { "placement": "Audience Network", "spend": 800, "roas": 1.2, "cpa": 95.0, "ctr": 0.4, "cpm": 2.1 }
    ]
  },
  "insight": "Feed tiene el mayor ROAS pero también el mayor CPM. Reels tiene CPM más bajo con buen volumen.",
  "recommendation": "No excluir placements por ROAS bajo sin análisis incremental. Testear Advantage+ Placements si no se está usando."
}
```

---

### 17. Performance por dispositivo

**Category:** Segmentación
**Mode:** LITE

**Required columns:**
- device_platform, spend, impressions, clicks, actions (purchase), action_values (purchase)

**Method:**
1. Agrupar por `device_platform` (Mobile, Desktop, tablet, etc.)
2. Calcular: spend, impressions, clicks, purchases, revenue, ROAS, CPA, CTR (ponderado), CPM (ponderado)
3. Calcular % del spend por dispositivo
4. Advertir Breakdown Effect

**Output JSON:**
```json
{
  "id": 17,
  "title": "Performance por dispositivo (Mobile vs Desktop)",
  "category": "Segmentación",
  "status": "ok",
  "data": {
    "breakdown_effect_warning": "Los ROAS por dispositivo son marginales. Considerar que mobile puede iniciar el journey y desktop convertir.",
    "by_device": [
      { "device": "Mobile", "spend": 10200, "spend_share_pct": 82, "roas": 3.4, "cpa": 40.0, "ctr": 1.5 },
      { "device": "Desktop", "spend": 2300, "spend_share_pct": 18, "roas": 4.2, "cpa": 32.0, "ctr": 2.1 }
    ]
  },
  "insight": "Desktop tiene ROAS 4.2x vs 3.4x de Mobile, pero solo representa 18% del spend.",
  "recommendation": "Si la tienda tiene buena experiencia desktop, testear bid adjustment o campaña separada para desktop. Verificar velocidad mobile de la tienda."
}
```

---

### 18. Top 5 recomendaciones priorizadas

**Category:** Síntesis
**Mode:** LITE

**Required columns:**
- (Síntesis de todos los análisis anteriores, no requiere columnas directas)

**Method:**
1. Compilar todos los hallazgos de los análisis 1-17
2. Rankear por impacto potencial (alto/medio/bajo) y urgencia (inmediato/esta semana/este mes)
3. Priorizar: primero las que combinan alto impacto + urgencia inmediata
4. Limitar a exactamente 5 recomendaciones
5. Cada recomendación incluye: título, descripción, impacto estimado, urgencia, referencia al análisis de origen

**Output JSON:**
```json
{
  "id": 18,
  "title": "Top 5 recomendaciones priorizadas",
  "category": "Síntesis",
  "status": "ok",
  "data": {
    "recommendations": [
      {
        "rank": 1,
        "title": "Pausar 4 ads fatigados",
        "description": "Los ads con frecuencia >5 y CTR decaído >30% están desperdiciando budget. Pausarlos libera presupuesto para creativos frescos.",
        "impact": "alto",
        "urgency": "inmediato",
        "estimated_cpa_improvement": "15-25%",
        "source_analysis": 10
      },
      {
        "rank": 2,
        "title": "Escalar Ad Set LAL 2% Compras",
        "description": "ROAS 4.8x con frecuencia 1.9 indica margen de audiencia. Aumentar budget 20-30%.",
        "impact": "alto",
        "urgency": "esta_semana",
        "estimated_roas_impact": "+0.3-0.5x si la curva se mantiene",
        "source_analysis": 7
      }
    ]
  },
  "insight": "Las mayores oportunidades están en pausar creativos fatigados y escalar la audiencia LAL más eficiente.",
  "recommendation": "Ejecutar las recomendaciones 1 y 2 esta semana. Las restantes pueden planificarse para la próxima revisión."
}
```

---

## FULL — Análisis 19 a 32

---

### 19. Parseo de naming

**Category:** Naming
**Mode:** FULL

**Required columns:**
- ad_name, adset_name, campaign_name

**Method:**
1. Definir convención de naming esperada (configurable, default: `PRODUCTO_FORMATO_ETAPA_CREADOR_VARIACION`)
2. Aplicar regex/split sobre `ad_name` para extraer campos
3. Clasificar cada ad como "parseado correctamente" o "sin formato estándar"
4. Generar tabla con campos extraídos por ad
5. Reportar % de ads sin naming estándar

**Campos extraídos:**
- `producto`: producto o colección del ad (ej: Camiseta, Bundle, General)
- `formato`: UGC | Estatico | Video | Carrusel
- `etapa`: TOF | MOF | BOF
- `creador`: identificador del creador/productor (ej: Maria, Juan, Agencia)
- `variacion`: versión del creativo (ej: V1, V2, A, B)

**Output JSON:**
```json
{
  "id": 19,
  "title": "Parseo de naming → tabla de componentes extraídos",
  "category": "Naming",
  "status": "ok",
  "data": {
    "naming_convention": "PRODUCTO_FORMATO_ETAPA_CREADOR_VARIACION",
    "total_ads": 32,
    "parsed_ok": 24,
    "parse_rate_pct": 75,
    "unparsed_ads": ["Ad sin formato 1", "Banner generico"],
    "parsed_ads": [
      {
        "ad_name": "Camiseta_UGC_TOF_Maria_V1",
        "producto": "Camiseta",
        "formato": "UGC",
        "etapa": "TOF",
        "creador": "Maria",
        "variacion": "V1"
      }
    ]
  },
  "insight": "75% de los ads tienen naming estándar. 8 ads no pudieron parsearse.",
  "recommendation": "Implementar naming convention en todos los ads nuevos. Los análisis 20-24 solo cubren el 75% parseado."
}
```

---

### 20. Performance por tipo de contenido

**Category:** Creativos
**Mode:** FULL

**Required columns:**
- ad_name (parseado del análisis 19), spend, impressions, clicks, actions (purchase), action_values (purchase)

**Depende de:** Análisis 19 (parseo de naming, campo `formato`)

**Method:**
1. Usar campo `formato` extraído del naming: UGC, Estatico, Video, Carrusel
2. Agrupar por `formato`
3. Calcular: spend, impressions, purchases, revenue, ROAS, CPA, CTR (ponderado), CPM (ponderado)
4. Calcular % del spend y % del revenue por formato
5. Ordenar por ROAS descendente

**Output JSON:**
```json
{
  "id": 20,
  "title": "Performance por tipo de contenido (UGC, Estático, Video, Carrusel)",
  "category": "Creativos",
  "status": "ok",
  "data": {
    "coverage_note": "Basado en 24/32 ads con naming estándar (75%)",
    "by_format": [
      { "formato": "UGC", "spend": 6200, "spend_share_pct": 52, "roas": 4.8, "cpa": 29.0, "ctr": 2.8, "cpm": 6.1, "purchases": 214 },
      { "formato": "Estatico", "spend": 3100, "spend_share_pct": 26, "roas": 2.9, "cpa": 48.0, "ctr": 1.2, "cpm": 7.8, "purchases": 65 },
      { "formato": "Video", "spend": 2100, "spend_share_pct": 17, "roas": 3.4, "cpa": 38.0, "ctr": 1.9, "cpm": 5.9, "purchases": 55 },
      { "formato": "Carrusel", "spend": 600, "spend_share_pct": 5, "roas": 2.1, "cpa": 62.0, "ctr": 0.9, "cpm": 8.2, "purchases": 10 }
    ]
  },
  "insight": "UGC domina con ROAS 4.8x y el mejor CTR (2.8%). Carrusel tiene el peor desempeño.",
  "recommendation": "Aumentar producción de UGC. Testear si los carruseles funcionan mejor en retargeting (MOF/BOF)."
}
```

---

### 21. Performance por etapa de funnel

**Category:** Funnel
**Mode:** FULL

**Required columns:**
- ad_name (parseado), spend, impressions, clicks, actions (purchase), action_values (purchase)

**Depende de:** Análisis 19 (campo `etapa`)

**Method:**
1. Usar campo `etapa` extraído: TOF, MOF, BOF
2. Agrupar por etapa
3. Calcular: spend, spend_share_pct, revenue, revenue_share_pct, ROAS, CPA, CTR, CPM
4. Verificar balance del funnel: spend TOF debería ser > MOF > BOF en estructuras prospecting-heavy
5. Calcular ratio TOF/BOF spend

**Output JSON:**
```json
{
  "id": 21,
  "title": "Performance por etapa de funnel (TOF/MOF/BOF)",
  "category": "Funnel",
  "status": "ok",
  "data": {
    "by_stage": [
      { "etapa": "TOF", "spend": 7200, "spend_share_pct": 60, "roas": 3.2, "cpa": 45.0, "ctr": 1.4 },
      { "etapa": "MOF", "spend": 2400, "spend_share_pct": 20, "roas": 4.1, "cpa": 35.0, "ctr": 2.1 },
      { "etapa": "BOF", "spend": 2400, "spend_share_pct": 20, "roas": 5.8, "cpa": 24.0, "ctr": 3.2 }
    ],
    "tof_bof_spend_ratio": 3.0,
    "funnel_balance": "ok"
  },
  "insight": "Estructura 60/20/20 TOF/MOF/BOF. BOF tiene ROAS 5.8x pero puede saturarse con audiencias de retargeting chicas.",
  "recommendation": "Si el BOF tiene frecuencia > 5, expandir audiencia de retargeting. Revisar que TOF esté alimentando el funnel con nuevos usuarios."
}
```

---

### 22. Performance por creador/productor

**Category:** Creativos
**Mode:** FULL

**Required columns:**
- ad_name (parseado), spend, impressions, clicks, actions (purchase), action_values (purchase)

**Depende de:** Análisis 19 (campo `creador`)

**Method:**
1. Usar campo `creador` extraído del naming
2. Agrupar por creador
3. Calcular: spend, número de ads activos, purchases, revenue, ROAS promedio, CPA promedio, CTR promedio (ponderado por impresiones)
4. Ordenar por ROAS descendente

**Output JSON:**
```json
{
  "id": 22,
  "title": "Performance por creador/productor",
  "category": "Creativos",
  "status": "ok",
  "data": {
    "by_creator": [
      { "creador": "Maria", "ads_count": 6, "spend": 4200, "roas": 5.1, "cpa": 28.0, "ctr": 2.9, "purchases": 150 },
      { "creador": "Juan", "ads_count": 4, "spend": 2800, "roas": 3.2, "cpa": 44.0, "ctr": 1.6, "purchases": 64 },
      { "creador": "Agencia", "ads_count": 8, "spend": 3100, "roas": 2.4, "cpa": 58.0, "ctr": 1.1, "purchases": 53 }
    ]
  },
  "insight": "Maria genera el ROAS más alto (5.1x) con 6 ads. Los creativos de Agencia tienen el peor desempeño.",
  "recommendation": "Invertir en más producción con Maria. Revisar brief de Agencia o explorar otros productores."
}
```

---

### 23. Performance por producto/colección

**Category:** Productos
**Mode:** FULL

**Required columns:**
- ad_name (parseado), spend, impressions, clicks, actions (purchase), action_values (purchase)

**Depende de:** Análisis 19 (campo `producto`)

**Method:**
1. Usar campo `producto` extraído del naming
2. Agrupar por producto
3. Calcular: spend, purchases, revenue, ROAS, CPA, CTR (ponderado)
4. Calcular % del revenue por producto para identificar contribución al total

**Output JSON:**
```json
{
  "id": 23,
  "title": "Performance por producto/colección",
  "category": "Productos",
  "status": "ok",
  "data": {
    "by_product": [
      { "producto": "Bundle Premium", "spend": 5100, "roas": 4.6, "cpa": 31.0, "purchases": 165, "revenue": 23460, "revenue_share_pct": 52 },
      { "producto": "Camiseta", "spend": 3200, "roas": 3.1, "cpa": 42.0, "purchases": 76, "revenue": 9920, "revenue_share_pct": 22 },
      { "producto": "General", "spend": 3700, "roas": 2.7, "cpa": 51.0, "purchases": 73, "revenue": 9990, "revenue_share_pct": 22 }
    ]
  },
  "insight": "Bundle Premium genera 52% del revenue con el mejor ROAS (4.6x). Ads genéricos tienen el ROAS más bajo.",
  "recommendation": "Aumentar budget en ads de Bundle Premium. Testear ads de producto específico vs genérico con mayor consistencia."
}
```

---

### 24. Matrix formato × etapa

**Category:** Creativos
**Mode:** FULL

**Required columns:**
- ad_name (parseado), spend, actions (purchase), action_values (purchase)

**Depende de:** Análisis 19 (campos `formato` y `etapa`)

**Method:**
1. Crear matriz con formatos en filas (UGC, Estatico, Video, Carrusel) y etapas en columnas (TOF, MOF, BOF)
2. Para cada celda [formato][etapa]: calcular ROAS promedio ponderado por spend
3. Colorear como heatmap: verde >3x, amarillo 1.5-3x, rojo <1.5x, gris = sin datos
4. Identificar la combinación mejor y la peor

**Output JSON:**
```json
{
  "id": 24,
  "title": "Matrix formato × etapa (heatmap de ROAS)",
  "category": "Creativos",
  "status": "ok",
  "data": {
    "matrix": {
      "UGC":     { "TOF": 3.8, "MOF": 4.9, "BOF": 6.2 },
      "Estatico": { "TOF": 2.1, "MOF": 3.1, "BOF": 4.0 },
      "Video":   { "TOF": 3.2, "MOF": 3.8, "BOF": null },
      "Carrusel": { "TOF": null, "MOF": 2.4, "BOF": 3.3 }
    },
    "best_combination": { "formato": "UGC", "etapa": "BOF", "roas": 6.2 },
    "worst_combination": { "formato": "Estatico", "etapa": "TOF", "roas": 2.1 },
    "no_data_cells": ["Video-BOF", "Carrusel-TOF"]
  },
  "insight": "UGC en BOF tiene el mejor ROAS (6.2x). No hay datos de Video en BOF ni Carrusel en TOF.",
  "recommendation": "Testear Video en BOF y Carrusel en TOF para llenar los gaps de la matrix. Priorizar más UGC en todas las etapas."
}
```

---

### 25. Ad Relevance Diagnostics

**Category:** Creativos
**Mode:** FULL

**Required columns:**
- ad_name, quality_ranking, engagement_rate_ranking, conversion_rate_ranking, spend, impressions

**Method:**
1. Agrupar por `ad_name`
2. Mapear rankings: "ABOVE_AVERAGE" = 3, "AVERAGE" = 2, "BELOW_AVERAGE" = 1
3. Calcular score compuesto = (quality + engagement + conversion) / 3
4. Clasificar: Excelente (>2.5), Normal (1.5-2.5), Problemático (<1.5)
5. Filtrar por ads con spend >= $50

**Output JSON:**
```json
{
  "id": 25,
  "title": "Ad Relevance Diagnostics",
  "category": "Creativos",
  "status": "ok",
  "data": {
    "ads": [
      {
        "ad_name": "UGC_Maria_TOF_V1",
        "quality_ranking": "ABOVE_AVERAGE",
        "engagement_rate_ranking": "ABOVE_AVERAGE",
        "conversion_rate_ranking": "AVERAGE",
        "composite_score": 2.67,
        "classification": "excelente",
        "spend": 1800
      },
      {
        "ad_name": "Estatico_Banner_TOF_V2",
        "quality_ranking": "BELOW_AVERAGE",
        "engagement_rate_ranking": "BELOW_AVERAGE",
        "conversion_rate_ranking": "BELOW_AVERAGE",
        "composite_score": 1.0,
        "classification": "problematico",
        "spend": 620
      }
    ],
    "summary": { "excelente": 6, "normal": 12, "problematico": 4 }
  },
  "insight": "4 ads tienen relevance score problemático. Están pagando más por cada impresión al tener peor relevance.",
  "recommendation": "Pausar o refrescar los 4 ads problemáticos. El CPM de ads con bajo relevance score puede ser hasta 2x mayor."
}
```

---

### 26. Hook rate analysis

**Category:** Video
**Mode:** FULL

**Required columns:**
- ad_name, video_p25_watched_actions (o acción equivalente de 3-sec views), impressions, spend

**Nota:** Meta no expone 3-sec views directamente en todos los exports. Si no está disponible, usar `video_p25_watched_actions` como proxy de "llegó al inicio del video". Indicar en el output qué proxy se usó.

**Method:**
1. Filtrar solo ads de video (formato=Video o UGC con video)
2. Hook rate = 3s_video_views / impressions (o p25 / impressions como proxy)
3. Benchmark hook rate: > 30% excelente, 15-30% normal, < 15% bajo
4. Ordenar por hook rate descendente

**Output JSON:**
```json
{
  "id": 26,
  "title": "Hook rate analysis",
  "category": "Video",
  "status": "ok",
  "data": {
    "metric_used": "video_p25_watched_actions (proxy, 3s views no disponibles)",
    "benchmark": { "excellent": ">30%", "normal": "15-30%", "low": "<15%" },
    "ads": [
      { "ad_name": "UGC_Maria_TOF_V1", "impressions": 120000, "hook_views": 48000, "hook_rate_pct": 40.0, "status": "excelente" },
      { "ad_name": "Video_Producto_MOF_V1", "impressions": 85000, "hook_views": 9350, "hook_rate_pct": 11.0, "status": "bajo" }
    ]
  },
  "insight": "UGC_Maria_TOF_V1 tiene hook rate 40%. Video_Producto_MOF_V1 pierde el 89% de la audiencia en los primeros segundos.",
  "recommendation": "Revisar los primeros 3 segundos de los videos con hook rate bajo. El hook debe capturar atención con texto, movimiento o pregunta directa."
}
```

---

### 27. Video completion rates

**Category:** Video
**Mode:** FULL

**Required columns:**
- ad_name, impressions, video_p25_watched_actions, video_p50_watched_actions, video_p75_watched_actions, video_p100_watched_actions, video_thruplay_watched_actions

**Method:**
1. Para cada ad de video: calcular tasa de completion en cada hito (25%, 50%, 75%, 100%) = watched_at_pct / impressions
2. Calcular drop-off entre cada hito
3. Identificar dónde ocurre la mayor caída (hook, middle, end)
4. ThruPlay rate = thruplay / impressions

**Output JSON:**
```json
{
  "id": 27,
  "title": "Video completion rates",
  "category": "Video",
  "status": "ok",
  "data": {
    "ads": [
      {
        "ad_name": "UGC_Maria_TOF_V1",
        "impressions": 120000,
        "p25_rate_pct": 40.0,
        "p50_rate_pct": 28.0,
        "p75_rate_pct": 18.0,
        "p100_rate_pct": 10.0,
        "thruplay_rate_pct": 9.5,
        "biggest_dropoff": "p25→p50",
        "dropoff_magnitude_pct": 30.0
      }
    ]
  },
  "insight": "La mayor caída ocurre entre 25% y 50% del video. El final es visto por el 10% que llegó al inicio.",
  "recommendation": "El CTA debe moverse antes del 50% del video. Testear versiones más cortas (15-20s) del mismo concepto."
}
```

---

### 28. Attribution window comparison

**Category:** Atribución
**Mode:** FULL

**Required columns:**
- cost_per_action_type (con desglose por ventana), actions (desglose por ventana)

**Nota:** Esta información solo está disponible si el export de Meta incluye columnas separadas por ventana de atribución (1d_click, 7d_click, 28d_click, 1d_view). Si no está disponible, skipear con explicación.

**Method:**
1. Verificar si existen columnas de atribución por ventana
2. Comparar purchases y revenue por ventana: 1d_click, 7d_click, 28d_click, 1d_view
3. Calcular ROAS por ventana de atribución
4. Calcular delta entre ventanas (overlap de atribución)

**Output JSON — caso con datos:**
```json
{
  "id": 28,
  "title": "Attribution window comparison",
  "category": "Atribución",
  "status": "ok",
  "data": {
    "windows": [
      { "window": "1d_click", "purchases": 180, "revenue": 16200, "roas": 1.30 },
      { "window": "7d_click", "purchases": 290, "revenue": 26100, "roas": 2.09 },
      { "window": "28d_click", "purchases": 320, "revenue": 28800, "roas": 2.30 },
      { "window": "1d_view", "purchases": 95, "revenue": 8550, "roas": 0.68 }
    ],
    "attribution_inflation_7d_vs_1d": "61%"
  },
  "insight": "Pasar de 1d_click a 7d_click infla las compras atribuidas 61%. El ROAS real depende del modelo de atribución elegido.",
  "recommendation": "Alinear la ventana de atribución del reporte con la configurada en la campaña. Preferir 7d_click para campañas de consideración."
}
```

**Output JSON — caso sin datos:**
```json
{
  "id": 28,
  "title": "Attribution window comparison",
  "category": "Atribución",
  "status": "skipped",
  "skip_reason": "El CSV no incluye columnas de atribución por ventana. Exportar el reporte incluyendo columnas de breakdown por attribution window.",
  "data": null,
  "insight": null,
  "recommendation": "Para activar este análisis, exportar desde Meta Ads Manager con 'Compare attribution windows' habilitado."
}
```

---

### 29. Forecast de spend/ROAS próximos 30 días

**Category:** Forecast
**Mode:** FULL

**Required columns:**
- date_start, spend, actions (purchase), action_values (purchase)

**Method:**
1. Usar datos históricos del período disponible (mínimo 14 días)
2. Calcular tendencia lineal de ROAS semanal (slope) del análisis 14
3. Proyectar spend = spend promedio diario actual (últimos 7 días) × 30
4. Proyectar ROAS = ROAS actual + (slope × 4 semanas)
5. Proyectar revenue = spend proyectado × ROAS proyectado
6. Calcular intervalos de confianza (± 1 std de ROAS histórico)
7. Advertir que es una proyección lineal simple, no un modelo econométrico

**Output JSON:**
```json
{
  "id": 29,
  "title": "Forecast de spend/ROAS próximos 30 días",
  "category": "Forecast",
  "status": "ok",
  "data": {
    "disclaimer": "Proyección lineal basada en tendencia histórica. No contempla estacionalidad, cambios de mercado ni decisiones de optimización.",
    "current_7d_avg_daily_spend": 420,
    "forecast_30d": {
      "spend": 12600,
      "roas_base": 3.8,
      "roas_optimistic": 4.3,
      "roas_pessimistic": 3.3,
      "revenue_base": 47880,
      "revenue_optimistic": 54180,
      "revenue_pessimistic": 41580
    },
    "trend_used": { "roas_slope_per_week": 0.11 }
  },
  "insight": "Si la tendencia positiva continúa, el ROAS podría llegar a 4.3x en 30 días con un revenue proyectado de $54K.",
  "recommendation": "Usar este forecast como referencia, no como objetivo fijo. Revisar semanalmente contra actuals."
}
```

---

### 30. Auction overlap detection

**Category:** Estructura
**Mode:** FULL

**Required columns:**
- adset_name, campaign_name, spend, impressions, reach, frequency

**Method:**
1. Identificar ad sets que targetean audiencias similares (detectar por nombres similares o misma campaña)
2. Calcular CPM de cada ad set (proxy de competitividad en subasta)
3. Si dos ad sets tienen audiencias potencialmente solapadas (mismo targeting inferido del nombre) y ambos tienen frecuencia > 3, alertar overlap
4. Calcular potencial de autocompetencia: número de ad sets con frecuencia > 3 en la misma campaña

**Nota:** La detección real de overlap requiere el Audience Overlap Tool de Meta. Esta versión es inferida por naming y métricas.

**Output JSON:**
```json
{
  "id": 30,
  "title": "Auction overlap detection entre ad sets",
  "category": "Estructura",
  "status": "ok",
  "data": {
    "disclaimer": "Overlap inferido por naming y métricas. Para overlap exacto usar Audience Overlap Tool en Meta Ads Manager.",
    "high_risk_overlaps": [
      {
        "adset_1": "LAL 1% - Compras 30D",
        "adset_2": "LAL 2% - Compras 30D",
        "risk_reason": "Audiencias LAL anidadas (LAL 1% está incluida en LAL 2%). Ambas con frecuencia > 3.",
        "frequency_1": 4.1,
        "frequency_2": 3.8,
        "combined_spend": 4200
      }
    ],
    "medium_risk_overlaps": [],
    "total_adsets_analyzed": 8
  },
  "insight": "LAL 1% y LAL 2% son audiencias anidadas y probablemente compiten en subasta, elevando el CPM de ambas.",
  "recommendation": "Usar exclusión de audiencias: excluir LAL 1% de la campaña de LAL 2%. Evaluar consolidar en Advantage+ Audience."
}
```

---

### 31. Budget pacing analysis

**Category:** Presupuesto
**Mode:** FULL

**Required columns:**
- adset_name o campaign_name, date_start, spend

**Method:**
1. Agrupar por ad set/campaña y día
2. Calcular gasto diario promedio (últimos 7 días) por entidad
3. Comparar con budget diario si está disponible en el nombre (o inferir de máximo histórico)
4. Calcular underspend (gasto < 80% del budget) y overspend (gasto > 100% del budget)
5. Identificar días con pacing irregular (coeficiente de variación > 30%)

**Nota:** Meta no expone el budget diario en los CSVs estándar. Pacing se analiza por variabilidad del gasto diario.

**Output JSON:**
```json
{
  "id": 31,
  "title": "Budget pacing analysis",
  "category": "Presupuesto",
  "status": "ok",
  "data": {
    "disclaimer": "Budget diario no disponible en el CSV. Pacing se evalúa por variabilidad del gasto diario.",
    "adsets": [
      {
        "adset_name": "Ad Set LAL 2% - Compras",
        "avg_daily_spend_7d": 148.5,
        "max_daily_spend": 210.0,
        "min_daily_spend": 88.0,
        "coefficient_of_variation_pct": 28.0,
        "pacing_status": "estable"
      },
      {
        "adset_name": "Ad Set Retargeting 7D",
        "avg_daily_spend_7d": 62.0,
        "max_daily_spend": 180.0,
        "min_daily_spend": 5.0,
        "coefficient_of_variation_pct": 71.0,
        "pacing_status": "irregular"
      }
    ]
  },
  "insight": "Ad Set Retargeting 7D muestra pacing muy irregular (CV 71%), probablemente por audiencia pequeña o limitación de entrega.",
  "recommendation": "Verificar tamaño de audiencia de Retargeting 7D. Si es < 5000 personas, expandir ventana o agregar más audiencias."
}
```

---

### 32. Marginal CPA trend

**Category:** Optimización
**Mode:** FULL

**Required columns:**
- date_start, spend, actions (purchase)

**Method:**
1. Ordenar datos por fecha
2. Calcular CPA semanal: spend_semana / purchases_semana
3. Calcular la variación de CPA entre semanas consecutivas: delta_cpa = CPA_semana_N - CPA_semana_N-1
4. Inferir marginal CPA trend: si el CPA sube a medida que sube el spend, hay curva de rendimientos decrecientes
5. Calcular correlación entre spend_semanal y CPA_semanal: correlación positiva = rendimientos decrecientes
6. Clasificar: "escalando bien" (correlación < 0.2), "rendimientos decrecientes leves" (0.2-0.5), "saturación" (> 0.5)

**Output JSON:**
```json
{
  "id": 32,
  "title": "Marginal CPA trend (inferido de time-series)",
  "category": "Optimización",
  "status": "ok",
  "data": {
    "disclaimer": "Marginal CPA inferido de series temporales. No es causalidad, puede haber variables confusoras (estacionalidad, mix de campañas).",
    "weekly_data": [
      { "week": "2024-01-01", "spend": 2800, "purchases": 72, "cpa": 38.9 },
      { "week": "2024-01-08", "spend": 3100, "purchases": 74, "cpa": 41.9 },
      { "week": "2024-01-15", "spend": 3400, "purchases": 76, "cpa": 44.7 },
      { "week": "2024-01-22", "spend": 3200, "purchases": 78, "cpa": 41.0 }
    ],
    "spend_cpa_correlation": 0.38,
    "trend_classification": "rendimientos_decrecientes_leves",
    "cpa_delta_per_1k_spend": 4.2
  },
  "insight": "A medida que el spend sube, el CPA tiende a subir levemente (+$4.2 por cada $1K adicional). Correlación 0.38: rendimientos decrecientes leves.",
  "recommendation": "El sistema puede escalar hasta un 20-30% más de spend antes de que los rendimientos decrecientes sean significativos. Monitorear semanalmente el CPA marginal."
}
```

---

## Resumen de análisis

| # | Nombre | Category | Mode | Depende de |
|---|--------|----------|------|------------|
| 1 | Dashboard ejecutivo | Overview | LITE | — |
| 2 | Semáforo de benchmarks | Benchmarks | LITE | — |
| 3 | Evolución diaria | Tendencias | LITE | — |
| 4 | Performance por campaña | Campañas | LITE | — |
| 5 | Budget vs resultados | Eficiencia | LITE | — |
| 6 | Learning Phase status | Optimización | LITE | — |
| 7 | Performance por ad set | Ad Sets | LITE | — |
| 8 | Análisis de audiencias | Audiencias | LITE | — |
| 9 | Ranking de ads | Creativos | LITE | — |
| 10 | Creative fatigue | Creativos | LITE | — |
| 11 | Funnel completo | Funnel | LITE | — |
| 12 | Drop-off analysis | Funnel | LITE | 11 |
| 13 | Estacionalidad | Tendencias | LITE | — |
| 14 | Tendencia CPA/ROAS | Tendencias | LITE | — |
| 15 | Performance por región | Segmentación | LITE | — |
| 16 | Performance por placement | Segmentación | LITE | — |
| 17 | Performance por dispositivo | Segmentación | LITE | — |
| 18 | Top 5 recomendaciones | Síntesis | LITE | 1-17 |
| 19 | Parseo de naming | Naming | FULL | — |
| 20 | Performance por formato | Creativos | FULL | 19 |
| 21 | Performance por etapa | Funnel | FULL | 19 |
| 22 | Performance por creador | Creativos | FULL | 19 |
| 23 | Performance por producto | Productos | FULL | 19 |
| 24 | Matrix formato × etapa | Creativos | FULL | 19 |
| 25 | Ad Relevance Diagnostics | Creativos | FULL | — |
| 26 | Hook rate | Video | FULL | — |
| 27 | Video completion rates | Video | FULL | — |
| 28 | Attribution window | Atribución | FULL | — |
| 29 | Forecast 30 días | Forecast | FULL | 14 |
| 30 | Auction overlap | Estructura | FULL | — |
| 31 | Budget pacing | Presupuesto | FULL | — |
| 32 | Marginal CPA trend | Optimización | FULL | — |
