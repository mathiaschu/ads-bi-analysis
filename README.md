# Ads & BI Analysis Skills for Claude Code

A collection of Claude Code skills for analyzing digital advertising campaigns and eCommerce data. Each skill provides expert-level analysis with HTML report generation.

## Skills

### Meta Ads

- **`meta-ads/analyzer/`** — Conceptual analysis and diagnosis for Meta Ads campaigns. Covers the Breakdown Effect, Learning Phase, bid strategies, auction mechanics, ad relevance diagnostics, and more. 9 reference documents.

- **`meta-ads/html-report/`** — Generates full HTML slide-based reports from Meta Ads Manager CSV exports or API data. Two modes: Lite (18 analyses) and Full (32). Includes nomenclature parsing for creative analysis, benchmark semaphores (AR/LATAM), and funnel visualization.

### Google Ads

- **`google-ads/analyzer/`** — Expert analysis for Google Ads via GAQL queries. Covers Quality Score, Impression Share, Smart Bidding, Performance Max, search terms, negative keywords, and account structure. 12 reference documents.

- **`google-ads/html-report/`** — Generates full HTML slide-based reports from Google Ads CSV exports or MCP API data. Two modes: Lite (18 analyses) and Full (30). Covers Search, Shopping, PMax, and mixed accounts.

### eCommerce BI

- **`ecommerce-bi/`** — Business Intelligence reports from eCommerce sales CSVs. Analyzes Market Basket, RFM segmentation, cohorts, CLV, cross-sell, seasonality, and more. Two modes: Lite (20 analyses) and Full (38).

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Python 3.9+
- `pandas` and `numpy` (`pip3 install pandas numpy`)

## Installation

Copy the skill folders into your Claude Code skills directory:

```bash
# Clone the repo
git clone https://github.com/mathiaschu/ads-bi-analysis.git

# Copy skills to your Claude Code config
cp -r ads-bi-analysis/meta-ads/ ~/.claude/skills/
cp -r ads-bi-analysis/google-ads/ ~/.claude/skills/
cp -r ads-bi-analysis/ecommerce-bi/ ~/.claude/skills/
```

Or selectively copy only the skills you need.

## Usage

Each skill is triggered by keywords in your Claude Code conversation:

| Skill | Trigger examples |
|-------|-----------------|
| Meta Ads Analyzer | "analyze meta ads", "campaign diagnosis", "CPA analysis" |
| Meta Ads HTML Report | "meta ads report", "informe meta ads html" |
| Google Ads Analyzer | "analyze google ads", "Quality Score", "Impression Share" |
| Google Ads HTML Report | "google ads report", "informe google ads html" |
| eCommerce BI | "business intelligence", "RFM", "market basket", "CLV" |

### HTML Reports

The HTML report skills generate slide-based presentations with:
- Keyboard navigation (arrow keys + number keys)
- Dark mode with print-friendly light mode
- Benchmark semaphores (green/amber/red)
- Actionable insights per analysis

The template uses `{{brand_name}}` placeholders — customize the branding in each `references/html_template.md` file.

### Customizing Nomenclature (Meta Ads)

The Meta Ads HTML report skill includes a nomenclature parser (`references/nomenclatura_parser.md`) that extracts structured data from campaign/ad names. Two built-in formats:

- **Standard**: `Product | Format | Stage | Creator | Variation`
- **Alternative**: `Stage_Product_Format_Variation`

You can also provide custom regex patterns with named groups.

## License

MIT
