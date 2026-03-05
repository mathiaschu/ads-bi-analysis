# HTML Template — {{brand_name}} Google Ads Report (Slides)

## Instrucciones

Este template define la estructura HTML completa del informe de Google Ads como presentación de slides full-screen. Claude debe usar este template como base, reemplazando los placeholders `{{...}}` con datos reales del análisis.

**Formato:** Slide-based (como meta-ads-html). Cada análisis ocupa un slide completo. Navegación por teclado o click.

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
| Semaphore green | `#22c55e` | `#22c55e` |
| Semaphore amber | `#f59e0b` | `#f59e0b` |
| Semaphore red | `#ef4444` | `#ef4444` |

## Navegación

| Tecla / Acción | Comportamiento |
|----------------|---------------|
| `→` / `ArrowRight` | Slide siguiente |
| `←` / `ArrowLeft` | Slide anterior |
| `1`–`9` | Saltar al slide N |
| Click mitad derecha | Slide siguiente |
| Click mitad izquierda | Slide anterior |
| Progress bar (bottom) | Indicador visual de posición |
| Slide counter (top-right) | "3 / 18" |

## Estructura de Slides

### Slide 1: Title Slide
- Brand badge "{{brand_name}}" (lime)
- Nombre del cliente (h1 grande)
- "Google Ads Report" (subtítulo)
- Rango de fechas analizado
- Mode badge (Lite / Full)
- Hero metrics: Inversión, Conversiones, CPA, ROAS
- Conversion lag warning banner (si aplica)

### Slides 2–N: Analysis Slides
- **Top:** número de slide + ícono de categoría + título del análisis
- **Middle:** visualización (tabla, bar chart, heatmap, funnel, scatter)
- **Bottom:** insight box (lime) + recommendation box (blue)
- **Si fue skipped:** slide con borde punteado + razón del skip

### Footer en cada slide
"{{brand_name}} — Google Ads Report" + contador "N / Total"

## Category Icons

| Categoría | Icon |
|-----------|------|
| Overview | 📊 |
| Campañas | 📢 |
| Keywords | 🔑 |
| Search Terms | 🔍 |
| Ads | 📝 |
| Funnel | 🔽 |
| Temporal | 📅 |
| Geo | 🗺️ |
| Device | 📱 |
| PMax | 🤖 |
| Smart Bidding | 🎯 |
| Conversion | 🔄 |
| Auction | ⚔️ |
| Estratégico | ⚡ |

## Semaphore Logic

| Métrica | Verde | Amarillo | Rojo |
|---------|-------|----------|------|
| CTR | >3% | 1.5–3% | <1.5% |
| Conv Rate | >3% | 1–3% | <1% |
| ROAS | >4x | 2–4x | <2x |
| CPA | < target | ~ target | > 1.5x target |
| Quality Score | 7–10 | 5–6 | 1–4 |
| Impression Share | >80% | 50–80% | <50% |

Clases CSS: `.semaphore-green`, `.semaphore-yellow`, `.semaphore-red`

## Conversion Lag Warning Banner

Cuando los datos incluyen los últimos 7 días, mostrar un banner en el title slide:

```html
<div class="conv-lag-banner">
    ⚠️ Los últimos 7 días tienen datos de conversión incompletos por conversion lag. Las métricas de ese período pueden estar subrepresentadas.
</div>
```

## Formato Numérico

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| Currency | `$XXX.XXX` (punto miles, sin decimales para valores grandes) | `$2.340.500` |
| Porcentajes | `XX.X%` (1 decimal) | `3.4%` |
| ROAS | `X.XX` (2 decimales) | `4.32` |
| Números grandes | `X.XXX` (punto miles) | `12.450` |
| CPA | `$X.XXX` | `$1.250` |
| Quality Score | `X/10` | `7/10` |

## Template HTML

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{client_name}} — Google Ads Report</title>
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
            --lime-dim: rgba(228, 255, 90, 0.12);
            --lime-glow: rgba(228, 255, 90, 0.06);
            --blue: #3346FF;
            --blue-dim: rgba(51, 70, 255, 0.12);
            --green: #22c55e;
            --green-dim: rgba(34, 197, 94, 0.12);
            --red: #ef4444;
            --red-dim: rgba(239, 68, 68, 0.12);
            --amber: #f59e0b;
            --amber-dim: rgba(245, 158, 11, 0.12);
            --font: 'Geist', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        html, body {
            width: 100%;
            height: 100%;
            overflow: hidden;
            font-family: var(--font);
            background: var(--bg);
            color: var(--text-primary);
            -webkit-font-smoothing: antialiased;
        }

        /* ═══════════════════════════════════════
           SLIDES CONTAINER
           ═══════════════════════════════════════ */
        .slides-wrapper {
            position: fixed;
            inset: 0;
            overflow: hidden;
        }

        .slides-track {
            display: flex;
            width: 100%;
            height: 100%;
            transition: transform 0.45s cubic-bezier(0.4, 0, 0.2, 1);
            will-change: transform;
        }

        .slide {
            min-width: 100vw;
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }

        /* Grid background */
        .slide::before {
            content: '';
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(rgba(228, 255, 90, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(228, 255, 90, 0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            pointer-events: none;
            z-index: 0;
        }

        .slide-inner {
            position: relative;
            z-index: 1;
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 48px 64px 32px;
            overflow: hidden;
        }

        /* ═══════════════════════════════════════
           PROGRESS BAR
           ═══════════════════════════════════════ */
        .progress-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: rgba(255,255,255,0.06);
            z-index: 100;
        }

        .progress-fill {
            height: 100%;
            background: var(--lime);
            transition: width 0.45s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* ═══════════════════════════════════════
           SLIDE COUNTER
           ═══════════════════════════════════════ */
        .slide-counter {
            position: fixed;
            top: 20px;
            right: 32px;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-muted);
            letter-spacing: 1px;
            z-index: 100;
            font-variant-numeric: tabular-nums;
        }

        .slide-counter .current { color: var(--lime); }

        /* ═══════════════════════════════════════
           NAV HINTS
           ═══════════════════════════════════════ */
        .nav-hint {
            position: fixed;
            bottom: 14px;
            font-size: 11px;
            color: var(--text-muted);
            opacity: 0.5;
            z-index: 100;
            letter-spacing: 0.5px;
        }

        .nav-hint.left { left: 32px; }
        .nav-hint.right { right: 32px; }

        /* ═══════════════════════════════════════
           SLIDE FOOTER
           ═══════════════════════════════════════ */
        .slide-footer {
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 64px;
            border-top: 1px solid var(--border);
            flex-shrink: 0;
        }

        .slide-footer .brand-footer {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: var(--text-muted);
        }

        .slide-footer .brand-footer span { color: var(--lime); }

        .slide-footer .slide-num {
            font-size: 11px;
            color: var(--text-muted);
            font-variant-numeric: tabular-nums;
        }

        .watermark {
            position: fixed;
            bottom: 4px;
            right: 12px;
            font-size: 7px;
            color: var(--text-muted);
            opacity: 0.15;
            letter-spacing: 0.3px;
            z-index: 0;
            pointer-events: none;
        }
        .watermark a { color: inherit; text-decoration: none; }

        /* ═══════════════════════════════════════
           TITLE SLIDE (Slide 1)
           ═══════════════════════════════════════ */
        .slide-title .slide-inner {
            justify-content: center;
            align-items: flex-start;
            gap: 0;
        }

        .slide-title .brand-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            color: var(--lime);
            margin-bottom: 32px;
        }

        .slide-title .brand-badge::before,
        .slide-title .brand-badge::after {
            content: '';
            width: 20px;
            height: 1px;
            background: var(--lime);
            opacity: 0.5;
        }

        .slide-title h1 {
            font-size: 72px;
            font-weight: 900;
            letter-spacing: -3px;
            line-height: 1;
            margin-bottom: 12px;
        }

        .slide-title .report-type {
            font-size: 22px;
            font-weight: 400;
            color: var(--text-secondary);
            letter-spacing: -0.5px;
            margin-bottom: 24px;
        }

        .slide-title .meta-row {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 32px;
        }

        .slide-title .date-range {
            font-size: 14px;
            color: var(--text-muted);
        }

        .slide-title .mode-badge {
            background: var(--lime-dim);
            color: var(--lime);
            padding: 3px 12px;
            border-radius: 100px;
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            border: 1px solid rgba(228, 255, 90, 0.25);
        }

        /* Conversion lag warning banner */
        .conv-lag-banner {
            background: var(--amber-dim);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 12px;
            color: var(--amber);
            margin-bottom: 24px;
            max-width: 900px;
            line-height: 1.5;
        }

        .slide-title .hero-metrics {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            max-width: 900px;
        }

        .slide-title .hero-metric {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px 24px;
        }

        .slide-title .hero-metric .metric-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }

        .slide-title .hero-metric .metric-value {
            font-size: 30px;
            font-weight: 800;
            letter-spacing: -1px;
        }

        .slide-title .hero-metric .metric-sub {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        .slide-title .hero-metric.accent-lime {
            border-color: rgba(228, 255, 90, 0.2);
            background: var(--lime-glow);
        }

        .slide-title .hero-metric.accent-lime .metric-value { color: var(--lime); }

        /* ═══════════════════════════════════════
           ANALYSIS SLIDE HEADER
           ═══════════════════════════════════════ */
        .slide-analysis .slide-inner { gap: 20px; }

        .analysis-slide-header {
            display: flex;
            align-items: center;
            gap: 14px;
            flex-shrink: 0;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }

        .analysis-slide-header .cat-icon {
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--lime-dim);
            border-radius: 10px;
            font-size: 22px;
            flex-shrink: 0;
            border: 1px solid rgba(228, 255, 90, 0.15);
        }

        .analysis-slide-header .header-text { flex: 1; }

        .analysis-slide-header h2 {
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.5px;
            line-height: 1.2;
        }

        .analysis-slide-header .analysis-meta {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 4px;
        }

        .analysis-slide-header .analysis-id {
            font-size: 11px;
            font-weight: 700;
            color: var(--blue);
            background: var(--blue-dim);
            padding: 2px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
        }

        .analysis-slide-header .analysis-cat {
            font-size: 12px;
            color: var(--text-muted);
        }

        /* ═══════════════════════════════════════
           VISUALIZATION AREA
           ═══════════════════════════════════════ */
        .viz-area {
            flex: 1;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            min-height: 0;
        }

        /* ═══════════════════════════════════════
           INSIGHT + RECOMMENDATION BOXES
           ═══════════════════════════════════════ */
        .bottom-boxes {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            flex-shrink: 0;
        }

        .insight-box {
            background: var(--lime-glow);
            border-left: 3px solid var(--lime);
            border-radius: 0 8px 8px 0;
            padding: 14px 18px;
        }

        .insight-box .box-label {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--lime);
            margin-bottom: 5px;
        }

        .insight-box p {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        .recommendation-box {
            background: var(--blue-dim);
            border-left: 3px solid var(--blue);
            border-radius: 0 8px 8px 0;
            padding: 14px 18px;
        }

        .recommendation-box .box-label {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--blue);
            margin-bottom: 5px;
        }

        .recommendation-box p {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        /* ═══════════════════════════════════════
           SKIPPED SLIDE
           ═══════════════════════════════════════ */
        .slide-skipped .slide-inner {
            justify-content: center;
            align-items: center;
        }

        .skipped-card {
            border: 2px dashed var(--border);
            border-radius: 16px;
            padding: 48px 64px;
            text-align: center;
            max-width: 600px;
            opacity: 0.6;
        }

        .skipped-card .skip-icon { font-size: 40px; margin-bottom: 16px; }
        .skipped-card h3 { font-size: 22px; font-weight: 600; margin-bottom: 12px; }

        .skipped-card .skip-reason {
            font-size: 14px;
            color: var(--text-muted);
            font-style: italic;
            line-height: 1.6;
        }

        /* ═══════════════════════════════════════
           TABLES
           ═══════════════════════════════════════ */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        .data-table thead th {
            text-align: left;
            padding: 8px 12px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
        }

        .data-table tbody td {
            padding: 9px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            color: var(--text-secondary);
        }

        .data-table tbody tr:hover td { background: rgba(255,255,255,0.02); }

        .data-table .number { font-variant-numeric: tabular-nums; text-align: right; }
        .data-table .highlight { color: var(--lime); font-weight: 600; }

        .data-table .name-cell {
            max-width: 240px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        /* Semaphore cells */
        .semaphore-green {
            color: var(--green);
            font-weight: 600;
            background: var(--green-dim);
            border-radius: 4px;
            padding: 2px 8px;
            display: inline-block;
            font-size: 12px;
        }

        .semaphore-yellow {
            color: var(--amber);
            font-weight: 600;
            background: var(--amber-dim);
            border-radius: 4px;
            padding: 2px 8px;
            display: inline-block;
            font-size: 12px;
        }

        .semaphore-red {
            color: var(--red);
            font-weight: 600;
            background: var(--red-dim);
            border-radius: 4px;
            padding: 2px 8px;
            display: inline-block;
            font-size: 12px;
        }

        /* QS Badge */
        .qs-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 700;
        }

        .qs-badge.qs-high { background: var(--green-dim); color: var(--green); }
        .qs-badge.qs-mid { background: var(--amber-dim); color: var(--amber); }
        .qs-badge.qs-low { background: var(--red-dim); color: var(--red); }

        /* ═══════════════════════════════════════
           BAR CHARTS
           ═══════════════════════════════════════ */
        .bar-chart {
            display: flex;
            flex-direction: column;
            gap: 7px;
        }

        .bar-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .bar-label {
            width: 200px;
            font-size: 12px;
            color: var(--text-secondary);
            text-align: right;
            flex-shrink: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .bar-track {
            flex: 1;
            height: 26px;
            background: rgba(255,255,255,0.04);
            border-radius: 5px;
            overflow: hidden;
        }

        .bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--lime), rgba(228, 255, 90, 0.5));
            border-radius: 5px;
            min-width: 2px;
        }

        .bar-fill.blue { background: linear-gradient(90deg, var(--blue), rgba(51, 70, 255, 0.5)); }
        .bar-fill.green { background: linear-gradient(90deg, var(--green), rgba(34, 197, 94, 0.5)); }
        .bar-fill.red { background: linear-gradient(90deg, var(--red), rgba(239, 68, 68, 0.5)); }

        .bar-value {
            width: 90px;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
        }

        /* ═══════════════════════════════════════
           HEATMAP
           ═══════════════════════════════════════ */
        .heatmap { display: grid; gap: 2px; }

        .heatmap-cell {
            padding: 5px 6px;
            text-align: center;
            font-size: 11px;
            font-weight: 500;
            border-radius: 3px;
            color: var(--text-primary);
        }

        .heatmap-header {
            font-size: 9px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .heat-0 { background: rgba(228, 255, 90, 0.04); }
        .heat-1 { background: rgba(228, 255, 90, 0.14); }
        .heat-2 { background: rgba(228, 255, 90, 0.28); }
        .heat-3 { background: rgba(228, 255, 90, 0.46); }
        .heat-4 { background: rgba(228, 255, 90, 0.68); color: #0a0a0a; }
        .heat-5 { background: rgba(228, 255, 90, 0.90); color: #0a0a0a; font-weight: 700; }

        /* ═══════════════════════════════════════
           FUNNEL
           ═══════════════════════════════════════ */
        .funnel {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 2px;
        }

        .funnel-step {
            display: flex;
            align-items: center;
            gap: 16px;
            width: 100%;
            max-width: 600px;
        }

        .funnel-bar-wrap { flex: 1; display: flex; justify-content: center; }

        .funnel-bar {
            height: 36px;
            background: var(--lime-dim);
            border: 1px solid rgba(228, 255, 90, 0.2);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 600;
            color: var(--lime);
        }

        .funnel-meta { width: 160px; }
        .funnel-meta .step-name { font-size: 12px; color: var(--text-secondary); font-weight: 500; }
        .funnel-meta .step-value { font-size: 16px; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }
        .funnel-meta .step-rate { font-size: 11px; color: var(--text-muted); }
        .funnel-arrow { text-align: center; color: var(--text-muted); font-size: 14px; padding: 2px 0; }

        /* ═══════════════════════════════════════
           SCATTER PLOT
           ═══════════════════════════════════════ */
        .scatter-wrap {
            position: relative;
            width: 100%;
            height: 200px;
            border-left: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
        }

        .scatter-dot {
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            transform: translate(-50%, 50%);
            background: var(--lime);
            opacity: 0.7;
        }

        .scatter-dot.large { width: 16px; height: 16px; }
        .scatter-dot.small { width: 7px; height: 7px; }
        .scatter-dot.blue { background: var(--blue); }
        .scatter-dot.red { background: var(--red); }

        .scatter-label-x {
            position: absolute;
            bottom: -18px;
            font-size: 10px;
            color: var(--text-muted);
            transform: translateX(-50%);
        }

        .scatter-axis-label {
            font-size: 10px;
            color: var(--text-muted);
            text-align: center;
            margin-top: 4px;
        }

        /* ═══════════════════════════════════════
           METRIC GRID
           ═══════════════════════════════════════ */
        .metric-grid { display: grid; gap: 12px; }
        .metric-grid.cols-2 { grid-template-columns: repeat(2, 1fr); }
        .metric-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
        .metric-grid.cols-4 { grid-template-columns: repeat(4, 1fr); }

        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px 20px;
        }

        .metric-card .mc-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 6px;
        }

        .metric-card .mc-value {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -1px;
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
        }

        .metric-card .mc-sub { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
        .metric-card.lime-accent { border-color: rgba(228, 255, 90, 0.2); }
        .metric-card.lime-accent .mc-value { color: var(--lime); }
        .metric-card.blue-accent { border-color: rgba(51, 70, 255, 0.25); }
        .metric-card.blue-accent .mc-value { color: var(--blue); }

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
                --lime-dim: rgba(51, 70, 255, 0.08);
                --lime-glow: rgba(51, 70, 255, 0.04);
                --blue: #3346FF;
                --blue-dim: rgba(51, 70, 255, 0.08);
                --green: #22c55e;
                --green-dim: rgba(34, 197, 94, 0.08);
                --red: #ef4444;
                --red-dim: rgba(239, 68, 68, 0.08);
                --amber: #f59e0b;
                --amber-dim: rgba(245, 158, 11, 0.08);
            }

            html, body { overflow: visible; height: auto; }
            .slides-wrapper { position: static; overflow: visible; }
            .slides-track { display: block; width: auto; height: auto; transform: none !important; transition: none; }

            .slide {
                min-width: unset;
                width: 100%;
                height: 100vh;
                min-height: 100vh;
                page-break-after: always;
                break-after: page;
                display: flex;
                flex-direction: column;
            }

            .slide:last-child { page-break-after: avoid; break-after: avoid; }
            .slide::before { display: none; }
            .progress-bar, .slide-counter, .nav-hint { display: none; }
            body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .bar-fill { background: var(--blue) !important; }
        }
    </style>
</head>
<body>

    <!-- ═══ PROGRESS BAR ═══ -->
    <div class="progress-bar">
        <div class="progress-fill" id="progressFill" style="width: 0%"></div>
    </div>

    <!-- ═══ SLIDE COUNTER ═══ -->
    <div class="slide-counter">
        <span class="current" id="counterCurrent">1</span> / <span id="counterTotal">1</span>
    </div>

    <!-- ═══ NAV HINTS ═══ -->
    <div class="nav-hint left">← anterior</div>
    <div class="nav-hint right">siguiente →</div>

    <!-- ═══ SLIDES WRAPPER ═══ -->
    <div class="slides-wrapper">
        <div class="slides-track" id="slidesTrack">

            <!-- ══════════════════════════════════
                 SLIDE 1: TITLE
                 ══════════════════════════════════ -->
            <div class="slide slide-title">
                <div class="slide-inner">
                    <div class="brand-badge">{{brand_name}}</div>
                    <h1>{{client_name}}</h1>
                    <p class="report-type">Google Ads Report</p>
                    <div class="meta-row">
                        <span class="date-range">{{date_range}}</span>
                        <span class="mode-badge">{{mode}}</span>
                    </div>
                    <!-- Conversion lag banner (solo si aplica) -->
                    <div class="conv-lag-banner">
                        ⚠️ Los últimos 7 días tienen datos de conversión incompletos por conversion lag. Las métricas de ese período pueden estar subrepresentadas.
                    </div>
                    <div class="hero-metrics">
                        <div class="hero-metric accent-lime">
                            <div class="metric-label">Inversión</div>
                            <div class="metric-value">{{total_cost}}</div>
                            <div class="metric-sub">período completo</div>
                        </div>
                        <div class="hero-metric">
                            <div class="metric-label">Conversiones</div>
                            <div class="metric-value">{{total_conversions}}</div>
                            <div class="metric-sub">primary conversions</div>
                        </div>
                        <div class="hero-metric">
                            <div class="metric-label">CPA</div>
                            <div class="metric-value">{{overall_cpa}}</div>
                            <div class="metric-sub">costo por conversión</div>
                        </div>
                        <div class="hero-metric">
                            <div class="metric-label">ROAS</div>
                            <div class="metric-value">{{overall_roas}}</div>
                            <div class="metric-sub">retorno sobre inversión</div>
                        </div>
                    </div>
                </div>
                <div class="slide-footer">
                    <div class="brand-footer"><span>{{brand_name}}</span> — Google Ads Report</div>
                    <div class="slide-num">1 / {{total_slides}}</div>
                </div>
            </div>

            <!-- ══════════════════════════════════
                 SLIDE 2+: ANALYSIS SLIDES
                 ══════════════════════════════════ -->
            <div class="slide slide-analysis">
                <div class="slide-inner">
                    <div class="analysis-slide-header">
                        <div class="cat-icon">{{category_icon}}</div>
                        <div class="header-text">
                            <h2>{{analysis_title}}</h2>
                            <div class="analysis-meta">
                                <span class="analysis-id">#{{analysis_number}}</span>
                                <span class="analysis-cat">{{category_name}}</span>
                            </div>
                        </div>
                    </div>
                    <div class="viz-area">
                        <!-- DATA VISUALIZATION GOES HERE -->
                    </div>
                    <div class="bottom-boxes">
                        <div class="insight-box">
                            <div class="box-label">Insight</div>
                            <p>{{insight_text}}</p>
                        </div>
                        <div class="recommendation-box">
                            <div class="box-label">Recomendación</div>
                            <p>{{recommendation_text}}</p>
                        </div>
                    </div>
                </div>
                <div class="slide-footer">
                    <div class="brand-footer"><span>{{brand_name}}</span> — Google Ads Report</div>
                    <div class="slide-num">{{slide_number}} / {{total_slides}}</div>
                </div>
            </div>

            <!-- ══════════════════════════════════
                 SLIDE SKIPPED
                 ══════════════════════════════════ -->
            <div class="slide slide-skipped">
                <div class="slide-inner">
                    <div class="analysis-slide-header">
                        <div class="cat-icon">{{category_icon}}</div>
                        <div class="header-text">
                            <h2>{{analysis_title}}</h2>
                            <div class="analysis-meta">
                                <span class="analysis-id">#{{analysis_number}}</span>
                                <span class="analysis-cat">{{category_name}}</span>
                            </div>
                        </div>
                    </div>
                    <div class="skipped-card">
                        <div class="skip-icon">—</div>
                        <h3>Análisis no disponible</h3>
                        <p class="skip-reason">{{skip_reason}}</p>
                    </div>
                </div>
                <div class="slide-footer">
                    <div class="brand-footer"><span>{{brand_name}}</span> — Google Ads Report</div>
                    <div class="slide-num">{{slide_number}} / {{total_slides}}</div>
                </div>
            </div>

        </div>
    </div>

    <script>
        (function() {
            const track = document.getElementById('slidesTrack');
            const progressFill = document.getElementById('progressFill');
            const counterCurrent = document.getElementById('counterCurrent');
            const counterTotal = document.getElementById('counterTotal');

            const slides = document.querySelectorAll('.slide');
            const total = slides.length;
            let current = 0;

            counterTotal.textContent = total;

            function goTo(index) {
                if (index < 0) index = 0;
                if (index >= total) index = total - 1;
                current = index;
                track.style.transform = `translateX(-${current * 100}vw)`;
                const pct = total > 1 ? (current / (total - 1)) * 100 : 100;
                progressFill.style.width = pct + '%';
                counterCurrent.textContent = current + 1;
            }

            function next() { goTo(current + 1); }
            function prev() { goTo(current - 1); }

            document.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); next(); }
                else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); prev(); }
                else if (e.key >= '1' && e.key <= '9') { goTo(parseInt(e.key) - 1); }
                else if (e.key === 'Home') { goTo(0); }
                else if (e.key === 'End') { goTo(total - 1); }
            });

            document.addEventListener('click', function(e) {
                if (e.target.closest('a, button, input, select')) return;
                if (e.clientX > window.innerWidth / 2) { next(); }
                else { prev(); }
            });

            let touchStartX = 0;
            document.addEventListener('touchstart', function(e) {
                touchStartX = e.changedTouches[0].clientX;
            }, { passive: true });
            document.addEventListener('touchend', function(e) {
                const diff = touchStartX - e.changedTouches[0].clientX;
                if (Math.abs(diff) > 50) {
                    if (diff > 0) { next(); } else { prev(); }
                }
            }, { passive: true });

            goTo(0);
        })();
    </script>
    <div class="watermark"><a href="https://mathiaschu.com" target="_blank">skill by mathiaschu</a></div>
</body>
</html>
```

## Visualization Patterns

### Tabla estándar con semáforos
```html
<table class="data-table">
    <thead>
        <tr>
            <th>Campaña</th>
            <th>Tipo</th>
            <th class="number">Cost</th>
            <th class="number">ROAS</th>
            <th class="number">CPA</th>
            <th class="number">CTR</th>
            <th class="number">QS</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="name-cell">Search - Brand</td>
            <td>Search</td>
            <td class="number highlight">$3.500</td>
            <td class="number"><span class="semaphore-green">7.14</span></td>
            <td class="number">$19</td>
            <td class="number"><span class="semaphore-green">7.1%</span></td>
            <td class="number"><span class="qs-badge qs-high">9</span></td>
        </tr>
        <tr>
            <td class="name-cell">Search - Generic</td>
            <td>Search</td>
            <td class="number">$5.500</td>
            <td class="number"><span class="semaphore-yellow">2.10</span></td>
            <td class="number">$58</td>
            <td class="number"><span class="semaphore-yellow">1.8%</span></td>
            <td class="number"><span class="qs-badge qs-mid">5</span></td>
        </tr>
    </tbody>
</table>
```

### Bar chart horizontal
```html
<div class="bar-chart">
    <div class="bar-row">
        <span class="bar-label">Search - Brand</span>
        <div class="bar-track"><div class="bar-fill" style="width: 85%"></div></div>
        <span class="bar-value">$3.500</span>
    </div>
    <div class="bar-row">
        <span class="bar-label">PMax - Generic</span>
        <div class="bar-track"><div class="bar-fill blue" style="width: 60%"></div></div>
        <span class="bar-value">$2.800</span>
    </div>
</div>
```

### Funnel diagram
```html
<div class="funnel">
    <div class="funnel-step">
        <div class="funnel-meta">
            <div class="step-name">Impresiones</div>
            <div class="step-value">850.000</div>
        </div>
        <div class="funnel-bar-wrap">
            <div class="funnel-bar" style="width: 100%">100%</div>
        </div>
    </div>
    <div class="funnel-arrow">▼</div>
    <div class="funnel-step">
        <div class="funnel-meta">
            <div class="step-name">Clicks</div>
            <div class="step-value">18.500</div>
            <div class="step-rate">2.18% CTR</div>
        </div>
        <div class="funnel-bar-wrap">
            <div class="funnel-bar" style="width: 55%">2.18%</div>
        </div>
    </div>
    <div class="funnel-arrow">▼</div>
    <div class="funnel-step">
        <div class="funnel-meta">
            <div class="step-name">Conversiones</div>
            <div class="step-value">320</div>
            <div class="step-rate">1.73% Conv Rate</div>
        </div>
        <div class="funnel-bar-wrap">
            <div class="funnel-bar" style="width: 20%">1.73%</div>
        </div>
    </div>
</div>
```

## Reglas para Claude

1. El HTML debe ser **self-contained** — solo dependencia externa es Google Fonts.
2. Todos los charts son **CSS puro** — no usar Chart.js, D3 ni ninguna librería JS.
3. El JS incluido es **solo para navegación** de slides — no agregar más JS.
4. Cada análisis genera **un slide** con su propia visualización adecuada al tipo de dato.
5. Para análisis skipped, usar el template `.slide-skipped` con la razón específica.
6. **Insights y recomendaciones los escribe Claude** basándose en los datos — no son estáticos.
7. El `{{total_slides}}` en cada footer y en el contador debe ser el número real de slides generados.
8. Usar semáforos en celdas de métricas según la lógica definida en "Semaphore Logic".
9. El template es responsive para pantalla, pero en **print mode** cada slide es una página A4.
10. Para tablas largas, reducir `font-size` a `12px` o usar `overflow-y: auto` en `.viz-area`.
11. **Conversion lag banner**: incluir solo si el período analizado incluye los últimos 7 días. Si no, remover el div `.conv-lag-banner`.
12. **Quality Score badges**: usar `.qs-high` (7-10), `.qs-mid` (5-6), `.qs-low` (1-4).
