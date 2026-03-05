---
name: google-ads-analyzer
description: "Provides expert-level analysis and diagnosis for Google Ads campaigns. Supports CSV exports and GAQL API queries. Use this skill to interpret performance data, diagnose Quality Score and Impression Share issues, evaluate Smart Bidding and Performance Max campaigns, and generate actionable recommendations. Use when the user mentions Google Ads analysis, CSV export, GAQL queries, Quality Score, Impression Share, PMax, Smart Bidding, ROAS, CPA, search terms, negative keywords, or asks to analyze Google Ads data."
---

# Google Ads Analysis & Diagnosis Skill

## When to Use This Skill

Use this skill when you need to **analyze and diagnose Google Ads campaign performance**, including:
- Interpreting campaign, ad group, or keyword-level performance data
- Analyzing CSV exports from Google Ads Manager (campaign, keyword, search term, or ad reports)
- Running GAQL queries to pull metrics from the Google Ads API (when MCP access is available)
- Diagnosing Quality Score, Impression Share, and Smart Bidding issues
- Evaluating Performance Max campaigns (asset groups, signals, feed quality)
- Analyzing search term reports and negative keyword coverage
- Generating structured analysis reports with actionable recommendations

## Data Sources

This skill supports two data sources:

| Source | When to use |
| :--- | :--- |
| **CSV export** | User provides files exported from Google Ads Manager. No API access needed. Use `csv_mapping.md` for column mapping and report type detection. |
| **GAQL API** | MCP tools available (`list_accessible_customers`, `search`). Use `gaql_queries.md` for ready-made queries. |

The analysis workflow adapts automatically based on the data source. Both paths converge at the Diagnose step (Step 3).

## Result Recommendations (MANDATORY for Final Reports)

> **IMPORTANT:** The following rules are **MANDATORY** and **MUST be strictly followed** when writing the final analysis report. These are not optional guidelines — they define the required standards for all deliverables.

- **ALWAYS divide `cost_micros` by 1,000,000** to get the actual cost. Google Ads API returns all monetary values in micros (1 unit = 1,000,000 micros). **CSV exports already use display currency — do NOT divide.**
- **ALWAYS identify the currency** before interpreting any cost values. API: check `customer.currency_code`. CSV: detect from column headers (e.g. "Cost (ARS)"). Never assume USD.
- **ALWAYS compare vs. prior period** (month-over-month at minimum). Never present metrics in isolation without temporal context.
- **ALWAYS discount the last 7 days** when evaluating conversion-based metrics. Conversion lag means recent data underreports actual performance.
- **ALWAYS discover account via MCC first** when using API. Use `list_accessible_customers` to find accounts, then query with `login-customer-id` header. **When working with CSV exports, skip this step** — the data is already scoped to the exported account.
- **NEVER judge Performance Max** without reviewing asset group performance, ad strength, and feed quality (if Shopping). PMax is a black box — surface-level metrics are misleading.
- **NEVER recommend increasing budget** if Impression Share lost by Ad Rank exceeds 50%. Fix Quality Score and bids first.
- **EVERY insight must include data evidence and explanation.** Every recommendation must be actionable and verifiable.
- **Disambiguate conversion types.** Always clarify whether you mean `conversions` (primary only) or `all_conversions` (primary + secondary). These are different columns with different strategic implications.

## Metric Naming Guidelines

**IMPORTANT:** Always rename API metric names to standardized display names in all responses:

| API Metric | Standardized Display Name |
| :--- | :--- |
| `metrics.cost_micros` | Cost |
| `metrics.impressions` | Impressions |
| `metrics.clicks` | Clicks |
| `metrics.ctr` | CTR |
| `metrics.average_cpc` | Avg. CPC |
| `metrics.conversions` | Conversions (Primary) |
| `metrics.all_conversions` | Conversions (All) |
| `metrics.conversions_value` | Conversion Value |
| `metrics.cost_per_conversion` | Cost / Conversion |
| `metrics.search_impression_share` | Search IS |
| `metrics.search_budget_lost_impression_share` | Search IS Lost (Budget) |
| `metrics.search_rank_lost_impression_share` | Search IS Lost (Rank) |
| `metrics.interaction_rate` | Interaction Rate |
| `metrics.average_cost` | Avg. Cost |
| `ad_group_criterion.quality_info.quality_score` | Quality Score |

**Monetary values (API):** Always divide `cost_micros` by 1,000,000 and format with the account's currency symbol.
**Monetary values (CSV):** Already in display currency — no conversion needed. Detect currency from column headers.

## Core Principles

- **Structure First:** Understand the account hierarchy (MCC → accounts → campaigns → ad groups → keywords) before drilling into metrics. Context determines what "good" looks like.
- **Signal over Noise:** Google Ads data is noisy day-to-day. Analyze trends over 14-30 day windows. Single-day spikes are rarely actionable.
- **System Awareness:** Smart Bidding, Broad Match, and Performance Max are ML-driven systems. Respect learning periods, avoid micro-managing, and diagnose the system's constraints (budget, conversion data, audience signals) rather than overriding its decisions.

## Google Ads Domain Knowledge

### Micros (API only)
All monetary values from the API are in **micros** (1 currency unit = 1,000,000 micros). Always divide by 1,000,000 before displaying. CSV exports already use display currency — no conversion needed.

### Account Hierarchy
- **MCC (Manager Account):** Top-level account managing multiple client accounts
- **Customer Account:** Individual ad account with campaigns
- **`login-customer-id`:** Required header when querying via MCC access. Set to the MCC ID.

### GAQL (Google Ads Query Language)
The API uses GAQL, a SQL-like language for querying resources. Key differences from SQL:
- No `JOIN` — each resource has pre-defined accessible fields
- Use `segments.*` for breakdowns (device, date, day_of_week, etc.)
- Filtering uses `WHERE` with specific operators per field type
- Date ranges via `segments.date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'`

### Campaign Types
| Type | Key Characteristics |
| :--- | :--- |
| **Search** | Keyword-targeted text ads on Search results |
| **Performance Max** | All-channel automated campaign (Search, Display, YouTube, Gmail, Maps, Discover) |
| **Shopping** | Product feed-based ads on Shopping tab and Search |
| **Display** | Banner/image ads across Google Display Network |
| **Video** | YouTube ads (in-stream, bumper, discovery) |
| **Demand Gen** | Visual ads across YouTube, Gmail, Discover |

## Analysis Workflow

**Reference Documents** (loaded automatically from `references/`):
- `core_concepts.md` - Hub: Ad Rank, Quality Score, Smart Bidding, PMax, GAQL overview
- `csv_mapping.md` - CSV column mapping, report type detection, parsing rules
- `gaql_queries.md` - Ready-to-use GAQL queries for each workflow step (API only)
- `quality_score.md` - 3 components, diagnosis by component
- `impression_share.md` - IS, lost by budget vs rank, auction insights
- `smart_bidding.md` - tCPA, tROAS, learning period, when to intervene
- `performance_max.md` - Asset groups, signals, feed quality, cannibalization
- `conversion_tracking.md` - Types, DDA, conversion lag, primary vs secondary
- `account_structure.md` - MCC hierarchy, naming, brand vs non-brand
- `search_terms_negatives.md` - Search term report, match types, negative keywords
- `ad_copy_rsa.md` - RSA, headlines, descriptions, ad strength, asset labels
- `segmentation.md` - GAQL segments: device, geo, day_of_week, audiences
- `performance_fluctuations.md` - Normal vs concerning, conversion lag trap, checklist

### Step 1: Discovery

Identify the data source and account structure before any analysis.

**If CSV export:**
1. Read CSV headers and detect report type using `csv_mapping.md` (campaign, keyword, search term, or ad report)
2. Map columns to canonical names using `csv_mapping.md`
3. Detect currency from cost column headers (e.g. "Cost (ARS)" → ARS)
4. Identify campaigns, types, and bidding strategies from the data
5. Note which campaigns are PMax (separate analysis path)
6. If user provides multiple CSVs (e.g. campaign report + keyword report), combine them for a richer analysis

**If GAQL API:**
1. Call `list_accessible_customers` to find available accounts
2. Query `customer` resource for account name, currency, timezone
3. Query `campaign` resource for active campaigns, types, and bidding strategies
4. Note which campaigns are PMax (separate analysis path)

### Step 2: Pull Metrics + Temporal Comparison

**If CSV export:**
The data is already available. Identify the date range present in the CSV and split into current vs previous period for comparison. If the CSV lacks daily granularity or a prior period, note this limitation but proceed with available data.

**If GAQL API:**
Pull performance data with always two periods for comparison:

| Period | Purpose |
| :--- | :--- |
| Current month (excluding last 7 days) | Primary analysis window |
| Previous month (same day count) | Comparison baseline |

Use queries from `gaql_queries.md`. Always pull daily granularity for trend analysis.

**Both sources converge here** — from Step 3 onward, the analysis is the same regardless of data source.

### Step 3: Diagnose

Run diagnostic checks in this order:

1. **Quality Score** — Pull keyword-level QS with components. Flag keywords with QS < 5
2. **Impression Share** — Check IS lost by budget vs rank. Budget-limited = opportunity. Rank-limited = fix QS/bids
3. **Smart Bidding** — Check bidding strategy status, learning state, target vs actual CPA/ROAS
4. **Conversions** — Verify tracking setup, conversion lag impact, primary vs secondary actions
5. **Search Terms** — Review search term report for wasted spend, irrelevant queries, missing negatives

### Step 4: Deep Dive Performance Max (if applicable)

PMax requires a separate analysis path:

1. Pull asset group performance (impressions, conversions, cost)
2. Check ad strength per asset group (Excellent, Good, Average, Poor)
3. Review listing group filters (if Shopping feed)
4. Check for cannibalization with branded Search campaigns
5. Evaluate audience signals vs actual reach

### Step 5: Generate Report

Structure every analysis report as:

1. **Executive Summary** — 2-3 key findings with business impact
2. **Account Overview** — Structure, campaign types, bidding strategies, budget allocation
3. **Performance Analysis** — Metrics with period comparison and trends
4. **Quality Score & Impression Share Diagnosis** — Component-level QS, IS breakdown
5. **Conversion & Bidding Analysis** — Tracking health, Smart Bidding status, lag impact
6. **Search Terms & Negatives** — Wasted spend, opportunities, negative keyword gaps
7. **Recommendations** — Prioritized, actionable, with expected impact and effort level
