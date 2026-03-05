# Ads & BI Analysis — Skills para Claude Code

Colección de skills de Claude Code para analizar campañas de publicidad digital y datos de eCommerce. Cada skill provee análisis a nivel experto con generación de informes HTML.

## Skills

### Meta Ads

- **`meta-ads/analyzer/`** — Análisis conceptual y diagnóstico de campañas Meta Ads. Cubre Breakdown Effect, Learning Phase, estrategias de puja, mecánica de subastas, diagnóstico de relevancia y más. 9 documentos de referencia.

- **`meta-ads/html-report/`** — Genera informes HTML en formato slides a partir de CSVs de Meta Ads Manager o datos de API. Dos modos: Lite (18 análisis) y Full (32). Incluye parseo de nomenclaturas para análisis creativo, semáforos de benchmarks (AR/LATAM) y visualización de funnel.

### Google Ads

- **`google-ads/analyzer/`** — Análisis experto de Google Ads vía consultas GAQL. Cubre Quality Score, Impression Share, Smart Bidding, Performance Max, search terms, negative keywords y estructura de cuenta. 12 documentos de referencia.

- **`google-ads/html-report/`** — Genera informes HTML en formato slides a partir de CSVs de Google Ads o datos de MCP API. Dos modos: Lite (18 análisis) y Full (30). Cubre Search, Shopping, PMax y cuentas mixtas.

### eCommerce BI

- **`ecommerce-bi/`** — Informes de Business Intelligence a partir de CSVs de ventas eCommerce. Analiza Market Basket, segmentación RFM, cohortes, CLV, cross-sell, estacionalidad y más. Dos modos: Lite (20 análisis) y Full (38).

## Requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Python 3.9+
- `pandas` y `numpy` (`pip3 install pandas numpy`)

## Instalación

Copiar las carpetas de skills al directorio de skills de Claude Code:

```bash
# Clonar el repo
git clone https://github.com/mathiaschu/ads-bi-analysis.git

# Copiar skills a la config de Claude Code
cp -r ads-bi-analysis/meta-ads/ ~/.claude/skills/
cp -r ads-bi-analysis/google-ads/ ~/.claude/skills/
cp -r ads-bi-analysis/ecommerce-bi/ ~/.claude/skills/
```

O copiar selectivamente solo las skills que necesites.

## Uso

Cada skill se activa por keywords en la conversación de Claude Code:

| Skill | Ejemplos de trigger |
|-------|---------------------|
| Meta Ads Analyzer | "analyze meta ads", "diagnóstico de campaña", "análisis CPA" |
| Meta Ads HTML Report | "meta ads report", "informe meta ads html" |
| Google Ads Analyzer | "analyze google ads", "Quality Score", "Impression Share" |
| Google Ads HTML Report | "google ads report", "informe google ads html" |
| eCommerce BI | "business intelligence", "RFM", "market basket", "CLV" |

### Informes HTML

Las skills de reportes HTML generan presentaciones en slides con:
- Navegación por teclado (flechas + números)
- Dark mode con modo claro para impresión
- Semáforos de benchmarks (verde/amarillo/rojo)
- Insights accionables por análisis

El template usa placeholders `{{brand_name}}` — personalizá el branding en el archivo `references/html_template.md` de cada skill.

### Nomenclaturas personalizables (Meta Ads)

La skill de HTML report de Meta Ads incluye un parser de nomenclaturas (`references/nomenclatura_parser.md`) que extrae datos estructurados de los nombres de campañas/ads. Dos formatos built-in:

- **Standard**: `Producto | Formato | Etapa | Creador | Variación`
- **Alternative**: `Etapa_Producto_Formato_Variación`

También podés definir patrones regex custom con named groups.

## Autor

Creado por [mathiaschu](https://mathiaschu.com)

## Licencia

MIT
