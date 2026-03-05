# HTML Template — {{brand_name}} BI Report

## Instrucciones

Este template define la estructura HTML completa del informe de Business Intelligence.
Claude debe usar este template como base, reemplazando los placeholders `{{...}}` con datos reales del JSON de resultados.

## Branding

| Elemento | Dark Mode | Print Mode |
|----------|-----------|------------|
| Background | `#0a0a0a` | `#ffffff` |
| Text primary | `#f5f5f5` | `#1a1a1a` |
| Text secondary | `#a3a3a3` | `#525252` |
| Lime accent | `#E4FF5A` | `#3346FF` |
| Blue accent | `#3346FF` | `#3346FF` |
| Card bg | `#141414` | `#f9f9f9` |
| Card border | `#262626` | `#e5e5e5` |
| Grid pattern | lime 3% opacity | none |
| Font | Geist (Google Fonts) | Geist |

## Template HTML

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{business_name}} — Business Intelligence Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        /* ═══════════════════════════════════════
           BASE & RESET
           ═══════════════════════════════════════ */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg: #0a0a0a;
            --bg-card: #141414;
            --bg-card-hover: #1a1a1a;
            --border: #262626;
            --border-hover: #404040;
            --text-primary: #f5f5f5;
            --text-secondary: #a3a3a3;
            --text-muted: #737373;
            --lime: #E4FF5A;
            --lime-dim: rgba(228, 255, 90, 0.15);
            --lime-glow: rgba(228, 255, 90, 0.08);
            --blue: #3346FF;
            --blue-dim: rgba(51, 70, 255, 0.15);
            --green: #22c55e;
            --red: #ef4444;
            --amber: #f59e0b;
            --font: 'Geist', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        body {
            font-family: var(--font);
            background: var(--bg);
            color: var(--text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }

        /* Grid background */
        body::before {
            content: '';
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(rgba(228, 255, 90, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(228, 255, 90, 0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            pointer-events: none;
            z-index: 0;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 24px;
            position: relative;
            z-index: 1;
        }

        /* ═══════════════════════════════════════
           HEADER
           ═══════════════════════════════════════ */
        .report-header {
            text-align: center;
            margin-bottom: 48px;
            padding-bottom: 48px;
            border-bottom: 1px solid var(--border);
        }

        .report-header .brand {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--lime);
            margin-bottom: 24px;
        }

        .report-header .brand::before,
        .report-header .brand::after {
            content: '';
            width: 24px;
            height: 1px;
            background: var(--lime);
            opacity: 0.5;
        }

        .report-header h1 {
            font-size: 42px;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 8px;
        }

        .report-header .subtitle {
            font-size: 18px;
            color: var(--text-secondary);
            font-weight: 400;
        }

        .report-header .meta {
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-top: 16px;
            font-size: 13px;
            color: var(--text-muted);
        }

        .report-header .meta span {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .report-header .meta .badge {
            background: var(--lime-dim);
            color: var(--lime);
            padding: 2px 10px;
            border-radius: 100px;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* ═══════════════════════════════════════
           HERO METRICS
           ═══════════════════════════════════════ */
        .hero-metrics {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 48px;
        }

        .hero-metric {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            transition: border-color 0.2s;
        }

        .hero-metric:hover {
            border-color: var(--border-hover);
        }

        .hero-metric .label {
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }

        .hero-metric .value {
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -1px;
            color: var(--text-primary);
        }

        .hero-metric .change {
            font-size: 13px;
            font-weight: 500;
            margin-top: 4px;
        }

        .hero-metric .change.positive { color: var(--green); }
        .hero-metric .change.negative { color: var(--red); }

        /* ═══════════════════════════════════════
           SECTIONS
           ═══════════════════════════════════════ */
        .section {
            margin-bottom: 48px;
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }

        .section-header .icon {
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--lime-dim);
            border-radius: 10px;
            font-size: 20px;
        }

        .section-header h2 {
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .section-header .count {
            font-size: 12px;
            color: var(--text-muted);
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 2px 10px;
            border-radius: 100px;
            margin-left: auto;
        }

        /* ═══════════════════════════════════════
           ANALYSIS CARDS
           ═══════════════════════════════════════ */
        .analysis-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 28px;
            margin-bottom: 20px;
            transition: border-color 0.2s;
        }

        .analysis-card:hover {
            border-color: var(--border-hover);
        }

        .analysis-card .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }

        .analysis-card .card-header h3 {
            font-size: 18px;
            font-weight: 600;
        }

        .analysis-card .card-header .analysis-id {
            font-size: 11px;
            font-weight: 600;
            color: var(--blue);
            background: var(--blue-dim);
            padding: 2px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
        }

        /* ═══════════════════════════════════════
           TABLES
           ═══════════════════════════════════════ */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            margin-bottom: 16px;
        }

        .data-table thead th {
            text-align: left;
            padding: 10px 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
        }

        .data-table tbody td {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            color: var(--text-secondary);
        }

        .data-table tbody tr:hover td {
            background: rgba(255,255,255,0.02);
        }

        .data-table .number {
            font-variant-numeric: tabular-nums;
            text-align: right;
        }

        .data-table .highlight {
            color: var(--lime);
            font-weight: 600;
        }

        /* ═══════════════════════════════════════
           BAR CHARTS (CSS only)
           ═══════════════════════════════════════ */
        .bar-chart {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 16px;
        }

        .bar-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .bar-label {
            width: 180px;
            font-size: 13px;
            color: var(--text-secondary);
            text-align: right;
            flex-shrink: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .bar-track {
            flex: 1;
            height: 28px;
            background: rgba(255,255,255,0.04);
            border-radius: 6px;
            overflow: hidden;
            position: relative;
        }

        .bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--lime), rgba(228, 255, 90, 0.6));
            border-radius: 6px;
            transition: width 0.3s ease;
            min-width: 2px;
        }

        .bar-fill.blue {
            background: linear-gradient(90deg, var(--blue), rgba(51, 70, 255, 0.6));
        }

        .bar-value {
            width: 100px;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
        }

        /* ═══════════════════════════════════════
           HEATMAP (CSS grid)
           ═══════════════════════════════════════ */
        .heatmap {
            display: grid;
            gap: 2px;
            margin-bottom: 16px;
        }

        .heatmap-cell {
            padding: 6px 8px;
            text-align: center;
            font-size: 11px;
            font-weight: 500;
            border-radius: 4px;
            color: var(--text-primary);
        }

        .heatmap-header {
            font-size: 10px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Heatmap intensity levels */
        .heat-0 { background: rgba(228, 255, 90, 0.05); }
        .heat-1 { background: rgba(228, 255, 90, 0.15); }
        .heat-2 { background: rgba(228, 255, 90, 0.30); }
        .heat-3 { background: rgba(228, 255, 90, 0.50); }
        .heat-4 { background: rgba(228, 255, 90, 0.70); color: #0a0a0a; }
        .heat-5 { background: rgba(228, 255, 90, 0.90); color: #0a0a0a; font-weight: 700; }

        /* ═══════════════════════════════════════
           RFM GRID
           ═══════════════════════════════════════ */
        .rfm-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }

        .rfm-segment {
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }

        .rfm-segment .seg-name {
            font-size: 12px;
            font-weight: 600;
            color: var(--lime);
            margin-bottom: 4px;
        }

        .rfm-segment .seg-count {
            font-size: 24px;
            font-weight: 800;
            color: var(--text-primary);
        }

        .rfm-segment .seg-pct {
            font-size: 12px;
            color: var(--text-muted);
        }

        /* ═══════════════════════════════════════
           INSIGHTS
           ═══════════════════════════════════════ */
        .insight-box {
            background: var(--lime-glow);
            border-left: 3px solid var(--lime);
            border-radius: 0 8px 8px 0;
            padding: 16px 20px;
            margin-top: 16px;
        }

        .insight-box .insight-label {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--lime);
            margin-bottom: 6px;
        }

        .insight-box p {
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.7;
        }

        .recommendation-box {
            background: var(--blue-dim);
            border-left: 3px solid var(--blue);
            border-radius: 0 8px 8px 0;
            padding: 16px 20px;
            margin-top: 12px;
        }

        .recommendation-box .rec-label {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--blue);
            margin-bottom: 6px;
        }

        .recommendation-box p {
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.7;
        }

        /* ═══════════════════════════════════════
           SKIPPED ANALYSIS
           ═══════════════════════════════════════ */
        .skipped {
            opacity: 0.5;
            border-style: dashed;
        }

        .skipped .skip-reason {
            font-size: 13px;
            color: var(--text-muted);
            font-style: italic;
            text-align: center;
            padding: 20px;
        }

        /* ═══════════════════════════════════════
           FOOTER
           ═══════════════════════════════════════ */
        .report-footer {
            text-align: center;
            padding-top: 48px;
            margin-top: 48px;
            border-top: 1px solid var(--border);
        }

        .report-footer .brand-footer {
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--text-muted);
        }

        .report-footer .brand-footer span {
            color: var(--lime);
        }

        .report-footer .disclaimer {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 8px;
            opacity: 0.6;
        }

        /* ═══════════════════════════════════════
           PRINT STYLES
           ═══════════════════════════════════════ */
        @media print {
            :root {
                --bg: #ffffff;
                --bg-card: #f9f9f9;
                --bg-card-hover: #f5f5f5;
                --border: #e5e5e5;
                --border-hover: #d4d4d4;
                --text-primary: #1a1a1a;
                --text-secondary: #525252;
                --text-muted: #737373;
                --lime: #3346FF;
                --lime-dim: rgba(51, 70, 255, 0.1);
                --lime-glow: rgba(51, 70, 255, 0.05);
                --blue: #3346FF;
                --blue-dim: rgba(51, 70, 255, 0.1);
            }

            body::before { display: none; }
            body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }

            .analysis-card { break-inside: avoid; }
            .section { break-before: page; }
            .section:first-of-type { break-before: auto; }

            .hero-metrics { grid-template-columns: repeat(4, 1fr); }

            .bar-fill {
                background: var(--blue) !important;
            }
        }

        /* ═══════════════════════════════════════
           RESPONSIVE
           ═══════════════════════════════════════ */
        @media (max-width: 768px) {
            .hero-metrics { grid-template-columns: repeat(2, 1fr); }
            .hero-metric .value { font-size: 24px; }
            .report-header h1 { font-size: 28px; }
            .rfm-grid { grid-template-columns: repeat(2, 1fr); }
            .bar-label { width: 120px; }
        }
    </style>
</head>
<body>
    <div class="container">

        <!-- ═══ HEADER ═══ -->
        <header class="report-header">
            <div class="brand">{{brand_name}}</div>
            <h1>{{business_name}}</h1>
            <p class="subtitle">Business Intelligence Report</p>
            <div class="meta">
                <span>{{date_range}}</span>
                <span>•</span>
                <span><span class="badge">{{mode}}</span></span>
                <span>•</span>
                <span>{{total_analyses}} análisis</span>
            </div>
        </header>

        <!-- ═══ HERO METRICS ═══ -->
        <div class="hero-metrics">
            <div class="hero-metric">
                <div class="label">Revenue Total</div>
                <div class="value">{{total_revenue}}</div>
                <div class="change {{revenue_trend_class}}">{{revenue_trend}}</div>
            </div>
            <div class="hero-metric">
                <div class="label">Órdenes</div>
                <div class="value">{{total_orders}}</div>
                <div class="change {{orders_trend_class}}">{{orders_trend}}</div>
            </div>
            <div class="hero-metric">
                <div class="label">Clientes Únicos</div>
                <div class="value">{{unique_customers}}</div>
                <div class="change {{customers_trend_class}}">{{customers_trend}}</div>
            </div>
            <div class="hero-metric">
                <div class="label">Ticket Promedio</div>
                <div class="value">{{avg_ticket}}</div>
                <div class="change {{ticket_trend_class}}">{{ticket_trend}}</div>
            </div>
        </div>

        <!-- ═══ SECTIONS ═══ -->
        <!--
            Repeat for each category: Producto, Cliente, Revenue, Geográfico, Operativo, Estratégico
            Icons: 🛍️ Producto, 👥 Cliente, 💰 Revenue, 🗺️ Geográfico, ⚙️ Operativo, 🎯 Estratégico
        -->

        <div class="section" id="section-producto">
            <div class="section-header">
                <div class="icon">🛍️</div>
                <h2>Producto</h2>
                <span class="count">{{producto_count}} análisis</span>
            </div>

            <!-- Repeat for each analysis in this category -->
            <div class="analysis-card">
                <div class="card-header">
                    <h3>{{analysis_title}}</h3>
                    <span class="analysis-id">#{{analysis_number}}</span>
                </div>

                <!-- DATA VISUALIZATION goes here: table, bar-chart, heatmap, rfm-grid, etc. -->

                <div class="insight-box">
                    <div class="insight-label">Insight</div>
                    <p>{{insight_text}}</p>
                </div>

                <div class="recommendation-box">
                    <div class="rec-label">Recomendación</div>
                    <p>{{recommendation_text}}</p>
                </div>
            </div>

            <!-- If analysis was skipped -->
            <div class="analysis-card skipped">
                <div class="card-header">
                    <h3>{{analysis_title}}</h3>
                    <span class="analysis-id">#{{analysis_number}}</span>
                </div>
                <div class="skip-reason">{{skip_reason}}</div>
            </div>
        </div>

        <!-- Repeat section pattern for: Cliente, Revenue, Geográfico, Operativo, Estratégico -->

        <!-- ═══ FOOTER ═══ -->
        <footer class="report-footer">
            <div class="brand-footer"><span>{{brand_name}}</span> — Business Intelligence Report</div>
            <div class="disclaimer">Generado el {{generation_date}} • Datos de {{platform}} • {{total_rows}} registros procesados</div>
        </footer>

    </div>
</body>
</html>
```

## Sección Icons

| Categoría | Icon | Color accent |
|-----------|------|-------------|
| Producto | 🛍️ | lime |
| Cliente | 👥 | lime |
| Revenue | 💰 | lime |
| Geográfico | 🗺️ | lime |
| Operativo | ⚙️ | lime |
| Estratégico | 🎯 | lime |

## Visualization Patterns

### Tabla estándar
```html
<table class="data-table">
    <thead>
        <tr><th>Producto</th><th class="number">Revenue</th><th class="number">Unidades</th></tr>
    </thead>
    <tbody>
        <tr><td>Producto A</td><td class="number highlight">$125,000</td><td class="number">450</td></tr>
    </tbody>
</table>
```

### Bar chart horizontal
```html
<div class="bar-chart">
    <div class="bar-row">
        <span class="bar-label">Buenos Aires</span>
        <div class="bar-track"><div class="bar-fill" style="width: 85%"></div></div>
        <span class="bar-value">$2.4M</span>
    </div>
</div>
```

### Heatmap (para cohortes)
```html
<div class="heatmap" style="grid-template-columns: 100px repeat(12, 1fr);">
    <div class="heatmap-header">Cohorte</div>
    <div class="heatmap-header">M+1</div>
    <!-- ... -->
    <div class="heatmap-cell">Ene 2025</div>
    <div class="heatmap-cell heat-3">15%</div>
    <!-- ... -->
</div>
```

### RFM Grid
```html
<div class="rfm-grid">
    <div class="rfm-segment">
        <div class="seg-name">Champions</div>
        <div class="seg-count">234</div>
        <div class="seg-pct">4.7%</div>
    </div>
</div>
```

## Reglas de formato numérico

- Currency: `$XXX.XXX` (punto como separador de miles, sin decimales para valores grandes; con 2 decimales para ticket promedio)
- Porcentajes: `XX.X%` (1 decimal)
- Cantidades: `X.XXX` (punto como separador de miles)
- Lift (Market Basket): `X.XX` (2 decimales)
- Support/Confidence: `X.X%` (1 decimal)

## Notas para Claude

1. El HTML debe ser **self-contained** (no dependencias externas excepto Google Fonts)
2. Los charts son CSS puro — no usar JS charting libraries
3. Cada análisis genera su propia visualización (tabla, bars, heatmap, grid) según el tipo de dato
4. Si un análisis fue skipped, usar la clase `.skipped` con la razón
5. Los insights y recomendaciones los escribe Claude basándose en los datos del JSON — NO son template estáticos
6. Abrir en browser y debe verse bien tanto en pantalla como impreso (Ctrl+P)
