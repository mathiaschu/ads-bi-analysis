# HTML Template — {{brand_name}} Meta Ads Report (Slides)

## Instrucciones

Este template define la estructura HTML completa del informe de Meta Ads como presentación de slides full-screen. Claude debe usar este template como base, reemplazando los placeholders `{{...}}` con datos reales del análisis.

**Diferencia clave respecto al BI Report:** Este template es slide-based (no scrollable). Cada análisis ocupa un slide completo. La navegación es por teclado o click.

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
- "Meta Ads Analysis" (subtítulo)
- Rango de fechas analizado
- Mode badge (Lite / Full)
- Hero metrics: Inversión, ROAS, CPA, Compras

### Slides 2–N: Analysis Slides
- **Top:** número de slide + ícono de categoría + título del análisis
- **Middle:** visualización (tabla, bar chart, heatmap, funnel, scatter)
- **Bottom:** insight box (lime) + recommendation box (blue)
- **Si fue skipped:** slide con borde punteado + razón del skip

### Footer en cada slide
"{{brand_name}} — Meta Ads Analysis" + contador "N / Total"

## Category Icons

| Categoría | Icon |
|-----------|------|
| Overview | 📊 |
| Campañas | 🎯 |
| Ad Sets | 📦 |
| Ads | 🎨 |
| Funnel | 🔄 |
| Temporal | 📅 |
| Geo | 🗺️ |
| Placement | 📱 |
| Device | 💻 |
| Estratégico | ⚡ |
| Nomenclatura | 🏷️ |
| Creativo | 🎬 |
| Revenue | 💰 |
| Avanzado | 🔬 |

## Semaphore Logic

| Métrica | Verde | Amarillo | Rojo |
|---------|-------|----------|------|
| CTR | >2% | 1–2% | <1% |
| Frecuencia | <3 | 3–5 | >5 |
| ROAS | >3x | 1.5–3x | <1.5x |
| CPA | < promedio cuenta | ~ promedio | > promedio |

Clases CSS: `.semaphore-green`, `.semaphore-yellow`, `.semaphore-red`

## Formato Numérico

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| Currency | `$XXX.XXX` (punto miles, sin decimales para valores grandes) | `$2.340.500` |
| Porcentajes | `XX.X%` (1 decimal) | `3.4%` |
| ROAS | `X.XX` (2 decimales) | `4.32` |
| Números grandes | `X.XXX` (punto miles) | `12.450` |
| CPA | `$X.XXX` | `$1.250` |

## Template HTML

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{client_name}} — Meta Ads Analysis</title>
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

        /* Grid background on each slide */
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
           SLIDE COUNTER (top-right)
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

        .slide-counter .current {
            color: var(--lime);
        }

        /* ═══════════════════════════════════════
           NAVIGATION HINTS (bottom corners)
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

        .slide-footer .brand-footer span {
            color: var(--lime);
        }

        .slide-footer .slide-num {
            font-size: 11px;
            color: var(--text-muted);
            font-variant-numeric: tabular-nums;
        }

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
            margin-bottom: 48px;
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

        .slide-title .hero-metric.accent-lime .metric-value {
            color: var(--lime);
        }

        /* ═══════════════════════════════════════
           ANALYSIS SLIDE HEADER
           ═══════════════════════════════════════ */
        .slide-analysis .slide-inner {
            gap: 20px;
        }

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

        .analysis-slide-header .header-text {
            flex: 1;
        }

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

        .skipped-card .skip-icon {
            font-size: 40px;
            margin-bottom: 16px;
        }

        .skipped-card h3 {
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 12px;
        }

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

        /* ═══════════════════════════════════════
           BAR CHARTS (CSS only)
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

        .bar-fill.blue {
            background: linear-gradient(90deg, var(--blue), rgba(51, 70, 255, 0.5));
        }

        .bar-fill.green {
            background: linear-gradient(90deg, var(--green), rgba(34, 197, 94, 0.5));
        }

        .bar-fill.red {
            background: linear-gradient(90deg, var(--red), rgba(239, 68, 68, 0.5));
        }

        .bar-value {
            width: 90px;
            font-size: 12px;
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
        }

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

        /* Heatmap intensity levels */
        .heat-0 { background: rgba(228, 255, 90, 0.04); }
        .heat-1 { background: rgba(228, 255, 90, 0.14); }
        .heat-2 { background: rgba(228, 255, 90, 0.28); }
        .heat-3 { background: rgba(228, 255, 90, 0.46); }
        .heat-4 { background: rgba(228, 255, 90, 0.68); color: #0a0a0a; }
        .heat-5 { background: rgba(228, 255, 90, 0.90); color: #0a0a0a; font-weight: 700; }

        /* ═══════════════════════════════════════
           FUNNEL DIAGRAM (CSS trapezoids)
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

        .funnel-bar-wrap {
            flex: 1;
            display: flex;
            justify-content: center;
        }

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
            transition: width 0.3s ease;
        }

        .funnel-meta {
            width: 160px;
        }

        .funnel-meta .step-name {
            font-size: 12px;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .funnel-meta .step-value {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
        }

        .funnel-meta .step-rate {
            font-size: 11px;
            color: var(--text-muted);
        }

        .funnel-arrow {
            text-align: center;
            color: var(--text-muted);
            font-size: 14px;
            padding: 2px 0;
        }

        /* ═══════════════════════════════════════
           SCATTER PLOT APPROXIMATION (CSS grid)
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
           METRIC GRID (2x2, 3x2, etc.)
           ═══════════════════════════════════════ */
        .metric-grid {
            display: grid;
            gap: 12px;
        }

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

        .metric-card .mc-sub {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }

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

            .progress-bar,
            .slide-counter,
            .nav-hint { display: none; }

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
                    <p class="report-type">Meta Ads Analysis</p>
                    <div class="meta-row">
                        <span class="date-range">{{date_range}}</span>
                        <span class="mode-badge">{{mode}}</span>
                    </div>
                    <div class="hero-metrics">
                        <div class="hero-metric accent-lime">
                            <div class="metric-label">Inversión</div>
                            <div class="metric-value">{{total_spend}}</div>
                            <div class="metric-sub">período completo</div>
                        </div>
                        <div class="hero-metric">
                            <div class="metric-label">ROAS</div>
                            <div class="metric-value">{{overall_roas}}</div>
                            <div class="metric-sub">retorno sobre inversión</div>
                        </div>
                        <div class="hero-metric">
                            <div class="metric-label">CPA</div>
                            <div class="metric-value">{{overall_cpa}}</div>
                            <div class="metric-sub">costo por conversión</div>
                        </div>
                        <div class="hero-metric">
                            <div class="metric-label">Compras</div>
                            <div class="metric-value">{{total_purchases}}</div>
                            <div class="metric-sub">total atribuido</div>
                        </div>
                    </div>
                </div>
                <div class="slide-footer">
                    <div class="brand-footer"><span>{{brand_name}}</span> — Meta Ads Analysis</div>
                    <div class="slide-num">1 / {{total_slides}}</div>
                </div>
            </div>

            <!-- ══════════════════════════════════
                 SLIDE 2+: ANALYSIS SLIDES
                 Repetir este bloque por cada análisis
                 ══════════════════════════════════ -->
            <div class="slide slide-analysis">
                <div class="slide-inner">

                    <!-- Header del análisis -->
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

                    <!-- Área de visualización -->
                    <div class="viz-area">
                        <!-- DATA VISUALIZATION GOES HERE -->
                        <!-- Ver sección "Visualization Patterns" más abajo -->
                    </div>

                    <!-- Insight + Recomendación -->
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
                    <div class="brand-footer"><span>{{brand_name}}</span> — Meta Ads Analysis</div>
                    <div class="slide-num">{{slide_number}} / {{total_slides}}</div>
                </div>
            </div>

            <!-- ══════════════════════════════════
                 SLIDE SKIPPED (si el análisis fue omitido)
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
                    <div class="brand-footer"><span>{{brand_name}}</span> — Meta Ads Analysis</div>
                    <div class="slide-num">{{slide_number}} / {{total_slides}}</div>
                </div>
            </div>

        </div><!-- /slides-track -->
    </div><!-- /slides-wrapper -->

    <script>
        /* ═══════════════════════════════════════
           SLIDES NAVIGATION
           ═══════════════════════════════════════ */
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
                // Progress: 0 on slide 1, 100 on last slide
                const pct = total > 1 ? (current / (total - 1)) * 100 : 100;
                progressFill.style.width = pct + '%';
                counterCurrent.textContent = current + 1;
            }

            function next() { goTo(current + 1); }
            function prev() { goTo(current - 1); }

            // Keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); next(); }
                else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); prev(); }
                else if (e.key >= '1' && e.key <= '9') { goTo(parseInt(e.key) - 1); }
                else if (e.key === 'Home') { goTo(0); }
                else if (e.key === 'End') { goTo(total - 1); }
            });

            // Click navigation (left/right halves)
            document.addEventListener('click', function(e) {
                // Ignore clicks on interactive elements
                if (e.target.closest('a, button, input, select')) return;
                if (e.clientX > window.innerWidth / 2) { next(); }
                else { prev(); }
            });

            // Touch/swipe support
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

            // Initialize
            goTo(0);
        })();
    </script>
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
            <th class="number">Inversión</th>
            <th class="number">ROAS</th>
            <th class="number">CTR</th>
            <th class="number">CPA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="name-cell">Retargeting — Carrito Abandonado</td>
            <td class="number highlight">$245.000</td>
            <td class="number"><span class="semaphore-green">4.32</span></td>
            <td class="number"><span class="semaphore-yellow">1.8%</span></td>
            <td class="number">$1.230</td>
        </tr>
        <tr>
            <td class="name-cell">Prospección — Lookalike 1%</td>
            <td class="number">$180.000</td>
            <td class="number"><span class="semaphore-yellow">2.10</span></td>
            <td class="number"><span class="semaphore-red">0.7%</span></td>
            <td class="number">$3.100</td>
        </tr>
    </tbody>
</table>
```

### Bar chart horizontal
```html
<div class="bar-chart">
    <div class="bar-row">
        <span class="bar-label">Retargeting Carrito</span>
        <div class="bar-track"><div class="bar-fill" style="width: 85%"></div></div>
        <span class="bar-value">$245.000</span>
    </div>
    <div class="bar-row">
        <span class="bar-label">Prospección LAL 1%</span>
        <div class="bar-track"><div class="bar-fill" style="width: 60%"></div></div>
        <span class="bar-value">$180.000</span>
    </div>
    <div class="bar-row">
        <span class="bar-label">Intereses Broad</span>
        <div class="bar-track"><div class="bar-fill blue" style="width: 40%"></div></div>
        <span class="bar-value">$120.000</span>
    </div>
</div>
```

### Heatmap (por hora/día)
```html
<!-- grid-template-columns: primera col label + N cols de datos -->
<div class="heatmap" style="grid-template-columns: 80px repeat(7, 1fr);">
    <div class="heatmap-header"></div>
    <div class="heatmap-header">Lun</div>
    <div class="heatmap-header">Mar</div>
    <div class="heatmap-header">Mié</div>
    <div class="heatmap-header">Jue</div>
    <div class="heatmap-header">Vie</div>
    <div class="heatmap-header">Sáb</div>
    <div class="heatmap-header">Dom</div>

    <div class="heatmap-header">08–12h</div>
    <div class="heatmap-cell heat-2">2.1%</div>
    <div class="heatmap-cell heat-3">3.4%</div>
    <div class="heatmap-cell heat-1">1.2%</div>
    <div class="heatmap-cell heat-3">3.1%</div>
    <div class="heatmap-cell heat-4">5.2%</div>
    <div class="heatmap-cell heat-2">2.8%</div>
    <div class="heatmap-cell heat-0">0.4%</div>

    <div class="heatmap-header">12–20h</div>
    <div class="heatmap-cell heat-4">4.8%</div>
    <div class="heatmap-cell heat-5">6.1%</div>
    <!-- ... -->
</div>
```

### Funnel diagram
```html
<div class="funnel">
    <div class="funnel-step">
        <div class="funnel-meta">
            <div class="step-name">Impresiones</div>
            <div class="step-value">1.240.000</div>
        </div>
        <div class="funnel-bar-wrap">
            <div class="funnel-bar" style="width: 100%">100%</div>
        </div>
    </div>
    <div class="funnel-arrow">▼</div>
    <div class="funnel-step">
        <div class="funnel-meta">
            <div class="step-name">Clicks</div>
            <div class="step-value">18.600</div>
            <div class="step-rate">1.5% CTR</div>
        </div>
        <div class="funnel-bar-wrap">
            <div class="funnel-bar" style="width: 60%">1.5%</div>
        </div>
    </div>
    <div class="funnel-arrow">▼</div>
    <div class="funnel-step">
        <div class="funnel-meta">
            <div class="step-name">Add to Cart</div>
            <div class="step-value">2.400</div>
            <div class="step-rate">12.9% de clicks</div>
        </div>
        <div class="funnel-bar-wrap">
            <div class="funnel-bar" style="width: 35%">12.9%</div>
        </div>
    </div>
    <div class="funnel-arrow">▼</div>
    <div class="funnel-step">
        <div class="funnel-meta">
            <div class="step-name">Compras</div>
            <div class="step-value">480</div>
            <div class="step-rate">20% de ATC</div>
        </div>
        <div class="funnel-bar-wrap">
            <div class="funnel-bar" style="width: 18%">20%</div>
        </div>
    </div>
</div>
```

### Metric Grid (para overview / resumen)
```html
<div class="metric-grid cols-4">
    <div class="metric-card lime-accent">
        <div class="mc-label">ROAS General</div>
        <div class="mc-value">3.84</div>
        <div class="mc-sub">vs 3.21 mes anterior</div>
    </div>
    <div class="metric-card">
        <div class="mc-label">CTR Promedio</div>
        <div class="mc-value">1.42%</div>
        <div class="mc-sub">Feed + Stories</div>
    </div>
    <div class="metric-card">
        <div class="mc-label">Frecuencia</div>
        <div class="mc-value">2.8</div>
        <div class="mc-sub">promedio período</div>
    </div>
    <div class="metric-card blue-accent">
        <div class="mc-label">CPM</div>
        <div class="mc-value">$4.200</div>
        <div class="mc-sub">costo por mil</div>
    </div>
</div>
```

### Scatter plot aproximado (CSS positioning)
```html
<div style="position: relative;">
    <div class="scatter-wrap">
        <!-- cada dot: bottom = eje Y (%), left = eje X (%) -->
        <div class="scatter-dot large lime-accent" style="bottom: 70%; left: 80%"
             title="Campaña A: ROAS 4.2, Inversión $300K"></div>
        <div class="scatter-dot" style="bottom: 40%; left: 45%"
             title="Campaña B: ROAS 2.5, Inversión $180K"></div>
        <div class="scatter-dot small red" style="bottom: 15%; left: 20%"
             title="Campaña C: ROAS 1.1, Inversión $80K"></div>
    </div>
    <div class="scatter-axis-label">Inversión (eje X) → Inversión mayor a la derecha</div>
    <!-- Labels eje X -->
    <span class="scatter-label-x" style="left: 20%">$80K</span>
    <span class="scatter-label-x" style="left: 45%">$180K</span>
    <span class="scatter-label-x" style="left: 80%">$300K</span>
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
8. Usar semáforos en celdas de métricas según la lógica definida en la sección "Semaphore Logic".
9. El template es responsive para pantalla, pero en **print mode** cada slide es una página A4.
10. Para tablas largas, reducir `font-size` a `12px` o usar `overflow-y: auto` en `.viz-area`.
