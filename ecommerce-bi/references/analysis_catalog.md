# eCommerce BI — Catálogo de Análisis

Metodología de referencia para los 38 análisis implementados en `bi_analysis.py`.

---

## Columnas canónicas

| Columna canónica | Descripción |
|---|---|
| `order_id` | ID único de orden |
| `date` | Fecha de la orden (datetime parseable) |
| `email` | Email del cliente |
| `total` | Total de la orden (float, sin signo $) |
| `product_name` | Nombre del producto |
| `product_price` | Precio unitario del producto |
| `product_qty` | Cantidad de unidades |
| `sku` | SKU o código de variante |
| `order_status` | Estado de la orden (texto) |
| `cancellation_date` | Fecha de cancelación (si aplica) |
| `cancellation_reason` | Motivo de cancelación |
| `payment_method` | Medio de pago |
| `discount` | Monto de descuento aplicado |
| `coupon` | Código de cupón usado |
| `state` | Provincia/estado |
| `city` | Ciudad |
| `shipping_cost` | Costo de envío |
| `shipping_method` | Método de envío |
| `shipping_date` | Fecha de despacho |
| `channel` | Canal de venta |

---

## LITE — Análisis 1 a 20

---

### #1 — Market Basket Analysis
**Category:** Producto
**Mode:** Lite
**Required columns:** `order_id`, `product_name`

**Method:**
Agrupar productos por `order_id` para construir "canastas". Usar `itertools.combinations` para generar todos los pares (2-item) y tríos (3-item) por orden. Calcular support = (órdenes con el set / total órdenes), confidence = P(B|A) = support(A∪B) / support(A), lift = confidence / P(B). Filtrar resultados con support > 1% y lift > 1.0. Ordenar por lift descendente.

**Output:**
```json
{
  "pairs": [{"items": ["Prod A", "Prod B"], "support": 0.03, "confidence": 0.45, "lift": 2.1}],
  "trios": [{"items": ["Prod A", "Prod B", "Prod C"], "support": 0.015, "confidence": 0.30, "lift": 3.2}],
  "total_orders_analyzed": 5000
}
```

**Insight template:**
"Los productos X e Y se compran juntos en el Z% de las órdenes, con lift de N (N× más probable que por azar). Oportunidad de bundle o cross-sell."

---

### #2 — Afinidad entre categorías
**Category:** Producto
**Mode:** Lite
**Required columns:** `order_id`, `product_name`

**Method:**
Extraer categoría de `product_name` usando el primer segmento antes del primer guion o espacio (configurable via regex). Si el nombre tiene formato "Categoria - Variante", usar todo lo antes del guion. Aplicar la misma lógica de basket analysis que #1 pero a nivel categoría. Ignorar órdenes donde todas las líneas son de la misma categoría (no hay afinidad inter-categoría).

**Output:**
```json
{
  "category_pairs": [{"categories": ["Remeras", "Pantalones"], "support": 0.08, "confidence": 0.52, "lift": 1.8}],
  "single_category_orders_pct": 0.62
}
```

**Insight template:**
"El Z% de las órdenes combinan categorías X e Y. Afinidad natural para armar colecciones o landing pages combinadas."

---

### #3 — Ranking de productos
**Category:** Producto
**Mode:** Lite
**Required columns:** `product_name`, `product_price`, `product_qty`, `date`

**Method:**
Agrupar por `product_name`. Calcular: revenue total (sum de product_price × product_qty), unidades vendidas (sum product_qty), órdenes únicas, precio promedio de venta. Para la tendencia: comparar revenue de los últimos 3 meses calendario vs los 3 meses anteriores, expresar como % de cambio. Si hay menos de 3 meses de datos usar lo disponible. Ordenar por revenue total desc por defecto, incluir rankings alternativos por unidades y por tendencia.

**Output:**
```json
{
  "products": [
    {
      "product_name": "Remera Básica Negra",
      "revenue": 150000,
      "units": 300,
      "unique_orders": 280,
      "avg_price": 500,
      "revenue_rank": 1,
      "units_rank": 2,
      "trend_pct": 15.3,
      "trend_direction": "up"
    }
  ],
  "period_months": 6
}
```

**Insight template:**
"Top producto por revenue: X con $Y. Mayor crecimiento: Z (+N% vs período anterior). Detectar héroes y estrellas emergentes."

---

### #4 — Productos ancla
**Category:** Producto
**Mode:** Lite
**Required columns:** `order_id`, `product_name`

**Method:**
Filtrar órdenes con 2 o más productos distintos. Para cada producto, contar en cuántas de esas órdenes multi-producto aparece (frecuencia absoluta y relativa). Los productos ancla son los que más aparecen en órdenes combinadas. Para cada producto ancla (top 20), listar sus top-5 co-productos más frecuentes con conteo y % de co-ocurrencia.

**Output:**
```json
{
  "anchors": [
    {
      "product": "Jeans Slim Azul",
      "multi_order_appearances": 450,
      "multi_order_pct": 0.18,
      "top_co_products": [{"product": "Remera Básica", "count": 120, "pct": 0.27}]
    }
  ],
  "multi_product_orders_total": 2500,
  "multi_product_orders_pct": 0.42
}
```

**Insight template:**
"El producto X aparece en el Y% de todas las órdenes con múltiples productos. Es el ancla del catálogo — su visibilidad arrastra otros productos."

---

### #5 — Long tail 80/20
**Category:** Producto
**Mode:** Lite
**Required columns:** `product_name`, `product_price`, `product_qty`

**Method:**
Calcular revenue por producto (product_price × product_qty). Ordenar de mayor a menor. Calcular revenue acumulado y porcentaje acumulado. Identificar el corte en 80% del revenue total. Reportar: cuántos productos = 80% revenue, cuántos = 20% restante, ratio de concentración. Repetir para 70% y 90% como referencias adicionales.

**Output:**
```json
{
  "total_products": 320,
  "top_products_80pct": 28,
  "top_products_80pct_share": 0.0875,
  "bottom_products_20pct": 292,
  "pareto_ratio": "9% de productos = 80% del revenue",
  "cutoffs": {"70pct": {"count": 15}, "80pct": {"count": 28}, "90pct": {"count": 65}},
  "products": [{"product_name": "...", "revenue": 0, "revenue_cumulative_pct": 0}]
}
```

**Insight template:**
"Solo N productos (X% del catálogo) generan el 80% del revenue. Oportunidad: enfocar inversión en el top, revisar continuidad del long tail."

---

### #6 — Productos con alta tasa de cancelación
**Category:** Producto
**Mode:** Lite
**Required columns:** `product_name`, `order_status` o `cancellation_date`

**Method:**
Identificar órdenes canceladas: si existe `cancellation_date` con valor no-nulo, o si `order_status` contiene palabras clave como "cancelad", "cancelled", "cancel", "refund", "devoluci" (case-insensitive). Calcular tasa de cancelación global = órdenes canceladas / total órdenes. Para cada producto, calcular su tasa de cancelación. Flagear productos con tasa > 2× el promedio global. Incluir mínimo 5 órdenes por producto para que sea estadísticamente relevante.

**Output:**
```json
{
  "global_cancellation_rate": 0.04,
  "threshold_used": 0.08,
  "flagged_products": [
    {"product_name": "...", "total_orders": 50, "cancelled_orders": 8, "cancellation_rate": 0.16, "vs_average": 4.0}
  ],
  "total_products_analyzed": 200
}
```

**Insight template:**
"El producto X tiene tasa de cancelación del Y% (N× el promedio). Revisar calidad, descripción, expectativas del cliente o proveedor."

---

### #7 — Segmentación RFM
**Category:** Cliente
**Mode:** Lite
**Required columns:** `email`, `date`, `total`

**Method:**
Calcular por cliente: R = días desde última compra (respecto a fecha máxima del dataset), F = cantidad total de órdenes, M = gasto total. Asignar score 1-5 a cada dimensión usando quintiles (5 = mejor). Para R: quintil más bajo de días = score 5. Para F y M: quintil más alto = score 5. Mapear combinaciones de scores a segmentos según la tabla estándar RFM. Contar clientes y revenue por segmento.

**Segmentos:**
- Champions: R≥4, F≥4, M≥4
- Loyal: R≥3, F≥3, M≥3 (no Champions)
- Potential Loyal: R≥3, F≤2, M≤3
- New Customers: R≥4, F=1, M≤2
- Promising: R3-4, F=1, M≤2
- Need Attention: R2-3, F2-3, M2-3
- About to Sleep: R=2, F2-3, M=2
- At Risk: R≤2, F≥3, M≥3
- Can't Lose: R=1, F≥4, M≥4
- Hibernating: R≤2, F≤2, M≤2
- Lost: R=1, F=1, M≤2

**Output:**
```json
{
  "segments": [
    {"segment": "Champions", "count": 120, "pct": 0.08, "revenue": 450000, "revenue_pct": 0.32}
  ],
  "scores": [{"email": "...", "r": 5, "f": 4, "m": 5, "segment": "Champions"}],
  "snapshot_date": "2025-12-31"
}
```

**Insight template:**
"Champions = X% de clientes pero Y% del revenue. At Risk = Z clientes con alto valor histórico que necesitan reactivación urgente."

---

### #8 — Customer Lifetime Value
**Category:** Cliente
**Mode:** Lite
**Required columns:** `email`, `date`, `total`

**Method:**
Por cliente: calcular total revenue, conteo de órdenes, AOV (total/órdenes), fecha primera y última compra, lifespan en días, frecuencia de compra en órdenes/año (órdenes / (lifespan/365), mínimo 1 año). CLV histórico = total gastado. CLV proyectado = AOV × frecuencia_anual × 3 (ventana de 3 años, ajustable). Dividir clientes en 4 cuartiles por CLV proyectado. Para clientes con 1 sola orden, usar promedio del segmento como proxy de frecuencia futura.

**Output:**
```json
{
  "overall": {"avg_clv_historical": 8500, "avg_clv_projected": 15000, "median_clv_projected": 9000},
  "quartiles": [
    {"quartile": 4, "min_clv": 25000, "count": 250, "avg_clv": 42000, "pct_revenue": 0.55}
  ],
  "customers": [{"email": "...", "total_revenue": 0, "orders": 0, "aov": 0, "frequency_annual": 0, "clv_projected": 0, "quartile": 0}]
}
```

**Insight template:**
"El cuartil top de clientes tiene CLV proyectado de $X, concentrando el Y% del revenue futuro esperado. Prioridad máxima de retención."

---

### #9 — Análisis de cohortes
**Category:** Cliente
**Mode:** Lite
**Required columns:** `email`, `date`

**Method:**
Definir la cohorte de cada cliente como el mes-año de su primera compra (formato YYYY-MM). Para cada cohorte, y para cada mes subsiguiente (mes 0 a mes 12), contar qué % de los clientes originales de esa cohorte realizaron al menos una compra en ese mes. Mes 0 = mes de adquisición, siempre 100%. Generar matriz cohorte × mes. Incluir solo cohortes con al menos 20 clientes para significancia. Calcular retención promedio por mes (promediando todas las cohortes con datos suficientes).

**Output:**
```json
{
  "cohorts": [
    {
      "cohort": "2024-01",
      "initial_customers": 150,
      "retention": {"0": 1.0, "1": 0.32, "2": 0.18, "3": 0.14}
    }
  ],
  "avg_retention_by_month": {"0": 1.0, "1": 0.28, "2": 0.15, "3": 0.12}
}
```

**Insight template:**
"La retención promedio al mes 1 es del X%. Las cohortes de [mes] retienen mejor — identificar qué cambió en adquisición o producto en ese período."

---

### #10 — Tasa de recompra y tiempo entre compras
**Category:** Cliente
**Mode:** Lite
**Required columns:** `email`, `date`

**Method:**
Calcular el total de clientes únicos. Identificar clientes con 2 o más órdenes (recompradores). Tasa de recompra = recompradores / total clientes. Para clientes con 2+ órdenes, calcular los intervalos en días entre cada par de compras consecutivas ordenadas por fecha. Reportar distribución: mediana, p25, p75, p90, máximo. Segmentar por comportamiento: clientes con intervalo mediano < 30 días (compradores frecuentes), 30-90 (ocasionales), 90+ (esporádicos).

**Output:**
```json
{
  "total_customers": 3000,
  "repeat_customers": 1200,
  "repeat_rate": 0.40,
  "interval_stats": {"median": 45, "p25": 22, "p75": 90, "p90": 180, "mean": 62},
  "segments": {"frequent": {"count": 300, "pct": 0.25}, "occasional": {"count": 550, "pct": 0.46}, "sporadic": {"count": 350, "pct": 0.29}},
  "single_purchase_customers": 1800,
  "single_purchase_pct": 0.60
}
```

**Insight template:**
"El X% de los clientes compra más de una vez. La mediana entre compras es de N días — la ventana ideal para disparar campañas de recompra."

---

### #11 — Evolución revenue mensual
**Category:** Revenue
**Mode:** Lite
**Required columns:** `date`, `total`

**Method:**
Truncar `date` a mes (YYYY-MM). Agrupar: sum de `total` (revenue), count de órdenes, revenue/órdenes (AOV mensual). Calcular MoM % change = (mes_actual - mes_anterior) / mes_anterior. Calcular YoY % change donde exista el mismo mes del año anterior. Calcular tendencia lineal (slope) sobre los últimos 6 meses para clasificar: si slope positivo = "growing", negativo = "declining", cerca de 0 (< 2% variación mensual promedio) = "stable".

**Output:**
```json
{
  "monthly": [
    {"month": "2024-01", "revenue": 500000, "orders": 1000, "aov": 500, "mom_pct": 5.2, "yoy_pct": 22.1}
  ],
  "summary": {"total_revenue": 0, "total_orders": 0, "avg_monthly_revenue": 0, "trend": "growing", "best_month": "2024-11", "worst_month": "2024-02"}
}
```

**Insight template:**
"Revenue mensual promedio de $X con tendencia [creciente/decreciente/estable]. Mejor mes: [mes] ($Y). MoM promedio: +Z%."

---

### #12 — Ticket promedio
**Category:** Revenue
**Mode:** Lite
**Required columns:** `date`, `total`, `email`

**Method:**
AOV global = sum(total) / count(órdenes). AOV mensual (igual que #11). Distribución de tickets: crear buckets fijos (0-1000, 1001-2000, 2001-5000, 5001-10000, 10001+, ajustar según moneda del dataset) y contar órdenes y revenue por bucket. AOV por tipo de cliente: primera compra vs recompra (identificar comparando date con la primera compra de cada email).

**Output:**
```json
{
  "aov_global": 1850,
  "aov_new_customers": 1650,
  "aov_returning_customers": 2100,
  "aov_by_month": [{"month": "2024-01", "aov": 1800}],
  "distribution": [{"bucket": "0-1000", "orders": 200, "pct_orders": 0.15, "revenue": 150000, "pct_revenue": 0.05}]
}
```

**Insight template:**
"Ticket promedio: $X. Clientes recurrentes compran $Y más por orden (+Z%). Concentración de órdenes en el bucket de $A-$B."

---

### #13 — Revenue por categoría
**Category:** Revenue
**Mode:** Lite
**Required columns:** `product_name`, `product_price`, `product_qty`, `date`

**Method:**
Extraer categoría de `product_name` con la misma lógica que #2. Calcular por categoría: revenue total (price × qty), unidades, % del revenue total. Para tendencia mensual por categoría: calcular revenue por mes para las top-10 categorías por revenue. Identificar categorías en crecimiento (slope positivo últimos 3 meses) vs declinando.

**Output:**
```json
{
  "categories": [
    {"category": "Remeras", "revenue": 800000, "units": 2000, "pct_revenue": 0.28, "trend": "growing"}
  ],
  "monthly_by_category": [{"month": "2024-01", "category": "Remeras", "revenue": 60000}],
  "total_categories": 12
}
```

**Insight template:**
"Top categoría: X con $Y (Z% del revenue). Categorías en crecimiento: A, B. En declive: C."

---

### #14 — Impacto de descuentos
**Category:** Revenue
**Mode:** Lite
**Required columns:** `discount`, `coupon`, `total`

**Method:**
Separar órdenes con descuento (discount > 0 o coupon no nulo) vs sin descuento. Para órdenes con descuento: calcular descuento promedio, descuento como % del total, AOV con vs sin descuento. Uso de cupones: % de órdenes con cupón, top-10 cupones por frecuencia de uso y por revenue generado. Calcular revenue "cedido" en descuentos (sum de discount). Si no existe columna discount pero sí coupon, marcar como binario (con/sin cupón).

**Output:**
```json
{
  "orders_with_discount": {"count": 800, "pct": 0.16, "avg_discount": 250, "avg_discount_pct": 0.12, "aov": 2100},
  "orders_without_discount": {"count": 4200, "pct": 0.84, "aov": 1800},
  "total_revenue_discounted": 120000,
  "top_coupons": [{"coupon": "PROMO20", "uses": 200, "revenue": 380000, "avg_discount": 400}]
}
```

**Insight template:**
"El X% de órdenes usan descuento. AOV con descuento = $Y vs $Z sin descuento (diferencia de $W). Revenue cedido en descuentos: $D total."

---

### #15 — Heatmap por provincia
**Category:** Geográfico
**Mode:** Lite
**Required columns:** `state`, `total`, `email`

**Method:**
Normalizar nombres de provincias (strip, title case, manejar variantes comunes: "Bs As", "Buenos Aires", "CABA", "Capital Federal", etc. — usar diccionario de mapeo). Agrupar por provincia: órdenes, revenue, AOV, clientes únicos, revenue per capita (revenue / clientes únicos). Calcular % de revenue y % de órdenes sobre el total. Ranking por revenue.

**Output:**
```json
{
  "provinces": [
    {"state": "Buenos Aires", "orders": 2000, "revenue": 3500000, "aov": 1750, "unique_customers": 1500, "revenue_per_customer": 2333, "pct_revenue": 0.42, "pct_orders": 0.38, "rank": 1}
  ],
  "provinces_covered": 22,
  "top_3_concentration": 0.75
}
```

**Insight template:**
"X provincia concentra el Y% del revenue. Las 3 principales = Z% del total. Provincias con AOV alto y bajo volumen = oportunidad de escala."

---

### #16 — Costo de envío vs conversión
**Category:** Geográfico
**Mode:** Lite
**Required columns:** `shipping_cost`, `state`, `total`

**Method:**
Por provincia: calcular costo de envío promedio, mediana, % de órdenes con envío gratis (shipping_cost = 0). Correlación entre costo promedio de envío y volumen de órdenes por provincia (Pearson si suficientes datos, o ranking visual). Calcular shipping_cost como % del total de la orden por provincia. Flagear provincias donde shipping_cost > 15% del ticket promedio.

**Output:**
```json
{
  "by_state": [
    {"state": "Mendoza", "avg_shipping_cost": 1200, "median_shipping_cost": 900, "free_shipping_pct": 0.15, "shipping_pct_of_total": 0.18, "orders": 300, "flagged": true}
  ],
  "overall": {"avg_shipping_cost": 650, "free_shipping_rate": 0.42, "correlation_cost_vs_volume": -0.55}
}
```

**Insight template:**
"Provincias donde el envío supera el 15% del ticket: X, Y, Z. Correlación costo-volumen: N (mayor costo = menor demanda). Oportunidad de subsidiar envío en zonas estratégicas."

---

### #17 — Tasa de cancelación
**Category:** Operativo
**Mode:** Lite
**Required columns:** `order_status` o `cancellation_date`, `cancellation_reason`, `payment_method`, `date`

**Method:**
Identificar cancelaciones igual que #6 (status keywords o cancellation_date no nulo). Tasa global. Tendencia mensual (% de cancelaciones por mes). Top motivos de cancelación (si existe `cancellation_reason`): frecuencia y % por motivo. Tasa de cancelación por método de pago. Tasa de cancelación por mes para detectar períodos problemáticos.

**Output:**
```json
{
  "global_rate": 0.038,
  "monthly_rate": [{"month": "2024-01", "total_orders": 500, "cancelled": 18, "rate": 0.036}],
  "by_reason": [{"reason": "Stock agotado", "count": 45, "pct": 0.32}],
  "by_payment_method": [{"method": "Transferencia", "total": 800, "cancelled": 48, "rate": 0.06}]
}
```

**Insight template:**
"Tasa de cancelación global: X%. Mayor tasa en [método de pago]: Y%. Motivo principal: [razón] (Z% de cancelaciones)."

---

### #18 — Mix de medios de pago
**Category:** Operativo
**Mode:** Lite
**Required columns:** `payment_method`, `total`, `date`

**Method:**
Normalizar nombres de métodos de pago (agrupar variantes: "Tarjeta de crédito", "Credito", "CC" → "Tarjeta Crédito"; "MercadoPago", "MP" → "MercadoPago", etc. — usar diccionario de mapeo configurable). Por método: órdenes, revenue, % del total, AOV. Tendencia mensual: evolución del mix en los últimos 6 meses (detectar si algún método está creciendo/declinando en participación).

**Output:**
```json
{
  "payment_mix": [
    {"method": "MercadoPago", "orders": 2500, "pct_orders": 0.50, "revenue": 4500000, "pct_revenue": 0.48, "aov": 1800}
  ],
  "monthly_mix": [{"month": "2024-01", "method": "MercadoPago", "orders": 200, "pct_orders": 0.52}],
  "methods_count": 5
}
```

**Insight template:**
"X concentra el Y% de las órdenes. AOV más alto: [método] ($Z). [Método] gana participación mes a mes (+N pp en 6 meses)."

---

### #19 — Oportunidades de bundling
**Category:** Estratégico
**Mode:** Lite
**Required columns:** output de análisis #1

**Method:**
Tomar los top-20 pares por lift del análisis #1. Para cada par: obtener precio promedio de cada producto (de los datos originales). Calcular precio del bundle = (precio_A + precio_B) × 0.87 (descuento del 13% como default, configurable entre 10-20%). Demanda estimada = soporte del par × total órdenes históricas / 12 (proyección mensual). Revenue uplift estimado = demanda_mensual × precio_bundle × 12. Ordenar por revenue uplift potencial anual descendente.

**Output:**
```json
{
  "bundle_opportunities": [
    {
      "products": ["Remera Básica Negra", "Jeans Slim Azul"],
      "individual_prices": [1200, 3500],
      "bundle_price_suggested": 4088,
      "discount_pct": 0.13,
      "estimated_monthly_demand": 45,
      "estimated_annual_revenue": 2203560,
      "lift": 3.2,
      "support": 0.03
    }
  ]
}
```

**Insight template:**
"Top bundle oportunidad: [Producto A] + [Producto B] a $X (13% off). Revenue anual potencial: $Y. Basado en lift de N× — la compra conjunta es altamente no aleatoria."

---

### #20 — Estacionalidad
**Category:** Estratégico
**Mode:** Lite
**Required columns:** `date`, `total`

**Method:**
Parsear `date` para extraer: mes del año (1-12), día de la semana (0=lunes, 6=domingo), hora del día (si el campo tiene timestamp). Calcular revenue promedio y órdenes promedio por: mes del año (promediando todos los años disponibles), día de la semana, hora del día (si disponible). Identificar peak months (top 3), low months (bottom 3), mejor día de la semana, mejor hora. Si hay datos de 2+ años, calcular estacionalidad relativa (índice = valor_periodo / promedio_global).

**Output:**
```json
{
  "by_month": [{"month": 11, "month_name": "Noviembre", "avg_revenue": 850000, "avg_orders": 1700, "index": 1.42}],
  "by_weekday": [{"day": 0, "day_name": "Lunes", "avg_revenue": 95000, "avg_orders": 190, "index": 0.95}],
  "by_hour": [{"hour": 21, "avg_orders": 45, "index": 1.8}],
  "peak_months": ["Noviembre", "Diciembre", "Mayo"],
  "low_months": ["Enero", "Febrero", "Julio"],
  "best_weekday": "Jueves",
  "has_hourly_data": true
}
```

**Insight template:**
"Picos en [meses]. El mejor día de la semana es [día] (índice N). Hora pico: [hora]hs. Alinear campañas y presupuesto de media a esta curva."

---

## FULL ONLY — Análisis 21 a 38

---

### #21 — Afinidad entre colores
**Category:** Producto
**Mode:** Full
**Required columns:** `order_id`, `product_name`

**Method:**
Definir lista de colores a detectar (Spanish + common): Negro, Blanca/Blanco, Rojo/Roja, Azul, Verde, Rosa, Gris, Beige, Marrón/Marron, Celeste, Naranja, Violeta/Viola, Bordo, Crudo, Natural, Nude, Arena, Ocre, Mostaza, Turquesa, Lila, Salmon/Salmón, Off White, Tiza. Buscar estas palabras (case-insensitive, word boundary) en product_name de cada línea de orden. Generar pares de colores que aparecen en la misma orden. Calcular frecuencia de co-ocurrencia y % sobre total de órdenes con 2+ colores. Excluir líneas donde no se detecta color.

**Output:**
```json
{
  "color_pairs": [{"colors": ["Negro", "Blanco"], "co_occurrences": 320, "pct_of_multi_color_orders": 0.22}],
  "color_distribution": [{"color": "Negro", "appearances": 1500, "pct": 0.38}],
  "orders_with_detected_colors": 2800,
  "detection_rate": 0.72
}
```

**Insight template:**
"El par [Color A] + [Color B] es el más frecuente en órdenes multi-color (X% de casos). Oportunidad para ediciones limitadas o looks coordinados."

---

### #22 — Afinidad entre talles
**Category:** Producto
**Mode:** Full
**Required columns:** `order_id`, `product_name`, `sku`

**Method:**
Extraer talle de `product_name` o `sku` con regex. Patrones a detectar: letras (S, M, L, XL, XXL, XXXL, XS), numéricos ropa (34-50 pares), numéricos calzado (35-46), strings (Único, Standard, Free Size). Priorizar detección en SKU si disponible. Calcular distribución de talles: frecuencia por talle en ventas. Calcular qué talles se compran juntos en la misma orden (afinidad). Detectar si hay "stockouts implícitos" comparando demanda por talle vs disponibilidad relativa (si hay datos).

**Output:**
```json
{
  "size_distribution": [{"size": "M", "units": 1200, "pct": 0.32}],
  "size_pairs": [{"sizes": ["M", "L"], "co_occurrences": 180, "pct": 0.08}],
  "detection_rate": 0.68,
  "size_type": "alpha"
}
```

**Insight template:**
"Talle más vendido: [talle] (X% del mix). Co-compra más frecuente: [talle A] + [talle B]. Implicaciones para curvas de producción."

---

### #23 — Análisis de SKU/variantes
**Category:** Producto
**Mode:** Full
**Required columns:** `sku`, `product_name`, `product_price`, `product_qty`

**Method:**
Agrupar por SKU. Intentar identificar el producto base (product_name sin variante): tomar los primeros N caracteres del product_name o hasta el primer guion/paréntesis como base. Por SKU: revenue, unidades, precio promedio, órdenes únicas. Para cada producto base, rankear sus variantes por revenue y unidades. Identificar variantes best-sellers (top 20% de unidades) y worst-sellers (bottom 20%). Calcular concentración: % de revenue en la variante top por producto.

**Output:**
```json
{
  "skus": [{"sku": "REM-NEG-M", "product_base": "Remera Básica", "units": 300, "revenue": 180000, "rank_within_base": 1}],
  "products_with_variants": [
    {"product_base": "Remera Básica", "total_skus": 8, "best_sku": "REM-NEG-M", "worst_sku": "REM-VIO-XL", "top_sku_concentration": 0.45}
  ]
}
```

**Insight template:**
"El SKU [X] domina el [Y]% del revenue de su producto base. Variantes de bajo rendimiento: [lista] — candidatas a discontinuar."

---

### #24 — Ciclo de vida del producto
**Category:** Producto
**Mode:** Full
**Required columns:** `product_name`, `product_price`, `product_qty`, `date`

**Method:**
Filtrar productos con datos en 6+ meses distintos. Para cada producto elegible, calcular revenue mensual. Aplicar regresión lineal simple sobre los últimos 3 meses de datos (slope). Clasificar etapa: si el producto tiene < 3 meses de datos = "Introduction"; si slope > 10%/mes promedio = "Growth"; si |slope| < 5%/mes = "Maturity"; si slope < -10%/mes = "Decline". También calcular el mes de peak revenue.

**Output:**
```json
{
  "products": [
    {
      "product_name": "Remera Básica Negra",
      "months_with_data": 10,
      "stage": "Maturity",
      "peak_month": "2024-11",
      "peak_revenue": 95000,
      "last_3m_slope_pct": 2.1,
      "monthly_revenue": [{"month": "2024-01", "revenue": 80000}]
    }
  ],
  "stage_summary": {"Introduction": 5, "Growth": 12, "Maturity": 28, "Decline": 8}
}
```

**Insight template:**
"X productos en declive — evaluar descontinuación o relanzamiento. Y en crecimiento — aumentar stock y visibilidad."

---

### #25 — Patrón de upgrade
**Category:** Cliente
**Mode:** Full
**Required columns:** `email`, `date`, `total`

**Method:**
Para clientes con 3+ órdenes: calcular AOV de la primera mitad de órdenes vs segunda mitad. Un cliente "upgrade" si el AOV de la segunda mitad > primera mitad por más del 10%. Un cliente "downgrade" si cae más del 10%. Calcular % de cada categoría. Para upgraders: calcular el incremento promedio en $ y %. Analizar si el upgrade correlaciona con tiempo como cliente (¿los clientes de mayor antigüedad gastan más?).

**Output:**
```json
{
  "customers_analyzed": 800,
  "upgraders": {"count": 320, "pct": 0.40, "avg_increase_pct": 35.2, "avg_increase_abs": 650},
  "downgraders": {"count": 180, "pct": 0.225, "avg_decrease_pct": -22.1},
  "stable": {"count": 300, "pct": 0.375},
  "correlation_tenure_aov": 0.42
}
```

**Insight template:**
"El X% de clientes recurrentes incrementa su ticket con el tiempo (+Y% promedio). Clientes de mayor antigüedad gastan Z× más. Programas de loyalty y upsell son especialmente efectivos."

---

### #26 — Clientes VIP (top 10%)
**Category:** Cliente
**Mode:** Full
**Required columns:** `email`, `total`, `product_name`, `state`

**Method:**
Calcular revenue total por cliente. Identificar el top 10% por revenue. Para este grupo: calcular perfil agregado (AOV promedio, órdenes promedio, primera y última compra, antigüedad). Top-10 productos más comprados por este grupo (en órdenes y revenue). Top-5 categorías. Distribución geográfica (top provincias). Comparar AOV y frecuencia del VIP vs el resto.

**Output:**
```json
{
  "vip_threshold": 15000,
  "vip_count": 300,
  "vip_pct": 0.10,
  "vip_revenue_share": 0.52,
  "vip_profile": {"avg_revenue": 45000, "avg_orders": 8.2, "avg_aov": 5487, "avg_tenure_days": 420},
  "non_vip_profile": {"avg_revenue": 3200, "avg_orders": 2.1, "avg_aov": 1524},
  "top_products": [{"product_name": "...", "orders": 0, "revenue": 0}],
  "top_states": [{"state": "Buenos Aires", "count": 120, "pct": 0.40}]
}
```

**Insight template:**
"El top 10% de clientes genera el X% del revenue, con AOV Y× mayor que el resto. Se concentran en [productos] y [provincias]. Justifican atención y beneficios especiales."

---

### #27 — Análisis de churn
**Category:** Cliente
**Mode:** Full
**Required columns:** `email`, `date`, `product_name`

**Method:**
Calcular el intervalo promedio de compra por cliente (para clientes con 2+ órdenes). Para clientes con 1 sola orden, usar la mediana global. Definir churn: un cliente se considera "churned" si han pasado más de 2× su intervalo promedio de compra desde su última orden (o 2× la mediana global para compradores únicos). Churn rate = churned / total clientes. Identificar la cohorte de adquisición de los churned. Último producto comprado por clientes churned (top-10) para identificar si hay productos que anteceden al churn.

**Output:**
```json
{
  "churn_definition_days_multiplier": 2.0,
  "median_purchase_interval_days": 45,
  "churned_customers": 1200,
  "total_customers": 3000,
  "churn_rate": 0.40,
  "churned_by_cohort": [{"cohort": "2024-01", "cohort_size": 150, "churned": 80, "churn_rate": 0.53}],
  "last_products_before_churn": [{"product_name": "...", "count": 85, "pct": 0.07}]
}
```

**Insight template:**
"Tasa de churn estimada: X%. Los clientes adquiridos en [cohorte] tienen el mayor churn (Y%). Los últimos productos comprados por churned: [lista] — potenciales señales de insatisfacción."

---

### #28 — Revenue por canal
**Category:** Revenue
**Mode:** Full
**Required columns:** `channel`, `total`, `date`

**Method:**
Normalizar valores de `channel` (strip, title case). Por canal: revenue total, órdenes, AOV, revenue % del total. Tendencia mensual por canal (evolución de participación en últimos 6 meses). Identificar canales en crecimiento vs declinando (slope de participación relativa). Si existe una sola categoría de canal o todos son iguales, reportar como dato insuficiente.

**Output:**
```json
{
  "channels": [
    {"channel": "Tienda Online", "revenue": 4500000, "pct_revenue": 0.72, "orders": 3000, "aov": 1500, "trend": "stable"}
  ],
  "monthly_by_channel": [{"month": "2024-01", "channel": "...", "revenue": 0, "pct": 0}],
  "channels_count": 4
}
```

**Insight template:**
"Canal principal: [X] con Y% del revenue. Canal en mayor crecimiento: [Z] (+N pp en participación en 6 meses)."

---

### #29 — Análisis de precio
**Category:** Revenue
**Mode:** Full
**Required columns:** `product_price`, `product_qty`, `date`

**Method:**
Distribución de precios: crear histograma con 10-15 buckets logarítmicos (o lineales si el rango de precios es < 10×). Identificar "sweet spots": los rangos de precio con mayor volumen de unidades vendidas. Para elasticidad básica: si el mismo producto tiene variación de precios en el tiempo (comparar períodos), calcular elasticidad = (% cambio qty) / (% cambio precio). Incluir solo productos con 3+ puntos de precio distintos para el análisis de elasticidad.

**Output:**
```json
{
  "price_distribution": [{"bucket_min": 0, "bucket_max": 1000, "products": 45, "units": 800, "revenue": 500000}],
  "sweet_spots": [{"price_range": "2000-3000", "units": 1500, "pct_units": 0.32}],
  "elasticity": [{"product_name": "...", "price_points": 4, "elasticity": -1.3, "interpretation": "elastic"}],
  "median_price": 2200,
  "price_range": {"min": 200, "max": 25000}
}
```

**Insight template:**
"El sweet spot de precio está en $X-$Y (Z% de las unidades). Productos elásticos al precio: [lista] — sensibles a descuentos y aumentos."

---

### #30 — Penetración por ciudad
**Category:** Geográfico
**Mode:** Full
**Required columns:** `city`, `total`

**Method:**
Normalizar nombres de ciudad (strip, title case). Calcular por ciudad: órdenes, revenue, AOV, % del revenue total. Rankear. Mostrar top-20 ciudades. Identificar ciudades con alto AOV pero bajo volumen (potencial no aprovechado). Si existe `state`, agrupar ciudades dentro de su provincia para contexto.

**Output:**
```json
{
  "top_cities": [
    {"city": "Buenos Aires", "state": "CABA", "orders": 1500, "revenue": 2700000, "aov": 1800, "pct_revenue": 0.32, "rank": 1}
  ],
  "high_aov_low_volume": [{"city": "Rosario", "aov": 3200, "orders": 80}],
  "cities_covered": 145
}
```

**Insight template:**
"Top ciudad: [X] con Y% del revenue. Ciudades con alto AOV y bajo volumen (oportunidad): [lista]."

---

### #31 — Medio de envío por zona
**Category:** Geográfico
**Mode:** Full
**Required columns:** `shipping_method`, `state`

**Method:**
Normalizar métodos de envío y provincias. Construir tabla de contingencia: filas = provincias (top-15 por volumen), columnas = métodos de envío, valores = count de órdenes y %. Identificar el método preferido (modal) por provincia. Detectar provincias donde predomina envío express vs estándar. Calcular concentración: si 1 método > 80% en una provincia, marcar como "dominant".

**Output:**
```json
{
  "cross_tab": [
    {"state": "Buenos Aires", "methods": {"Correo Argentino": {"count": 600, "pct": 0.48}, "OCA": {"count": 400, "pct": 0.32}}, "dominant_method": "Correo Argentino"}
  ],
  "methods_available": ["Correo Argentino", "OCA", "Andreani", "Pickup"],
  "provinces_analyzed": 15
}
```

**Insight template:**
"En [provincia] domina [método] (X% de órdenes). Detectar si la preferencia de envío correlaciona con costo o velocidad para optimizar opciones ofrecidas."

---

### #32 — Tiempo de fulfillment
**Category:** Operativo
**Mode:** Full
**Required columns:** `date`, `shipping_date`, `shipping_method`

**Method:**
Calcular días entre `date` (orden) y `shipping_date` (despacho). Excluir valores negativos (error de datos) y outliers extremos (> 60 días). Calcular: media, mediana, p25, p75, p90 del total. Tendencia mensual (¿mejora o empeora el fulfillment?). Breakdown por método de envío. Identificar períodos con fulfillment degradado (mediana mensual > 1.5× la mediana global).

**Output:**
```json
{
  "overall": {"mean_days": 3.2, "median_days": 2.0, "p25": 1.0, "p75": 4.0, "p90": 7.0},
  "by_method": [{"method": "OCA", "median_days": 2.0, "p90": 5.0, "orders": 800}],
  "monthly_trend": [{"month": "2024-01", "median_days": 2.5}],
  "degraded_months": ["2024-11", "2024-12"],
  "orders_excluded_bad_data": 12
}
```

**Insight template:**
"Mediana de fulfillment: N días. P90: M días (9 de cada 10 órdenes despachadas en M días). Meses con peor fulfillment: [lista] — correlacionar con períodos de alta demanda."

---

### #33 — Análisis de canal
**Category:** Operativo
**Mode:** Full
**Required columns:** `channel`, `total`, `email`, `order_status`

**Method:**
Combinación de #28 con métricas operativas. Por canal: revenue, órdenes, AOV, clientes únicos, tasa de cancelación (usando lógica de #6/#17), retención (% de clientes con 2+ órdenes). Comparar eficiencia de canales: revenue/cliente, cancelación, retención. Ordenar canales por "calidad" (baja cancelación, alta retención, alto AOV).

**Output:**
```json
{
  "channels": [
    {
      "channel": "Tienda Online",
      "orders": 3000,
      "revenue": 4500000,
      "aov": 1500,
      "unique_customers": 2200,
      "revenue_per_customer": 2045,
      "cancellation_rate": 0.03,
      "repeat_rate": 0.38
    }
  ]
}
```

**Insight template:**
"Canal más eficiente: [X] — menor cancelación (Y%), mayor retención (Z%). Canal con mayor potencial: [W] — alto AOV pero baja retención."

---

### #34 — Eficiencia de envío gratis
**Category:** Operativo
**Mode:** Full
**Required columns:** `shipping_cost`, `total`, `email`, `date`

**Method:**
Separar órdenes con shipping_cost = 0 (envío gratis) vs shipping_cost > 0 (pago). Comparar: AOV, distribución de ticket, frecuencia de recompra (días promedio entre compras para clientes que predominantemente usan envío gratis vs pago), revenue por cliente. Calcular si el envío gratis está correlacionado con órdenes de mayor ticket (¿se activa con un mínimo?). Detectar el ticket mínimo aparente para envío gratis (percentil 10 de órdenes con envío gratis).

**Output:**
```json
{
  "free_shipping": {"count": 2100, "pct": 0.42, "aov": 2800, "avg_interval_days": 38},
  "paid_shipping": {"count": 2900, "pct": 0.58, "aov": 1400, "avg_interval_days": 55},
  "implied_free_threshold": 2000,
  "aov_uplift_pct": 0.50,
  "repeat_rate_free": 0.52,
  "repeat_rate_paid": 0.31
}
```

**Insight template:**
"Órdenes con envío gratis tienen AOV X% mayor ($Y vs $Z). Clientes de envío gratis recompran más (W% vs V%). El umbral implícito de envío gratis parece ser $T."

---

### #35 — Forecast de ventas
**Category:** Estratégico
**Mode:** Full
**Required columns:** `date`, `total`

**Method:**
Calcular revenue mensual (misma lógica que #11). Requiere mínimo 6 meses de datos históricos. Aplicar dos métodos y promediarlos: (1) Moving Average: promedio de los últimos 3 meses como forecast del siguiente, proyectar 3-6 meses. (2) Linear regression: usar numpy para fit de regresión lineal (mes_index vs revenue), proyectar los próximos 3-6 meses. Forecast final = promedio de ambos métodos. Banda de confianza = ±1 desviación estándar de los residuos históricos. Si hay estacionalidad clara (del análisis #20), aplicar factor estacional multiplicativo al forecast.

**Output:**
```json
{
  "historical": [{"month": "2024-01", "revenue": 500000}],
  "forecast": [
    {"month": "2025-01", "forecast_revenue": 620000, "lower_bound": 550000, "upper_bound": 690000, "method": "avg_ma_linreg"}
  ],
  "model_stats": {"mae": 42000, "mape": 0.08, "r_squared": 0.82},
  "seasonality_applied": true,
  "months_historical": 18,
  "months_forecasted": 6
}
```

**Insight template:**
"Revenue proyectado para los próximos 6 meses: $X-$Y (rango de confianza). Tendencia implícita: [crecimiento/descenso] de Z%/mes. MAPE histórico: W% (precisión del modelo)."

---

### #36 — Recomendación de cross-sell
**Category:** Estratégico
**Mode:** Full
**Required columns:** output de análisis #1

**Method:**
Tomar el output del análisis #1. Para cada uno de los top-20 productos por revenue (cruzar con #3): encontrar los 3 productos con mayor lift donde ese producto sea el "item A". Si un producto no aparece en los pares de MBA, usar frecuencia de co-ocurrencia simple como fallback. Generar una "tarjeta de recomendación" por producto con sus 3 sugerencias de cross-sell y las métricas que la justifican.

**Output:**
```json
{
  "cross_sell_map": [
    {
      "anchor_product": "Jeans Slim Azul",
      "recommendations": [
        {"product": "Remera Básica Negra", "lift": 3.2, "confidence": 0.45, "support": 0.03, "rationale": "MBA lift"},
        {"product": "Cinturón Cuero", "lift": 2.8, "confidence": 0.38, "support": 0.02, "rationale": "MBA lift"},
        {"product": "Zapatilla Casual", "lift": 2.1, "confidence": 0.28, "support": 0.015, "rationale": "MBA lift"}
      ]
    }
  ],
  "products_covered": 20
}
```

**Insight template:**
"Para el producto [X]: cross-sell recomendado [A] (lift N×), [B] (lift M×), [C] (lift P×). Implementar en PDP como 'completá tu look'."

---

### #37 — Análisis de pricing
**Category:** Estratégico
**Mode:** Full
**Required columns:** `product_name`, `product_price`, `product_qty`

**Method:**
Extraer categoría de product_name (igual que #2/#13). Por categoría: calcular precio promedio ponderado por volumen (sum(price×qty) / sum(qty)), precio mediano, precio mínimo y máximo. Identificar productos "under-priced" (precio < percentil 25 de su categoría) y "over-priced" (precio > percentil 75) en relación a su volumen de ventas: si un producto tiene precio bajo y baja demanda = posiblemente subvalorado; si tiene precio alto y baja demanda = posiblemente sobrevalorado. Calcular el "precio óptimo sugerido" como el precio más común en el decil de mayor volumen de la categoría.

**Output:**
```json
{
  "categories": [
    {
      "category": "Remeras",
      "avg_price_weighted": 1850,
      "median_price": 1800,
      "price_range": {"min": 900, "max": 3500},
      "suggested_price_range": {"low": 1500, "high": 2200},
      "underpriced_products": [{"product": "...", "price": 900, "units": 50}],
      "overpriced_products": [{"product": "...", "price": 3500, "units": 8}]
    }
  ]
}
```

**Insight template:**
"En categoría [X], el rango óptimo de precio (mayor volumen) es $A-$B. Productos potencialmente subvalorados: [lista]. Revisar si tienen margen para subir precio sin perder demanda."

---

### #38 — Identificación de nichos
**Category:** Estratégico
**Mode:** Full
**Required columns:** `email`, `date`, `total`

**Method:**
Construir feature matrix por cliente: total_spend, order_count, aov (total_spend/order_count), days_since_last_order, avg_days_between_orders (para clientes con 1 orden, usar mediana global). Normalizar features (min-max scaling manual con numpy). Implementar k-means básico con numpy (inicialización random, iteración hasta convergencia o 100 iteraciones). Probar k=3,4,5 y seleccionar usando inercia (elbow method simplificado). Si numpy no disponible, usar segmentación por cuartiles como fallback (2×2 de frecuencia × gasto). Perfilar cada cluster con sus estadísticas.

**Output:**
```json
{
  "k_selected": 4,
  "method": "kmeans",
  "clusters": [
    {
      "cluster_id": 0,
      "size": 450,
      "pct": 0.15,
      "profile": {"avg_spend": 45000, "avg_orders": 8.2, "avg_aov": 5487, "avg_days_since_last": 25, "avg_interval": 30},
      "label": "VIP Frecuentes",
      "revenue_share": 0.52
    }
  ],
  "inertia_by_k": {"3": 2500, "4": 1800, "5": 1700},
  "features_used": ["total_spend", "order_count", "aov", "days_since_last_order"]
}
```

**Insight template:**
"Se identificaron N nichos distintos. Cluster más valioso: [label] — X% de clientes, Y% del revenue. Cluster con mayor potencial de crecimiento: [label] — alta frecuencia pero bajo ticket."

---

## Notas de implementación

### Detección de cancelaciones (compartido por #6, #17, #27)
```python
CANCEL_KEYWORDS = ["cancelad", "cancelled", "cancel", "refund", "devoluci", "returned", "anulad"]

def is_cancelled(row):
    if 'cancellation_date' in row and pd.notna(row['cancellation_date']):
        return True
    if 'order_status' in row:
        return any(kw in str(row['order_status']).lower() for kw in CANCEL_KEYWORDS)
    return False
```

### Extracción de categoría (compartido por #2, #13, #24, #37)
```python
def extract_category(product_name):
    # Estrategia 1: todo lo antes del primer " - " o " – "
    if " - " in product_name:
        return product_name.split(" - ")[0].strip()
    if " – " in product_name:
        return product_name.split(" – ")[0].strip()
    # Estrategia 2: primera palabra si el nombre es compuesto
    parts = product_name.split()
    return parts[0] if parts else "Sin categoría"
```

### Manejo de dependencias entre análisis
- #19 (Bundling) depende de #1 (MBA) → ejecutar #1 primero
- #36 (Cross-sell) depende de #1 (MBA) y #3 (Ranking) → ejecutar ambos primero
- En modo Full, ejecutar todos los análisis base antes de los dependientes

### Mínimos de datos para activar un análisis
- Mínimo 50 órdenes para análisis de producto
- Mínimo 100 clientes para análisis de cliente
- Mínimo 6 meses para análisis de tendencias y forecast
- Mínimo 2 órdenes por cliente para análisis de cohortes e intervalos
- Si no se cumplen: incluir en output `"skipped": true, "reason": "insufficient_data"`
